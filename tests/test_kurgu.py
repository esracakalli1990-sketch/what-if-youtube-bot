"""Sinematik kurgu v3: geçiş türleri, ayna, ton eşitleme, L-kesme ses, kurgu denetimi."""
import json
import subprocess
from pathlib import Path

import numpy as np

from scripts import doc_audio as da
from scripts import doc_kurgu as dk
from scripts import doc_render as dr
from scripts import doc_timeline as dt


def _clip(path: Path, color: str = "gray", d: float = 3.0, size: str = "320x180", audio: bool = False,
          src: str | None = None) -> Path:
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", src or f"color=c={color}:s={size}:d={d}:r=30"]
    if audio:
        cmd += ["-f", "lavfi", "-i", f"sine=f=440:d={d}", "-shortest", "-c:a", "aac"]
    subprocess.run(cmd + ["-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)], check=True)
    return path


def _frames(path: Path) -> np.ndarray:
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", "scale=64:36,format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(out, np.uint8).reshape(-1, 36, 64).astype(float).mean(axis=(1, 2))


def _render(tmp_path, shots, name="out.mp4"):
    look = dr.Look(grain=0.0, vignette=0.0)
    out = tmp_path / name
    dr.render_chapter(shots, str(out), look=look, fade_in=0, fade_out=0, preset="ultrafast")
    return _frames(out)


def test_black_transition_dips_to_black(tmp_path):
    a, b = _clip(tmp_path / "a.mp4", "white"), _clip(tmp_path / "b.mp4", "white")
    lum = _render(tmp_path, [dr.Shot("video", str(a), 2.0, grade=False),
                             dr.Shot("video", str(b), 2.0, grade=False, transition="black", xfade=1.0)])
    assert len(lum) == 120
    assert lum[60] < 20 and lum[10] > 200 and lum[110] > 200      # sınırda siyah, iki yanda beyaz


def test_flash_transition_brightens_after_cut(tmp_path):
    a, b = _clip(tmp_path / "a.mp4", "black"), _clip(tmp_path / "b.mp4", "black")
    lum = _render(tmp_path, [dr.Shot("video", str(a), 1.0, grade=False),
                             dr.Shot("video", str(b), 1.0, grade=False, transition="flash")])
    assert lum[29] < 20 and lum[30] > 150 and lum[50] < 30        # kesmede parlama, sonra söner


def test_cut_has_no_blend(tmp_path):
    a, b = _clip(tmp_path / "a.mp4", "black"), _clip(tmp_path / "b.mp4", "white")
    lum = _render(tmp_path, [dr.Shot("video", str(a), 1.0, grade=False),
                             dr.Shot("video", str(b), 1.0, grade=False, transition="cut")])
    assert lum[29] < 20 and lum[30] > 200


def test_flip_mirrors_clip(tmp_path):
    # Sol yarı siyah, sağ yarı beyaz klip; aynalanınca sol beyaz olmalı
    src = "color=c=black:s=320x180:d=1:r=30[a];color=c=white:s=160x180:d=1:r=30[b];[a][b]overlay=160:0"
    clip = tmp_path / "c.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-filter_complex", src, "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", str(clip)], check=True)
    src_ = dr.VideoSource(dr.Shot("video", str(clip), 1.0, flip=True, grade=False), span=1.0)
    f = src_.frame(0.5)
    src_.close()
    assert f[:, :dr.OUT_W // 4].mean() > 200 and f[:, -dr.OUT_W // 4:].mean() < 40


def test_tone_params_pull_dark_clip_toward_target(tmp_path):
    dark = _clip(tmp_path / "d.mp4", "0x202020")
    gain, beta = dr.tone_params(str(dark), strength=0.5)
    new = 0x20 * gain + beta
    assert 0x20 < new < dr.TONE_TARGET[0]                          # aydınlanır ama hedefe tam gitmez
    assert dr.tone_params(str(dark), strength=0.0) == (1.0, 0.0)


def test_requested_speed_and_auto_slowdown(tmp_path):
    clip = _clip(tmp_path / "c.mp4", d=4.0)
    assert dr.effective_speed(str(clip), 0.0, 3.0, 0.8) == 0.8     # istenen ağır çekim
    assert abs(dr.effective_speed(str(clip), 0.0, 6.0) - 4 / 6) < 0.01
    assert dr.effective_speed(str(clip), 0.0, 20.0) == 0.6          # alt sınır


def test_sfx_events_overlap_and_speed(tmp_path):
    clip = _clip(tmp_path / "c.mp4", d=4.0, audio=True)
    shots = [{"path": "x", "duration": 2.0},
             {"path": str(clip), "duration": 3.0, "sfx": True, "speed": 0.8}]
    (ev,) = da.shot_sfx_events(shots, t0=10.0)
    assert ev[2] == 12.0 and ev[3] == 3.0 + da.SFX_OVERLAP and ev[4] == 0.8
    seg = da.decode_span(str(clip), 0.0, 2.0, speed=0.8)
    assert abs(len(seg) / da.SR - 2.0) < 0.1                        # yavaşlatılmış ses yine 2 sn
    bed = da.sfx_bed([ev], total=20.0)
    assert np.abs(bed[int(15.3 * da.SR):int(15.5 * da.SR)]).max() > 0   # kesmeden sonra da sürer (L-kesme)


def test_timeline_passes_clip_options_and_defaults(tmp_path):
    _clip(tmp_path / "k.mp4")
    words = [{"word": "Bir.", "start": 0.0, "end": 0.5}, {"word": "İki.", "start": 3.0, "end": 3.5}]
    ch = {"title": "T", "paragraphs": [{"text": "Bir. İki.", "shots": [
        {"clip": "k.mp4", "start": 1.0, "flip": True, "speed": 0.8},
        {"clip": "k.mp4", "transition": "flash"}]}]}
    lay = dt.layout_chapter(ch, [6.0])
    shots = dt.chapter_shots(ch, [{"words": words, "duration": 6.0}], lay, {}, tmp_path,
                             kurgu={"gecis": "cut", "ton_esitle": 0.4})
    assert shots[0]["start"] == 1.0 and shots[0]["flip"] and shots[0]["speed"] == 0.8
    assert shots[0]["transition"] == "cut" and shots[0]["match"] == 0.4
    assert shots[1]["transition"] == "flash"
    dr.Shot(**shots[0])                                              # Shot alanlarıyla uyumlu


def test_validate_rejects_unknown_transition():
    data = {"slug": "s", "title": "t", "images": {"x": {}}, "kurgu": {"gecis": "wipe"},
            "chapters": [{"title": "c", "paragraphs": [{"text": "a", "shots": [{"image": "x", "transition": "zoom"}]}]}]}
    problems = dt.validate(data)
    assert any("kurgu.gecis" in p for p in problems) and any("geçiş" in p for p in problems)


def test_kurgu_check_and_strip(tmp_path):
    _clip(tmp_path / "a.mp4", "red", d=3.0)
    _clip(tmp_path / "b.mp4", "blue", d=12.0)
    text = "x" * 140                                                # 14 kr/sn → 10 sn paragraf
    data = {"slug": "s", "title": "t", "images": {"g": {}}, "chapters": [{"title": "c", "paragraphs": [
        {"text": text, "shots": [{"clip": "a.mp4"}, {"clip": "b.mp4", "transition": "cut"}]},
        {"text": text, "shots": [{"clip": "b.mp4"}]},
        {"text": "y" * 300, "shots": [{"image": "g"}]}]}]}
    (tmp_path / "senaryo.json").write_text(json.dumps(data), encoding="utf-8")
    problems = dk.check(tmp_path)
    assert any(p.startswith("DONMA 0.0.0") for p in problems)       # 3 sn klip, 5 sn yuva
    assert "TEKRAR b.mp4 ×2" in problems
    assert any(p.startswith("UZUN 0.2.0") for p in problems)
    sheets = dk.strip(tmp_path, tmp_path / "serit")
    assert len(sheets) == 1 and sheets[0].exists()
