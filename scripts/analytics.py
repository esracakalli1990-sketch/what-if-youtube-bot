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
from datetime import datetime, timezone, date, timedelta
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


def format_report_text() -> str:
    """
    Kanal performans raporunu düz metin olarak üret (Telegram için).
    """
    stats = fetch_video_stats()
    if not stats:
        return ("📊 <b>Kanal Raporu</b>\n\n"
                "Henüz istatistik yok — ilk videolar yüklendikten sonra rapor oluşacak.")

    stats.sort(key=lambda s: s.get("views", 0), reverse=True)
    total_views = sum(s["views"] for s in stats)
    total_likes = sum(s["likes"] for s in stats)
    shorts = [s for s in stats if s["kind"] == "short"]
    longs = [s for s in stats if s["kind"] == "long"]

    lines = [
        "📊 <b>Kanal Performans Raporu</b>",
        "",
        f"🎬 Video: {len(longs)} uzun + {len(shorts)} Short",
        f"👁 Toplam izlenme: {total_views:,}",
        f"👍 Toplam beğeni: {total_likes:,}",
        "",
        "<b>En iyi 5:</b>",
    ]
    for i, s in enumerate(stats[:5], 1):
        icon = "📱" if s["kind"] == "short" else "🎬"
        lines.append(f"{i}. {icon} {s['title'][:60]}")
        lines.append(f"    👁 {s['views']:,} | 👍 {s['likes']:,} | 💬 {s['comments']:,}")

    return "\n".join(lines)


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
# Derin analitik — YouTube Analytics API (retention, izlenme süresi, abone)
# Data API'nin veremediği metrikler; yt-analytics.readonly scope'u gerektirir.
# ──────────────────────────────────────
def _analytics_service():
    """youtubeAnalytics v2 servisi (yt-analytics.readonly scope gerektirir)."""
    if not GOOGLE_API_AVAILABLE:
        return None
    try:
        credentials = authenticate()
    except Exception as e:  # pragma: no cover - yetki akışı
        logger.warning("Analytics yetkilendirme hatası: %s", e)
        return None
    if not credentials:
        return None
    from googleapiclient.discovery import build
    return build("youtubeAnalytics", "v2", credentials=credentials)


def _analytics_query(service, *, start, end, metrics,
                     dimensions=None, sort=None, max_results=None):
    """youtubeAnalytics.reports().query çağrısını sar."""
    params = {
        "ids": "channel==MINE",
        "startDate": start,
        "endDate": end,
        "metrics": metrics,
    }
    if dimensions:
        params["dimensions"] = dimensions
    if sort:
        params["sort"] = sort
    if max_results:
        params["maxResults"] = max_results
    return service.reports().query(**params).execute()


def channel_summary(service, days: int = 28) -> dict:
    """Kanal geneli toplamlar (son `days` gün)."""
    end = date.today()
    start = end - timedelta(days=days)
    metrics = ("views,estimatedMinutesWatched,averageViewDuration,"
               "averageViewPercentage,subscribersGained,subscribersLost,"
               "likes,comments")
    resp = _analytics_query(service, start=start.isoformat(),
                            end=end.isoformat(), metrics=metrics)
    headers = [h["name"] for h in resp.get("columnHeaders", [])]
    rows = resp.get("rows", [])
    if not rows:
        return {h: 0 for h in headers}
    return dict(zip(headers, rows[0]))


def top_videos_analytics(service, days: int = 28, limit: int = 8) -> list[dict]:
    """En çok izlenen videolar + retention (son `days` gün)."""
    end = date.today()
    start = end - timedelta(days=days)
    metrics = ("views,estimatedMinutesWatched,averageViewDuration,"
               "averageViewPercentage")
    resp = _analytics_query(service, start=start.isoformat(),
                            end=end.isoformat(), metrics=metrics,
                            dimensions="video", sort="-views",
                            max_results=limit)
    headers = [h["name"] for h in resp.get("columnHeaders", [])]
    return [dict(zip(headers, row)) for row in resp.get("rows", [])]


def _fmt_duration(seconds) -> str:
    """Saniyeyi d:ss biçimine çevir."""
    try:
        s = int(round(float(seconds)))
    except (TypeError, ValueError):
        return "0:00"
    return f"{s // 60}:{s % 60:02d}"


def _num(v) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def _reauth_hint() -> str:
    """Analitik scope'u eksikse tek seferlik kurulum talimatı."""
    return (
        "📊 <b>Derin analitik için ek yetki gerekli</b>\n\n"
        "Mevcut YouTube token'ı analitik okuma izni (yt-analytics.readonly) "
        "içermiyor. Tek seferlik kurulum:\n\n"
        "1️⃣ Lokal makinede: <code>python scripts/youtube_uploader.py --auth</code>\n"
        "2️⃣ Açılan tarayıcıda izin ver (analitik dahil)\n"
        "3️⃣ <code>base64 -w0 youtube_token.pickle</code> çıktısını GitHub'da "
        "<b>YOUTUBE_TOKEN_B64</b> secret'ına yapıştır\n\n"
        "Sonra /analitik yeniden çalışır. (Bu arada /rapor temel izlenme "
        "sayılarını yetki olmadan da gösterir.)"
    )


