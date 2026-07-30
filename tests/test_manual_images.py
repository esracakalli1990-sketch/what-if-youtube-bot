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
        assert "GÖRSEL 1/4" in isolated_state[1]
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
        assert "steampunk spacesuit" in isolated_state[1]   # tavşanlı sahne
        assert "steampunk spacesuit" not in isolated_state[2]  # tavşansız sahne

    def test_start_pending_long_includes_thumbnail(self, isolated_state):
        assert mi.start_pending("Test topic", "long", _scenario(5))
        pending = mi.load_pending()
        assert pending["expected_images"] == 6  # 5 sahne + thumbnail
        assert "THUMBNAIL" in isolated_state[-1]


class TestBuildPromptsVideo:
    def test_video_scene_labeled_and_motion_prompt(self):
        scenario = _scenario(2)
        scenario["scenes"][0]["asset_type"] = "image"
        scenario["scenes"][1]["asset_type"] = "video"
        prompts, kinds = mi._build_prompts(scenario, "long")
        # 2 sahne + thumbnail = 3, ikinci sahne video
        assert kinds == ["photo", "video", "photo"]
        assert "VIDEO CLIP" in prompts[1]
        assert "VIDEO CLIP" not in prompts[0]

    def test_roli_video_clip_forbids_lip_movement(self):
        """Roli'li VİDEO klibinde konuşma yasaklanmalı.

        Canlı sorun: kullanıcının ürettiği Roli klibinde Roli konuşuyordu; montajda
        klibin sesi atılıp TTS anlatımı bindiği için dudaklar sözlerle tutmuyor
        (kötü dublaj görüntüsü). Prompt artık ağzın KAPALI kalmasını şart koşar.
        """
        scenario = _scenario(1)
        scenario["scenes"][0]["asset_type"] = "video"
        scenario["scenes"][0]["visual_prompt"] = "Roli the rabbit scientist on the ice"
        prompts, kinds = mi._build_prompts(scenario, "shorts")
        assert kinds == ["video"]
        p = prompts[0]
        assert "MUST NOT SPEAK" in p
        assert "mouth stays" in p and "CLOSED" in p
        assert "no lip movement" in p
        # Karakter tarifi yine de gelmeli (marka tutarlılığı)
        assert "steampunk spacesuit" in p

    def test_non_character_video_clip_has_no_speech_rule(self):
        """Karaktersiz atmosfer klibinde konuşma kuralına gerek yok."""
        scenario = _scenario(1)
        scenario["scenes"][0]["asset_type"] = "video"
        scenario["scenes"][0]["visual_prompt"] = "A collapsing glacier wall"
        prompts, _ = mi._build_prompts(scenario, "shorts")
        assert "MUST NOT SPEAK" not in prompts[0]
        assert "NO characters or people" in prompts[0]

class TestLongVideoAssetPlan:
    """Uzun videoda sahne başına HEM klip HEM devam görseli istenir.

    Uzun video sahneleri 30-60 sn sürüyor; kullanıcı en fazla ~10 sn klip
    üretebiliyor. Tek klip verilirse kalan süre donuk kare olurdu.
    """

    def _long_scenario(self):
        return {
            "title": "T", "clickbait_title": "T!", "thumbnail_concept": "C",
            "scenes": [
                {"scene_number": 1, "narration": "n", "visual_prompt": "A collapsing city",
                 "asset_type": "video"},
                {"scene_number": 2, "narration": "n", "visual_prompt": "Roli the rabbit watches",
                 "asset_type": "image"},
                {"scene_number": 3, "narration": "n", "visual_prompt": "Oceans boiling",
                 "asset_type": "video"},
            ],
        }

    def test_video_scenes_get_paired_image(self):
        plan = mi.build_asset_plan(self._long_scenario(), "long")
        # 2 video sahnesi ×2 + 1 görsel sahnesi + thumbnail = 6
        assert len(plan) == 6
        assert [(p["scene_number"], p["role"]) for p in plan] == [
            (1, "video"), (1, "image"),
            (2, "image"),
            (3, "video"), (3, "image"),
            (None, "thumbnail"),
        ]

    def test_paired_image_prompt_is_still_and_matches_clip(self):
        plan = mi.build_asset_plan(self._long_scenario(), "long")
        pair = plan[1]                       # sahne 1'in devam görseli
        assert pair["kind"] == "photo"
        assert "STILL IMAGE" in pair["prompt"]
        assert "after the video clip ends" in pair["prompt"]
        assert "A collapsing city" in pair["prompt"]   # aynı sahne tarifi

    def test_paired_image_keeps_character_brief(self):
        sc = {"scenes": [{"scene_number": 1, "narration": "n",
                          "visual_prompt": "Roli the rabbit scientist on ice",
                          "asset_type": "video"}]}
        plan = mi.build_asset_plan(sc, "long")
        assert "steampunk spacesuit" in plan[1]["prompt"]

    def test_shorts_get_no_paired_image(self):
        """Short sahneleri ~8 sn; tek klip yeter, çift varlık istenmez."""
        sc = {"scenes": [
            {"scene_number": i + 1, "narration": "n", "visual_prompt": f"V{i}",
             "asset_type": "video"} for i in range(4)
        ]}
        plan = mi.build_asset_plan(sc, "shorts")
        assert len(plan) == 4
        assert all(p["role"] == "video" for p in plan)

    def test_start_pending_stores_slots(self, isolated_state):
        mi.start_pending("T", "long", self._long_scenario())
        pending = mi.load_pending()
        assert pending["expected_images"] == 6
        assert pending["asset_slots"][0] == {"scene_number": 1, "role": "video"}
        assert pending["asset_slots"][1] == {"scene_number": 1, "role": "image"}
        assert pending["asset_slots"][-1]["role"] == "thumbnail"


