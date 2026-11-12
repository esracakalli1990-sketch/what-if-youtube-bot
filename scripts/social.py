"""
social.py - Shorts'ların TikTok / Instagram / Facebook'ta paylaşımı.

Akış:
1) Short üretilince (doc_shorts --sosyal) her Short için platformlara uygun bir
   kopya (≤45 MB, Telegram sınırı 50 MB) ve açıklama hazırlanır; paket GitHub
   Release'e ("sosyal-<klasör>") yüklenir — Actions artifact kotasına girmez.
2) Günlük iş (sosyal.yml) o günün Short'larını bulur:
   - Telegram'a video + kopyalanabilir açıklama gönderir (TikTok elle: 1 dk).
   - META_* gizli anahtarları varsa Instagram Reels ve Facebook Reels'e
     otomatik paylaşır. Anahtar yoksa bu adımlar atlanır, hata vermez.

    python -m scripts.social paylas [--tarih YYYY-MM-DD] [--klasor K --id X] [--deneme]

Takvim: shorts.json'daki her Short'un "sosyal" alanı (ISO tarih-saat); yoksa
"yayin" (YouTube) tarihi kullanılır. Yalnızca tarih (gün) karşılaştırılır.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from scripts.utils import PROJECT_ROOT, logger

GRAPH = "https://graph.facebook.com/v21.0"
MAX_MB = 45
CHANNEL = "Tarih Dosyaları"
BASE_TAGS = ["tarih", "belgesel", "tarihdosyalari"]


# ─────────────────────────────────────────────
# Açıklama ve takvim (saf, test edilebilir)
# ─────────────────────────────────────────────

def hashtags(tags: list[str], limit: int = 8) -> list[str]:
    """'istanbul'un fethi' → '#istanbulunfethi'. 'shorts' platform dışı, atılır."""
    out = []
    for t in list(tags) + BASE_TAGS:
        h = "".join(ch for ch in t.lower().replace("'", "") if ch.isalnum())
        if h and h != "shorts" and f"#{h}" not in out:
            out.append(f"#{h}")
    return out[:limit]


def social_caption(spec: dict, full_url: str, credits: list[str], tags: list[str], ai_note: str = "") -> str:
    """TikTok/Instagram/Facebook açıklaması (≤2200 karakter)."""
    title = spec.get("baslik", "").replace("#shorts", "").strip()
    parts = [title, "", spec.get("aciklama", "").strip(), "",
             f"▶️ Tam belgesel YouTube'da: {CHANNEL}", full_url, ""]
    if ai_note:
        parts += [f"ℹ️ {ai_note}", ""]
    parts += [" ".join(hashtags(tags)), ""]
    if credits:
        parts += ["Kaynaklar: " + " · ".join(dict.fromkeys(credits))]
    text = "\n".join(parts).strip()
    return text[:2200]


def post_day(spec: dict) -> str:
    """Short'un sosyal medya paylaşım günü (YYYY-MM-DD)."""
    when = spec.get("sosyal") or spec.get("yayin") or ""
    return when[:10]


def due_posts(root: Path, day: str, folder: str | None = None, sid: str | None = None) -> list[dict]:
    """Bugün (ya da --klasor/--id ile seçilen) paylaşılacak Short'lar."""
    rows = []
    for cfg_path in sorted(Path(root).glob("belgeseller/*/shorts.json")):
        slug = cfg_path.parent.name
        if folder and Path(folder).name != slug:
            continue
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        for spec in cfg.get("shorts", []):
            if sid and spec["id"] != sid:
                continue
            if sid or post_day(spec) == day:
                rows.append({"slug": slug, "id": spec["id"]})
    return rows


def transcode_cmd(src: Path, dst: Path, max_mb: int = MAX_MB, seconds: float = 60.0) -> list[str]:
    """Sosyal kopya: 1080×1920, bit hızı süreye göre sınırlı (dosya ≤ max_mb)."""
    total_kbps = int(max_mb * 8 * 1024 / max(seconds, 1) * 0.92)
    v_kbps = max(1500, min(8000, total_kbps - 160))
    return ["ffmpeg", "-y", "-v", "error", "-i", str(src),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "medium", "-crf", "21",
            "-maxrate", f"{v_kbps}k", "-bufsize", f"{v_kbps * 2}k", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(dst)]


