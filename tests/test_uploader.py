"""youtube_uploader yardımcı fonksiyon testleri (API gerektirmez)."""

from datetime import datetime, timedelta, timezone

import scripts.youtube_uploader as uploader
from scripts.youtube_uploader import (
    _generate_timestamps, _generate_description,
    next_optimal_publish_time, record_upload, load_uploads,
)


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
