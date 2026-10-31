"""Belgesel hattı testleri: arşiv lisansı, ses metni, zaman çizelgesi, render."""

import subprocess
from pathlib import Path

import cv2
import numpy as np
import pytest

from scripts import archive_images as ai
from scripts import doc_audio as da
from scripts import doc_timeline as dt
from scripts import doc_render as dr


# ── Arşiv lisansları ─────────────────────────

@pytest.mark.parametrize("name,ok", [
    ("Public domain", True), ("CC0", True), ("CC BY 3.0", True), ("CC BY-SA 4.0", True),
    ("CC BY-SA 2.0", True), ("CC BY-NC 2.0", False), ("CC BY-ND 4.0", False),
    ("CC BY-NC-SA 3.0", False), ("Fair use", False), ("", False), ("All rights reserved", False),
])
def test_license_allowed(name, ok):
    assert ai.license_allowed(name) is ok


def test_check_usable_rejects_small_and_nc():
    good = {"license": "CC BY-SA 3.0", "width": 5184, "height": 3456, "mime": "image/jpeg"}
    assert ai.check_usable(good) == []
    assert ai.check_usable({**good, "width": 800, "height": 600})
    assert ai.check_usable({**good, "license": "CC BY-NC 2.0"})
    # SVG harita istenen genişlikte rasterleşir: piksel boyutu engel değil
    assert ai.check_usable({**good, "mime": "image/svg+xml", "width": 900, "height": 700}) == []


def test_normalize_title():
    assert ai.normalize_title("Lion Gate.jpg") == "File:Lion Gate.jpg"
    assert ai.normalize_title("File:X.jpg") == "File:X.jpg"


# ── Ses metni ve hizalama ────────────────────

def test_pronunciations_keep_suffix_and_longest_first():
    text = "Hattuşili, Hattuşa'nın kralıydı."
    out = da.apply_pronunciations(text, {"Hattuşa": "Hattu-şa", "Hattuşili": "Hattu-şili"})
    assert out == "Hattu-şili, Hattu-şa'nın kralıydı."
    assert len(out.split()) == len(text.split())


def test_pronunciation_must_be_single_word():
    with pytest.raises(ValueError):
        da.apply_pronunciations("Muvattali", {"Muvattali": "Mu vattali"})


def test_words_from_alignment_uses_display_text():
    spoken = "Hattu-şa yandı."
    chars = list(spoken)
    starts = [i * 0.1 for i in range(len(chars))]
    ends = [s + 0.1 for s in starts]
    words = da.words_from_alignment(
        {"characters": chars, "character_start_times_seconds": starts,
         "character_end_times_seconds": ends}, "Hattuşa yandı.")
    assert [w["word"] for w in words] == ["Hattuşa", "yandı."]
    assert words[1]["start"] == pytest.approx(0.9)


def test_sentence_starts():
    words = [{"word": w, "start": i, "end": i + 0.5} for i, w in
             enumerate("Bir şehir. İki kral! Üç savaş".split())]
    assert da.sentence_starts(words) == [0, 2, 4]


# ── Zaman çizelgesi ──────────────────────────

def _words(text, step=0.4):
    return [{"word": w, "start": round(i * step, 3), "end": round(i * step + 0.35, 3)}
            for i, w in enumerate(text.split())]


def test_cut_points_snap_to_sentence_and_respect_min_shot():
    text = ("Hattuşa bir dağ kentiydi. Surları kilometrelerce uzanıyordu. "
            "Kapılarında aslanlar bekliyordu. Kral burada hüküm sürdü.")
    words = _words(text, step=0.8)
    duration = words[-1]["end"]
    cuts = dt._cut_points(words, 3, duration)
    sentence_times = [words[i]["start"] for i in da.sentence_starts(words)]
    assert len(cuts) == 2
    for c in cuts:
        assert any(abs(c - (s - dt.CUT_LEAD)) < 1e-6 for s in sentence_times)
    bounds = [0] + cuts + [duration]
    assert all(b - a >= dt.MIN_SHOT - 1e-6 for a, b in zip(bounds, bounds[1:]))
    # Sığmayan çekim istenirse en az süre korunur, çekim sayısı azalır
    short = _words(text, step=0.2)
    assert len(dt._cut_points(short, 3, short[-1]["end"])) < 2


