"""Sosyal medya paylaşımı (TikTok/Instagram/Facebook) testleri — ağ çağrıları sahte."""
import json
import subprocess
from pathlib import Path

import pytest

from scripts import social


def test_hashtags_turkish_and_no_shorts():
    tags = social.hashtags(["istanbul'un fethi", "fatih sultan mehmed", "1453", "shorts", "tarih"])
    assert tags[:3] == ["#istanbulunfethi", "#fatihsultanmehmed", "#1453"]
    assert "#shorts" not in tags and tags.count("#tarih") == 1 and "#tarihdosyalari" in tags


def test_caption_has_link_credits_and_limit():
    spec = {"baslik": "Gemiler karadan yürüdü #shorts", "aciklama": "22 Nisan 1453 gecesi."}
    text = social.social_caption(spec, "https://youtu.be/x", ["A — B (CC BY-SA 4.0)", "A — B (CC BY-SA 4.0)", "Video: Pexels"],
                                 ["istanbul'un fethi"], "Temsili canlandırma içerir.")
    assert text.startswith("Gemiler karadan yürüdü\n") and "#shorts" not in text
    assert "https://youtu.be/x" in text and "Tarih Dosyaları" in text and "Temsili" in text
    assert text.count("A — B") == 1 and "Video: Pexels" in text
    long = social.social_caption({"baslik": "x", "aciklama": "y" * 5000}, "u", [], [])
    assert len(long) <= 2200


def test_post_day_prefers_social_date():
    assert social.post_day({"yayin": "2026-11-10T15:00:00Z"}) == "2026-11-10"
    assert social.post_day({"yayin": "2026-11-10T15:00:00Z", "sosyal": "2026-11-20T15:00:00Z"}) == "2026-11-20"


def test_due_posts_by_day_and_by_id(tmp_path):
    for slug, specs in {"01-a": [{"id": "x", "yayin": "2026-11-02T10:00:00Z", "sosyal": "2026-11-20T15:00:00Z"}],
                        "02-b": [{"id": "y", "yayin": "2026-11-20T10:00:00Z"}, {"id": "z", "yayin": "2026-11-21T10:00:00Z"}]}.items():
        d = tmp_path / "belgeseller" / slug
        d.mkdir(parents=True)
        (d / "shorts.json").write_text(json.dumps({"shorts": specs}), encoding="utf-8")
    assert social.due_posts(tmp_path, "2026-11-20") == [{"slug": "01-a", "id": "x"}, {"slug": "02-b", "id": "y"}]
    assert social.due_posts(tmp_path, "1999-01-01", "belgeseller/02-b", "z") == [{"slug": "02-b", "id": "z"}]


def test_transcode_bitrate_fits_telegram_limit():
    cmd = social.transcode_cmd(Path("a.mp4"), Path("b.mp4"), max_mb=45, seconds=60)
    kbps = int(cmd[cmd.index("-maxrate") + 1].rstrip("k"))
    assert (kbps + 160) * 60 / 8 / 1024 < 45          # video + ses, MB
    assert "scale=1080:1920" in cmd[cmd.index("-vf") + 1]


def test_package_writes_manifest(tmp_path):
    src = tmp_path / "s.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=red:s=1080x1920:d=1",
                    "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
                    "-c:v", "libx264", "-c:a", "aac", str(src)], check=True)
    cfg = {"tam_video": "https://youtu.be/v", "etiketler": ["mısır"],
           "shorts": [{"id": "k", "baslik": "Kleopatra #shorts", "aciklama": "Açıklama."}]}
    out = social.package(tmp_path, cfg, [{"id": "k", "video": str(src), "seconds": 1.0,
                                          "credits": ["Müzik: X"], "uses_clip": True}], "YZ notu")
    man = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert man[0]["dosya"] == "k.mp4" and (out / "k.mp4").exists()
    assert man[0]["baslik"] == "Kleopatra" and "YZ notu" in man[0]["aciklama"] and "#mısır" in man[0]["aciklama"]


