"""
video_assembler.py - FFmpeg ile Video Montaj Motoru.

Üretilen görselleri ve ses dosyalarını birleştirerek final videoyu oluşturur.
Ken Burns efekti, altyazı, arka plan müziği ve geçiş efektleri uygular.
"""

import subprocess
import json
import shutil
from pathlib import Path

from scripts.utils import (
    print_header, print_step, print_success, print_error,
    console, AUDIO_DIR, IMAGES_DIR, CLIPS_DIR, OUTPUT_DIR,
    ASSETS_DIR, get_episode_number
)


def check_ffmpeg() -> bool:
    """FFmpeg'in sistemde kurulu olup olmadığını kontrol et."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def create_scene_clip(
    image_path: str,
    audio_path: str,
    output_path: str,
    duration: float,
    effect: str = "zoom_in"
) -> bool:
    """
    Tek bir sahne klibi oluşturur: görsel + Ken Burns efekti + ses.

    Args:
        image_path: Sahne görseli yolu
        audio_path: Sahne ses dosyası yolu
        output_path: Çıktı klip dosyası yolu
        duration: Klip süresi (saniye)
        effect: Ken Burns efekt tipi (zoom_in, zoom_out, pan_left, pan_right)

    Returns:
        bool: Başarılı mı?
    """
    # Ken Burns efekt filtreleri
    effects = {
        "zoom_in": (
            f"scale=8000:-1,zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)'"
            f":y='ih/2-(ih/zoom/2)':d={int(duration * 25)}:s=1920x1080:fps=25"
        ),
        "zoom_out": (
            f"scale=8000:-1,zoompan=z='if(lte(zoom,1.0),1.5,max(1.001,zoom-0.0015))'"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={int(duration * 25)}:s=1920x1080:fps=25"
        ),
        "pan_left": (
            f"scale=8000:-1,zoompan=z='1.2':x='if(lte(on,1),(iw-iw/zoom)/2,x-1)'"
            f":y='(ih-ih/zoom)/2':d={int(duration * 25)}:s=1920x1080:fps=25"
        ),
        "pan_right": (
            f"scale=8000:-1,zoompan=z='1.2':x='if(lte(on,1),0,x+1)'"
            f":y='(ih-ih/zoom)/2':d={int(duration * 25)}:s=1920x1080:fps=25"
        ),
    }

    filter_str = effects.get(effect, effects["zoom_in"])

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-filter_complex", f"[0:v]{filter_str}[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except Exception as e:
        print_error(f"Klip oluşturma hatası: {e}")
        return False


def add_subtitles_to_clip(
    clip_path: str,
    text: str,
    output_path: str
) -> bool:
    """
    Klibe altyazı ekler.

    Args:
        clip_path: Kaynak klip yolu
        text: Altyazı metni
        output_path: Çıktı yolu

    Returns:
        bool: Başarılı mı?
    """
    # Uzun metinleri böl (her satır max 60 karakter)
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line + " " + word) > 60:
            lines.append(current_line.strip())
            current_line = word
        else:
            current_line += " " + word
    if current_line.strip():
        lines.append(current_line.strip())

    subtitle_text = "\\n".join(lines[-2:])  # Son 2 satır
    # FFmpeg drawtext için özel karakterleri escape et
    subtitle_text = subtitle_text.replace("'", "'\\''").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y",
        "-i", clip_path,
        "-vf", (
            f"drawtext=text='{subtitle_text}'"
            f":fontsize=42:fontcolor=white:borderw=3:bordercolor=black"
            f":x=(w-text_w)/2:y=h-th-80"
            f":font='Arial'"
        ),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "copy",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except Exception as e:
        print_error(f"Altyazı ekleme hatası: {e}")
        return False


def concatenate_clips(clip_paths: list[str], output_path: str) -> bool:
    """
    Klipleri sırayla birleştirerek final videoyu oluşturur.

    Args:
        clip_paths: Birleştirilecek klip dosya yolları
        output_path: Final video çıktı yolu

    Returns:
        bool: Başarılı mı?
    """
    # Concat dosyası oluştur
    concat_file = CLIPS_DIR / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in clip_paths:
            # Windows yollarını düzelt
            safe_path = clip.replace("\\", "/")
            f.write(f"file '{safe_path}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return result.returncode == 0
    except Exception as e:
        print_error(f"Video birleştirme hatası: {e}")
        return False


def assemble_video(
    scenes: list[dict],
    audio_results: list[dict],
    image_results: list[dict],
    episode_title: str = ""
) -> str:
    """
    Tüm parçaları birleştirerek final videoyu oluşturur.

    Args:
        scenes: Senaryo sahne listesi
        audio_results: Ses üretim sonuçları
        image_results: Görsel üretim sonuçları
        episode_title: Bölüm başlığı

    Returns:
        str: Final video dosya yolu
    """
    print_header("🎬 VİDEO MONTAJ MOTORU")

    # FFmpeg kontrolü
    if not check_ffmpeg():
        print_error("FFmpeg bulunamadı!")
        print_error("FFmpeg'i https://ffmpeg.org adresinden indirip PATH'e ekleyin.")
        print_error("Veya: winget install FFmpeg")
        return ""

    print_step(1, "FFmpeg bulundu, montaj başlıyor...")

    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Ses ve görsel eşleştirmesi
    audio_map = {r["scene_number"]: r for r in audio_results}
    image_map = {r["scene_number"]: r for r in image_results}

    # Ken Burns efekt döngüsü
    effect_cycle = ["zoom_in", "pan_right", "zoom_out", "pan_left"]
    clip_paths = []

    print_step(2, "Sahne klipleri oluşturuluyor...")

    for i, scene in enumerate(scenes):
        scene_num = scene.get("scene_number", i + 1)

        audio_info = audio_map.get(scene_num)
        image_info = image_map.get(scene_num)

        if not audio_info or not image_info:
            console.print(f"  [yellow]⚠[/yellow] Sahne {scene_num}: Ses veya görsel eksik, atlanıyor.")
            continue

        effect = effect_cycle[i % len(effect_cycle)]
        clip_path = str(CLIPS_DIR / f"clip_{scene_num:02d}.mp4")

        console.print(f"  🎥 Sahne {scene_num} montajlanıyor ({effect})... ", end="")

        success = create_scene_clip(
            image_path=image_info["image_path"],
            audio_path=audio_info["audio_path"],
            output_path=clip_path,
            duration=audio_info["duration_seconds"],
            effect=effect,
        )

        if success:
            # Altyazı ekle
            sub_path = str(CLIPS_DIR / f"clip_{scene_num:02d}_sub.mp4")
            narration = scene.get("narration", "")
            if narration and add_subtitles_to_clip(clip_path, narration, sub_path):
                clip_paths.append(sub_path)
            else:
                clip_paths.append(clip_path)
            console.print("[green]✓[/green]")
        else:
            console.print("[red]✗[/red]")

    if not clip_paths:
        print_error("Hiçbir klip oluşturulamadı!")
        return ""

    # Final birleştirme
    print_step(3, "Final video oluşturuluyor...")

    episode_num = get_episode_number()
    final_path = str(OUTPUT_DIR / f"episode_{episode_num:02d}.mp4")

    success = concatenate_clips(clip_paths, final_path)

    if success:
        # Dosya boyutu
        size_mb = Path(final_path).stat().st_size / (1024 * 1024)
        print_success(f"Final video hazır!")
        console.print(f"  📹 Dosya: {final_path}")
        console.print(f"  💾 Boyut: {size_mb:.1f} MB")
        console.print(f"  🎬 Bölüm: Episode {episode_num}")
        return final_path
    else:
        print_error("Final video oluşturulamadı!")
        return ""


# Doğrudan çalıştırma testi
if __name__ == "__main__":
    if check_ffmpeg():
        print_success("FFmpeg kurulu ve çalışıyor!")
    else:
        print_error("FFmpeg bulunamadı. Kurulum gerekli.")