class TestSlotOrderGuard:
    """Gelen dosyanın türü slotla uyuşmazsa sayılmamalı.

    Canlı hata: kullanıcı görselleri 'dosya olarak' gönderdi, bot onları
    sessizce düşürdü, arkadan gelen videolar boşalan slotlara kaydı ve
    hizalama bozuldu (sahne 2'nin devam görseli yerine sahne 4'ün videosu).
    """

    def _pending_with_slots(self):
        mi._save_pending({
            "topic": "T", "mode": "long", "privacy": "public",
            "scenario": {"scenes": []},
            "expected_images": 4,
            "image_file_ids": [],
            "asset_kinds": [],
            "asset_slots": [
                {"scene_number": 1, "role": "video"},
                {"scene_number": 1, "role": "image"},
                {"scene_number": 2, "role": "video"},
                {"scene_number": None, "role": "thumbnail"},
            ],
        })

    def test_rejects_wrong_kind(self, isolated_state):
        self._pending_with_slots()
        mi.add_video("v1")                       # slot 1 doğru
        reply = mi.add_video("v2")               # slot 2 GÖRSEL bekliyor
        assert "Sıra uyuşmuyor" in reply
        assert "GÖRSEL" in reply and "Sahne 1" in reply
        # Yanlış dosya sayılmamalı
        assert mi.load_pending()["image_file_ids"] == ["v1"]

    def test_accepts_correct_kind(self, isolated_state):
        self._pending_with_slots()
        mi.add_video("v1")
        reply = mi.add_photo("p1")
        assert "Sıra uyuşmuyor" not in reply
        assert mi.load_pending()["image_file_ids"] == ["v1", "p1"]
        assert mi.load_pending()["asset_kinds"] == ["video", "photo"]

    def test_thumbnail_slot_expects_photo(self, isolated_state):
        self._pending_with_slots()
        mi.add_video("v1")
        mi.add_photo("p1")
        mi.add_video("v2")
        reply = mi.add_video("v3")               # thumbnail slotu görsel ister
        assert "Sıra uyuşmuyor" in reply
        assert "THUMBNAIL" in reply

    def test_no_slots_keeps_old_behaviour(self, isolated_state):
        """Slot planı olmayan eski üretimler eskisi gibi çalışmalı."""
        mi._save_pending({
            "topic": "T", "mode": "shorts", "privacy": "public",
            "scenario": {"scenes": []},
            "expected_images": 2,
            "image_file_ids": [], "asset_kinds": [],
        })
        assert "Sıra uyuşmuyor" not in mi.add_video("v1")
        assert "Sıra uyuşmuyor" not in mi.add_photo("p1")


