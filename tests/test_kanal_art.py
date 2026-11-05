"""Kanal sanatı (banner, profil) testleri."""
import json


def test_channel_art_uses_series_images_and_skips_v2_thumbnails(tmp_path, monkeypatch):
    """Mısır gibi Hitit görseli olmayan planlarda da banner/profil üretilebilmeli."""
    from scripts import channel_setup as cs
    (tmp_path / "cekim_plani.json").write_text(json.dumps({
        "images": {"tut_maske": {"commons": "File:X.jpg"}},
        "thumbnails": [{"sablon": "v2", "odak": "tut_maske", "line1": "a", "line2": "b"}]}), encoding="utf-8")
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
    monkeypatch.setattr(cs, "_still", lambda comp, out, props, extra=None: out)
    (tmp_path / "remotion").mkdir()
    monkeypatch.setattr(cs, "REMOTION_DIR", tmp_path / "remotion")
    art = cs.render_art(tmp_path, tmp_path / "out")
    assert fetched == [["buyuk_mabet_3", "aslan_kapi_1"]]
    assert set(art) == {"banner", "profil"}


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
