"""video_assembler saf fonksiyon testleri (FFmpeg gerektirmez)."""

from scripts.video_assembler import (
    _split_into_subtitle_chunks, _format_srt_time, generate_srt
)


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
