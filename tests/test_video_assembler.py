"""video_assembler saf fonksiyon testleri (FFmpeg gerektirmez)."""

import scripts.video_assembler as va
from scripts.video_assembler import (
    _split_into_subtitle_chunks, _format_srt_time, generate_srt, is_video_asset,
    create_scene_clip_from_video, _scene_fade_filter,
)


class TestVideoSceneClipNoLoop:
    """Video sahne klibi: kısa klip döngülenmez, son kare dondurulur."""

    def test_uses_freeze_not_stream_loop(self, monkeypatch, tmp_path):
        captured = {}

        def fake_run(cmd, *a, **k):
            captured["cmd"] = cmd
            return True

        monkeypatch.setattr(va, "_run_ffmpeg", fake_run)
        create_scene_clip_from_video(
            "in.mp4", "a.mp3", str(tmp_path / "out.mp4"),
            duration=8.5, resolution=(1080, 1920),
        )
        cmd = captured["cmd"]
        # Döngü kaldırıldı
        assert "-stream_loop" not in cmd
        joined = " ".join(cmd)
        # Son kare dondurma filtresi var
        assert "tpad=stop_mode=clone" in joined
        # Süre anlatıma sabitleniyor
        assert "-t" in cmd and "8.500" in cmd


class TestSceneFadeTransition:
    """Sahneler arası dip-to-black geçiş: sert kesme + renk sıçraması yumuşar."""

    def test_fade_filter_both_sides(self):
        f = _scene_fade_filter(8.0, fade_in=True, fade_out=True)
        assert "fade=t=in:st=0:" in f
        # Çıkış fade'i sahne sonuna (duration - d) yakın başlar
        assert "fade=t=out:st=7.700:d=0.300" in f

    def test_first_scene_no_fade_in(self):
        """İlk sahne karadan AÇILMAZ (hook ilk karede anında vursun)."""
        f = _scene_fade_filter(8.0, fade_in=False, fade_out=True)
        assert "t=in" not in f
        assert "t=out" in f

    def test_last_scene_no_fade_out(self):
        """Son sahne karartmaZ (final kare kalsın, loop temiz)."""
        f = _scene_fade_filter(8.0, fade_in=True, fade_out=False)
        assert "t=in" in f
        assert "t=out" not in f

    def test_short_clip_shrinks_fade(self):
        """Çok kısa klipte fade süresi küçülür (giriş+çıkış klibi yutmasın)."""
        f = _scene_fade_filter(0.6, fade_in=True, fade_out=True)
        # d = min(0.3, 0.6/3) = 0.2
        assert "d=0.200" in f

    def test_applied_in_video_clip_command(self, monkeypatch, tmp_path):
        captured = {}

        def fake_run(cmd, *a, **k):
            captured["cmd"] = cmd
            return True

        monkeypatch.setattr(va, "_run_ffmpeg", fake_run)
        create_scene_clip_from_video(
            "in.mp4", "a.mp3", str(tmp_path / "out.mp4"),
            duration=8.0, resolution=(1080, 1920),
            fade_in=True, fade_out=True,
        )
        joined = " ".join(captured["cmd"])
        assert "fade=t=out" in joined
        # tpad'den SONRA gelmeli (dondurulmuş son kare de karartılsın)
        assert joined.index("tpad") < joined.index("fade=t=out")


class TestVideoThenImageScene:
    """Uzun sahne: klip bitince görselden devam (donma yerine hareket+Ken Burns)."""

    def _capture(self, monkeypatch):
        calls = []
        monkeypatch.setattr(va, "_run_ffmpeg", lambda cmd, *a, **k: calls.append(cmd) or True)
        return calls

    def test_builds_video_then_image_segments(self, monkeypatch, tmp_path):
        calls = self._capture(monkeypatch)
        monkeypatch.setattr(va, "probe_duration", lambda p: 10.0)
        monkeypatch.setattr(va, "TEMP_DIR", tmp_path)

        ok = va.create_scene_clip_video_then_image(
            "clip.mp4", "still.png", "a.mp3", str(tmp_path / "out.mp4"),
            duration=40.0, resolution=(1920, 1080),
        )
        assert ok
        assert len(calls) == 3                      # video bölümü, görsel bölümü, birleştirme
        vcmd, icmd, final = (" ".join(c) for c in calls)

        # 1) Video bölümü klibin kendi uzunluğunda ve sessiz
        assert "clip.mp4" in vcmd and "-an" in vcmd and "10.000" in vcmd
        # 2) Görsel bölümü kalan süreyi kaplar (40 - 10 = 30 sn) ve Ken Burns uygular
        assert "still.png" in icmd and "zoompan" in icmd and "30.000" in icmd
        # 3) Birleştirme anlatım sesini bindirir ve toplam süreyi sahneye sabitler
        assert "concat" in final and "a.mp3" in final and "40.000" in final

    def test_transition_between_segments(self, monkeypatch, tmp_path):
        """Klip kararak biter, görsel karadan açılır — sert kesme olmasın."""
        calls = self._capture(monkeypatch)
        monkeypatch.setattr(va, "probe_duration", lambda p: 10.0)
        monkeypatch.setattr(va, "TEMP_DIR", tmp_path)

        va.create_scene_clip_video_then_image(
            "clip.mp4", "still.png", "a.mp3", str(tmp_path / "out.mp4"),
            duration=40.0, resolution=(1920, 1080), fade_in=False, fade_out=False,
        )
        vcmd, icmd, _ = (" ".join(c) for c in calls)
        assert "fade=t=out" in vcmd      # klip sonunda karar
        assert "fade=t=in" in icmd       # görsel karadan açılır

    def test_falls_back_when_clip_covers_narration(self, monkeypatch, tmp_path):
        """Klip anlatımı zaten karşılıyorsa görsele geçmeye gerek yok."""
        monkeypatch.setattr(va, "probe_duration", lambda p: 12.0)
        called = {}

        def fake_from_video(*a, **k):
            called["used"] = True
            return True

        monkeypatch.setattr(va, "create_scene_clip_from_video", fake_from_video)
        ok = va.create_scene_clip_video_then_image(
            "clip.mp4", "still.png", "a.mp3", str(tmp_path / "out.mp4"),
            duration=9.0, resolution=(1080, 1920),
        )
        assert ok and called.get("used")


