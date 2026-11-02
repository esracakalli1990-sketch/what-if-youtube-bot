"""
channel_setup.py - "Tarih Dosyaları" kanal ve video ayarları (YouTube Data API).

    python -m scripts.channel_setup <klasör> rapor
    python -m scripts.channel_setup <klasör> uygula --yayin 2026-11-01T16:00:00Z

rapor  : yalnızca okur — kanal bilgileri, belgesel videoları (gizlilik, planlı
         yayın, altyazı, beyanlar), oynatma listeleri → build/kanal/rapor.json
uygula : kanal açıklaması/anahtar kelimeler/ülke/dil, banner, seri oynatma
         listesi, en yeni belgesel videosunun planlı yayını ve ilk yorum.
         Banner, profil resmi ve 3 kapak Remotion ile üretilir; profil resmi ve
         kapaklar API ile yüklenemediği için Telegram'a dosya olarak gönderilir.

API'nin izin vermediği işler (kanal adı, profil resmi, kapak testi, yorumu
sabitleme, bitiş ekranı) kullanıcıya adım adım Telegram mesajıyla bildirilir.
Hiçbir video silinmez.
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from scripts.utils import PROJECT_ROOT, logger

CHANNEL_NAME = "Tarih Dosyaları"
PLAYLIST_TITLE = "Tarih Dosyaları: İmparatorluklar"
KANAL_JSON = PROJECT_ROOT / "kanal.json"
REMOTION_DIR = PROJECT_ROOT / "remotion"

CHANNEL_DESCRIPTION = """Tarih Dosyaları: Anadolu'dan dünyaya imparatorlukların, uygarlıkların ve unutulmuş halkların tam hikâyesi.

Her belgesel kaynaklara dayanır: akademik eserler, müze kayıtları ve arşiv görüntüleri. Kesin olmayan bilgiler anlatımda açıkça belirtilir; kaynaklar ve görsel lisansları her videonun açıklamasında yer alır.

📜 Uzun, bölümlü belgeseller: kuruluştan yıkılışa tek videoda
🏛️ Gerçek eser ve kazı alanı görüntüleri
🗺️ Hareketli haritalarla seferler ve savaşlar

Yeni belgeseller düzenli olarak yayımlanır. Seriyi kaçırmamak için abone olun."""

KEYWORDS = ["tarih", "tarih belgeseli", "belgesel", "türkçe belgesel", "anadolu tarihi",
            "antik tarih", "imparatorluklar", "hititler", "medeniyetler", "tarih dosyaları"]


HITIT_COMMENT = ("Sizce Hititlerin çöküşünün asıl nedeni neydi: kuraklık mı, Deniz Kavimleri mi, iç savaşlar mı? "
                 "Yorumlarda tartışalım.\n\n🔔 Sıradaki belgesel: Antik Mısır'ın Tam Hikâyesi.")


def first_comment(playlist_id: str | None, body: str | None = None) -> str:
    """İlk yorum. body: belgeselin kendi sorusu ve duyurusu (cekim_plani.json → "ilk_yorum")."""
    lines = ["📜 Tarih Dosyaları'na hoş geldiniz! Bu belgeselde kullanılan kaynakların ve görsellerin "
             "tam listesi açıklamada.",
             "",
             body or HITIT_COMMENT]
    if playlist_id:
        lines.append(f"▶️ Serinin tamamı: https://www.youtube.com/playlist?list={playlist_id}")
    return "\n".join(lines)


STUDIO_STEPS = """🛠️ YouTube Studio'da sizin yapacaklarınız (API bunlara izin vermiyor):
1) Kanal adı: Studio → Özelleştirme → Profil → Ad: "Tarih Dosyaları" → Yayınla.
   İsterseniz aynı ekrandan tanıtıcıyı (@) da değiştirin (ör. @tarihdosyalari).
2) Profil resmi: aynı ekranda "Resim" → Telegram'a gelen profil.png dosyasını yükleyin.
3) Kapak testi: İçerik → Hitit videosu → Kapak → "Test ve karşılaştır" → Telegram'a gelen 3 kapağı ekleyin.
4) Yorumu sabitle: videonun yorumlarında kanalın yorumunun ⋮ menüsü → "Sabitle".
5) Bitiş ekranı: video düzenle → Bitiş ekranı → "Abone ol" + "Oynatma listesi: Tarih Dosyaları: İmparatorluklar".
6) Ana sayfa: Özelleştirme → Düzen → "Geri gelen aboneler için öne çıkan video" → Hitit videosu.
7) Eski sürümler: aşağıda "silinebilir" yazan gizli Hitit videolarını İçerik'ten silin."""


