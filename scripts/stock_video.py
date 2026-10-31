"""
stock_video.py - Pexels stok video arama ve indirme.

Belgeselde atmosfer görüntüleri (gökyüzü, bozkır, ateş, toz, eller…) ve
fotoğraflara bindirilen hareketli katmanlar (toz zerreleri, sis, kıvılcım)
için kullanılır. Pexels lisansı ticari kullanıma izin verir, atıf zorunlu
değildir; yine de çekenin adı açıklamaya yazılır.

Senaryo planında çekim {"stock": {"q": "arama", "id": 123}} biçimindedir.
"id" verilmişse (inceleme sonrası sabitlenmiş) o video kullanılır; yoksa
aramanın ilk uygun sonucu seçilir ve kayda geçer.
"""

import json
import os
import time
from pathlib import Path

import requests

from scripts.utils import logger

API = "https://api.pexels.com/videos"
MIN_WIDTH = 1920
PREFERRED_WIDTH = 2560


class StockError(Exception):
    pass


def _headers() -> dict:
    key = os.getenv("PEXELS_API_KEY", "").strip()
    if not key:
        raise StockError("PEXELS_API_KEY tanımlı değil (GitHub secret olarak eklenmeli)")
    return {"Authorization": key}


def _get(url: str, params: dict | None = None, retries: int = 4) -> dict:
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=_headers(), timeout=60)
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.HTTPError(f"HTTP {r.status_code}")
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if attempt == retries - 1:
                raise StockError(f"Pexels isteği başarısız: {e}") from e
            time.sleep(2 ** (attempt + 1))
    return {}


def best_file(video: dict) -> dict | None:
    """Videonun en uygun mp4 dosyası: ≥1920 genişlik, 2560'a en yakın."""
    files = [f for f in video.get("video_files", [])
             if f.get("file_type") == "video/mp4" and (f.get("width") or 0) >= MIN_WIDTH
             and (f.get("width") or 0) >= (f.get("height") or 0)]
    if not files:
        return None
    return min(files, key=lambda f: abs(f["width"] - PREFERRED_WIDTH))


def summarize(video: dict) -> dict:
    """Kayıt ve inceleme için gereken alanlar."""
    f = best_file(video) or {}
    user = video.get("user") or {}
    return {
        "id": video.get("id"), "duration": video.get("duration", 0),
        "width": f.get("width"), "height": f.get("height"), "link": f.get("link"),
        "preview": video.get("image"), "page": video.get("url"),
        "author": user.get("name", ""), "author_url": user.get("url", ""),
    }


def search(query: str, min_duration: float = 0, per_page: int = 15) -> list[dict]:
    """Yatay, yeterince büyük ve uzun videolar (Pexels sıralamasıyla)."""
    data = _get(f"{API}/search", {"query": query, "orientation": "landscape",
                                  "size": "large", "per_page": per_page})
    out = []
    for v in data.get("videos", []):
        s = summarize(v)
        if s["link"] and s["duration"] >= min_duration:
            out.append(s)
    return out


def get_video(video_id: int) -> dict:
    s = summarize(_get(f"{API}/videos/{int(video_id)}"))
    if not s["link"]:
        raise StockError(f"Pexels {video_id}: uygun çözünürlükte dosya yok")
    return s


def resolve(spec: dict, min_duration: float = 0) -> dict:
    """Çekim tanımını somut videoya çevir: sabit id varsa o, yoksa ilk arama sonucu."""
    if spec.get("id"):
        return get_video(spec["id"])
    results = search(spec["q"], min_duration=min_duration)
    if not results:
        raise StockError(f"Pexels'te sonuç yok: {spec['q']!r}")
    return results[0]


def download(info: dict, out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"pexels_{info['id']}.mp4"
    if path.exists() and path.stat().st_size > 100_000:
        return path
    for attempt in range(4):
        try:
            with requests.get(info["link"], stream=True, timeout=300) as r:
                r.raise_for_status()
                with open(path, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            return path
        except requests.RequestException as e:
            if attempt == 3:
                raise StockError(f"Pexels indirme hatası ({info['id']}): {e}") from e
            time.sleep(2 ** (attempt + 1))
    return path


def fetch_all(specs: dict[str, dict], out_dir: Path) -> dict:
    """
    {anahtar: {"q": ..., "id": ...?, "min": sn?}} → {anahtar: {"path", "credit"}}.
    Seçimler out_dir/credits.json'a yazılır (açıklama ve sabitleme için).
    """
    out_dir = Path(out_dir)
    result = {}
    for key, spec in specs.items():
        info = resolve(spec, min_duration=spec.get("min", 0))
        path = download(info, out_dir)
        result[key] = {"path": str(path), "credit": {
            "id": info["id"], "author": info["author"], "page": info["page"], "query": spec.get("q", "")}}
        logger.info("Pexels: %s ← %s (%s)", key, info["id"], info["author"])
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "credits.json").write_text(
        json.dumps({k: v["credit"] for k, v in result.items()}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return result
