"""
archive_images.py - Wikimedia Commons'tan lisanslı arşiv görseli indirme.

Belgesel serisi gerçek eser/arşiv görselleriyle çalışır. Bu modül:
- Commons'ta dosya arar (search_commons)
- Dosyanın boyut ve lisans bilgisini okur (file_info)
- Yalnızca yeniden kullanıma izin veren lisansları kabul eder
  (kamu malı, CC0, CC BY, CC BY-SA); NC/ND ve "fair use" reddedilir
- Görseli indirir ve yazar/lisans kaydını tutar (açıklamadaki
  "Görsel kaynakları" listesi bu kayıttan üretilir)

Wikimedia, User-Agent başlığı olmayan istekleri reddeder.
"""

import json
import re
import time
from pathlib import Path

import requests

from scripts.utils import logger

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "TarihBelgeseliBot/1.0 (https://github.com/esracakalli1990-sketch/what-if-youtube-bot)"
MIN_WIDTH = 1920
# İndirilen görselin uzun kenarı en fazla bu kadar (Ken Burns için 1440p'nin
# üstünde pay bırakır, dev TIFF'leri indirmeyi önler).
DOWNLOAD_WIDTH = 4000

_ALLOWED_LICENSE = re.compile(r"^(public domain|pd\b|pd-|cc0|cc[- ]by(-sa)?[- ]?\d|cc[- ]by(-sa)?$)", re.I)
_BLOCKED_LICENSE = re.compile(r"\b(nc|nd)\b|non-?commercial|no ?deriv|fair use", re.I)


class ArchiveError(Exception):
    pass


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    return s


_MIN_INTERVAL = 1.0  # Wikimedia'yı yormamak için istekler arası asgari süre
_last_request = [0.0]


def _wait_turn():
    gap = time.monotonic() - _last_request[0]
    if gap < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - gap)
    _last_request[0] = time.monotonic()


def _retry_delay(response, attempt: int) -> float:
    """429'da sunucunun Retry-After değerine uy, yoksa üstel bekle."""
    try:
        return min(float(response.headers.get("retry-after", "")), 120.0)
    except (TypeError, ValueError, AttributeError):
        return float(2 ** (attempt + 1))


def _request(session, url: str, params: dict | None = None, retries: int = 6, timeout: int = 60):
    for attempt in range(retries):
        _wait_turn()
        response = None
        try:
            response = session.get(url, params=params, timeout=timeout)
            if response.status_code == 429 or response.status_code >= 500:
                raise requests.HTTPError(f"HTTP {response.status_code}")
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if attempt == retries - 1:
                raise ArchiveError(f"Commons isteği başarısız ({url}): {e}") from e
            delay = _retry_delay(response, attempt)
            logger.warning("Commons %s — %.0f sn sonra tekrar denenecek", e, delay)
            time.sleep(delay)
    raise ArchiveError("Commons isteği başarısız")


def _get(session, params: dict) -> dict:
    params = {"format": "json", "formatversion": 2, **params}
    try:
        return _request(session, COMMONS_API, params=params).json()
    except ValueError as e:
        raise ArchiveError(f"Commons yanıtı okunamadı: {e}") from e


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    return re.sub(r"\s+", " ", text).strip()


def license_allowed(short_name: str) -> bool:
    """Lisans yeniden kullanıma (ticari dahil, türev dahil) izin veriyor mu?"""
    name = (short_name or "").strip()
    if not name or _BLOCKED_LICENSE.search(name):
        return False
    return bool(_ALLOWED_LICENSE.match(name))


def normalize_title(title: str) -> str:
    title = title.strip()
    return title if title.lower().startswith("file:") else f"File:{title}"


def _parse_page(page: dict) -> dict | None:
    if page.get("missing") or not page.get("imageinfo"):
        return None
    ii = page["imageinfo"][0]
    meta = ii.get("extmetadata", {})

    def m(key):
        return _strip_html(meta.get(key, {}).get("value", ""))

    return {
        "title": page["title"],
        "width": ii.get("width", 0),
        "height": ii.get("height", 0),
        "mime": ii.get("mime", ""),
        # Orijinal genişlik DOWNLOAD_WIDTH'ten küçükse thumburl orijinali verir
        "url": ii.get("thumburl") or ii.get("url"),
        "original_url": ii.get("url"),
        "page_url": ii.get("descriptionurl", ""),
        "license": m("LicenseShortName"),
        "license_url": m("LicenseUrl"),
        "artist": m("Artist") or "Bilinmiyor",
        "credit": m("Credit"),
    }


