from scripts.video_guncelle import new_description, plan_changes, SIRADAKI


def test_new_description_replaces_old_line_idempotent():
    d = new_description("Merhaba\nKaynaklar", f"{SIRADAKI} A → https://youtu.be/x")
    assert d.startswith(SIRADAKI) and d.endswith("Merhaba\nKaynaklar")
    d2 = new_description(d, f"{SIRADAKI} B → https://youtu.be/y")
    assert d2.count(SIRADAKI) == 1 and "B →" in d2 and d2.endswith("Merhaba\nKaynaklar")


def test_plan_uses_new_title_of_next_video_and_keeps_fields():
    videos = {"a": {"title": "Eski A", "description": "metin", "categoryId": "27", "tags": ["t"]},
              "b": {"title": "Eski B", "description": "", "categoryId": "27"}}
    items = [{"id": "a", "siradaki": "b"}, {"id": "b", "baslik": "Yeni B"}]
    ch = {c["id"]: c for c in plan_changes(items, videos)}
    assert "Yeni B → https://youtu.be/b" in ch["a"]["snippet"]["description"]
    assert ch["a"]["snippet"]["categoryId"] == "27" and ch["a"]["snippet"]["tags"] == ["t"]
    assert ch["b"]["snippet"]["title"] == "Yeni B"


def test_plan_skips_unchanged_and_flags_long_title():
    videos = {"a": {"title": "A", "description": "x"}}
    assert plan_changes([{"id": "a"}], videos) == []
    bad = plan_changes([{"id": "a", "baslik": "x" * 101}], videos)
    assert "hata" in bad[0]
    assert plan_changes([{"id": "z"}], videos)[0]["hata"] == "video bulunamadı"


def test_long_description_gets_short_line():
    videos = {"a": {"title": "A", "description": "x" * 4950}, "b": {"title": "B" * 80, "description": ""}}
    c = plan_changes([{"id": "a", "siradaki": "b"}], videos)[0]
    assert len(c["snippet"]["description"]) <= 5000
    assert c["siradaki"] == f"{SIRADAKI} https://youtu.be/b"
    too_long = plan_changes([{"id": "a", "siradaki": "b"}], {**videos, "a": {"title": "A", "description": "x" * 4990}})
    assert "hata" in too_long[0]
