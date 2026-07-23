"""video_assembler saf fonksiyon testleri (FFmpeg gerektirmez)."""

import scripts.video_assembler as va
from scripts.video_assembler import (
    _split_into_subtitle_chunks, _format_srt_time, generate_srt, is_video_asset,
    create_scene_clip_from_video,
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
