"""shorts_queue (Short üretim kuyruğu) testleri."""

import pytest

import scripts.shorts_queue as sq


@pytest.fixture(autouse=True)
def isolated_queue(tmp_path, monkeypatch):
    monkeypatch.setattr(sq, "QUEUE_FILE", tmp_path / "shorts_queue.json")
    yield


class TestQueue:
    def test_empty_by_default(self):
        assert sq.load_queue() == []
        assert sq.length() == 0
        assert sq.pop_next() is None

    def test_enqueue_and_order_fifo(self):
        assert sq.enqueue(["a", "b", "c"]) == 3
        assert sq.load_queue() == ["a", "b", "c"]
        assert sq.pop_next() == "a"
        assert sq.pop_next() == "b"
        assert sq.length() == 1

    def test_enqueue_deduplicates(self):
        sq.enqueue(["a", "b"])
        added = sq.enqueue(["b", "c", "a"])  # b,a zaten var
        assert added == 1
        assert sq.load_queue() == ["a", "b", "c"]

    def test_ignores_blank_topics(self):
        added = sq.enqueue(["  ", "", "real"])
        assert added == 1
        assert sq.load_queue() == ["real"]

    def test_clear(self):
        sq.enqueue(["a", "b", "c"])
        assert sq.clear() == 3
        assert sq.load_queue() == []

    def test_survives_reload(self):
        sq.enqueue(["x", "y"])
        # Aynı dosyadan tekrar okuma (kalıcılık)
        assert sq.load_queue() == ["x", "y"]
