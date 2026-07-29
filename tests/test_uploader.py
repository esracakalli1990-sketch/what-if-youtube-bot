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

    def test_enforces_youtube_real_char_limit_with_quotes(self):
        """Canlı hata (invalidTags 400): çok-kelimeli etiketler YouTube'da TIRNAK
        içinde sayılır; gerçek toplam 500'ü aşıyordu. Artık tırnak payıyla kesilir."""
        long_tags = [f"what if scenario keyword number {i} explained" for i in range(30)]
        result = _sanitize_tags(long_tags)
        # YouTube'un gerçek sayımı: boşluklu etiket = uzunluk + 2 (tırnak) + ayraç
        real_total = sum(len(t) + (2 if " " in t else 0) + 1 for t in result)
        assert real_total <= 500          # YouTube'un sert sınırı — asla aşılmamalı
        assert real_total <= YOUTUBE_TAGS_MAX_CHARS
        assert len(result) < 30           # hepsi sığmaz, kesilmeli

    def test_short_tags_all_kept(self):
        tags = ["a", "b", "c"]
        assert _sanitize_tags(tags) == tags


class TestFirstComment:
    """İlk yorum: senaryonun İÇ NOTU sızmamalı, Roli'nin sesi olmalı."""

    _SCENARIO = {
        "scenes": [
            {"twist_element": "The visceral shock of immediate mass marine death."},
            {"twist_element": "The big twist of Earth's mass redistribution and its "
                              "effect on rotation and geology, leading to a looping "
                              "re-watch by connecting 'Earth itself shifts' back."},
        ]
    }

    def test_does_not_leak_internal_twist_element(self):
        """Canlı hata: twist_element yoruma yapıştırılıyordu.

        O alan senaryo yazarı için yazılmış bir iç not; izleyiciye hitap etmiyor.
        Yayınlanan yorum robotik ve anlamsız görünüyordu.
        """
        c = uploader._build_first_comment(self._SCENARIO, "UWZenX5WpTU")
        assert "mass redistribution" not in c
        assert "looping re-watch" not in c
        assert "visceral shock" not in c
        assert "twist" not in c.lower()

    def test_has_roli_voice_and_question(self):
        c = uploader._build_first_comment(self._SCENARIO, "UWZenX5WpTU")
        assert c.startswith("🐰 ")
        assert "👇" in c                     # etkileşim sorusu var
        assert any(o in c for o in uploader._ROLI_OPENERS)

    def test_deterministic_per_video(self):
        a = uploader._build_first_comment(self._SCENARIO, "abc123")
        b = uploader._build_first_comment(self._SCENARIO, "abc123")
        assert a == b

    def test_works_without_scenario(self):
        c = uploader._build_first_comment(None, "abc123")
        assert c.startswith("🐰 ") and "👇" in c


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
