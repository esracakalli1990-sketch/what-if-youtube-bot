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


def scene_asset_path(scene_num: int, vertical: bool) -> Path | None:
    """Sahne varlığının cache yolunu döndür (görsel .png veya video .mp4); yoksa None."""
    suffix = "_vertical" if vertical else ""
    img_path = IMAGES_DIR / f"scene_{scene_num:02d}{suffix}.png"
    vid_path = IMAGES_DIR / f"scene_{scene_num:02d}{suffix}.mp4"
    if img_path.exists() and img_path.stat().st_size >= 10240:
        return img_path
    if vid_path.exists() and vid_path.stat().st_size >= 10240:
        return vid_path
    return None


def images_ready(scenes: list[dict], vertical: bool) -> bool:
    """Tüm sahne varlıkları (görsel veya video) pipeline cache'inde hazır mı?"""
    for i, scene in enumerate(scenes):
        scene_num = scene.get("scene_number", i + 1)
        if scene_asset_path(scene_num, vertical) is None:
            return False
    return bool(scenes)


# Kısa karakter tarifi — sahnede tavşan geçiyorsa prompt'a eklenir
_CHARACTER_BRIEF = (
    "The character: a photorealistic anthropomorphic rabbit scientist, "
    "human-proportioned, warm grey fur with white chest, wearing a worn "
    "steampunk space suit with brass goggles on forehead and a leather satchel."
)


def _build_prompts(scenario: dict, mode: str) -> list[str]:
    """
    Sahne prompt'larını (uzun videoda + thumbnail) hazırla.

    Manuel akış için YALIN şablon: kullanıcı bunu Flow/Gemini'ye yapıştırır —
    API'ye özgü teknik satırlar (IP-Adapter vb.) eklenmez.
    """
    vertical = mode == "shorts"
    orientation = (
        "Vertical 9:16 portrait format, subject centered for mobile fullscreen."
        if vertical else "Widescreen 16:9 cinematic format."
    )
    base_style = (
        "Photorealistic, cinematic lighting, 8K detail, dramatic atmosphere. "
        "No text, no watermarks, no borders."
    )

    prompts = []
    for scene in scenario.get("scenes", []):
        visual = scene.get("visual_prompt", "").strip()
        if not visual:
            continue
        parts = [visual, orientation, base_style]
        if "rabbit" in visual.lower():
            parts.append(_CHARACTER_BRIEF)
        prompts.append("\n\n".join(parts))

    # Uzun videoda son görsel: thumbnail arka planı
    if mode == "long":
        concept = scenario.get("thumbnail_concept", "") or (
            f"A dramatic, eye-catching scene for: {scenario.get('title', '')}"
        )
        prompts.append(
            f"{concept}\n\n"
            "Widescreen 16:9 format. Ultra dramatic, vivid saturated colors with "
            "extreme contrast, golden hour or neon lighting, photorealistic, 8K. "
            "Absolutely no text or watermarks — clean composition for text overlay."
        )

    return prompts


def build_turkish_brief(scenario: dict) -> str:
    """
    Senaryodan Türkçe bilgi notu üret (Gemini ile çeviri/özet).

    Kullanıcının hangi videoyu ürettiğini ve her sahnenin/görselin ne anlattığını
    Türkçe bilmesini sağlar. Gemini erişilemezse boş string döner (not atlanır).
    """
    from google import genai
    from scripts.scenario_generator import _call_gemini

    keys = load_env()
    api_key = keys.get("GEMINI_API_KEY", "")
    if not api_key or "buraya" in api_key:
        return ""

    scenes = scenario.get("scenes", [])
    if not scenes:
        return ""

    title = scenario.get("clickbait_title", scenario.get("title", ""))
    scene_texts = "\n".join(
        f"Scene {i + 1}: {s.get('narration', '')}" for i, s in enumerate(scenes)
    )

    system_prompt = (
        "You translate and summarize a video script into TURKISH so the channel "
        "owner knows what each scene is about. Output ONLY valid JSON, no extra text."
    )
    user_prompt = f"""Summarize this video in Turkish for the channel owner.

TITLE: {title}

SCENES:
{scene_texts}

Output valid JSON exactly in this shape:
{{
  "konu": "Videonun ana konusu tek cümlede, Türkçe",
  "sahneler": ["1. sahnede ne anlatılıyor - kısa Türkçe", "2. sahne...", ...]
}}
Rules: one 'sahneler' entry per scene, each max 15 Turkish words, plain and clear."""

    try:
        client = genai.Client(api_key=api_key)
        result = _call_gemini(client, system_prompt, user_prompt, temperature=0.3)
    except Exception as e:
        logger.warning("Türkçe bilgi notu üretilemedi: %s", e)
        return ""

    if not isinstance(result, dict):
        return ""

    konu = result.get("konu", "").strip()
    sahneler = result.get("sahneler", [])

    nums = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]
    lines = ["📋 <b>BU VİDEO NE ANLATIYOR?</b> (Türkçe bilgi notu)", ""]
    if konu:
        lines.append(f"🎬 <b>Konu:</b> {konu}")
    lines.append(f"📌 <b>Başlık:</b> {title}")
    lines.append("")
    lines.append("<b>Görsel → Sahne eşleşmesi:</b>")
    for i, s in enumerate(sahneler):
        marker = nums[i] if i < len(nums) else f"{i + 1}."
        lines.append(f"{marker} <b>Görsel {i + 1}:</b> {s}")
    lines.append("")
    lines.append("💡 Böylece her görselin hangi sahneye ait olduğunu bilerek üretebilir, "
                 "sonucu karşılaştırabilirsiniz.")

    return "\n".join(lines)


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

    # Türkçe bilgi notu — kullanıcı ne ürettiğini bilerek görselleri hazırlasın
    brief = build_turkish_brief(scenario)
    if brief:
        send_message(brief)

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
        "asset_kinds": [],
        "prompts_sent_at": datetime.now(timezone.utc).isoformat(),
        "last_reminder_at": datetime.now(timezone.utc).isoformat(),
    })

    print_success(f"{len(prompts)} görsel promptu Telegram'a gönderildi. Görseller bekleniyor.")
    logger.info("Manuel görsel akışı başladı: %s (%d görsel)", topic, len(prompts))
    return True


