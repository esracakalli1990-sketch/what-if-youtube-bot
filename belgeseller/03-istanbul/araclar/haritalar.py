"""İstanbul'un Fethi: MapStory haritaları ve bilgi grafikleri (gerçek boylam/enlem)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.doc_maps import fit_bounds

OSM, BIZ, VEN, ALTIN = "#b5302a", "#6a4c93", "#2f6f8f", "#e3b04b"

# Kara parçaları (yaklaşık kıyı çizgileri)
TARIHI_YARIMADA = [[28.986, 41.016], [28.979, 41.018], [28.972, 41.019], [28.962, 41.023], [28.952, 41.029],
                   [28.944, 41.036], [28.9395, 41.041], [28.928, 41.05], [28.90, 41.06], [28.86, 41.06], [28.86, 40.96],
                   [28.905, 40.985], [28.922, 40.9925], [28.935, 40.996], [28.950, 41.000], [28.965, 41.004],
                   [28.981, 41.005], [28.987, 41.009]]
GALATA = [[28.940, 41.060], [28.944, 41.046], [28.950, 41.040], [28.958, 41.035], [28.966, 41.027], [28.974, 41.0225],
          [28.981, 41.025], [28.990, 41.032], [28.998, 41.038], [29.008, 41.043], [29.020, 41.052], [29.040, 41.075],
          [29.06, 41.10], [28.94, 41.10]]
ANADOLU = [[29.009, 41.020], [29.016, 41.030], [29.025, 41.045], [29.045, 41.068], [29.07, 41.10], [29.12, 41.10],
           [29.12, 40.95], [29.035, 40.975], [29.020, 40.995], [29.008, 41.008]]
# Theodosius kara surları: Haliç (Ayvansaray) → Marmara (Yedikule)
KARA_SURU = [[28.9405, 41.0405], [28.937, 41.034], [28.9355, 41.031], [28.930, 41.026], [28.921, 41.019],
             [28.918, 41.012], [28.917, 41.003], [28.920, 40.997], [28.922, 40.9925]]
HALIC_SURU = [[28.9405, 41.0405], [28.948, 41.031], [28.958, 41.024], [28.972, 41.019], [28.983, 41.0165]]
DENIZ_SURU = [[28.986, 41.0125], [28.981, 41.005], [28.965, 41.004], [28.950, 41.000], [28.935, 40.996], [28.922, 40.9925]]
ZINCIR = [[28.982, 41.0168], [28.976, 41.0228]]
KARA_YOLU = [[28.999, 41.037], [28.991, 41.039], [28.982, 41.040], [28.973, 41.037], [28.966, 41.032], [28.962, 41.029]]
KOPRU = [[28.943, 41.0395], [28.947, 41.045]]

SEHIR = fit_bounds((28.955, 41.022), 0.13)
LANDS = [{"poly": TARIHI_YARIMADA}, {"poly": GALATA}, {"poly": ANADOLU}]
BASE_LINES = [{"points": KARA_SURU, "kind": "wall", "start": 0.5, "duration": 2.0},
              {"points": HALIC_SURU, "kind": "wall", "start": 1.0, "duration": 1.5},
              {"points": DENIZ_SURU, "kind": "wall", "start": 1.0, "duration": 1.5}]
SEA = [{"at": [28.965, 40.990], "text": "Marmara Denizi", "start": 0.4, "kind": "sea"},
       {"at": [28.957, 41.032], "text": "Haliç", "start": 0.4, "kind": "sea"},
       {"at": [29.003, 41.022], "text": "Boğaz", "start": 0.4, "kind": "sea"}]
CITY = [{"at": [28.950, 41.012], "label": "Konstantinopolis", "start": 0.6, "major": True},
        {"at": [28.974, 41.026], "label": "Galata", "start": 0.8, "side": "right"}]

def city_map(title, subtitle, day, **extra):
    m = {"taban": "parsomen", "bounds": SEHIR, "durationSec": extra.pop("durationSec", 12), "title": title,
         "subtitle": subtitle, "lands": LANDS, "lines": BASE_LINES + extra.pop("lines", []),
         "labels": SEA + extra.pop("labels", []), "cities": CITY + extra.pop("cities", []),
         "years": [{"t": 0.3, "text": day}] + extra.pop("years", []), "note": extra.pop("note", "Kıyı ve sur çizgileri yaklaşıktır")}
    m.update(extra)
    return m

M = {}
M["sehir_plani"] = city_map("Bin Yıllık Surlar", "Kara, deniz ve Haliç surları", "1453",
    lines=[{"points": ZINCIR, "kind": "chain", "start": 4.0, "duration": 1.5, "label": "Haliç zinciri"}],
    labels=[{"at": [28.905, 41.015], "text": "Theodosius Surları", "start": 2.5, "kind": "land"}],
    camera=[{"t": 0, "center": [28.955, 41.022], "zoom": 1.0}, {"t": 6, "center": [28.955, 41.022], "zoom": 1.0},
            {"t": 10, "center": [28.975, 41.02], "zoom": 1.8}])
M["kusatma_dizilis"] = city_map("Kuşatma Başlıyor", "Osmanlı ordusu surların önünde", "Kuşatmanın 1. günü",
    units=[{"label": "Rumeli birlikleri", "color": OSM, "path": [[28.90, 41.045], [28.925, 41.036]], "start": 1.0, "duration": 2.5},
           {"label": "Sultan'ın otağı · Yeniçeriler", "color": ALTIN, "path": [[28.885, 41.022], [28.908, 41.019]], "start": 1.6, "duration": 2.5, "labelSide": "above"},
           {"label": "Anadolu birlikleri", "color": OSM, "path": [[28.89, 40.995], [28.91, 41.000]], "start": 2.2, "duration": 2.5, "labelSide": "below"},
           {"label": "Zağanos Paşa", "color": OSM, "path": [[28.975, 41.055], [28.962, 41.040]], "start": 2.8, "duration": 2.5, "labelSide": "above"}],
    lines=[{"points": ZINCIR, "kind": "chain", "start": 0.6, "duration": 0.8}],
    convoys=[{"points": [[29.03, 41.06], [29.005, 41.042]], "count": 6, "start": 3.5, "duration": 2.5, "spacing": 0.25,
              "color": OSM, "label": "Osmanlı donanması"}])
M["gemiler_karadan"] = city_map("Gemiler Karadan Yürüyor", "22 Nisan 1453 gecesi", "Kuşatmanın 17. günü",
    lines=[{"points": ZINCIR, "kind": "chain", "start": 0.6, "duration": 0.8, "label": "Zincir"}],
    routes=[{"points": KARA_YOLU, "color": ALTIN, "start": 1.5, "duration": 2.0, "dashed": True, "army": False}],
    labels=[{"at": [28.986, 41.0345], "text": "~1,5 km kara yolu", "start": 2.0, "kind": "land"}],
    convoys=[{"points": [[29.02, 41.045], [28.999, 41.037]] + KARA_YOLU[1:], "count": 14, "start": 3.0, "duration": 6.0,
              "spacing": 0.35, "color": OSM}],
    camera=[{"t": 0, "center": [28.965, 41.025], "zoom": 1.0}, {"t": 3, "center": [28.975, 41.03], "zoom": 1.6},
            {"t": 12, "center": [28.97, 41.03], "zoom": 1.9}], durationSec=14)

# ─── Boğaz ve hisarlar ───
AVRUPA_B = [[28.95, 41.03], [28.98, 41.025], [29.005, 41.043], [29.027, 41.047], [29.044, 41.077], [29.056, 41.085],
            [29.057, 41.103], [29.06, 41.13], [28.95, 41.13]]
ASYA_B = [[29.012, 41.02], [29.043, 41.045], [29.051, 41.051], [29.066, 41.082], [29.067, 41.10], [29.07, 41.13],
          [29.16, 41.13], [29.16, 41.00], [29.02, 41.00]]
M["bogazkesen"] = {"taban": "parsomen", "bounds": fit_bounds((29.04, 41.072), 0.16), "durationSec": 12,
    "title": "Boğazkesen", "subtitle": "İki hisar arasında boğaz", "lands": [{"poly": AVRUPA_B}, {"poly": ASYA_B}],
    "cities": [{"at": [29.0665, 41.0825], "label": "Anadolu Hisarı", "start": 0.8, "side": "right"},
               {"at": [29.0565, 41.0845], "label": "Rumeli Hisarı", "start": 2.5, "major": True, "side": "left"},
               {"at": [28.975, 41.03], "label": "Konstantinopolis", "start": 0.5, "side": "right"}],
    "convoys": [{"points": [[29.066, 41.125], [29.061, 41.095], [29.0605, 41.0865]], "count": 1, "start": 5.0,
                 "duration": 3.0, "color": VEN, "label": "Venedik gemisi"}],
    "clashes": [{"at": [29.0605, 41.0865], "start": 8.0}],
    "labels": [{"at": [29.035, 41.06], "text": "İstanbul Boğazı", "start": 0.4, "kind": "sea"},
               {"at": [29.10, 41.115], "text": "Karadeniz yolu ↑", "start": 4.5, "kind": "land"}],
    "years": [{"t": 0.3, "text": "1452"}], "note": "Kıyı çizgileri yaklaşıktır",
    "camera": [{"t": 0, "center": [29.04, 41.072], "zoom": 1.0}, {"t": 4, "center": [29.055, 41.085], "zoom": 1.9}]}

# ─── Bizans'ın küçülmesi (uydu taban) ───
BIZANS_1050 = [[19.5, 41.5], [19.3, 40.0], [21.0, 37.0], [23.0, 36.3], [26.5, 35.0], [28.5, 36.4], [32.0, 36.1],
               [36.0, 36.0], [36.5, 37.2], [40.0, 37.5], [42.5, 39.5], [42.0, 41.2], [38.0, 41.0], [33.0, 42.0],
               [29.0, 41.3], [28.5, 43.5], [27.0, 44.3], [22.5, 44.5], [20.0, 43.0]]
BIZANS_1453 = [[28.4, 41.25], [28.75, 41.35], [29.1, 41.2], [29.0, 40.95], [28.4, 40.95]]
MORA = [[21.1, 38.2], [22.9, 38.0], [23.3, 37.5], [23.0, 36.4], [22.4, 36.4], [21.6, 36.8], [21.1, 37.6]]
M["bizans_kuculme"] = {"taban": "dunya", "bounds": fit_bounds((28.5, 39.2), 26), "durationSec": 12,
    "title": "Küçülen İmparatorluk", "subtitle": "Bizans, 1050 → 1453",
    "regions": [{"name": "Bizans · 1050", "color": BIZ, "poly": BIZANS_1050, "start": 0.6, "end": 6.0, "label": [31.5, 38.6]},
                {"name": "", "color": BIZ, "poly": BIZANS_1453, "start": 6.0},
                {"name": "", "color": BIZ, "poly": MORA, "start": 6.0}],
    "cities": [{"at": [28.97, 41.01], "label": "Konstantinopolis", "start": 0.4, "major": True}],
    "labels": [{"at": [25.0, 34.6], "text": "Akdeniz", "start": 0.4, "kind": "sea"},
               {"at": [34.0, 43.3], "text": "Karadeniz", "start": 0.4, "kind": "sea"},
               {"at": [22.0, 35.9], "text": "Mora", "start": 7.0, "kind": "land"}],
    "years": [{"t": 0.5, "text": "1050"}, {"t": 6.0, "text": "1453"}], "note": "Sınırlar yaklaşıktır",
    "camera": [{"t": 0, "center": [28.5, 39.2], "zoom": 1.0}, {"t": 7, "center": [28.5, 39.2], "zoom": 1.0},
               {"t": 11, "center": [27.5, 39.5], "zoom": 1.5}]}

M["eski_kusatmalar"] = {"taban": "dunya", "bounds": fit_bounds((31.5, 39.0), 26), "durationSec": 13,
    "title": "Bin Yıllık Kuşatmalar", "subtitle": "Hepsi surlarda durdu",
    "routes": [{"points": [[36.3, 33.5], [34.5, 37.0], [31.0, 39.5], [29.1, 40.95]], "color": "#2e8b57", "start": 1.0,
                "duration": 2.5, "label": "674", "dashed": True},
               {"points": [[36.0, 34.5], [33.5, 38.5], [30.0, 40.3], [29.1, 40.95]], "color": "#2e8b57", "start": 3.5,
                "duration": 2.5, "label": "717", "dashed": True},
               {"points": [[29.06, 40.18], [29.06, 40.6], [29.05, 41.0]], "color": OSM, "start": 6.0,
                "duration": 2.0, "label": "1394", "dashed": True},
               {"points": [[26.56, 41.68], [27.8, 41.4], [28.9, 41.05]], "color": OSM, "start": 8.5,
                "duration": 2.0, "label": "1422", "dashed": True}],
    "clashes": [{"at": [28.95, 41.02], "start": 3.6}, {"at": [28.95, 41.02], "start": 6.1}, {"at": [28.95, 41.02], "start": 8.1},
                {"at": [28.95, 41.02], "start": 10.6}],
    "cities": [{"at": [28.97, 41.01], "label": "Konstantinopolis", "start": 0.4, "major": True},
               {"at": [29.06, 40.18], "label": "Bursa", "start": 5.8}, {"at": [26.56, 41.68], "label": "Edirne", "start": 8.3}],
    "years": [{"t": 1.0, "text": "674"}, {"t": 3.5, "text": "717"}, {"t": 6.0, "text": "1394"}, {"t": 8.5, "text": "1422"}],
    "note": "Yollar temsilidir"}

M["varna_1444"] = {"taban": "dunya", "bounds": fit_bounds((26.8, 42.6), 12), "durationSec": 11,
    "title": "Varna Zaferi", "subtitle": "10 Kasım 1444",
    "routes": [{"points": [[23.0, 46.2], [24.5, 45.0], [26.5, 44.0], [27.6, 43.4], [27.9, 43.2]], "color": "#5b6fa8",
                "start": 1.0, "duration": 3.5, "label": "Haçlı ordusu", "dashed": True},
               {"points": [[26.56, 41.68], [27.2, 42.4], [27.85, 43.15]], "color": OSM, "start": 2.0, "duration": 3.0,
                "label": "II. Murad", "dashed": True}],
    "clashes": [{"at": [27.9, 43.2], "start": 5.5}],
    "cities": [{"at": [27.92, 43.21], "label": "Varna", "start": 4.5, "major": True},
               {"at": [26.56, 41.68], "label": "Edirne", "start": 0.6},
               {"at": [28.97, 41.01], "label": "Konstantinopolis", "start": 0.8}],
    "labels": [{"at": [30.0, 43.0], "text": "Karadeniz", "start": 0.4, "kind": "sea"}],
    "years": [{"t": 0.5, "text": "1444"}], "note": "Yollar temsilidir"}

M["donanma_gelibolu"] = {"taban": "dunya", "bounds": fit_bounds((27.8, 40.7), 10), "durationSec": 11,
    "title": "Osmanlı Donanması", "subtitle": "Gelibolu'dan Marmara'ya",
    "convoys": [{"points": [[26.67, 40.41], [27.4, 40.62], [28.3, 40.85], [28.95, 40.98]], "count": 10, "start": 1.5,
                 "duration": 6.0, "spacing": 0.3, "color": OSM, "label": "Donanma"}],
    "cities": [{"at": [26.67, 40.41], "label": "Gelibolu", "start": 0.6, "side": "left"},
               {"at": [28.97, 41.01], "label": "Konstantinopolis", "start": 0.6, "major": True}],
    "labels": [{"at": [28.0, 40.65], "text": "Marmara", "start": 0.4, "kind": "sea"}],
    "years": [{"t": 0.5, "text": "1453"}]}

M["topun_yolu"] = {"taban": "dunya", "bounds": fit_bounds((27.8, 41.0), 9), "durationSec": 11,
    "title": "Dev Topun Yolculuğu", "subtitle": "Edirne → Konstantinopolis",
    "routes": [{"points": [[26.56, 41.68], [27.0, 41.55], [27.6, 41.35], [28.2, 41.15], [28.92, 41.02]], "color": ALTIN,
                "start": 1.0, "duration": 8.0, "label": "Dev top", "dashed": True}],
    "cities": [{"at": [26.56, 41.68], "label": "Edirne", "start": 0.5, "major": True},
               {"at": [28.97, 41.01], "label": "Konstantinopolis", "start": 0.5, "major": True}],
    "years": [{"t": 0.5, "text": "Şubat–Mart 1453"}], "note": "Güzergâh temsilidir"}

TOP_MEVZILERI = [[28.912, 41.032], [28.906, 41.020], [28.908, 41.008], [28.910, 40.998]]
M["top_mevzileri"] = city_map("Toplar Surların Karşısında", "Batarya mevzileri", "Kuşatmanın 6. günü",
    units=[{"label": "Top bataryası", "color": ALTIN, "path": [q, q], "start": 1.0 + i * 0.6, "duration": 0.5,
            "labelSide": "above" if i % 2 else "below"} for i, q in enumerate(TOP_MEVZILERI)],
    clashes=[{"at": [28.931, 41.027], "start": 4.5}, {"at": [28.921, 41.019], "start": 5.2},
             {"at": [28.918, 41.009], "start": 5.9}, {"at": [28.918, 41.0], "start": 6.6}],
    camera=[{"t": 0, "center": [28.955, 41.022], "zoom": 1.0}, {"t": 3, "center": [28.925, 41.018], "zoom": 1.7}])

M["deniz_savasi"] = city_map("20 Nisan Deniz Savaşı", "Dört gemi zinciri aşıyor", "Kuşatmanın 15. günü",
    lines=[{"points": ZINCIR, "kind": "chain", "start": 0.6, "duration": 0.8, "label": "Zincir"}],
    convoys=[{"points": [[28.975, 40.965], [28.988, 40.995], [28.992, 41.012], [28.983, 41.019], [28.976, 41.021]],
              "count": 4, "start": 1.0, "duration": 8.0, "spacing": 0.45, "color": VEN, "label": "Yardım gemileri"},
             {"points": [[29.02, 41.03], [29.0, 41.01], [28.995, 41.0]], "count": 8, "start": 2.0, "duration": 3.0,
              "spacing": 0.2, "color": OSM}],
    clashes=[{"at": [28.992, 41.004], "start": 4.5}],
    camera=[{"t": 0, "center": [28.975, 41.01], "zoom": 1.3}, {"t": 9, "center": [28.98, 41.015], "zoom": 1.7}])

M["venedik_baskini"] = city_map("Gece Baskını", "Venedik gemileri Haliç'te", "Kuşatmanın 23. günü",
    convoys=[{"points": [[28.966, 41.0215], [28.962, 41.026], [28.961, 41.0285]], "count": 3, "start": 1.0,
              "duration": 4.0, "spacing": 0.4, "color": VEN, "label": "Yangın gemileri"}],
    units=[{"label": "Osmanlı gemileri", "color": OSM, "path": [[28.957, 41.032], [28.958, 41.031]], "start": 0.5,
            "duration": 0.5, "labelSide": "above"}],
    clashes=[{"at": [28.961, 41.0285], "start": 5.2}],
    camera=[{"t": 0, "center": [28.962, 41.027], "zoom": 2.2}])

M["yuzer_kopru"] = city_map("Haliç'e Köprü", "Fıçılar ve kalaslarla", "Mayıs 1453",
    lines=[{"points": KOPRU, "kind": "bridge", "start": 1.5, "duration": 3.0, "label": "Yüzer köprü"}],
    units=[{"label": "Askerler ve toplar", "color": OSM, "path": [[28.95, 41.05], [28.947, 41.045], [28.943, 41.0395]],
            "start": 5.0, "duration": 3.0}],
    camera=[{"t": 0, "center": [28.95, 41.04], "zoom": 2.0}])

M["son_hucum"] = city_map("Son Hücum", "29 Mayıs 1453 · gece yarısından sonra", "Kuşatmanın 53. günü",
    units=[{"label": "1. dalga", "color": "#c46a4a", "path": [[28.893, 41.030], [28.912, 41.027]], "start": 1.0, "duration": 2.0, "labelSide": "above"},
           {"label": "2. dalga · Anadolu", "color": OSM, "path": [[28.888, 41.008], [28.909, 41.011]], "start": 3.5, "duration": 2.0,
            "labelSide": "below"},
           {"label": "3. dalga · Yeniçeriler", "color": ALTIN, "path": [[28.885, 41.019], [28.913, 41.019]], "start": 6.0,
            "duration": 2.5, "labelSide": "below"}],
    clashes=[{"at": [28.921, 41.019], "start": 3.0}, {"at": [28.921, 41.019], "start": 8.5}],
    labels=[{"at": [28.935, 41.0135], "text": "Topkapı", "start": 0.6, "kind": "land"}],
    camera=[{"t": 0, "center": [28.93, 41.02], "zoom": 1.4}, {"t": 9, "center": [28.915, 41.02], "zoom": 1.8}],
    durationSec=13)

M["kerkoporta"] = city_map("Kerkoporta", "Kuzeydeki küçük kapı", "29 Mayıs, şafak",
    cities=[{"at": [28.9375, 41.0345], "label": "Kerkoporta (rivayet)", "start": 1.0, "side": "left"}],
    clashes=[{"at": [28.9375, 41.0345], "start": 3.0}],
    camera=[{"t": 0, "center": [28.94, 41.032], "zoom": 2.6}])

OSMANLI_1453 = [[19.5, 42.5], [20.5, 40.0], [22.0, 39.5], [23.5, 40.3], [26.0, 40.6], [27.0, 40.3], [26.5, 39.5],
                [27.0, 38.0], [29.0, 37.3], [31.5, 37.0], [33.0, 38.5], [35.5, 40.5], [34.0, 41.9], [31.0, 41.2],
                [29.2, 41.25], [28.2, 41.6], [28.0, 43.8], [24.0, 44.2], [21.5, 44.8]]
OSMANLI_1520 = [[16.0, 45.0], [19.3, 40.5], [21.0, 37.5], [26.0, 39.5], [27.0, 37.0], [30.0, 36.3], [33.0, 36.0],
                [35.8, 36.2], [34.9, 32.0], [32.6, 31.3], [29.0, 31.0], [25.2, 31.6], [25.0, 22.5], [36.0, 22.5],
                [38.0, 28.0], [35.0, 30.0], [37.5, 33.0], [39.5, 36.5], [42.0, 37.2], [43.5, 39.5], [41.5, 41.5],
                [36.0, 41.8], [31.0, 41.3], [29.2, 41.3], [28.0, 44.0], [30.0, 45.5], [22.0, 46.5]]
M["osmanli_yukselis"] = {"taban": "dunya", "bounds": fit_bounds((30.0, 36.0), 34), "durationSec": 12,
    "title": "Bir Dünya İmparatorluğu", "subtitle": "Başkent İstanbul",
    "regions": [{"name": "Osmanlı · 1453", "color": OSM, "poly": OSMANLI_1453, "start": 0.6, "end": 6.0, "label": [26.0, 42.6]},
                {"name": "Osmanlı · 1520", "color": OSM, "poly": OSMANLI_1520, "start": 6.0, "label": [31.0, 27.0]}],
    "routes": [{"points": [[26.56, 41.68], [27.8, 41.4], [28.95, 41.02]], "color": ALTIN, "start": 2.0, "duration": 2.0,
                "label": "Başkent İstanbul'a", "dashed": True, "army": False}],
    "cities": [{"at": [28.97, 41.01], "label": "İstanbul", "start": 3.8, "major": True},
               {"at": [26.56, 41.68], "label": "Edirne", "start": 1.0, "side": "left"}],
    "years": [{"t": 0.5, "text": "1453"}, {"t": 6.0, "text": "1520"}], "note": "Sınırlar yaklaşıktır"}

# ─── Bilgi grafikleri ve karakter kartları ("bilesen") ───
def G(**kw):
    return {"bilesen": "Infographic", "durationSec": kw.pop("durationSec", 9), **kw}

def K(name, role, facts, image="", focusY=0.3, side="left"):
    return {"bilesen": "PortraitCard", "image": image, "name": name, "role": role, "facts": facts,
            "focusY": focusY, "side": side, "durationSec": 7}

M["g_iki_taraf"] = G(type="rakam", title="İki Taraf", subtitle="6 Nisan 1453", background="surlar_genis",
    stats=[{"value": 80, "prefix": "60–", "suffix": " bin", "label": "Osmanlı ordusu (modern tahmin)"},
           {"value": 5, "prefix": "~", "suffix": " bin", "label": "Rum savunucu (Sfrancis)"},
           {"value": 53, "suffix": " gün", "label": "süren kuşatma"}], note="Rakamlar tahminidir")
M["g_hisar"] = G(type="rakam", title="Boğazkesen", subtitle="Rumeli Hisarı, 1452", background="rumeli_hisari",
    stats=[{"value": 4.5, "decimals": 1, "prefix": "~", "suffix": " ay", "label": "inşaat süresi (kaynaklara göre)"},
           {"value": 3, "suffix": " büyük kule", "label": "her birini bir paşa üstlendi"}], durationSec=8)
M["g_top"] = G(type="olcek", title="Dev Top", subtitle="Urban'ın Edirne'de döktüğü top", background="sahi_topu",
    object={"label": "Dev top (kaynaklara göre)", "lengthM": 8, "caption": "Gülleleri yüzlerce kilo ağırlığındaydı"},
    note="Ölçüler yaklaşıktır")
M["g_sur_kesiti"] = G(type="kesit", title="Theodosius Surları", subtitle="Üç kat savunma", background="surlar_kule",
    layers=[{"label": "Hendek", "height": -6, "width": 6, "note": "~20 m genişlik"},
            {"label": "Dış sur", "height": 9, "width": 3, "note": "~8–9 m"},
            {"label": "İç sur", "height": 12, "width": 5, "note": "~12 m, 96 kule"}], note="Ölçüler yaklaşıktır")
M["g_gemiler"] = G(type="rakam", title="Bir Gecede", subtitle="22 Nisan 1453",
    stats=[{"value": 70, "prefix": "~", "suffix": "", "label": "gemi (kaynaklara göre)"},
           {"value": 1.5, "decimals": 1, "prefix": "~", "suffix": " km", "label": "tepelerin üzerinden"},
           {"value": 1, "suffix": " gece", "label": "Haliç'e ulaştılar"}], note="Rakamlar kaynaklara göre değişir")
M["g_tunel"] = G(type="tunel", title="Toprak Altında Savaş", subtitle="Mayıs 1453", background="surlar_kule",
    tunnels={"left": "Osmanlı lağımcıları", "right": "Karşı tünel", "meet": "Yer altında çarpışma"}, durationSec=8)
M["g_yol"] = G(type="zaman", title="Fethe Giden Yol",
    events=[{"date": "1444", "text": "Varna Zaferi"}, {"date": "1451", "text": "Mehmed tahta çıkar"},
            {"date": "1452", "text": "Rumeli Hisarı"}, {"date": "6 Nisan", "text": "Kuşatma başlar"},
            {"date": "22 Nisan", "text": "Gemiler karadan"}, {"date": "29 Mayıs", "text": "Fetih"}], durationSec=10)

M["k_fatih"] = K("II. Mehmed", "Osmanlı Sultanı", ["Doğum: 1432, Edirne", "Tahta çıkış: 1451, 19 yaşında",
                                                   "Fetihte 21 yaşında"], image="fatih_bellini", focusY=0.35)
M["k_candarli"] = K("Çandarlı Halil Paşa", "Sadrazam", ["Barıştan yana", "Kuşatmanın kaldırılmasını önerdi"],
                    image="edirne_cami", side="right")
M["k_zaganos"] = K("Zağanos Paşa", "Vezir", ["Fetihten yana", "Rumeli Hisarı'nda bir kule onun adını taşır"],
                   image="rumeli_hisari_kule")
M["k_urban"] = K("Urban", "Top ustası", ["Önce Bizans'a başvurdu", "Edirne'de dev topu döktü"], image="sahi_topu",
                 side="right")
M["k_konstantin"] = K("XI. Konstantin", "Son Bizans İmparatoru", ["1449'dan beri imparator", "Şehri terk etmedi"],
                      image="mermer_kule", focusY=0.4)
M["k_giustiniani"] = K("Giovanni Giustiniani", "Cenevizli komutan", ["Kara surlarının savunmasını yönetti",
                       "Son hücumda ağır yaralandı"], image="surlar_kule", side="right")
M["k_aksemseddin"] = K("Akşemseddin", "Fatih'in hocası", ["Zafer müjdesi veren mektuplar yazdı",
                       "Eyüp Sultan'ın kabrini bulduğu anlatılır"], image="eyup_sultan")
M["k_ulubatli"] = K("Ulubatlı Hasan", "Yeniçeri", ["Osmanlı geleneğine göre sancağı surlara ilk diken",
                    "Orada şehit düştü"], image="surlar_genis", side="right")

if __name__ == "__main__":
    from scripts.doc_maps import check_bounds
    for v in M.values():
        if "bounds" in v:
            check_bounds(v["bounds"])
    json.dump(M, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
    print(len(M), "harita")