class TestIsVideoAsset:
    def test_video_extensions(self):
        assert is_video_asset("scene_03.mp4")
        assert is_video_asset("/tmp/clip.MOV")
        assert is_video_asset("a.webm")

    def test_image_extensions(self):
        assert not is_video_asset("scene_03.png")
        assert not is_video_asset("/tmp/thumb.JPG")
        assert not is_video_asset("noext")


class TestSubtitleChunks:
    def test_short_text_single_chunk(self):
        chunks = _split_into_subtitle_chunks("Hello world.", max_chars=80)
        assert chunks == ["Hello world."]

    def test_sentences_grouped_within_limit(self):
        text = "One. Two. Three."
        chunks = _split_into_subtitle_chunks(text, max_chars=80)
        assert chunks == ["One. Two. Three."]

    def test_respects_max_chars(self):
        text = "This is a fairly long sentence. And here is another one that follows."
        chunks = _split_into_subtitle_chunks(text, max_chars=40)
        assert all(len(c) <= 40 for c in chunks)

    def test_very_long_sentence_split_by_words(self):
        text = "word " * 40  # 200 karakter, cümle sonu yok
        chunks = _split_into_subtitle_chunks(text.strip(), max_chars=30)
        assert len(chunks) > 1
        assert all(len(c) <= 30 for c in chunks)

    def test_vertical_short_lines(self):
        text = "Your blood would boil in ninety seconds. Every coastal city would vanish."
        chunks = _split_into_subtitle_chunks(text, max_chars=32)
        assert all(len(c) <= 32 for c in chunks)

    def test_empty_text_returns_original(self):
        assert _split_into_subtitle_chunks("", max_chars=80) == [""]


class TestSrtTime:
    def test_zero(self):
        assert _format_srt_time(0.0) == "00:00:00,000"

    def test_minutes_seconds_millis(self):
        assert _format_srt_time(75.5) == "00:01:15,500"

    def test_hours(self):
        assert _format_srt_time(3661.25) == "01:01:01,250"


class TestGenerateSrt:
    def test_generates_entries_with_scene_durations(self, tmp_path, monkeypatch):
        import scripts.video_assembler as va
        monkeypatch.setattr(va, "TEMP_DIR", tmp_path)

        scenes = [
            {"scene_number": 1, "narration": "First sentence. Second sentence."},
            {"scene_number": 2, "narration": "Third sentence."},
        ]
        audio_results = [
            {"scene_number": 1, "duration_seconds": 10.0},
            {"scene_number": 2, "duration_seconds": 5.0},
        ]

        srt_path = generate_srt(scenes, audio_results)
        content = srt_path.read_text(encoding="utf-8")

        assert "First sentence." in content
        assert "Third sentence." in content
        assert "-->" in content
        # Toplam süre son timestamp'ta görünmeli (10 + 5 = 15 sn)
        assert "00:00:15,000" in content

    def test_skips_scenes_without_audio(self, tmp_path, monkeypatch):
        import scripts.video_assembler as va
        monkeypatch.setattr(va, "TEMP_DIR", tmp_path)

        scenes = [
            {"scene_number": 1, "narration": "Has audio."},
            {"scene_number": 2, "narration": "No audio."},
        ]
        audio_results = [{"scene_number": 1, "duration_seconds": 4.0}]

        srt_path = generate_srt(scenes, audio_results)
        content = srt_path.read_text(encoding="utf-8")
        assert "Has audio." in content
        assert "No audio." not in content

    def test_time_proportional_to_chunk_length(self, tmp_path, monkeypatch):
        """Uzun altyazı parçası, kısa parçadan daha uzun ekran süresi almalı."""
        import scripts.video_assembler as va
        monkeypatch.setattr(va, "TEMP_DIR", tmp_path)

        # Kısa bir ilk cümle, çok daha uzun bir ikinci cümle
        scenes = [{
            "scene_number": 1,
            "narration": (
                "Gone. Every single coastal city on the entire planet "
                "vanishes beneath the churning, unstoppable waves forever."
            ),
        }]
        audio_results = [{"scene_number": 1, "duration_seconds": 10.0}]

        srt_path = generate_srt(scenes, audio_results)
        content = srt_path.read_text(encoding="utf-8")

        # Parça bölme kontrolü: iki ayrı giriş olmalı
        assert "Gone." in content
        # İlk parçanın bitişi 10 sn'lik sahnenin ortasından ÖNCE olmalı (kısa parça)
        # Bloklar: "idx\nstart --> end\ntext\n"
        blocks = [b for b in content.split("\n\n") if b.strip()]
        first_end = blocks[0].split("\n")[1].split(" --> ")[1]
        # "Gone." çok kısa → 5 sn'den (ortadan) çok önce bitmeli
        assert first_end < "00:00:05,000"
        # Sahne tam 10 sn'de bitmeli (birikimli hata olmamalı)
        assert "00:00:10,000" in content
