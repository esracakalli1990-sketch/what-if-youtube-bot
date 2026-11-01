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


# ── Faz 1b: stok video, film kesiti, atmosfer katmanı ──

def test_pexels_best_file_prefers_landscape_near_1440p():
    from scripts import stock_video as sv
    video = {"id": 7, "duration": 12, "image": "p.jpg", "url": "u", "user": {"name": "Ayşe"},
             "video_files": [
                 {"file_type": "video/mp4", "width": 1280, "height": 720, "link": "a"},
                 {"file_type": "video/mp4", "width": 3840, "height": 2160, "link": "b"},
                 {"file_type": "video/mp4", "width": 2560, "height": 1440, "link": "c"},
                 {"file_type": "video/mp4", "width": 1080, "height": 1920, "link": "d"}]}
    assert sv.best_file(video)["link"] == "c"
    s = sv.summarize(video)
    assert s["id"] == 7 and s["author"] == "Ayşe" and s["link"] == "c"
    assert sv.best_file({"video_files": [{"file_type": "video/mp4", "width": 1280, "height": 720}]}) is None


def test_pexels_requires_key(monkeypatch):
    from scripts import stock_video as sv
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    with pytest.raises(sv.StockError):
        sv.search("dust")


def test_screen_blend_brightens_and_ignores_black():
    base = np.full((4, 4, 3), 100, np.uint8)
    black = np.zeros((4, 4, 3), np.uint8)
    white = np.full((4, 4, 3), 255, np.uint8)
    assert np.array_equal(dr.screen_blend(base, black, 0.8), base)
    out = dr.screen_blend(base, white, 0.5)
    assert (out > base).all() and (out < 255).all()


@pytest.fixture
def short_video(tmp_path):
    path = tmp_path / "klip.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                    "testsrc=size=320x180:rate=30:duration=4", str(path)], check=True)
    return str(path)


def test_video_source_start_and_slowdown(short_video):
    dr.OUT_W, dr.OUT_H = 320, 180
    try:
        # 4 sn'lik klip, 2. saniyeden başla, 3 sn'lik çekim: kalan 2 sn → yavaşlatılır
        src = dr.VideoSource(dr.Shot("video", short_video, 3.0, start=2.0), span=3.0)
        frames = [src.frame(t / 30) for t in range(0, 90, 10)]
        src.close()
        # Yavaşlatma sayesinde son kareler de hâlâ değişiyor (donmuyor)
        assert not np.array_equal(frames[-1], frames[-2])
    finally:
        dr.OUT_W, dr.OUT_H = 2560, 1440


def test_chapter_shots_stock_film_overlay(tmp_path):
    chapter = {"title": "c", "paragraphs": [{"text": "a", "shots": [
        {"stock": "gok"}, {"film": "hattusa", "start": 42.0},
        {"image": "x", "overlay": "toz", "overlay_opacity": 0.4}]}]}
    audio = [{"duration": 12.0, "words": _words("Bir. İki. Üç. Dört. Beş. Altı.", 2.0)}]
    layout = dt.layout_chapter(chapter, [12.0])
    shots = dt.chapter_shots(chapter, audio, layout, {"x": "x.jpg"}, tmp_path,
                             stock_paths={"gok": "gok.mp4", "toz": "toz.mp4"},
                             film_paths={"hattusa": "film.webm"})
    assert [s["kind"] for s in shots] == ["video", "video", "image"]
    assert shots[1]["path"] == "film.webm" and shots[1]["start"] == 42.0
    assert shots[2]["overlay"] == "toz.mp4" and shots[2]["overlay_opacity"] == 0.4


