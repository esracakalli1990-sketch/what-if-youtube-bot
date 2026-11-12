"""senaryo.md → senaryo.json (anlatım metni + taslak çekim listesi).

Anlatım metni ve bölüm yapısı senaryo.md'den okunur (onaylı tek kaynak).
Çekimler [EKRAN: …] satırlarındaki klip kimliklerinden (y01, z05…) ve geçiş
işaretlerinden (/kes/ /erit/ /karart/ /parla/) taslak olarak çıkarılır; ses
üretildikten sonra cekimler.py ile gerçek sürelere göre ince ayar yapılır.

python belgeseller/04-yavuz/araclar/plan_kur.py
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
import sys  # noqa: E402
sys.path.insert(0, str(HERE))
from haritalar import M as MAPS  # noqa: E402
ROOT = HERE.parent
GECIS = {"kes": "cut", "erit": "dissolve", "karart": "black", "parla": "flash"}
MUZIK = ["karanlik", "gizem", "agir", "karanlik", "derin", "karanlik", "agir", "derin", "isik", "huzun", "huzun"]


def tr_title(text: str) -> str:
    """Türkçe başlık biçimi: "TRABZON'DAKİ ŞEHZADE" → "Trabzon'daki Şehzade"."""
    def word(w):
        low = w.replace("I", "ı").replace("İ", "i").lower()
        first = {"i": "İ", "ı": "I"}.get(low[0], low[0].upper())
        return first + low[1:] if low not in ("ve",) else low
    return " ".join(word(w) for w in text.split())


def ekran_shots(line: str) -> list[dict]:
    """[EKRAN: …] satırından klip sırası ve her klibe GİRİŞ geçişi."""
    shots, pending = [], None
    for tok in re.finditer(r"/(kes|erit|karart|parla)/|\b([yz]\d\d)\b|\b((?:m|k)_\w+)\b|\b(s_\w+)\b", line):
        if tok.group(3) or tok.group(4):          # harita / kart / stok video
            s = {"map": tok.group(3)} if tok.group(3) else {"stock": tok.group(4)}
            if pending:
                s["transition"] = pending
            shots.append(s)
            pending = None
            continue
        if tok.group(1):
            if tok.group(1) == "parla" and shots:      # parlama: klibin İÇİNDEKİ top atışından sonraki kesme
                pending = "flash"
            else:
                pending = GECIS[tok.group(1)]
        else:
            name = tok.group(2)
            if shots and shots[-1].get("clip", "").endswith(f"/{name}.mp4"):
                continue
            s = {"clip": f"klipler/{name}.mp4"}
            if pending:
                s["transition"] = pending
            shots.append(s)
            pending = None
    return shots


def parse(md: str) -> list[dict]:
    body = md.split("# DOĞRULA")[0]
    chapters, ch, ekran = [], None, []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("## "):
            title = line[3:].strip()
            title = tr_title(title.split("—", 1)[1].strip() if "—" in title else title)
            ch = {"title": title, "paragraphs": []}
            chapters.append(ch)
            ekran = []
            continue
        if line.startswith("*Kart:"):
            parts = [p.strip() for p in line.strip("*").split("·")]
            ch["card"] = {"kicker": parts[0].replace("Kart:", "").strip().upper(),
                          "date": " · ".join(parts[2:])}
            continue
        if line.startswith("[EKRAN"):
            ekran += ekran_shots(line)
            continue
        if not line or line.startswith(("#", "*", ">", "---", "|", "-")):
            continue
        ch["paragraphs"].append({"text": line, "shots": ekran or [{"clip": "klipler/TBD.mp4"}]})
        ekran = []
    for i, c in enumerate(chapters):
        c["music"] = MUZIK[i % len(MUZIK)]
    return chapters


def main():
    md = (ROOT / "senaryo.md").read_text(encoding="utf-8")
    ist = json.loads((ROOT.parent / "03-istanbul" / "senaryo.json").read_text(encoding="utf-8"))
    data = {
        "slug": "04-yavuz",
        "title": "Yavuz Sultan Selim: 8 Yılda Bir Dünya İmparatorluğu | Çaldıran'dan Kahire'ye",
        "description": (
            "1514 yazı, Çaldıran ovası. Zincirlenmiş toplar, kırmızı başlıklı Kızılbaş süvarileri ve tepede "
            "her şeyi tek bir savaşa yatırmış bir sultan.\n\n"
            "Bu belgeselde Yavuz Sultan Selim'in hikâyesini anlatıyoruz: Trabzon'daki şehzadelik yıllarından "
            "babasına karşı verdiği taht mücadelesine, Çaldıran'da Şah İsmail'le hesaplaşmasından Mercidabık ve "
            "Ridaniye'ye, Sina Çölü'nü bir orduyla geçişinden Kahire'ye ve kutsal emanetlere kadar. Tartışmalı "
            "bilgiler anlatımda \"rivayete göre\" ya da \"kaynaklara göre\" diye belirtilmiştir.\n\n"
            "Serinin önceki bölümleri: İstanbul'un Fethi → https://youtu.be/AI-RfRzQfos · "
            "Antik Mısır → https://youtu.be/Ns-ozDX_Y6g · Hitit İmparatorluğu → https://youtu.be/ibuMFDr7rmI"),
        "tags": ["yavuz sultan selim", "çaldıran savaşı", "mercidabık", "ridaniye", "şah ismail",
                 "osmanlı tarihi", "memlükler", "tomanbay", "kansu gavri", "kutsal emanetler",
                 "osmanlı belgeseli", "tarih belgeseli", "türk tarihi", "1514", "1517", "belgesel",
                 "türkçe belgesel"],
        "hashtags": ["#YavuzSultanSelim", "#Çaldıran", "#OsmanlıTarihi", "#Belgesel", "#Tarih"],
        "ai_disclosure": ("Bu belgeseldeki canlandırma sahneleri yapay zekâ ile üretilmiştir ve temsilidir; "
                          "videoda \"Temsili canlandırma\" olarak işaretlidir."),
        "sources": [
            "Feridun M. Emecen, Yavuz Sultan Selim",
            "Halil İnalcık, Osmanlı İmparatorluğu Klasik Çağ (1300–1600)",
            "TDV İslâm Ansiklopedisi: Selim I, Bayezid II, Çaldıran Savaşı, Mercidabık Savaşı, Ridaniye Savaşı, "
            "Kansu Gavri, Tomanbay, Şahkulu, Şah İsmail, Pîrî Reis, İdrîs-i Bitlisî",
            "Roger Savory, Iran under the Safavids",
            "Celalzade Mustafa, Selimnâme; Hoca Sadeddin, Tâcü't-Tevârîh",
        ],
        "tts_model": ist.get("tts_model", "eleven_v4"),
        "voice_settings": ist["voice_settings"],
        "pronunciations": {"Mercidabık": "Merci-dâbık", "Bâbüzzüveyle": "Bâbüz-züveyle",
                           "Gavri": "Gavrî", "Ridaniye": "Rîdâniye", "şirpençe": "şîr-pençe"},
        "ilk_yorum": ("Sizce Yavuz'un en büyük hamlesi hangisiydi: Çaldıran mı, Mercidabık mı, yoksa ordusuyla "
                      "Sina Çölü'nü geçmesi mi? Yorumlarda tartışalım.\n\n"
                      "🔔 Sıradaki belgesel: Kanuni Sultan Süleyman."),
        "kurgu": {"gecis": "cut", "ton_esitle": 0.5},
        "music_sources": ist["music_sources"],
        "images": {"dunya": {"commons": "File:Whole world - land and oceans 12000.jpg", "original": True}},
        "stock": {"s_yavuz_camii": {"q": "Yavuz Selim mosque Istanbul"}},
        "films": {},
        "maps": MAPS,
        "chapters": parse(md),
    }
    (ROOT / "senaryo.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(c["paragraphs"]) for c in data["chapters"])
    chars = sum(len(re.sub(r"\[[^\]]*\]", "", p["text"])) for c in data["chapters"] for p in c["paragraphs"])
    print(f"{len(data['chapters'])} bölüm, {n} paragraf, {chars} karakter")


if __name__ == "__main__":
    main()
