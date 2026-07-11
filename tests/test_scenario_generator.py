"""scenario_generator saf fonksiyon testleri (API gerektirmez)."""

import json

import pytest

from scripts.scenario_generator import (
    validate_scenario, fix_scenario, _extract_json, _scenario_cache_path,
    select_video_scene_numbers, mark_video_scenes,
)


def _valid_scenario():
    return {
        "title": "Test Episode",
        "scenes": [
            {"scene_number": 1, "narration": "Hook text.", "visual_prompt": "A dramatic scene."},
            {"scene_number": 2, "narration": "More text.", "visual_prompt": "Another scene."},
        ],
    }


class TestValidateScenario:
    def test_valid_scenario_passes(self):
        is_valid, errors = validate_scenario(_valid_scenario())
        assert is_valid
        assert errors == []

    def test_missing_title(self):
        scenario = _valid_scenario()
        del scenario["title"]
        is_valid, errors = validate_scenario(scenario)
        assert not is_valid
        assert any("title" in e for e in errors)

    def test_empty_scenes(self):
        is_valid, errors = validate_scenario({"title": "X", "scenes": []})
        assert not is_valid

    def test_missing_narration(self):
        scenario = _valid_scenario()
        del scenario["scenes"][0]["narration"]
        is_valid, errors = validate_scenario(scenario)
        assert not is_valid

    def test_blank_visual_prompt(self):
        scenario = _valid_scenario()
        scenario["scenes"][1]["visual_prompt"] = "   "
        is_valid, errors = validate_scenario(scenario)
        assert not is_valid

    def test_unsorted_scene_numbers(self):
        scenario = _valid_scenario()
        scenario["scenes"][0]["scene_number"] = 5
        is_valid, errors = validate_scenario(scenario)
        assert not is_valid

    def test_non_dict_input(self):
        is_valid, _ = validate_scenario([])
        assert not is_valid


class TestFixScenario:
    def test_adds_missing_scene_numbers(self):
        scenario = {"title": "X", "scenes": [
            {"narration": "a", "visual_prompt": "b"},
            {"narration": "c", "visual_prompt": "d"},
        ]}
        fixed = fix_scenario(scenario)
        assert fixed["scenes"][0]["scene_number"] == 1
        assert fixed["scenes"][1]["scene_number"] == 2

    def test_infers_scene_types(self):
        scenario = {"title": "X", "scenes": [
            {"narration": "a", "visual_prompt": "b"},
            {"narration": "c", "visual_prompt": "d"},
            {"narration": "e", "visual_prompt": "f"},
        ]}
        fixed = fix_scenario(scenario)
        types = [s["scene_type"] for s in fixed["scenes"]]
        assert types == ["hook", "development", "outro"]

    def test_long_mode_default_durations(self):
        scenario = {"title": "X", "scenes": [
            {"narration": "a", "visual_prompt": "b"},
            {"narration": "c", "visual_prompt": "d"},
        ]}
        fixed = fix_scenario(scenario, mode="long")
        assert fixed["scenes"][0]["duration_seconds"] == 30   # hook
        assert fixed["scenes"][1]["duration_seconds"] == 120  # outro/development

    def test_shorts_mode_default_durations(self):
        scenario = {"title": "X", "scenes": [
            {"narration": "a", "visual_prompt": "b"},
            {"narration": "c", "visual_prompt": "d"},
        ]}
        fixed = fix_scenario(scenario, mode="shorts")
        assert fixed["scenes"][0]["duration_seconds"] == 10
        assert fixed["scenes"][1]["duration_seconds"] == 15

    def test_defaults_asset_type_to_image(self):
        scenario = {"title": "X", "scenes": [
            {"narration": "a", "visual_prompt": "b"},
            {"narration": "c", "visual_prompt": "d"},
        ]}
        fixed = fix_scenario(scenario)
        assert all(s["asset_type"] == "image" for s in fixed["scenes"])

    def test_preserves_existing_asset_type(self):
        scenario = {"title": "X", "scenes": [
            {"narration": "a", "visual_prompt": "b", "asset_type": "video"},
        ]}
        fixed = fix_scenario(scenario)
        assert fixed["scenes"][0]["asset_type"] == "video"