def test_validate_stock_film_overlay_refs(tmp_path):
    data = {"slug": "x", "title": "t", "images": {"a": {}}, "stock": {"gok": {"q": "sky"}},
            "films": {}, "chapters": [{"title": "c", "paragraphs": [{"text": "t", "shots": [
                {"stock": "yok"}, {"film": "f"}, {"image": "a", "overlay": "sis"}]}]}]}
    problems = dt.validate(data, tmp_path)
    assert any("stok video tanımsız" in p for p in problems)
    assert any("film tanımsız" in p for p in problems)
    assert any("katman tanımsız" in p for p in problems)


def test_validate_label_must_be_dict(tmp_path):
    data = {"slug": "x", "title": "t", "images": {"a": {}}, "chapters": [{"title": "c", "paragraphs": [
        {"text": "t", "shots": [{"image": "a", "label": "HATTUŞA · ÇORUM"},
                                {"image": "a", "label": {"title": "HATTUŞA", "subtitle": "ÇORUM"}}]}]}]}
    problems = dt.validate(data, tmp_path)
    assert len([p for p in problems if "etiket" in p]) == 1


def test_edge_cache_replaced_when_elevenlabs_available(tmp_path, monkeypatch):
    import json
    # Önceki çalışmada ses kimliği yoktu → edge-tts önbelleği
    (tmp_path / "engine.json").write_text(json.dumps({"engine": "edge"}))
    (tmp_path / "p000.json").write_text(json.dumps({"fp": "eski", "words": []}))
    (tmp_path / "p000.mp3").write_bytes(b"x")
    calls = []

    def fake_eleven(client, voice_id, text, prev, nxt, settings):
        calls.append(text)
        raise RuntimeError("ağ yok (test)")

    monkeypatch.setattr(da, "_eleven_paragraph", fake_eleven)
    monkeypatch.setitem(__import__("sys").modules, "elevenlabs",
                        type("M", (), {"ElevenLabs": lambda api_key: None}))
    monkeypatch.setattr(da, "_edge_paragraph", None)  # edge'e düşerse hata verir
    with pytest.raises(Exception):
        da.synthesize(["Merhaba"], tmp_path, voice_id="v", api_key="k")
    assert calls == ["Merhaba"]                       # ElevenLabs denendi
    assert not (tmp_path / "p000.mp3").exists()       # eski yedek ses atıldı


def test_commons_music_used_and_credited(tmp_path):
    import json
    prod = _mini_production(tmp_path)
    prod.data["chapters"][0]["music"] = "gizem"
    credit = {"title": "File:Kevin MacLeod - Dream Culture.ogg", "artist": "Kevin MacLeod",
              "license": "CC BY 3.0"}
    prod.path("videos.json").write_text(json.dumps(
        {"stock": {}, "films": {}, "music": {"gizem": {"path": "music/gizem.ogg", "credit": credit},
                                             "huzun": {"path": "music/huzun.ogg", "credit": credit}}}))
    assert prod._music_for("gizem") == str(prod.build / "music/gizem.ogg")
    assert prod._music_for(None) is None
    text = prod.description("0:00 Giriş\n1:00 A\n2:00 B")
    assert '🎵 Müzik\n• "Dream Culture" — Kevin MacLeod (CC BY 3.0)' in text
    assert text.count("Dream Culture") == 1          # kullanılmayan "huzun" listelenmez


def _fake_elevenlabs(monkeypatch, error="403 output_format not allowed"):
    calls = []

    def fake(client, voice_id, text, prev, nxt, settings):
        calls.append(text)
        raise RuntimeError(error)

    monkeypatch.setattr(da, "_eleven_paragraph", fake)
    monkeypatch.setitem(__import__("sys").modules, "elevenlabs",
                        type("M", (), {"ElevenLabs": lambda api_key: None}))
    monkeypatch.setattr(da, "_edge_paragraph", None)   # edge'e düşerse TypeError
    return calls


def test_strict_elevenlabs_raises_instead_of_robot_voice(tmp_path, monkeypatch):
    _fake_elevenlabs(monkeypatch)
    with pytest.raises(da.TTSError, match="output_format not allowed"):
        da.synthesize(["Merhaba"], tmp_path, voice_id="v", api_key="k", engine="elevenlabs")
    assert not (tmp_path / "engine.json").exists()      # edge kaydı oluşmadı


