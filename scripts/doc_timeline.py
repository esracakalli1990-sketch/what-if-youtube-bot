"""
doc_timeline.py - Belgesel senaryosu → zaman çizelgesi.

Senaryo (belgeseller/<slug>/senaryo.json) bölüm → paragraf → çekim yapısındadır.
Bu modül ses süreleri ve kelime zaman damgalarıyla:
- bölüm içi ses yerleşimini (kart, paragraf aralıkları, kuyruk),
- çekim sürelerini (kesmeler cümle başlarına, yoksa kelime başlarına oturur),
- Türkçe altyazıyı (.srt) ve YouTube bölüm listesini ("0:00 Giriş")
hesaplar. Render (doc_render) ve ses (doc_audio) bu çıktıyı kullanır.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from scripts.doc_audio import sentence_starts

CARD_SECONDS = 5.0      # bölüm kartı = Remotion ChapterCard süresi (150 kare)
LEAD_SECONDS = 0.6      # kartsız bölümde anlatım öncesi
PARAGRAPH_GAP = 0.65    # paragraflar arası nefes
TAIL_SECONDS = 1.4      # bölüm sonu (siyaha geçiş + müzik)
MIN_SHOT = 2.2          # bundan kısa çekim göz yorar
CUT_LEAD = 0.12         # kesme, kelimeden hemen önce


SHOT_SOURCES = ("image", "clip", "map", "stock", "film")


class ScenarioError(Exception):
    pass


def load_scenario(folder: Path) -> dict:
    folder = Path(folder)
    data = json.loads((folder / "senaryo.json").read_text(encoding="utf-8"))
    problems = validate(data, folder)
    if problems:
        raise ScenarioError("Senaryo hataları:\n- " + "\n- ".join(problems))
    return data


def validate(data: dict, folder: Path | None = None) -> list[str]:
    """Render'a girmeden önce yakalanabilecek senaryo hataları."""
    problems = []
    for key in ("slug", "title", "chapters", "images"):
        if not data.get(key):
            problems.append(f"'{key}' eksik")
    images = data.get("images", {})
    for name, m in data.get("maps", {}).items():
        if "bounds" in m:
            from scripts.doc_maps import check_bounds
            try:
                check_bounds(m["bounds"])
            except ValueError as e:
                problems.append(f"harita {name}: {e}")
            if m.get("taban", "dunya") == "dunya" and "dunya" not in images:
                problems.append(f"harita {name}: 'dunya' taban görseli images içinde yok "
                                f"(File:Whole world - land and oceans 12000.jpg, original: true)")
    for ci, ch in enumerate(data.get("chapters", [])):
        if not ch.get("title"):
            problems.append(f"bölüm {ci}: başlık yok")
        if ch.get("card") and ch["card"].get("image") and ch["card"]["image"] not in images:
            problems.append(f"bölüm {ci}: kart görseli tanımsız ({ch['card']['image']})")
        if not ch.get("paragraphs"):
            problems.append(f"bölüm {ci}: paragraf yok")
        for pi, para in enumerate(ch.get("paragraphs", [])):
            where = f"bölüm {ci} paragraf {pi}"
            if not para.get("text", "").strip():
                problems.append(f"{where}: metin boş")
            if not para.get("shots"):
                problems.append(f"{where}: çekim yok")
            for si, shot in enumerate(para.get("shots", [])):
                if "image" in shot and shot["image"] not in images:
                    problems.append(f"{where} çekim {si}: görsel tanımsız ({shot['image']})")
                if "clip" in shot and folder and not (Path(folder) / shot["clip"]).exists():
                    problems.append(f"{where} çekim {si}: klip yok ({shot['clip']})")
                if "map" in shot and shot["map"] not in data.get("maps", {}):
                    problems.append(f"{where} çekim {si}: harita tanımsız ({shot['map']})")
                if "stock" in shot and shot["stock"] not in data.get("stock", {}):
                    problems.append(f"{where} çekim {si}: stok video tanımsız ({shot['stock']})")
                if "film" in shot and shot["film"] not in data.get("films", {}):
                    problems.append(f"{where} çekim {si}: film tanımsız ({shot['film']})")
                if shot.get("overlay") and shot["overlay"] not in data.get("stock", {}):
                    problems.append(f"{where} çekim {si}: katman tanımsız ({shot['overlay']})")
                if "label" in shot and not (isinstance(shot["label"], dict) and shot["label"].get("title")):
                    problems.append(f"{where} çekim {si}: etiket {{\"title\", \"subtitle\"}} biçiminde olmalı")
                if not any(k in shot for k in SHOT_SOURCES):
                    problems.append(f"{where} çekim {si}: {'/'.join(SHOT_SOURCES)} biri gerekli")
    return problems