class TestDuplicatePublishGuard:
    """Üst üste binen koşular aynı videoyu iki kez yayınlamamalı.

    Canlı hata: elle tetiklenen koşu 22:18-22:41 arası çalışırken saatlik cron
    22:34'te başladı; ikisi de aynı bekleyen üretimi tamamlanmış görüp AYNI
    videoyu YouTube'a yükledi (2 yayın oldu).
    """

    def _fake_git(self, monkeypatch, responses):
        """git çağrılarını taklit et: (returncode, stdout) döndürür."""
        import subprocess

        def fake_run(cmd, **kw):
            key = cmd[1] if len(cmd) > 1 else ""
            if key == "fetch":
                out = responses.get("fetch", (0, ""))
            elif "pending_production.json" in " ".join(cmd):
                out = responses.get("pending", (0, "{}"))
            else:
                out = responses.get("uploads", (0, "[]"))
            return subprocess.CompletedProcess(cmd, out[0], out[1], "")

        monkeypatch.setattr(subprocess, "run", fake_run)

    def test_blocks_when_pending_gone_remotely(self, monkeypatch):
        """Uzakta bekleyen üretim silinmişse başka koşu tamamlamış demektir."""
        self._fake_git(monkeypatch, {"pending": (1, "")})
        reason = mi._remote_production_taken("konu", "BAŞLIK")
        assert "başka bir koşu" in reason

    def test_blocks_when_same_title_recently_uploaded(self, monkeypatch):
        recent = datetime.now(timezone.utc).isoformat()
        uploads = json.dumps([
            {"video_id": "abc123", "title": "BAŞLIK", "uploaded_at": recent}
        ])
        self._fake_git(monkeypatch, {"pending": (0, "{}"), "uploads": (0, uploads)})
        reason = mi._remote_production_taken("konu", "BAŞLIK")
        assert "zaten yayınlanmış" in reason and "abc123" in reason

    def test_allows_when_upload_is_old(self, monkeypatch):
        old = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        uploads = json.dumps([
            {"video_id": "abc123", "title": "BAŞLIK", "uploaded_at": old}
        ])
        self._fake_git(monkeypatch, {"pending": (0, "{}"), "uploads": (0, uploads)})
        assert mi._remote_production_taken("konu", "BAŞLIK") == ""

    def test_allows_when_title_differs(self, monkeypatch):
        recent = datetime.now(timezone.utc).isoformat()
        uploads = json.dumps([
            {"video_id": "abc123", "title": "BAŞKA VİDEO", "uploaded_at": recent}
        ])
        self._fake_git(monkeypatch, {"pending": (0, "{}"), "uploads": (0, uploads)})
        assert mi._remote_production_taken("konu", "BAŞLIK") == ""

    def test_fails_open_when_git_unavailable(self, monkeypatch):
        """Ağ/git sorunu üretimi durdurmamalı — kanal susmasın."""
        self._fake_git(monkeypatch, {"fetch": (1, "")})
        assert mi._remote_production_taken("konu", "BAŞLIK") == ""


class TestSceneAssetPriority:
    def test_video_wins_when_both_exist(self, tmp_path, monkeypatch):
        """Sahnede hem klip hem görsel varsa VİDEO döndürülmeli.

        Görsel önce döndürülürse montaj klibi hiç kullanmaz.
        """
        monkeypatch.setattr(mi, "IMAGES_DIR", tmp_path)
        (tmp_path / "scene_01.png").write_bytes(b"x" * 20000)
        (tmp_path / "scene_01.mp4").write_bytes(b"y" * 20000)
        assert mi.scene_asset_path(1, vertical=False).suffix == ".mp4"

    def test_image_used_when_no_video(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mi, "IMAGES_DIR", tmp_path)
        (tmp_path / "scene_02.png").write_bytes(b"x" * 20000)
        assert mi.scene_asset_path(2, vertical=False).suffix == ".png"


