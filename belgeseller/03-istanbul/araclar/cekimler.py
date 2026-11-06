"""
Paragraf → çekim listesi (v2, 6 Kasım). Ayrıntı: ../cekim_senaryosu.md

i=arşiv görseli, m=harita/grafik/kart, c=Gemini klibi (klipler/), v=gerçek mekân videosu (Pexels).
Kurallar: önceki videolardan görüntü yok; bir Pexels videosu ≤2, bir görsel ≤2, bir klip 1 kez;
1453 anlatılırken modern görüntü yok ("BUGÜN" etiketli anlar hariç).
"""


def i(k, move="in", **kw): return {"image": k, "move": move, **kw}
def m(k): return {"map": k}
def c(name, sfx=True, **kw): return {"clip": f"klipler/{name}.mp4", "move": "still", "sfx": sfx, **kw}
def v(pid, start=0.0, **kw): return {"stock": f"p{pid}", "start": start, **kw}
def L(t, st): return {"title": t, "subtitle": st}


# Pexels kimliği → (süre sn, arama, çeken). İnceleme: inceleme/03-istanbul-mekan dalı, 5 Kasım.
PEXELS = {
 19671347: (17, "Golden Horn aerial", "Dogukan Bilgin"),
 32304331: (9, "Istanbul city walls aerial", "Kenan Turguç"),
 31639721: (16, "Rumeli Hisari aerial", "Metin Özdemir"),
 34432985: (24, "Istanbul historic peninsula drone", "K"),
 37789039: (10, "Sarayburnu Istanbul sea", "Sururi Ballıdağ"),
 32220990: (5, "Anadolu Hisari", "Kenan Turguç"),
 29217883: (8, "Eyup Sultan mosque", "Sururi Ballıdağ"),
 35615255: (10, "Bosphorus sunrise", "Sururi Ballıdağ"),
 34490200: (5, "Theodosian walls Istanbul", "Salih Sezgen"),
 31774009: (8, "Edirne Turkey", "Kenan Turguç"),
 37191274: (27, "ship Bosphorus strait", "Sururi Ballıdağ"),
 33294992: (13, "Rumeli fortress Bosphorus", "Zeki Binici"),
 33294993: (14, "Rumeli Hisari aerial", "Zeki Binici"),
 35977724: (12, "Bosphorus fog", "Sururi Ballıdağ"),
 39394631: (15, "empty sea horizon calm", "Kadir Oguzhan"),
 32304330: (17, "Istanbul city walls aerial", "Kenan Turguç"),
 32304332: (8, "Istanbul city walls aerial", "Kenan Turguç"),
 32304336: (9, "Yedikule fortress", "Kenan Turguç"),
 32304338: (8, "Yedikule fortress", "Kenan Turguç"),
 19057675: (11, "Golden Horn Istanbul", "Ahmed"),
 10716775: (10, "Hagia Sophia interior", "Ibrahim Bennett"),
 38530731: (10, "Hagia Sophia interior", "umut izgi"),
 38530728: (6, "Hagia Sophia interior", "umut izgi"),
 30734481: (10, "empty sea horizon calm", "Eren Ataselim"),
 31822117: (8, "Galata hill aerial Istanbul", "Okan Demiray"),
 14441647: (36, "Golden Horn aerial", "Sururi Ballıdağ"),
 34432939: (16, "Galata hill aerial Istanbul", "K"),
 11229446: (32, "lunar eclipse blood moon", "Tom Fisk"),
 12030510: (60, "Hagia Sophia night", "Yasir Gürbüz"),
 39618754: (14, "Ottoman mehter band", "Yasin Onuş"),
 19163087: (14, "Hagia Sophia aerial drone", "Volkan Yılmaz"),
 18293182: (13, "Galata tower", "Ibrahim Bennett"),
 34432986: (14, "Topkapi palace", "K"),
 19312245: (10, "Topkapi palace", "Volkan Yılmaz"),
 36403074: (14, "Grand Bazaar Istanbul", "Sururi Ballıdağ"),
 29218872: (7, "Eyup Sultan mosque", "Sururi Ballıdağ"),
 35314400: (18, "Istanbul skyline sunset", "Sururi Ballıdağ"),
 34432926: (37, "Istanbul skyline night", "K"),
}
STOCK = {f"p{k}": {"q": q, "id": k} for k, (_, q, _) in PEXELS.items()}