def test_strict_elevenlabs_requires_voice_id(tmp_path):
    with pytest.raises(da.TTSError, match="TTS_VOICE_ID_TR"):
        da.synthesize(["Merhaba"], tmp_path, voice_id="", api_key="k", engine="elevenlabs")


def test_elevenlabs_format_works_on_all_plans():
    assert da.ELEVEN_FORMAT == "mp3_44100_128"


def test_voice_preview_sent_to_telegram(tmp_path, monkeypatch):
    prod = _mini_production(tmp_path)
    clips = []
    for i in range(3):
        p = tmp_path / f"p{i}.mp3"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=d=1",
                        "-c:a", "libmp3lame", str(p)], check=True)
        clips.append({"path": str(p), "duration": 30.0, "engine": "elevenlabs"})
    sent = {}
    from scripts import notifier
    monkeypatch.setattr(notifier, "send_audio", lambda path, cap: sent.update(path=path, cap=cap) or True)
    prod._send_voice_preview(clips)
    assert Path(sent["path"]).exists() and "elevenlabs" in sent["cap"]
    listing = prod.path("ses", "onizleme.txt").read_text()
    assert listing.count("file ") == 2                  # 60 sn'ye ulaşınca durur


def test_normalize_rms_equalizes_loud_and_quiet_tracks():
    t = np.linspace(0, 2, 2 * da.SR, dtype=np.float32)
    loud = 0.8 * np.sin(2 * np.pi * 220 * t).astype(np.float32)
    quiet = 0.01 * np.sin(2 * np.pi * 220 * t).astype(np.float32)
    a, b = da.normalize_rms(loud), da.normalize_rms(quiet)
    rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)))
    assert abs(rms(a) - da.BED_RMS_DB) < 0.5 and abs(rms(b) - da.BED_RMS_DB) < 0.5


def test_sfx_bed_places_clip_audio_with_fades(tmp_path):
    clip = tmp_path / "k.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=64x36:d=4",
                    "-f", "lavfi", "-i", "sine=f=300:d=4", "-shortest", "-c:v", "libx264",
                    "-c:a", "aac", str(clip)], check=True)
    bed = da.sfx_bed([(str(clip), 1.0, 2.0, 2.0)], total=6.0)
    sr = da.SR
    assert np.abs(bed[: int(1.9 * sr)]).max() == 0          # öncesi sessiz
    assert np.abs(bed[int(2.8 * sr): int(3.2 * sr)]).max() > 0.01
    assert abs(bed[int(2.0 * sr)]) < 0.01                    # yumuşak giriş
    assert np.abs(bed[int(4.1 * sr):]).max() == 0            # sonrası sessiz


def test_clip_shots_have_natural_sound_by_default(tmp_path):
    (tmp_path / "klip.mp4").write_bytes(b"x")
    ch = {"title": "c", "paragraphs": [{"text": "Bir. İki. Üç.", "shots": [
        {"clip": "klip.mp4"}, {"clip": "klip.mp4", "sfx": False}, {"stock": "s"}]}]}
    audio = [{"duration": 9.0, "words": [{"word": "Bir.", "start": 0, "end": 1},
                                          {"word": "İki.", "start": 3, "end": 4},
                                          {"word": "Üç.", "start": 6, "end": 7}]}]
    lay = dt.layout_chapter(ch, [9.0])
    shots = dt.chapter_shots(ch, audio, lay, {}, tmp_path, stock_paths={"s": "s.mp4"})
    assert [s["sfx"] for s in shots] == [True, False, False]
    dr.Shot(**shots[0])                                      # render çekimi kabul ediyor


