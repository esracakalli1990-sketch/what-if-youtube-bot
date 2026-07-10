"""
manual_images.py - Manuel Görsel Akışı (Telegram üzerinden).

Görselleri API yerine kullanıcı üretir (ör. Google Flow / Nano Banana Pro):
1. Faz 1: Bot senaryoyu üretir, her sahnenin prompt'unu Telegram'a gönderir
   ve bekleyen üretimi pending_production.json'a kaydeder.
2. Kullanıcı prompt'larla görselleri üretip bota fotoğraf olarak gönderir
   (gönderim sırası = sahne sırası).
3. Faz 2: Saatlik Telegram işleyicisi fotoğrafları toplar; hepsi gelince
   indirir, hedef orana merkez-kırpar, pipeline cache dosyalarına yazar ve
   videoyu tamamlar.

Aktifleştirme: IMAGE_MODE=manual (env / GitHub Variables).
"""

import io
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Doğrudan çalıştırma desteği
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from PIL import Image

from scripts.utils import (
    print_success, print_error, print_warning, console, logger,
    PROJECT_ROOT, TEMP_DIR, IMAGES_DIR, load_env, save_json,
)
from scripts.notifier import TELEGRAM_API, send_message

# Bekleyen üretim durumu — workflow'larca commit edilir (topics.json gibi)
PENDING_FILE = PROJECT_ROOT / "pending_production.json"

# Hatırlatma aralığı (saat)
REMINDER_INTERVAL_HOURS = 24


def is_manual_mode() -> bool:
    """Manuel görsel akışı aktif mi?"""
    return os.getenv("IMAGE_MODE", "").strip().lower() == "manual"