def test_chapter_shots_total_matches_layout(tmp_path):
    chapter = {"title": "Giriş", "paragraphs": [
        {"text": "a", "shots": [{"image": "x"}, {"image": "y", "move": "left"}]},
        {"text": "b", "shots": [{"image": "y", "label": {"title": "Hattuşa"}}]},
    ]}
    audio = [{"duration": 9.0, "words": _words("Bir. İki üç dört. Beş altı yedi. Sekiz", 1.0)},
             {"duration": 5.0, "words": _words("Dokuz on", 1.0)}]
    layout = dt.layout_chapter(chapter, [a["duration"] for a in audio])
    shots = dt.chapter_shots(chapter, audio, layout, {"x": "x.jpg", "y": "y.jpg"}, tmp_path)
    assert sum(s["duration"] for s in shots) == pytest.approx(layout.total)
    assert [s["path"] for s in shots] == ["x.jpg", "y.jpg", "y.jpg"]
    assert shots[2]["label"] == {"title": "Hattuşa"}


def test_card_chapter_starts_with_card(tmp_path):
    chapter = {"title": "Bölüm", "card": {"kicker": "BÖLÜM I"},
               "paragraphs": [{"text": "a", "shots": [{"image": "x"}]}]}
    audio = [{"duration": 6.0, "words": _words("Bir iki", 1.0)}]
    layout = dt.layout_chapter(chapter, [6.0])
    assert layout.lead == dt.CARD_SECONDS
    shots = dt.chapter_shots(chapter, audio, layout, {"x": "x.jpg"}, tmp_path, card_clip="kart.mp4")
    assert shots[0]["path"] == "kart.mp4" and shots[0]["duration"] == dt.CARD_SECONDS
    assert sum(s["duration"] for s in shots) == pytest.approx(layout.total)


def test_validate_reports_missing_refs(tmp_path):
    data = {"slug": "x", "title": "t", "images": {"a": {}}, "chapters": [
        {"title": "c", "paragraphs": [{"text": "t", "shots": [{"image": "yok"}, {"clip": "k.mp4"}]}]}]}
    problems = dt.validate(data, tmp_path)
    assert any("yok" in p for p in problems)
    assert any("k.mp4" in p for p in problems)


def test_youtube_chapters_format_and_rules():
    text = dt.youtube_chapters(["Giriş", "Kuruluş", "Kadeş"], [0, 95.4, 3725])
    assert text.splitlines() == ["0:00 Giriş", "1:35 Kuruluş", "1:02:05 Kadeş"]
    with pytest.raises(dt.ScenarioError):
        dt.youtube_chapters(["a", "b"], [0, 20])
    with pytest.raises(dt.ScenarioError):
        dt.youtube_chapters(["a", "b", "c"], [0, 5, 30])


def test_srt_cues_split_on_sentences(tmp_path):
    cues = dt.subtitle_cues(_words("Hattuşa yandı. Krallık dağıldı."), offset=10.0)
    assert [c[2] for c in cues] == ["Hattuşa yandı.", "Krallık dağıldı."]
    assert cues[0][0] == pytest.approx(10.0)
    srt = dt.write_srt(cues, tmp_path / "a.srt").read_text(encoding="utf-8")
    assert srt.startswith("1\n00:00:10,000 --> ")


# ── Render ───────────────────────────────────

@pytest.fixture
def photo(tmp_path):
    rng = np.random.default_rng(1)
    img = cv2.GaussianBlur(rng.integers(0, 255, (900, 1600, 3), dtype=np.uint8), (0, 0), 3)
    path = tmp_path / "foto.jpg"
    cv2.imwrite(str(path), img)
    return str(path)


def test_pan_moves_smoothly_even_near_edge(photo):
    """Kenara yakın odakta da kaydırma olmalı ve kare başı kayma sabit kalmalı."""
    src = dr.ImageSource(dr.Shot("image", photo, 3, move="right", focus=(0.1, 0.5)), 3, {})
    gray = [np.float32(cv2.cvtColor(src.frame(t / 30), cv2.COLOR_BGR2GRAY)[600:900, 1100:1500])
            for t in range(20)]
    shifts = np.array([cv2.phaseCorrelate(a, b)[0][0] for a, b in zip(gray, gray[1:])])
    assert abs(shifts.mean()) > 0.5
    assert shifts.std() < 0.05


