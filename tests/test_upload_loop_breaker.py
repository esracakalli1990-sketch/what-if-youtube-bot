"""Yükleme döngü-kırıcı ve auth-hata sınıflandırma testleri.

Gerçek YouTube/Telegram çağrısı yok; PENDING_FILE ve send_message izole edilir.
"""

import json

import pytest

import scripts.youtube_uploader as yt
import scripts.manual_images as mi


# ── Auth hata sınıflandırma (youtube_uploader) ───────────────────────────
class TestAuthErrorClassification:
    def test_invalid_grant_is_auth(self):
        assert yt._is_auth_error("invalid_grant: Token has been expired or revoked.")

    def test_revoked_and_expired_are_auth(self):
        assert yt._is_auth_error("The token was revoked")
        assert yt._is_auth_error("expired or revoked")

    def test_network_and_quota_are_not_auth(self):
        assert not yt._is_auth_error("Connection reset by peer")
        assert not yt._is_auth_error("quotaExceeded: daily limit reached")
        assert not yt._is_auth_error("")

    def test_set_and_read_roundtrip(self):
        yt._reset_upload_error()
        assert yt.last_upload_error() == {"message": "", "auth": False}
        yt._set_upload_error("invalid_grant: bla")
        err = yt.last_upload_error()
        assert err["auth"] is True
        assert "invalid_grant" in err["message"]
        yt._set_upload_error("some network blip")
        assert yt.last_upload_error()["auth"] is False


# ── Döngü kırıcı (manual_images) ─────────────────────────────────────────
@pytest.fixture
def isolated_pending(tmp_path, monkeypatch):
    monkeypatch.setattr(mi, "PENDING_FILE", tmp_path / "pending.json")
    sent = []
    monkeypatch.setattr(mi, "send_message", lambda text, *a, **k: sent.append(text) or True)
    return sent


def _write_complete_pending(extra=None):
    """expected=1, 1 dosya gelmiş → is_complete() True olacak bir pending yaz."""
    data = {
        "topic": "What if X?", "mode": "shorts", "privacy": "public",
        "scenario": {"scenes": [{"scene_number": 1}]},
        "expected_images": 1, "image_file_ids": ["fid1"], "asset_kinds": ["photo"],
    }
    if extra:
        data.update(extra)
    mi._save_pending(data)


class TestPausedGuard:
    def test_paused_pending_skips_render(self, isolated_pending, monkeypatch):
        _write_complete_pending({"paused": True})

        # run_pipeline çağrılırsa test patlasın — duraklatılmışken çağrılmamalı
        import main
        monkeypatch.setattr(main, "run_pipeline",
                            lambda *a, **k: pytest.fail("run_pipeline duraklatılmışken çağrıldı"))

        assert mi.complete_production() is False
        # Duraklatılmış üretim mesaj da atmaz (sessiz)
        assert isolated_pending == []


class TestResume:
    def test_resume_no_pending(self, isolated_pending):
        assert "yok" in mi.resume_pending().lower()

    def test_resume_active_pending(self, isolated_pending):
        _write_complete_pending()  # paused değil
        assert "zaten aktif" in mi.resume_pending().lower()

    def test_resume_clears_pause_and_counter(self, isolated_pending):
        _write_complete_pending({"paused": True, "upload_failures": 5})
        msg = mi.resume_pending()
        assert "sürdürül" in msg.lower()
        p = mi.load_pending()
        assert p["paused"] is False
        assert p["upload_failures"] == 0


class TestPauseHelper:
    def test_pause_sets_flag_and_notifies(self, isolated_pending):
        _write_complete_pending()
        p = mi.load_pending()
        mi._pause_pending(p, "duraklatıldı-mesajı")
        assert mi.load_pending()["paused"] is True
        assert isolated_pending == ["duraklatıldı-mesajı"]
