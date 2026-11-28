"""Yayınlanmış videoların başlığını güncelle ve açıklamanın başına "Sıradaki belgesel" bağlantısı ekle.

Kullanım:  python -m scripts.video_guncelle <json> [--uygula]
--uygula olmadan yalnızca ne değişeceğini yazar (kuru çalışma). Hiçbir video silinmez,
gizlilik ayarına dokunulmaz. Aynı dosya tekrar çalıştırılırsa sonuç değişmez.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SIRADAKI = "▶ Sıradaki belgesel:"


def next_line(title: str, video_id: str) -> str:
    return f"{SIRADAKI} {title} → https://youtu.be/{video_id}"


def new_description(desc: str, line: str | None) -> str:
    """Eski 'Sıradaki' satırını kaldırır, varsa yenisini en başa koyar."""
    rest = [ln for ln in (desc or "").splitlines() if not ln.startswith(SIRADAKI)]
    while rest and not rest[0].strip():
        rest.pop(0)
    body = "\n".join(rest)
    return f"{line}\n\n{body}" if line else body


def plan_changes(items: list[dict], videos: dict[str, dict]) -> list[dict]:
    """items: [{id, baslik?, siradaki?}] · videos: id → YouTube snippet. Değişen snippet'leri döndürür."""
    titles = {i["id"]: i.get("baslik") or videos.get(i["id"], {}).get("title", "") for i in items}
    out = []
    for it in items:
        snip = videos.get(it["id"])
        if snip is None:
            out.append({"id": it["id"], "hata": "video bulunamadı"})
            continue
        nxt = it.get("siradaki")
        line = next_line(titles.get(nxt) or videos.get(nxt, {}).get("title", ""), nxt) if nxt else None
        title = it.get("baslik") or snip["title"]
        if len(title) > 100:
            out.append({"id": it["id"], "hata": f"başlık 100 karakteri aşıyor ({len(title)})"})
            continue
        desc = new_description(snip.get("description", ""), line)
        if title == snip["title"] and desc == snip.get("description", ""):
            continue
        body = {k: snip[k] for k in ("categoryId", "tags", "defaultLanguage", "defaultAudioLanguage")
                if k in snip}
        body.update(title=title, description=desc)
        out.append({"id": it["id"], "eski_baslik": snip["title"], "yeni_baslik": title,
                    "siradaki": line, "snippet": body})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dosya")
    ap.add_argument("--uygula", action="store_true")
    a = ap.parse_args(argv)
    items = json.loads(Path(a.dosya).read_text(encoding="utf-8"))["videolar"]

    from scripts.channel_setup import _youtube
    yt = _youtube()
    ids = sorted({i["id"] for i in items} | {i["siradaki"] for i in items if i.get("siradaki")})
    res = yt.videos().list(part="snippet", id=",".join(ids)).execute().get("items", [])
    videos = {v["id"]: v["snippet"] for v in res}

    changes = plan_changes(items, videos)
    rapor = []
    for c in changes:
        if "hata" in c:
            rapor.append(f"⚠️ {c['id']}: {c['hata']}")
            continue
        if a.uygula:
            yt.videos().update(part="snippet", body={"id": c["id"], "snippet": c["snippet"]}).execute()
        rapor.append(f"{'✓' if a.uygula else '•'} {c['id']}: {c['eski_baslik']} ⇒ {c['yeni_baslik']}"
                     + (f"\n   {c['siradaki']}" if c["siradaki"] else ""))
    if not rapor:
        rapor.append("Değişecek bir şey yok.")
    text = ("✅ Videolar güncellendi:\n" if a.uygula else "🔎 Kuru çalışma (değişiklik yapılmadı):\n") + "\n".join(rapor)
    print(text)
    try:
        from scripts.notifier import send_message
        send_message(text, parse_mode=None)
    except Exception:
        pass
    return 1 if any(r.startswith("⚠️") for r in rapor) else 0


if __name__ == "__main__":
    sys.exit(main())
