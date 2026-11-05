F = {
 "fatih_bellini": "Bellini, Gentile - Portrait of Mehmed II - National Gallery, London.jpg",
 "fatih_madalya": "Costanzo da ferrara, medaglia con mehmed II, sultano ottomano, conquistatore di costantinopoli, 1478.jpg",
 "surlar_genis": "Theodosian Walls of Constantinople, Istanbul (1991).jpg",
 "surlar_kule": "Istanbul Yedikule Theodosian Walls southern end in 2006 3426b.jpg",
 "surlar_guney": "Istanbul Yedikule Theodosian Walls southern end in 2012 6416.jpg",
 "altin_kapi": "Golden Gate of Constantinole.jpg",
 "mermer_kule": "Istanbul Marble Tower 3144.jpg",
 "yedikule": "Istanbul Marble Tower end of walls leading to it 0499.jpg",
 "rumeli_hisari": "Rumelihisarı (8393629929).jpg",
 "rumeli_hisari_2": "Rumeli Hisarı Müzesi.jpg",
 "rumeli_hisari_kule": "Small Zaganos Pasha Tower Rumeli Hisarı in 2016 3014.jpg",
 "anadolu_hisari": "Anadoluhisarı.JPG",
 "bogaz_gravur": "Count amadeo preziosi view over the bosphorus showing the fortress of d6462373095712).jpg",
 "sahi_topu": "Dardanelles Gun 2023.JPG",
 "sahi_topu_2": "Dardanelles Gun Turkish Bronze.jpg",
 "ayasofya": "Hagia Sophia Mars 2013.jpg",
 "ayasofya_2": "Hagia Sophia Istanbul July 2022-2.jpg",
 "ayasofya_ic": "Hagia Sophia Interior Panorama.jpg",
 "zonaro_fetih": "Conquest of Constantinople, Zonaro.jpg",
 "buondelmonti": "Map of Constantinople, Buondelmonti.jpg",
 "kusatma_minyatur": "Le siège de Constantinople (1453) by Jean Le Tavernier after 1455.jpg",
 "kusatma_gravur": "Siege de Constantinople par Mohammed II - depuis le 6 Avril jusqu'au 29 Mai 1453 (27 Rebioul). Grave par Ch. Schreiber. (IA dr siege-de-constantinople-par-mohammed-ii-depuis-le-6-avril-jusquau-29-mai-13229041).jpg",
 "kusatma_maket": "Siege of Constantinople Model, Istanbul Military Museum.jpg",
 "gennadios": "Gennadios II and Mehmed II.jpg",
 "topkapi": "İstanbul - Topkapı Sarayı 1291.jpg",
 "fatih_camii": "Fatih Camii - Aerial view.jpg",
 "eyup_sultan": "Eyüp Sultan Mosque.jpg",
 "eyup_kubbe": "Dome of the Eyüp Sultan Mosque (2022).jpg",
 "kapalicarsi": "Grand Bazaar (Istanbul).jpg",
 "edirne_cami": "Eski Cami, Edirne 41.JPG",
 "edirne_panorama": "20120604 Edirne view from the top of the Minaret of Selimiye Mosque Edirne Turkey Panoramic.jpg",
 "halic": "Golden Horn and european side of Istanbul 001.jpg",
 "halic_2": "Golden horn view.jpg",
 "istanbul_siluet": "Istanbul siluet.jpg",
 "osmanli_minyatur": "Frontispiece (folio 1v-2r). Ottoman court scene. Khusrau and Shirin, 1498–99 CE (MET 69.27).jpg",
 "konstantinopolis_mural": "Constantinople mural, Istanbul Archaeological Museums.jpg",
}
IMAGES = {k: {"commons": "File:" + v} for k, v in F.items()}
# Kısa kenarı küçük ama eşsiz eserler
IMAGES["zonaro_fetih"]["min_width"] = 1600
IMAGES["kusatma_minyatur"]["min_width"] = 1700
# Kapak arka planları (Gemini klibinden kare; "temsili")
IMAGES["kapak_gemiler"] = {"file": "kapak/gemiler.jpg", "credit": {"title": "Temsili canlandırma", "artist": "Gemini ile üretildi", "license": "—"}}
IMAGES["kapak_sancak"] = {"file": "kapak/sancak.jpg", "credit": {"title": "Temsili canlandırma", "artist": "Gemini ile üretildi", "license": "—"}}
