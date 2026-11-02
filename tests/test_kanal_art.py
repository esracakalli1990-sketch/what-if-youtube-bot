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
