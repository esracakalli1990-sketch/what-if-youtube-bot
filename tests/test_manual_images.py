"""manual_images (Telegram üzerinden manuel görsel akışı) testleri."""

import io
import json
from datetime import datetime, timedelta, timezone

import pytest
from PIL import Image

import scripts.manual_images as mi


def _scenario(n_scenes=4):
    return {
        "title": "Test Episode",
        "clickbait_title": "TEST! (Shocking)",
        "thumbnail_concept": "A dramatic frozen Earth",
        "scenes": [
            {"scene_number": i + 1, "narration": f"Text {i}", "visual_prompt": f"Visual {i}"}
            for i in range(n_scenes)
        ],
    }


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """Pending dosyası ve Telegram gönderimi izole edilir."""
    monkeypatch.setattr(mi, "PENDING_FILE", tmp_path / "pending_production.json")
    sent = []
    monkeypatch.setattr(mi, "send_message", lambda text, **kw: sent.append(text) or True)
    yield sent


class TestPendingLifecycle:
    def test_start_pending_shorts(self, isolated_state):
        assert mi.start_pending("Test topic", "shorts", _scenario(4), privacy="public")

        pending = mi.load_pending()
        assert pending["topic"] == "Test topic"
        assert pending["expected_images"] == 4  # Short: sadece sahneler
        assert pending["image_file_ids"] == []

        # 1 giriş mesajı + 4 prompt mesajı
        assert len(isolated_state) == 5
        assert "9:16 DİKEY" in isolated_state[0]
        assert "Görsel 1/4" in isolated_state[1]
        assert "Visual 0" in isolated_state[1]
        # Prompt'lar yalın olmalı — API'ye özgü teknik satırlar sızmamalı
        for msg in isolated_state[1:]:
            assert "IP-Adapter" not in msg
            assert "CONSISTENCY RULES" not in msg
            assert "9:16" in msg  # yön talimatı her prompt'ta

    def test_character_brief_added_when_rabbit_in_prompt(self, isolated_state):
        scenario = _scenario(2)
        scenario["scenes"][0]["visual_prompt"] = "A rabbit scientist observing deep-sea vents"
        mi.start_pending("Test topic", "shorts", scenario)
        assert "steampunk space suit" in isolated_state[1]   # tavşanlı sahne
        assert "steampunk space suit" not in isolated_state[2]  # tavşansız sahne

    def test_start_pending_long_includes_thumbnail(self, isolated_state):
        assert mi.start_pending("Test topic", "long", _scenario(5))
        pending = mi.load_pending()
        assert pending["expected_images"] == 6  # 5 sahne + thumbnail
        assert "THUMBNAIL" in isolated_state[-1]


class TestTurkishBrief:
    def test_brief_from_gemini(self, monkeypatch):
        monkeypatch.setattr(mi, "load_env", lambda: {"GEMINI_API_KEY": "test-key"})
        import scripts.scenario_generator as sg
        monkeypatch.setattr(sg, "_call_gemini", lambda *a, **k: {
            "konu": "Güneş aniden yok olsaydı ne olurdu",
            "sahneler": ["Şehir karanlığa gömülür", "Dünya donar"],
        })
        brief = mi.build_turkish_brief(_scenario(2))
        assert "BU VİDEO NE ANLATIYOR" in brief
        assert "Güneş aniden yok" in brief
        assert "Görsel 1" in brief and "Şehir karanlığa" in brief
        assert "Görsel 2" in brief and "Dünya donar" in brief

    def test_brief_empty_without_gemini_key(self, monkeypatch):
        monkeypatch.setattr(mi, "load_env", lambda: {"GEMINI_API_KEY": ""})
        assert mi.build_turkish_brief(_scenario(2)) == ""

    def test_brief_gemini_failure_returns_empty(self, monkeypatch):
        monkeypatch.setattr(mi, "load_env", lambda: {"GEMINI_API_KEY": "test-key"})
        import scripts.scenario_generator as sg

        def boom(*a, **k):
            raise RuntimeError("api down")

        monkeypatch.setattr(sg, "_call_gemini", boom)
        assert mi.build_turkish_brief(_scenario(2)) == ""

    def test_start_pending_sends_brief(self, monkeypatch, isolated_state):
        monkeypatch.setattr(mi, "load_env", lambda: {"GEMINI_API_KEY": "test-key"})
        import scripts.scenario_generator as sg
        monkeypatch.setattr(sg, "_call_gemini", lambda *a, **k: {
            "konu": "Test konu", "sahneler": ["Sahne bir", "Sahne iki"],
        })
        mi.start_pending("Test topic", "shorts", _scenario(2))
        # intro + brief + 2 prompt = 4 mesaj
        assert len(isolated_state) == 4
        assert any("BU VİDEO NE ANLATIYOR" in m for m in isolated_state)

    def test_add_photo_progress_and_complete(self, isolated_state):
        mi.start_pending("Test topic", "shorts", _scenario(2))

        reply1 = mi.add_photo("file_a")
        assert "1/2" in reply1
        assert not mi.is_complete()

        reply2 = mi.add_photo("file_b")
        assert reply2 == ""  # Tamamlanınca sessiz — complete akışı devralır
        assert mi.is_complete()

    def test_add_photo_without_pending(self):
        assert "bekleyen" in mi.add_photo("file_x").lower()

    def test_cancel(self):
        mi.start_pending("Test topic", "shorts", _scenario(2))
        assert mi.cancel_pending()
        assert mi.load_pending() is None
        assert not mi.cancel_pending()  # İkinci iptal: zaten yok


