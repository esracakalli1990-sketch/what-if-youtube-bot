"""Cem Sultan uyku belgeseli: senaryo.md → senaryo.json.

Uyku formatı: yalnızca çizim görseller (g01…g46) + bir sürgün haritası; yavaş çapraz geçişler,
her görselde yavaş Ken Burns hareketi; sakin müzik; yavaş ve yumuşak anlatım.

    python belgeseller/05-uyku-cem-sultan/araclar/plan_kur.py
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT.parents[1]))
from scripts.doc_maps import fit_bounds  # noqa: E402

AI_CREDIT = {"title": "Temsili çizim", "artist": "Yapay zekâ ile üretildi (Gemini)", "license": "—"}
GORSELLER = [f"g{i:02d}" for i in range(1, 47)] + ["kapak1", "kapak2"]
KART = ["g07", "g11", "g02", "g19", "g25", "g33", "g36", "g44", "g46"]      # Bölüm I…IX kart görselleri
MUZIK = ["derin", "isik", "huzun", "derin", "gizem", "huzun", "derin", "isik", "huzun", "derin"]
HAREKET = ["in", "left", "out", "right"]
XFADE = 2.5                      # yavaş çapraz geçiş (sn)

# ── Sürgün haritası (boylam, enlem) ──
C = {"Bursa": [29.06, 40.18], "Yenişehir": [29.65, 40.26], "Konya": [32.49, 37.87], "Halep": [37.16, 36.2],
     "Şam": [36.29, 33.51], "Kahire": [31.24, 30.04], "Rodos": [28.22, 36.44], "Nice": [7.26, 43.7],
     "Bourganeuf": [1.76, 45.95], "Roma": [12.5, 41.9], "Napoli": [14.27, 40.85]}
SURGUN = "#c99a2e"


def _city(name, start, major=False, side=None):
    c = {"at": C[name], "label": name, "start": start}
    if major:
        c["major"] = True
    if side:
        c["side"] = side
    return c


MAPS = {
    "m_surgun": {
        "taban": "dunya", "bounds": fit_bounds((20.5, 36.5), 40), "durationSec": 24,
        "title": "Cem Sultan'ın Yolculuğu", "subtitle": "1481–1499",
        "routes": [
            {"points": [C["Bursa"], C["Konya"], C["Halep"], C["Şam"], C["Kahire"]], "color": SURGUN,
             "start": 1.0, "duration": 5.0, "label": "1481", "dashed": True},
            {"points": [C["Kahire"], [33.5, 33.0], C["Konya"], [33.0, 36.3], C["Rodos"]], "color": SURGUN,
             "start": 6.5, "duration": 3.5, "label": "1482", "dashed": True},
            {"points": [C["Rodos"], [20.0, 36.0], [12.0, 38.5], [8.5, 42.0], C["Nice"]], "color": SURGUN,
             "start": 10.5, "duration": 3.5, "label": "", "dashed": True},
            {"points": [C["Nice"], [5.0, 45.0], C["Bourganeuf"]], "color": SURGUN,
             "start": 14.2, "duration": 2.0, "label": "", "dashed": True},
            {"points": [C["Bourganeuf"], [6.0, 44.5], [10.0, 43.0], C["Roma"]], "color": SURGUN,
             "start": 16.5, "duration": 2.5, "label": "1489", "dashed": True},
            {"points": [C["Roma"], C["Napoli"]], "color": SURGUN, "start": 19.3, "duration": 1.2,
             "label": "1495", "dashed": True}],
        "cities": [_city("Bursa", 0.5, major=True, side="right"), _city("Konya", 1.6), _city("Halep", 3.2),
                   _city("Şam", 4.2, side="right"), _city("Kahire", 5.6, major=True, side="left"),
                   _city("Rodos", 9.8, side="left"), _city("Nice", 13.8, side="left"),
                   _city("Bourganeuf", 15.8, side="right"), _city("Roma", 18.6, major=True, side="left"),
                   _city("Napoli", 20.3, side="right")],
        "labels": [{"at": [18.0, 34.0], "text": "Akdeniz", "start": 0.4, "kind": "sea"}],
        "years": [{"t": 0.5, "text": "1481"}, {"t": 6.5, "text": "1482"}, {"t": 16.5, "text": "1489"},
                  {"t": 19.3, "text": "1495"}],
        "note": "Güzergâh temsilidir",
        "camera": [{"t": 0, "center": [33.0, 35.5], "zoom": 1.6}, {"t": 9.0, "center": [20.5, 37.0], "zoom": 1.0}]},
}
GECIS = {"kes": "cut", "erit": "dissolve", "karart": "black"}


def tr_title(text: str) -> str:
    def word(w):
        low = w.replace("I", "ı").replace("İ", "i").lower()
        first = {"i": "İ", "ı": "I"}.get(low[0], low[0].upper())
        return first + low[1:] if low not in ("ve",) else low
    return " ".join(word(w) for w in text.split())


def ekran_shots(line: str, counter: list) -> list[dict]:
    """[EKRAN: g01 (…) /erit/ g02 (…)] → görsel/harita çekimleri. Açıklamalar (parantez) atlanır."""
    line = re.sub(r"\([^)]*\)", "", line)
    shots = []
    for tok in re.finditer(r"\b(g\d\d)\b|\b(m_\w+)\b", line):
        if tok.group(2):
            shots.append({"map": tok.group(2), "transition": "dissolve", "xfade": XFADE})
            continue
        move = HAREKET[counter[0] % len(HAREKET)]
        counter[0] += 1
        shots.append({"image": tok.group(1), "move": move, "transition": "dissolve", "xfade": XFADE})
    return shots


def parse(md: str) -> list[dict]:
    body = md.split("# DOĞRULA")[0]
    chapters, ch, ekran, counter = [], None, [], [0]
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
            ekran += ekran_shots(line, counter)
            continue
        if not line or line.startswith(("#", "*", ">", "---", "|", "-")):
            continue
        if not ekran:
            raise ValueError(f"Paragrafın görseli yok: {line[:60]}")
        ch["paragraphs"].append({"text": line, "shots": ekran})
        ekran = []
    for i, c in enumerate(chapters):
        c["music"] = MUZIK[i % len(MUZIK)]
        if c.get("card") and 1 <= i <= len(KART):
            c["card"]["image"] = KART[i - 1]
    return chapters


def main():
    md = (ROOT / "senaryo.md").read_text(encoding="utf-8")
    yavuz = json.loads((ROOT.parent / "04-yavuz" / "senaryo.json").read_text(encoding="utf-8"))
    data = {
        "slug": "05-uyku-cem-sultan",
        "title": "Kardeşine Yenilen Şehzade: Cem Sultan'ın 13 Yıllık Sürgünü | Uyku Belgeseli",
        "description": (
            "Işıkları kısın, rahatça uzanın. Bu gece Fatih Sultan Mehmed'in küçük oğlu Cem Sultan'ın hikâyesini "
            "dinliyoruz: Konya'daki şair şehzade, Bursa'daki on sekiz günlük saltanat, Kahire ve hac yolculuğu, "
            "Rodos şövalyeleri, Fransa'nın taş kuleleri, Roma ve Napoli'de geçen on üç yıllık sürgün.\n\n"
            "Uykuya dalmanız için yavaş ve sakin bir anlatımla hazırlandı. Tartışmalı bilgiler anlatımda "
            "\"rivayete göre\" ya da \"kaynaklara göre\" diye belirtilmiştir.\n\n"
            "Tarih Dosyaları belgeselleri: Yavuz Sultan Selim → https://youtu.be/J0DGI9Kqlqc · "
            "İstanbul'un Fethi → https://youtu.be/AI-RfRzQfos"),
        "tags": ["cem sultan", "uyku belgeseli", "uyku için tarih", "tarih uyku", "osmanlı tarihi",
                 "fatih sultan mehmed", "ii. bayezid", "cem sultan sürgün", "osmanlı şehzadeleri",
                 "uyku için belgesel", "sesli tarih", "türkçe belgesel", "belgesel"],
        "hashtags": ["#CemSultan", "#UykuBelgeseli", "#OsmanlıTarihi", "#Tarih"],
        "ai_disclosure": ("Bu belgeseldeki çizimler yapay zekâ ile üretilmiştir ve temsilidir."),
        "sources": [
            "TDV İslâm Ansiklopedisi: Cem Sultan, Bayezid II, Kayıtbay",
            "Halil İnalcık, Osmanlı İmparatorluğu Klasik Çağ (1300–1600)",
            "Halil İnalcık, \"A Case Study in Renaissance Diplomacy: The Agreement between Innocent VIII "
            "and Bayezid II on Djem Sultan\"",
            "Nicolas Vatin, Sultan Djem: Un prince ottoman dans l'Europe du XVe siècle",
            "Vâkıât-ı Sultan Cem",
        ],
        "tts_model": yavuz.get("tts_model", "eleven_v4"),
        # Uyku: daha yavaş ve daha sabit anlatım
        "voice_settings": {"stability": 0.65, "similarity_boost": 0.8, "style": 0.05,
                           "use_speaker_boost": True, "speed": 0.9},
        "pronunciations": {"d'Aubusson": "Dobüson", "Bourganeuf": "Burganöf", "Bourganeuf'te": "Burganöf'te",
                           "Sassenage": "Sasnaj", "Innocentius": "İnnosentius", "Nice'e": "Nis'e",
                           "Charles": "Şarl", "Philippine-Hélène": "Filipin-Elen",
                           "Saint-Jean": "Sen-Jan"},
        "ilk_yorum": ("Cem Sultan sizce Kudüs teklifini kabul etmeli miydi? Yorumlarda konuşalım.\n\n"
                      "🌙 Uyku belgeselleri oynatma listemizde başka hikâyeler de var. İyi geceler."),
        "kurgu": {"gecis": "dissolve", "ton_esitle": 0.0, "bolum_sonu": 4.0, "bolum_karartma": 2.5},
        "music_sources": yavuz["music_sources"],
        "images": {"dunya": {"commons": "File:Whole world - land and oceans 12000.jpg", "original": True},
                   **{k: {"file": f"gorseller/{k}.png", "credit": AI_CREDIT} for k in GORSELLER}},
        "thumbnails": [
            {"sablon": "v2", "arka_plan": "kapak1", "arka_plan_kadraj": "50% 40%", "hale": "transparent",
             "line1": "13 yıl", "line2": "sürgün", "vurgu": "#FFC83D", "etiket": "Uyku Belgeseli"},
            {"sablon": "v2", "arka_plan": "kapak2", "arka_plan_kadraj": "50% 40%", "hale": "transparent",
             "line1": "Tahtı", "line2": "kaybetti", "vurgu": "#FFC83D", "etiket": "Uyku Belgeseli"}],
        "stock": {},
        "films": {},
        "maps": MAPS,
        "chapters": parse(md),
    }
    (ROOT / "senaryo.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(c["paragraphs"]) for c in data["chapters"])
    chars = sum(len(re.sub(r"\[[^\]]*\]", "", p["text"])) for c in data["chapters"] for p in c["paragraphs"])
    imgs = {s["image"] for c in data["chapters"] for p in c["paragraphs"] for s in p["shots"] if "image" in s}
    print(f"{len(data['chapters'])} bölüm, {n} paragraf, {chars} karakter, {len(imgs)} farklı görsel")


if __name__ == "__main__":
    main()
