"""
video_assembler.py - FFmpeg ile Video Montaj Motoru.

Üretilen görselleri ve ses dosyalarını birleştirerek final videoyu oluşturur.

Özellikler:
- Ken Burns efektleri (zoom, pan)
- Sahneler arası dip-to-black geçiş (sert kesme + renk sıçramasını yumuşatır)
- SRT altyazı dosyası üretimi
- Arka plan müziği ekleme (varsa)
- Intro/outro kartları
- Detaylı loglama ve hata yönetimi
"""

import subprocess
import json
import shutil
from pathlib import Path

from scripts.utils import (
    print_header, print_step, print_success, print_error,
    print_warning, console, logger,
    AUDIO_DIR, IMAGES_DIR, CLIPS_DIR, OUTPUT_DIR,
    ASSETS_DIR, TEMP_DIR, get_episode_number
)


# ──────────────────────────────────────
# FFmpeg Kontrol
# ──────────────────────────────────────
def check_ffmpeg() -> bool:
    """FFmpeg'in sistemde kurulu olup olmadığını kontrol et."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            # Versiyon bilgisi al
            version_line = result.stdout.split("\n")[0] if result.stdout else "unknown"
            logger.info("FFmpeg bulundu: %s", version_line.strip())
            return True
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        logger.error("FFmpeg bulunamadı!")
        return False


def _run_ffmpeg(cmd: list[str], description: str = "", timeout: int = 600) -> bool:
    """
    FFmpeg komutunu çalıştır ve sonucu logla.

    Args:
        cmd: FFmpeg komut listesi
        description: İşlem açıklaması (loglama için)
        timeout: Maksimum çalışma süresi (saniye)

    Returns:
        bool: Başarılı mı?
    """
    try:
        logger.debug("FFmpeg komutu: %s", " ".join(cmd[:8]) + "...")
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )

        if result.returncode != 0:
            logger.error("FFmpeg hatası (%s): %s", description, result.stderr[-500:] if result.stderr else "N/A")
            return False

        logger.debug("FFmpeg başarılı: %s", description)
        return True

    except subprocess.TimeoutExpired:
        logger.error("FFmpeg zaman aşımı (%ds): %s", timeout, description)
        return False
    except Exception as e:
        logger.error("FFmpeg çalıştırma hatası (%s): %s", description, e)
        return False


# ──────────────────────────────────────
# Sahne Klip Oluşturma
# ──────────────────────────────────────
# Sahneler arası karartma (dip-to-black) geçiş süresi (saniye).
# Sahne sonu karartılır + sonraki sahne karadan açılır → sert kesme ve
# beyaz↔siyah renk sıçraması yumuşar, araya görsel bir "nefes" girer.
SCENE_FADE_DURATION = 0.3


def _scene_fade_filter(
    duration: float,
    fade_in: bool,
    fade_out: bool,
    fade_d: float = SCENE_FADE_DURATION,
) -> str:
    """
    Sahne klibi için karartma (dip-to-black) geçiş filtresi üretir.

    Sahne sonunda video karartılır, bir sonraki sahne karadan açılır; böylece
    sahneler arası sert kesme ve beyaz↔siyah renk sıçraması yumuşar, araya
    görsel bir "nefes" girer. Klip SÜRESİNİ DEĞİŞTİRMEZ (fade, mevcut karelerin
    üstüne uygulanır) → altyazı ve ses senkronu bozulmaz. Çok kısa kliplerde
    fade süresi otomatik küçülür.

    Args:
        duration: Klip süresi (saniye)
        fade_in:  Baştan karadan-açılma uygulansın mı (ilk sahnede kapalı — hook
                  anında vursun)
        fade_out: Sonda karartma uygulansın mı (son sahnede kapalı — final kare
                  kalsın, döngü/loop temiz olsun)
        fade_d:   Geçiş süresi (saniye)

    Returns:
        str: Virgülle birleştirilebilir fade filtre parçası ("" olabilir)
    """
    # Kısa klip güvenliği: giriş + çıkış fade'i klibin ~1/3'ünü geçmesin
    d = max(0.05, min(fade_d, duration / 3.0))
    parts = []
    if fade_in:
        parts.append(f"fade=t=in:st=0:d={d:.3f}")
    if fade_out:
        parts.append(f"fade=t=out:st={max(0.0, duration - d):.3f}:d={d:.3f}")
    return ",".join(parts)


def create_scene_clip(
    image_path: str,
    audio_path: str,
    output_path: str,
    duration: float,
    effect: str = "zoom_in",
    resolution: tuple[int, int] = (1920, 1080),
    fade_in: bool = True,
    fade_out: bool = True,
) -> bool:
    """
    Tek bir sahne klibi oluşturur: görsel + Ken Burns efekti + ses.

    Args:
        image_path: Sahne görseli yolu
        audio_path: Sahne ses dosyası yolu
        output_path: Çıktı klip dosyası yolu
        duration: Klip süresi (saniye)
        effect: Ken Burns efekt tipi
        resolution: (genişlik, yükseklik) — Shorts için (1080, 1920)

    Returns:
        bool: Başarılı mı?
    """
    frames = int(duration * 25)
    width, height = resolution
    size = f"{width}x{height}"
    # Dikey görsellerde ön-ölçekleme yüksekliğe göre yapılmalı (zoompan kalitesi için)
    prescale = "scale=-1:8000" if height > width else "scale=8000:-1"

    # Ken Burns efekt filtreleri
    effects = {
        "zoom_in": (
            f"{prescale},zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)'"
            f":y='ih/2-(ih/zoom/2)':d={frames}:s={size}:fps=25"
        ),
        "zoom_out": (
            f"{prescale},zoompan=z='if(lte(zoom,1.0),1.5,max(1.001,zoom-0.0015))'"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={size}:fps=25"
        ),
        "pan_left": (
            f"{prescale},zoompan=z='1.2':x='if(lte(on,1),(iw-iw/zoom)/2,x-1)'"
            f":y='(ih-ih/zoom)/2':d={frames}:s={size}:fps=25"
        ),
        "pan_right": (
            f"{prescale},zoompan=z='1.2':x='if(lte(on,1),0,x+1)'"
            f":y='(ih-ih/zoom)/2':d={frames}:s={size}:fps=25"
        ),
        "slow_zoom": (
            f"{prescale},zoompan=z='min(zoom+0.0008,1.25)':x='iw/2-(iw/zoom/2)'"
            f":y='ih/2-(ih/zoom/2)':d={frames}:s={size}:fps=25"
        ),
    }

    filter_str = effects.get(effect, effects["zoom_in"])

    # Sahneler arası dip-to-black geçiş (sert kesme + renk sıçramasını yumuşatır)
    fade = _scene_fade_filter(duration, fade_in, fade_out)
    if fade:
        filter_str = f"{filter_str},{fade}"

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
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ac", "2",
        "-ar", "44100",
        "-shortest",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    return _run_ffmpeg(cmd, f"scene clip ({effect})", timeout=300)


# Video varlığı olarak kabul edilen uzantılar (manuel akışta kullanıcı klip gönderir)
VIDEO_ASSET_EXTS = (".mp4", ".mov", ".webm", ".mkv", ".m4v")


def is_video_asset(path: str) -> bool:
    """Verilen dosya bir video klip mi (görsel değil)?"""
    return str(path).lower().endswith(VIDEO_ASSET_EXTS)


def create_scene_clip_from_video(
    video_path: str,
    audio_path: str,
    output_path: str,
    duration: float,
    resolution: tuple[int, int] = (1920, 1080),
    fade_in: bool = True,
    fade_out: bool = True,
) -> bool:
    """
    Kullanıcının ürettiği kısa video klibinden sahne klibi oluşturur.

    Görsel + Ken Burns yerine gerçek videoyu kullanır:
    - Kaynak klibi çözünürlüğü DOLDURACAK şekilde ölçekler ve merkez-kırpar.
    - Klip anlatımdan KISAYSA son kare DONDURULUR (döngü değil — aynı sahnenin
      baştan tekrar oynaması "kalitesiz" görünüyordu; artık son karede beklenir).
      Uzunsa kırpılır. Uzunluk sahne anlatımına (ses süresine) sabitlenir.
    - Ses, sahne anlatımıyla değiştirilir.
    - 25fps + libx264/aac ile üretilir (görsel klipleriyle sorunsuz birleşsin).

    Args:
        video_path: Kaynak video klip yolu
        audio_path: Sahne ses (anlatım) dosyası
        output_path: Çıktı klip yolu
        duration: Hedef süre (saniye) — sahne anlatım süresi
        resolution: (genişlik, yükseklik)

    Returns:
        bool: Başarılı mı?
    """
    width, height = resolution
    # Çözünürlüğü doldur (kenar boşluğu bırakma), tam boyuta kırp, ve klip
    # anlatımdan kısaysa SON KAREYİ DONDUR (tpad clone) — döngü yerine. Sonra
    # -t ile süre anlatıma sabitlenir: klip uzunsa kırpılır, kısaysa son kare
    # kalan süre boyunca donuk durur (aynı sahne tekrar oynamaz).
    vfilter = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},fps=25,setsar=1,"
        f"tpad=stop_mode=clone:stop_duration=30"
    )

    # Sahneler arası dip-to-black geçiş — sert kesme ve beyaz↔siyah renk
    # sıçramasını yumuşatır. -t ile kırpma öncesi uygulanır; fade-out tam
    # sahne sonunda (duration) biter → altyazı/ses senkronu bozulmaz.
    fade = _scene_fade_filter(duration, fade_in, fade_out)
    if fade:
        vfilter = f"{vfilter},{fade}"

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-filter_complex", f"[0:v]{vfilter}[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-t", f"{duration:.3f}",  # Uzunluğu sahne anlatımına sabitle
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ac", "2",
        "-ar", "44100",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    return _run_ffmpeg(cmd, "scene clip (video)", timeout=300)


def probe_duration(path: str) -> float:
    """Medya dosyasının süresini saniye olarak döndür (okunamazsa 0.0)."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=30,
        )
        return float(result.stdout.strip())
    except (ValueError, FileNotFoundError, subprocess.TimeoutExpired, AttributeError):
        logger.warning("Süre okunamadı: %s", path)
        return 0.0


