"""Sümerler: MapStory haritaları (gerçek boylam/enlem; nehir yatakları bugünkü, sınırlar yaklaşık)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.doc_maps import fit_bounds  # noqa: E402

SUMER, AKAD, ELAM, AMURRU, YESIL = "#c99a2e", "#b5302a", "#6b4f8f", "#8a6a3a", "#5f8f4e"

C = {
    "Eridu": [46.10, 30.82], "Ur": [46.10, 30.96], "Uruk": [45.64, 31.32], "Lagaş": [46.41, 31.41],
    "Girsu": [46.14, 31.56], "Umma": [45.89, 31.67], "Nippur": [45.23, 32.13], "Kiş": [44.60, 32.54],
    "Akad": [44.10, 33.10], "Susa": [48.26, 32.19], "Mari": [40.89, 34.55], "Ebla": [36.80, 35.80],
    "Babil": [44.42, 32.54],
}
DICLE = [[39.3, 38.5], [40.2, 37.9], [41.5, 37.2], [43.1, 36.3], [43.7, 35.0], [44.4, 33.3], [45.8, 32.5],
         [46.7, 31.6], [47.4, 31.0], [47.8, 30.5], [48.5, 29.95]]
FIRAT = [[38.8, 38.8], [38.3, 37.5], [38.0, 36.7], [39.0, 35.95], [40.1, 35.3], [41.0, 34.5], [42.2, 33.6],
         [43.8, 33.35], [44.4, 32.5], [45.3, 31.3], [46.25, 31.05], [47.4, 31.0]]
MEZOPOTAMYA = [[38.6, 37.6], [41.5, 37.2], [43.3, 36.2], [44.9, 33.2], [47.5, 31.0], [47.6, 30.2], [46.0, 30.6],
               [44.0, 32.2], [42.0, 33.4], [40.0, 35.0], [38.4, 36.6]]
AKAD_IMP = [[35.9, 36.2], [36.6, 37.4], [39.5, 37.8], [43.5, 37.3], [46.5, 35.2], [48.5, 32.3], [49.5, 29.8],
            [47.6, 29.4], [45.8, 30.6], [42.0, 32.6], [38.5, 33.5], [35.8, 34.6]]


def city(name, start, major=False, side=None, label=None):
    c = {"at": C[name], "label": label or name, "start": start}
    if major:
        c["major"] = True
    if side:
        c["side"] = side
    return c


def nehirler(start):
    return [{"points": DICLE, "name": "Dicle", "start": start, "labelAt": [43.9, 35.9]},
            {"points": FIRAT, "name": "Fırat", "start": start + 0.8, "labelAt": [40.3, 34.7]}]


M = {}

M["m_mezopotamya"] = {"taban": "dunya", "bounds": fit_bounds((43.0, 34.2), 13), "durationSec": 15,
    "title": "Mezopotamya", "subtitle": "İki nehrin arasındaki ülke",
    "rivers": nehirler(0.6),
    "regions": [{"name": "Mezopotamya", "color": YESIL, "poly": MEZOPOTAMYA, "start": 5.0, "label": [42.6, 34.4]}],
    "labels": [{"at": [38.5, 39.6], "text": "Anadolu", "start": 0.4, "kind": "land"},
               {"at": [49.6, 28.6], "text": "Basra Körfezi", "start": 0.4, "kind": "sea"},
               {"at": [34.0, 34.0], "text": "Akdeniz", "start": 0.4, "kind": "sea"}],
    "note": "Nehir yatakları bugünkü hâliyle",
    "camera": [{"t": 0, "center": [41.5, 36.0], "zoom": 1.0}, {"t": 9.0, "center": [45.5, 31.8], "zoom": 1.8}]}

M["m_sumer_sehirler"] = {"taban": "dunya", "bounds": fit_bounds((45.6, 31.7), 3.6), "durationSec": 14,
    "title": "Sümer Şehirleri", "subtitle": "MÖ 3500–2500",
    "rivers": nehirler(0.3),
    "cities": [city("Eridu", 1.0, side="left"), city("Ur", 2.2, side="right"), city("Uruk", 3.4, True, "left"),
               city("Lagaş", 4.6, side="right"), city("Girsu", 5.4, side="right"), city("Umma", 6.2, side="left"),
               city("Nippur", 7.4, side="left"), city("Kiş", 8.6, side="left")],
    "note": "Kıyı çizgisi bugünkü hâliyle",
    "camera": [{"t": 0, "center": [45.6, 31.7], "zoom": 1.0}, {"t": 9.5, "center": [45.6, 31.4], "zoom": 1.4}]}

M["m_sehir_devletleri"] = {"taban": "dunya", "bounds": fit_bounds((45.9, 31.6), 2.0), "durationSec": 13,
    "title": "Şehir Devletleri", "subtitle": "Lagaş ile Umma'nın sınır kavgası",
    "rivers": nehirler(0.3),
    "cities": [city("Lagaş", 0.8, True, "right"), city("Girsu", 1.4, side="right"), city("Umma", 2.0, True, "left"),
               city("Uruk", 2.6, side="left"), city("Ur", 3.0, side="left")],
    "routes": [{"points": [C["Umma"], [46.02, 31.62]], "color": SUMER, "start": 4.5, "duration": 2.0,
                "label": "Umma", "dashed": True},
               {"points": [C["Lagaş"], [46.12, 31.58]], "color": AKAD, "start": 5.0, "duration": 2.0,
                "label": "Lagaş", "dashed": True}],
    "clashes": [{"at": [46.07, 31.60], "start": 7.2}],
    "labels": [{"at": [46.05, 31.78], "text": "Gu-edena (sınır toprağı)", "start": 6.0, "kind": "land"}],
    "note": "Konumlar yaklaşıktır",
    "camera": [{"t": 0, "center": [45.9, 31.6], "zoom": 1.0}]}

M["m_akad"] = {"taban": "dunya", "bounds": fit_bounds((41.5, 34.0), 15), "durationSec": 15,
    "title": "Akad İmparatorluğu", "subtitle": "Sargon ve torunları, MÖ 2334–2154",
    "rivers": nehirler(0.3),
    "regions": [{"name": "Akad", "color": AKAD, "poly": AKAD_IMP, "start": 6.5, "label": [41.0, 34.2]}],
    "routes": [{"points": [C["Akad"], C["Mari"], C["Ebla"], [35.95, 35.6]], "color": AKAD, "start": 1.5,
                "duration": 4.0, "label": "Akdeniz'e", "dashed": True},
               {"points": [C["Mari"], [38.0, 37.2], [35.8, 37.3]], "color": AKAD, "start": 3.5, "duration": 3.0,
                "label": "Toroslar", "dashed": True},
               {"points": [C["Akad"], C["Ur"], [48.5, 29.9]], "color": AKAD, "start": 1.0, "duration": 3.0,
                "label": "Körfez'e", "dashed": True}],
    "cities": [city("Akad", 0.5, True, "right", "Akad (?)"), city("Ur", 2.5, side="right"),
               city("Mari", 3.0, side="left"), city("Ebla", 4.8, side="left"), city("Susa", 5.5, side="right")],
    "labels": [{"at": [34.0, 34.0], "text": "Akdeniz", "start": 0.4, "kind": "sea"},
               {"at": [49.6, 28.6], "text": "Basra Körfezi", "start": 0.4, "kind": "sea"},
               {"at": [36.0, 38.6], "text": "Anadolu", "start": 0.4, "kind": "land"}],
    "years": [{"t": 0.5, "text": "MÖ ~2300"}], "note": "Yaklaşık sınırlar",
    "camera": [{"t": 0, "center": [43.0, 33.5], "zoom": 1.2}, {"t": 6.0, "center": [41.5, 34.0], "zoom": 1.0}]}

M["m_ur_dusus"] = {"taban": "dunya", "bounds": fit_bounds((45.0, 32.3), 6.5), "durationSec": 13,
    "title": "Ur'un Düşüşü", "subtitle": "MÖ ~2004",
    "rivers": nehirler(0.3),
    "routes": [{"points": [[40.5, 33.5], [42.5, 33.0], [44.2, 32.6]], "color": AMURRU, "start": 1.0,
                "duration": 4.0, "label": "Amurru göçleri", "dashed": True},
               {"points": [C["Susa"], [47.4, 31.8], [46.6, 31.2], C["Ur"]], "color": ELAM, "start": 5.5,
                "duration": 4.0, "label": "Elam ordusu", "dashed": False}],
    "clashes": [{"at": C["Ur"], "start": 9.6}],
    "cities": [city("Ur", 0.5, True, "left"), city("Susa", 4.8, True, "right"), city("Nippur", 0.9, side="left")],
    "years": [{"t": 0.5, "text": "MÖ ~2004"}], "note": "Güzergâh yaklaşıktır",
    "camera": [{"t": 0, "center": [45.0, 32.3], "zoom": 1.0}]}


def esnet(spec: dict, seconds: float) -> dict:
    """Haritayı yuvaya göre uzat: bütün zamanlar orantılı ölçeklenir."""
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
