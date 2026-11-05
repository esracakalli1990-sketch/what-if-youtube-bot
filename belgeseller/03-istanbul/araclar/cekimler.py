"""Paragraf → çekim listesi. i=görsel, m=harita/grafik/kart, c=Gemini klibi, s=Pexels."""
def i(k, move="in", **kw): return {"image": k, "move": move, **kw}
def m(k): return {"map": k}
def s(k, start=0.0, **kw): return {"stock": k, "start": start, **kw}
def c(n, sfx=True): return {"clip": f"klipler/klip{n}.mp4", "move": "still", "sfx": sfx}
def L(t, st): return {"title": t, "subtitle": st}

SHOTS = {
 # GİRİŞ — soğuk açılış
 "0.0": [dict(c(1), label=L("22 NİSAN 1453", "GALATA SIRTLARI · TEMSİLİ CANLANDIRMA")), i("halic", "left", overlay="katman_sis")],
 "0.1": [i("surlar_genis", "up"), c(2)],
 "0.2": [i("fatih_bellini", "in"), i("surlar_kule", "left"), c(4)],
 "0.3": [i("rumeli_hisari", "right"), i("sahi_topu", "in"), m("sehir_plani"), c(8)],
 # I. KIZIL ELMA
 "1.0": [i("buondelmonti", "in", label=L("KONSTANTİNOPOLİS", "BUONDELMONTİ HARİTASI · 1422")), i("ayasofya", "left"), i("halic_2", "right")],
 "1.1": [m("eski_kusatmalar"), i("surlar_guney", "in")],
 "1.2": [i("eyup_sultan", "in", label=L("EYÜP SULTAN", "İSTANBUL")), i("eyup_kubbe", "up")],
 "1.3": [m("bizans_kuculme"), i("konstantinopolis_mural", "in")],
 "1.4": [i("buondelmonti", "out"), i("ayasofya_2", "in"), s("yildizli_gece")],
 "1.5": [i("altin_kapi", "in"), i("surlar_kule", "out")],
 # II. GENÇ SULTAN
 "2.0": [m("k_fatih"), i("fatih_madalya", "in")],
 "2.1": [i("edirne_cami", "in"), i("osmanli_minyatur", "left")],
 "2.2": [m("varna_1444"), m("g_yol")],
 "2.3": [i("osmanli_minyatur", "right"), s("mum_isigi")],
 "2.4": [i("edirne_panorama", "left", label=L("EDİRNE", "OSMANLI BAŞKENTİ · 1451")), i("fatih_bellini", "in")],
 "2.5": [m("k_candarli"), m("k_zaganos")],
 "2.6": [i("buondelmonti", "in")],
 # III. BOĞAZKESEN
 "3.0": [m("bogazkesen"), i("anadolu_hisari", "left")],
 "3.1": [i("rumeli_hisari", "in", label=L("RUMELİ HİSARI", "BOĞAZKESEN · 1452")), m("g_hisar")],
 "3.2": [i("rumeli_hisari_kule", "up"), c(3)],
 "3.3": [i("bogaz_gravur", "left"), s("mum_isigi")],
 "3.4": [m("donanma_gelibolu"), s("deniz_safak")],
 "3.5": [i("kusatma_gravur", "in"), i("buondelmonti", "right")],
 # IV. SURLARI YIKACAK TOP
 "4.0": [s("ates_gece"), m("k_urban")],
 "4.1": [i("sahi_topu_2", "in", overlay="katman_kivilcim"), s("ates_gece", start=5.0)],
 "4.2": [m("g_top"), i("sahi_topu", "left")],
 "4.3": [m("topun_yolu"), i("edirne_panorama", "right")],
 "4.4": [i("sahi_topu", "in", label=L("OSMANLI TOPU · 1464", "BUGÜN İNGİLTERE'DE SERGİLENİYOR")), i("sahi_topu_2", "right")],
 "4.5": [m("top_mevzileri"), i("kusatma_maket", "in")],
 # V. BİN YILLIK SURLAR
 "5.0": [i("surlar_genis", "left", label=L("THEODOSİUS SURLARI", "İSTANBUL")), i("mermer_kule", "up")],
 "5.1": [m("g_sur_kesiti"), i("surlar_guney", "in")],
 "5.2": [m("sehir_plani")],
 "5.3": [m("k_konstantin"), m("k_giustiniani")],
 "5.4": [i("ayasofya_ic", "in", overlay="katman_toz"), i("konstantinopolis_mural", "left")],
 "5.5": [i("yedikule", "out")],
 "5.6": [m("kusatma_dizilis"), m("g_iki_taraf")],
 # VI. KUŞATMA BAŞLIYOR
 "6.0": [c(4), i("surlar_kule", "in", overlay="katman_kivilcim")],
 "6.1": [i("kusatma_minyatur", "in"), i("surlar_genis", "right")],
 "6.2": [c(8), s("ates_gece")],
 "6.3": [m("sehir_plani"), i("halic", "left")],
 "6.4": [m("deniz_savasi"), i("kusatma_gravur", "in")],
 "6.5": [c(5), i("fatih_bellini", "in")],
 "6.6": [i("fatih_madalya", "in")],
 # VII. GEMİLER KARADAN YÜRÜYOR
 "7.0": [m("gemiler_karadan"), i("halic_2", "left")],
 "7.1": [c(6), i("galata", "up")],
 "7.2": [m("gemiler_karadan"), m("g_gemiler")],
 "7.3": [c(1), c(2)],
 "7.4": [i("zonaro_fetih", "in"), i("halic", "right")],
 "7.5": [m("venedik_baskini"), s("ates_gece")],
 "7.6": [m("yuzer_kopru"), i("kusatma_maket", "left")],
 # VIII. TOPRAK ALTINDA SAVAŞ
 "8.0": [m("g_tunel"), s("mum_isigi")],
 "8.1": [i("surlar_guney", "in"), s("ates_gece", start=10.0)],
 "8.2": [c(7), i("kusatma_minyatur", "out")],
 "8.3": [i("ayasofya", "in", overlay="katman_sis"), s("yildizli_gece")],
 "8.4": [c(11), i("surlar_genis", "left")],
 "8.5": [i("osmanli_minyatur", "in"), m("k_aksemseddin")],
 "8.6": [s("ates_gece"), i("fatih_bellini", "out")],
 # IX. SON HÜCUM
 "9.0": [m("son_hucum"), c(12)],
 "9.1": [c(12), i("kusatma_maket", "in")],
 "9.2": [c(8), m("k_giustiniani")],
 "9.3": [m("kerkoporta"), i("surlar_kule", "left")],
 "9.4": [c(9), m("k_ulubatli")],
 "9.5": [i("surlar_genis", "right", overlay="katman_sis"), i("mermer_kule", "in")],
 "9.6": [c(9)],
 # X. FETİH
 "10.0": [c(10), i("zonaro_fetih", "in", label=L("FATİH'İN İSTANBUL'A GİRİŞİ", "FAUSTO ZONARO"))],
 "10.1": [i("ayasofya_ic", "up"), i("ayasofya_2", "in")],
 "10.2": [i("gennadios", "in", label=L("FATİH VE PATRİK GENNADİOS", "MOZAİK")), i("galata", "left")],
 "10.3": [m("osmanli_yukselis")],
 "10.4": [i("topkapi", "in", label=L("TOPKAPI SARAYI", "İSTANBUL")), i("fatih_camii", "left"), i("kapalicarsi", "in")],
 "10.5": [i("eyup_sultan", "in"), i("eyup_kubbe", "up")],
 "10.6": [i("fatih_bellini", "in")],
 # KAPANIŞ
 "11.0": [i("istanbul_siluet", "left"), i("rumeli_hisari_2", "right"), i("ayasofya", "out")],
}
