"""Mısır belgeseli MapStory haritaları (gerçek boylam/enlem)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.doc_maps import fit_bounds

ALTIN, KIZIL, MOR, YESIL, MAVI, ROMA, KAHVE, BEYAZ = ("#e3b04b", "#c8553d", "#9b6fc4", "#6fae6a",
                                                    "#5b93c7", "#b8323a", "#b07a4a", "#efe6cc")
C = {  # kentler
    "Asvan": (32.90, 24.09), "Teb": (32.64, 25.70), "Abidos": (31.92, 26.18), "Nehen": (32.78, 25.10),
    "Memfis": (31.255, 29.845), "Gize": (31.134, 29.979), "Sakkara": (31.216, 29.871),
    "Dahşur": (31.209, 29.808), "Meydum": (31.157, 29.388), "Buto": (30.73, 31.20),
    "Herakleopolis": (30.94, 29.08), "Avaris": (31.82, 30.79), "Şaruhen": (34.38, 31.25),
    "Amarna": (30.90, 27.65), "Megiddo": (35.184, 32.585), "Gazze": (34.46, 31.50),
    "Kargamış": (38.00, 36.83), "Kadeş": (36.52, 34.56), "Hattuşa": (34.62, 40.02),
    "Pi-Ramses": (31.83, 30.80), "Halep": (37.16, 36.20), "Mikene": (22.76, 37.73),
    "Truva": (26.24, 39.96), "Ugarit": (35.78, 35.60), "Alaşiya": (33.90, 35.15),
    "Ninova": (43.15, 36.36), "Babil": (44.42, 32.54), "Sus": (48.26, 32.19),
    "Pelusion": (32.55, 31.04), "İskenderiye": (29.92, 31.20), "Siva": (25.52, 29.20),
    "Paraitonion": (27.23, 31.35), "Roma": (12.50, 41.90), "Atina": (23.73, 37.98),
    "Kartaca": (10.32, 36.85), "Reşit": (30.42, 31.40), "Kahire": (31.24, 30.04),
    "Ebukır": (30.06, 31.32), "Koptos": (32.81, 26.00), "Mersa Gavasis": (33.97, 26.55),
}
def city(n, t, major=False, side=None, label=None):
    d = {"at": list(C[n]), "label": label or n, "start": t}
    if major: d["major"] = True
    if side: d["side"] = side
    return d

NIL = [[32.89, 24.09], [32.93, 24.45], [32.87, 24.98], [32.55, 25.3], [32.64, 25.70], [32.72, 26.10],
       [32.25, 26.15], [31.92, 26.3], [31.6, 26.6], [31.18, 27.18], [30.85, 27.7], [30.75, 28.10],
       [30.9, 28.8], [31.1, 29.3], [31.25, 29.85], [31.22, 30.1], [31.13, 30.2], [30.9, 30.6],
       [30.6, 31.1], [30.40, 31.45]]
DIMYAT = [[31.13, 30.2], [31.3, 30.6], [31.6, 31.1], [31.83, 31.50]]
FIRAT = [[38.6, 37.5], [38.05, 36.83], [38.2, 36.0], [38.9, 35.9], [40.1, 35.3], [41.0, 34.4],
         [42.0, 34.0], [43.5, 33.2], [44.4, 32.6], [46.0, 31.2]]
ASI = [[35.9, 33.9], [36.3, 34.3], [36.52, 34.56], [36.6, 35.2], [36.4, 35.9], [36.1, 36.2], [35.9, 36.1]]
def nil(t=0.3, label=True):
    r = [{"points": NIL, "name": "Nil", "start": t, "labelAt": [30.75, 28.6]} if label else
         {"points": NIL, "start": t}, {"points": DIMYAT, "start": t}]
    return r

VADI = [[32.8, 24.1], [32.8, 24.9], [32.45, 25.6], [32.5, 26.0], [31.9, 26.1], [31.0, 27.1], [30.65, 28.0],
        [30.8, 28.8], [30.6, 29.3], [31.1, 29.9], [30.9, 30.2], [30.1, 31.3], [30.8, 31.55], [31.8, 31.55],
        [32.2, 31.2], [31.4, 30.2], [31.35, 29.85], [31.3, 29.0], [31.0, 28.1], [31.35, 27.2], [32.0, 26.4],
        [32.8, 26.2], [32.75, 25.7], [33.0, 24.9], [33.0, 24.1]]
YUKARI = [[32.8, 24.1], [32.8, 24.9], [32.45, 25.6], [32.5, 26.0], [31.9, 26.1], [31.0, 27.1], [30.65, 28.0],
          [30.8, 28.8], [30.6, 29.3], [31.0, 29.75], [31.4, 29.75], [31.3, 29.0], [31.0, 28.1], [31.35, 27.2],
          [32.0, 26.4], [32.8, 26.2], [32.75, 25.7], [33.0, 24.9], [33.0, 24.1]]
ASAGI = [[31.0, 29.75], [31.1, 29.9], [30.9, 30.2], [30.1, 31.3], [30.8, 31.55], [31.8, 31.55], [32.2, 31.2],
         [31.4, 30.2], [31.35, 29.85], [31.4, 29.75]]
KUZEY_PARCA = [[30.6, 28.6], [30.8, 28.8], [30.6, 29.3], [31.1, 29.9], [30.9, 30.2], [30.1, 31.3],
               [30.8, 31.55], [31.8, 31.55], [32.2, 31.2], [31.4, 30.2], [31.35, 29.85], [31.3, 29.0], [31.1, 28.6]]
GUNEY_PARCA = [[32.8, 24.1], [32.8, 24.9], [32.45, 25.6], [32.5, 26.0], [31.9, 26.1], [31.6, 26.5],
               [32.0, 26.6], [32.8, 26.2], [32.75, 25.7], [33.0, 24.9], [33.0, 24.1]]
HIKSOS = [[31.0, 31.5], [32.3, 31.3], [32.6, 30.8], [31.6, 30.2], [31.0, 30.4]]
MISIR_GENIS = [[25.0, 31.6], [29.9, 31.2], [32.3, 31.3], [34.2, 31.3], [34.9, 29.5], [33.6, 27.3],
               [32.8, 25.7], [33.3, 24.0], [31.0, 22.0], [25.0, 22.0]]
LEVANT = [[34.2, 31.3], [34.9, 32.8], [35.6, 34.6], [35.9, 35.8], [36.2, 36.6], [37.5, 36.9], [38.2, 36.8],
          [38.6, 36.2], [38.0, 35.0], [36.8, 33.6], [36.0, 32.0], [35.5, 31.0], [34.9, 29.5]]
HITIT = [[26.5, 38.5], [29.5, 41.0], [33.5, 41.8], [36.5, 41.3], [39.0, 40.6], [40.5, 39.0], [40.2, 37.5],
         [38.8, 36.0], [37.3, 35.2], [36.5, 35.6], [36.0, 36.2], [34.5, 36.4], [32.5, 36.3], [29.5, 36.8], [27.5, 37.5]]

IKI_MISIR = fit_bounds((30.0, 28.4), 16)
M = {}
M["nil_vadisi"] = {"taban": "dunya", "bounds": fit_bounds((31, 26), 24), "durationSec": 13,
    "title": "Nil Vadisi", "subtitle": "Çölün ortasında yeşil bir şerit",
    "regions": [{"name": "Kemet", "color": YESIL, "poly": VADI, "start": 2.0, "label": [33.9, 27.0]}],
    "rivers": nil(0.6), "cities": [city("Memfis", 4.5, True), city("Teb", 8.5), city("Asvan", 10.5)],
    "labels": [{"at": [27.0, 32.3], "text": "Akdeniz", "start": 0.4, "kind": "sea"},
               {"at": [36.6, 22.5], "text": "Kızıldeniz", "start": 0.6, "kind": "sea"},
               {"at": [25.5, 25.0], "text": "Deşret (Batı Çölü)", "start": 1.2, "kind": "land"}],
    "camera": [{"t": 0, "center": [31, 26], "zoom": 1.0}, {"t": 3.0, "center": [31, 26], "zoom": 1.0},
               {"t": 6.0, "center": [31.0, 30.0], "zoom": 2.2}, {"t": 11.5, "center": [32.4, 25.0], "zoom": 2.2}]}
M["iki_misir"] = {"taban": "dunya", "bounds": IKI_MISIR, "durationSec": 12,
    "title": "İki Taç, Tek Ülke", "subtitle": "Yukarı ve Aşağı Mısır'ın birleşmesi",
    "regions": [{"name": "Yukarı Mısır", "color": BEYAZ, "poly": YUKARI, "start": 0.6, "end": 7.0, "label": [28.6, 26.4]},
                {"name": "Aşağı Mısır", "color": KIZIL, "poly": ASAGI, "start": 1.6, "end": 7.0, "label": [27.8, 30.6]},
                {"name": "Birleşik Mısır", "color": ALTIN, "poly": VADI, "start": 7.0, "label": [34.6, 28.2]}],
    "rivers": nil(0.3), "cities": [city("Nehen", 2.6), city("Abidos", 3.0), city("Buto", 3.4, side="left"),
                                   city("Memfis", 7.6, True)],
    "years": [{"t": 6.5, "text": "MÖ 3100"}], "note": "Sınırlar yaklaşıktır"}
M["memfis_piramitleri"] = {"taban": "parsomen", "bounds": fit_bounds((31.05, 29.68), 1.6), "durationSec": 12,
    "title": "Piramitlerin Evrimi", "subtitle": "Memfis nekropolü",
    "rivers": [{"points": [[31.29, 29.30], [31.25, 29.5], [31.27, 29.7], [31.255, 29.85], [31.23, 30.05]],
                "name": "Nil", "start": 0.3, "labelAt": [31.3, 29.55]}],
    "cities": [city("Memfis", 0.8, side="right"), city("Sakkara", 2.0, True, side="left", label="Sakkara · Coser"),
               city("Meydum", 4.5, side="left"), city("Dahşur", 6.5, side="left", label="Dahşur · Eğik Piramit"),
               city("Gize", 8.5, True, side="right", label="Gize · Keops")],
    "labels": [{"at": [30.6, 29.5], "text": "Batı Çölü", "start": 0.5, "kind": "land"}],
    "years": [{"t": 2.0, "text": "MÖ 2650"}, {"t": 6.5, "text": "MÖ 2600"}, {"t": 8.5, "text": "MÖ 2560"}],
    "camera": []}
M["parcalanma"] = {"taban": "dunya", "bounds": IKI_MISIR, "durationSec": 12,
    "title": "Bölünmüş Ülke", "subtitle": "Birinci Ara Dönem ve yeniden birleşme",
    "regions": [{"name": "Kuzey krallığı", "color": MOR, "poly": KUZEY_PARCA, "start": 0.6, "end": 8.0, "label": [27.4, 27.9]},
                {"name": "Teb", "color": ALTIN, "poly": GUNEY_PARCA, "start": 1.2, "end": 8.0, "label": [34.3, 25.4]},
                {"name": "Orta Krallık", "color": ALTIN, "poly": VADI, "start": 8.0, "label": [34.6, 28.2]}],
    "rivers": nil(0.3), "cities": [city("Herakleopolis", 1.0, side="left"), city("Teb", 1.6, True)],
    "routes": [{"points": [list(C["Teb"]), [32.0, 26.4], [31.2, 27.2], [30.8, 28.2], list(C["Herakleopolis"]),
                           list(C["Memfis"])], "color": ALTIN, "start": 3.5, "duration": 4.0,
                "label": "II. Mentuhotep", "dashed": True, "army": True}],
    "years": [{"t": 0.5, "text": "MÖ 2160"}, {"t": 7.5, "text": "MÖ 2055"}], "note": "Sınırlar yaklaşıktır"}
M["hiksos_gocu"] = {"taban": "dunya", "bounds": fit_bounds((33.5, 31), 12), "durationSec": 11,
    "title": "Hiksoslar", "subtitle": "Doğudan Delta'ya",
    "regions": [{"name": "Hiksos", "color": MOR, "poly": HIKSOS, "start": 6.0, "label": [30.2, 32.2]}],
    "rivers": nil(0.3, label=False),
    "routes": [{"points": [[35.6, 33.2], [34.9, 32.2], [34.4, 31.4], [33.4, 31.1], list(C["Avaris"])], "color": MOR,
                "start": 1.0, "duration": 4.0, "dashed": True},
               {"points": [[36.5, 32.0], [35.2, 31.0], [34.0, 30.9], [32.6, 30.85], list(C["Avaris"])], "color": MOR,
                "start": 1.8, "duration": 4.0, "dashed": True}],
    "cities": [city("Memfis", 0.5), city("Şaruhen", 1.4), city("Avaris", 5.2, True)],
    "labels": [{"at": [31.5, 33.3], "text": "Akdeniz", "start": 0.4, "kind": "sea"},
               {"at": [33.9, 29.4], "text": "Sina", "start": 0.6, "kind": "land"},
               {"at": [36.4, 32.9], "text": "Kenan", "start": 0.8, "kind": "land"}],
    "years": [{"t": 0.5, "text": "MÖ 1650"}], "note": "Göç yolları temsilidir"}
M["ahmose_seferi"] = {"taban": "dunya", "bounds": IKI_MISIR, "durationSec": 12,
    "title": "Kurtuluş Savaşı", "subtitle": "Ahmose Hiksosları kovuyor",
    "regions": [{"name": "Hiksos", "color": MOR, "poly": HIKSOS, "start": 0.3, "end": 7.5, "label": [33.6, 31.3]},
                {"name": "Yeni Krallık", "color": ALTIN, "poly": VADI, "start": 8.5, "label": [34.6, 28.2]}],
    "rivers": nil(0.2), "cities": [city("Teb", 0.6, True), city("Memfis", 1.0), city("Avaris", 1.2),
                                   city("Şaruhen", 7.6)],
    "routes": [{"points": [list(C["Teb"]), [32.0, 26.4], [31.2, 27.2], [30.8, 28.2], [31.1, 29.3], list(C["Memfis"]),
                           [31.4, 30.3], list(C["Avaris"])], "color": ALTIN, "start": 1.5, "duration": 5.0,
                "label": "Ahmose", "dashed": True, "army": True},
               {"points": [list(C["Avaris"]), [32.6, 31.0], [33.6, 31.1], list(C["Şaruhen"])], "color": MOR,
                "start": 7.2, "duration": 2.5, "dashed": True}],
    "clashes": [{"at": list(C["Avaris"]), "start": 6.6}], "years": [{"t": 6.4, "text": "MÖ 1550"}]}
M["punt_seferi"] = {"taban": "dunya", "bounds": fit_bounds((36.5, 21.0), 22), "durationSec": 12,
    "title": "Punt Seferi", "subtitle": "Hatşepsut'un gemileri güneye açılıyor",
    "routes": [{"points": [list(C["Teb"]), list(C["Koptos"]), list(C["Mersa Gavasis"])], "color": ALTIN,
                "start": 0.8, "duration": 2.0, "dashed": True},
               {"points": [list(C["Mersa Gavasis"]), [35.2, 25.0], [37.2, 22.0], [38.6, 19.0], [39.4, 16.3]],
                "color": ALTIN, "start": 2.8, "duration": 4.0, "label": "Gemiler", "dashed": True, "army": True},
               {"points": [[39.6, 15.9], [38.3, 18.9], [36.7, 22.1], [35.0, 25.0], [34.1, 26.3]],
                "color": YESIL, "start": 8.0, "duration": 3.0, "label": "Tütsü ağaçları", "dashed": True}],
    "rivers": nil(0.3, label=False), "cities": [city("Teb", 0.4, True), city("Mersa Gavasis", 1.8, side="right")],
    "labels": [{"at": [39.9, 20.0], "text": "Kızıldeniz", "start": 0.4, "kind": "sea"},
               {"at": [38.4, 15.7], "text": "Punt (yaklaşık)", "start": 6.5, "kind": "land"}],
    "years": [{"t": 0.5, "text": "MÖ 1470"}], "note": "Punt'un yeri tartışmalıdır"}
M["megiddo_savas"] = {"taban": "parsomen", "bounds": fit_bounds((35.12, 32.53), 0.5), "durationSec": 12,
    "title": "Megiddo Savaşı", "subtitle": "Tutmosis dar geçidi seçiyor",
    "units": [{"label": "Mısır ordusu", "color": ALTIN, "path": [[34.95, 32.41], [35.03, 32.45], [35.09, 32.50],
               [35.14, 32.55], [35.165, 32.57]], "start": 1.0, "duration": 6.0, "labelSide": "below"},
              {"label": "Kenan güney kanadı", "color": KIZIL, "path": [[35.24, 32.505], [35.22, 32.535]],
               "start": 0.5, "duration": 7.5, "labelSide": "below"},
              {"label": "Kenan kuzey kanadı", "color": KIZIL, "path": [[35.12, 32.645], [35.15, 32.62]],
               "start": 0.5, "duration": 7.5, "labelSide": "above"}],
    "clashes": [{"at": [35.175, 32.575], "start": 8.2}],
    "cities": [city("Megiddo", 0.3, True, side="right")],
    "labels": [{"at": [35.04, 32.6], "text": "Karmel sıradağları", "start": 0.3, "kind": "land"},
               {"at": [35.06, 32.49], "text": "Aruna geçidi", "start": 1.5, "kind": "land"},
               {"at": [35.25, 32.47], "text": "Taanah yolu", "start": 0.6, "kind": "land"},
               {"at": [35.04, 32.62], "text": "Kuzey yolu", "start": 0.6, "kind": "land"}],
    "years": [{"t": 0.3, "text": "MÖ 1457"}], "note": "Karnak yıllıklarına göre",
    "camera": [{"t": 0, "center": [35.12, 32.53], "zoom": 1.0}, {"t": 8, "center": [35.15, 32.55], "zoom": 1.35}]}
M["tutmosis_imparatorluk"] = {"taban": "dunya", "bounds": fit_bounds((35, 30), 25), "durationSec": 12,
    "title": "İmparatorluk Fırat'a Ulaşıyor", "subtitle": "III. Tutmosis'in seferleri",
    "regions": [{"name": "Mısır", "color": ALTIN, "poly": VADI, "start": 0.5, "label": [29.0, 26.0]},
                {"name": "Mısır'a bağlı topraklar", "color": ALTIN, "poly": LEVANT, "start": 6.5, "label": [41.0, 31.0]}],
    "rivers": nil(0.3, label=False) + [{"points": FIRAT, "name": "Fırat", "start": 0.3, "labelAt": [40.8, 35.3]}],
    "routes": [{"points": [list(C["Memfis"]), [32.3, 30.9], list(C["Gazze"]), list(C["Megiddo"])], "color": ALTIN,
                "start": 1.0, "duration": 3.0, "label": "1. sefer", "dashed": True, "army": True},
               {"points": [list(C["Megiddo"]), [35.9, 34.0], [36.9, 35.6], list(C["Kargamış"])], "color": ALTIN,
                "start": 4.5, "duration": 3.0, "label": "8. sefer", "dashed": True, "army": True}],
    "clashes": [{"at": list(C["Megiddo"]), "start": 4.0}],
    "cities": [city("Memfis", 0.6), city("Gazze", 1.5), city("Megiddo", 3.6, True), city("Kargamış", 7.4)],
    "years": [{"t": 1.0, "text": "MÖ 1457"}, {"t": 7.4, "text": "MÖ 1446"}], "note": "Sınırlar yaklaşıktır"}
M["amarna_goc"] = {"taban": "dunya", "bounds": IKI_MISIR, "durationSec": 11,
    "title": "Yeni Başkent", "subtitle": "Ahenaton Teb'i terk ediyor",
    "rivers": nil(0.2), "cities": [city("Teb", 0.5, True), city("Memfis", 0.8), city("Amarna", 6.0, True, label="Ahetaton (Amarna)")],
    "routes": [{"points": [list(C["Teb"]), [32.0, 26.4], [31.2, 27.2], list(C["Amarna"])], "color": ALTIN,
                "start": 2.0, "duration": 4.0, "label": "Ahenaton", "dashed": True}],
    "years": [{"t": 1.5, "text": "MÖ 1346"}],
    "camera": [{"t": 0, "center": [31.3, 27.9], "zoom": 1.0}, {"t": 6.5, "center": [31.3, 27.9], "zoom": 1.0},
               {"t": 10.5, "center": [31.0, 27.4], "zoom": 1.8}]}
M["kades_seferi"] = {"taban": "dunya", "bounds": {"west": 19.5, "east": 47.5, "south": 24.925, "north": 40.675},
    "durationSec": 11, "title": "Kadeş Seferi", "subtitle": "İki imparatorluk karşı karşıya",
    "regions": [{"name": "Mısır", "color": ALTIN, "poly": [[29.0, 31.0], [32.3, 31.3], [34.2, 31.5], [35.0, 33.0], [35.7, 34.4],
                [36.3, 34.3], [35.9, 33.0], [35.6, 31.0], [34.9, 29.6], [34.3, 28.0], [33.5, 27.0], [33.0, 25.0], [32.7, 23.5],
                [31.5, 23.5], [32.0, 25.5], [31.0, 27.0], [30.5, 29.0], [29.3, 30.2]], "start": 0.5, "label": [31.6, 27.2]},
                {"name": "Hitit", "color": KIZIL, "poly": HITIT, "start": 1.0, "label": [34.8, 38.6]}],
    "routes": [{"points": [[31.83, 30.8], [34.47, 31.5], [35.18, 32.58], [35.9, 33.9], [36.52, 34.56]], "color": ALTIN,
                "start": 2.5, "duration": 4.5, "label": "II. Ramses", "dashed": True, "army": True},
               {"points": [[34.62, 40.02], [35.8, 38.3], [36.6, 37.0], [37.16, 36.2], [36.52, 34.56]], "color": KIZIL,
                "start": 3.0, "duration": 4.5, "label": "Muvattali", "dashed": True, "army": True}],
    "clashes": [{"at": [36.52, 34.56], "start": 7.6}],
    "cities": [city("Hattuşa", 1.4, True), city("Teb", 0.8), city("Memfis", 0.9), city("Pi-Ramses", 2.2, side="left"),
               city("Kadeş", 6.8, True), city("Halep", 2.8)],
    "labels": [{"at": [29.5, 33.6], "text": "Akdeniz", "start": 0.6, "kind": "sea"}],
    "rivers": [{"points": [[32.9, 24.1], [32.65, 25.7], [32.0, 26.5], [31.2, 27.5], [30.8, 28.5], [31.25, 29.9],
                [31.24, 30.05], [31.0, 31.4]], "name": "Nil", "start": 0.4, "labelAt": [31.25, 28.0]}],
    "years": [{"t": 0.5, "text": "MÖ 1274"}],
    "camera": [{"t": 0, "center": [33.5, 32.8], "zoom": 1.0}, {"t": 6.5, "center": [33.5, 32.8], "zoom": 1.0},
               {"t": 9.5, "center": [36.2, 34.8], "zoom": 2.2}], "note": "Sınırlar yaklaşıktır"}
M["kades_savas"] = {"taban": "parsomen", "bounds": {"west": 36.19, "east": 36.81, "south": 34.3556, "north": 34.7044},
    "durationSec": 11, "title": "Kadeş Savaşı", "subtitle": "Pusu: Hitit arabaları nehri geçiyor",
    "units": [{"label": "Re Tümeni", "color": ALTIN, "path": [[36.44, 34.36], [36.47, 34.47]], "start": 0.8, "duration": 4.0, "labelSide": "below"},
              {"label": "Amun Tümeni", "color": ALTIN, "path": [[36.455, 34.585], [36.46, 34.6]], "start": 0.5, "duration": 1.5},
              {"label": "Hitit arabaları", "color": KIZIL, "path": [[36.62, 34.58], [36.57, 34.52], [36.52, 34.48], [36.485, 34.47]],
               "start": 4.0, "duration": 3.5, "labelSide": "above"}],
    "clashes": [{"at": [36.48, 34.47], "start": 7.4}], "cities": [{"at": [36.52, 34.56], "label": "Kadeş", "start": 0.3, "major": True}],
    "labels": [{"at": [36.62, 34.66], "text": "Hitit ordusu (gizli)", "start": 0.3, "kind": "land"}],
    "rivers": [{"points": [[36.47, 34.33], [36.49, 34.42], [36.505, 34.5], [36.515, 34.56], [36.53, 34.62], [36.52, 34.7], [36.5, 34.75]],
                "name": "Asi", "start": 0.2, "labelAt": [36.495, 34.43]}],
    "camera": [{"t": 0, "center": [36.5, 34.53], "zoom": 1.0}, {"t": 7, "center": [36.5, 34.5], "zoom": 1.35}],
    "note": "Mısır kaynaklarına göre"}
M["tunc_cokus"] = {"taban": "dunya", "bounds": fit_bounds((30, 35), 28), "durationSec": 12,
    "title": "Tunç Çağı'nın Çöküşü", "subtitle": "Deniz Kavimleri",
    "regions": [{"name": "Hitit", "color": KIZIL, "poly": HITIT, "start": 0.4, "end": 6.0, "label": [33.0, 38.9]}],
    "routes": [{"points": [[24.0, 38.0], [27.0, 36.6], [30.5, 36.0], [33.3, 35.3], list(C["Ugarit"])], "color": MAVI,
                "start": 1.5, "duration": 4.0, "label": "Deniz Kavimleri", "dashed": True, "army": True},
               {"points": [[25.0, 36.5], [28.0, 34.0], [31.0, 32.2], [31.6, 31.4]], "color": MAVI,
                "start": 3.0, "duration": 4.5, "dashed": True, "army": True},
               {"points": [[22.0, 32.5], [25.5, 31.7], [28.5, 31.2], [30.4, 31.2]], "color": MAVI,
                "start": 3.8, "duration": 4.0, "dashed": True}],
    "clashes": [{"at": list(C["Ugarit"]), "start": 5.5}, {"at": [31.5, 31.35], "start": 8.0}],
    "cities": [city("Mikene", 0.8), city("Truva", 0.9), city("Hattuşa", 1.0, True), city("Ugarit", 1.2),
               city("Alaşiya", 1.4, label="Alaşiya (Kıbrıs)", side="left"), city("Memfis", 1.6)],
    "labels": [{"at": [27.5, 33.0], "text": "Akdeniz", "start": 0.4, "kind": "sea"}],
    "years": [{"t": 0.5, "text": "MÖ 1200"}, {"t": 7.6, "text": "MÖ 1177"}], "note": "Yollar temsilidir"}
M["yabanci_taclar"] = {"taban": "dunya", "bounds": fit_bounds((36, 29.5), 36), "durationSec": 14,
    "title": "Yabancı Taçlar", "subtitle": "Mısır tahtı el değiştiriyor",
    "regions": [{"name": "Mısır", "color": ALTIN, "poly": MISIR_GENIS, "start": 0.3, "label": [28.0, 25.5]}],
    "routes": [{"points": [[31.8, 19.6], [33.0, 21.5], [32.9, 24.1], list(C["Teb"]), [31.6, 27.0], list(C["Memfis"])],
                "color": YESIL, "start": 0.8, "duration": 2.4, "label": "Kuş", "dashed": True, "army": True},
               {"points": [list(C["Ninova"]), [39.5, 35.5], [36.0, 33.0], [34.0, 31.2], list(C["Memfis"])],
                "color": KAHVE, "start": 4.0, "duration": 2.4, "label": "Asur", "dashed": True, "army": True},
               {"points": [list(C["Sus"]), [44.5, 33.3], [39.0, 34.5], [35.0, 31.8], list(C["Memfis"])],
                "color": MAVI, "start": 7.2, "duration": 2.4, "label": "Pers", "dashed": True, "army": True},
               {"points": [[23.0, 39.3], [26.5, 37.0], [30.0, 33.5], list(C["Pelusion"]), list(C["Memfis"])],
                "color": MOR, "start": 10.4, "duration": 2.4, "label": "Makedonya", "dashed": True, "army": True}],
    "cities": [city("Memfis", 0.5, True), city("Teb", 0.6), city("Ninova", 3.8), city("Babil", 3.9), city("Sus", 7.0)],
    "labels": [{"at": [28.0, 34.0], "text": "Akdeniz", "start": 0.3, "kind": "sea"}],
    "years": [{"t": 0.8, "text": "MÖ 728"}, {"t": 4.0, "text": "MÖ 671"}, {"t": 7.2, "text": "MÖ 525"},
              {"t": 10.4, "text": "MÖ 332"}], "note": "Sınırlar yaklaşıktır"}
M["iskender_misir"] = {"taban": "dunya", "bounds": fit_bounds((28.5, 30.5), 9), "durationSec": 12,
    "title": "İskender Mısır'da", "subtitle": "Pelusion'dan Siva vahasına",
    "rivers": nil(0.2, label=False),
    "routes": [{"points": [list(C["Pelusion"]), [31.9, 30.6], [31.3, 30.1], list(C["Memfis"])], "color": MOR,
                "start": 0.8, "duration": 2.0, "dashed": True, "army": True},
               {"points": [list(C["Memfis"]), [30.9, 30.5], [30.3, 31.0], list(C["İskenderiye"]), list(C["Paraitonion"]),
                           [26.3, 30.5], list(C["Siva"])], "color": MOR, "start": 3.0, "duration": 4.5, "label": "İskender", "dashed": True, "army": True}],
    "cities": [city("Pelusion", 0.5), city("Memfis", 1.2), city("İskenderiye", 4.4, True), city("Siva", 7.4, True, label="Siva vahası")],
    "labels": [{"at": [27.8, 32.4], "text": "Akdeniz", "start": 0.3, "kind": "sea"},
               {"at": [26.5, 28.6], "text": "Batı Çölü", "start": 0.5, "kind": "land"}],
    "years": [{"t": 0.5, "text": "MÖ 332"}, {"t": 4.4, "text": "MÖ 331"}],
    "camera": [{"t": 0, "center": [28.5, 30.5], "zoom": 1.0}, {"t": 8.5, "center": [28.5, 30.5], "zoom": 1.0},
               {"t": 11.5, "center": [29.92, 31.1], "zoom": 2.0}]}
ROMA_133 = [
    [[7.5, 44], [9, 44.4], [12.3, 45.5], [13.7, 45.7], [12.5, 44], [14, 42.5], [16, 41.9], [18.5, 40.2], [16.5, 38], [15.6, 38],
     [15.7, 40], [14, 41], [12.5, 41.8], [10.5, 43], [8, 43.8]],
    [[12.4, 38.1], [15.6, 38.3], [15.1, 36.7], [12.5, 37.6]],
    [[-9, 43.7], [-2, 43.4], [3.2, 42.4], [3.2, 41.8], [0.5, 40.5], [-0.3, 39.4], [0.2, 38.7], [-0.7, 37.6], [-2.1, 36.7],
     [-5.6, 36.0], [-7.4, 37.2], [-8.9, 37]],
    [[19.4, 41.8], [19.3, 40.4], [20.2, 39.4], [21.1, 38.3], [21.6, 37], [22.8, 36.4], [23.2, 38], [24, 38.2], [22.9, 40.2],
     [24, 40.8], [26.0, 40.8], [26.6, 41.6], [23.5, 42], [21, 42.6]],
    [[8.5, 37], [10.3, 37.3], [11.1, 36.9], [10.5, 36], [11.1, 35.2], [10.1, 34.2], [8.5, 34.5]],
    [[26.1, 40], [26.9, 39], [27.3, 37.6], [28, 36.7], [29.6, 36.2], [31, 36.8], [31.5, 38], [30, 39.8], [29.5, 41], [27.5, 40.9]]]
ROMA_51 = [
    [[3.2, 42.5], [7.5, 43.8], [7.6, 45.9], [6.8, 47.5], [8.2, 48.9], [8, 50], [6, 51], [3, 51.2], [-1, 49.6], [-4.5, 48.5],
     [-1.2, 46.2], [-1.6, 43.4]],
    [[31, 36.8], [31.5, 38], [30, 39.8], [32, 41.8], [35, 42], [37.5, 41], [35.5, 39], [36.2, 36.9], [34.5, 36.8], [32.5, 36.1]],
    [[35.6, 36.9], [37.0, 37.0], [38.5, 36.5], [38.8, 35.2], [37.0, 33.0], [35.9, 32.2], [34.9, 31.6], [35.0, 33.0], [35.6, 34.4],
     [35.8, 35.6]],
    [[19.9, 30.9], [20.1, 32.2], [21.5, 32.9], [23.2, 32.6], [25.0, 31.7], [25.0, 30], [20, 29.5]]]
M["roma_genisleme"] = {"taban": "dunya", "bounds": fit_bounds((18, 37), 40), "durationSec": 12,
    "title": "Roma'nın Gölgesi", "subtitle": "Akdeniz Roma'nın eline geçiyor",
    "regions": [{"name": "Roma" if i == 0 else "", "color": ROMA, "poly": p, "start": 1.0 + 0.3 * i, **({"label": [13.0, 43.2]} if i == 0 else {})}
                for i, p in enumerate(ROMA_133)]
               + [{"name": "", "color": ROMA, "poly": p, "start": 5.0 + 0.4 * i} for i, p in enumerate(ROMA_51)]
               + [{"name": "Mısır", "color": ALTIN, "poly": MISIR_GENIS, "start": 0.4, "label": [29.0, 27.5]}],
    "cities": [city("Roma", 0.8, True), city("İskenderiye", 0.6, True), city("Kartaca", 1.6), city("Atina", 2.0)],
    "years": [{"t": 1.0, "text": "MÖ 133"}, {"t": 5.0, "text": "MÖ 51"}], "note": "Sınırlar yaklaşıktır",
    "camera": [{"t": 0, "center": [18, 37], "zoom": 1.0}, {"t": 8.5, "center": [18, 37], "zoom": 1.0},
               {"t": 11.5, "center": [27, 33], "zoom": 1.6}]}
M["aktion_savas"] = {"taban": "parsomen", "bounds": fit_bounds((20.72, 38.93), 0.5), "durationSec": 12,
    "title": "Aktion Deniz Savaşı", "subtitle": "Kleopatra'nın gemileri ayrılıyor",
    "units": [{"label": "Oktavianus · Agrippa", "color": ROMA, "path": [[20.5, 38.98], [20.58, 38.96]], "start": 0.5,
               "duration": 4.0, "labelSide": "above"},
              {"label": "Antonius", "color": MOR, "path": [[20.74, 38.955], [20.66, 38.955]], "start": 1.0,
               "duration": 3.5, "labelSide": "below"},
              {"label": "Kleopatra", "color": ALTIN, "path": [[20.73, 38.94], [20.70, 38.90], [20.67, 38.85]],
               "start": 6.0, "duration": 4.0, "labelSide": "below"}],
    "clashes": [{"at": [20.62, 38.96], "start": 4.6}],
    "labels": [{"at": [20.88, 38.98], "text": "Ambrakia Körfezi", "start": 0.3, "kind": "sea"},
               {"at": [20.5, 38.86], "text": "İon Denizi", "start": 0.3, "kind": "sea"},
               {"at": [20.78, 39.04], "text": "Aktion burnu", "start": 0.5, "kind": "land"}],
    "years": [{"t": 0.3, "text": "MÖ 31"}], "note": "Antik kaynaklara göre",
    "camera": [{"t": 0, "center": [20.72, 38.93], "zoom": 1.0}, {"t": 6, "center": [20.68, 38.91], "zoom": 1.2}]}
M["napolyon_resit"] = {"taban": "dunya", "bounds": fit_bounds((30, 32), 14), "durationSec": 11,
    "title": "Napolyon Mısır'da", "subtitle": "Reşit'te bulunan taş",
    "rivers": nil(0.2, label=False),
    "routes": [{"points": [[23.2, 35.5], [26.5, 33.5], list(C["İskenderiye"])], "color": MAVI, "start": 0.8,
                "duration": 2.5, "label": "Fransız donanması", "dashed": True, "army": True},
               {"points": [list(C["İskenderiye"]), [30.6, 30.9], list(C["Kahire"])], "color": MAVI, "start": 3.5,
                "duration": 2.0, "dashed": True}],
    "cities": [city("İskenderiye", 2.8), city("Kahire", 5.2), city("Ebukır", 6.0, side="left"),
               city("Reşit", 6.8, True, side="right", label="Reşit (Rosetta)")],
    "labels": [{"at": [27.5, 34.0], "text": "Akdeniz", "start": 0.3, "kind": "sea"}],
    "years": [{"t": 0.5, "text": "1798"}, {"t": 6.8, "text": "1799"}],
    "camera": [{"t": 0, "center": [30, 32], "zoom": 1.0}, {"t": 7.0, "center": [30, 32], "zoom": 1.0},
               {"t": 10.5, "center": [30.6, 31.2], "zoom": 2.2}]}

if __name__ == "__main__":
    from scripts.doc_maps import check_bounds
    for k, v in M.items():
        check_bounds(v["bounds"])
    json.dump(M, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
    print(len(M), "harita")
