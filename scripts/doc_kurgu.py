"""
doc_kurgu.py - Render'dan önce kurgu denetimi ve "geçiş şeridi".

Ses henüz üretilmemişken çekim sürelerini metin uzunluğundan tahmin eder
(karakter/saniye) ve şunları yakalar:
  - DONMA   klip, yuvasını dolduramıyor (en fazla %25 yavaşlatma güvenli)
  - TEKRAR  aynı klip birden fazla kez kullanılmış
  - KISA    2 sn'den kısa çekim (göz okuyamaz, kurgu "titrer")
  - UZUN    9 sn'den uzun durağan görsel (slayt hissi)
  - GEÇİŞ   tanımsız geçiş türü

Geçiş şeridi: art arda gelen iki klibin sınırında A'nın son karesi ile B'nin
ilk karesini yan yana koyar. Kesmenin "bağlayıp bağlamadığı" (yön, ışık,
ölçek, hareket devamlılığı) gözle buradan denetlenir.

Kullanım:
  python -m scripts.doc_kurgu denetle belgeseller/04-yavuz [--hiz 14]
  python -m scripts.doc_kurgu serit belgeseller/04-yavuz [--hiz 14] [--cikti klasör]
"""

import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from scripts.doc_render import probe_duration
from scripts.doc_timeline import TRANSITIONS

SAFE_SPEED = 0.75
MIN_SHOT, MAX_STILL = 2.0, 9.0


def _clean(text: str) -> str:
    return re.sub(r"\[[^\]]*\]|<[^>]*>", "", text)


def estimate_shots(data: dict, rate: float = 14.0) -> list[dict]:
    """Her çekim için tahmini yuva: bölüm, paragraf, sıra, süre ve çekim tanımı."""
    out = []
    for ci, ch in enumerate(data["chapters"]):
        for pi, para in enumerate(ch["paragraphs"]):
            dur = max(len(_clean(para["text"])) / rate, 1.0)
            shots = para["shots"]
            for si, spec in enumerate(shots):   # kesmeler paragrafı yaklaşık eşit böler
                out.append({"yer": f"{ci}.{pi}.{si}", "sure": dur / len(shots), "spec": spec})
    return out


def _name(spec: dict) -> str:
    for k in ("clip", "map", "stock", "film", "image"):
        if k in spec:
            return f"{k}:{Path(str(spec[k])).stem}"
    return "?"


def check(folder: Path, rate: float = 14.0) -> list[str]:
    folder = Path(folder)
    data = json.loads((folder / "senaryo.json").read_text(encoding="utf-8"))
    problems, uses = [], Counter()
    for s in estimate_shots(data, rate):
        spec, slot, yer = s["spec"], s["sure"], s["yer"]
        tr = spec.get("transition", data.get("kurgu", {}).get("gecis", "dissolve"))
        if tr not in TRANSITIONS:
            problems.append(f"GEÇİŞ {yer}: '{tr}'")
        if slot < MIN_SHOT:
            problems.append(f"KISA {yer}: {_name(spec)} {slot:.1f} sn")
        if "image" in spec and slot > MAX_STILL:
            problems.append(f"UZUN {yer}: {_name(spec)} {slot:.1f} sn durağan görsel")
        if "clip" in spec:
            uses[spec["clip"]] += 1
            path = folder / spec["clip"]
            if not path.exists():
                problems.append(f"EKSİK {yer}: {spec['clip']}")
                continue
            have = probe_duration(str(path)) - spec.get("start", 0.0)
            need = slot * (spec.get("speed") or 1.0)
            if have / need < SAFE_SPEED:
                problems.append(f"DONMA {yer}: {spec['clip']} {have:.1f} sn < gereken {need:.1f} sn")
    problems += [f"TEKRAR {k} ×{n}" for k, n in uses.items() if n > 1]
    return problems


def _frame(path: Path, t: float, flip: bool, w: int = 480) -> np.ndarray:
    vf = f"scale={w}:-2" + (",hflip" if flip else "")
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(t, 0):.3f}", "-i", str(path),
                          "-frames:v", "1", "-vf", vf, "-f", "image2pipe", "-vcodec", "png", "-"],
                         capture_output=True)
    img = cv2.imdecode(np.frombuffer(out.stdout, np.uint8), cv2.IMREAD_COLOR) if out.stdout else None
    return img if img is not None else np.full((w * 9 // 16, w, 3), 40, np.uint8)


def strip(folder: Path, out_dir: Path, rate: float = 14.0, per_sheet: int = 6) -> list[Path]:
    """Ardışık klip çiftlerinin sınır karelerini sayfalara diz (A sonu | B başı)."""
    folder = Path(folder)
    data = json.loads((folder / "senaryo.json").read_text(encoding="utf-8"))
    shots = estimate_shots(data, rate)
    rows = []
    for a, b in zip(shots, shots[1:]):
        if "clip" not in a["spec"] or "clip" not in b["spec"]:
            continue
        pa, pb = folder / a["spec"]["clip"], folder / b["spec"]["clip"]
        if not (pa.exists() and pb.exists()):
            continue
        sa = a["spec"].get("speed") or 1.0
        end_a = min(a["spec"].get("start", 0.0) + a["sure"] * sa, probe_duration(str(pa)) - 0.1)
        fa = _frame(pa, end_a, a["spec"].get("flip", False))
        fb = _frame(pb, b["spec"].get("start", 0.0), b["spec"].get("flip", False))
        tr = b["spec"].get("transition", data.get("kurgu", {}).get("gecis", "dissolve"))
        h = min(fa.shape[0], fb.shape[0])
        row = np.hstack([fa[:h], np.full((h, 12, 3), 255, np.uint8), fb[:h]])
        bar = np.full((34, row.shape[1], 3), 20, np.uint8)
        cv2.putText(bar, f"{b['yer']}  {pa.stem} -> {pb.stem}  [{tr}]", (8, 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        rows.append(np.vstack([bar, row]))
    out_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for k in range(0, len(rows), per_sheet):
        group = rows[k:k + per_sheet]
        w = max(r.shape[1] for r in group)
        group = [np.pad(r, ((0, 6), (0, w - r.shape[1]), (0, 0))) for r in group]
        f = out_dir / f"serit_{k // per_sheet + 1:02d}.jpg"
        cv2.imwrite(str(f), np.vstack(group), [cv2.IMWRITE_JPEG_QUALITY, 85])
        files.append(f)
    return files


def main():
    ap = argparse.ArgumentParser(description="Kurgu denetimi ve geçiş şeridi")
    ap.add_argument("komut", choices=["denetle", "serit"])
    ap.add_argument("klasor")
    ap.add_argument("--hiz", type=float, default=14.0, help="anlatım hızı (karakter/sn)")
    ap.add_argument("--cikti", default="")
    a = ap.parse_args()
    folder = Path(a.klasor)
    if a.komut == "denetle":
        problems = check(folder, a.hiz)
        print(f"{len(problems)} sorun")
        for p in problems:
            print("  " + p)
        raise SystemExit(1 if any(p.startswith(("DONMA", "TEKRAR", "EKSİK", "GEÇİŞ")) for p in problems) else 0)
    for f in strip(folder, Path(a.cikti or folder / "build" / "serit"), a.hiz):
        print(f)


if __name__ == "__main__":
    main()
