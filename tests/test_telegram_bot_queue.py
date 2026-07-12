"""telegram_bot Short kuyruğu entegrasyon testleri (ağ/pipeline mock'lu)."""

import pytest

import scripts.telegram_bot as tb
import scripts.shorts_queue as sq
import scripts.manual_images as mi
import scripts.scheduler as scheduler


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(sq, "QUEUE_FILE", tmp_path / "shorts_queue.json")
    monkeypatch.setattr(scheduler, "TOPICS_FILE", tmp_path / "topics.json")
    sent = []
    monkeypatch.setattr(tb, "send_message", lambda text, **kw: sent.append(text) or True)
    # manual_images.send_message da izole (start_pending buradan mesaj atar)
    monkeypatch.setattr(mi, "send_message", lambda text, **kw: sent.append(text) or True)
    yield sent


class TestAdvanceShortsQueue:
    def test_no_op_when_production_pending(self, monkeypatch):
        sq.enqueue(["topic A", "topic B"])
        monkeypatch.setattr(mi, "load_pending", lambda: {"topic": "busy"})
        started = []
        monkeypatch.setattr(scheduler, "run_short", lambda **kw: started.append(kw))

        assert tb._advance_shorts_queue() is False
        assert started == []               # başlatılmadı
        assert sq.length() == 2            # kuyruk dokunulmadı

    def test_starts_next_when_idle(self, monkeypatch):
        sq.enqueue(["topic A", "topic B"])
        monkeypatch.setattr(mi, "load_pending", lambda: None)
        started = []
        monkeypatch.setattr(scheduler, "run_short",
                            lambda **kw: started.append(kw.get("topic")) or True)

        assert tb._advance_shorts_queue() is True
        assert started == ["topic A"]      # ilk konu başlatıldı
        assert sq.load_queue() == ["topic B"]  # kuyruktan çıktı

    def test_empty_queue_no_op(self, monkeypatch):
        monkeypatch.setattr(mi, "load_pending", lambda: None)
        assert tb._advance_shorts_queue() is False

    def test_run_short_failure_does_not_crash(self, monkeypatch):
        sq.enqueue(["topic A"])
        monkeypatch.setattr(mi, "load_pending", lambda: None)

        def boom(**kw):
            raise RuntimeError("gemini down")

        monkeypatch.setattr(scheduler, "run_short", boom)
        # Patlamamalı, False dönmeli
        assert tb._advance_shorts_queue() is False


class TestCmdShort:
    def test_number_enqueues_from_pool(self, monkeypatch):
        # Boşta değil ki auto-start pipeline'ı çalıştırmasın; sadece kuyruğu test et
        monkeypatch.setattr(mi, "load_pending", lambda: {"topic": "busy"})
        reply = tb._cmd_short("3")
        assert sq.length() == 3
        assert "3 Short" in reply

    def test_custom_topic_enqueues(self, monkeypatch):
        monkeypatch.setattr(mi, "load_pending", lambda: {"topic": "busy"})
        tb._cmd_short("What if the moon turned to cheese")
        assert "What if the moon turned to cheese" in sq.load_queue()

    def test_idle_triggers_start(self, monkeypatch):
        monkeypatch.setattr(mi, "load_pending", lambda: None)
        started = []
        monkeypatch.setattr(scheduler, "run_short",
                            lambda **kw: started.append(kw.get("topic")) or True)
        reply = tb._cmd_short("2")
        # 2 eklendi, biri hemen başladı (kuyrukta 1 kaldı)
        assert len(started) == 1
        assert sq.length() == 1
        assert "başlat" in reply.lower() or "gönder" in reply.lower()
