"""Çekim planı denetimi: tekrar sayıları ve donma riski (tahmini konuşma hızıyla).
python belgeseller/03-istanbul/araclar/kontrol.py [karakter/sn]"""
import json, re, subprocess, sys
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from cekimler import SHOTS, PEXELS
from haritalar import M

RATE = float(sys.argv[1]) if len(sys.argv) > 1 else 13.0
SAFE = 0.75                       # klip en fazla bu kadar yavaşlatılsın (render sınırı 0.6)
sen = json.load(open(HERE.parent / "senaryo.json", encoding="utf-8"))
clip_len = {}
def clip_dur(p):
    if p not in clip_len:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                              str(HERE.parent / p)], capture_output=True, text=True).stdout
        clip_len[p] = float(out)
    return clip_len[p]

uses, problems = Counter(), []
for ci, ch in enumerate(sen["chapters"]):
    for pi, para in enumerate(ch["paragraphs"]):
        key = f"{ci}.{pi}"
        shots = SHOTS[key]
        text = re.sub(r"\[[^\]]*\]", "", para["text"])
        dur = len(text) / RATE
        slot = dur / len(shots)
        for s in shots:
            if "clip" in s:
                uses["klip " + s["clip"]] += 1
                have = clip_dur(s["clip"])
            elif "stock" in s:
                uses["pexels " + s["stock"]] += 1
                have = PEXELS[int(s["stock"][1:])][0] - s.get("start", 0)
            elif "map" in s:
                uses["harita " + s["map"]] += 1
                have = M[s["map"]].get("durationSec", 12) / 0.6 * SAFE   # haritada son kare donması sorun değil
            else:
                uses["görsel " + s["image"]] += 1
                continue
            if have / slot < SAFE:
                problems.append(f"{key}: {list(s.values())[0]} {have:.1f} sn < yuva {slot:.1f} sn (oran {have/slot:.2f})")
lim = {"klip": 1, "pexels": 2, "görsel": 2, "harita": 2}
over = [f"{k} ×{n}" for k, n in uses.items() if n > lim[k.split()[0]]]
print(f"Hız {RATE} kr/sn · çekim: {sum(uses.values())} · donma riski: {len(problems)} · fazla tekrar: {len(over)}")
for p in problems: print("  DONMA", p)
for o in over: print("  TEKRAR", o)
