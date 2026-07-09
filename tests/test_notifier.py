"""notifier ve telegram_bot testleri (ağa çıkmaz — her şey mock'lu)."""

from datetime import datetime, timezone

import pytest

import scripts.notifier as notifier
import scripts.telegram_bot as tg
from scripts.notifier import build_video_message, build_error_message


class TestMessageBuilders:
    def test_long_video_uploaded(self):
        msg = build_video_message(
            title="What If GRAVITY Doubled?",
            mode="long",
            video_path="output/episode_01.mp4",
            duration_text="12dk 30sn",
            video_id="abc123",
        )
        assert "Uzun video" in msg
        assert "What If GRAVITY Doubled?" in msg
        assert "https://youtu.be/abc123" in msg
        assert "yüklendi" in msg

    def test_short_with_scheduled_publish(self):
        publish = datetime(2026, 7, 10, 15, 0, tzinfo=timezone.utc)
        msg = build_video_message(
            title="Test Short", mode="shorts", video_id="xyz", publish_at=publish,
        )
        assert "Short" in msg
        assert "10.07.2026 15:00 UTC" in msg

    def test_not_uploaded_warning(self):
        msg = build_video_message(title="T", mode="long", video_id=None)
        assert "yüklenmedi" in msg

    def test_error_message_truncates(self):
        msg = build_error_message("Test bağlamı", "x" * 5000)
        assert "Test bağlamı" in msg
        assert len(msg) < 1500


class TestSendMessage:
    def test_unconfigured_returns_false(self, monkeypatch):
        monkeypatch.setattr(notifier, "_config", lambda: ("", ""))
        assert not notifier.send_message("test")

    def test_sends_payload_when_configured(self, monkeypatch):
        monkeypatch.setattr(notifier, "_config", lambda: ("TOKEN", "42"))
        captured = {}

        class FakeResponse:
            status_code = 200
            text = "ok"

        def fake_post(url, json=None, **kwargs):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse()

        monkeypatch.setattr(notifier.requests, "post", fake_post)

        assert notifier.send_message("merhaba")
        assert "botTOKEN/sendMessage" in captured["url"]
        assert captured["json"]["chat_id"] == "42"
        assert captured["json"]["text"] == "merhaba"

    def test_network_error_swallowed(self, monkeypatch):
        monkeypatch.setattr(notifier, "_config", lambda: ("TOKEN", "42"))

        def boom(*args, **kwargs):
            raise ConnectionError("network down")

        monkeypatch.setattr(notifier.requests, "post", boom)
        # Hata yutulur, pipeline'ı durdurmaz
        assert not notifier.send_message("merhaba")


class TestCommandRouting:
    @pytest.fixture(autouse=True)
    def isolated_state(self, tmp_path, monkeypatch):
        import scripts.scheduler as scheduler
        monkeypatch.setattr(tg, "STATE_FILE", tmp_path / "telegram_state.json")
        monkeypatch.setattr(scheduler, "TOPICS_FILE", tmp_path / "topics.json")

    def test_yardim(self):
        reply = tg.handle_command("/yardim")
        assert "/durum" in reply
        assert "/short" in reply

    def test_command_with_bot_suffix(self):
        reply = tg.handle_command("/yardim@WhatIfBot")
        assert "/durum" in reply

    def test_unknown_command(self):
        reply = tg.handle_command("/bilinmeyen")
        assert "Bilinmeyen" in reply

    def test_durum_shows_pool(self, monkeypatch):
        import scripts.youtube_uploader as uploader
        monkeypatch.setattr(uploader, "UPLOADS_FILE", tg.STATE_FILE.parent / "uploads.json")
        reply = tg.handle_command("/durum")
        assert "Bekleyen konu" in reply

    def test_konu_adds_topic(self):
        reply = tg.handle_command("/konu What if the Moon was made of iron?")
        assert "eklendi" in reply
        # Duplikat
        reply2 = tg.handle_command("/konu What if the Moon was made of iron?")
        assert "zaten" in reply2

    def test_konu_without_arg(self):
        reply = tg.handle_command("/konu")
        assert "Kullanım" in reply


class TestProcessPending:
    def test_unauthorized_chat_ignored(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tg, "STATE_FILE", tmp_path / "state.json")
        monkeypatch.setattr(tg, "is_configured", lambda: True)
        monkeypatch.setattr(tg, "load_env", lambda: {
            "TELEGRAM_BOT_TOKEN": "TOKEN", "TELEGRAM_CHAT_ID": "42",
        })

        updates = [{
            "update_id": 100,
            "message": {"chat": {"id": 999}, "text": "/durum"},  # yetkisiz
        }]
        monkeypatch.setattr(tg, "get_updates", lambda token, offset: updates)

        sent = []
        monkeypatch.setattr(tg, "send_message", lambda text, **kw: sent.append(text))

        assert tg.process_pending_commands() == 0
        assert sent == []
        # Offset yine de ilerledi — aynı mesaj tekrar işlenmez
        assert tg._load_offset() == 101

    def test_authorized_command_processed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tg, "STATE_FILE", tmp_path / "state.json")
        monkeypatch.setattr(tg, "is_configured", lambda: True)
        monkeypatch.setattr(tg, "load_env", lambda: {
            "TELEGRAM_BOT_TOKEN": "TOKEN", "TELEGRAM_CHAT_ID": "42",
        })

        updates = [{
            "update_id": 200,
            "message": {"chat": {"id": 42}, "text": "/yardim"},
        }]
        monkeypatch.setattr(tg, "get_updates", lambda token, offset: updates)

        sent = []
        monkeypatch.setattr(tg, "send_message", lambda text, **kw: sent.append(text) or True)

        assert tg.process_pending_commands() == 1
        assert len(sent) == 1
        assert "/durum" in sent[0]
        assert tg._load_offset() == 201
