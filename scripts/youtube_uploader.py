"""
youtube_uploader.py - YouTube Data API v3 ile Otomatik Video Yükleme.

Üretilen videoları otomatik olarak YouTube'a yükler.
OAuth 2.0 kimlik doğrulaması kullanır.

Özellikler:
- Video yükleme (başlık, açıklama, etiketler otomatik)
- Thumbnail yükleme
- Planlı yayın (scheduled publish)
- Oynatma listesine ekleme
- Retry mekanizması (resumable upload)

İlk Kurulum:
1. Google Cloud Console'da proje oluştur
2. YouTube Data API v3'ü etkinleştir
3. OAuth 2.0 client ID oluştur (Desktop App)
4. client_secrets.json dosyasını proje kök dizinine kaydet
5. python scripts/youtube_uploader.py --auth  (ilk kez çalıştır, tarayıcıda yetkilendir)
"""

import os
import sys
import json
import time
import pickle
import httplib2
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Doğrudan çalıştırma desteği: python scripts/youtube_uploader.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils import (
    print_header, print_step, print_success, print_error,
    print_warning, console, logger, PROJECT_ROOT, OUTPUT_DIR
)

# Google API bağımlılıkları — lazy import (kurulu olmayabilir)
GOOGLE_API_AVAILABLE = False
try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    GOOGLE_API_AVAILABLE = True
except ImportError:
    pass

# OAuth konfigürasyon
CLIENT_SECRETS_FILE = PROJECT_ROOT / "client_secrets.json"
TOKEN_FILE = PROJECT_ROOT / "youtube_token.pickle"
# NOT: force-ssl scope'u yorum atabilmek için gerekli. Scope değiştiği için
# mevcut token'ı silip yeniden yetkilendirme gerekir: python scripts/youtube_uploader.py --auth
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube",
          "https://www.googleapis.com/auth/youtube.force-ssl"]

# Yükleme kaydı — analytics geri besleme döngüsünün veri kaynağı
UPLOADS_FILE = OUTPUT_DIR / "uploads.json"

# YouTube kategori ID'leri
CATEGORY_IDS = {
    "science": "28",
    "education": "27",
    "entertainment": "24",
    "howto": "26",
}

# Varsayılan video ayarları
DEFAULT_TAGS = [
    "what if", "science", "documentary", "thought experiment",
    "education", "what would happen", "science explained",
    "what if scenario", "mind blowing", "kurzgesagt",
]


def record_upload(video_id: str, title: str, kind: str = "long", privacy: str = "private"):
    """Yüklenen videoyu output/uploads.json kaydına ekle (analytics için)."""
    records = []
    if UPLOADS_FILE.exists():
        try:
            with open(UPLOADS_FILE, "r", encoding="utf-8") as f:
                records = json.load(f)
        except (json.JSONDecodeError, IOError):
            records = []

    records.append({
        "video_id": video_id,
        "title": title,
        "kind": kind,  # "long" | "short"
        "privacy": privacy,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    })

    UPLOADS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(UPLOADS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    logger.info("Yükleme kaydedildi: %s (%s)", video_id, kind)


def load_uploads() -> list[dict]:
    """uploads.json kayıtlarını oku."""
    if not UPLOADS_FILE.exists():
        return []
    try:
        with open(UPLOADS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def next_optimal_publish_time(hour_utc: int = 15) -> datetime:
    """
    Bir sonraki optimal yayın zamanını döndür (varsayılan 15:00 UTC —
    ABD sabahı + Avrupa akşamı kesişimi). En az 1 saat ileride olması garanti.
    """
    now = datetime.now(timezone.utc)
    candidate = now.replace(hour=hour_utc, minute=0, second=0, microsecond=0)
    while candidate <= now + timedelta(hours=1):
        candidate += timedelta(days=1)
    return candidate


def check_youtube_setup() -> dict:
    """
    YouTube API kurulumunu kontrol et.

    Returns:
        dict: {"api_available": bool, "secrets_exist": bool, "authenticated": bool}
    """
    status = {
        "api_available": GOOGLE_API_AVAILABLE,
        "secrets_exist": CLIENT_SECRETS_FILE.exists(),
        "authenticated": TOKEN_FILE.exists(),
    }

    if not GOOGLE_API_AVAILABLE:
        logger.warning("YouTube API paketleri kurulu değil.")
    if not CLIENT_SECRETS_FILE.exists():
        logger.warning("client_secrets.json bulunamadı: %s", CLIENT_SECRETS_FILE)
    if not TOKEN_FILE.exists():
        logger.info("YouTube token yok, yetkilendirme gerekli.")

    return status


def authenticate() -> object | None:
    """
    YouTube API için OAuth 2.0 kimlik doğrulaması yap.

    Returns:
        Yetkilendirilmiş credentials objesi veya None
    """
    if not GOOGLE_API_AVAILABLE:
        print_error("YouTube API paketleri kurulu değil!")
        print_error("Kurun: pip install google-api-python-client google-auth-oauthlib")
        return None

    if not CLIENT_SECRETS_FILE.exists():
        print_error(f"client_secrets.json bulunamadı: {CLIENT_SECRETS_FILE}")
        print_error("Google Cloud Console'dan OAuth 2.0 Client ID oluşturup indirin.")
        print_error("  → https://console.cloud.google.com/apis/credentials")
        return None

    credentials = None

    # Mevcut token'ı yükle
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, "rb") as f:
                credentials = pickle.load(f)
        except Exception:
            pass

    # Token geçersiz veya süresi dolmuş — yenile
    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            logger.info("YouTube token yenilendi.")
        except Exception as e:
            logger.warning("Token yenileme başarısız: %s", e)
            credentials = None

    # Yeni yetkilendirme gerekli
    if not credentials or not credentials.valid:
        # CI/otomasyon ortamında tarayıcı açılamaz — asılı kalmak yerine hata ver
        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
            print_error("Token geçersiz ve CI ortamında interaktif yetkilendirme yapılamaz.")
            print_error("Lokal makinede --auth çalıştırıp YOUTUBE_TOKEN_B64 secret'ını güncelleyin.")
            return None
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRETS_FILE), SCOPES
            )
            credentials = flow.run_local_server(port=8080, open_browser=True)
            logger.info("YouTube yetkilendirme başarılı.")
        except Exception as e:
            print_error(f"YouTube yetkilendirme hatası: {e}")
            return None

    # Token'ı kaydet
    try:
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(credentials, f)
        logger.info("YouTube token kaydedildi: %s", TOKEN_FILE)
    except Exception as e:
        logger.warning("Token kaydetme hatası: %s", e)

    return credentials