def test_music_calmness_ranks_pad_above_drums():
    from scripts import doc_music as dm
    sr = dm.SR
    t = np.arange(int(100 * sr)) / sr
    pad = (0.3 * np.sin(2 * np.pi * 110 * t) + 0.2 * np.sin(2 * np.pi * 165 * t)).astype(np.float32)
    rng = np.random.default_rng(0)
    drums = np.zeros_like(pad)
    for beat in np.arange(0, 100, 0.25):                 # 4 vuruş/sn, parlak gürültü atakları
        a = int(beat * sr)
        drums[a:a + 2000] += rng.normal(0, 0.5, 2000).astype(np.float32) * np.exp(-np.arange(2000) / 300)
    m_pad, m_drum = dm.analyze_signal(pad), dm.analyze_signal(drums)
    assert m_pad["onset_rate"] < m_drum["onset_rate"]
    assert m_pad["centroid_hz"] < m_drum["centroid_hz"]
    ranked = dm.rank([{"commons": "davul", "duration": 100, **m_drum},
                      {"commons": "pad", "duration": 100, **m_pad},
                      {"commons": "kisa", "duration": 30, **m_pad}])
    assert [r["commons"] for r in ranked] == ["pad", "davul"]   # kısa parça elendi


def test_music_credit_names_are_clean():
    from scripts.doc_pipeline import _track_name
    assert _track_name("File:Kevin MacLeod - 06 - Impact Lento.ogg") == "Impact Lento"
    assert _track_name("File:Heart of Nowhere (MacLeod, Kevin) (ISRC USUAN1400045).oga") == "Heart of Nowhere"


def _timed_words(n, sec_per_word, t0=0.0, word="kelime"):
    out, t = [], t0
    for _ in range(n):
        out.append({"word": word, "start": round(t, 3), "end": round(t + sec_per_word * 0.9, 3)})
        t += sec_per_word
    return out


def test_rush_score_flags_sped_up_section():
    normal = _timed_words(30, 0.5)
    rushed = _timed_words(10, 0.5) + _timed_words(8, 0.3, t0=5.0) + _timed_words(10, 0.5, t0=7.4)
    ref = da.reference_rate([normal, normal, rushed])
    assert da.rush_score(normal, ref) < da.RUSH_LIMIT
    assert da.rush_score(rushed, ref) > da.RUSH_LIMIT


def test_rush_repair_regenerates_only_rushed_paragraph(tmp_path, monkeypatch):
    import json
    normal, rushed = _timed_words(30, 0.5), _timed_words(10, 0.5) + _timed_words(8, 0.3, t0=5.0) + _timed_words(10, 0.5, t0=7.4)
    results = []
    for i, w in enumerate([normal, normal, rushed]):
        mp3 = tmp_path / f"p{i:03d}.mp3"
        mp3.write_bytes(b"eski")
        (tmp_path / f"p{i:03d}.json").write_text(json.dumps({"fp": "x", "words": w}))
        results.append({"path": str(mp3), "duration": 15.0, "words": w})
    calls = []

    def fake(client, voice_id, text, prev, nxt, settings):
        calls.append((text, settings))
        steady = " ".join(["kelime"] * 28)
        ends = [k * 0.5 for k in range(len(steady))]
        return b"yeni", {"characters": list(steady), "character_start_times_seconds": ends,
                         "character_end_times_seconds": [e + 0.04 for e in ends]}

    monkeypatch.setattr(da, "_eleven_paragraph", fake)
    monkeypatch.setattr(da, "_probe_duration", lambda p: 15.0)
    texts = ["a " * 28] * 3
    da._repair_rushes(results, texts, texts, tmp_path, None, "v", budget=5000)
    assert len(calls) == 1 and calls[0][1] == da.STEADY_SETTINGS     # yalnızca hızlanan paragraf
    assert (tmp_path / "p002.mp3").read_bytes() == b"yeni"
    assert json.loads((tmp_path / "p002.json").read_text())["repaired"] is True
    report = json.loads((tmp_path / "hiz_raporu.json").read_text())
    assert report["paragraflar"][0]["durum"] == "düzeltildi"
    # İkinci çalıştırmada aynı paragraf için tekrar kredi harcanmaz
    da._repair_rushes(results, texts, texts, tmp_path, None, "v", budget=5000)
    assert len(calls) == 1


