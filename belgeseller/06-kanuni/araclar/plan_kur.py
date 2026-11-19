"""Kanuni Sultan Süleyman: senaryo.md → senaryo.json.

Çekim türleri ([EKRAN: …] satırlarından):
  c01…c52  Google Flow klipleri (klipler/cNN.mp4)
  r_…      Wikimedia Commons'taki gerçek dönem eserleri (görsel)
  m_… k_…  hareketli harita / bilgi grafiği (haritalar.py; seslendirmeden sonra eklenecek)

Seslendirme uyku hesabıyla ama Seyfullah Kartal sesiyle yapılır (voice_id senaryoda).

    python belgeseller/06-kanuni/araclar/plan_kur.py
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT.parents[1]))
sys.path.insert(0, str(HERE))
from haritalar import M as MAPS, esnet  # noqa: E402
from cekimler import SHOTS  # noqa: E402

SEYFULLAH_KARTAL = "mF7tIc9VLrznhGooGjaT"       # ElevenLabs ses kütüphanesi (herkese açık kimlik)
GECIS = {"kes": "cut", "erit": "dissolve", "karart": "black", "parla": "flash"}
AI_CREDIT = {"title": "Temsili canlandırma", "artist": "Yapay zekâ ile üretildi (Google Flow / Gemini)", "license": "—"}
KARELER = [f"kart{i}" for i in range(1, 10)] + ["kapak1", "kapak2", "kapak3"]
SESSIZ = {"c45"}            # konuşma sesi içeren klipler: doğal sesi kapatılır
MUZIK = ["karanlik", "gizem", "agir", "karanlik", "derin", "derin", "gizem", "huzun", "huzun", "agir", "huzun"]


def tr_title(text: str) -> str:
    def word(w):
        low = w.replace("I", "ı").replace("İ", "i").lower()
        first = {"i": "İ", "ı": "I"}.get(low[0], low[0].upper())
        return first + low[1:] if low not in ("ve",) else low
    return " ".join(word(w) for w in text.split())


def ekran_shots(line: str) -> list[dict]:
    """[EKRAN: …] → çekim sırası ve her çekime GİRİŞ geçişi. Parantez içi açıklamalar atlanır."""
    line = re.sub(r"\([^)]*\)", "", line)
    shots, pending = [], None
    for tok in re.finditer(r"/(kes|erit|karart|parla)/|\b(c\d\d)\b|\b((?:m|k)_\w+)\b|\b(r_\w+)\b", line):
        if tok.group(1):
            pending = GECIS[tok.group(1)]
            continue
        if tok.group(2):
            s = {"clip": f"klipler/{tok.group(2)}.mp4"}
        elif tok.group(3):
            s = {"map": tok.group(3)}
        else:
            s = {"image": tok.group(4), "move": "in"}
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
            ch["card"] = {"kicker": parts[0].replace("Kart:", "").strip().upper(), "date": " · ".join(parts[2:])}
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
        if c.get("card") and 1 <= i <= 9:
            c["card"]["image"] = f"kart{i}"
        for p in c["paragraphs"]:
            for sh in p["shots"]:
                if sh.get("clip", "").split("/")[-1][:-4] in SESSIZ:
                    sh["sfx"] = False
    return chapters


def apply_shots(data: dict) -> None:
    """cekimler.py'deki listeyi uygula; ilk çekimin giriş geçişi senaryodaki gibi kalır."""
    for ci, ch in enumerate(data["chapters"]):
        for pi, para in enumerate(ch["paragraphs"]):
            new = SHOTS.get(f"{ci}.{pi}")
            if not new:
                continue
            new = [dict(s) for s in new]
            tr = para["shots"][0].get("transition")
            if tr and "transition" not in new[0]:
                new[0]["transition"] = tr
            para["shots"] = new


