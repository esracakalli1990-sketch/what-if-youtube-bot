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


class TestSnapshot:
    def test_no_service_writes_error_field(self, monkeypatch):
        monkeypatch.setattr(analytics, "_analytics_service", lambda: None)
        snap = analytics.build_snapshot(days=14)
        assert snap["error"] and "yt-analytics" in snap["error"]
        assert snap["channel"] == {}
        assert snap["videos"] == []
        assert snap["period_days"] == 14
        assert "generated_at" in snap

    def test_structured_snapshot(self, monkeypatch):
        monkeypatch.setattr(analytics, "_analytics_service", lambda: object())
        monkeypatch.setattr(analytics, "channel_summary", lambda *a, **k: {
            "views": 200, "estimatedMinutesWatched": 150,
            "averageViewDuration": 50, "averageViewPercentage": 48.7,
            "subscribersGained": 6, "subscribersLost": 2, "likes": 9,
            "comments": 3,
        })
        monkeypatch.setattr(analytics, "top_videos_analytics", lambda *a, **k: [
            {"video": "vid1", "views": 120, "averageViewPercentage": 60.2,
             "averageViewDuration": 55, "estimatedMinutesWatched": 100},
        ])
        monkeypatch.setattr(analytics, "load_uploads", lambda: [
            {"video_id": "vid1", "title": "MOON GONE", "kind": "short"},
        ])

        snap = analytics.build_snapshot(days=28)
        assert snap["error"] is None
        assert snap["channel"]["views"] == 200
        assert snap["channel"]["avg_view_percentage"] == 48.7
        assert snap["channel"]["subscribers_gained"] == 6
        assert len(snap["videos"]) == 1
        v = snap["videos"][0]
        assert v["title"] == "MOON GONE" and v["kind"] == "short"
        assert v["views"] == 120 and v["avg_view_percentage"] == 60.2

    def test_snapshot_includes_reach_and_traffic(self, monkeypatch):
        """Gösterim/TO ve trafik kaynağı snapshot'a girmeli.

        Teşhisin kritik verisi: görüntülenme düşükse sebep 'hiç gösterilmiyor'
        mu (gösterim düşük) yoksa 'gösteriliyor ama tıklanmıyor' mu (TO düşük)?
        """
        monkeypatch.setattr(analytics, "_analytics_service", lambda: object())
        monkeypatch.setattr(analytics, "channel_summary", lambda *a, **k: {
            "views": 200, "estimatedMinutesWatched": 150,
            "averageViewDuration": 50, "averageViewPercentage": 48.7,
            "subscribersGained": 6, "subscribersLost": 2, "likes": 9,
            "comments": 3,
        })
        monkeypatch.setattr(analytics, "top_videos_analytics", lambda *a, **k: [])
        monkeypatch.setattr(analytics, "load_uploads", lambda: [])
        monkeypatch.setattr(analytics, "reach_summary", lambda *a, **k: {
            "impressions": 5400, "impressionClickThroughRate": 2.14,
        })
        monkeypatch.setattr(analytics, "traffic_sources", lambda *a, **k: [
            {"insightTrafficSourceType": "SHORTS", "views": 180,
             "estimatedMinutesWatched": 120},
            {"insightTrafficSourceType": "NO_LINK_OTHER", "views": 20,
             "estimatedMinutesWatched": 30},
        ])

        snap = analytics.build_snapshot(days=28)
        assert snap["error"] is None
        assert snap["reach"]["impressions"] == 5400
        assert snap["reach"]["impressionClickThroughRate"] == 2.14
        assert snap["traffic_sources"][0]["source"] == "SHORTS"
        assert snap["traffic_sources"][0]["views"] == 180

    def test_reach_failure_does_not_break_snapshot(self, monkeypatch):
        """Gösterim metrikleri bazı hesaplarda/Shorts'ta desteklenmiyor —
        hata alınsa bile snapshot'ın geri kalanı yazılmalı."""
        monkeypatch.setattr(analytics, "_analytics_service", lambda: object())
        monkeypatch.setattr(analytics, "channel_summary", lambda *a, **k: {
            "views": 200, "estimatedMinutesWatched": 150,
            "averageViewDuration": 50, "averageViewPercentage": 48.7,
            "subscribersGained": 6, "subscribersLost": 2, "likes": 9,
            "comments": 3,
        })
        monkeypatch.setattr(analytics, "top_videos_analytics", lambda *a, **k: [])
        monkeypatch.setattr(analytics, "load_uploads", lambda: [])

        def boom(*a, **k):
            raise RuntimeError("metric not supported")

        monkeypatch.setattr(analytics, "reach_summary", boom)
        monkeypatch.setattr(analytics, "traffic_sources", boom)

        snap = analytics.build_snapshot(days=28)
        assert snap["error"] is None                  # snapshot yine geçerli
        assert snap["channel"]["views"] == 200        # asıl veri korundu
        assert "not supported" in snap["reach"]["error"]
        assert "not supported" in snap["traffic_sources"][0]["error"]

    def test_write_snapshot_creates_file(self, monkeypatch, tmp_path):
        monkeypatch.setattr(analytics, "SNAPSHOT_FILE", tmp_path / "snap.json")
        monkeypatch.setattr(analytics, "_analytics_service", lambda: None)
        path = analytics.write_snapshot(days=7)
        assert path.exists()
        import json
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["period_days"] == 7
        assert data["error"]