class TestSelectVideoScenes:
    def test_character_scenes_stay_image(self):
        scenes = [
            {"scene_number": 1, "visual_prompt": "A steampunk rabbit scientist waves."},
            {"scene_number": 2, "visual_prompt": "A frozen city under heavy snow."},
        ]
        assert select_video_scene_numbers(scenes) == [2]

    def test_caps_at_max_videos(self):
        scenes = [
            {"scene_number": n, "visual_prompt": f"Dramatic scene {n}."}
            for n in range(1, 8)
        ]
        assert select_video_scene_numbers(scenes, max_videos=3) == [1, 2, 3]

    def test_all_character_scenes_returns_empty(self):
        scenes = [
            {"scene_number": 1, "visual_prompt": "The rabbit scientist smiles."},
            {"scene_number": 2, "visual_prompt": "A RABBIT in a lab."},
        ]
        assert select_video_scene_numbers(scenes) == []

    def test_any_rabbit_mention_stays_image(self):
        """Karakter geçen sahne (sonda bile) GÖRSEL kalır — video'ya girmez."""
        scenes = [
            {"scene_number": 1, "visual_prompt": (
                "A desolate frozen Earth landscape at night, giant cracks in a vast "
                "icy ocean, skeletal frost-covered trees, as the rabbit scientist watches."
            )},
            {"scene_number": 2, "visual_prompt": "A pure frozen wasteland, no characters."},
        ]
        assert select_video_scene_numbers(scenes) == [2]

    def test_roli_by_name_stays_image(self):
        """Karakter yalnızca 'Roli' ismiyle anılsa (rabbit kelimesi olmadan) da görsel kalır."""
        scenes = [
            {"scene_number": 1, "visual_prompt": (
                "Roli stands on a dark frozen Earth looking at a rogue planet."
            )},
            {"scene_number": 2, "visual_prompt": "Bioluminescent creatures glowing in the deep sea."},
        ]
        assert select_video_scene_numbers(scenes) == [2]


class TestMarkVideoScenes:
    def test_long_marks_non_character_scenes_video(self):
        scenario = {"scenes": [
            {"scene_number": 1, "visual_prompt": "A rabbit scientist intro."},
            {"scene_number": 2, "visual_prompt": "A frozen wasteland."},
        ]}
        mark_video_scenes(scenario, mode="long")
        types = [s["asset_type"] for s in scenario["scenes"]]
        assert types == ["image", "video"]  # tavşan görsel, diğeri video

    def test_shorts_all_image(self):
        scenario = {"scenes": [
            {"scene_number": 1, "visual_prompt": "A frozen wasteland."},
            {"scene_number": 2, "visual_prompt": "A burning sky."},
        ]}
        mark_video_scenes(scenario, mode="shorts")
        assert all(s["asset_type"] == "image" for s in scenario["scenes"])


class TestExtractJson:
    def test_plain_json(self):
        assert _extract_json('{"a": 1}') == {"a": 1}

    def test_markdown_code_block(self):
        raw = '```json\n{"a": 1}\n```'
        assert _extract_json(raw) == {"a": 1}

    def test_code_block_without_language(self):
        raw = '```\n{"b": [1, 2]}\n```'
        assert _extract_json(raw) == {"b": [1, 2]}

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            _extract_json("not json at all")


class TestCachePath:
    def test_modes_use_separate_caches(self):
        assert _scenario_cache_path("long") != _scenario_cache_path("shorts")
        assert _scenario_cache_path("shorts").name == "scenario_shorts.json"
        assert _scenario_cache_path("long").name == "scenario.json"