def create_scene_clip_video_then_image(
    video_path: str,
    image_path: str,
    audio_path: str,
    output_path: str,
    duration: float,
    effect: str = "slow_zoom",
    resolution: tuple[int, int] = (1920, 1080),
    fade_in: bool = True,
    fade_out: bool = True,
) -> bool:
    """
    Uzun video sahnesi: önce video klip, klip bitince görselden devam.

    NEDEN: uzun video sahnelerinin anlatımı 30-60 saniye sürüyor ama kullanıcı
    en fazla ~10 saniyelik klip üretebiliyor. Tek klip verilirse kalan 20-50
    saniye donuk kare olarak kalırdı. Bu fonksiyon klibi kendi doğal uzunluğunda
    oynatır, ardından AYNI sahnenin görseline geçip Ken Burns ile anlatımın
    sonuna kadar sürdürür — hareket de olur, donma da olmaz.

    Geçiş, sahneler arası geçişle aynı dilde: klip karararak biter, görsel
    karadan açılır.

    Args:
        video_path: Kullanıcının ~10 sn klibi
        image_path: Aynı sahnenin devam görseli
        audio_path: Sahne anlatımı (toplam süreyi bu belirler)
        duration: Sahne süresi (anlatım uzunluğu)
        effect: Görsel bölüm için Ken Burns efekti

    Returns:
        bool: Başarılı mı?
    """
    width, height = resolution
    vdur = probe_duration(video_path)

    # Klip anlatımı zaten karşılıyorsa görsele hiç gerek yok
    if vdur <= 0 or vdur >= duration - 0.5:
        return create_scene_clip_from_video(
            video_path, audio_path, output_path, duration,
            resolution=resolution, fade_in=fade_in, fade_out=fade_out,
        )

    vpart = min(vdur, duration)
    ipart = max(duration - vpart, 0.5)
    fade_d = min(SCENE_FADE_DURATION, vpart / 3.0, ipart / 3.0)

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    stem = Path(output_path).stem
    seg_v = str(TEMP_DIR / f"{stem}_seg_video.mp4")
    seg_i = str(TEMP_DIR / f"{stem}_seg_image.mp4")

    # 1) Video bölümü — sessiz, klip sonunda karar (görsele geçiş)
    vfilter = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},fps=25,setsar=1"
    )
    vfade = _scene_fade_filter(vpart, fade_in=fade_in, fade_out=True, fade_d=fade_d)
    if vfade:
        vfilter = f"{vfilter},{vfade}"
    if not _run_ffmpeg([
        "ffmpeg", "-y", "-i", video_path,
        "-filter_complex", f"[0:v]{vfilter}[v]",
        "-map", "[v]", "-an",
        "-t", f"{vpart:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", seg_v,
    ], "scene segment (video part)", timeout=300):
        return False

    # 2) Görsel bölümü — sessiz, karadan açılır, Ken Burns ile devam eder
    frames = max(int(ipart * 25), 1)
    size = f"{width}x{height}"
    prescale = "scale=-1:8000" if height > width else "scale=8000:-1"
    kb = (f"{prescale},zoompan=z='min(zoom+0.0008,1.25)':x='iw/2-(iw/zoom/2)'"
          f":y='ih/2-(ih/zoom/2)':d={frames}:s={size}:fps=25")
    ifade = _scene_fade_filter(ipart, fade_in=True, fade_out=fade_out, fade_d=fade_d)
    if ifade:
        kb = f"{kb},{ifade}"
    if not _run_ffmpeg([
        "ffmpeg", "-y", "-loop", "1", "-i", image_path,
        "-filter_complex", f"[0:v]{kb}[v]",
        "-map", "[v]", "-an",
        "-t", f"{ipart:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", seg_i,
    ], "scene segment (image part)", timeout=300):
        return False

    # 3) İki görsel bölümü birleştir + sahne anlatımını bindir
    concat_file = TEMP_DIR / f"{stem}_segments.txt"
    concat_file.write_text(
        f"file '{seg_v}'\nfile '{seg_i}'\n".replace("\\", "/"), encoding="utf-8"
    )
    return _run_ffmpeg([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-i", audio_path,
        "-map", "0:v", "-map", "1:a",
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "44100",
        "-pix_fmt", "yuv420p", output_path,
    ], "scene clip (video→image)", timeout=300)


