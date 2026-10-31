"""
doc_music.py - Belgesel fon müziği adaylarını ölçerek sıralama.

Müziği "kulakla" seçemediğimiz durumda (ör. bulut ortamı), Commons'taki CC
lisanslı parçalar indirilir ve her biri için nesnel ölçüler hesaplanır:

- onset_rate   : saniyedeki vuruş/atak sayısı (ritim, hareketlilik)   → düşük = sakin
- flux         : tınının kareden kareye değişimi (kıpırtı)            → düşük = sakin
- centroid_hz  : tınının parlaklığı                                   → düşük = derin, koyu
- low_ratio    : 300 Hz altındaki enerji payı                         → yüksek = derin
- dyn_db       : ses yüksekliği dalgalanması (dB std)                 → düşük = düzgün alt iz

calm_score bu ölçülerin z-puanlarından hesaplanır; küçük puan = belgesel
altına uygun (TRT/Discovery tarzı sakin, derin, ritimsiz) parça.
"""

import json
import subprocess
from pathlib import Path

import numpy as np

from scripts.utils import logger

SR = 22050
MIN_SECONDS = 90          # bölüm altında döngü az olsun diye kısa parçalar elenir


def _decode(path: Path, offset: float = 0.0, seconds: float = 240.0) -> np.ndarray:
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(offset), "-t", str(seconds), "-i", str(path),
         "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True)
    return np.frombuffer(out.stdout, np.float32)


def _duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def analyze_signal(y: np.ndarray, sr: int = SR) -> dict:
    """Mono sinyalden sakinlik ölçüleri."""
    n, hop = 2048, 1024
    if len(y) < n * 4:
        return {}
    frames = np.lib.stride_tricks.sliding_window_view(y, n)[::hop] * np.hanning(n)
    mag = np.abs(np.fft.rfft(frames, axis=1))
    freqs = np.fft.rfftfreq(n, 1 / sr)
    energy = mag.sum(axis=1)
    loud = energy > max(energy.max() * 1e-3, 1e-6)
    if loud.sum() < 8:
        return {}
    m = mag[loud]
    centroid = float(np.mean((m * freqs).sum(axis=1) / m.sum(axis=1)))
    power = m ** 2
    low_ratio = float(power[:, freqs < 300].sum() / power.sum())
    diff = np.maximum(m[1:] - m[:-1], 0).sum(axis=1) / (m[:-1].sum(axis=1) + 1e-9)
    flux = float(np.mean(diff))
    med = np.median(diff)
    mad = np.median(np.abs(diff - med)) + 1e-9
    peaks = (diff[1:-1] > med + 4 * mad) & (diff[1:-1] > diff[:-2]) & (diff[1:-1] >= diff[2:])
    seconds = len(diff) * hop / sr
    rms_db = 20 * np.log10(np.sqrt(np.mean(frames[loud] ** 2, axis=1)) + 1e-9)
    return {"onset_rate": round(float(peaks.sum() / seconds), 3), "flux": round(flux, 4),
            "centroid_hz": round(centroid, 1), "low_ratio": round(low_ratio, 4),
            "dyn_db": round(float(np.std(rms_db)), 2)}


def analyze_file(path: Path) -> dict:
    dur = _duration(path)
    # Girişi (sessiz açılış) atla: parçanın gövdesi ölçülür
    y = _decode(path, offset=min(15.0, dur * 0.1))
    return {"duration": round(dur, 1), **analyze_signal(y)}


def rank(tracks: list[dict]) -> list[dict]:
    """calm_score ekleyip sakinden hareketliye sırala."""
    usable = [t for t in tracks if "onset_rate" in t and t.get("duration", 0) >= MIN_SECONDS]
    if not usable:
        return []

    def z(key):
        v = np.array([t[key] for t in usable], float)
        return (v - v.mean()) / (v.std() + 1e-9)

    score = z("onset_rate") + z("flux") + 0.7 * z("centroid_hz") - 0.4 * z("low_ratio") + 0.3 * z("dyn_db")
    for t, s in zip(usable, score):
        t["calm_score"] = round(float(s), 3)
    return sorted(usable, key=lambda t: t["calm_score"])


def review(queries: list[str], work_dir: Path, limit: int = 200) -> list[dict]:
    """Commons'ta ara, lisansı uygun ses dosyalarını indir, ölç ve sırala."""
    from scripts.archive_images import (_session, download_stream, file_infos,
                                        license_allowed, search_commons)
    session = _session()
    titles = []
    for q in queries:
        titles += search_commons(f"{q} filetype:audio", limit=limit, session=session)
    titles = list(dict.fromkeys(titles))
    infos = file_infos(titles, session=session)
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    tracks = []
    for i, (title, info) in enumerate(infos.items()):
        if not info or not license_allowed(info.get("license", "")):
            continue
        if not str(info.get("mime", "")).startswith(("audio/", "application/ogg")):
            continue
        ext = Path(info["original_url"].split("?")[0]).suffix.lower() or ".ogg"
        dest = work_dir / f"aday{i:03d}{ext}"
        try:
            download_stream(info["original_url"], dest, session=session)
            metrics = analyze_file(dest)
        except Exception as e:      # tek bozuk dosya incelemeyi durdurmasın
            logger.warning("Müzik adayı atlandı (%s): %s", title, e)
            continue
        finally:
            dest.unlink(missing_ok=True)
        tracks.append({"commons": title, "license": info.get("license"),
                       "artist": info.get("artist"), **metrics})
        logger.info("Müzik ölçüldü: %s %s", title, metrics)
    return rank(tracks)


def write_report(ranked: list[dict], path: Path) -> Path:
    path = Path(path)
    path.write_text(json.dumps(ranked, ensure_ascii=False, indent=1), encoding="utf-8")
    return path
