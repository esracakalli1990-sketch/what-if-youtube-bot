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
