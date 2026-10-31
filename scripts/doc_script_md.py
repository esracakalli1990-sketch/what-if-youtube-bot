"""
doc_script_md.py - Okunabilir senaryo (.md) → üretim senaryosu (senaryo.json).

Senaryo, kullanıcının okuyup onayladığı tek kaynak olsun diye markdown'da
yazılır. Bu modül anlatım paragraflarını ve bölüm kartlarını .md'den alır,
çekim planını (görsel, hareket, etiket) ayrı bir plan dosyasından
(cekim_plani.json) birleştirir. Böylece metin düzeltmesi çekim planını,
çekim planı düzeltmesi metni bozmaz.

    python -m scripts.doc_script_md belgeseller/01-hititler
"""

import json
import re
import sys
from pathlib import Path

CHAPTER_RE = re.compile(r"^##\s+(.+?)\s*$")
CARD_RE = re.compile(r"^\*Kart:\s*(.+?)\*\s*$")
SCREEN_RE = re.compile(r"^\[EKRAN:\s*(.+?)\]\s*$")


def tr_title(text: str) -> str:
    """Türkçe baş harf büyütme: "GİRİŞ" → "Giriş" (str.title() noktalı İ'yi bozar)."""
    lower = text.replace("İ", "i").replace("I", "ı").lower()
    return " ".join(w[:1].replace("i", "İ").replace("ı", "I").upper() + w[1:] for w in lower.split())


def parse_markdown(text: str) -> list[dict]:
    """Bölümler: {"title", "card": {kicker, title, date} | None, "paragraphs": [{"text", "screen"}]}"""
    body = text.split("# DOĞRULA TABLOSU")[0]
    chapters, cur, screen = [], None, ""
    for raw in body.splitlines():
        line = raw.strip()
        m = CHAPTER_RE.match(line)
        if m:
            heading = m.group(1)
            title = heading.split("—", 1)[1].strip() if "—" in heading else heading
            cur = {"heading": heading, "title": tr_title(title) if title.isupper() else title,
                   "card": None, "paragraphs": []}
            chapters.append(cur)
            screen = ""
            continue
        if cur is None or not line or line.startswith(("---", ">", "**")):
            continue
        m = CARD_RE.match(line)
        if m:
            parts = [p.strip() for p in m.group(1).split("·")]
            kicker, title = parts[0], parts[1] if len(parts) > 1 else cur["title"]
            date = " · ".join(parts[2:])
            cur["card"] = {"kicker": kicker, "date": date}
            cur["title"] = title
            continue
        m = SCREEN_RE.match(line)
        if m:
            screen = m.group(1)
            continue
        if line.startswith(("#", "*", "[")):
            continue
        cur["paragraphs"].append({"text": line, "screen": screen})
    return [c for c in chapters if c["paragraphs"]]


def build(folder: Path) -> dict:
    folder = Path(folder)
    chapters = parse_markdown((folder / "senaryo.md").read_text(encoding="utf-8"))
    plan = json.loads((folder / "cekim_plani.json").read_text(encoding="utf-8"))
    shots_by_para = plan.get("shots", {})
    out_chapters = []
    for ci, ch in enumerate(chapters):
        paragraphs = []
        for pi, para in enumerate(ch["paragraphs"]):
            key = f"{ci}.{pi}"
            shots = shots_by_para.get(key)
            if not shots:
                raise ValueError(f"Çekim planında {key} yok: {para['text'][:60]}…")
            paragraphs.append({"text": para["text"], "shots": shots})
        chapter = {"title": ch["title"], "paragraphs": paragraphs,
                   "music": plan.get("music", {}).get(str(ci))}
        if ch["card"]:
            chapter["card"] = {**ch["card"], "image": plan.get("cards", {}).get(str(ci), "")}
        out_chapters.append(chapter)
    meta = {k: v for k, v in plan.items() if k not in ("shots", "cards", "music")}
    return {**meta, "chapters": out_chapters}


def outline(folder: Path) -> str:
    """Çekim planı yazarken kullanılacak paragraf listesi (anahtar, karakter, ekran notu)."""
    chapters = parse_markdown((Path(folder) / "senaryo.md").read_text(encoding="utf-8"))
    lines = []
    for ci, ch in enumerate(chapters):
        lines.append(f"## {ci} {ch['title']}  kart={bool(ch['card'])}")
        for pi, p in enumerate(ch["paragraphs"]):
            lines.append(f"{ci}.{pi} [{len(p['text'])}] ({p['screen']}) {p['text'][:70]}")
    return "\n".join(lines)


if __name__ == "__main__":
    folder = Path(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2] == "--taslak":
        print(outline(folder))
    else:
        data = build(folder)
        (folder / "senaryo.json").write_text(json.dumps(data, ensure_ascii=False, indent=1),
                                             encoding="utf-8")
        print("senaryo.json yazıldı:", sum(len(c["paragraphs"]) for c in data["chapters"]), "paragraf")
