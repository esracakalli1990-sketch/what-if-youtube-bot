"""Sümerler — çekim listesi (gerçek ses süreleriyle, 24 Kasım). Anahtar "bölüm.paragraf".
Gerçek müze eserleri (i), Pexels mekân videoları (s), hareketli haritalar (m). Yapay zekâ klibi yok.
Hareket sırası değişken tutulur; aynı görsel tekrar kullanılırsa farklı odak (focus) verilir."""

T = {"kes": "cut", "erit": "dissolve", "karart": "black"}


def i(name, move="in", focus=None, tr=None, label=None):
    s = {"image": name, "move": move}
    if focus:
        s["focus"] = list(focus)
    if tr:
        s["transition"] = T[tr]
    if label:
        s["label"] = {"title": label[0], "subtitle": label[1]}
    return s


def s(name, start=0.0, tr=None, label=None):
    x = {"stock": name, "start": float(start)}
    if tr:
        x["transition"] = T[tr]
    if label:
        x["label"] = {"title": label[0], "subtitle": label[1]}
    return x


def m(name, tr="erit"):
    return {"map": name, "transition": T[tr]}


SHOTS = {
    # ── Giriş ──
    "0.0": [i("zig1", "in", label=("UR", "IRAK")), i("zig2", "left")],
    "0.1": [i("tab1", "in"), i("tab2", "right"), i("tab3", "out")],
    "0.2": [i("puabi1", "in", label=("PUABİ'NİN BAŞLIĞI", "PENN MÜZESİ")), i("sancak_on", "left"), i("heykelcik", "in")],
    "0.3": [i("tufan1", "in"), i("puabi2", "out"), i("lir", "right"), s("nehir_gunbatimi", 6)],
    # ── I · İki Nehrin Arası ──
    "1.0": [m("m_mezopotamya")],
    "1.1": [s("nehir_kamis", 0, "erit"), i("bataklik2", "left"), i("bataklik1", "in")],
    "1.2": [s("sulama_kanali", 4), i("uydu_irak", "in")],
    "1.3": [i("ubeyd1", "in", label=("UBEYD ÇANAĞI", "MÖ 5300–4700")), i("ubeyd2", "right"), s("harabe_gunbatimi", 0)],
    "1.4": [i("mudhif", "in", label=("MUDHİF", "KAMIŞ EV, GÜNÜMÜZ")), i("bataklik4", "left"), i("bataklik3", "out")],
    # ── II · İlk Şehir: Uruk ──
    "2.0": [m("m_sumer_sehirler"), i("uruk_1930", "in", label=("URUK (WARKA)", "1930'LAR"))],
    "2.1": [i("beyaz_tapinak", "left"), i("beyaz_cizim", "in")],
    "2.2": [i("vazo_tam", "out", (0.5, 0.75), label=("URUK VAZOSU", "IRAK MÜZESİ")), i("vazo_ust", "in"),
            i("vazo_yakin", "right"), i("vazo_ust2", "in", (0.5, 0.35))],
    "2.3": [i("maske", "in", label=("URUK'UN HANIMI", "MÖ ~3100")), i("maske_profil", "left"), i("maske", "out", (0.45, 0.4))],
    "2.4": [i("muhur1", "right"), i("muhur2", "in"), s("kil_eller", 3)],
    # ── III · Yazının Doğuşu ──
    "3.0": [i("proto3", "in", tr="erit"), i("tab4", "left"), i("tab5", "in", (0.4, 0.5))],
    "3.1": [i("proto1", "in", label=("İLK TABLETLER", "MÖ 3300–3100")), i("proto2", "right"), i("tab5", "out")],
    "3.2": [i("proto_bira", "in"), i("proto2", "left", (0.35, 0.5)), i("proto1", "out", (0.6, 0.5))],
    "3.3": [s("kil_eller", 10), i("tab1", "in", (0.4, 0.45)), i("okul3", "right")],
    "3.4": [i("okul1", "in"), i("okul2", "left"), i("tab2", "in", (0.6, 0.5)), i("okul3", "out", (0.5, 0.4))],
    "3.5": [i("okul2", "in", (0.5, 0.6)), i("okul1", "right", (0.4, 0.5)), i("okul3", "in", (0.6, 0.5))],
    # ── IV · Şehirler Savaşıyor ──
    "4.0": [m("m_sehir_devletleri")],
    "4.1": [i("kral_listesi", "in", label=("SÜMER KRAL LİSTESİ", "ASHMOLEAN MÜZESİ")), i("kral_prizma", "left"), i("kral_listesi", "out", (0.5, 0.3))],
    "4.2": [i("akbaba", "out", label=("AKBABALAR STELİ", "LOUVRE")), i("akbaba_savas", "in"),
            i("akbaba_akbaba", "right"), i("akbaba", "in", (0.3, 0.5))],
    "4.3": [i("akbaba_yazi", "in"), i("akbaba_savas", "left", (0.5, 0.6)), i("akbaba", "out", (0.7, 0.5))],
    "4.4": [i("urukagina", "in", label=("URUKAGİNA", "LOUVRE")), i("tab3", "right", (0.4, 0.5)), s("bugday_ruzgar", 0)],
    # ── V · Ur'un Kraliyet Mezarları ──
    "5.0": [i("zig4", "in", tr="erit"), i("zig3", "left"), s("harabe_gunbatimi", 8)],
    "5.1": [i("puabi1", "in", (0.5, 0.4)), i("puabi2", "out"), i("puabi4", "right"), i("geyik_kolye", "in")],
    "5.2": [i("sancak_savas", "right", label=("UR SANCAĞI", "BRITISH MUSEUM")), i("sancak_araba", "in"),
            i("sancak_baris", "left"), i("sancak_on", "in", (0.6, 0.5)), i("aslan_kutu", "out")],
    "5.3": [i("lir", "in"), i("lir_boga", "out"), i("koc", "in", label=("ÇALILIKTAKİ KOÇ", "PENN MÜZESİ"))],
    "5.4": [i("migfer", "in"), i("olum_diadem", "right"), i("olum_mucevher", "out"), s("mum_isigi", 0)],
    "5.5": [i("puabi3", "left"), i("lir_altin", "in")],
    # ── VI · Gılgamış ──
    "6.0": [i("tufan1", "in", (0.5, 0.45), tr="erit"), i("tufan2", "out"), i("uruk_1930", "right")],
    "6.1": [i("gilgamis", "in"), i("heykelcik2", "left"), i("gilgamis", "out", (0.5, 0.35))],
    "6.2": [s("col_ruzgar", 0), i("tufan2", "in"), s("nehir_gunbatimi", 20)],
    "6.3": [i("smith", "in", label=("GEORGE SMITH", "1840–1876")), i("smith2", "right"), i("tufan1", "out")],
    "6.4": [i("zig5", "left"), i("uruk_1930", "in", (0.4, 0.5)), i("gilgamis", "in", (0.5, 0.6))],
    # ── VII · İlk İmparatorluk: Akad ──
    "7.0": [i("akad_bas", "in", label=("AKADLI BİR HÜKÜMDAR", "IRAK MÜZESİ")), i("akad_bas", "out", (0.5, 0.35))],
    "7.1": [s("nehir_kamis", 3), i("tab4", "in", (0.5, 0.4)), i("akad_bas", "left", (0.5, 0.5))],
    "7.2": [m("m_akad")],
    "7.3": [i("enheduanna", "in", label=("ENHEDUANNA DİSKİ", "PENN MÜZESİ")), i("enheduanna", "right", (0.4, 0.5)),
            i("zig2", "out")],
    "7.4": [i("naram", "in", (0.5, 0.6), label=("NARAM-SİN STELİ", "LOUVRE")), i("naram2", "left"),
            i("naram", "out", (0.5, 0.3))],
    # ── VIII · Ur'un Yeniden Yükselişi ──
    "8.0": [i("gudea1", "in", tr="erit", label=("GUDEA", "LAGAŞ")), i("gudea2", "left"), i("gudea1", "out", (0.5, 0.3))],
    "8.1": [i("zig1", "right"), i("zig3", "in"), i("zig5", "out")],
    "8.2": [i("urnammu_yasa", "in", label=("UR-NAMMU YASALARI", "İSTANBUL ARKEOLOJİ MÜZELERİ")),
            i("istanbul_muze", "left"), i("urnammu_yasa", "out", (0.5, 0.4))],
    "8.3": [i("istanbul_muze2", "in"), i("ask_siiri", "right", label=("EN ESKİ AŞK ŞİİRİ", "İSTANBUL")),
            i("ask_siiri_etiket", "in")],
    "8.4": [i("ur_tablet_hesap", "in"), i("tab5", "left", (0.5, 0.4)), i("tab3", "in"), i("muhur3", "right")],
    # ── IX · Ur İçin Ağıt ──
    "9.0": [m("m_ur_dusus")],
    "9.1": [s("col_ruzgar", 20), i("zig4", "in", (0.4, 0.5)), s("harabe_gunbatimi", 4)],
    "9.2": [i("hammurabi", "in", label=("HAMMURABİ STELİ", "LOUVRE")), i("tab2", "right", (0.4, 0.4)), i("okul1", "out"), i("tab4", "in", (0.6, 0.5))],
    # ── X · Sümerlerden Kalanlar ──
    "10.0": [i("ybc", "in", label=("YBC 7289", "YALE")), i("plimpton", "left"), s("saat_yelkovan", 0)],
    "10.1": [i("sancak_araba", "in", (0.3, 0.6)), i("muhur4", "right"), i("muhur3", "in")],
    "10.2": [i("proto_bira", "in", (0.6, 0.5)), i("muhur1", "left", (0.4, 0.5)), s("bugday_ruzgar", 6)],
    "10.3": [s("nehir_gunbatimi", 30), i("bataklik4", "in"), i("zig4", "out")],
    # ── Kapanış ──
    "11.0": [i("tab1", "in", (0.5, 0.5), tr="erit"), i("tab3", "left", (0.6, 0.4)), i("zig1", "out")],
    "11.1": [s("yildizli_gece", 0), i("zig2", "in")],
    "11.2": [i("zig1", "out", (0.5, 0.45))],
}

# Bölüm kartı görselleri (bölüm sırası → görsel)
CARDS = {"1": "bataklik2", "2": "vazo_ust", "3": "proto2", "4": "akbaba", "5": "puabi1", "6": "tufan2",
         "7": "naram", "8": "gudea1", "9": "zig4", "10": "tab1"}
