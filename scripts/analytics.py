"""
analytics.py - Kanal Performans Takibi ve Geri Besleme.

output/uploads.json'daki videoların YouTube istatistiklerini çeker,
performans raporu üretir ve en iyi performans gösteren başlıkları
konu motoruna (scheduler --refill) geri besler.

Kullanım:
    python scripts/analytics.py --report      # Performans tablosu
    python scripts/analytics.py --top 5       # En iyi 5 video
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path

# Doğrudan çalıştırma desteği: python scripts/analytics.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils import (
    print_header, print_success, print_error, print_warning,
    console, logger, OUTPUT_DIR
)
from scripts.youtube_uploader import (
    authenticate, load_uploads, GOOGLE_API_AVAILABLE
)

# İstatistik cache dosyası — API kotasını korumak için
STATS_FILE = OUTPUT_DIR / "video_stats.json"
STATS_MAX_AGE_HOURS = 6


def _load_cached_stats() -> dict | None:
    """Taze cache varsa oku (STATS_MAX_AGE_HOURS'tan eski değilse)."""
    if not STATS_FILE.exists():
        return None
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        fetched_at = datetime.fromisoformat(data.get("fetched_at", ""))
        age_hours = (datetime.now(timezone.utc) - fetched_at).total_seconds() / 3600
        if age_hours <= STATS_MAX_AGE_HOURS:
            return data
    except (json.JSONDecodeError, IOError, ValueError):
        pass
    return None


def _save_stats(stats: dict):
    """İstatistikleri cache'e yaz."""
    STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def fetch_video_stats(force_refresh: bool = False) -> list[dict]:
    """
    Yüklenen tüm videoların istatistiklerini YouTube Data API'den çek.

    Sonuçlar STATS_FILE'a cache'lenir (API kota koruması).

    Returns:
        list[dict]: [{video_id, title, kind, views, likes, comments, uploaded_at}, ...]
    """
    uploads = load_uploads()
    if not uploads:
        logger.info("uploads.json boş — henüz yüklenen video yok.")
        return []

    if not force_refresh:
        cached = _load_cached_stats()
        if cached:
            logger.info("Video istatistikleri cache'ten okundu.")
            return cached.get("videos", [])

    if not GOOGLE_API_AVAILABLE:
        print_error("YouTube API paketleri kurulu değil!")
        return []

    credentials = authenticate()
    if not credentials:
        return []

    from googleapiclient.discovery import build
    youtube = build("youtube", "v3", credentials=credentials)

    upload_map = {u["video_id"]: u for u in uploads}
    video_ids = list(upload_map.keys())

    results = []
    # API tek istekte max 50 ID kabul eder
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        try:
            response = youtube.videos().list(
                part="statistics",
                id=",".join(batch),
            ).execute()
        except Exception as e:
            print_error(f"İstatistik çekme hatası: {e}")
            logger.error("Analytics API hatası: %s", e)
            return results

        for item in response.get("items", []):
            vid = item["id"]
            stats = item.get("statistics", {})
            upload_info = upload_map.get(vid, {})
            results.append({
                "video_id": vid,
                "title": upload_info.get("title", "?"),
                "kind": upload_info.get("kind", "long"),
                "uploaded_at": upload_info.get("uploaded_at", ""),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
            })

    _save_stats({
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "videos": results,
    })
    logger.info("Video istatistikleri güncellendi: %d video", len(results))
    return results


def get_top_performers(n: int = 5, kind: str | None = None) -> list[dict]:
    """
    En çok izlenen n videoyu döndür (konu motoru geri beslemesi için).

    Args:
        n: Döndürülecek video sayısı
        kind: "long" | "short" | None (hepsi)
    """
    stats = fetch_video_stats()
    if kind:
        stats = [s for s in stats if s.get("kind") == kind]
    return sorted(stats, key=lambda s: s.get("views", 0), reverse=True)[:n]


def print_report():
    """Kanal performans tablosunu yazdır."""
    from rich.table import Table

    print_header("📊 KANAL PERFORMANS RAPORU")

    stats = fetch_video_stats()
    if not stats:
        print_warning("Henüz istatistik yok. Önce video yükleyin (uploads.json boş).")
        return

    stats.sort(key=lambda s: s.get("views", 0), reverse=True)

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", width=3)
    table.add_column("Başlık", max_width=50)
    table.add_column("Tür", width=6)
    table.add_column("İzlenme", justify="right")
    table.add_column("Beğeni", justify="right")
    table.add_column("Yorum", justify="right")

    total_views = 0
    for i, s in enumerate(stats, 1):
        total_views += s["views"]
        table.add_row(
            str(i),
            s["title"][:50],
            "📱" if s["kind"] == "short" else "🎬",
            f"{s['views']:,}",
            f"{s['likes']:,}",
            f"{s['comments']:,}",
        )

    console.print(table)
    console.print()
    print_success(f"Toplam: {len(stats)} video, {total_views:,} izlenme")

    # Konu motoru ipucu
    top = stats[:3]
    if top and top[0]["views"] > 0:
        console.print("\n[bold cyan]💡 En iyi performans gösterenler "
                      "(scheduler --refill bunları otomatik kullanır):[/bold cyan]")
        for s in top:
            console.print(f"  ⭐ {s['title']} — {s['views']:,} izlenme")


# ──────────────────────────────────────
# Doğrudan çalıştırma
# ──────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Kanal Performans Analizi")
    parser.add_argument("--report", action="store_true", help="Performans tablosu göster")
    parser.add_argument("--top", type=int, metavar="N", help="En iyi N videoyu listele")
    parser.add_argument("--refresh", action="store_true", help="Cache'i atla, taze veri çek")

    args = parser.parse_args()

    if args.refresh:
        fetch_video_stats(force_refresh=True)

    if args.report:
        print_report()
    elif args.top:
        for i, s in enumerate(get_top_performers(args.top), 1):
            console.print(f"  {i}. {s['title']} — {s['views']:,} izlenme")
    elif not args.refresh:
        parser.print_help()
