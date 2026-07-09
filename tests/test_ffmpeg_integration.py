"""Gerçek FFmpeg ile klip üretim entegrasyon testleri.

FFmpeg kurulu değilse otomatik atlanır.
"""

import json
import subprocess

import pytest
from PIL import Image

from scripts.video_assembler import check_ffmpeg, create_scene_clip, burn_subtitles

pytestmark = pytest.mark.skipif(not check_ffmpeg(), reason="FFmpeg kurulu değil")


def _make_image(path, width, height):
    Image.new("RGB", (width, height), color=(30, 60, 120)).save(path)


def _make_audio(path, duration=2):
    """Sine dalgasıyla kısa test sesi üret."""
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
         "-c:a", "libmp3lame", str(path)],
        capture_output=True, check=True,
    )


def _probe_dimensions(path) -> tuple[int, int]:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_streams", "-select_streams", "v:0", str(path)],
        capture_output=True, text=True, check=True,
    )
    stream = json.loads(result.stdout)["streams"][0]
    return stream["width"], stream["height"]


class TestSceneClip:
    def test_horizontal_clip_is_1920x1080(self, tmp_path):
        image = tmp_path / "scene.png"
        audio = tmp_path / "scene.mp3"
        output = tmp_path / "clip.mp4"
        _make_image(image, 1344, 768)
        _make_audio(audio)

        assert create_scene_clip(str(image), str(audio), str(output), duration=2.0)
        assert _probe_dimensions(output) == (1920, 1080)

    def test_vertical_clip_is_1080x1920(self, tmp_path):
        image = tmp_path / "scene_v.png"
        audio = tmp_path / "scene_v.mp3"
        output = tmp_path / "short_clip.mp4"
        _make_image(image, 768, 1344)
        _make_audio(audio)

        assert create_scene_clip(
            str(image), str(audio), str(output),
            duration=2.0, resolution=(1080, 1920),
        )
        assert _probe_dimensions(output) == (1080, 1920)


class TestBurnSubtitles:
    def test_vertical_subtitle_burn(self, tmp_path):
        # Önce kısa dikey klip üret
        image = tmp_path / "scene.png"
        audio = tmp_path / "scene.mp3"
        clip = tmp_path / "clip.mp4"
        _make_image(image, 768, 1344)
        _make_audio(audio)
        assert create_scene_clip(str(image), str(audio), str(clip),
                                 duration=2.0, resolution=(1080, 1920))

        srt = tmp_path / "subs.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:02,000\nTest subtitle\n",
                       encoding="utf-8")

        output = tmp_path / "subtitled.mp4"
        assert burn_subtitles(str(clip), str(srt), str(output), vertical=True)
        assert _probe_dimensions(output) == (1080, 1920)
