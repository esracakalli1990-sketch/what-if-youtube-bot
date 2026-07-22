"""Büyüme yükseltmeleri testleri: ilk-yorum etkileşimi + TTS ses tutarlılığı."""

import pytest

import scripts.youtube_uploader as yt
import scripts.tts_engine as tts
import scripts.manual_images as mi


# ── Roli marka çıpası (kanonik görünüm korunuyor mu?) ────────────────────
class TestRoliBrand:
    def test_character_brief_has_signature_look(self):
        brief = mi._CHARACTER_BRIEF.lower()
        assert "roli" in brief
        assert "glowing blue pocket-watch" in brief  # imza aksesuar
        assert "amber eyes" in brief
        assert "steampunk" in brief


# ── İlk yorum (etkileşim sorusu) ─────────────────────────────────────────
class TestFirstComment:
    def test_includes_twist_and_question(self):
        scenario = {"scenes": [{"twist_element": "You have 8 minutes to live."}]}
        text = yt._build_first_comment(scenario, "vid123")
        assert text.startswith("🐰")
        assert "You have 8 minutes to live." in text
        assert any(q in text for q in yt._ENGAGEMENT_QUESTIONS)

    def test_deterministic_per_video(self):
        s = {"scenes": [{"twist_element": "X"}]}
        assert yt._build_first_comment(s, "abc") == yt._build_first_comment(s, "abc")

    def test_varies_by_video_id(self):
        # Farklı video_id'ler (çoğunlukla) farklı soru seçer — en az bir fark bekleriz
        s = {"scenes": [{"twist_element": "X"}]}
        qs = {yt._build_first_comment(s, vid) for vid in ("aaa", "bbb", "ccc", "ddd", "eee", "fff")}
        assert len(qs) >= 2

    def test_no_scenario_still_valid(self):
        text = yt._build_first_comment(None, "vid")
        assert text.startswith("🐰")
        assert any(q in text for q in yt._ENGAGEMENT_QUESTIONS)

    def test_no_generic_suggest_topic_cta(self):
        # Eski zayıf CTA kaldırıldı
        text = yt._build_first_comment({"scenes": [{"twist_element": "X"}]}, "v")
        assert "explore next" not in text.lower()


# ── TTS marka sesi tutarlılığı (motor kilitleme) ─────────────────────────
@pytest.fixture
def tts_env(monkeypatch, tmp_path):
    monkeypatch.setattr(tts, "load_env",
                        lambda: {"ELEVENLABS_API_KEY": "k", "CHARACTER_VOICE_ID": "v"})
    monkeypatch.setattr(tts, "ElevenLabs", lambda api_key: object())
    monkeypatch.setattr(tts, "AUDIO_DIR", tmp_path)
    monkeypatch.setattr(tts.time, "sleep", lambda *a, **k: None)


def _install_fake_single(monkeypatch, engine_for_first):
    """_generate_single_audio'yu sahte ile değiştir; force_engine çağrılarını kaydeder."""
    calls = []

    def fake_single(client, voice_id, narration, audio_path,
                    max_retries=3, force_engine=None):
        calls.append(force_engine)
        # İlk çağrıda (auto) verilen motora düş; sonra çağıran kilitler
        eng = engine_for_first if force_engine is None else force_engine
        return {"audio_path": str(audio_path), "duration_seconds": 1.0, "engine": eng}

    monkeypatch.setattr(tts, "_generate_single_audio", fake_single)
    return calls


class TestVoiceConsistency:
    def test_locks_to_edge_when_first_scene_falls_back(self, tts_env, monkeypatch):
        calls = _install_fake_single(monkeypatch, engine_for_first="edge")
        scenes = [{"scene_number": i, "narration": "x"} for i in (1, 2, 3)]
        results = tts.generate_audio(scenes)
        assert len(results) == 3
        # İlk sahne auto (None); gerisi "edge"e kilitli — karışık ses yok
        assert calls == [None, "edge", "edge"]

    def test_locks_to_elevenlabs_when_first_scene_succeeds(self, tts_env, monkeypatch):
        calls = _install_fake_single(monkeypatch, engine_for_first="elevenlabs")
        scenes = [{"scene_number": i, "narration": "x"} for i in (1, 2, 3)]
        results = tts.generate_audio(scenes)
        assert len(results) == 3
        assert calls == [None, "elevenlabs", "elevenlabs"]