def package(folder: Path, cfg: dict, results: list[dict], ai_note: str = "") -> Path:
    """build/sosyal/: <id>.mp4 + manifest.json (açıklamalar). Paket klasörünü döndürür."""
    out = Path(folder) / "build" / "sosyal"
    out.mkdir(parents=True, exist_ok=True)
    specs = {s["id"]: s for s in cfg["shorts"]}
    manifest = []
    for r in results:
        spec = specs[r["id"]]
        dst = out / f"{r['id']}.mp4"
        subprocess.run(transcode_cmd(Path(r["video"]), dst, seconds=r.get("seconds", 60)), check=True)
        manifest.append({"id": r["id"], "dosya": dst.name, "sure": r.get("seconds"),
                         "baslik": spec.get("baslik", "").replace("#shorts", "").strip(),
                         "aciklama": social_caption(spec, cfg["tam_video"], r.get("credits", []),
                                                    cfg.get("etiketler", []),
                                                    ai_note if r.get("uses_clip") else "")})
        logger.info("Sosyal kopya: %s (%.1f MB)", dst.name, dst.stat().st_size / 1e6)
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


# ─────────────────────────────────────────────
# Instagram ve Facebook (Meta Graph API)
# ─────────────────────────────────────────────

class SocialError(RuntimeError):
    pass


def _check(resp: requests.Response, what: str) -> dict:
    try:
        data = resp.json()
    except ValueError:
        data = {}
    if resp.status_code >= 400 or "error" in data:
        msg = data.get("error", {}).get("message") if isinstance(data.get("error"), dict) else resp.text[:300]
        raise SocialError(f"{what}: {msg}")
    return data


def _rupload(url: str, path: Path, token: str, what: str):
    data = Path(path).read_bytes()
    r = requests.post(url, data=data, timeout=600, headers={
        "Authorization": f"OAuth {token}", "offset": "0", "file_size": str(len(data))})
    _check(r, what)


def instagram_reel(path: Path, caption: str, ig_user: str, token: str,
                   poll_every: float = 10.0, max_wait: float = 600.0) -> str:
    """Instagram Reels: konteyner → dosya yükleme → işlenmesini bekle → yayınla. Medya kimliği döner."""
    c = _check(requests.post(f"{GRAPH}/{ig_user}/media", timeout=60, data={
        "media_type": "REELS", "upload_type": "resumable", "caption": caption,
        "share_to_feed": "true", "access_token": token}), "Instagram konteyner")
    _rupload(c["uri"], path, token, "Instagram yükleme")
    waited = 0.0
    while True:
        st = _check(requests.get(f"{GRAPH}/{c['id']}", timeout=60, params={
            "fields": "status_code,status", "access_token": token}), "Instagram durum")
        code = st.get("status_code")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            raise SocialError(f"Instagram işleme hatası: {st.get('status')}")
        if waited >= max_wait:
            raise SocialError("Instagram işleme zaman aşımı")
        time.sleep(poll_every)
        waited += poll_every
    pub = _check(requests.post(f"{GRAPH}/{ig_user}/media_publish", timeout=60, data={
        "creation_id": c["id"], "access_token": token}), "Instagram yayınla")
    return pub["id"]


def facebook_reel(path: Path, caption: str, page_id: str, token: str) -> str:
    """Facebook Sayfası Reels: başlat → yükle → yayınla. Video kimliği döner."""
    start = _check(requests.post(f"{GRAPH}/{page_id}/video_reels", timeout=60, data={
        "upload_phase": "start", "access_token": token}), "Facebook başlat")
    _rupload(start["upload_url"], path, token, "Facebook yükleme")
    _check(requests.post(f"{GRAPH}/{page_id}/video_reels", timeout=60, data={
        "upload_phase": "finish", "video_id": start["video_id"], "video_state": "PUBLISHED",
        "description": caption, "access_token": token}), "Facebook yayınla")
    return start["video_id"]


# ─────────────────────────────────────────────
# Günlük paylaşım
# ─────────────────────────────────────────────

