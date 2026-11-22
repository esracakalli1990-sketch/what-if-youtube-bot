"""Kösem Sultan uyku belgeseli: senaryo.md → senaryo.json.

Uyku formatı: yalnızca çizim görseller (g01…g53); yavaş çapraz geçişler,
her görselde yavaş Ken Burns hareketi; sakin müzik; yavaş ve yumuşak anlatım.

    python belgeseller/07-uyku-kosem-sultan/araclar/plan_kur.py
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT.parents[1]))

AI_CREDIT = {"title": "Temsili çizim", "artist": "Yapay zekâ ile üretildi (Gemini)", "license": "—"}
GORSELLER = [f"g{i:02d}" for i in range(1, 54)] + ["kapak1", "kapak2"]
KART = ["g05", "g11", "g14", "g19", "g21", "g26", "g31", "g35", "g43"]      # Bölüm I…IX kart görselleri
MUZIK = ["derin", "huzun", "derin", "gizem", "huzun", "derin", "huzun", "gizem", "derin", "huzun", "derin"]   # "isik" yok: telif talebi aldı
HAREKET = ["in", "left", "out", "right"]
XFADE = 2.5                      # yavaş çapraz geçiş (sn)

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
        "slug": "07-uyku-kosem-sultan",
        "title": "Altı Padişah Gören Kadın: Kösem Sultan'ın Hikâyesi | Uyku Belgeseli",
        "description": (
            "Işıkları kısın, rahatça uzanın. Bu gece Ege'deki küçük bir adadan Topkapı Sarayı'na uzanan bir ömrü, "
            "Kösem Sultan'ın hikâyesini dinliyoruz: Harem'deki ilk yıllar, Sultan Birinci Ahmed ve Mavi Cami, "
            "Eski Saray'daki bekleyiş, valide sultanlık, Bağdat'ın fethi ve kaybedilen oğullar, İbrahim'in yılları "
            "ve büyük valide olarak geçen son günler.\n\n"
            "Uykuya dalmanız için yavaş ve sakin bir anlatımla hazırlandı. Tartışmalı bilgiler anlatımda "
            "\"rivayete göre\" ya da \"kaynaklara göre\" diye belirtilmiştir.\n\n"
            "Uyku belgeselleri: Cem Sultan → https://youtu.be/1WkEFLoVnWQ · "
            "Kanuni Sultan Süleyman → https://youtu.be/6V9KWu2zO8Y"),
        "tags": ["kösem sultan", "uyku belgeseli", "uyku için tarih", "tarih uyku", "osmanlı tarihi",
                 "osmanlı harem", "valide sultan", "sultan ahmed", "iv. murad", "sultan ibrahim",
                 "uyku için belgesel", "sesli tarih", "türkçe belgesel", "belgesel"],
        "hashtags": ["#KösemSultan", "#UykuBelgeseli", "#OsmanlıTarihi", "#Tarih"],
        "ai_disclosure": ("Bu belgeseldeki çizimler yapay zekâ ile üretilmiştir ve temsilidir."),
        "sources": [
            "TDV İslâm Ansiklopedisi: Kösem Sultan, Ahmed I, Murad IV, İbrahim, Mehmed IV, Sultan Ahmed Camii",
            "Leslie P. Peirce, The Imperial Harem: Women and Sovereignty in the Ottoman Empire",
            "Halil İnalcık, Osmanlı İmparatorluğu Klasik Çağ (1300–1600)",
            "Mustafa Naîmâ, Târih-i Naîmâ",
        ],
        "tts_model": yavuz.get("tts_model", "eleven_v4"),
        # Uyku: daha yavaş ve daha sabit anlatım
        "voice_settings": {"stability": 0.65, "similarity_boost": 0.8, "style": 0.05,
                           "use_speaker_boost": True, "speed": 0.9},
        "pronunciations": {"Mahpeyker": "Mahpeyker", "Anastasia": "Anastasya", "Bahtî": "Bahti",
                           "Revan": "Revan", "Kemankeş": "Kemankeş", "Muazzama": "Muazzama"},
        "ilk_yorum": ("Sizce Kösem Sultan devleti mi ayakta tuttu, yoksa gücü bırakmak mı istemedi? Yorumlarda konuşalım.\n\n"
                      "🌙 Uyku belgeselleri oynatma listemizde başka hikâyeler de var. İyi geceler."),
        "kurgu": {"gecis": "dissolve", "ton_esitle": 0.0, "bolum_sonu": 4.0, "bolum_karartma": 2.5},
        "music_sources": {k: v for k, v in yavuz["music_sources"].items() if k != "isik"},
        "images": {**{k: {"file": f"gorseller/{k}.jpg", "credit": AI_CREDIT} for k in GORSELLER}},
        "thumbnails": [   # uyku serisi kuralı: büyük yazı her zaman "UYKU BELGESELİ" (doc_timeline.validate denetler)
            {"sablon": "v2", "arka_plan": "kapak1", "arka_plan_kadraj": "50% 40%", "hale": "transparent",
             "line1": "Uyku", "line2": "belgeseli", "vurgu": "#FFFFFF", "etiket": "Kösem Sultan"},
            {"sablon": "v2", "arka_plan": "kapak2", "arka_plan_kadraj": "50% 40%", "hale": "transparent",
             "line1": "Uyku", "line2": "belgeseli", "vurgu": "#FFFFFF", "etiket": "Kösem Sultan"}],
        "stock": {},
        "films": {},
        "maps": {},
        "chapters": parse(md),
    }
    (ROOT / "senaryo.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(c["paragraphs"]) for c in data["chapters"])
    chars = sum(len(re.sub(r"\[[^\]]*\]", "", p["text"])) for c in data["chapters"] for p in c["paragraphs"])
    imgs = {s["image"] for c in data["chapters"] for p in c["paragraphs"] for s in p["shots"] if "image" in s}
    print(f"{len(data['chapters'])} bölüm, {n} paragraf, {chars} karakter, {len(imgs)} farklı görsel")


if __name__ == "__main__":
    main()