def load_pending() -> dict | None:
    """Bekleyen üretimi oku (yoksa None)."""
    if not PENDING_FILE.exists():
        return None
    try:
        with open(PENDING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if data.get("topic") else None
    except (json.JSONDecodeError, IOError):
        return None


def _save_pending(data: dict):
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cancel_pending() -> bool:
    """Bekleyen üretimi iptal et."""
    if PENDING_FILE.exists():
        PENDING_FILE.unlink()
        logger.info("Bekleyen üretim iptal edildi.")
        return True
    return False


def images_ready(scenes: list[dict], vertical: bool) -> bool:
    """Tüm sahne görselleri pipeline cache'inde hazır mı?"""
    suffix = "_vertical" if vertical else ""
    for i, scene in enumerate(scenes):
        scene_num = scene.get("scene_number", i + 1)
        path = IMAGES_DIR / f"scene_{scene_num:02d}{suffix}.png"
        if not path.exists() or path.stat().st_size < 10240:
            return False
    return bool(scenes)


def _build_prompts(scenario: dict, mode: str) -> list[str]:
    """Sahne prompt'larını (uzun videoda + thumbnail) hazırla."""
    from scripts.image_generator import _build_full_prompt
    from scripts.utils import read_prompt

    vertical = mode == "shorts"
    style_guide = read_prompt("image_style.txt")

    prompts = []
    for scene in scenario.get("scenes", []):
        visual = scene.get("visual_prompt", "")
        if visual:
            prompts.append(_build_full_prompt(visual, style_guide, vertical=vertical))

    # Uzun videoda son görsel: thumbnail arka planı
    if mode == "long":
        concept = scenario.get("thumbnail_concept", "") or (
            f"A dramatic, eye-catching scene for: {scenario.get('title', '')}"
        )
        prompts.append(
            f"{concept}\n"
            "Ultra dramatic, cinematic composition. Vivid saturated colors with extreme contrast. "
            "Golden hour or neon lighting, strong bokeh, depth of field. "
            "Photorealistic, 8K quality, epic scale. "
            "ABSOLUTELY NO text, NO watermarks, NO borders, NO letters. "
            "Clean background composition optimized for text overlay."
        )

    return prompts


def start_pending(topic: str, mode: str, scenario: dict, privacy: str = "public") -> bool:
    """
    Faz 1: Bekleyen üretimi kaydet ve prompt'ları Telegram'a gönder.

    Returns:
        bool: Prompt'lar gönderildi mi?
    """
    prompts = _build_prompts(scenario, mode)
    if not prompts:
        print_error("Senaryoda görsel promptu yok!")
        return False

    orientation = "9:16 DİKEY" if mode == "shorts" else "16:9 YATAY"
    kind = "Short" if mode == "shorts" else "uzun video"

    intro = (
        f"🎨 <b>Görsel zamanı!</b> Yeni {kind} hazır:\n"
        f"<i>{scenario.get('clickbait_title', scenario.get('title', topic))}</i>\n\n"
        f"Aşağıda {len(prompts)} görsel promptu göndereceğim. Her birini "
        f"Flow/Gemini'ye yapıştırıp <b>{orientation}</b> formatta üretin ve "
        f"çıkan görselleri <b>sırayla</b> bu sohbete gönderin.\n\n"
        f"Hepsi gelince videoyu otomatik tamamlayıp kanala yükleyeceğim. "
        f"Vazgeçmek için: /iptal"
    )
    if not send_message(intro):
        print_error("Telegram'a ulaşılamadı — manuel görsel akışı başlatılamadı.")
        return False

    for i, prompt in enumerate(prompts, 1):
        label = f"📸 Görsel {i}/{len(prompts)}"
        if mode == "long" and i == len(prompts):
            label += " (THUMBNAIL arka planı)"
        send_message(f"{label}:\n\n<code>{prompt[:3900]}</code>")

    _save_pending({
        "topic": topic,
        "mode": mode,
        "privacy": privacy,
        "scenario": scenario,
        "expected_images": len(prompts),
        "image_file_ids": [],
        "prompts_sent_at": datetime.now(timezone.utc).isoformat(),
        "last_reminder_at": datetime.now(timezone.utc).isoformat(),
    })

    print_success(f"{len(prompts)} görsel promptu Telegram'a gönderildi. Görseller bekleniyor.")
    logger.info("Manuel görsel akışı başladı: %s (%d görsel)", topic, len(prompts))
    return True


def add_photo(file_id: str) -> str:
    """
    Kullanıcıdan gelen fotoğrafı bekleyen üretime ekle.

    Returns:
        str: Kullanıcıya yanıt metni ("" ise sessiz kal)
    """
    pending = load_pending()
    if not pending:
        return ("📷 Fotoğraf aldım ama bekleyen bir video üretimi yok. "
                "/short veya /video ile üretim başlatabilirsiniz.")

    pending["image_file_ids"].append(file_id)
    _save_pending(pending)

    received = len(pending["image_file_ids"])
    expected = pending["expected_images"]

    if received < expected:
        return f"✅ Görsel {received}/{expected} alındı — {expected - received} görsel daha bekliyorum."
    if received == expected:
        return ""  # Tamamlama mesajını complete_production akışı yönetir
    return f"⚠️ Beklenenden fazla görsel geldi ({received}/{expected}) — fazlalıkları yok sayacağım."


def is_complete() -> bool:
    """Tüm görseller geldi mi?"""
    pending = load_pending()
    return bool(pending) and len(pending["image_file_ids"]) >= pending["expected_images"]


def send_reminder_if_due():
    """24 saatte bir eksik görselleri hatırlat."""
    pending = load_pending()
    if not pending:
        return

    try:
        last = datetime.fromisoformat(pending.get("last_reminder_at", ""))
    except ValueError:
        last = datetime.now(timezone.utc)

    hours_since = (datetime.now(timezone.utc) - last).total_seconds() / 3600
    if hours_since < REMINDER_INTERVAL_HOURS:
        return

    received = len(pending["image_file_ids"])
    expected = pending["expected_images"]
    send_message(
        f"⏰ <b>Hatırlatma:</b> \"{pending['topic']}\" videosu görsel bekliyor "
        f"({received}/{expected} geldi). Kalan görselleri gönderin veya /iptal yazın."
    )
    pending["last_reminder_at"] = datetime.now(timezone.utc).isoformat()
    _save_pending(pending)


def _download_telegram_photo(token: str, file_id: str) -> bytes | None:
    """Telegram'dan fotoğrafı indir."""
    try:
        r = requests.get(
            f"{TELEGRAM_API}/bot{token}/getFile",
            params={"file_id": file_id}, timeout=30,
        )
        file_path = r.json().get("result", {}).get("file_path")
        if not file_path:
            logger.warning("getFile başarısız: %s", r.text[:200])
            return None

        r = requests.get(
            f"{TELEGRAM_API}/file/bot{token}/{file_path}", timeout=120,
        )
        if r.status_code == 200:
            return r.content
        logger.warning("Fotoğraf indirme hatası (%d)", r.status_code)
    except Exception as e:
        logger.warning("Telegram fotoğraf indirme hatası: %s", e)
    return None


def center_crop_to_aspect(image_bytes: bytes, target_w: int, target_h: int) -> Image.Image:
    """Görseli hedef orana merkez-kırpıp yeniden boyutlandır."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    target_ratio = target_w / target_h
    ratio = w / h

    if ratio > target_ratio:
        # Çok geniş — yanlardan kırp
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    elif ratio < target_ratio:
        # Çok uzun — alt/üstten kırp
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))

    return img.resize((target_w, target_h), Image.LANCZOS)


def complete_production() -> bool:
    """
    Faz 2: Görselleri indir, cache dosyalarına yaz ve pipeline'ı tamamla.

    Returns:
        bool: Video başarıyla üretildi mi?
    """
    pending = load_pending()
    if not pending or not is_complete():
        return False

    topic = pending["topic"]
    mode = pending["mode"]
    scenario = pending["scenario"]
    vertical = mode == "shorts"

    keys = load_env()
    token = keys.get("TELEGRAM_BOT_TOKEN", "")

    send_message("🎬 Tüm görseller alındı — video üretimi başlıyor! (~5-10 dk)")
    logger.info("Manuel üretim tamamlanıyor: %s", topic)

    # 1) Senaryoyu pipeline cache'ine yaz (aynı sahnelerle devam edilsin)
    scenario["_topic"] = topic
    scenario["_mode"] = mode
    cache_name = "scenario_shorts.json" if vertical else "scenario.json"
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    save_json(scenario, TEMP_DIR / cache_name)

    # 2) Görselleri indir, kırp, sahne dosyalarına yaz
    target_w, target_h = (768, 1344) if vertical else (1344, 768)
    suffix = "_vertical" if vertical else ""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    scenes = scenario.get("scenes", [])
    scene_count = len(scenes)
    file_ids = pending["image_file_ids"][:pending["expected_images"]]

    thumbnail_path = None
    for i, file_id in enumerate(file_ids):
        data = _download_telegram_photo(token, file_id)
        if not data:
            # Sıra bozulmasın diye liste korunur; bir sonraki saatlik koşuda
            # baştan denenir (geçici Telegram hatalarında kendini toparlar)
            send_message(f"⚠️ Görsel {i + 1} indirilemedi — bir sonraki kontrolde tekrar deneyeceğim.")
            logger.warning("Manuel görsel indirme başarısız (sıra %d), sonraki koşuda denenecek.", i + 1)
            return False

        if i < scene_count:
            scene_num = scenes[i].get("scene_number", i + 1)
            out_path = IMAGES_DIR / f"scene_{scene_num:02d}{suffix}.png"
            center_crop_to_aspect(data, target_w, target_h).save(out_path, "PNG")
            logger.info("Manuel görsel kaydedildi: %s", out_path.name)
        else:
            # Uzun videoda fazladan gelen görsel = thumbnail arka planı
            from scripts.utils import THUMBNAILS_DIR
            THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
            thumbnail_path = THUMBNAILS_DIR / "thumbnail_raw.png"
            center_crop_to_aspect(data, 1344, 768).save(thumbnail_path, "PNG")
            logger.info("Manuel thumbnail arka planı kaydedildi.")

    # 3) Pipeline'ı çalıştır — senaryo + görseller cache'ten okunur.
    # resume=True ile çağrılır; aksi halde clean_temp() az önce yazdığımız
    # görselleri siler. Bunun için senaryo adımı tamamlanmış bir checkpoint kurulur.
    from main import run_pipeline
    from scripts.utils import PipelineCheckpoint

    checkpoint = PipelineCheckpoint()
    checkpoint.start(topic)
    checkpoint.data["mode"] = mode
    checkpoint.complete_step("scenario", episode_title=scenario.get("title", ""))

    # Uzun videolar bir sonraki optimal saate planlanır; Short'lar hemen yayınlanır
    publish_at = None
    if mode == "long":
        from scripts.youtube_uploader import next_optimal_publish_time
        publish_at = next_optimal_publish_time()

    try:
        result = run_pipeline(
            topic, resume=True, mode=mode,
            privacy=pending.get("privacy", "public"), publish_at=publish_at,
        )
    except Exception as e:
        logger.error("Manuel üretim pipeline hatası: %s", e)
        send_message(f"🚨 Video üretimi hatası: <code>{str(e)[:300]}</code>")
        return False

    if result:
        # Konu havuzunu güncelle
        from scripts.scheduler import mark_short_done, mark_topic_completed
        from scripts.utils import get_episode_number
        if vertical:
            mark_short_done(topic)
        else:
            mark_topic_completed(topic, get_episode_number() - 1)

        cancel_pending()
        return True

    send_message("🚨 Video üretimi başarısız oldu — loglara bakın. Görseller kayıtlı, /iptal ile sıfırlayabilirsiniz.")
    return False


def get_pending_status_text() -> str:
    """Bekleyen üretim özetini döndür (/durum için)."""
    pending = load_pending()
    if not pending:
        return ""
    received = len(pending["image_file_ids"])
    expected = pending["expected_images"]
    return (f"\n🎨 <b>Görsel bekleyen video:</b> {pending['topic'][:60]}\n"
            f"    📸 {received}/{expected} görsel geldi")