# YouTube'un gerçek kısıtı: etiket SAYISI değil, TÜM etiketlerin toplam
# karakter uzunluğu (500'ü aşarsa API "invalidTags" ile reddeder).
YOUTUBE_TAGS_MAX_CHARS = 500


def _sanitize_tags(tags: list[str]) -> list[str]:
    """
    Etiketleri YouTube API kurallarına uygun hale getir:
    - Boş/geçersiz karakterli (< >) etiketler atılır
    - Tekrarlar temizlenir (büyük/küçük harf duyarsız)
    - Toplam karakter uzunluğu YOUTUBE_TAGS_MAX_CHARS'ı aşmayacak şekilde kesilir
    """
    seen = set()
    unique_tags = []
    for t in tags:
        t = t.strip()
        if not t or "<" in t or ">" in t:
            continue
        if t.lower() not in seen:
            seen.add(t.lower())
            unique_tags.append(t)

    result = []
    total_len = 0
    for t in unique_tags:
        total_len += len(t) + 1  # etiketler arası ayraç payı
        if total_len > YOUTUBE_TAGS_MAX_CHARS:
            break
        result.append(t)
    return result


def upload_video(
    video_path: str,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    category: str = "science",
    privacy: str = "private",
    thumbnail_path: str | None = None,
    publish_at: datetime | None = None,
    playlist_id: str | None = None,
    scenario: dict | None = None,
    audio_results: list[dict] | None = None,
    is_short: bool = False,
) -> str | None:
    """
    Videoyu YouTube'a yükle.

    Args:
        video_path: Video dosya yolu
        title: Video başlığı
        description: Video açıklaması
        tags: Etiketler (None ise varsayılan kullanılır)
        category: Kategori (science, education, entertainment)
        privacy: Gizlilik (private, unlisted, public)
        thumbnail_path: Thumbnail dosya yolu (opsiyonel)
        publish_at: Planlı yayın tarihi (opsiyonel)
        playlist_id: Eklenecek oynatma listesi ID'si (opsiyonel)
        is_short: True ise YouTube Shorts (başlık/açıklamaya #Shorts eklenir)

    Returns:
        str | None: YouTube video ID'si veya None
    """
    print_header("📤 YOUTUBE YÜKLEME" + (" — SHORTS" if is_short else ""))

    if not GOOGLE_API_AVAILABLE:
        print_error("YouTube API paketleri kurulu değil!")
        print_error("Kurun: pip install google-api-python-client google-auth-oauthlib")
        return None

    # Video dosyası kontrolü
    video_file = Path(video_path)
    if not video_file.exists():
        print_error(f"Video dosyası bulunamadı: {video_path}")
        return None

    size_mb = video_file.stat().st_size / (1024 * 1024)
    console.print(f"  📹 Video: {video_file.name} ({size_mb:.1f} MB)")

    # Kimlik doğrulama
    print_step(1, "YouTube kimlik doğrulama...")
    credentials = authenticate()
    if not credentials:
        return None

    # YouTube API istemcisi
    youtube = build("youtube", "v3", credentials=credentials)

    # Video metadata — senaryo verisi varsa SEO-optimize et
    if scenario:
        # Clickbait başlık
        if scenario.get("clickbait_title"):
            title = scenario["clickbait_title"]
        # Konu-spesifik etiketler
        if scenario.get("youtube_tags"):
            tags = scenario["youtube_tags"] + DEFAULT_TAGS

    if tags is None:
        tags = DEFAULT_TAGS.copy()

    tags = _sanitize_tags(tags)

    category_id = CATEGORY_IDS.get(category, "28")

    # Açıklama şablonu — SEO-optimize
    if not description:
        seo_desc = scenario.get("seo_description", "") if scenario else ""
        description = _generate_description(title, tags, seo_desc, audio_results)

    # Shorts: #Shorts hashtag'i keşif için kritik (dikey + ≤60sn video otomatik Short sayılır)
    if is_short:
        if "#shorts" not in title.lower() and len(title) <= 91:
            title = f"{title} #Shorts"
        if "#shorts" not in description.lower():
            description = f"{description}\n#Shorts"
        if "shorts" not in [t.lower() for t in tags]:
            tags = _sanitize_tags(["shorts"] + tags)

    body = {
        "snippet": {
            "title": title[:100],  # YouTube max 100 karakter
            "description": description[:5000],  # YouTube max 5000
            "tags": tags,  # Toplam karakter uzunluğu _sanitize_tags'ta sınırlanır
            "categoryId": category_id,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    # Planlı yayın — YouTube kuralı gereği video private yüklenir, zamanı gelince yayınlanır
    if publish_at:
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = publish_at.isoformat()
        console.print(f"  📅 Planlı yayın: {publish_at.strftime('%Y-%m-%d %H:%M %Z')}")

    # Yükleme
    print_step(2, "Video yükleniyor...")
    logger.info("YouTube yükleme başlıyor: %s (%.1f MB)", title, size_mb)

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=10 * 1024 * 1024,  # 10MB chunks
    )

    try:
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        video_id = None
        response = None

        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                console.print(f"\r  📤 Yükleniyor: {progress}%", end="")

        video_id = response["id"]
        console.print()
        print_success(f"Video yüklendi! ID: {video_id}")
        console.print(f"  🔗 https://youtu.be/{video_id}")
        logger.info("Video yüklendi: https://youtu.be/%s", video_id)

        # Yükleme kaydı (analytics geri beslemesi için)
        record_upload(video_id, title, kind="short" if is_short else "long", privacy=privacy)

        # Thumbnail yükle
        if thumbnail_path and Path(thumbnail_path).exists():
            print_step(3, "Thumbnail yükleniyor...")
            _upload_thumbnail(youtube, video_id, thumbnail_path)

        # Oynatma listesine ekle (.env'deki YOUTUBE_PLAYLIST_ID varsayılan)
        if not playlist_id:
            from scripts.utils import load_env
            playlist_id = load_env().get("YOUTUBE_PLAYLIST_ID", "").strip() or None
        if playlist_id and not is_short:
            print_step(4, "Oynatma listesine ekleniyor...")
            _add_to_playlist(youtube, video_id, playlist_id)

        # Etkileşim yorumu — yayınlanmış videolarda ilk yorumu at
        # (private videoya yorum atılamaz; planlı yayında da atlanır)
        if privacy in ("public", "unlisted") and "publishAt" not in body["status"]:
            _post_first_comment(youtube, video_id, scenario)

        return video_id

    except HttpError as e:
        print_error(f"YouTube API hatası: {e}")
        logger.error("YouTube yükleme hatası: %s", e)
        return None
    except Exception as e:
        print_error(f"Yükleme hatası: {e}")
        logger.error("YouTube yükleme hatası: %s", e)
        return None


def _upload_thumbnail(youtube, video_id: str, thumbnail_path: str):
    """Thumbnail yükle."""
    try:
        media = MediaFileUpload(thumbnail_path, mimetype="image/png")
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=media,
        ).execute()
        print_success("Thumbnail yüklendi!")
        logger.info("Thumbnail yüklendi: video=%s", video_id)
    except Exception as e:
        print_warning(f"Thumbnail yükleme hatası: {e}")
        logger.warning("Thumbnail yükleme hatası: %s", e)