def test_portrait_image_uses_contain(tmp_path):
    img = np.full((1800, 900, 3), 200, np.uint8)
    path = tmp_path / "dikey.jpg"
    cv2.imwrite(str(path), img)
    canvas = dr.build_canvas(str(path))
    assert canvas.shape[:2] == (int(dr.OUT_H * dr.CANVAS_SCALE), int(dr.OUT_W * dr.CANVAS_SCALE))
    # Kenarlar karartılmış bulanık arka plan, orta görselin kendisi
    assert canvas[:, :50].mean() < canvas[:, canvas.shape[1] // 2].mean()


def test_render_chapter_duration(photo, tmp_path):
    out = tmp_path / "bolum.mp4"
    shots = [dr.Shot("image", photo, 1.0, move="in", label={"title": "Hattuşa", "subtitle": "MÖ 1650"}),
             dr.Shot("image", photo, 1.0, move="left", transition="cut")]
    dr.OUT_W, dr.OUT_H = 640, 360   # testte küçük çözünürlük
    try:
        dr.render_chapter(shots, str(out), look=dr.Look(640, 360))
    finally:
        dr.OUT_W, dr.OUT_H = 2560, 1440
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(out)], capture_output=True, text=True)
    assert float(probe.stdout) == pytest.approx(2.0, abs=0.05)


def test_label_stays_readable_in_short_shot():
    """4 sn'lik çekimde etiket en az ~2 sn tam görünür olmalı."""
    visible = [t / 30 for t in range(120) if dr._envelope(t / 30, 4.0) >= 0.999]
    assert visible and visible[-1] - visible[0] >= 2.0


# ── Üretim hattı ve yükleme ──────────────────

def _mini_production(tmp_path, n_images=3):
    import json
    images = {f"g{i}": {"file": f"g{i}.jpg"} for i in range(n_images)}
    data = {"slug": "t", "title": "Deneme", "description": "Giriş metni.", "images": images,
            "sources": ["Bryce, T. The Kingdom of the Hittites (2005)"],
            "chapters": [{"title": "Giriş", "paragraphs": [{"text": "a", "shots": [{"image": "g0"}]}]}]}
    (tmp_path / "senaryo.json").write_text(json.dumps(data), encoding="utf-8")
    from scripts.doc_pipeline import Production
    prod = Production(str(tmp_path))
    credit = {"title": "File:" + "Uzun bir eser adı " * 6 + ".jpg", "artist": "Fotoğrafçı",
              "license": "CC BY-SA 4.0"}
    manifest = {k: {"path": f"images/{k}.jpg",
                    "credit": credit | {"title": credit["title"].replace("File:", f"File:{k} ")}}
                for k in images}
    prod.path("images", "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return prod


def test_description_has_sections_and_fits_limit(tmp_path):
    prod = _mini_production(tmp_path, n_images=80)
    text = prod.description("0:00 Giriş\n1:00 Kuruluş\n5:00 Son")
    assert len(text) <= 5000
    assert "📍 Bölümler\n0:00 Giriş" in text
    assert "📚 Kaynaklar" in text and "Bryce" in text
    assert "tam liste sabit yorumda" in text      # sığmayan lisanslar kesildi


def test_sample_mode_limits_chapters(tmp_path):
    prod = _mini_production(tmp_path)
    from scripts.doc_pipeline import Production
    sample = Production(str(tmp_path), sample=1)
    assert sample.final_name == "ornek.mp4" and len(sample.data["chapters"]) == 1
    assert sample._manifest_name() == "manifest-ornek.json"
    assert prod._manifest_name() == "manifest.json"


def test_upload_documentary_body(monkeypatch, tmp_path):
    from scripts import youtube_uploader as yu
    video = tmp_path / "v.mp4"
    video.write_bytes(b"0" * 1024)
    captured = {}

    class Req:
        def next_chunk(self):
            return None, {"id": "abc123"}

    class Videos:
        def insert(self, part, body, media_body):
            captured["body"] = body
            return Req()

    class YT:
        def videos(self):
            return Videos()

    monkeypatch.setattr(yu, "authenticate", lambda: object())
    monkeypatch.setattr(yu, "build", lambda *a, **k: YT())
    monkeypatch.setattr(yu, "MediaFileUpload", lambda *a, **k: None)
    monkeypatch.setattr(yu, "record_upload", lambda *a, **k: None)
    from datetime import datetime, timezone
    when = datetime(2026, 11, 4, 16, 0, tzinfo=timezone.utc)
    vid = yu.upload_documentary(str(video), "Hititler", "açıklama", ["tarih"],
                                publish_at=when, synthetic_media=True)
    assert vid == "abc123"
    body = captured["body"]
    assert body["status"]["privacyStatus"] == "private"
    assert body["status"]["publishAt"] == when.isoformat()
    assert body["status"]["containsSyntheticMedia"] is True
    assert body["snippet"]["defaultLanguage"] == "tr"
    assert body["snippet"]["defaultAudioLanguage"] == "tr"
    assert body["snippet"]["categoryId"] == "27"
