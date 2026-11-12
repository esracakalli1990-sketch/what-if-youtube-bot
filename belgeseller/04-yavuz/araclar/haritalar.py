"""Yavuz Sultan Selim: MapStory haritaları (gerçek boylam/enlem; sınırlar yaklaşık)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.doc_maps import fit_bounds  # noqa: E402

OSM, SAF, MEM, ALTIN, GRI = "#b5302a", "#3f7d4e", "#c99a2e", "#e3b04b", "#8a8a8a"

# Kentler (boylam, enlem)
C = {
    "İstanbul": [28.97, 41.01], "Edirne": [26.56, 41.68], "Amasya": [35.83, 40.65], "Trabzon": [39.72, 41.0],
    "Manisa": [27.43, 38.61], "Kefe": [35.38, 45.03], "Akkerman": [30.35, 46.2], "Çorlu": [27.8, 41.16],
    "Bursa": [29.06, 40.18], "Yenişehir": [29.65, 40.26], "Sivas": [37.02, 39.75], "Erzincan": [39.49, 39.75],
    "Erzurum": [41.27, 39.9], "Çaldıran": [43.95, 39.14], "Tebriz": [46.29, 38.08], "Kemah": [39.03, 39.6],
    "Maraş": [36.93, 37.58], "Elbistan": [37.2, 38.2], "Diyarbakır": [40.22, 37.91], "Halep": [37.16, 36.2],
    "Mercidabık": [37.07, 36.53], "Şam": [36.29, 33.51], "Gazze": [34.47, 31.5], "Kahire": [31.24, 30.04],
    "Mekke": [39.83, 21.42], "Medine": [39.61, 24.47], "Antalya": [30.7, 36.9], "Ankara": [32.85, 39.93],
    "Bağdat": [44.36, 33.31], "İsfahan": [51.67, 32.65], "Ayıntab": [37.38, 37.07], "Malatya": [38.31, 38.35],
}


def city(name, start, major=False, side=None, label=None):
    c = {"at": C[name], "label": label or name, "start": start}
    if major:
        c["major"] = True
    if side:
        c["side"] = side
    return c


# Yaklaşık sınırlar
OSM_1500 = [[16.5, 45.0], [19.3, 42.0], [19.4, 40.3], [21.0, 37.0], [23.0, 36.5], [24.0, 38.5], [26.0, 40.6],
            [26.3, 40.0], [26.5, 39.0], [27.2, 37.5], [28.5, 36.7], [30.5, 36.8], [32.5, 36.1], [34.0, 36.3],
            [35.0, 37.0], [35.5, 38.3], [37.0, 39.0], [38.5, 39.6], [40.5, 39.9], [41.5, 41.4], [39.0, 41.1],
            [36.0, 41.7], [33.0, 42.0], [31.0, 41.2], [29.2, 41.25], [28.0, 41.6], [28.6, 43.5], [29.6, 45.2],
            [28.2, 45.5], [22.5, 44.6], [21.5, 45.0], [19.0, 45.0]]
SAF_1502 = [[44.5, 39.7], [46.5, 39.9], [48.6, 39.2], [48.0, 37.5], [47.0, 37.0], [45.5, 37.2], [44.8, 38.2]]
SAF_1510 = [[44.0, 39.8], [46.5, 39.8], [48.5, 41.0], [49.5, 40.3], [49.0, 38.5], [51.0, 37.0], [54.0, 37.3],
            [57.0, 38.2], [61.0, 36.5], [61.5, 31.0], [61.0, 26.0], [57.5, 25.5], [54.0, 26.5], [51.5, 27.8],
            [50.0, 30.0], [48.0, 30.0], [47.5, 30.9], [45.5, 32.5], [44.0, 33.5], [42.5, 34.5], [42.0, 36.8],
            [43.5, 37.5], [44.3, 38.4]]
DOGU_1514 = [[38.5, 39.6], [40.5, 39.9], [41.5, 41.4], [43.0, 41.0], [43.8, 40.0], [43.0, 39.0], [41.5, 38.8],
             [40.0, 39.0], [38.0, 39.0]]
DULKADIR = [[35.8, 37.3], [37.6, 37.2], [38.3, 38.0], [38.0, 38.9], [36.5, 39.0], [35.6, 38.2]]
DIYARBAKIR = [[38.3, 37.0], [41.5, 36.9], [42.8, 37.6], [42.0, 38.6], [40.0, 38.9], [38.6, 38.3]]
MEM_1516 = [[25.0, 31.6], [29.0, 31.0], [32.3, 31.3], [34.2, 31.3], [34.9, 32.5], [35.5, 34.5], [35.8, 36.0],
            [36.2, 36.8], [38.5, 36.8], [38.5, 35.0], [38.0, 33.5], [37.0, 31.0], [38.0, 28.0], [39.0, 25.0],
            [40.5, 21.5], [41.5, 19.0], [39.5, 18.5], [38.5, 21.0], [36.5, 24.5], [35.0, 27.5], [34.5, 28.5],
            [33.5, 27.5], [34.5, 25.0], [35.5, 23.5], [36.0, 22.0], [31.0, 22.0], [25.0, 22.0]]
OSM_1520 = [[16.0, 45.0], [19.3, 40.5], [21.0, 37.5], [26.0, 39.5], [27.0, 37.0], [30.0, 36.3], [33.0, 36.0],
            [35.8, 36.2], [34.9, 32.0], [32.6, 31.3], [29.0, 31.0], [25.2, 31.6], [25.0, 22.5], [36.0, 22.5],
            [38.5, 21.0], [39.5, 18.5], [41.5, 19.0], [40.5, 21.5], [39.0, 25.0], [38.0, 28.0], [37.0, 31.0],
            [38.0, 33.5], [38.5, 35.0], [41.5, 36.9], [42.8, 37.6], [43.8, 40.0], [43.0, 41.0], [41.5, 41.5],
            [36.0, 41.8], [31.0, 41.3], [29.2, 41.3], [28.0, 44.0], [30.0, 45.5], [22.0, 46.5]]

SEAS = {"Karadeniz": [34.5, 43.3], "Akdeniz": [27.0, 34.0], "Hazar Denizi": [51.0, 41.5], "Kızıldeniz": [37.5, 22.5]}


def sea(*names, start=0.4):
    return [{"at": SEAS[n], "text": n, "start": start, "kind": "sea"} for n in names]


M = {}

M["m_osmanli_1500"] = {"taban": "dunya", "bounds": fit_bounds((37.0, 40.0), 24), "durationSec": 12,
    "title": "İmparatorluğun Uç Köşesi", "subtitle": "Osmanlı Devleti, 1500 civarı",
    "regions": [{"name": "Osmanlı", "color": OSM, "poly": OSM_1500, "start": 0.6, "label": [31.0, 39.0]},
                {"name": "Safevîler", "color": SAF, "poly": SAF_1502, "start": 7.5, "label": [46.6, 38.4]}],
    "cities": [city("İstanbul", 0.5, side="left"), city("Amasya", 1.5),
               city("Trabzon", 3.0, major=True, side="right")],
    "labels": sea("Karadeniz") + [{"at": [43.5, 42.3], "text": "Gürcü beylikleri", "start": 4.5, "kind": "land"}],
    "years": [{"t": 0.5, "text": "1500"}, {"t": 7.5, "text": "1501"}], "note": "Sınırlar yaklaşıktır",
    "camera": [{"t": 0, "center": [33.0, 40.0], "zoom": 1.0}, {"t": 3.0, "center": [39.5, 40.5], "zoom": 1.7},
               {"t": 7.0, "center": [42.5, 40.0], "zoom": 1.4}]}

M["m_safevi"] = {"taban": "dunya", "bounds": fit_bounds((45.0, 35.5), 32), "durationSec": 13,
    "title": "Doğudan Gelen Fırtına", "subtitle": "Safevî Devleti, 1501–1510",
    "regions": [{"name": "Osmanlı", "color": OSM, "poly": OSM_1500, "start": 0.4},
                {"name": "", "color": SAF, "poly": SAF_1502, "start": 0.8, "end": 4.5},
                {"name": "Safevîler · 1510", "color": SAF, "poly": SAF_1510, "start": 4.5, "label": [54.0, 32.0]}],
    "routes": [{"points": [[46.29, 38.08], [42.5, 39.0], [38.5, 39.2], [34.5, 38.8]], "color": SAF, "start": 8.0,
                "duration": 3.0, "label": "Kızılbaş propagandası", "dashed": True, "army": False}],
    "cities": [city("Tebriz", 0.8, major=True, side="right"), city("Bağdat", 6.0), city("İsfahan", 6.5)],
    "labels": sea("Karadeniz", "Hazar Denizi"),
    "years": [{"t": 0.5, "text": "1501"}, {"t": 4.5, "text": "1510"}], "note": "Sınırlar yaklaşıktır"}

M["m_selim_yolu"] = {"taban": "dunya", "bounds": fit_bounds((32.0, 42.6), 18), "durationSec": 12,
    "title": "Şehzadenin Yolu", "subtitle": "Trabzon'dan Edirne'ye, 1510–1511",
    "routes": [{"points": [C["Trabzon"], [36.5, 42.6], C["Kefe"]], "color": ALTIN, "start": 1.0, "duration": 2.5,
                "label": "Denizden Kırım'a", "dashed": True, "army": False},
               {"points": [C["Kefe"], [33.0, 46.2], C["Akkerman"], [28.6, 44.2], [27.5, 42.6], C["Edirne"]],
                "color": OSM, "start": 4.0, "duration": 4.0, "label": "Selim'in ordusu", "dashed": True}],
    "clashes": [{"at": [27.85, 41.2], "start": 9.0}],
    "cities": [city("Trabzon", 0.5, major=True, side="right"), city("Kefe", 2.8), city("Akkerman", 5.0),
               city("Edirne", 7.0, side="left"), city("İstanbul", 0.5), city("Çorlu", 8.8, side="left",
               label="Çorlu · Uğraşdere")],
    "labels": sea("Karadeniz"),
    "years": [{"t": 0.5, "text": "1510"}, {"t": 8.5, "text": "1511"}], "note": "Güzergâh temsilidir"}

M["m_caldiran_seferi"] = {"taban": "dunya", "bounds": fit_bounds((37.5, 39.3), 21), "durationSec": 13,
    "title": "Doğu Seferi", "subtitle": "İstanbul'dan Çaldıran'a, 1514",
    "routes": [{"points": [C["İstanbul"], [30.5, 40.75], C["Ankara"], [34.8, 39.8], C["Sivas"], C["Erzincan"],
                           C["Erzurum"], [42.8, 39.5], C["Çaldıran"]], "color": OSM, "start": 1.0, "duration": 8.0,
                "label": "Osmanlı ordusu", "dashed": True},
               {"points": [C["Tebriz"], [45.2, 38.7], [44.2, 39.05]], "color": SAF, "start": 6.0, "duration": 3.0,
                "label": "Safevî ordusu", "dashed": True}],
    "clashes": [{"at": C["Çaldıran"], "start": 9.4}],
    "cities": [city("İstanbul", 0.5, side="left"), city("Sivas", 4.0), city("Erzincan", 5.5),
               city("Çaldıran", 9.0, major=True, side="left"), city("Tebriz", 5.8, side="right")],
    "labels": sea("Karadeniz"),
    "years": [{"t": 0.5, "text": "Nisan 1514"}, {"t": 9.4, "text": "23 Ağustos 1514"}],
    "note": "Güzergâh yaklaşıktır",
    "camera": [{"t": 0, "center": [37.5, 39.3], "zoom": 1.0}, {"t": 8.5, "center": [43.0, 39.0], "zoom": 1.8}]}

M["m_1515"] = {"taban": "dunya", "bounds": fit_bounds((38.5, 38.6), 14), "durationSec": 12,
    "title": "Doğu Tamamlanıyor", "subtitle": "1514–1516",
    "regions": [{"name": "Osmanlı", "color": OSM, "poly": OSM_1500, "start": 0.4},
                {"name": "", "color": OSM, "poly": DOGU_1514, "start": 1.0},
                {"name": "Dulkadir", "color": GRI, "poly": DULKADIR, "start": 0.6, "end": 5.0, "label": [36.9, 38.2]},
                {"name": "", "color": OSM, "poly": DULKADIR, "start": 5.0},
                {"name": "Diyarbakır", "color": GRI, "poly": DIYARBAKIR, "start": 0.6, "end": 8.0,
                 "label": [40.6, 37.7]},
                {"name": "", "color": OSM, "poly": DIYARBAKIR, "start": 8.0},
                {"name": "Memlûkler", "color": MEM, "poly": MEM_1516, "start": 10.0, "label": [36.8, 35.0]}],
    "cities": [city("Kemah", 2.0, side="left"), city("Maraş", 4.5), city("Elbistan", 4.8, side="right"),
               city("Diyarbakır", 7.5, major=True), city("Halep", 10.0)],
    "years": [{"t": 0.5, "text": "1514"}, {"t": 2.0, "text": "1515"}, {"t": 8.0, "text": "1516"}],
    "note": "Sınırlar yaklaşıktır"}

M["m_memluk"] = {"taban": "dunya", "bounds": fit_bounds((34.0, 30.5), 30), "durationSec": 12,
    "title": "Memlûk Devleti", "subtitle": "Mısır, Suriye ve Hicaz, 1516",
    "regions": [{"name": "Osmanlı", "color": OSM, "poly": OSM_1500, "start": 0.4, "label": [31.0, 39.0]},
                {"name": "", "color": OSM, "poly": DOGU_1514, "start": 0.4},
                {"name": "", "color": OSM, "poly": DULKADIR, "start": 0.4},
                {"name": "", "color": OSM, "poly": DIYARBAKIR, "start": 0.4},
                {"name": "Memlûkler", "color": MEM, "poly": MEM_1516, "start": 1.5, "label": [30.0, 26.5]}],
    "cities": [city("Kahire", 2.5, major=True, side="left"), city("Şam", 3.5), city("Halep", 4.0),
               city("Mekke", 5.0, major=True), city("Medine", 5.3), city("İstanbul", 0.5)],
    "labels": sea("Akdeniz", "Kızıldeniz"), "clashes": [{"at": [36.9, 36.9], "start": 8.0}],
    "years": [{"t": 0.5, "text": "1516"}], "note": "Sınırlar yaklaşıktır",
    "camera": [{"t": 0, "center": [34.0, 30.5], "zoom": 1.0}, {"t": 7.0, "center": [36.5, 34.5], "zoom": 1.6}]}

M["m_sina"] = {"taban": "dunya", "bounds": fit_bounds((33.6, 31.4), 9), "durationSec": 13,
    "title": "Çöl Yolu", "subtitle": "Şam'dan Kahire'ye, Aralık 1516 – Ocak 1517",
    "routes": [{"points": [C["Şam"], [35.6, 32.6], [34.9, 31.9], C["Gazze"]], "color": OSM, "start": 0.8,
                "duration": 3.0, "label": "", "dashed": True},
               {"points": [C["Gazze"], [33.8, 31.13], [32.6, 30.95], [31.9, 30.8], [31.5, 30.4], C["Kahire"]],
                "color": OSM, "start": 4.0, "duration": 7.0, "label": "Osmanlı ordusu", "dashed": True}],
    "cities": [city("Şam", 0.5, side="right"), city("Gazze", 3.6), city("Kahire", 10.5, major=True, side="left")],
    "labels": sea("Akdeniz") + [{"at": [33.6, 29.9], "text": "Sina Çölü", "start": 3.5, "kind": "land"}],
    "years": [{"t": 0.5, "text": "Aralık 1516"}, {"t": 4.0, "text": "Ocak 1517"}], "note": "Güzergâh temsilidir",
    "camera": [{"t": 0, "center": [33.6, 31.4], "zoom": 1.0}, {"t": 5.0, "center": [32.7, 30.9], "zoom": 1.4}]}

# Ridaniye: Kahire'nin kuzeydoğusu (parşömen zemin, yakın plan)
NIL = [[31.2, 29.94], [31.225, 30.0], [31.23, 30.05], [31.225, 30.1], [31.21, 30.18]]
M["m_ridaniye"] = {"taban": "parsomen", "bounds": fit_bounds((31.31, 30.07), 0.30), "durationSec": 14,
    "title": "Ridaniye", "subtitle": "Kahire'nin kuzeydoğusu",
    "rivers": [{"points": NIL, "name": "Nil", "start": 0.3, "labelAt": [31.205, 30.0]}],
    "lines": [{"points": [[31.28, 30.068], [31.30, 30.085], [31.32, 30.101]], "kind": "trench", "start": 0.8,
               "duration": 1.5, "color": MEM, "label": "Hendek ve sabit toplar", "labelAt": [31.262, 30.104]}],
    "units": [{"label": "Memlûk hattı", "color": MEM, "path": [[31.296, 30.08], [31.296, 30.08]], "start": 1.0,
               "duration": 0.5, "labelSide": "below"},
              {"label": "Osmanlı ana ordusu", "color": OSM, "path": [[31.445, 30.135], [31.375, 30.112]],
               "start": 2.5, "duration": 2.5, "labelSide": "above"},
              {"label": "Kuşatma kolu", "color": "#d9663f", "path": [[31.43, 30.095], [31.395, 30.035], [31.335, 30.017],
                                                                  [31.305, 30.052]], "start": 5.0, "duration": 4.0,
               "labelSide": "below"},
              {"label": "Tomanbay'ın hücumu", "color": MEM, "path": [[31.31, 30.088], [31.362, 30.106]],
               "start": 9.5, "duration": 1.8, "labelSide": "below"}],
    "clashes": [{"at": [31.302, 30.064], "start": 9.0}, {"at": [31.368, 30.109], "start": 11.4}],
    "cities": [city("Kahire", 0.5, major=True, side="left")],
    "labels": [{"at": [31.35, 30.008], "text": "Mukattam tepeleri", "start": 4.5, "kind": "land"}],
    "years": [{"t": 0.5, "text": "22 Ocak 1517"}], "note": "Konumlar yaklaşıktır",
    "camera": [{"t": 0, "center": [31.31, 30.07], "zoom": 1.0}, {"t": 14, "center": [31.33, 30.07], "zoom": 1.12}]}

M["m_sinirlar"] = {"taban": "dunya", "bounds": fit_bounds((32.0, 33.0), 44), "durationSec": 12,
    "title": "Sekiz Yılda", "subtitle": "Osmanlı toprakları, 1512 → 1520",
    "regions": [{"name": "Osmanlı · 1512", "color": OSM, "poly": OSM_1500, "start": 0.6, "end": 5.0,
                 "label": [30.0, 40.0]},
                {"name": "Osmanlı · 1520", "color": OSM, "poly": OSM_1520, "start": 5.0, "label": [31.0, 27.0]}],
    "cities": [city("İstanbul", 0.5, major=True), city("Kahire", 5.5), city("Mekke", 6.0), city("Diyarbakır", 6.5)],
    "labels": sea("Akdeniz", "Karadeniz", "Kızıldeniz"),
    "years": [{"t": 0.5, "text": "1512"}, {"t": 5.0, "text": "1520"}], "note": "Sınırlar yaklaşıktır"}

# Bilgi grafikleri
M["k_sehzadeler"] = {"bilesen": "Infographic", "type": "zaman", "title": "Üç Şehzade",
    "subtitle": "II. Bayezid'in tahta aday oğulları", "durationSec": 10,
    "events": [{"date": "Ahmed", "text": "Amasya · vezirlerin gözdesi"},
               {"date": "Korkud", "text": "Manisa · âlim, sakin"},
               {"date": "Selim", "text": "Trabzon · ordunun gözdesi"}]}


def esnet(spec: dict, seconds: float) -> dict:
    """Haritayı yuvaya göre uzat: bütün zamanlar orantılı ölçeklenir (sona boş bekleme kalmaz)."""
    if spec.get("bilesen"):
        return {**spec, "durationSec": round(seconds, 1)}
    k = seconds / spec["durationSec"]
    out = {**spec, "durationSec": round(seconds, 1)}
    for key in ("regions", "routes", "units", "clashes", "cities", "labels", "rivers", "lines", "convoys"):
        if key in spec:
            out[key] = [{**it, **{f: round(it[f] * k, 2) for f in ("start", "end", "duration") if f in it}}
                        for it in spec[key]]
    for key in ("years", "camera"):
        if key in spec:
            out[key] = [{**it, "t": round(it["t"] * k, 2)} for it in spec[key]]
    return out
