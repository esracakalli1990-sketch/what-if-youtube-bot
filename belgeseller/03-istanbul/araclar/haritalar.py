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
    labels=[{"at": [28.982, 41.0445], "text": "~1,5 km kara yolu", "start": 2.0, "kind": "land"}],
    convoys=[{"points": [[29.02, 41.045], [28.999, 41.037]] + KARA_YOLU[1:], "count": 14, "start": 3.0, "duration": 6.0,
              "spacing": 0.35, "color": OSM}],
    camera=[{"t": 0, "center": [28.965, 41.025], "zoom": 1.0}, {"t": 3, "center": [28.975, 41.03], "zoom": 1.6},
            {"t": 12, "center": [28.97, 41.03], "zoom": 1.9}], durationSec=14)

if __name__ == "__main__":
    from scripts.doc_maps import check_bounds
    for v in M.values():
        check_bounds(v["bounds"])
    json.dump(M, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
    print(len(M), "harita")
