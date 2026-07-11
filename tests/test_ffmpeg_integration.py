"""Gerçek FFmpeg ile klip üretim entegrasyon testleri.

FFmpeg kurulu değilse otomatik atlanır.
"""

import json
import subprocess

import pytest
from PIL import Image

from scripts.video_assembler import (
    check_ffmpeg, create_scene_clip, create_scene_clip_from_video, burn_subtitles,
)

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


def _make_video(path, width, height, duration=1):
    """Test deseniyle kısa sessiz video klip üret."""
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi",
         "-i", f"testsrc=size={width}x{height}:rate=30:duration={duration}",
         "-pix_fmt", "yuv420p", str(path)],
        capture_output=True, check=True,
    )


def _probe_duration(path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


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


class TestSceneClipFromVideo:
    def test_video_clip_filled_to_resolution(self, tmp_path):
        """Kaynak klip farklı oranda olsa da çıktı tam çözünürlükte olmalı."""
        video = tmp_path / "src.mp4"
        audio = tmp_path / "scene.mp3"
        output = tmp_path / "clip.mp4"
        _make_video(video, 1280, 720, duration=1)
        _make_audio(audio, duration=2)

        assert create_scene_clip_from_video(
            str(video), str(audio), str(output),
            duration=2.0, resolution=(1920, 1080),
        )
        assert _probe_dimensions(output) == (1920, 1080)

    def test_short_clip_loops_to_narration_length(self, tmp_path):
        """1 sn'lik klip, 3 sn'lik anlatımı doldurmak için döngülenmeli."""
        video = tmp_path / "src.mp4"
        audio = tmp_path / "scene.mp3"
        output = tmp_path / "clip.mp4"
        _make_video(video, 1920, 1080, duration=1)
        _make_audio(audio, duration=3)

        assert create_scene_clip_from_video(
            str(video), str(audio), str(output),
            duration=3.0, resolution=(1920, 1080),
        )
        # Uzunluk sahne anlatımına (~3 sn) sabitlenmeli, 1 sn'de kalmamalı
        assert abs(_probe_duration(output) - 3.0) < 0.4


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