def file_infos(titles: list[str], session=None) -> dict:
    """Birden çok dosyanın bilgisini tek istekte (50'şerli) al. {başlık: bilgi | None}"""
    session = session or _session()
    titles = [normalize_title(t) for t in titles]
    out = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        data = _get(session, {
            "action": "query", "titles": "|".join(chunk), "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata", "iiurlwidth": DOWNLOAD_WIDTH,
        })
        query = data.get("query", {})
        # API başlıkları normalize edebilir (alt çizgi → boşluk)
        renamed = {n["to"]: n["from"] for n in query.get("normalized", [])}
        for page in query.get("pages", []):
            original = renamed.get(page.get("title"), page.get("title"))
            out[original] = _parse_page(page)
    for t in titles:
        out.setdefault(t, None)
    return out


def file_info(title: str, session=None) -> dict:
    """Commons dosyasının URL, boyut ve lisans bilgisini döndür."""
    title = normalize_title(title)
    info = file_infos([title], session=session).get(title)
    if not info:
        raise ArchiveError(f"Dosya bulunamadı: {title}")
    return info


def check_usable(info: dict, min_width: int = MIN_WIDTH) -> list[str]:
    """Görselin belgeselde kullanılmasına engel durumları listele (boşsa uygun)."""
    problems = []
    if not license_allowed(info.get("license", "")):
        problems.append(f"lisans uygun değil: {info.get('license') or 'yok'}")
    is_vector = "svg" in str(info.get("mime", ""))  # SVG istenen genişlikte rasterleştirilir
    if not is_vector and max(info.get("width", 0), info.get("height", 0)) < min_width:
        problems.append(f"çözünürlük düşük: {info.get('width')}x{info.get('height')}")
    if not str(info.get("mime", "")).startswith("image/"):
        problems.append(f"görsel değil: {info.get('mime')}")
    return problems


def search_commons(query: str, limit: int = 20, session=None) -> list[str]:
    """Commons dosya ad alanında arama yap, dosya başlıklarını döndür."""
    session = session or _session()
    data = _get(session, {
        "action": "query", "list": "search", "srsearch": query,
        "srnamespace": 6, "srlimit": limit,
    })
    return [hit["title"] for hit in data.get("query", {}).get("search", [])]


def download(info: dict, dest: Path, session=None) -> Path:
    """Görseli indir (zaten varsa tekrar indirme)."""
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > 10_000:
        return dest
    session = session or _session()
    dest.parent.mkdir(parents=True, exist_ok=True)
    response = _request(session, info["url"], timeout=180)
    dest.write_bytes(response.content)
    return dest


def fetch_images(images: dict, out_dir: Path, min_width: int = MIN_WIDTH) -> dict:
    """
    Senaryodaki görsel tablosunu indir.

    Args:
        images: {anahtar: {"commons": "File:..."} | {"file": "yerel/yol.jpg", "credit": ...}}
        out_dir: indirme klasörü

    Returns:
        {anahtar: {"path": str, "credit": {...}}} — uygun olmayan görselde ArchiveError
    """
    out_dir = Path(out_dir)
    session = _session()
    result = {}
    credits_path = out_dir / "credits.json"
    infos = file_infos([s["commons"] for s in images.values() if s.get("commons")], session=session)
    for key, spec in images.items():
        if spec.get("file"):
            result[key] = {"path": str(spec["file"]), "credit": spec.get("credit", {})}
            continue
        info = infos.get(normalize_title(spec["commons"]))
        if not info:
            raise ArchiveError(f"{key}: dosya bulunamadı ({spec['commons']})")
        problems = check_usable(info, min_width=spec.get("min_width", min_width))
        if problems:
            raise ArchiveError(f"{key} ({info['title']}): " + "; ".join(problems))
        if spec.get("original"):
            # Kırpılacak büyük haritalar: küçültülmüş kopya yerine özgün dosya
            info = {**info, "url": info["original_url"]}
        ext = Path(info["url"].split("?")[0]).suffix.lower() or ".jpg"
        path = download(info, out_dir / f"{key}{ext}", session=session)
        result[key] = {"path": str(path), "credit": {
            k: info[k] for k in ("title", "artist", "license", "license_url", "page_url")
        }}
        logger.info("Arşiv görseli: %s ← %s (%s)", key, info["title"], info["license"])
    out_dir.mkdir(parents=True, exist_ok=True)
    credits_path.write_text(json.dumps({k: v["credit"] for k, v in result.items()},
                                       ensure_ascii=False, indent=2), encoding="utf-8")
    return result