class TestBuildPromptsVideoExtra:
    def test_shorts_never_video(self):
        scenario = _scenario(3)
        for s in scenario["scenes"]:
            s["asset_type"] = "image"
        prompts, kinds = mi._build_prompts(scenario, "shorts")
        assert kinds == ["photo", "photo", "photo"]

    def test_start_pending_long_labels_video(self, isolated_state):
        scenario = _scenario(2)
        scenario["scenes"][1]["asset_type"] = "video"
        mi.start_pending("T", "long", scenario)
        joined = "\n".join(isolated_state)
        assert "🎬 VİDEO" in joined


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
        assert "GÖRSEL 1" in brief and "Şehir karanlığa" in brief
        assert "GÖRSEL 2" in brief and "Dünya donar" in brief

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

    def test_add_video_records_kind(self, isolated_state):
        # Sahne 1 görsel, sahne 2 video → gönderim sırası slot planına uymalı
        scenario = _scenario(2)
        scenario["scenes"][1]["asset_type"] = "video"
        mi.start_pending("Test topic", "shorts", scenario)

        mi.add_photo("file_a")
        mi.add_video("clip_b")

        pending = mi.load_pending()
        assert pending["image_file_ids"] == ["file_a", "clip_b"]
        assert pending["asset_kinds"] == ["photo", "video"]
        assert mi.is_complete()

    def test_add_video_without_pending(self):
        assert "bekleyen" in mi.add_video("clip_x").lower()

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

    def test_video_asset_counts_as_ready(self, tmp_path, monkeypatch):
        """Sahne varlığı .mp4 olarak gelmişse de hazır sayılmalı."""
        monkeypatch.setattr(mi, "IMAGES_DIR", tmp_path)
        scenes = _scenario(2)["scenes"]

        # Sahne 1 görsel, sahne 2 video klip
        import os as _os
        Image.frombytes("RGB", (768, 1344), _os.urandom(768 * 1344 * 3)).save(
            tmp_path / "scene_01_vertical.png"
        )
        (tmp_path / "scene_02_vertical.mp4").write_bytes(_os.urandom(20000))

        assert mi.images_ready(scenes, vertical=True)


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


class TestCompleteProductionImagesCheckpoint:
    """
    Regresyon testi: manuel modda 'images' checkpoint adımı doğru
    işaretlenmezse main.py ücretli API'yi tekrar çağırır — bu da yalnızca
    .png'yi 'cached' sayıp .mp4 (video) sahnelerini tanımadığı için o
    sahneleri videodan tamamen düşürür (ilk hibrit üretimde yaşanan hata).
    """

    def _png_bytes(self, w=200, h=200):
        import os as _os
        buf = io.BytesIO()
        # Gürültülü içerik: düz renk PNG'si 10KB minimum boyut eşiğinin altında sıkışır
        Image.frombytes("RGB", (w, h), _os.urandom(w * h * 3)).save(buf, "PNG")
        return buf.getvalue()

    def test_images_step_includes_video_and_image_assets(self, tmp_path, monkeypatch, isolated_state):
        monkeypatch.setattr(mi, "IMAGES_DIR", tmp_path / "images")
        monkeypatch.setattr(mi, "TEMP_DIR", tmp_path / "temp")
        mi.IMAGES_DIR.mkdir(parents=True, exist_ok=True)

        scenario = _scenario(2)
        scenario["scenes"][0]["asset_type"] = "image"
        scenario["scenes"][1]["asset_type"] = "video"
        mi.start_pending("T", "long", scenario)

        # Uzun videoda sahne 2 (video) için klip + devam görseli istenir:
        # [s1 görsel, s2 klip, s2 devam görseli, thumbnail] = 4 varlık
        pending = mi.load_pending()
        assert pending["expected_images"] == 4
        pending["image_file_ids"] = ["file_a", "clip_b", "still_b", "thumb_c"]
        pending["asset_kinds"] = ["photo", "video", "photo", "photo"]
        mi._save_pending(pending)

        monkeypatch.setattr(mi, "load_env", lambda: {"TELEGRAM_BOT_TOKEN": "tok"})
        # Çift yayın koruması ayrı test ediliyor; burada varlık eşleştirmesine bak
        monkeypatch.setattr(mi, "_remote_production_taken", lambda *a, **k: "")

        png_bytes = self._png_bytes()
        video_bytes = b"\x00" * 20000

        def fake_download(token, file_id):
            return video_bytes if file_id == "clip_b" else png_bytes

        monkeypatch.setattr(mi, "_download_telegram_file", fake_download)

        captured = {}

        class FakeCheckpoint:
            def start(self, topic):
                pass

            def __init__(self):
                self.data = {}

            def complete_step(self, step, **extra):
                captured[step] = extra

        import scripts.utils as utils_module
        monkeypatch.setattr(utils_module, "PipelineCheckpoint", FakeCheckpoint)

        import main as main_module
        monkeypatch.setattr(main_module, "run_pipeline", lambda *a, **k: None)

        mi.complete_production()

        assert "images" in captured
        results = {r["scene_number"]: r["image_path"] for r in captured["images"]["image_results"]}
        assert results[1].endswith(".png")
        # Sahne 2'de hem klip hem devam görseli var → montaja VİDEO yolu gitmeli
        # (montaj yanındaki .png'yi kendisi bulup klip bitince ona geçer)
        assert results[2].endswith(".mp4")
        assert (mi.IMAGES_DIR / "scene_02.png").exists()   # devam görseli kaydedildi


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
