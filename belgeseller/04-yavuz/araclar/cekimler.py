"""Yavuz Sultan Selim — kesin çekim listesi (gerçek ses süreleriyle kuruldu, 12 Kasım).

Anahtar "bölüm.paragraf". Her çekim: klip (y/z/w), harita (m_/k_) ya da stok (s_).
Kurallar:
  - Çekim başına 5–9 sn (kesmeler cümle başına oturur, paragraf eşit bölünür).
  - Klip yalnızca BİR kez; tek istisna soğuk açılış montajı (farklı giriş noktasıyla, savaş
    sahnelerinin ön gösterimi).
  - Varsayılan geçiş düz kesme (senaryo "kurgu.gecis"); zaman/mekân atlamasında "erit",
    bölüm içi büyük atlamada "karart", top atışından sonra "parla".
  - Haritaların süresi yuvaya göre uzatılır (haritalar.py → esnet).
Ekran yönü (flip) klipler geldikten sonra geçiş şeridiyle tek tek belirlenir.
"""

T = {"kes": "cut", "erit": "dissolve", "karart": "black", "parla": "flash"}


def c(name, tr=None, **kw):
    s = {"clip": f"klipler/{name}.mp4"}
    if tr:
        s["transition"] = T[tr]
    s.update(kw)
    return s


def m(name, tr=None):
    s = {"map": name}
    if tr:
        s["transition"] = T[tr]
    return s


def st(name, tr=None, **kw):
    s = {"stock": name, **kw}
    if tr:
        s["transition"] = T[tr]
    return s


SHOTS = {
    # ── Soğuk açılış ──
    "0.0": [c("y01"), c("y02"), c("y04", start=6.0)],
    "0.1": [c("y07", start=0.0), c("y06", flip=True)],
    "0.2": [c("y05"), c("w01")],
    # ön gösterim montajı: sonraki sahnelerin farklı anları (giriş noktası kaydırılır)
    "0.3": [c("y08", start=0.0, flip=True), c("y20", "parla", start=8.0), c("y28", start=9.0), c("y32", start=6.0)],
    # ── I · Trabzon'daki Şehzade ──
    "1.0": [c("z01"), c("z02"), c("w02")],
    "1.1": [m("m_osmanli_1500", "erit")],
    "1.2": [c("z27", "erit"), c("w03")],
    "1.3": [c("z03", "erit"), c("z04")],
    "1.4": [c("z05", "erit")],
    # ── II · Doğudan Gelen Fırtına ──
    "2.0": [c("w04"), c("w05")],
    "2.1": [m("m_safevi", "erit")],
    "2.2": [c("w06", "erit"), c("z06"), c("z07")],
    "2.3": [c("z08", "karart"), c("w07")],
    # ── III · Taht Kavgası ──
    "3.0": [c("w08"), m("k_sehzadeler"), c("w09")],
    "3.1": [m("m_selim_yolu", "erit")],
    "3.2": [c("z09", "erit"), c("z10")],
    "3.3": [c("z11", "erit"), c("w10"), c("w11", "erit")],
    "3.4": [c("z12", "erit"), c("w12")],
    # ── IV · Çaldıran ──
    "4.0": [m("m_caldiran_seferi")],
    "4.1": [c("z13", "erit"), c("w13")],
    "4.2": [c("y36", "erit"), c("w14")],
    "4.3": [c("w15", "erit"), c("z28"), c("w16")],
    "4.4": [c("y03", "erit"), c("y04", start=0.0)],
    "4.5": [c("y07", start=4.0), c("w17"), c("y08", start=5.0, flip=True), c("y09", "parla", flip=True), c("y10", start=1.5, flip=True)],
    "4.6": [c("y11", "erit"), c("y12", "erit")],
    "4.7": [c("y13", "karart"), c("w18")],
    "4.8": [m("m_1515", "erit")],
    # ── V · Mercidabık ──
    "5.0": [m("m_memluk")],
    "5.1": [c("y15", "erit"), c("y14")],
    "5.2": [c("z14", "erit"), c("y35")],
    "5.3": [c("y16"), c("y17"), c("w19", "parla")],
    "5.4": [c("y18"), c("y19", start=4.5)],
    "5.5": [c("z15", "karart"), c("z16", "erit")],
    # ── VI · Çöl ──
    "6.0": [c("y20")],
    "6.1": [m("m_sina", "erit")],
    "6.2": [c("y21", "erit"), c("y22"), c("y24")],
    "6.3": [c("y23", "erit"), c("w20", "erit")],
    # ── VII · Ridaniye ve Kahire ──
    "7.0": [c("y25"), c("y27")],
    "7.1": [m("m_ridaniye", "erit")],
    "7.2": [c("y26", "erit"), c("w21"), c("w22"), c("w23", "erit")],
    "7.3": [c("y28", "karart", start=1.5), c("y29")],
    "7.4": [c("z17", "erit"), c("y30", "erit")],
    # ── VIII · Emanetler ──
    "8.0": [c("y31"), c("z18", "erit")],
    "8.1": [c("w24", "erit"), c("z19")],
    "8.2": [c("z29", "erit"), c("w25")],
    "8.3": [c("y32", "erit"), c("y33", "erit")],
    "8.4": [c("z20", "erit"), c("w26", "erit"), c("w27", "erit")],
    "8.5": [m("m_sinirlar", "erit")],
    # ── IX · Son Yolculuk ──
    "9.0": [c("z21")],
    "9.1": [c("z22", "karart"), c("w28"), c("z23")],
    "9.2": [c("w29"), c("z30", "erit")],
    "9.3": [c("z24", "erit"), c("z25", "erit")],
    # ── Kapanış ──
    "10.0": [c("w30"), c("w31", "erit")],
    "10.1": [st("s_yavuz_camii", "erit", label={"title": "BUGÜN", "subtitle": "YAVUZ SELİM CAMİİ · İSTANBUL"}),
             c("w32", "erit")],
    "10.2": [c("y34", "erit", speed=0.8)],
}