BUGUN = "BUGÜN"
TEMSILI = "TEMSİLİ CANLANDIRMA"

SHOTS = {
 # GİRİŞ — soğuk açılış
 "0.0": [c("klip1", label=L("22 NİSAN 1453", "GALATA SIRTLARI · " + TEMSILI)), c("y10")],
 "0.1": [c("klip2"), v(19671347)],
 "0.2": [i("fatih_bellini", "in"), v(32304331), v(32304330)],
 "0.3": [v(31639721), i("sahi_topu", "in"), v(14441647)],
 # I. KIZIL ELMA
 "1.0": [v(34432985), v(37789039), i("buondelmonti", "in", label=L("KONSTANTİNOPOLİS", "BUONDELMONTİ HARİTASI · 1422"))],
 "1.1": [m("eski_kusatmalar"), i("anadolu_hisari", "left", label=L("ANADOLU HİSARI", "1394 · " + BUGUN))],
 "1.2": [v(29217883, label=L("EYÜP SULTAN", "İSTANBUL · " + BUGUN)), i("eyup_kubbe", "up"), i("eyup_sultan", "in")],
 "1.3": [m("bizans_kuculme"), c("y2"), i("buondelmonti", "right")],
 "1.4": [v(35615255), i("ayasofya", "in"), v(37191274)],
 "1.5": [v(34490200), i("surlar_genis", "left")],
 # II. GENÇ SULTAN
 "2.0": [m("k_fatih"), c("y3k", sfx=False), i("edirne_cami", "left")],
 "2.1": [i("osmanli_minyatur", "left"), i("fatih_madalya", "in")],
 "2.2": [m("varna_1444"), c("t4", label=L("VARNA SAVAŞI · 1444", "MATEJKO TABLOSUNDAN " + TEMSILI)), m("g_yol")],
 "2.3": [m("g_yol")],
 "2.4": [v(31774009, label=L("EDİRNE", "OSMANLI BAŞKENTİ · " + BUGUN)), i("edirne_cami", "in")],
 "2.5": [c("y4"), m("sehir_plani"), m("k_fatih")],
 "2.6": [v(37191274, start=12.0)],
 # III. BOĞAZKESEN
 "3.0": [m("bogazkesen"), v(33294992)],
 "3.1": [c("y5"), v(33294993, label=L("RUMELİ HİSARI", "BOĞAZKESEN · 1452")), m("g_hisar")],
 "3.2": [c("klip3"), i("rumeli_hisari_kule", "up")],
 "3.3": [m("k_konstantin"), v(35977724)],
 "3.4": [m("donanma_gelibolu"), v(39394631)],
 "3.5": [i("kusatma_gravur", "right"), m("kusatma_dizilis")],
 # IV. SURLARI YIKACAK TOP
 "4.0": [c("y6", label=L("URBAN", "TOP DÖKÜMCÜSÜ · " + TEMSILI)), v(32304332), i("altin_kapi", "in")],
 "4.1": [c("y1"), i("fatih_madalya", "out")],
 "4.2": [m("g_top"), c("klip4")],
 "4.3": [m("topun_yolu"), c("y7")],
 "4.4": [i("sahi_topu", "left", label=L("OSMANLI TOPU · 1464", "BUGÜN İNGİLTERE'DE SERGİLENİYOR")), i("sahi_topu_2", "in")],
 "4.5": [m("top_mevzileri"), i("kusatma_maket", "in")],
 # V. BİN YILLIK SURLAR
 "5.0": [v(32304330, start=8.0, label=L("THEODOSİUS SURLARI", "İSTANBUL · " + BUGUN)), v(32304336)],
 "5.1": [m("g_sur_kesiti"), i("surlar_guney", "in")],
 "5.2": [m("sehir_plani"), v(19057675)],
 "5.3": [c("y8", label=L("GİOVANNİ GİUSTİNİANİ", "CENEVİZLİ KOMUTAN · " + TEMSILI)), m("g_iki_taraf"), i("mermer_kule", "up")],
 "5.4": [v(10716775), i("ayasofya_ic", "in"), v(38530731), i("ayasofya_2", "left")],
 "5.5": [v(30734481)],
 "5.6": [m("kusatma_dizilis"), i("kusatma_maket", "left")],
 # VI. KUŞATMA BAŞLIYOR
 "6.0": [c("y9")],
 "6.1": [i("kusatma_minyatur", "in", label=L("KUŞATMA · 1453", "JEAN LE TAVERNIER MİNYATÜRÜ")), i("surlar_kule", "in")],
 "6.2": [c("klip8"), i("kusatma_gravur", "in"), i("altin_kapi", "right")],
 "6.3": [m("deniz_savasi"), v(19671347, start=8.0), i("halic", "left")],
 "6.4": [c("y11k"), v(39394631, start=7.0), i("bogaz_gravur", "left")],
 "6.5": [c("klip5"), i("surlar_kule", "left")],
 "6.6": [v(31822117, label=L("GALATA SIRTLARI", BUGUN))],
 # VII. GEMİLER KARADAN YÜRÜYOR
 "7.0": [m("gemiler_karadan"), v(14441647, start=18.0)],
 "7.1": [c("klip6"), v(34432939, label=L("GEMİLERİN YOLU", "BUGÜN BEYOĞLU · KASIMPAŞA"))],
 "7.2": [c("t1", label=L("GEMİLER KARADAN YÜRÜYOR", "ZONARO TABLOSUNDAN " + TEMSILI)), m("g_gemiler")],
 "7.3": [c("y12"), i("halic_2", "left")],
 "7.4": [v(34432939, start=8.0), i("fatih_bellini", "out")],
 "7.5": [m("venedik_baskini"), c("y13")],
 "7.6": [m("yuzer_kopru"), c("y14")],
 # VIII. TOPRAK ALTINDA SAVAŞ
 "8.0": [m("g_tunel"), c("y15")],
 "8.1": [c("y16"), m("g_tunel"), i("surlar_guney", "right")],
 "8.2": [c("klip7"), c("t5", label=L("KUŞATMA PLANI", "SCHREIBER GRAVÜRÜNDEN " + TEMSILI))],
 "8.3": [v(11229446), v(12030510)],
 "8.4": [c("klip11"), i("konstantin_minyatur", "in", label=L("XI. KONSTANTİN", "15. YÜZYIL MİNYATÜRÜ"))],
 "8.5": [c("y17k", label=L("SON SAVAŞ DİVANI", TEMSILI)), i("osmanli_minyatur", "right"), i("konstantinopolis_mural", "in"), i("rumeli_hisari_kule", "up", label=L("ZAĞANOS PAŞA KULESİ", "RUMELİ HİSARI"))],
 "8.6": [c("y18"), i("ayasofya", "out"), v(12030510, start=30.0)],
 # IX. SON HÜCUM
 "9.0": [m("son_hucum"), v(39618754)],
 "9.1": [c("klip12"), c("y19k"), m("son_hucum"), v(39618754, start=7.0)],
 "9.2": [c("y20k", label=L("GİUSTİNİANİ YARALANDI", TEMSILI)), i("surlar_genis", "right")],
 "9.3": [m("kerkoporta"), v(32304338), i("yedikule", "in")],
 "9.4": [c("klip9", label=L("ULUBATLI HASAN", TEMSILI)), i("kapak_sancak", "in")],
 "9.5": [c("y21"), i("konstantinopolis_mural", "left"), i("mermer_kule", "in")],
 "9.6": [i("kapak_sancak", "out", label=L("29 MAYIS 1453", "İSTANBUL")), v(35615255, start=5.0)],
 # X. FETİH
 "10.0": [c("klip10"), c("t2", label=L("FATİH İSTANBUL'DA", "ZONARO TABLOSUNDAN " + TEMSILI))],
 "10.1": [v(19163087), v(38530728), i("ayasofya_ic", "up")],
 "10.2": [i("gennadios", "in", label=L("FATİH VE PATRİK GENNADİOS", "MOZAİK")), v(18293182, label=L("GALATA KULESİ", "CENEVİZ YAPISI · 1348"))],
 "10.3": [m("osmanli_yukselis"), v(34432986)],
 "10.4": [v(19312245, label=L("TOPKAPI SARAYI", "İSTANBUL")), i("fatih_camii", "in", label=L("FATİH CAMİİ", "İSTANBUL")), v(36403074)],
 "10.5": [v(29218872), i("eyup_sultan", "up"), i("eyup_kubbe", "in")],
 "10.6": [v(35314400), i("istanbul_siluet", "left")],
 # KAPANIŞ
 "11.0": [v(31639721, start=8.0), v(32304331, start=4.0), v(19163087, start=7.0), v(34432926), i("rumeli_hisari_2", "in")],
}