def test_credit_report_counts_new_paragraphs(tmp_path, monkeypatch):
    import json
    prod = _mini_production(tmp_path)
    from scripts import notifier
    sent = []
    monkeypatch.setattr(notifier, "send_message", lambda m: sent.append(m) or True)
    monkeypatch.setattr(da, "elevenlabs_balance",
                        lambda key: {"tier": "starter", "used": 12000, "limit": 40000})
    results = [{"new": True, "chars": 100}, {"new": False, "chars": 50}]
    prod._send_credit_report(results, {"tier": "starter", "used": 11900, "limit": 40000}, "k")
    k = json.loads(prod.path("kredi.json").read_text())
    assert k["yeni_paragraf"] == 1 and k["yeni_karakter"] == 100
    assert "100 kredi düştü" in sent[0] and "1 paragraf önbellekten" in sent[0]


def _vid(vid, title, when, privacy="private"):
    return {"id": vid, "snippet": {"title": title, "publishedAt": when, "categoryId": "27"},
            "status": {"privacyStatus": privacy, "embeddable": True, "license": "youtube",
                       "publicStatsViewable": True, "containsSyntheticMedia": True},
            "contentDetails": {"duration": "PT35M"}}


def test_channel_pick_latest_and_status():
    from scripts import channel_setup as cs
    vids = [_vid("a", "Hitit İmparatorluğu'nun Tam Hikâyesi", "2026-10-31T23:00:00Z"),
            _vid("c", "Hitit İmparatorluğu'nun Tam Hikâyesi", "2026-11-01T09:30:00Z"),
            _vid("w", "What If The Moon Vanished", "2026-11-01T10:00:00Z", "unlisted"),
            _vid("b", "Hitit İmparatorluğu'nun Tam Hikâyesi", "2026-11-01T04:00:00Z")]
    latest, older = cs.pick_latest(vids, "hitit")
    assert latest["id"] == "c" and [v["id"] for v in older] == ["b", "a"]
    st = cs.scheduled_status(latest["status"], "2026-11-01T16:00:00Z")
    assert st["privacyStatus"] == "private" and st["publishAt"] == "2026-11-01T16:00:00Z"
    assert st["containsSyntheticMedia"] is True and st["selfDeclaredMadeForKids"] is False
    no_flag = {k: v for k, v in latest["status"].items() if k != "containsSyntheticMedia"}
    assert cs.scheduled_status(no_flag, "2026-11-01T16:00:00Z")["containsSyntheticMedia"] is True
    assert cs.valid_publish_time("2026-11-01T16:00:00Z") == "2026-11-01T16:00:00Z"
    with pytest.raises(ValueError):
        cs.valid_publish_time("2026-11-01T16:00:00")


def test_channel_branding_keeps_other_settings():
    from scripts import channel_setup as cs
    b = cs.branding_update({"channel": {"title": "Eski", "unsubscribedTrailer": "x"},
                            "watch": {"textColor": "#fff"}}, banner_url="https://banner")
    assert b["channel"]["unsubscribedTrailer"] == "x" and b["watch"] == {"textColor": "#fff"}
    assert b["channel"]["country"] == "TR" and b["channel"]["defaultLanguage"] == "tr"
    assert '"tarih belgeseli"' in b["channel"]["keywords"]
    assert b["image"]["bannerExternalUrl"] == "https://banner"


class _Req:
    def __init__(self, result, log, name):
        self.result, self.log, self.name = result, log, name

    def execute(self):
        self.log.append(self.name)
        return self.result