# ─────────────────────────────────────────────
# Ses yerleşimi
# ─────────────────────────────────────────────

@dataclass
class ChapterLayout:
    lead: float                  # ilk paragrafın başladığı an
    para_starts: list[float]     # bölüm içi paragraf başlangıçları
    total: float                 # bölüm süresi


def layout_chapter(chapter: dict, durations: list[float]) -> ChapterLayout:
    lead = CARD_SECONDS if chapter.get("card") else LEAD_SECONDS
    starts, t = [], lead
    for i, d in enumerate(durations):
        starts.append(round(t, 3))
        t += d + (PARAGRAPH_GAP if i < len(durations) - 1 else 0)
    return ChapterLayout(lead=lead, para_starts=starts, total=round(t + TAIL_SECONDS, 3))


# ─────────────────────────────────────────────
# Çekim süreleri
# ─────────────────────────────────────────────

def _cut_points(words: list[dict], n_shots: int, duration: float) -> list[float]:
    """
    Paragrafı n çekime böl: eşit bölme noktalarını en yakın cümle başına,
    yakında cümle başı yoksa en yakın kelime başına oturt (paragraf içi saniye).
    """
    if n_shots <= 1 or not words:
        return []
    sent = [words[i]["start"] for i in sentence_starts(words)][1:]
    word_starts = [w["start"] for w in words[1:]]
    seg = duration / n_shots
    cuts, prev = [], 0.0
    for j in range(1, n_shots):
        ideal = j * seg
        near_sent = [s for s in sent if abs(s - ideal) <= 0.4 * seg and s - prev >= MIN_SHOT]
        pool = near_sent or [s for s in word_starts if s - prev >= MIN_SHOT]
        if not pool:
            break
        best = min(pool, key=lambda s: abs(s - ideal))
        cut = max(prev + MIN_SHOT, best - CUT_LEAD)
        if duration - cut < MIN_SHOT:
            break
        cuts.append(round(cut, 3))
        prev = cut
    return cuts


def chapter_shots(chapter: dict, audio: list[dict], layout: ChapterLayout,
                  image_paths: dict, folder: Path, card_clip: str | None = None,
                  stock_paths: dict | None = None, film_paths: dict | None = None) -> list[dict]:
    """
    Bölümün çekim listesi (doc_render.Shot alanlarıyla sözlükler).
    Her paragrafın çekimleri bir sonraki paragrafın başına kadar sürer.
    stock_paths / film_paths: indirilmiş Pexels videoları ve uzun filmler.
    """
    stock_paths, film_paths = stock_paths or {}, film_paths or {}
    shots = []
    if chapter.get("card"):
        if not card_clip:
            raise ScenarioError(f"'{chapter['title']}' için bölüm kartı klibi yok")
        shots.append({"kind": "video", "path": card_clip, "duration": layout.lead,
                      "transition": "cut", "grade": False})
    n_para = len(chapter["paragraphs"])
    for pi, para in enumerate(chapter["paragraphs"]):
        start = layout.para_starts[pi] if (pi or shots) else 0.0
        end = layout.para_starts[pi + 1] if pi + 1 < n_para else layout.total
        span = end - start
        offset = layout.para_starts[pi] - start   # kartsız ilk paragrafta lead payı
        n = len(para["shots"])
        cuts = [c + offset for c in _cut_points(audio[pi]["words"], n, audio[pi]["duration"])]
        bounds = [0.0] + cuts + [span]
        specs = para["shots"][:len(bounds) - 1]
        for si, spec in enumerate(specs):
            dur = round(bounds[si + 1] - bounds[si], 3)
            shot = {
                "duration": dur,
                "move": spec.get("move", "in"),
                "focus": tuple(spec.get("focus", (0.5, 0.5))),
                "fit": spec.get("fit", "auto"),
                "transition": spec.get("transition", "dissolve"),
                "label": spec.get("label"),
                "note": spec.get("note", ""),
            }
            if "clip" in spec:
                shot.update(kind="video", path=str(Path(folder) / spec["clip"]),
                            note=spec.get("note", "Temsili canlandırma"),
                            sfx=spec.get("sfx", True))   # Gemini kliplerinin doğal sesi
            elif "map" in spec:
                # Remotion harita sahnesi; renk tonu bileşende uygulanmış durumda
                shot.update(kind="video", path=str(Path(folder) / "build" / "maps" / f"{spec['map']}.mp4"),
                            grade=False)
            elif "stock" in spec:
                shot.update(kind="video", path=stock_paths[spec["stock"]], start=spec.get("start", 0.0),
                            sfx=spec.get("sfx", False))
            elif "film" in spec:
                shot.update(kind="video", path=film_paths[spec["film"]], start=spec.get("start", 0.0),
                            sfx=spec.get("sfx", False))
            else:
                shot.update(kind="image", path=image_paths[spec["image"]])
            if spec.get("overlay"):
                shot.update(overlay=stock_paths[spec["overlay"]],
                            overlay_opacity=spec.get("overlay_opacity", 0.55))
            shots.append(shot)
    # Yuvarlama artıkları: toplam, bölüm süresine birebir eşit olsun
    drift = layout.total - sum(s["duration"] for s in shots)
    shots[-1]["duration"] = round(shots[-1]["duration"] + drift, 3)
    return shots


