"""Kanal sanatı (banner, profil) testleri."""
import json


def test_channel_art_uses_series_images_and_renders_v2_thumbnails(tmp_path, monkeypatch):
    """Banner/profil seri (Hitit) görselleriyle; v2 kapaklar da üretilip Telegram'a gönderilebilmeli."""
    from scripts import channel_setup as cs
    (tmp_path / "cekim_plani.json").write_text(json.dumps({
        "images": {"tut_maske": {"commons": "File:X.jpg"}, "yerel": {"file": "kapak/y.jpg"}},
        "thumbnails": [{"sablon": "v2", "odak": "tut_maske", "line1": "a", "line2": "b"},
                       {"sablon": "v2", "arka_plan": "yerel", "line1": "c", "line2": "d"}]}), encoding="utf-8")
    (tmp_path / "kapak").mkdir()
    (tmp_path / "kapak" / "y.jpg").write_bytes(b"x")
    fetched = []

    def fake_fetch(plan, keys, out_dir):
        fetched.append(list(keys))
        out_dir.mkdir(parents=True, exist_ok=True)
        res = {}
        for k in keys:
            assert k in plan["images"]
            p = out_dir / f"{k}.jpg"
            p.write_bytes(b"x")
            res[k] = str(p)
        return res

    monkeypatch.setattr(cs, "_fetch", fake_fetch)
    calls = []
    monkeypatch.setattr(cs, "_still", lambda comp, out, props, extra=None: calls.append((comp, props)) or out)
    (tmp_path / "remotion").mkdir()
    monkeypatch.setattr(cs, "REMOTION_DIR", tmp_path / "remotion")
    art = cs.render_art(tmp_path, tmp_path / "out")
    assert fetched == [["buyuk_mabet_3", "aslan_kapi_1"], ["tut_maske"]]   # yerel dosya indirilmez
    assert set(art) == {"banner", "profil", "kapak1", "kapak2"}
    thumbs = [p for c, p in calls if c == "ThumbnailV2"]
    assert thumbs[0]["subject"] == "kanal_tut_maske.jpg" and thumbs[1]["background"] == "kanal_yerel.jpg"


def test_studio_steps_name_the_video():
    from scripts.channel_setup import studio_steps
    text = studio_steps("https://youtu.be/abc", "İstanbul")
    assert "İstanbul videosu" in text and "https://youtu.be/abc" in text and "Hitit" not in text


def test_pick_latest_skips_shorts():
    """Başlığında hedef kelime geçen Short (ör. 'Mısır kraliçesi… #shorts') belgesel sayılmaz."""
    from scripts import channel_setup as cs

    def v(i, title, when, dur):
        return {"id": i, "snippet": {"title": title, "publishedAt": when},
                "status": {"privacyStatus": "private"}, "contentDetails": {"duration": dur}}
    vids = [v("doc", "Antik Mısır'ın Tam Hikâyesi", "2026-11-02T10:00:00Z", "PT33M11S"),
            v("s1", "Mısır kraliçesi Hitit kralından neden koca istedi? #shorts", "2026-11-04T10:00:00Z", "PT1M5S"),
            v("s2", "Mısır'da ilk grev", "2026-11-05T10:00:00Z", "PT59S")]
    latest, older = cs.pick_latest(vids, "Mısır")
    assert latest["id"] == "doc" and older == []
    assert cs._seconds("PT1H2M3S") == 3723 and cs._seconds("") == 0


def test_component_maps_render_with_staged_images(tmp_path, monkeypatch):
    """maps içinde "bilesen" olan girdiler kendi Remotion bileşeniyle render edilir; görseller sahnelenir."""
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    from test_belgesel import _mini_production
    prod = _mini_production(tmp_path)
    prod.data["maps"] = {"fatih": {"bilesen": "PortraitCard", "image": "g1", "name": "II. Mehmed", "role": "Sultan",
                                   "facts": [], "durationSec": 6}}
    calls = []
    monkeypatch.setattr(prod, "_stage_image", lambda key: f"staged_{key}.jpg")
    monkeypatch.setattr(prod, "_remotion", lambda args: calls.append(args))
    prod.stage_kartlar()
    comp_calls = [c for c in calls if c[2] == "PortraitCard"]
    assert len(comp_calls) == 1
    props = json.loads(comp_calls[0][-2].removeprefix("--props="))
    assert props["image"] == "staged_g1.jpg" and "bilesen" not in props
    assert comp_calls[0][3].endswith("maps/fatih.mp4")
