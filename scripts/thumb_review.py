"""
thumb_review.py - Kapak (thumbnail) rakip analizi için inceleme sayfaları.

<klasör>/kapak_rakipler.json'daki videoların kapakları indirilir (Actions'ta;
i.ytimg.com bulut oturumundan erişilemiyor) ve:
- kapak_rakipler_NN.jpg : normal boy ızgara, altında izlenme · kanal
- kapak_mobil.jpg       : gerçek telefon boyutu (168×94) ızgara — "ilk bakışta ne seçiliyor?"
- kapak_olcumler.json   : parlaklık, kontrast, doygunluk, renk canlılığı, kenar yoğunluğu
yazılır. Kendi kapaklarımız (kapak_adaylari/*.jpg varsa) mobil ızgaranın içine
rastgele değil sabit konumlara yerleştirilir ki rakiplerin arasında nasıl
göründükleri değerlendirilebilsin.
"""

import json
from io import BytesIO
from pathlib import Path

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont

from scripts.doc_review import FONT, _sheet
from scripts.utils import logger

THUMB_URL = "https://i.ytimg.com/vi/{id}/hqdefault.jpg"
MOBILE = (168, 94)


def _crop_16_9(im: Image.Image) -> Image.Image:
    """hqdefault 480×360 üst/alt siyah bantlı gelir; 16:9 orta bölümü al."""
    w, h = im.size
    th = int(w * 9 / 16)
    top = (h - th) // 2
    return im.crop((0, top, w, top + th))


def metrics(im: Image.Image) -> dict:
    """Kapağın nesnel ölçüleri (küçük boyutta seçilebilirlikle ilişkili)."""
    a = np.asarray(im.convert("RGB").resize((320, 180)), dtype=np.float32) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    mx, mn = a.max(axis=2), a.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    rg, yb = r - g, 0.5 * (r + g) - b
    colorful = float(np.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2))
    gy, gx = np.gradient(lum)
    edges = float((np.hypot(gx, gy) > 0.08).mean())
    return {"parlaklik": round(float(lum.mean()), 3), "kontrast": round(float(lum.std()), 3),
            "doygunluk": round(float(sat.mean()), 3), "canlilik": round(colorful, 3),
            "kenar": round(edges, 3)}


def fetch(video_id: str) -> Image.Image | None:
    try:
        r = requests.get(THUMB_URL.format(id=video_id), timeout=30)
        r.raise_for_status()
        return _crop_16_9(Image.open(BytesIO(r.content)).convert("RGB"))
    except Exception as e:
        logger.warning("Kapak inmedi (%s): %s", video_id, e)
        return None


def mobile_grid(images: list[tuple[Image.Image, str]], path: Path, cols: int = 6) -> Path:
    """Telefon boyutunda ızgara; altında yalnızca kısa etiket (numara)."""
    w, h = MOBILE
    pad, lab = 14, 22
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + pad + lab) + pad), (15, 15, 15))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(FONT), 16)
    for i, (im, label) in enumerate(images):
        x = pad + (i % cols) * (w + pad)
        y = pad + (i // cols) * (h + pad + lab)
        sheet.paste(im.resize(MOBILE, Image.LANCZOS), (x, y))
        draw.text((x, y + h + 3), label, font=font, fill="yellow")
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=90)
    return path


def run(folder: Path) -> list[Path]:
    folder = Path(folder)
    cfg_path = folder / "kapak_rakipler.json"
    if not cfg_path.exists():
        return []
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    out_dir = folder / "inceleme"
    out_dir.mkdir(exist_ok=True)
    cells, mobile, report = [], [], []
    for n, r in enumerate(cfg["rakipler"], 1):
        im = fetch(r["id"])
        if im is None:
            continue
        m = metrics(im)
        report.append({**r, **m, "no": n})
        views = f"{r['views'] / 1e6:.1f} M" if r["views"] >= 1e6 else f"{r['views'] // 1000} B"
        cells.append((im, f"#{n} {views} · {r['channel'][:20]}"))
        mobile.append((im, f"#{n}"))
    # Kendi aday kapaklarımız (varsa) rakiplerin arasına
    for k, p in enumerate(sorted((folder / "kapak_adaylari").glob("*.jpg")) if (folder / "kapak_adaylari").exists() else []):
        im = Image.open(p).convert("RGB")
        report.append({"id": p.stem, "title": f"ADAY {p.stem}", "channel": "BİZ", **metrics(im)})
        mobile.insert(min(len(mobile), 3 + k * 7), (im, f"★{p.stem}"))
    sheets = []
    for k in range(0, len(cells), 20):
        sheets.append(_sheet(cells[k:k + 20], out_dir / f"kapak_rakipler_{k // 20 + 1:02d}.jpg",
                             f"Rakip kapakları (en çok izlenen) — sayfa {k // 20 + 1}"))
    sheets.append(mobile_grid(mobile, out_dir / "kapak_mobil.jpg"))
    (out_dir / "kapak_olcumler.json").write_text(json.dumps(report, ensure_ascii=False, indent=1),
                                                encoding="utf-8")
    logger.info("Kapak incelemesi: %d kapak, %d sayfa", len(report), len(sheets))
    return sheets
