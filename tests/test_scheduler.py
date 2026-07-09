"""scheduler konu havuzu testleri (dosya sistemi tmp_path'e yönlendirilir)."""

import pytest

import scripts.scheduler as scheduler


@pytest.fixture(autouse=True)
def isolated_topics_file(tmp_path, monkeypatch):
    """Her test kendi topics.json dosyasını kullanır — repo kirlenmez."""
    monkeypatch.setattr(scheduler, "TOPICS_FILE", tmp_path / "topics.json")


class TestTopicPool:
    def test_default_pool_created_on_first_load(self):
        data = scheduler.load_topics()
        assert len(data["topics"]) == len(scheduler.DEFAULT_TOPICS)
        assert all(t["status"] == "pending" for t in data["topics"])

    def test_get_next_topic_returns_first_pending(self):
        topic = scheduler.get_next_topic()
        assert topic == scheduler.DEFAULT_TOPICS[0]

    def test_mark_completed_advances_queue(self):
        first = scheduler.get_next_topic()
        scheduler.mark_topic_completed(first, episode_number=1)

        data = scheduler.load_topics()
        entry = next(t for t in data["topics"] if t["topic"] == first)
        assert entry["status"] == "completed"
        assert entry["episode"] == 1

        assert scheduler.get_next_topic() == scheduler.DEFAULT_TOPICS[1]

    def test_mark_failed_and_reset(self):
        first = scheduler.get_next_topic()
        scheduler.mark_topic_failed(first, error="boom")

        data = scheduler.load_topics()
        entry = next(t for t in data["topics"] if t["topic"] == first)
        assert entry["status"] == "failed"
        assert entry["error"] == "boom"

        scheduler.reset_failed()
        data = scheduler.load_topics()
        entry = next(t for t in data["topics"] if t["topic"] == first)
        assert entry["status"] == "pending"

    def test_add_topic_deduplicates_case_insensitive(self):
        scheduler.load_topics()
        before = len(scheduler.load_topics()["topics"])

        scheduler.add_topic("What if cats ruled the world?")
        scheduler.add_topic("WHAT IF CATS RULED THE WORLD?")  # duplikat

        after = len(scheduler.load_topics()["topics"])
        assert after == before + 1

    def test_all_completed_returns_none(self):
        data = scheduler.load_topics()
        for t in data["topics"]:
            t["status"] = "completed"
        scheduler.save_topics(data)
        assert scheduler.get_next_topic() is None


class TestShortTopics:
    def test_short_topic_independent_of_long_status(self):
        # Uzun videosu tamamlanmış konu hâlâ Short alabilir
        first = scheduler.get_next_topic()
        scheduler.mark_topic_completed(first, episode_number=1)
        assert scheduler.get_next_short_topic() == first

    def test_mark_short_done_advances(self):
        first = scheduler.get_next_short_topic()
        scheduler.mark_short_done(first)
        assert scheduler.get_next_short_topic() == scheduler.DEFAULT_TOPICS[1]

    def test_failed_topics_skipped_for_shorts(self):
        first = scheduler.DEFAULT_TOPICS[0]
        scheduler.load_topics()
        scheduler.mark_topic_failed(first, "boom")
        assert scheduler.get_next_short_topic() == scheduler.DEFAULT_TOPICS[1]


class TestRunShort:
    def test_success_marks_short_done(self, monkeypatch):
        import main
        calls = {}

        def fake_pipeline(topic, **kwargs):
            calls["topic"] = topic
            calls["kwargs"] = kwargs
            return "output/short_01.mp4"

        monkeypatch.setattr(main, "run_pipeline", fake_pipeline)

        assert scheduler.run_short(privacy="public")
        assert calls["topic"] == scheduler.DEFAULT_TOPICS[0]
        assert calls["kwargs"]["mode"] == "shorts"
        assert calls["kwargs"]["privacy"] == "public"
        # İşaretlendi — bir sonraki çağrı ikinci konuyu seçer
        assert scheduler.get_next_short_topic() == scheduler.DEFAULT_TOPICS[1]

    def test_failure_does_not_mark(self, monkeypatch):
        import main
        monkeypatch.setattr(main, "run_pipeline", lambda topic, **kw: None)

        assert not scheduler.run_short()
        # İşaretlenmedi — aynı konu sırada kalır
        assert scheduler.get_next_short_topic() == scheduler.DEFAULT_TOPICS[0]
