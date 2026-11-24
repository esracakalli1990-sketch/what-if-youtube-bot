"""Sümerler belgeseli: senaryo.md → senaryo.json.

Görsel kavramı (kullanıcı kararı): Mısır/Hitit gibi gerçek müze eserleri (Commons), gerçek mekân
videoları (Pexels/Commons) ve hareketli haritalar. Yapay zekâ klibi yok.
Çekimler `cekimler.py`'de (anahtar "bölüm.paragraf"), görseller `gorseller.py`'de, haritalar `haritalar.py`'de.

    python belgeseller/08-sumerler/araclar/plan_kur.py
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT.parents[1]))
sys.path.insert(0, str(HERE))

try:
    from cekimler import SHOTS, CARDS  # noqa: E402
except ImportError:          # taslak (yalnızca ses) aşaması
    SHOTS, CARDS = {}, {}
try:
    from gorseller import IMAGES, STOCK  # noqa: E402
except ImportError:
    IMAGES, STOCK = {}, {}
try:
    from haritalar import M as MAPS  # noqa: E402
except ImportError:
    MAPS = {}

SEYFULLAH_KARTAL = "mF7tIc9VLrznhGooGjaT"
MUZIK = ["gizem", "derin", "gizem", "tapinak", "karanlik", "agir", "ses", "agir", "tapinak", "huzun", "derin", "huzun"]


def tr_title(text: str) -> str:
    def word(w):
        low = w.replace("I", "ı").replace("İ", "i").lower()
        first = {"i": "İ", "ı": "I"}.get(low[0], low[0].upper())
        return first + low[1:] if low not in ("ve",) else low
    return " ".join(word(w) for w in text.split())


def parse(md: str) -> list[dict]:
    body = md.split("# DOĞRULA")[0]
    chapters, ch = [], None
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("## "):
            title = line[3:].strip()
            title = tr_title(title.split("—", 1)[1].strip() if "—" in title else title)
            ch = {"title": title, "paragraphs": []}
            chapters.append(ch)
            continue
        if line.startswith("*Kart:"):
            parts = [p.strip() for p in line.strip("*").split("·")]
            ch["card"] = {"kicker": parts[0].replace("Kart:", "").strip().upper(), "date": " · ".join(parts[2:])}
            continue
        if not line or line.startswith(("#", "*", ">", "---", "|", "-", "[EKRAN")):
            continue
        ch["paragraphs"].append({"text": line})
    for ci, c in enumerate(chapters):
        c["music"] = MUZIK[ci % len(MUZIK)]
        if c.get("card") and str(ci) in CARDS:
            c["card"]["image"] = CARDS[str(ci)]
        for pi, p in enumerate(c["paragraphs"]):
            p["shots"] = [dict(s) for s in SHOTS.get(f"{ci}.{pi}", [{"clip": "klipler/TBD.mp4"}])]
    return chapters


def stretch_maps(data: dict) -> None:
    """Haritaları gerçek ses yuvasına göre uzat (build/audio varsa)."""
    manifest = ROOT / "build" / "audio" / "manifest.json"
    if not manifest.exists() or not data["maps"]:
        return
    from scripts import doc_timeline as dt
    from haritalar import esnet
    audio = json.loads(manifest.read_text(encoding="utf-8"))
    for ci, ch in enumerate(data["chapters"]):
        for pi, para in enumerate(ch["paragraphs"]):
            au = audio[ci][pi]
            words = json.loads((ROOT / "build" / au["words_path"]).read_text(encoding="utf-8")) \
                if "words_path" in au else au.get("words", [])
            cuts = dt._cut_points(words, len(para["shots"]), au["duration"])
            bounds = [0.0] + cuts + [au["duration"] + dt.PARAGRAPH_GAP]
            for si, shot in enumerate(para["shots"]):
                if "map" in shot and si + 1 < len(bounds):
                    slot = bounds[si + 1] - bounds[si] + 1.0
                    data["maps"][shot["map"]] = esnet(data["maps"][shot["map"]], max(slot, 8.0))


def main():
    md = (ROOT / "senaryo.md").read_text(encoding="utf-8")
    yavuz = json.loads((ROOT.parent / "04-yavuz" / "senaryo.json").read_text(encoding="utf-8"))
    data = {
        "slug": "08-sumerler",
        "title": "Sümerler: Yazıyı İcat Eden İnsanlar | Uruk'tan Ur'a İlk Uygarlığın Tam Hikâyesi",
        "description": (
            "Tarih, yazıyla başlar. Ve yazı, beş bin yıl önce Dicle ile Fırat'ın arasında, Sümerlerin şehirlerinde doğdu.\n\n"
            "Bu belgeselde ilk şehir Uruk'tan yazının bir hesap pusulasıyla başlayan hikâyesine, Lagaş ile Umma'nın "
            "savaşından Ur'un altın dolu kraliyet mezarlarına, Gılgamış Destanı ve tufan tabletinden ilk imparatorluk "
            "Akad'a, adı bilinen ilk yazar Enheduanna'dan İstanbul Arkeoloji Müzeleri'nde duran Ur-Nammu yasalarına "
            "kadar Sümerlerin tam hikâyesini, gerçek müze eserleri eşliğinde anlatıyoruz. Tartışmalı bilgiler "
            "anlatımda öyle belirtilmiştir.\n\n"
            "Serinin önceki bölümleri: Antik Mısır → https://youtu.be/Ns-ozDX_Y6g · "
            "Hititler → https://youtu.be/ibuMFDr7rmI"),
        "tags": ["sümerler", "sümer", "mezopotamya", "yazının icadı", "çivi yazısı", "gılgamış destanı", "ur",
                 "uruk", "akad", "sargon", "enheduanna", "ur-nammu", "antik tarih", "ilk uygarlık",
                 "tarih belgeseli", "belgesel", "türkçe belgesel"],
        "hashtags": ["#Sümerler", "#Mezopotamya", "#AntikTarih", "#Belgesel", "#Tarih"],
        "ai_disclosure": "",
        "sources": [
            "Samuel Noah Kramer, The Sumerians: Their History, Culture, and Character; History Begins at Sumer",
            "J. N. Postgate, Early Mesopotamia: Society and Economy at the Dawn of History",
            "Michael Roaf, Cultural Atlas of Mesopotamia and the Ancient Near East",
            "Andrew George, The Epic of Gilgamesh (Penguin, 2003)",
            "Martha Roth, Law Collections from Mesopotamia and Asia Minor",
            "Electronic Text Corpus of Sumerian Literature (ETCSL), Oxford",
        ],
        "tts_model": yavuz.get("tts_model", "eleven_v4"),
        "voice_id": SEYFULLAH_KARTAL,
        "voice_settings": yavuz["voice_settings"],
        "pronunciations": {"Woolley": "Vuli", "Woolley'nin": "Vuli'nin", "Woolley'yi": "Vuli'yi",
                           "George": "Corc", "Smith": "Smit",
                           "Louvre": "Luvr", "Louvre'da": "Luvr'da",
                           "Louvre'daki": "Luvr'daki"},
        "ilk_yorum": ("Sizce Sümerlerin en büyük icadı hangisiydi: yazı mı, şehir mi, yoksa yasalar mı? "
                      "Yorumlarda konuşalım.\n\n🔔 Serinin sıradaki bölümü için kanala abone olun."),
        "kurgu": {"gecis": "dissolve", "ton_esitle": 0.5, "bolum_sonu": 3.5, "bolum_karartma": 2.0},
        "music_sources": {k: v for k, v in yavuz["music_sources"].items() if k != "isik"},  # "isik" telif talebi aldı
        "images": dict(IMAGES),
        "thumbnails": [
            {"sablon": "v2", "arka_plan": "tab1", "arka_plan_kadraj": "60% 50%", "hale": "transparent",
             "line1": "İlk", "line2": "yazı", "vurgu": "#FFC83D"},
            {"sablon": "v2", "arka_plan": "puabi1", "arka_plan_kadraj": "50% 40%", "hale": "transparent",
             "line1": "4500 yıllık", "line2": "mezar", "vurgu": "#FFC83D"},
            {"sablon": "v2", "arka_plan": "tufan2", "arka_plan_kadraj": "50% 50%", "hale": "transparent",
             "line1": "Tufanı ilk", "line2": "onlar yazdı", "vurgu": "#FFC83D"}],
        "stock": dict(STOCK),
        "films": {},
        "maps": dict(MAPS),
        "chapters": parse(md),
    }
    stretch_maps(data)
    (ROOT / "senaryo.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(c["paragraphs"]) for c in data["chapters"])
    chars = sum(len(re.sub(r"\[[^\]]*\]", "", p["text"])) for c in data["chapters"] for p in c["paragraphs"])
    print(f"{len(data['chapters'])} bölüm, {n} paragraf, {chars} karakter")


if __name__ == "__main__":
    main()