def _add_asset(file_id: str, kind: str) -> str:
    """
    Kullanıcıdan gelen varlığı (foto/video) bekleyen üretime ekle.

    Args:
        file_id: Telegram dosya kimliği
        kind: "photo" veya "video"

    Returns:
        str: Kullanıcıya yanıt metni ("" ise sessiz kal)
    """
    noun = "video" if kind == "video" else "görsel"
    pending = load_pending()
    if not pending:
        return (f"📷 {noun.capitalize()} aldım ama bekleyen bir video üretimi yok. "
                "/short veya /video ile üretim başlatabilirsiniz.")

    pending["image_file_ids"].append(file_id)
    # Varlık türünü pozisyonla eşleşecek şekilde kaydet (indirmede foto/video ayrımı için)
    pending.setdefault("asset_kinds", []).append(kind)
    _save_pending(pending)

    received = len(pending["image_file_ids"])
    expected = pending["expected_images"]

    if received < expected:
        return f"✅ Dosya {received}/{expected} alındı — {expected - received} dosya daha bekliyorum."
    if received == expected:
        return ""  # Tamamlama mesajını complete_production akışı yönetir
    return f"⚠️ Beklenenden fazla dosya geldi ({received}/{expected}) — fazlalıkları yok sayacağım."


def add_photo(file_id: str) -> str:
    """Kullanıcıdan gelen fotoğrafı bekleyen üretime ekle."""
    return _add_asset(file_id, "photo")


def add_video(file_id: str) -> str:
    """Kullanıcıdan gelen video klibini bekleyen üretime ekle."""
    return _add_asset(file_id, "video")


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


def _download_telegram_file(token: str, file_id: str) -> bytes | None:
    """Telegram'dan dosyayı indir (foto veya video)."""
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
    asset_kinds = pending.get("asset_kinds") or []

    thumbnail_path = None
    for i, file_id in enumerate(file_ids):
        kind = asset_kinds[i] if i < len(asset_kinds) else "photo"
        data = _download_telegram_file(token, file_id)
        if not data:
            # Sıra bozulmasın diye liste korunur; bir sonraki saatlik koşuda
            # baştan denenir (geçici Telegram hatalarında kendini toparlar)
            send_message(f"⚠️ Dosya {i + 1} indirilemedi — bir sonraki kontrolde tekrar deneyeceğim.")
            logger.warning("Manuel varlık indirme başarısız (sıra %d), sonraki koşuda denenecek.", i + 1)
            return False

        if i < scene_count:
            scene_num = scenes[i].get("scene_number", i + 1)
            png_path = IMAGES_DIR / f"scene_{scene_num:02d}{suffix}.png"
            mp4_path = IMAGES_DIR / f"scene_{scene_num:02d}{suffix}.mp4"
            if kind == "video":
                # Video klip: ham kaydet (montaj ölçekleme/kırpmayı kendi yapıyor)
                mp4_path.write_bytes(data)
                if png_path.exists():
                    png_path.unlink()  # Aynı sahnenin eski görseli varsa temizle
                logger.info("Manuel video klip kaydedildi: %s", mp4_path.name)
            else:
                center_crop_to_aspect(data, target_w, target_h).save(png_path, "PNG")
                if mp4_path.exists():
                    mp4_path.unlink()  # Aynı sahnenin eski videosu varsa temizle
                logger.info("Manuel görsel kaydedildi: %s", png_path.name)
        elif kind != "video":
            # Uzun videoda fazladan gelen görsel = thumbnail arka planı
            from scripts.utils import THUMBNAILS_DIR
            THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
            thumbnail_path = THUMBNAILS_DIR / "thumbnail_raw.png"
            center_crop_to_aspect(data, 1344, 768).save(thumbnail_path, "PNG")
            logger.info("Manuel thumbnail arka planı kaydedildi.")
        else:
            # Thumbnail slotuna video gelmesi beklenmez — atla, thumbnail fallback devrede
            logger.warning("Thumbnail slotuna video geldi, atlandı (sıra %d).", i + 1)

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