# ──────────────────────────────────────
# SRT Altyazı Üretimi
# ──────────────────────────────────────
def generate_srt(scenes: list[dict], audio_results: list[dict], max_chars: int = 80) -> Path:
    """
    SRT altyazı dosyası üretir.

    Args:
        scenes: Senaryo sahne listesi
        audio_results: Ses üretim sonuçları (süre bilgileri için)
        max_chars: Altyazı satırı başına maksimum karakter (dikey videoda daha kısa)

    Returns:
        Path: SRT dosya yolu
    """
    srt_path = TEMP_DIR / "subtitles.srt"
    audio_map = {r["scene_number"]: r for r in audio_results}

    current_time = 0.0
    srt_entries = []
    entry_num = 1

    for scene in scenes:
        scene_num = scene.get("scene_number", 0)
        narration = scene.get("narration", "")
        audio_info = audio_map.get(scene_num)

        if not narration or not audio_info:
            continue

        duration = audio_info["duration_seconds"]

        # Metni cümlelere böl
        sentences = _split_into_subtitle_chunks(narration, max_chars=max_chars)

        # Süreyi parça UZUNLUĞUNA orantılı dağıt (eşit dağıtım değil).
        # Kısa parça ("Gone.") ile uzun parça aynı süreyi almasın; böylece
        # altyazı konuşmayla senkron kalır. Ağırlık = boşluksuz karakter sayısı
        # (konuşma süresinin iyi bir yaklaşığı).
        weights = [max(len(s.replace(" ", "")), 1) for s in sentences]
        total_weight = sum(weights)
        # Sahne bitişini birikimli hatadan koru: son parçayı tam sahne sonuna sabitle
        scene_end = current_time + duration

        for idx, (sentence, weight) in enumerate(zip(sentences, weights)):
            start = current_time
            if idx == len(sentences) - 1:
                end = scene_end
            else:
                end = current_time + duration * (weight / total_weight)

            srt_entries.append(
                f"{entry_num}\n"
                f"{_format_srt_time(start)} --> {_format_srt_time(end)}\n"
                f"{sentence}\n"
            )
            entry_num += 1
            current_time = end

    # Dosyaya yaz
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_entries))

    logger.info("SRT altyazı üretildi: %d giriş, %s", entry_num - 1, srt_path)
    return srt_path


