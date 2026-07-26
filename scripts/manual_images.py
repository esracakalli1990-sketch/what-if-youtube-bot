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

# Yükleme bu kadar kez başarısız olursa üretim DURAKLATILIR (döngü kırıcı).
# Auth hatası (token süresi dolmuş vb.) tek denemede duraklatır — tekrar
# denemek işe yaramaz. Böylece video her saat boşuna yeniden üretilmez.
MAX_UPLOAD_RETRIES = 2


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


# Kanonik karakter tarifi — sahnede Roli geçiyorsa prompt'a eklenir.
# Roli kanalın markası; bu tarif HER videoda birebir aynı görünmesini sağlar
# (parlayan mavi cep saati = imza aksesuar / marka çıpası).
_CHARACTER_BRIEF = (
    "The character 'Roli' (keep this EXACT design every time): a photorealistic "
    "anthropomorphic rabbit scientist, human-proportioned, warm grey fur with a "
    "white chest and amber eyes, one ear slightly bent. He wears a worn "
    "brass-and-leather steampunk spacesuit with goggles pushed up on his "
    "forehead, and carries a glowing blue pocket-watch (his time-travel device) "
    "clipped to his belt."
)


def _build_prompts(scenario: dict, mode: str) -> tuple[list[str], list[str]]:
    """
    Sahne prompt'larını (uzun videoda + thumbnail) hazırla.

    Manuel akış için YALIN şablon: kullanıcı bunu Flow/Gemini'ye yapıştırır —
    API'ye özgü teknik satırlar (IP-Adapter vb.) eklenmez.

    Returns:
        tuple: (prompt listesi, tür listesi) — tür "video" veya "photo",
        pozisyonlar birebir eşleşir. Thumbnail her zaman "photo".
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
    kinds = []
    for scene in scenario.get("scenes", []):
        visual = scene.get("visual_prompt", "").strip()
        if not visual:
            continue

        if scene.get("asset_type") == "video":
            from scripts.scenario_generator import mentions_character
            if mentions_character(visual):
                # Roli'li video klip (short'ta Roli de video). Karakter DAHİL,
                # tutarlı tasarım + doğal karakter hareketi.
                prompts.append(
                    f"{visual}\n\n"
                    "FULL 10 SECOND VIDEO CLIP featuring the character (make it "
                    "the maximum ~10 seconds — it must be at least as long as the "
                    "narration so it never freezes). Subtle natural character "
                    "motion (breathing, a small gesture, a glance at the camera) "
                    "with gentle cinematic camera movement that keeps evolving for "
                    "the whole 10 seconds.\n\n"
                    "CRITICAL — THE CHARACTER MUST NOT SPEAK: his mouth stays "
                    "CLOSED the entire clip. No talking, no lip movement, no "
                    "mouth opening, no dialogue. The voice-over narration is added "
                    "separately in editing, so any lip movement would be out of "
                    "sync and look like bad dubbing. He communicates only through "
                    "his eyes, posture and a small hand gesture — a silent, "
                    f"knowing presence. {orientation}\n\n{base_style}\n\n{_CHARACTER_BRIEF}"
                )
            else:
                # Atmosfer/olay video klibi — karakter yok, hareket odaklı.
                prompts.append(
                    f"{visual}\n\n"
                    "FULL 10 SECOND VIDEO CLIP (make it the maximum ~10 seconds — "
                    "it must be at least as long as the narration so it never "
                    "freezes). Cinematic camera motion with continuous natural "
                    "movement throughout the whole 10 seconds — drifting particles, "
                    "flowing light, shifting atmosphere. Environment/phenomenon "
                    f"only, NO characters or people in the frame. {orientation}"
                    f"\n\n{base_style}"
                )
            kinds.append("video")
        else:
            parts = [visual, orientation, base_style]
            from scripts.scenario_generator import mentions_character
            if mentions_character(visual):
                parts.append(_CHARACTER_BRIEF)
            prompts.append("\n\n".join(parts))
            kinds.append("photo")

    # Uzun videoda son görsel: thumbnail arka planı (her zaman görsel)
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
        kinds.append("photo")

    return prompts, kinds


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
    lines.append("<b>Sahne eşleşmesi:</b>")
    for i, s in enumerate(sahneler):
        marker = nums[i] if i < len(nums) else f"{i + 1}."
        asset = scenes[i].get("asset_type", "image") if i < len(scenes) else "image"
        tur = "🎬 VİDEO" if asset == "video" else "🖼 GÖRSEL"
        lines.append(f"{marker} <b>{tur} {i + 1}:</b> {s}")
    lines.append("")
    lines.append("💡 Her üretimin hangi sahneye ait olduğunu ve video mu görsel mi "
                 "olacağını böylece bilerek hazırlayabilirsiniz.")

    return "\n".join(lines)


def start_pending(topic: str, mode: str, scenario: dict, privacy: str = "public") -> bool:
    """
    Faz 1: Bekleyen üretimi kaydet ve prompt'ları Telegram'a gönder.

    Returns:
        bool: Prompt'lar gönderildi mi?
    """
    prompts, kinds = _build_prompts(scenario, mode)
    if not prompts:
        print_error("Senaryoda görsel promptu yok!")
        return False

    orientation = "9:16 DİKEY" if mode == "shorts" else "16:9 YATAY"
    kind = "Short" if mode == "shorts" else "uzun video"
    video_count = kinds.count("video")

    video_note = ""
    if video_count:
        video_note = (
            f"\n\n🎬 Bunların <b>{video_count} tanesi VİDEO</b> — her birini "
            f"<b>tam ~10 saniye</b> yapın (yapabildiğiniz en uzun süre). "
            f"⚠️ Klip anlatımdan kısa olursa son kare 1-2 sn donar; 10 sn "
            f"yaparsanız donma olmaz. Kalanı GÖRSEL. Her mesajda hangisi olduğu "
            f"yazacak — video isteyenleri Flow'da <b>video</b>, görsel "
            f"isteyenleri <b>görsel</b> olarak üretip <b>sırayla</b> gönderin."
        )

    intro = (
        f"🎨 <b>Üretim zamanı!</b> Yeni {kind} hazır:\n"
        f"<i>{scenario.get('clickbait_title', scenario.get('title', topic))}</i>\n\n"
        f"Aşağıda {len(prompts)} prompt göndereceğim. Her birini "
        f"Flow/Gemini'ye yapıştırıp <b>{orientation}</b> formatta üretin ve "
        f"çıktıları <b>sırayla</b> bu sohbete gönderin.{video_note}\n\n"
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

    for i, (prompt, kind_i) in enumerate(zip(prompts, kinds), 1):
        if kind_i == "video":
            label = f"🎬 VİDEO {i}/{len(prompts)} (tam ~10 sn klip)"
        else:
            label = f"🖼 GÖRSEL {i}/{len(prompts)}"
        if mode == "long" and i == len(prompts):
            label = f"🖼 GÖRSEL {i}/{len(prompts)} (THUMBNAIL arka planı)"
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

    # Duraklatılmış üretim için görsel-hatırlatması gönderme (görseller zaten
    # gelmiş, sorun yüklemede) — ayrı bir duraklatma mesajı zaten atıldı.
    if pending.get("paused"):
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

    # DÖNGÜ KIRICI: üretim duraklatıldıysa (tekrarlanan yükleme hatası) otomatik
    # tekrar deneme — kullanıcı sorunu çözüp /devam yazana kadar bekle. Bu,
    # videonun her saat boşuna yeniden üretilmesini (kota/dakika yangını) önler.
    if pending.get("paused"):
        logger.info("Üretim duraklatılmış, otomatik tekrar atlanıyor: %s",
                    pending.get("topic"))
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

    # "images" adımını da tamamlanmış işaretle. Manuel modda görseller/videolar
    # zaten kaydedildi; işaretlenmezse main.py ücretli API'yi (generate_images)
    # tekrar çağırır — o da yalnızca .png'yi "cached" sayıp .mp4 (video) sahnelerini
    # tanımadığı için API'yi dener, kota/limit hatası alır ve o sahneler videodan
    # tamamen düşer. (İlk hibrit üretimde tam bu yüzden 4 video sahnesi kayboldu.)
    image_results = []
    for i, scene in enumerate(scenes):
        scene_num = scene.get("scene_number", i + 1)
        asset_path = scene_asset_path(scene_num, vertical)
        if asset_path:
            image_results.append({"scene_number": scene_num, "image_path": str(asset_path)})
    checkpoint.complete_step("images", image_results=image_results)

    # Uzun ve Short videolar HEMEN public yayınlanır. Daha önce uzun videolar
    # "bir sonraki optimal saate" planlanıyordu; bu, videoyu publishAt'e kadar
    # private tutuyordu ve otoritesiz (yeni) bir kanalda YouTube videoyu hiç
    # dağıtıma sokmadan bekletiyordu (canlı veride 0 gösterim'in sebebi buydu).
    # Artık video anında dağıtım sistemine girsin diye planlama kaldırıldı.
    publish_at = None

    # notify_on_upload_fail=False: yükleme-hatası mesajını burada (döngü kırıcı)
    # yönetiyoruz; run_pipeline'ın her saat tekrarlanan bildirimini bastırıyoruz.
    try:
        result = run_pipeline(
            topic, resume=True, mode=mode,
            privacy="public", publish_at=publish_at,
            notify_on_upload_fail=False,
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

    # Başarısız — üretim mi patladı, yükleme mi? (döngü kırıcı ayrımı)
    from scripts import youtube_uploader
    up_err = youtube_uploader.last_upload_error()

    if up_err.get("message"):
        # Video ÜRETİLDİ ama YÜKLEME patladı. Konu 'tamamlandı' sayılmadı.
        failures = int(pending.get("upload_failures", 0)) + 1
        pending["upload_failures"] = failures
        pending["last_upload_error"] = up_err["message"][:200]
        _save_pending(pending)

        if up_err.get("auth"):
            # Kimlik/yetki hatası: tekrar denemek çözmez → HEMEN duraklat.
            _pause_pending(
                pending,
                "⏸️ <b>Üretim duraklatıldı — YouTube yetkisi geçersiz.</b>\n\n"
                "Video üretildi ama yüklenemedi: giriş anahtarının süresi dolmuş "
                "veya iptal edilmiş (<code>invalid_grant</code>). Her saat boşuna "
                "yeniden üretmeyi <b>durdurdum</b>.\n\n"
                "🔧 Yeniden yetkilendirdikten sonra <b>/devam</b> yazın — videoyu "
                "yeniden üretip yükleyeceğim. Vazgeçmek için /iptal.",
            )
            return False

        if failures >= MAX_UPLOAD_RETRIES:
            _pause_pending(
                pending,
                f"⏸️ <b>Üretim duraklatıldı</b> — yükleme {failures} kez başarısız "
                f"oldu.\n\n<code>{up_err['message'][:150]}</code>\n\n"
                "Her saat tekrar denemeyi durdurdum. Sorun çözülünce <b>/devam</b> "
                "yazın, yeniden deneyeceğim. Vazgeçmek için /iptal.",
            )
            return False

        # Geçici olabilir — sınırlı sayıda bir sonraki saatlik koşuda tekrar dene.
        send_message(
            f"⚠️ Video üretildi ama yükleme başarısız ({failures}/{MAX_UPLOAD_RETRIES}) "
            "— bir sonraki kontrolde tekrar deneyeceğim."
        )
        return False

    # Gerçek üretim hatası (yükleme aşamasına hiç gelinemedi).
    send_message("🚨 Video üretimi başarısız oldu — loglara bakın. Görseller "
                 "kayıtlı, /iptal ile sıfırlayabilirsiniz.")
    return False


def _pause_pending(pending: dict, message: str):
    """Bekleyen üretimi duraklat (otomatik tekrar durur) ve tek mesaj gönder."""
    pending["paused"] = True
    _save_pending(pending)
    send_message(message)
    logger.warning("Üretim duraklatıldı: %s (yükleme hatası)", pending.get("topic"))


def resume_pending() -> str:
    """
    Duraklatılmış üretimi sürdür (/devam). Sayaç sıfırlanır; bir sonraki
    saatlik kontrolde video yeniden üretilip yüklenmeyi dener.
    """
    pending = load_pending()
    if not pending:
        return "Sürdürülecek bekleyen üretim yok."
    if not pending.get("paused"):
        return "Bekleyen üretim zaten aktif — sıradaki kontrolde denenecek."
    pending["paused"] = False
    pending["upload_failures"] = 0
    _save_pending(pending)
    logger.info("Üretim sürdürüldü (/devam): %s", pending.get("topic"))
    return ("▶️ <b>Üretim sürdürülüyor.</b> Bir sonraki saatlik kontrolde videoyu "
            "yeniden üretip yüklemeyi deneyeceğim. (Görseller kayıtlı; yeniden "
            "göndermenize gerek yok.)")


def get_pending_status_text() -> str:
    """Bekleyen üretim özetini döndür (/durum için)."""
    pending = load_pending()
    if not pending:
        return ""
    received = len(pending["image_file_ids"])
    expected = pending["expected_images"]
    return (f"\n🎨 <b>Görsel bekleyen video:</b> {pending['topic'][:60]}\n"
            f"    📸 {received}/{expected} görsel geldi")