# ─────────────────────────────────────────────
# Saf yardımcılar (test edilebilir)
# ─────────────────────────────────────────────

def pick_latest(videos: list[dict], title_word: str) -> tuple[dict | None, list[dict]]:
    """Başlığında `title_word` geçen videolardan en yeni yüklenen ve diğerleri."""
    matching = [v for v in videos if title_word.lower() in v["snippet"]["title"].lower()]
    matching.sort(key=lambda v: v["snippet"]["publishedAt"], reverse=True)
    return (matching[0] if matching else None), matching[1:]


def scheduled_status(current: dict, publish_at: str, synthetic: bool = True) -> dict:
    """videos.update için durum: mevcut değiştirilebilir alanlar korunur, gizli + planlı yayın.
    Gemini canlandırmaları kullanıldığı için "değiştirilmiş/yapay içerik" beyanı açıkça işaretlenir
    (API okumasında alan boş dönebiliyor; boş bırakmak beyanı kaldırır)."""
    keep = ("embeddable", "license", "publicStatsViewable")
    status = {k: current[k] for k in keep if k in current}
    status.update(privacyStatus="private", publishAt=publish_at, selfDeclaredMadeForKids=False,
                  containsSyntheticMedia=bool(synthetic))
    return status


def branding_update(current: dict, banner_url: str | None = None) -> dict:
    """channels.update brandingSettings: mevcut ayarlar korunur, kanal bilgileri değişir."""
    branding = json.loads(json.dumps(current or {}))
    ch = branding.setdefault("channel", {})
    ch.update(description=CHANNEL_DESCRIPTION, keywords=" ".join(
        f'"{k}"' if " " in k else k for k in KEYWORDS), country="TR", defaultLanguage="tr")
    if banner_url:
        branding.setdefault("image", {})["bannerExternalUrl"] = banner_url
    return branding


def playlist_id_from_config() -> str | None:
    if KANAL_JSON.exists():
        return json.loads(KANAL_JSON.read_text(encoding="utf-8")).get("playlist_id")
    return None


def valid_publish_time(text: str) -> str:
    when = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if when.tzinfo is None:
        raise ValueError("yayın saati saat dilimi içermeli (ör. ...Z)")
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


# ─────────────────────────────────────────────
# YouTube işlemleri
# ─────────────────────────────────────────────

def _youtube():
    from googleapiclient.discovery import build
    from scripts.youtube_uploader import authenticate
    creds = authenticate()
    if not creds:
        raise RuntimeError("YouTube kimlik doğrulaması başarısız (token geçersiz olabilir)")
    return build("youtube", "v3", credentials=creds)


def _my_channel(yt) -> dict:
    items = yt.channels().list(part="snippet,brandingSettings,contentDetails,statistics",
                               mine=True).execute().get("items", [])
    if not items:
        raise RuntimeError("Kanal bulunamadı")
    return items[0]


def _uploads(yt, channel: dict, limit: int = 50) -> list[dict]:
    uploads = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    ids = [i["contentDetails"]["videoId"] for i in yt.playlistItems().list(
        part="contentDetails", playlistId=uploads, maxResults=limit).execute().get("items", [])]
    if not ids:
        return []
    return yt.videos().list(part="snippet,status,contentDetails",
                            id=",".join(ids)).execute().get("items", [])


def _captions(yt, video_id: str) -> list[str]:
    try:
        items = yt.captions().list(part="snippet", videoId=video_id).execute().get("items", [])
        return [c["snippet"]["language"] for c in items]
    except Exception as e:
        return [f"okunamadı: {e}"]


def _summary(yt, v: dict) -> dict:
    s, st = v["snippet"], v["status"]
    return {"id": v["id"], "url": f"https://youtu.be/{v['id']}", "title": s["title"],
            "uploaded": s["publishedAt"], "privacy": st.get("privacyStatus"),
            "publishAt": st.get("publishAt"), "madeForKids": st.get("selfDeclaredMadeForKids"),
            "syntheticMedia": st.get("containsSyntheticMedia"), "category": s.get("categoryId"),
            "language": s.get("defaultLanguage"), "audioLanguage": s.get("defaultAudioLanguage"),
            "tags": len(s.get("tags", [])), "duration": v["contentDetails"].get("duration"),
            "captions": _captions(yt, v["id"])}


def _find_playlist(yt, title: str) -> str | None:
    items = yt.playlists().list(part="snippet", mine=True, maxResults=50).execute().get("items", [])
    for p in items:
        if p["snippet"]["title"] == title:
            return p["id"]
    return None


