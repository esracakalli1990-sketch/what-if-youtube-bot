"""Derin analitik (YouTube Analytics API) rapor testleri.

Gerçek API çağrılmaz; servis ve load_uploads monkeypatch'lenir.
"""

import pytest

import scripts.analytics as analytics


class TestFmtDuration:
    def test_seconds_to_mmss(self):
        assert analytics._fmt_duration(42) == "0:42"
        assert analytics._fmt_duration(125) == "2:05"

    def test_invalid_returns_zero(self):
        assert analytics._fmt_duration(None) == "0:00"
        assert analytics._fmt_duration("abc") == "0:00"


class TestNum:
    def test_parses_numbers(self):
        assert analytics._num("12") == 12.0
        assert analytics._num(3.5) == 3.5

    def test_none_and_bad_are_zero(self):
        assert analytics._num(None) == 0.0
        assert analytics._num("x") == 0.0


class TestBuildDeepReport:
    def test_no_service_returns_reauth_hint(self, monkeypatch):
        monkeypatch.setattr(analytics, "_analytics_service", lambda: None)
        out = analytics.build_deep_report()
        assert "yt-analytics.readonly" in out
        assert "youtube_token.pickle" in out

    def test_scope_error_returns_reauth_hint(self, monkeypatch):
        monkeypatch.setattr(analytics, "_analytics_service", lambda: object())

        def boom(*a, **k):
            raise RuntimeError("Request had insufficient authentication scopes")

        monkeypatch.setattr(analytics, "channel_summary", boom)
        out = analytics.build_deep_report()
        assert "ek yetki" in out.lower() or "yt-analytics" in out

    def test_generic_error_surfaced(self, monkeypatch):
        monkeypatch.setattr(analytics, "_analytics_service", lambda: object())

        def boom(*a, **k):
            raise RuntimeError("network exploded")

        monkeypatch.setattr(analytics, "channel_summary", boom)
        out = analytics.build_deep_report()
        assert "çekilemedi" in out.lower()
        assert "network exploded" in out

    def test_formats_channel_and_videos(self, monkeypatch):
        monkeypatch.setattr(analytics, "_analytics_service", lambda: object())
        monkeypatch.setattr(analytics, "channel_summary", lambda *a, **k: {
            "views": 120,
            "estimatedMinutesWatched": 90,
            "averageViewDuration": 45,
            "averageViewPercentage": 55,
            "subscribersGained": 4,
            "subscribersLost": 1,
            "likes": 7,
        })
        monkeypatch.setattr(analytics, "top_videos_analytics", lambda *a, **k: [
            {"video": "abc123", "views": 80, "averageViewPercentage": 62},
            {"video": "def456", "views": 40, "averageViewPercentage": 20},
        ])
        monkeypatch.setattr(analytics, "load_uploads", lambda: [
            {"video_id": "abc123", "title": "THE MOON VANISHED", "kind": "short"},
            {"video_id": "def456", "title": "WHAT IF THE SUN VANISHED", "kind": "long"},
        ])

        out = analytics.build_deep_report(days=28)
        assert "son 28 gün" in out
        assert "120" in out                       # kanal izlenme
        assert "%55 tamamlanma" in out            # kanal retention
        assert "net +3" in out                    # abone net
        assert "THE MOON VANISHED" in out         # video başlığı eşleşti
        assert "📱" in out and "🎞" in out         # short + long ikonu
        assert "80 izlenme" in out

    def test_zero_views_note(self, monkeypatch):
        monkeypatch.setattr(analytics, "_analytics_service", lambda: object())
        monkeypatch.setattr(analytics, "channel_summary", lambda *a, **k: {
            "views": 0, "estimatedMinutesWatched": 0, "averageViewDuration": 0,
            "averageViewPercentage": 0, "subscribersGained": 0,
            "subscribersLost": 0, "likes": 0,
        })
        monkeypatch.setattr(analytics, "top_videos_analytics", lambda *a, **k: [])
        monkeypatch.setattr(analytics, "load_uploads", lambda: [])

        out = analytics.build_deep_report()
        assert "dağıtım almadı" in out
        assert "soğuk" in out

    def test_low_retention_note(self, monkeypatch):
        monkeypatch.setattr(analytics, "_analytics_service", lambda: object())
        monkeypatch.setattr(analytics, "channel_summary", lambda *a, **k: {
            "views": 50, "estimatedMinutesWatched": 5, "averageViewDuration": 6,
            "averageViewPercentage": 12, "subscribersGained": 0,
            "subscribersLost": 0, "likes": 0,
        })
        monkeypatch.setattr(analytics, "top_videos_analytics", lambda *a, **k: [])
        monkeypatch.setattr(analytics, "load_uploads", lambda: [])

        out = analytics.build_deep_report()
        assert "retention" in out.lower()