def _post_first_comment(youtube, video_id: str, scenario: dict | None = None):
    """
    Videoya etkileşim odaklı ilk yorumu at.

    İlk yorum algoritma için erken etkileşim sinyali üretir; kanal sahibi
    YouTube Studio'dan bu yorumu sabitleyebilir.
    """
    question = None
    if scenario:
        # Senaryonun outro'daki merak tohumunu kullanmayı dene
        scenes = scenario.get("scenes", [])
        if scenes:
            question = scenes[-1].get("twist_element")

    comment_text = (
        f"🐰 {question}\n\n" if question else "🐰 "
    ) + "What \"What If\" scenario should we explore next? Drop it below 👇"

    try:
        youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {"textOriginal": comment_text}
                    },
                }
            },
        ).execute()
        print_success("İlk yorum atıldı (Studio'dan sabitleyebilirsiniz).")
        logger.info("İlk yorum atıldı: video=%s", video_id)
    except Exception as e:
        print_warning(f"İlk yorum atılamadı: {e}")
        logger.warning("İlk yorum hatası (scope için --auth ile yeniden yetkilendirme gerekebilir): %s", e)


def _add_to_playlist(youtube, video_id: str, playlist_id: str):
    """Videoyu oynatma listesine ekle."""
    try:
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id,
                    },
                },
            },
        ).execute()
        print_success("Oynatma listesine eklendi!")
        logger.info("Playlist'e eklendi: video=%s, playlist=%s", video_id, playlist_id)
    except Exception as e:
        print_warning(f"Playlist ekleme hatası: {e}")
        logger.warning("Playlist ekleme hatası: %s", e)