def fetch_package(slug: str, sid: str, dest: Path) -> tuple[Path, dict]:
    """GitHub Release'ten (sosyal-<slug>) Short'u ve açıklamasını indir."""
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(["gh", "release", "download", f"sosyal-{slug}", "--clobber", "-D", str(dest),
                    "-p", f"{sid}.mp4", "-p", "manifest.json"], check=True)
    manifest = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
    row = next((m for m in manifest if m["id"] == sid), None)
    if not row:
        raise SocialError(f"{slug}/{sid}: pakette yok")
    return dest / f"{sid}.mp4", row


def share(slug: str, sid: str, work: Path, dry_run: bool = False) -> dict:
    from scripts import notifier
    video, row = fetch_package(slug, sid, work / slug)
    result = {"slug": slug, "id": sid, "telegram": False, "instagram": None, "facebook": None, "hatalar": []}
    if not dry_run:
        result["telegram"] = notifier.send_video(str(video), f"📱 Bugünün Short'u: {row['baslik']}\n"
                                                 "TikTok için: videoyu kaydet → TikTok'ta paylaş, "
                                                 "açıklamayı alttaki mesajdan kopyala.")
        notifier.send_message(row["aciklama"], parse_mode=None)
    token = os.environ.get("META_PAGE_TOKEN", "").strip()
    ig_user = os.environ.get("META_IG_USER_ID", "").strip()
    page_id = os.environ.get("META_PAGE_ID", "").strip()
    if token and ig_user and not dry_run:
        try:
            result["instagram"] = instagram_reel(video, row["aciklama"], ig_user, token)
        except Exception as e:      # bir platformun hatası diğerini durdurmasın
            result["hatalar"].append(f"Instagram: {e}")
    if token and page_id and not dry_run:
        try:
            result["facebook"] = facebook_reel(video, row["aciklama"], page_id, token)
        except Exception as e:
            result["hatalar"].append(f"Facebook: {e}")
    return result


def summary(results: list[dict], meta_ready: bool) -> str:
    if not results:
        return ""
    lines = ["📣 Sosyal medya paylaşımı:"]
    for r in results:
        ig = "✅" if r["instagram"] else ("—" if not meta_ready else "❌")
        fb = "✅" if r["facebook"] else ("—" if not meta_ready else "❌")
        lines.append(f"• {r['slug']}/{r['id']} · Telegram {'✅' if r['telegram'] else '❌'} · "
                     f"Instagram {ig} · Facebook {fb}")
        lines += [f"  ⚠️ {h}" for h in r["hatalar"]]
    if not meta_ready:
        lines.append("ℹ️ Instagram/Facebook anahtarları henüz eklenmedi (docs/SOSYAL_MEDYA_KURULUM.md).")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Shorts → TikTok (Telegram), Instagram, Facebook")
    sub = ap.add_subparsers(dest="komut", required=True)
    p = sub.add_parser("paylas")
    p.add_argument("--tarih", default=None, help="YYYY-MM-DD (varsayılan: bugün, UTC)")
    p.add_argument("--klasor", default=None)
    p.add_argument("--id", default=None)
    p.add_argument("--deneme", action="store_true", help="indir ama gönderme")
    args = ap.parse_args(argv)
    day = args.tarih or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rows = due_posts(PROJECT_ROOT, day, args.klasor, args.id)
    logger.info("%s için %d Short", day, len(rows))
    work = PROJECT_ROOT / "build" / "sosyal_indir"
    meta_ready = bool(os.environ.get("META_PAGE_TOKEN") and
                      (os.environ.get("META_IG_USER_ID") or os.environ.get("META_PAGE_ID")))
    results, failed = [], False
    for r in rows:
        try:
            results.append(share(r["slug"], r["id"], work, dry_run=args.deneme))
        except Exception as e:
            failed = True
            results.append({"slug": r["slug"], "id": r["id"], "telegram": False, "instagram": None,
                            "facebook": None, "hatalar": [f"paket: {e}"]})
    text = summary(results, meta_ready)
    print(json.dumps(results, ensure_ascii=False, indent=1))
    if text and not args.deneme:
        from scripts import notifier
        notifier.send_message(text, parse_mode=None)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