class _FakeYT:
    """Yalnızca channel_setup'ın kullandığı çağrıları taklit eden YouTube istemcisi."""

    def __init__(self, videos):
        self.videos_data, self.log, self.bodies = videos, [], {}

    def _r(self, name, result=None, body=None):
        if body is not None:
            self.bodies[name] = body
        return _Req(result or {}, self.log, name)

    def channels(self):
        yt = self
        class C:
            def list(self, **k):
                return yt._r("channels.list", {"items": [{"id": "UC1", "snippet": {"title": "Roli"},
                    "statistics": {}, "brandingSettings": {"channel": {"title": "Roli"}},
                    "contentDetails": {"relatedPlaylists": {"uploads": "UU1"}}}]})
            def update(self, part, body):
                return yt._r("channels.update", body=body)
        return C()

    def channelBanners(self):
        yt = self
        class B:
            def insert(self, media_body):
                return yt._r("banner", {"url": "https://banner"})
        return B()

    def playlistItems(self):
        yt = self
        class P:
            def list(self, playlistId, **k):
                if playlistId == "UU1":
                    return yt._r("uploads", {"items": [{"contentDetails": {"videoId": v["id"]}} for v in yt.videos_data]})
                return yt._r("pl.items", {"items": []})
            def insert(self, part, body):
                return yt._r("pl.add", body=body)
        return P()

    def videos(self):
        yt = self
        class V:
            def list(self, **k):
                return yt._r("videos.list", {"items": yt.videos_data})
            def update(self, part, body):
                return yt._r("videos.update", body=body)
        return V()

    def playlists(self):
        yt = self
        class L:
            def list(self, **k):
                return yt._r("playlists.list", {"items": []})
            def insert(self, part, body):
                return yt._r("playlists.insert", {"id": "PL9"}, body=body)
        return L()

    def commentThreads(self):
        yt = self
        class T:
            def list(self, **k):
                return yt._r("comments.list", {"items": []})
            def insert(self, part, body):
                return yt._r("comments.insert", body=body)
        return T()


def test_channel_apply_with_fake_youtube(tmp_path, monkeypatch):
    from scripts import channel_setup as cs
    monkeypatch.setattr(cs, "render_art", lambda folder, out: {"banner": tmp_path / "b.jpg"})
    monkeypatch.setattr(cs, "KANAL_JSON", tmp_path / "yok.json")
    (tmp_path / "b.jpg").write_bytes(b"jpg")
    yt = _FakeYT([_vid("old", "Hitit İmparatorluğu", "2026-10-31T23:00:00Z"),
                  _vid("new", "Hitit İmparatorluğu", "2026-11-01T09:30:00Z")])
    r = cs.apply(yt, tmp_path, "2026-11-01T16:00:00Z", "Hitit", tmp_path)
    assert r["video_id"] == "new" and r["playlist_id"] == "PL9" and not r["sorunlar"]
    assert yt.bodies["videos.update"]["status"]["publishAt"] == "2026-11-01T16:00:00Z"
    assert yt.bodies["pl.add"]["snippet"]["resourceId"]["videoId"] == "new"
    assert "playlist?list=PL9" in yt.bodies["comments.insert"]["snippet"]["topLevelComment"]["snippet"]["textOriginal"]
    assert yt.bodies["channels.update"]["brandingSettings"]["image"]["bannerExternalUrl"] == "https://banner"
    assert r["silinebilir"] == ["https://youtu.be/old (private)"]
    assert "delete" not in " ".join(yt.log)                 # hiçbir şey silinmez


def test_channel_retry_waits_for_new_playlist(monkeypatch):
    from scripts import channel_setup as cs
    import time
    monkeypatch.setattr(time, "sleep", lambda s: None)
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise RuntimeError("playlistNotFound")
        return {"ok": True}

    assert cs._retry(flaky) == {"ok": True} and len(calls) == 3