def _retry(call, tries: int = 4, wait: float = 5.0):
    """Yeni oluşturulan kaynak (ör. oynatma listesi) API'de birkaç saniye geç görünebilir."""
    import time
    for attempt in range(tries):
        try:
            return call()
        except Exception:
            if attempt == tries - 1:
                raise
            time.sleep(wait * (attempt + 1))


def report(yt, title_word: str) -> dict:
    ch = _my_channel(yt)
    latest, older = pick_latest(_uploads(yt, ch), title_word)
    playlists = yt.playlists().list(part="snippet", mine=True, maxResults=50).execute().get("items", [])
    return {
        "kanal": {"id": ch["id"], "ad": ch["snippet"]["title"],
                  "abone": ch["statistics"].get("subscriberCount"),
                  "aciklama": ch["brandingSettings"].get("channel", {}).get("description", "")[:200],
                  "ulke": ch["brandingSettings"].get("channel", {}).get("country")},
        "hedef_video": _summary(yt, latest) if latest else None,
        "eski_surumler": [_summary(yt, v) for v in older],
        "oynatma_listeleri": [{"id": p["id"], "ad": p["snippet"]["title"]} for p in playlists],
    }


# ─────────────────────────────────────────────
# Görseller (Remotion)
# ─────────────────────────────────────────────

def _fetch(plan: dict, keys: list[str], out_dir: Path) -> dict:
    from scripts.archive_images import fetch_images
    return {k: v["path"] for k, v in fetch_images({k: plan["images"][k] for k in keys}, out_dir).items()}


def _still(composition: str, out: Path, props: dict, extra: list[str] | None = None) -> Path:
    cmd = ["npx", "remotion", "still", "src/index.ts", composition, str(out),
           f"--props={json.dumps(props, ensure_ascii=False)}", *(extra or [])]
    subprocess.run(cmd, cwd=REMOTION_DIR, check=True)
    return out


CHANNEL_ART_PLAN = PROJECT_ROOT / "belgeseller" / "01-hititler" / "cekim_plani.json"


def render_art(folder: Path, out_dir: Path) -> dict:
    """Banner, profil resmi ve 3 kapak."""
    plan = json.loads((folder / "cekim_plani.json").read_text(encoding="utf-8"))
    # v2 kapaklar ("sablon": "v2") belgesel hattında üretilir; burada yalnızca eski şablon
    thumbs = [t for t in plan.get("thumbnails", []) if t.get("image") and t.get("sablon") != "v2"]
    # Kanal kimliği (banner, profil) her zaman seri görselleriyle: Hitit planından
    art_plan = json.loads(CHANNEL_ART_PLAN.read_text(encoding="utf-8"))
    paths = _fetch(art_plan, ["buyuk_mabet_3", "aslan_kapi_1"], out_dir / "gorseller")
    if thumbs:
        paths.update(_fetch(plan, list(dict.fromkeys(t["image"] for t in thumbs)), out_dir / "gorseller"))
    public = REMOTION_DIR / "public"
    public.mkdir(exist_ok=True)
    for font in (PROJECT_ROOT / "assets" / "fonts").glob("*.ttf"):
        shutil.copy2(font, public / font.name)
    for k, p in paths.items():
        shutil.copy2(p, public / f"kanal_{k}{Path(p).suffix}")
    name = {k: f"kanal_{k}{Path(p).suffix}" for k, p in paths.items()}
    art = {
        "banner": _still("ChannelBanner", out_dir / "banner.jpg",
                         {"image": name["buyuk_mabet_3"], "title": CHANNEL_NAME,
                          "tagline": "Anadolu'dan dünyaya imparatorlukların tam hikâyesi"},
                         ["--image-format=jpeg", "--jpeg-quality=92"]),
        "profil": _still("ChannelAvatar", out_dir / "profil.png",
                         {"image": name["aslan_kapi_1"], "monogram": "TD", "focusX": 0.5, "focusY": 0.4}),
    }
    for i, t in enumerate(thumbs, 1):
        art[f"kapak{i}"] = _still("Thumbnail", out_dir / f"kapak{i}.jpg",
                                  {"image": name[t["image"]], "line1": t.get("line1", ""),
                                   "line2": t.get("line2", ""), "badge": t.get("badge", "TAM HİKÂYE"),
                                   "focusX": t.get("focus_x", 0.6)},
                                  ["--image-format=jpeg", "--jpeg-quality=92"])
    return art


# ─────────────────────────────────────────────
# Uygulama
# ─────────────────────────────────────────────

def _plan_comment(folder: Path) -> str | None:
    plan = Path(folder) / "cekim_plani.json"
    if plan.exists():
        return json.loads(plan.read_text(encoding="utf-8")).get("ilk_yorum")
    return None


