"""youtube_uploader yardımcı fonksiyon testleri (API gerektirmez)."""

from datetime import datetime, timedelta, timezone

import scripts.youtube_uploader as uploader
from scripts.youtube_uploader import (
    _generate_timestamps, _generate_description, _sanitize_tags,
    next_optimal_publish_time, record_upload, load_uploads,
    YOUTUBE_TAGS_MAX_CHARS,
)


class TestSanitizeTags:
    def test_deduplicates_case_insensitive(self):
        result = _sanitize_tags(["Science", "science", "SCIENCE", "what if"])
        assert result == ["Science", "what if"]

    def test_drops_empty_and_invalid_chars(self):
        result = _sanitize_tags(["ok", "", "  ", "bad<tag>", "fine"])
        assert result == ["ok", "fine"]

    def test_enforces_total_char_limit_not_count(self):
        """Gerçek hata: 30 uzun etiket kolayca 500 karakteri aşıyordu (invalidTags)."""
        long_tags = [f"what if scenario keyword number {i} explained" for i in range(30)]
        result = _sanitize_tags(long_tags)
        total_len = sum(len(t) + 1 for t in result)
        assert total_len <= YOUTUBE_TAGS_MAX_CHARS
        assert len(result) < 30  # hepsi sığmaz, kesilmeli

    def test_short_tags_all_kept(self):
        tags = ["a", "b", "c"]
        assert _sanitize_tags(tags) == tags


class TestTimestamps:
    def test_fallback_without_audio_results(self):
        result = _generate_timestamps(None)
        assert "00:00" in result

    def test_real_durations(self):
        audio_results = [
            {"duration_seconds": 30},
            {"duration_seconds": 90},
            {"duration_seconds": 60},
        ]
        result = _generate_timestamps(audio_results)
        lines = result.split("\n")
        assert lines[0].startswith("00:00")
        assert lines[1].startswith("00:30")   # 30 sn sonra
        assert lines[2].startswith("02:00")   # 30 + 90 = 120 sn


class TestDescription:
    def test_includes_seo_intro_and_hashtags(self):
        desc = _generate_description(
            "Test Title", ["what if", "science"], seo_description="SEO intro line."
        )
        assert desc.startswith("SEO intro line.")
        assert "#whatif" in desc
        assert "Timestamps" in desc


class TestPublishTime:
    def test_returns_future_time_at_target_hour(self):
        t = next_optimal_publish_time(hour_utc=15)
        now = datetime.now(timezone.utc)
        assert t > now + timedelta(hours=1)
        assert t.hour == 15
        assert t.minute == 0

    def test_within_next_two_days(self):
        t = next_optimal_publish_time()
        assert t <= datetime.now(timezone.utc) + timedelta(days=2)


class TestUploadRegistry:
    def test_record_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setattr(uploader, "UPLOADS_FILE", tmp_path / "uploads.json")

        assert load_uploads() == []

        record_upload("abc123", "Test Video", kind="short", privacy="public")
        record_upload("def456", "Long Video", kind="long")

        records = load_uploads()
        assert len(records) == 2
        assert records[0]["video_id"] == "abc123"
        assert records[0]["kind"] == "short"
        assert records[1]["kind"] == "long"
        assert records[1]["privacy"] == "private"