def build_deep_report(days: int = 28) -> str:
    """Kanal + video derin analitiğini çekip Telegram için HTML metin döndür."""
    service = _analytics_service()
    if service is None:
        return _reauth_hint()

    try:
        summary = channel_summary(service, days=days)
        videos = top_videos_analytics(service, days=days, limit=8)
    except Exception as e:
        msg = str(e)
        logger.warning("Derin analitik sorgu hatası: %s", msg)
        low = msg.lower()
        if any(k in low for k in ("insufficient", "scope", "403",
                                  "forbidden", "permission")):
            return _reauth_hint()
        return f"📊 Analitik çekilemedi: <code>{msg[:200]}</code>"

    id_map = {u.get("video_id"): u for u in load_uploads()}

    views = int(_num(summary.get("views")))
    watch_min = _num(summary.get("estimatedMinutesWatched"))
    avg_dur = summary.get("averageViewDuration", 0)
    avg_pct = _num(summary.get("averageViewPercentage"))
    subs_gained = int(_num(summary.get("subscribersGained")))
    subs_lost = int(_num(summary.get("subscribersLost")))
    likes = int(_num(summary.get("likes")))

    lines = [
        f"📊 <b>Derin Analitik — son {days} gün</b>",
        "",
        f"👁 İzlenme: <b>{views}</b>",
        f"⏱ İzlenme süresi: <b>{watch_min:.0f} dk</b> ({watch_min / 60:.1f} saat)",
        f"📈 Ort. izlenme: {_fmt_duration(avg_dur)} (%{avg_pct:.0f} tamamlanma)",
        f"➕ Abone: +{subs_gained} / −{subs_lost} "
        f"(net {subs_gained - subs_lost:+d})",
        f"👍 Beğeni: {likes}",
        "",
        f"🎬 <b>En çok izlenen ({len(videos)}):</b>",
    ]

    if not videos:
        lines.append("— Bu dönemde izlenme verisi yok.")
    for v in videos:
        vid = v.get("video", "")
        rec = id_map.get(vid, {})
        title = (rec.get("title") or vid)[:42]
        icon = "📱" if rec.get("kind") == "short" else "🎞"
        vv = int(_num(v.get("views")))
        vpct = _num(v.get("averageViewPercentage"))
        lines.append(f"{icon} {vv} izlenme · %{vpct:.0f} tamamlanma — {title}")

    # Kısa otomatik nabız — derin yorum sohbette yapılır
    lines.append("")
    if views == 0:
        lines.append("💡 Bu dönemde kanal dağıtım almadı: yeni-kanal soğuk "
                     "başlangıcı. Kaldıraç = tamamlanma oranı + hacim.")
    elif avg_pct and avg_pct < 30:
        lines.append("💡 Tamamlanma düşük. Asıl darboğaz retention — "
                     "ilk 1-3 saniye kancası kritik.")
    else:
        lines.append("💡 Dağıtım var. Tamamlanma oranı yüksek kalan "
                     "videoları çoğaltmaya odaklan.")

    return "\n".join(lines)


# ──────────────────────────────────────
# Doğrudan çalıştırma
# ──────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Kanal Performans Analizi")
    parser.add_argument("--report", action="store_true", help="Performans tablosu göster")
    parser.add_argument("--top", type=int, metavar="N", help="En iyi N videoyu listele")
    parser.add_argument("--refresh", action="store_true", help="Cache'i atla, taze veri çek")
    parser.add_argument("--deep", action="store_true",
                        help="Derin analitik raporu (retention/izlenme süresi/abone)")
    parser.add_argument("--deep-send", action="store_true",
                        help="Derin analitik raporunu Telegram'a gönder")
    parser.add_argument("--days", type=int, default=28, help="Derin rapor dönemi (gün)")

    args = parser.parse_args()

    if args.refresh:
        fetch_video_stats(force_refresh=True)

    if args.report:
        print_report()
    elif args.top:
        for i, s in enumerate(get_top_performers(args.top), 1):
            console.print(f"  {i}. {s['title']} — {s['views']:,} izlenme")
    elif args.deep or args.deep_send:
        text = build_deep_report(days=args.days)
        print(text)
        if args.deep_send:
            from scripts.notifier import send_message
            send_message(text)
    elif not args.refresh:
        parser.print_help()