def _split_into_subtitle_chunks(text: str, max_chars: int = 80) -> list[str]:
    """Metni altyazı parçalarına böl."""
    import re
    # Cümle sonu işaretlerine göre böl
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current = ""
    for sentence in sentences:
        if len(current + " " + sentence) <= max_chars:
            current = (current + " " + sentence).strip()
        else:
            if current:
                chunks.append(current)
            # Uzun cümleleri kelime bazında böl
            if len(sentence) > max_chars:
                words = sentence.split()
                current = ""
                for word in words:
                    if len(current + " " + word) <= max_chars:
                        current = (current + " " + word).strip()
                    else:
                        if current:
                            chunks.append(current)
                        current = word
            else:
                current = sentence

    if current:
        chunks.append(current)

    return chunks if chunks else [text]


def _format_srt_time(seconds: float) -> str:
    """Saniyeyi SRT zaman formatına çevir: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


# ──────────────────────────────────────
# Klipleri Birleştirme (Crossfade ile)
# ──────────────────────────────────────
def concatenate_clips_with_crossfade(
    clip_paths: list[str],
    output_path: str,
    crossfade_duration: float = 0.5,
) -> bool:
    """
    Klipleri crossfade geçişlerle birleştir.

    Args:
        clip_paths: Klip dosya yolları
        output_path: Çıktı dosya yolu
        crossfade_duration: Geçiş süresi (saniye)

    Returns:
        bool: Başarılı mı?
    """
    if len(clip_paths) == 0:
        return False

    if len(clip_paths) == 1:
        # Tek klip — sadece kopyala
        shutil.copy2(clip_paths[0], output_path)
        return True

    # Çok sayıda klip varsa basit concat kullan (crossfade çok kompleks olabilir)
    if len(clip_paths) > 8:
        return concatenate_clips_simple(clip_paths, output_path)

    # Crossfade filter graph oluştur
    inputs = []
    for clip in clip_paths:
        inputs.extend(["-i", clip])

    n = len(clip_paths)
    filter_parts = []

    # Her klibi hazırla
    for i in range(n):
        filter_parts.append(f"[{i}:v]setpts=PTS-STARTPTS[v{i}];")
        filter_parts.append(f"[{i}:a]asetpts=PTS-STARTPTS[a{i}];")

    # Crossfade zinciri
    if n == 2:
        filter_parts.append(
            f"[v0][v1]xfade=transition=fade:duration={crossfade_duration}:offset=auto[vout];"
        )
        filter_parts.append(
            f"[a0][a1]acrossfade=d={crossfade_duration}[aout]"
        )
    else:
        # 3+ klip için basit concat kullan (xfade zincirleme karmaşık)
        return concatenate_clips_simple(clip_paths, output_path)

    filter_str = "".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_path,
    ]

    return _run_ffmpeg(cmd, "crossfade concat", timeout=600)


def concatenate_clips_simple(clip_paths: list[str], output_path: str) -> bool:
    """Klipleri basit concat ile birleştir (crossfade olmadan)."""
    concat_file = CLIPS_DIR / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in clip_paths:
            safe_path = clip.replace("\\", "/")
            f.write(f"file '{safe_path}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_path,
    ]

    return _run_ffmpeg(cmd, "simple concat", timeout=600)


# ──────────────────────────────────────
# Arka Plan Müziği Ekleme
# ──────────────────────────────────────
def add_background_music(
    video_path: str,
    output_path: str,
    music_volume: float = 0.15,
) -> bool:
    """
    Videoya arka plan müziği ekle (assets/music/ klasöründen).

    Args:
        video_path: Kaynak video
        output_path: Çıktı video
        music_volume: Müzik ses seviyesi (0.0 - 1.0)

    Returns:
        bool: Başarılı mı?
    """
    # Müzik dosyasını bul
    music_files = list(ASSETS_DIR.glob("*.mp3")) + list(ASSETS_DIR.glob("*.wav"))
    if not music_files:
        logger.info("Arka plan müziği bulunamadı, atlanan.")
        return False

    music_path = str(music_files[0])
    logger.info("Arka plan müziği ekleniyor: %s (volume=%.2f)", music_path, music_volume)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-stream_loop", "-1",  # Müziği döngüye al
        "-i", music_path,
        "-filter_complex",
        f"[1:a]volume={music_volume}[bg];"
        f"[0:a][bg]amix=inputs=2:duration=first:dropout_transition=3[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path,
    ]

    return _run_ffmpeg(cmd, "background music", timeout=300)


# ──────────────────────────────────────
# SRT Altyazı Gömme (Hardsub)
# ──────────────────────────────────────
def burn_subtitles(video_path: str, srt_path: str, output_path: str, vertical: bool = False) -> bool:
    """
    SRT altyazıyı videoya göm (hardsub).

    Args:
        video_path: Kaynak video
        srt_path: SRT altyazı dosyası
        output_path: Çıktı video
        vertical: True ise Shorts stili (büyük font, ekran ortası)

    Returns:
        bool: Başarılı mı?
    """
    # Windows yollarını düzelt (FFmpeg subtitles filter'ı için)
    safe_srt = srt_path.replace("\\", "/").replace(":", "\\:")

    if vertical:
        # Shorts: büyük font, ekrana ortalanmış (mobilde altyazı ana odak)
        style = (
            "FontSize=15,FontName=Arial,Bold=1,"
            "PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,"
            "BorderStyle=3,Outline=3,Shadow=1,"
            "MarginV=80,Alignment=2"
        )
    else:
        style = (
            "FontSize=22,FontName=Arial,"
            "PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,"
            "BorderStyle=3,Outline=2,Shadow=1,"
            "MarginV=40,Alignment=2"
        )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"subtitles='{safe_srt}':force_style='{style}'",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "22",
        "-c:a", "copy",
        output_path,
    ]

    return _run_ffmpeg(cmd, "burn subtitles", timeout=600)


# ──────────────────────────────────────
# Ana Montaj Fonksiyonu
# ──────────────────────────────────────
def assemble_video(
    scenes: list[dict],
    audio_results: list[dict],
    image_results: list[dict],
    episode_title: str = "",
    vertical: bool = False,
) -> str:
    """
    Tüm parçaları birleştirerek final videoyu oluşturur.

    Pipeline:
    1. Her sahne için klip oluştur (görsel + ses + Ken Burns)
    2. Klipleri birleştir
    3. SRT altyazı üret ve göm
    4. Arka plan müziği ekle (varsa)

    Args:
        vertical: True ise 1080x1920 dikey Shorts videosu üretilir

    Returns:
        str: Final video dosya yolu
    """
    print_header("🎬 VİDEO MONTAJ MOTORU" + (" — SHORTS (9:16)" if vertical else ""))

    resolution = (1080, 1920) if vertical else (1920, 1080)
    clip_prefix = "short_clip" if vertical else "clip"

    # FFmpeg kontrolü
    if not check_ffmpeg():
        print_error("FFmpeg bulunamadı!")
        print_error("Kurulum: winget install Gyan.FFmpeg")
        return ""

    print_step(1, "FFmpeg bulundu, montaj başlıyor...")

    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Ses ve görsel eşleştirmesi
    audio_map = {r["scene_number"]: r for r in audio_results}
    image_map = {r["scene_number"]: r for r in image_results}

    # Ken Burns efekt döngüsü
    effect_cycle = ["zoom_in", "pan_right", "slow_zoom", "zoom_out", "pan_left"]
    clip_paths = []

    print_step(2, "Sahne klipleri oluşturuluyor...")
    logger.info("Sahne klip üretimi başlıyor: %d sahne", len(scenes))

    for i, scene in enumerate(scenes):
        scene_num = scene.get("scene_number", i + 1)

        audio_info = audio_map.get(scene_num)
        image_info = image_map.get(scene_num)

        if not audio_info or not image_info:
            print_warning(f"Sahne {scene_num}: Ses veya görsel eksik, atlanıyor.")
            logger.warning("Sahne %d: ses veya görsel eksik", scene_num)
            continue

        effect = effect_cycle[i % len(effect_cycle)]
        clip_path = str(CLIPS_DIR / f"{clip_prefix}_{scene_num:02d}.mp4")

        # Sahneler arası dip-to-black geçiş bayrakları: ilk sahne karadan
        # AÇILMAZ (hook ilk karede anında vursun); son sahne karartmaZ (final
        # kare kalsın — loop/kapanış temiz). Aradaki her sahne iki taraftan
        # karartılır → sert kesme ve renk sıçraması yumuşar, araya nefes girer.
        is_first = i == 0
        is_last = i == len(scenes) - 1

        # Resume desteği
        if Path(clip_path).exists() and Path(clip_path).stat().st_size > 10240:
            clip_paths.append(clip_path)
            console.print(f"  🎥 Sahne {scene_num}: [cyan]♻ cached[/cyan]")
            continue

        asset_path = image_info["image_path"]

        # Varlık bir video klip ise Ken Burns yerine klibi doğrudan kullan
        if is_video_asset(asset_path):
            # Aynı sahnenin devam görseli varsa (uzun videoda çift varlık):
            # klip bitince görselden devam et — uzun anlatımda donma olmasın.
            still = Path(asset_path).with_suffix(".png")
            if still.exists() and still.stat().st_size > 10240:
                console.print(
                    f"  🎥 Sahne {scene_num} montajlanıyor (video→görsel)... ", end="")
                success = create_scene_clip_video_then_image(
                    video_path=asset_path,
                    image_path=str(still),
                    audio_path=audio_info["audio_path"],
                    output_path=clip_path,
                    duration=audio_info["duration_seconds"],
                    effect=effect,
                    resolution=resolution,
                    fade_in=not is_first,
                    fade_out=not is_last,
                )
            else:
                console.print(f"  🎥 Sahne {scene_num} montajlanıyor (video klip)... ", end="")
                success = create_scene_clip_from_video(
                    video_path=asset_path,
                    audio_path=audio_info["audio_path"],
                    output_path=clip_path,
                    duration=audio_info["duration_seconds"],
                    resolution=resolution,
                    fade_in=not is_first,
                    fade_out=not is_last,
                )
        else:
            console.print(f"  🎥 Sahne {scene_num} montajlanıyor ({effect})... ", end="")
            success = create_scene_clip(
                image_path=asset_path,
                audio_path=audio_info["audio_path"],
                output_path=clip_path,
                duration=audio_info["duration_seconds"],
                effect=effect,
                resolution=resolution,
                fade_in=not is_first,
                fade_out=not is_last,
            )

        if success:
            clip_paths.append(clip_path)
            console.print("[green]✓[/green]")
        else:
            console.print("[red]✗[/red]")
            logger.error("Sahne %d klip oluşturulamadı", scene_num)

    if not clip_paths:
        print_error("Hiçbir klip oluşturulamadı!")
        return ""

    # ═══════════════════════════════════
    # Klipleri birleştir
    # ═══════════════════════════════════
    print_step(3, "Klipler birleştiriliyor...")
    raw_video_path = str(CLIPS_DIR / f"{clip_prefix}_raw_combined.mp4")
    success = concatenate_clips_simple(clip_paths, raw_video_path)

    if not success:
        print_error("Video birleştirme başarısız!")
        return ""

    current_video = raw_video_path

    # ═══════════════════════════════════
    # SRT altyazı üret ve göm
    # ═══════════════════════════════════
    print_step(4, "Altyazı ekleniyor...")
    srt_path = generate_srt(scenes, audio_results, max_chars=32 if vertical else 80)

    subtitled_path = str(CLIPS_DIR / f"{clip_prefix}_with_subtitles.mp4")
    if burn_subtitles(current_video, str(srt_path), subtitled_path, vertical=vertical):
        current_video = subtitled_path
        console.print("  [green]✓[/green] SRT altyazı gömüldü")
    else:
        print_warning("Altyazı gömme başarısız, altyazısız devam ediliyor.")

    # ═══════════════════════════════════
    # Arka plan müziği (opsiyonel)
    # ═══════════════════════════════════
    music_files = list(ASSETS_DIR.glob("*.mp3")) + list(ASSETS_DIR.glob("*.wav"))
    if music_files:
        print_step(5, "Arka plan müziği ekleniyor...")
        music_path = str(CLIPS_DIR / f"{clip_prefix}_with_music.mp4")
        if add_background_music(current_video, music_path):
            current_video = music_path
            console.print("  [green]✓[/green] Müzik eklendi")
        else:
            print_warning("Müzik ekleme başarısız, müziksiz devam ediliyor.")

    # ═══════════════════════════════════
    # Final dosyayı taşı
    # ═══════════════════════════════════
    output_prefix = "short" if vertical else "episode"
    episode_num = get_episode_number(prefix=output_prefix)
    final_path = str(OUTPUT_DIR / f"{output_prefix}_{episode_num:02d}.mp4")

    try:
        shutil.copy2(current_video, final_path)
    except Exception as e:
        print_error(f"Final video kopyalama hatası: {e}")
        return ""

    # SRT'yi de output'a kopyala
    try:
        srt_output = OUTPUT_DIR / f"{output_prefix}_{episode_num:02d}.srt"
        shutil.copy2(str(srt_path), str(srt_output))
        logger.info("SRT altyazı kopyalandı: %s", srt_output)
    except Exception:
        pass

    # Dosya boyutu
    size_mb = Path(final_path).stat().st_size / (1024 * 1024)

    print_success("Final video hazır!")
    console.print(f"  📹 Video: {final_path}")
    console.print(f"  💾 Boyut: {size_mb:.1f} MB")
    console.print(f"  🎬 Bölüm: {'Short' if vertical else 'Episode'} {episode_num}")

    logger.info(
        "Final video oluşturuldu: %s (%.1f MB, Episode %d)",
        final_path, size_mb, episode_num
    )

    return final_path


# Doğrudan çalıştırma testi
if __name__ == "__main__":
    if check_ffmpeg():
        print_success("FFmpeg kurulu ve çalışıyor!")
    else:
        print_error("FFmpeg bulunamadı. Kurulum gerekli.")