def apply(yt, folder: Path, publish_at: str, title_word: str, out_dir: Path) -> dict:
    from googleapiclient.http import MediaFileUpload
    done, problems = [], []
    art = render_art(folder, out_dir)

    # 1) Banner + kanal bilgileri
    ch = _my_channel(yt)
    banner_url = None
    try:
        resp = yt.channelBanners().insert(
            media_body=MediaFileUpload(str(art["banner"]), mimetype="image/jpeg")).execute()
        banner_url = resp.get("url")
        done.append("banner yüklendi")
    except Exception as e:
        problems.append(f"banner: {e}")
    try:
        yt.channels().update(part="brandingSettings", body={
            "id": ch["id"], "brandingSettings": branding_update(ch.get("brandingSettings"), banner_url)}).execute()
        done.append("kanal açıklaması, anahtar kelimeler, ülke ve dil ayarlandı")
    except Exception as e:
        problems.append(f"kanal bilgileri: {e}")

    # 2) Hedef video: planlı yayın
    latest, older = pick_latest(_uploads(yt, ch), title_word)
    if not latest:
        raise RuntimeError(f"Başlığında '{title_word}' geçen video bulunamadı")
    vid = latest["id"]
    if latest["status"].get("privacyStatus") == "public":
        done.append("video zaten yayında (planlama atlandı)")
    else:
        yt.videos().update(part="status", body={
            "id": vid, "status": scheduled_status(latest["status"], publish_at)}).execute()
        done.append(f"video planlandı: {publish_at}")

    # 3) Seri oynatma listesi
    pl = playlist_id_from_config() or _find_playlist(yt, PLAYLIST_TITLE)
    if not pl:
        pl = yt.playlists().insert(part="snippet,status", body={
            "snippet": {"title": PLAYLIST_TITLE, "defaultLanguage": "tr",
                        "description": "Anadolu'dan dünyaya imparatorlukların tam hikâyesi: "
                                       "Tarih Dosyaları belgesel serisi."},
            "status": {"privacyStatus": "public"}}).execute()["id"]
        done.append("oynatma listesi oluşturuldu")
    try:
        in_list = {i["contentDetails"]["videoId"] for i in _retry(lambda: yt.playlistItems().list(
            part="contentDetails", playlistId=pl, maxResults=50).execute()).get("items", [])}
    except Exception:
        in_list = set()      # yeni liste henüz görünmüyor olabilir: boş say
    if vid not in in_list:
        try:
            _retry(lambda: yt.playlistItems().insert(part="snippet", body={"snippet": {
                "playlistId": pl, "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute())
            done.append("video oynatma listesine eklendi")
        except Exception as e:
            problems.append(f"oynatma listesine ekleme: {e}")

    # 4) İlk yorum (gizli videoda reddedilebilir; o zaman yayından sonra tekrar çalıştırılır)
    try:
        threads = yt.commentThreads().list(part="snippet", videoId=vid, maxResults=20).execute().get("items", [])
        mine = [t for t in threads
                if t["snippet"]["topLevelComment"]["snippet"].get("authorChannelId", {}).get("value") == ch["id"]]
        if not mine:
            yt.commentThreads().insert(part="snippet", body={"snippet": {
                "videoId": vid, "topLevelComment": {"snippet": {"textOriginal": first_comment(pl, _plan_comment(folder))}}}}).execute()
            done.append("ilk yorum eklendi")
    except Exception as e:
        problems.append(f"ilk yorum (yayından sonra tekrar denenecek): {e}")

    return {"video": f"https://youtu.be/{vid}", "video_id": vid, "playlist_id": pl,
            "yapilanlar": done, "sorunlar": problems,
            "silinebilir": [f"https://youtu.be/{v['id']} ({v['status'].get('privacyStatus')})" for v in older],
            "dosyalar": {k: str(v) for k, v in art.items()}}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Tarih Dosyaları kanal/video ayarları")
    ap.add_argument("klasor")
    ap.add_argument("mod", choices=["rapor", "uygula"])
    ap.add_argument("--yayin", default=None, help="planlı yayın (ISO-8601, UTC)")
    ap.add_argument("--baslik", default="Hitit", help="hedef videonun başlığında geçen kelime")
    args = ap.parse_args(argv)
    folder = Path(args.klasor).resolve()
    out_dir = folder / "build" / "kanal"
    out_dir.mkdir(parents=True, exist_ok=True)
    yt = _youtube()
    if args.mod == "rapor":
        result = report(yt, args.baslik)
    else:
        if not args.yayin:
            ap.error("uygula için --yayin gerekli")
        result = apply(yt, folder, valid_publish_time(args.yayin), args.baslik, out_dir)
    (out_dir / f"{args.mod}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1),
                                             encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
