"""
doc_maps.py - Coğrafi harita sahneleri (Remotion MapStory) için taban harita.

Taban: NASA Blue Marble "Whole world - land and oceans 12000" (kamu malı,
eşdikdörtgen, 24000×12000). Eşdikdörtgende boylam/enlem doğrudan piksele
dönüşür; bu yüzden kentler, rotalar ve sınırlar GERÇEK koordinatlarıyla
yerleşir. Bölge, 16:9 oranında (derece cinsinden) kırpılıp 2560×1440'a ölçeklenir.
"""

from pathlib import Path

from PIL import Image

OUT_W, OUT_H = 2560, 1440
WORLD_COMMONS = "File:Whole world - land and oceans 12000.jpg"


def fit_bounds(center: tuple[float, float], lon_span: float) -> dict:
    """Merkez (boylam, enlem) ve boylam genişliğinden 16:9 sınırlar."""
    lon, lat = center
    lat_span = lon_span * OUT_H / OUT_W
    return {"west": round(lon - lon_span / 2, 4), "east": round(lon + lon_span / 2, 4),
            "south": round(lat - lat_span / 2, 4), "north": round(lat + lat_span / 2, 4)}


def check_bounds(b: dict, tol: float = 0.02) -> None:
    ratio = (b["east"] - b["west"]) / (b["north"] - b["south"])
    if abs(ratio - OUT_W / OUT_H) > tol * OUT_W / OUT_H:
        raise ValueError(f"Harita sınırları 16:9 değil (oran {ratio:.3f}); fit_bounds kullanın")
    if not (-180 <= b["west"] < b["east"] <= 180 and -90 <= b["south"] < b["north"] <= 90):
        raise ValueError(f"Geçersiz sınırlar: {b}")


def lonlat_to_px(lon: float, lat: float, size: tuple[int, int]) -> tuple[float, float]:
    """Eşdikdörtgen dünya görüntüsünde boylam/enlem → piksel."""
    w, h = size
    return (lon + 180) / 360 * w, (90 - lat) / 180 * h


def prepare_base(world_path: str | Path, bounds: dict, out_path: str | Path) -> Path:
    """Dünya görüntüsünden bölgeyi kırp, 2560×1440 kaydet."""
    check_bounds(bounds)
    Image.MAX_IMAGE_PIXELS = None
    world = Image.open(world_path).convert("RGB")
    x0, y0 = lonlat_to_px(bounds["west"], bounds["north"], world.size)
    x1, y1 = lonlat_to_px(bounds["east"], bounds["south"], world.size)
    crop = world.crop((round(x0), round(y0), round(x1), round(y1)))
    crop = crop.resize((OUT_W, OUT_H), Image.LANCZOS)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    crop.save(out_path, quality=95)
    return out_path