def _generate_description(
    title: str,
    tags: list[str],
    seo_description: str = "",
    audio_results: list[dict] | None = None,
) -> str:
    """SEO-optimize YouTube açıklaması oluştur."""
    hashtags = " ".join(f"#{tag.replace(' ', '')}" for tag in tags[:8])

    # SEO ilk 2 satır — arama sonuçlarında görünür
    seo_intro = seo_description if seo_description else (
        f"{title} — What would REALLY happen? Our time-traveling rabbit scientist "
        f"reveals the shocking truth in this mind-bending science documentary."
    )

    # Gerçek timestamp'ları hesapla
    timestamps = _generate_timestamps(audio_results)

    return f"""{seo_intro}

🐰 Welcome to another mind-bending journey through the impossible!
Our time-traveling rabbit scientist takes you on an epic exploration of one of the most fascinating "What If" scenarios ever imagined.

⏰ Timestamps:
{timestamps}

🔬 This video explores real scientific concepts through creative storytelling.
All scenarios are based on actual physics and scientific research.

👍 Like & Subscribe for more "What If" adventures!
🔔 Turn on notifications to never miss an episode!
💬 What "What If" scenario should we explore next? Tell us in the comments!

{hashtags}

#WhatIf #Science #Documentary #ThoughtExperiment #WhatWouldHappen
"""


def _generate_timestamps(audio_results: list[dict] | None) -> str:
    """Gerçek ses sürelerinden timestamp oluştur."""
    if not audio_results:
        return (
            "00:00 - The Hook\n"
            "00:30 - Setting the Stage\n"
            "02:30 - The First Twist\n"
            "05:00 - Going Deeper\n"
            "07:30 - The Mind-Blowing Conclusion"
        )

    scene_labels = [
        "The Hook", "Setting the Stage", "The First Twist",
        "Going Deeper", "The Escalation", "The Mind-Blowing Conclusion",
        "Final Thoughts", "The Reveal",
    ]

    timestamps = []
    current_time = 0.0
    for i, result in enumerate(audio_results):
        minutes = int(current_time // 60)
        seconds = int(current_time % 60)
        label = scene_labels[i] if i < len(scene_labels) else f"Part {i + 1}"
        timestamps.append(f"{minutes:02d}:{seconds:02d} - {label}")
        current_time += result.get("duration_seconds", 60)

    return "\n".join(timestamps)


# ──────────────────────────────────────
# Doğrudan çalıştırma
# ──────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="YouTube Video Uploader")
    parser.add_argument("--auth", action="store_true", help="YouTube yetkilendirmesi yap")
    parser.add_argument("--check", action="store_true", help="Kurulum durumunu kontrol et")
    parser.add_argument("--upload", metavar="VIDEO", help="Video dosyası yolu")
    parser.add_argument("--title", default="What If Episode", help="Video başlığı")

    args = parser.parse_args()

    if args.auth:
        print_header("🔐 YouTube Yetkilendirme")
        creds = authenticate()
        if creds:
            print_success("Yetkilendirme başarılı! Token kaydedildi.")
        else:
            print_error("Yetkilendirme başarısız.")

    elif args.check:
        print_header("🔍 YouTube API Kontrol")
        status = check_youtube_setup()
        for key, value in status.items():
            icon = "✓" if value else "✗"
            color = "green" if value else "red"
            console.print(f"  [{color}]{icon}[/{color}] {key}: {value}")

    elif args.upload:
        upload_video(args.upload, args.title)

    else:
        parser.print_help()
