"""
doc_review.py - Video seçimi için inceleme sayfaları (temas sayfaları).

Kesitleri ve stok görüntüleri körlemesine seçmemek için:
- Uzun filmlerden (Commons) her N saniyede bir kare alınır; karelerin altına
  dakika:saniye yazılır → planda {"film": ..., "start": sn} seçilir.
- Plandaki her Pexels sorgusu için ilk adayların önizlemeleri dizilir;
  altına id, süre ve çekenin adı yazılır → planda "id" sabitlenir.

Çıktılar <klasör>/inceleme/ altına yazılır (küçük JPG'ler + adaylar.json).
"""

import json
import subprocess
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

from scripts.utils import logger

FONT = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "SourceSans3.ttf"
CELL_W, CELL_H, COLS = 384, 216, 5


def _sheet(cells: list[tuple[Image.Image, str]], path: Path, title: str = "") -> Path:
    """Küçük kareleri etiketleriyle tek bir JPG'ye diz."""
    font = ImageFont.truetype(str(FONT), 22)
    head = 44 if title else 0
    rows = (len(cells) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * CELL_W, head + rows * (CELL_H + 30)), "black")
    draw = ImageDraw.Draw(sheet)
    if title:
        draw.text((10, 8), title, font=font, fill="white")
    for i, (im, label) in enumerate(cells):
        im = im.convert("RGB")
        im.thumbnail((CELL_W - 6, CELL_H - 6))
        x, y = (i % COLS) * CELL_W, head + (i // COLS) * (CELL_H + 30)
        sheet.paste(im, (x + (CELL_W - im.width) // 2, y + (CELL_H - im.height) // 2))
        draw.text((x + 6, y + CELL_H + 2), label, font=font, fill="yellow")
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=82)
    return path


def film_frames(video: Path, every: float, tmp: Path) -> list[tuple[float, Path]]:
    """Videodan her `every` saniyede bir küçük kare çıkar."""
    tmp.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video),
                    "-vf", f"fps=1/{every},scale={CELL_W}:-2", str(tmp / "k%05d.jpg")], check=True)
    frames = sorted(tmp.glob("k*.jpg"))
    return [(i * every, f) for i, f in enumerate(frames)]


def film_sheets(key: str, video: Path, out_dir: Path, every: float = 15.0, per_sheet: int = 40) -> list[Path]:
    frames = film_frames(video, every, out_dir / f".kareler_{key}")
    sheets = []
    for n in range(0, len(frames), per_sheet):
        cells = [(Image.open(p), f"{int(t // 60)}:{int(t % 60):02d}  ({t:.0f} sn)")
                 for t, p in frames[n:n + per_sheet]]
        sheets.append(_sheet(cells, out_dir / f"film_{key}_{n // per_sheet + 1:02d}.jpg",
                             f"{key} — her {every:.0f} sn'de bir kare (sayfa {n // per_sheet + 1})"))
    return sheets


def stock_sheet(key: str, query: str, candidates: list[dict], out_dir: Path) -> Path:
    cells = []
    for c in candidates:
        try:
            r = requests.get(c["preview"], timeout=60)
            r.raise_for_status()
            from io import BytesIO
            im = Image.open(BytesIO(r.content))
        except Exception as e:  # önizleme inmezse boş kare
            logger.warning("Önizleme inmedi (%s): %s", c["id"], e)
            im = Image.new("RGB", (CELL_W, CELL_H), "gray")
        cells.append((im, f"id {c['id']} · {c['duration']} sn · {c['author'][:18]}"))
    return _sheet(cells, out_dir / f"stok_{key}.jpg", f"{key}: \"{query}\"")


def run(folder: Path, plan: dict, every: float = 15.0, per_query: int = 5) -> list[Path]:
    """Plandaki filmler ve stok sorguları için inceleme sayfaları üret."""
    from scripts.archive_images import fetch_films
    from scripts.stock_video import StockError, search

    folder = Path(folder)
    out_dir = folder / "inceleme"
    out_dir.mkdir(exist_ok=True)
    sheets, candidates = [], {}
    films = plan.get("films", {})
    if films:
        for key, v in fetch_films(films, folder / "build" / "films").items():
            sheets += film_sheets(key, Path(v["path"]), out_dir, every)
    for key, spec in plan.get("stock", {}).items():
        if spec.get("id"):
            continue  # zaten sabitlenmiş
        try:
            found = search(spec["q"])[:per_query]
        except StockError as e:
            # Anahtar yoksa film sayfaları yine de üretilsin
            logger.warning("Pexels adayları atlandı: %s", e)
            break
        candidates[key] = {"q": spec["q"], "adaylar": found}
        if found:
            sheets.append(stock_sheet(key, spec["q"], found, out_dir))
    (out_dir / "adaylar.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    logger.info("İnceleme: %d sayfa → %s", len(sheets), out_dir)
    return sheets
