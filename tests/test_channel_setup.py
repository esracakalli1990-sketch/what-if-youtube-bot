

def test_plan_comment_falls_back_to_senaryo(tmp_path):
    import json as _json
    from scripts import channel_setup as cs
    (tmp_path / "cekim_plani.json").write_text(_json.dumps({"maps": {}}), encoding="utf-8")
    (tmp_path / "senaryo.json").write_text(_json.dumps({"ilk_yorum": "Yavuz sorusu"}), encoding="utf-8")
    assert cs._plan_comment(tmp_path) == "Yavuz sorusu"
    assert cs._plan_comment(tmp_path / "yok") is None