def stretch_maps(data: dict) -> None:
    """Haritaları gerçek ses yuvasına göre uzat (build/audio varsa)."""
    manifest = ROOT / "build" / "audio" / "manifest.json"
    if not manifest.exists():
        return
    from scripts import doc_timeline as dt
    audio = json.loads(manifest.read_text(encoding="utf-8"))
    for ci, ch in enumerate(data["chapters"]):
        for pi, para in enumerate(ch["paragraphs"]):
            au = audio[ci][pi]
            words = json.loads((ROOT / "build" / au["words_path"]).read_text(encoding="utf-8")) \
                if "words_path" in au else au.get("words", [])
            cuts = dt._cut_points(words, len(para["shots"]), au["duration"])
            bounds = [0.0] + cuts + [au["duration"] + dt.PARAGRAPH_GAP]
            for si, shot in enumerate(para["shots"]):
                if "map" in shot:
                    slot = bounds[si + 1] - bounds[si] + 1.0
                    data["maps"][shot["map"]] = esnet(data["maps"][shot["map"]], max(slot, 8.0))


def main():
    md = (ROOT / "senaryo.md").read_text(encoding="utf-8")
    yavuz = json.loads((ROOT.parent / "04-yavuz" / "senaryo.json").read_text(encoding="utf-8"))
    data = {
        "slug": "06-kanuni",
        "title": "Kanuni Sultan Süleyman: 46 Yıl, 13 Sefer, Tek Bir Sır | Mohaç'tan Zigetvar'a",
        "description": (
            "Eylül 1566, Zigetvar. Yetmiş bir yaşındaki padişah gece yarısı öldü ve bu ölüm 48 gün saklandı.\n\n"
            "Bu belgeselde Kanuni Sultan Süleyman'ın hikâyesini anlatıyoruz: Trabzon'daki doğumundan Belgrad ve "
            "Rodos'a, Mohaç'tan Viyana kapılarına, Barbaros ve Preveze'den kanunlara ve Mimar Sinan'ın kubbelerine, "
            "İbrahim Paşa, Hürrem ve Şehzade Mustafa'dan Zigetvar'daki son sefere kadar. Tartışmalı bilgiler "
            "anlatımda \"rivayete göre\" ya da \"kaynaklara göre\" diye belirtilmiştir.\n\n"
            "Serinin önceki bölümleri: Yavuz Sultan Selim → https://youtu.be/J0DGI9Kqlqc · "
            "İstanbul'un Fethi → https://youtu.be/AI-RfRzQfos"),
        "tags": ["kanuni sultan süleyman", "muhteşem süleyman", "mohaç", "viyana kuşatması", "preveze",
                 "barbaros", "mimar sinan", "hürrem sultan", "ibrahim paşa", "şehzade mustafa", "zigetvar",
                 "osmanlı tarihi", "osmanlı belgeseli", "tarih belgeseli", "belgesel", "türkçe belgesel"],
        "hashtags": ["#KanuniSultanSüleyman", "#Mohaç", "#OsmanlıTarihi", "#Belgesel", "#Tarih"],
        "ai_disclosure": ("Bu belgeseldeki canlandırma sahneleri yapay zekâ ile üretilmiştir ve temsilidir; "
                          "videoda \"Temsili canlandırma\" olarak işaretlidir."),
        "sources": [
            "TDV İslâm Ansiklopedisi: Süleyman I, İbrâhim Paşa (Makbul), Hürrem Sultan, Mustafa Sultan, Mohaç, "
            "Viyana Kuşatması, Preveze, Zigetvar Seferi, Barbaros Hayreddin, Mimar Sinan",
            "Halil İnalcık, Osmanlı İmparatorluğu Klasik Çağ (1300–1600)",
            "Feridun M. Emecen, Kanuni Sultan Süleyman ve Zamanı",
            "Arifî, Süleymanname (Topkapı Sarayı Müzesi)",
            "Selânikî Mustafa Efendi, Tarih-i Selânikî",
        ],
        "tts_model": yavuz.get("tts_model", "eleven_v4"),
        "voice_id": SEYFULLAH_KARTAL,
        "voice_settings": yavuz["voice_settings"],
        "pronunciations": {"Zrinyi": "Zirinyi", "Roxelana": "Roksolana", "Muhibbi": "Muhibbî",
                           "François": "Fransuva", "Toulon'da": "Tulon'da", "Zapolya": "Zapolya",
                           "Layoş": "Layoş"},
        "ilk_yorum": ("Sizce Kanuni'nin en büyük başarısı hangisiydi: Mohaç mı, kanunlar mı, yoksa Süleymaniye mi? "
                      "Yorumlarda konuşalım.\n\n🔔 Serinin sıradaki bölümü için kanala abone olun."),
        "kurgu": {"gecis": "cut", "ton_esitle": 0.5, "bolum_sonu": 3.5, "bolum_karartma": 2.0},
        "music_sources": {k: v for k, v in yavuz["music_sources"].items() if k != "isik"},   # "Bathed in the Light" telif talebi aldı
        "images": {   # Wikimedia Commons, kamu malı / CC0
            "dunya": {"commons": "File:Whole world - land and oceans 12000.jpg", "original": True},
            "r_kanuni_genc": {"commons": "File:Istanbul, Topkapi Palace Museum MS Hazine 1563 fol. 47v Suleyman I by Nakkaş Osman.jpg"},
            "r_suleymanname_mohac": {"commons": "File:1526-Sultan Suleiman during the Battle of Mohacs-Suleymanname.jpg"},
            "r_lorck_kanuni": {"commons": "File:EmperorSuleiman.jpg"},
            "r_lorck_kanuni_yasli": {"commons": "File:Melchior Lorck Sultan Suleiman.jpg"},
            "r_barbaros": {"commons": "File:Agostino dei Musi, Barbarossa, Khair-ed-Din, 1535, NGA 46891.jpg"},
            "r_piri_reis_harita": {"commons": "File:Piri reis world map 01.jpg"},
            "r_tugra": {"commons": "File:Tughra (Official Signature) of Sultan Süleiman the Magnificent (r. 1520–66) MET DP234753.jpg"},
            "r_tugra2": {"commons": "File:Tughra (Official Signature) of Sultan Süleiman the Magnificent (r. 1520–66) MET 116663.jpg"},
            "r_migferli": {"commons": "File:Emperor Turc - Sultan Suleyman the Magnificent Wearing the Jewel-Studded Helmet.jpg", "min_width": 1200},
            "r_preveze": {"commons": "File:Battle of Preveza (1538).jpg", "min_width": 1200},
            "r_lorck_camii": {"commons": "File:Sultan Süleyman and the Süleymaniye Mosque, Constantinople, 1574 (or earlier) , altered in 1688 to represent Ibrahim I MET DP146517.jpg"},
            "r_hurrem": {"commons": "File:Titian - Portrait of a Woman (La Sultana Rossa).jpg", "min_width": 1200},
            **{k: {"file": f"kareler/{k}.jpg", "credit": AI_CREDIT} for k in KARELER},
        },
        "thumbnails": [
            {"sablon": "v2", "arka_plan": "kapak1", "arka_plan_kadraj": "50% 40%", "hale": "transparent",
             "line1": "48 gün", "line2": "saklandı", "vurgu": "#FFC83D"},
            {"sablon": "v2", "arka_plan": "kapak2", "arka_plan_kadraj": "50% 50%", "hale": "transparent",
             "line1": "2 saatte", "line2": "bir krallık", "vurgu": "#FFC83D"},
            {"sablon": "v2", "arka_plan": "kapak3", "arka_plan_kadraj": "50% 30%", "hale": "transparent",
             "line1": "Viyana", "line2": "kapılarında", "vurgu": "#FFC83D"}],
        "stock": {},
        "films": {},
        "maps": dict(MAPS),
        "chapters": parse(md),
    }
    apply_shots(data)
    # Yer tutucular: harita ve Commons eserleri seslendirmeden sonra (haritalar.py / gerçek dosya adları) eklenecek
    for c in data["chapters"]:
        for p in c["paragraphs"]:
            for sh in p["shots"]:
                if "image" in sh:
                    data["images"].setdefault(sh["image"], {"file": f"gorseller/{sh['image']}.jpg",
                                                            "credit": {"title": "TBD", "artist": "", "license": ""}})
                if "map" in sh:
                    data["maps"].setdefault(sh["map"], {"bilesen": "Infographic", "type": "zaman",
                                                        "title": sh["map"], "durationSec": 10, "events": []})
    stretch_maps(data)
    (ROOT / "senaryo.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(c["paragraphs"]) for c in data["chapters"])
    chars = sum(len(re.sub(r"\[[^\]]*\]", "", p["text"])) for c in data["chapters"] for p in c["paragraphs"])
    print(f"{len(data['chapters'])} bölüm, {n} paragraf, {chars} karakter")


if __name__ == "__main__":
    main()
