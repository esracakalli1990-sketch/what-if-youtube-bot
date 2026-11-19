"""Kanuni Sultan Süleyman: MapStory haritaları (gerçek boylam/enlem; güzergâh ve sınırlar yaklaşık)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.doc_maps import fit_bounds  # noqa: E402

OSM, MAC, HAB, HAC, SAF, ALTIN = "#b5302a", "#3f5f8f", "#6b4f8f", "#5a6f7f", "#3f7d4e", "#e3b04b"

# Kentler (boylam, enlem)
C = {
    "İstanbul": [28.97, 41.01], "Edirne": [26.56, 41.68], "Sofya": [23.32, 42.70], "Niş": [21.90, 43.32],
    "Belgrad": [20.46, 44.82], "Rodos": [28.22, 36.44], "Marmaris": [28.27, 36.85], "Mohaç": [18.68, 45.99],
    "Budin": [19.04, 47.50], "Viyana": [16.37, 48.21], "Güns": [16.54, 47.39], "Tebriz": [46.29, 38.08],
    "Bağdat": [44.36, 33.31], "Erzurum": [41.27, 39.90], "Preveze": [20.75, 38.96], "Zigetvar": [17.80, 46.05],
    "Ösek": [18.69, 45.55], "Halep": [37.16, 36.20], "Konya": [32.49, 37.87],
}


def city(name, start, major=False, side=None, label=None):
    c = {"at": C[name], "label": label or name, "start": start}
    if major:
        c["major"] = True
    if side:
        c["side"] = side
    return c


M = {}

M["m_belgrad_rodos"] = {"taban": "dunya", "bounds": fit_bounds((24.5, 40.6), 16), "durationSec": 14,
    "title": "İlk İki Sefer", "subtitle": "Belgrad 1521 · Rodos 1522",
    "routes": [{"points": [C["İstanbul"], C["Edirne"], C["Sofya"], C["Niş"], C["Belgrad"]], "color": OSM,
                "start": 1.0, "duration": 5.0, "label": "1521", "dashed": True},
               {"points": [C["İstanbul"], [27.6, 40.4], [26.3, 39.6], [26.5, 38.2], [27.4, 37.3], C["Marmaris"],
                           C["Rodos"]], "color": OSM, "start": 7.0, "duration": 5.0, "label": "1522", "dashed": True}],
    "clashes": [{"at": C["Belgrad"], "start": 6.0}, {"at": C["Rodos"], "start": 12.0}],
    "cities": [city("İstanbul", 0.5, major=True, side="right"), city("Belgrad", 5.6, major=True, side="left"),
               city("Rodos", 11.6, major=True, side="right")],
    "labels": [{"at": [25.0, 35.2], "text": "Akdeniz", "start": 0.4, "kind": "sea"},
               {"at": [30.5, 43.2], "text": "Karadeniz", "start": 0.4, "kind": "sea"}],
    "years": [{"t": 0.5, "text": "1521"}, {"t": 7.0, "text": "1522"}], "note": "Güzergâh yaklaşıktır",
    "camera": [{"t": 0, "center": [24.5, 41.5], "zoom": 1.0}]}

M["m_mohac_seferi"] = {"taban": "dunya", "bounds": fit_bounds((23.0, 44.2), 13), "durationSec": 13,
    "title": "Mohaç Seferi", "subtitle": "İstanbul'dan Mohaç'a, 1526",
    "routes": [{"points": [C["İstanbul"], C["Edirne"], C["Sofya"], C["Niş"], C["Belgrad"], [19.9, 45.25],
                           C["Ösek"], C["Mohaç"]], "color": OSM, "start": 1.0, "duration": 8.0,
                "label": "Osmanlı ordusu", "dashed": True},
               {"points": [C["Budin"], [18.9, 46.9], [18.75, 46.3]], "color": MAC, "start": 6.5, "duration": 2.5,
                "label": "Macar ordusu", "dashed": True}],
    "clashes": [{"at": C["Mohaç"], "start": 9.5}],
    "cities": [city("İstanbul", 0.5, side="right"), city("Belgrad", 4.5), city("Budin", 6.0, side="right"),
               city("Mohaç", 9.0, major=True, side="left")],
    "years": [{"t": 0.5, "text": "Nisan 1526"}, {"t": 9.5, "text": "29 Ağustos 1526"}], "note": "Güzergâh yaklaşıktır",
    "camera": [{"t": 0, "center": [23.0, 44.2], "zoom": 1.0}, {"t": 7.5, "center": [19.2, 46.2], "zoom": 1.9}]}

# Mohaç meydan savaşı (parşömen zemin, yakın plan; konumlar yaklaşık)
M["m_mohac_savasi"] = {"taban": "parsomen", "bounds": fit_bounds((18.66, 45.96), 0.22), "durationSec": 15,
    "title": "Mohaç", "subtitle": "29 Ağustos 1526, öğleden sonra",
    "rivers": [{"points": [[18.72, 46.09], [18.70, 46.02], [18.69, 45.96], [18.70, 45.89]], "name": "Tuna",
                "start": 0.3, "labelAt": [18.735, 45.93]}],
    "units": [{"label": "Macar ağır süvarisi", "color": MAC, "path": [[18.60, 46.02], [18.62, 45.985]],
               "start": 1.0, "duration": 3.0, "labelSide": "above"},
              {"label": "Osmanlı öncüleri (geri çekilir)", "color": "#d9663f",
               "path": [[18.62, 45.98], [18.63, 45.95]], "start": 3.0, "duration": 2.5, "labelSide": "below"},
              {"label": "Zincirli toplar ve yeniçeriler", "color": OSM, "path": [[18.62, 45.935], [18.62, 45.935]],
               "start": 1.5, "duration": 0.5, "labelSide": "below"},
              {"label": "Kuşatan kanat", "color": OSM, "path": [[18.56, 45.94], [18.57, 45.99], [18.60, 46.02]],
               "start": 8.0, "duration": 4.0, "labelSide": "above"}],
    "clashes": [{"at": [18.625, 45.945], "start": 5.8}, {"at": [18.61, 46.0], "start": 11.5}],
    "cities": [city("Mohaç", 0.5, side="right")],
    "years": [{"t": 0.5, "text": "29 Ağustos 1526"}], "note": "Konumlar yaklaşıktır",
    "camera": [{"t": 0, "center": [18.64, 45.97], "zoom": 1.0}]}

M["m_viyana"] = {"taban": "dunya", "bounds": fit_bounds((19.0, 46.6), 10), "durationSec": 13,
    "title": "Viyana Seferi", "subtitle": "1529",
    "routes": [{"points": [C["Belgrad"], [19.9, 45.25], C["Mohaç"], C["Budin"], [17.6, 47.8], C["Viyana"]],
                "color": OSM, "start": 1.0, "duration": 7.0, "label": "Osmanlı ordusu", "dashed": True},
               {"points": [C["Viyana"], [17.6, 47.6], C["Budin"]], "color": OSM, "start": 10.0, "duration": 2.5,
                "label": "Geri dönüş", "dashed": True}],
    "clashes": [{"at": C["Viyana"], "start": 8.3}],
    "cities": [city("Belgrad", 0.5, side="right"), city("Budin", 4.5, side="right"),
               city("Viyana", 7.8, major=True, side="left")],
    "years": [{"t": 0.5, "text": "Mayıs 1529"}, {"t": 8.3, "text": "27 Eylül – 15 Ekim 1529"}],
    "note": "Güzergâh yaklaşıktır",
    "camera": [{"t": 0, "center": [19.0, 46.6], "zoom": 1.0}, {"t": 7.0, "center": [16.8, 48.0], "zoom": 1.8}]}

M["m_bagdat"] = {"taban": "dunya", "bounds": fit_bounds((38.0, 37.8), 22), "durationSec": 13,
    "title": "Irakeyn Seferi", "subtitle": "Tebriz ve Bağdat, 1534",
    "routes": [{"points": [C["İstanbul"], [32.0, 40.0], [36.5, 39.5], C["Erzurum"], [44.0, 39.0], C["Tebriz"]],
                "color": OSM, "start": 1.0, "duration": 5.5, "label": "1534", "dashed": True},
               {"points": [C["Tebriz"], [46.0, 36.5], [45.5, 35.0], C["Bağdat"]], "color": OSM, "start": 7.0,
                "duration": 4.0, "label": "Zagros'u aşarak", "dashed": True}],
    "cities": [city("İstanbul", 0.5, side="right"), city("Tebriz", 6.0, major=True, side="right"),
               city("Bağdat", 10.8, major=True, side="left")],
    "labels": [{"at": [34.5, 43.3], "text": "Karadeniz", "start": 0.4, "kind": "sea"},
               {"at": [51.0, 41.5], "text": "Hazar Denizi", "start": 0.4, "kind": "sea"}],
    "years": [{"t": 0.5, "text": "1534"}], "note": "Güzergâh yaklaşıktır",
    "camera": [{"t": 0, "center": [38.0, 37.8], "zoom": 1.0}, {"t": 7.0, "center": [44.0, 35.8], "zoom": 1.6}]}

M["m_preveze"] = {"taban": "dunya", "bounds": fit_bounds((20.5, 38.9), 3.2), "durationSec": 13,
    "title": "Preveze", "subtitle": "28 Eylül 1538",
    "routes": [{"points": [[20.72, 38.97], [20.55, 38.90], [20.30, 38.85]], "color": OSM, "start": 2.0,
                "duration": 4.0, "label": "Osmanlı donanması", "dashed": False},
               {"points": [[19.75, 38.95], [20.05, 38.88]], "color": HAC, "start": 1.0, "duration": 3.0,
                "label": "Haçlı donanması", "dashed": False},
               {"points": [[20.05, 38.88], [19.70, 39.20]], "color": HAC, "start": 9.0, "duration": 3.0,
                "label": "Geri çekilme", "dashed": True}],
    "clashes": [{"at": [20.18, 38.86], "start": 6.5}],
    "cities": [city("Preveze", 0.5, major=True, side="right")],
    "labels": [{"at": [20.0, 38.55], "text": "İyon Denizi", "start": 0.4, "kind": "sea"}],
    "years": [{"t": 0.5, "text": "28 Eylül 1538"}], "note": "Konumlar yaklaşıktır",
    "camera": [{"t": 0, "center": [20.4, 38.95], "zoom": 1.0}]}

M["m_zigetvar"] = {"taban": "dunya", "bounds": fit_bounds((23.0, 44.0), 14), "durationSec": 13,
    "title": "Son Sefer", "subtitle": "İstanbul'dan Zigetvar'a, 1566",
    "routes": [{"points": [C["İstanbul"], C["Edirne"], C["Sofya"], C["Niş"], C["Belgrad"], [19.9, 45.25],
                           [18.8, 45.6], C["Zigetvar"]], "color": OSM, "start": 1.0, "duration": 8.0,
                "label": "Osmanlı ordusu", "dashed": True}],
    "clashes": [{"at": C["Zigetvar"], "start": 9.5}],
    "cities": [city("İstanbul", 0.5, side="right"), city("Belgrad", 5.5, side="right"),
               city("Zigetvar", 9.0, major=True, side="left")],
    "years": [{"t": 0.5, "text": "Mayıs 1566"}, {"t": 9.5, "text": "Ağustos – Eylül 1566"}],
    "note": "Güzergâh yaklaşıktır",
    "camera": [{"t": 0, "center": [23.0, 44.0], "zoom": 1.0}, {"t": 8.0, "center": [18.6, 45.8], "zoom": 1.9}]}


def esnet(spec: dict, seconds: float) -> dict:
    """Haritayı yuvaya göre uzat: bütün zamanlar orantılı ölçeklenir."""
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
