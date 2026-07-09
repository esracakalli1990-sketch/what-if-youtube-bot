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
import json
import time
import pickle
import httplib2
from pathlib import Path
from datetime import datetime, timedelta, timezone

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
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]

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

    Returns:
        str | None: YouTube video ID'si veya None
    """
    print_header("📤 YOUTUBE YÜKLEME")

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

    # Duplikat etiketleri temizle
    seen = set()
    unique_tags = []
    for t in tags:
        if t.lower() not in seen:
            seen.add(t.lower())
            unique_tags.append(t)
    tags = unique_tags[:30]  # YouTube max 500 karakter

    category_id = CATEGORY_IDS.get(category, "28")

    # Açıklama şablonu — SEO-optimize
    if not description:
        seo_desc = scenario.get("seo_description", "") if scenario else ""
        description = _generate_description(title, tags, seo_desc, audio_results)

    body = {
        "snippet": {
            "title": title[:100],  # YouTube max 100 karakter
            "description": description[:5000],  # YouTube max 5000
            "tags": tags[:500],  # Max 500 etiket
            "categoryId": category_id,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    # Planlı yayın
    if publish_at and privacy == "private":
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = publish_at.isoformat()
        console.print(f"  📅 Planlı yayın: {publish_at.strftime('%Y-%m-%d %H:%M')}")

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

        # Thumbnail yükle
        if thumbnail_path and Path(thumbnail_path).exists():
            print_step(3, "Thumbnail yükleniyor...")
            _upload_thumbnail(youtube, video_id, thumbnail_path)

        # Oynatma listesine ekle
        if playlist_id:
            print_step(4, "Oynatma listesine ekleniyor...")
            _add_to_playlist(youtube, video_id, playlist_id)

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