class FakeResp:
    def __init__(self, data, status=200):
        self._d, self.status_code, self.text = data, status, json.dumps(data)

    def json(self):
        return self._d


def test_instagram_reel_flow(tmp_path, monkeypatch):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"1234")
    calls, states = [], iter(["IN_PROGRESS", "FINISHED"])

    def post(url, data=None, timeout=None, headers=None):
        calls.append((url, data if isinstance(data, dict) else len(data), headers))
        if url.endswith("/media"):
            return FakeResp({"id": "C1", "uri": "https://rupload.facebook.com/ig-api-upload/v21.0/C1"})
        if "rupload" in url:
            return FakeResp({"success": True})
        if url.endswith("/media_publish"):
            return FakeResp({"id": "M9"})
        raise AssertionError(url)

    monkeypatch.setattr(social.requests, "post", post)
    monkeypatch.setattr(social.requests, "get", lambda url, params=None, timeout=None: FakeResp({"status_code": next(states)}))
    monkeypatch.setattr(social.time, "sleep", lambda s: None)
    assert social.instagram_reel(video, "metin", "IG1", "TOK", poll_every=1) == "M9"
    assert calls[0][1]["media_type"] == "REELS" and calls[0][1]["caption"] == "metin"
    assert calls[1][2]["Authorization"] == "OAuth TOK" and calls[1][2]["file_size"] == "4"
    assert calls[2][1]["creation_id"] == "C1"


def test_instagram_error_is_reported(tmp_path, monkeypatch):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"x")
    monkeypatch.setattr(social.requests, "post",
                        lambda *a, **k: FakeResp({"error": {"message": "Invalid OAuth access token"}}, 400))
    with pytest.raises(social.SocialError, match="Invalid OAuth"):
        social.instagram_reel(video, "m", "IG1", "BAD")


def test_facebook_reel_flow(tmp_path, monkeypatch):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"ab")
    seen = []

    def post(url, data=None, timeout=None, headers=None):
        seen.append(data if isinstance(data, dict) else "bytes")
        if url.endswith("/video_reels") and data["upload_phase"] == "start":
            return FakeResp({"video_id": "V1", "upload_url": "https://rupload.facebook.com/video-upload/v21.0/V1"})
        return FakeResp({"success": True})

    monkeypatch.setattr(social.requests, "post", post)
    assert social.facebook_reel(video, "metin", "P1", "TOK") == "V1"
    assert seen[2]["upload_phase"] == "finish" and seen[2]["video_state"] == "PUBLISHED"
    assert seen[2]["description"] == "metin"


def test_share_without_meta_keys_only_telegram(tmp_path, monkeypatch):
    video = tmp_path / "03-x" / "g.mp4"
    monkeypatch.setattr(social, "fetch_package",
                        lambda slug, sid, dest: (video, {"id": sid, "baslik": "B", "aciklama": "A"}))
    sent = []
    from scripts import notifier
    monkeypatch.setattr(notifier, "send_video", lambda p, c="": sent.append(("video", p)) or True)
    monkeypatch.setattr(notifier, "send_message", lambda t, chat_id=None, parse_mode="HTML": sent.append(("msg", t)) or True)
    for k in ("META_PAGE_TOKEN", "META_IG_USER_ID", "META_PAGE_ID"):
        monkeypatch.delenv(k, raising=False)
    r = social.share("03-x", "g", tmp_path)
    assert r["telegram"] and r["instagram"] is None and r["facebook"] is None and not r["hatalar"]
    assert sent == [("video", str(video)), ("msg", "A")]
    assert "anahtarları henüz eklenmedi" in social.summary([r], meta_ready=False)


def test_real_shorts_configs_have_valid_social_dates():
    root = Path(__file__).resolve().parent.parent
    for p in root.glob("belgeseller/*/shorts.json"):
        for s in json.loads(p.read_text(encoding="utf-8"))["shorts"]:
            day = social.post_day(s)
            assert len(day) == 10 and day[4] == "-" and day[7] == "-", (p, s["id"])