class TestImagesReady:
    def test_ready_and_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mi, "IMAGES_DIR", tmp_path)
        scenes = _scenario(2)["scenes"]

        assert not mi.images_ready(scenes, vertical=True)

        # Gürültülü görsel — 10KB minimum dosya boyutu kontrolünü geçmesi için
        import os as _os
        for n in (1, 2):
            img = Image.frombytes("RGB", (768, 1344), _os.urandom(768 * 1344 * 3))
            img.save(tmp_path / f"scene_{n:02d}_vertical.png")
        assert mi.images_ready(scenes, vertical=True)
        # Yatay adlar farklı — yatay için hazır sayılmaz
        assert not mi.images_ready(scenes, vertical=False)

    def test_empty_scene_list_not_ready(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mi, "IMAGES_DIR", tmp_path)
        assert not mi.images_ready([], vertical=True)


class TestCenterCrop:
    def _png_bytes(self, w, h):
        buf = io.BytesIO()
        Image.new("RGB", (w, h), color=(200, 30, 30)).save(buf, "PNG")
        return buf.getvalue()

    def test_square_to_vertical(self):
        out = mi.center_crop_to_aspect(self._png_bytes(1024, 1024), 768, 1344)
        assert out.size == (768, 1344)

    def test_wide_to_vertical(self):
        out = mi.center_crop_to_aspect(self._png_bytes(1920, 1080), 768, 1344)
        assert out.size == (768, 1344)

    def test_exact_ratio_no_crop(self):
        out = mi.center_crop_to_aspect(self._png_bytes(1536, 2688), 768, 1344)
        assert out.size == (768, 1344)

    def test_vertical_to_wide(self):
        out = mi.center_crop_to_aspect(self._png_bytes(1080, 1920), 1344, 768)
        assert out.size == (1344, 768)


class TestReminder:
    def test_no_reminder_before_interval(self, isolated_state):
        mi.start_pending("Test topic", "shorts", _scenario(2))
        sent_before = len(isolated_state)
        mi.send_reminder_if_due()
        assert len(isolated_state) == sent_before  # 24 saat geçmedi

    def test_reminder_after_interval(self, isolated_state):
        mi.start_pending("Test topic", "shorts", _scenario(2))
        pending = mi.load_pending()
        pending["last_reminder_at"] = (
            datetime.now(timezone.utc) - timedelta(hours=25)
        ).isoformat()
        mi._save_pending(pending)

        sent_before = len(isolated_state)
        mi.send_reminder_if_due()
        assert len(isolated_state) == sent_before + 1
        assert "Hatırlatma" in isolated_state[-1]
        # Zaman damgası yenilendi — ikinci çağrı tekrar göndermez
        mi.send_reminder_if_due()
        assert len(isolated_state) == sent_before + 1


class TestPhotoRouting:
    def test_telegram_bot_routes_photo(self, tmp_path, monkeypatch, isolated_state):
        import scripts.telegram_bot as tg

        monkeypatch.setattr(tg, "STATE_FILE", tmp_path / "state.json")
        monkeypatch.setattr(tg, "is_configured", lambda: True)
        monkeypatch.setattr(tg, "load_env", lambda: {
            "TELEGRAM_BOT_TOKEN": "TOKEN", "TELEGRAM_CHAT_ID": "42",
        })

        mi.start_pending("Test topic", "shorts", _scenario(3))

        updates = [{
            "update_id": 300,
            "message": {"chat": {"id": 42},
                        "photo": [{"file_id": "small"}, {"file_id": "big"}]},
        }]
        monkeypatch.setattr(tg, "get_updates", lambda token, offset: updates)

        tg_sent = []
        monkeypatch.setattr(tg, "send_message", lambda text, **kw: tg_sent.append(text) or True)

        assert tg.process_pending_commands() == 1
        pending = mi.load_pending()
        assert pending["image_file_ids"] == ["big"]  # En büyük boyut seçildi
        assert any("1/3" in m for m in tg_sent)