# ─────────────────────────────────────────────
# Altyazı ve YouTube bölümleri
# ─────────────────────────────────────────────

def _srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def subtitle_cues(words: list[dict], offset: float, max_chars: int = 84,
                  max_seconds: float = 6.0) -> list[tuple[float, float, str]]:
    """Kelimeleri okunur altyazı parçalarına böl (cümle sonunda yeni parça)."""
    cues, cur = [], []

    def flush():
        if cur:
            cues.append((offset + cur[0]["start"], offset + cur[-1]["end"],
                         " ".join(w["word"] for w in cur)))
            cur.clear()

    for w in words:
        text_len = len(" ".join(x["word"] for x in cur + [w]))
        if cur and (text_len > max_chars or w["end"] - cur[0]["start"] > max_seconds):
            flush()
        cur.append(w)
        if SENTENCE_BREAK(w["word"]):
            flush()
    flush()
    return cues


def SENTENCE_BREAK(word: str) -> bool:
    return word.rstrip("\"'”’)").endswith((".", "!", "?", "…"))


def _wrap(text: str, width: int = 42) -> str:
    """Altyazıyı en fazla iki dengeli satıra böl."""
    if len(text) <= width:
        return text
    words = text.split()
    best, best_diff = text, 1e9
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        diff = abs(len(a) - len(b))
        if diff < best_diff:
            best, best_diff = f"{a}\n{b}", diff
    return best


def write_srt(cues: list[tuple[float, float, str]], path: Path) -> Path:
    lines = []
    for i, (s, e, text) in enumerate(cues, 1):
        lines += [str(i), f"{_srt_time(s)} --> {_srt_time(e)}", _wrap(text), ""]
    Path(path).write_text("\n".join(lines), encoding="utf-8")
    return Path(path)


def youtube_chapters(titles: list[str], starts: list[float]) -> str:
    """YouTube bölüm listesi: 0:00 ile başlar, en az 3 bölüm, her biri ≥10 sn."""
    if len(titles) < 3:
        raise ScenarioError("YouTube bölümleri için en az 3 bölüm gerekir")
    if starts[0] != 0:
        raise ScenarioError("İlk bölüm 0:00'da başlamalı")
    for a, b in zip(starts, starts[1:]):
        if b - a < 10:
            raise ScenarioError("Her bölüm en az 10 saniye olmalı")

    def fmt(t: float) -> str:
        t = int(t)
        h, rem = divmod(t, 3600)
        m, s = divmod(rem, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    return "\n".join(f"{fmt(s)} {t}" for t, s in zip(titles, starts))
