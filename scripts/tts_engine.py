"""
tts_engine.py - ElevenLabs API ile Seslendirme Motoru.

Senaryo sahnelerinin metin-konuşma dönüşümünü yapar.
Sabit bir karakter sesi (Voice ID) kullanarak tutarlı ses kimliği sağlar.

Özellikler:
- Retry with exponential backoff
- Rate limit koruması (otomatik bekleme)
- Kısmi başarı desteği (bazı sahneler başarısız olsa pipeline devam eder)
- Ses dosyası bütünlük kontrolü
- Detaylı loglama
"""

import time
import subprocess
from pathlib import Path

from elevenlabs import ElevenLabs
from mutagen.mp3 import MP3

from scripts.utils import (
    load_env, print_header, print_step, print_success,
    print_error, print_warning, console, logger,
    retry, create_progress_bar, AUDIO_DIR
)


def _validate_audio_file(audio_path: Path) -> bool:
    """
    Ses dosyasının geçerli olup olmadığını kontrol et.

    Returns:
        bool: Dosya geçerli mi?
    """
    try:
        if not audio_path.exists():
            return False

        # Minimum dosya boyutu kontrolü (1KB — boş/bozuk dosyaları yakala)
        if audio_path.stat().st_size < 1024:
            logger.warning("Ses dosyası çok küçük: %s (%d bytes)",
                           audio_path, audio_path.stat().st_size)
            return False

        # MP3 metadata okumayı dene
        audio_info = MP3(str(audio_path))
        if audio_info.info.length < 0.5:
            logger.warning("Ses dosyası çok kısa: %s (%.2fs)",
                           audio_path, audio_info.info.length)
            return False

        return True
    except Exception as e:
        logger.warning("Ses dosyası doğrulama hatası: %s — %s", audio_path, e)
        return False


def _generate_with_edge_tts(narration: str, audio_path: Path) -> bool:
    """
    Ücretsiz edge-tts fallback kullanarak ses üretir.
    """
    try:
        # Uygun bir yetişkin erkek sesi (Bilim adamı karakterine yakın)
        voice = "en-GB-RyanNeural" 
        cmd = [
            "edge-tts", 
            "--voice", voice, 
            "--text", narration, 
            "--write-media", str(audio_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if result.returncode == 0 and audio_path.exists():
            return True
        else:
            logger.warning("edge-tts hatası: %s", result.stderr)
            return False
    except Exception as e:
        logger.warning("edge-tts çalışma hatası: %s", e)
        return False


def _generate_single_audio(
    client: ElevenLabs,
    voice_id: str,
    narration: str,
    audio_path: Path,
    max_retries: int = 3,
) -> dict | None:
    """
    Tek bir sahne için seslendirme üret (retry mekanizmalı).

    Returns:
        dict | None: Başarılı ise ses bilgisi, değilse None
    """
    for attempt in range(1, max_retries + 1):
        try:
            # ElevenLabs TTS çağrısı
            audio_generator = client.text_to_speech.convert(
                voice_id=voice_id,
                text=narration,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )

            # Ses dosyasını kaydet
            with open(audio_path, "wb") as f:
                for chunk in audio_generator:
                    f.write(chunk)

            # Bütünlük kontrolü
            if not _validate_audio_file(audio_path):
                raise ValueError(f"Ses dosyası bütünlük kontrolünden geçemedi: {audio_path}")

            # Süre bilgisini al
            audio_info = MP3(str(audio_path))
            duration_seconds = audio_info.info.length

            logger.info("Ses üretildi: %s (%.1fs)", audio_path.name, duration_seconds)
            return {
                "audio_path": str(audio_path),
                "duration_seconds": round(duration_seconds, 2),
            }

        except Exception as e:
            logger.warning(
                "Ses üretim hatası (deneme %d/%d): %s — %s",
                attempt, max_retries, audio_path.name, e
            )

            # Bozuk dosyayı temizle
            if audio_path.exists():
                audio_path.unlink()

            if attempt < max_retries:
                delay = 2 ** attempt
                console.print(f"  [yellow]⚠ Deneme {attempt}/{max_retries} başarısız. "
                              f"{delay}s bekleniyor...[/yellow]")
                time.sleep(delay)
            else:
                logger.warning("ElevenLabs %d denemeden sonra başarısız: %s",
                             max_retries, audio_path.name)
                
    # Fallback: edge-tts
    logger.info("ElevenLabs başarısız, edge-tts (ücretsiz) deneniyor: %s", audio_path.name)
    console.print("  🔄 edge-tts (ücretsiz) ile deneniyor...")
    if _generate_with_edge_tts(narration, audio_path):
        if _validate_audio_file(audio_path):
            audio_info = MP3(str(audio_path))
            duration_seconds = audio_info.info.length
            logger.info("Ses üretildi (edge-tts): %s (%.1fs)", audio_path.name, duration_seconds)
            return {
                "audio_path": str(audio_path),
                "duration_seconds": round(duration_seconds, 2),
            }

    logger.error("Tüm ses üretim yöntemleri başarısız oldu: %s", audio_path.name)
    return None


def generate_audio(scenes: list[dict]) -> list[dict]:
    """
    Her sahne için seslendirme üretir.

    Args:
        scenes: Senaryo sahne listesi (her biri 'narration' alanı içermeli)

    Returns:
        list[dict]: Her sahne için ses dosyası yolu ve süre bilgisi
                    (kısmi başarı durumunda başarılı olanlar döner)
    """
    print_header("🎤 SESLENDİRME MOTORU")
    print_step(1, "ElevenLabs API'ye bağlanılıyor...")

    # API anahtarını yükle
    keys = load_env()
    api_key = keys.get("ELEVENLABS_API_KEY")
    voice_id = keys.get("CHARACTER_VOICE_ID")

    if not api_key or api_key == "buraya_elevenlabs_api_key_gelecek":
        print_error("ELEVENLABS_API_KEY .env dosyasında tanımlı değil!")
        print_error("Lütfen https://elevenlabs.io adresinden API key alın.")
        return []

    if not voice_id or voice_id == "buraya_voice_id_gelecek":
        print_error("CHARACTER_VOICE_ID .env dosyasında tanımlı değil!")
        print_error("ElevenLabs panelinden bir ses seçip ID'sini .env'ye ekleyin.")
        return []

    # ElevenLabs istemcisini başlat
    client = ElevenLabs(api_key=api_key)

    # Ses dosyalarını sakla
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    audio_results = []
    failed_scenes = []

    total_scenes = len(scenes)
    print_step(2, f"{total_scenes} sahne için seslendirme üretiliyor...")
    logger.info("Seslendirme başlıyor: %d sahne", total_scenes)

    for i, scene in enumerate(scenes):
        scene_num = scene.get("scene_number", i + 1)
        narration = scene.get("narration", "")

        if not narration:
            print_warning(f"Sahne {scene_num}: Metin yok, atlanıyor.")
            logger.warning("Sahne %d: narration alanı boş, atlandı.", scene_num)
            continue

        console.print(f"  🔊 Sahne {scene_num}/{total_scenes} seslendiriliyor... ", end="")

        audio_path = AUDIO_DIR / f"scene_{scene_num:02d}.mp3"

        # Daha önce üretilmiş mi? (resume desteği)
        if audio_path.exists() and _validate_audio_file(audio_path):
            audio_info = MP3(str(audio_path))
            duration = audio_info.info.length
            audio_results.append({
                "scene_number": scene_num,
                "audio_path": str(audio_path),
                "duration_seconds": round(duration, 2),
            })
            console.print(f"[cyan]♻ cached[/cyan] ({duration:.1f}s)")
            logger.info("Sahne %d: Cached ses kullanılıyor (%.1fs)", scene_num, duration)
            continue

        result = _generate_single_audio(
            client=client,
            voice_id=voice_id,
            narration=narration,
            audio_path=audio_path,
        )

        if result:
            result["scene_number"] = scene_num
            audio_results.append(result)
            console.print(f"[green]✓[/green] ({result['duration_seconds']:.1f}s)")
        else:
            failed_scenes.append(scene_num)
            console.print("[red]✗ başarısız[/red]")

        # Rate limit koruması — her istek arasında kısa bekleme
        if i < total_scenes - 1:
            time.sleep(1.0)

    # Sonuç özeti
    total_duration = sum(r["duration_seconds"] for r in audio_results)

    console.print()
    if audio_results:
        print_success(f"Seslendirme tamamlandı! ({len(audio_results)}/{total_scenes} sahne)")
        console.print(f"  ⏱️  Toplam ses süresi: [bold]{total_duration:.1f}[/bold] saniye "
                      f"({total_duration / 60:.1f} dakika)")

    if failed_scenes:
        print_warning(f"Başarısız sahneler: {failed_scenes}")
        logger.warning("Başarısız sahneler: %s", failed_scenes)

    if not audio_results:
        print_error("Hiçbir sahne seslendirilemedi!")

    logger.info(
        "Seslendirme sonucu: %d/%d başarılı, toplam süre: %.1fs",
        len(audio_results), total_scenes, total_duration
    )

    return audio_results


def list_available_voices() -> list[dict]:
    """Kullanılabilir ElevenLabs seslerini listele."""
    keys = load_env()
    api_key = keys.get("ELEVENLABS_API_KEY")

    if not api_key or api_key == "buraya_elevenlabs_api_key_gelecek":
        print_error("ELEVENLABS_API_KEY tanımlı değil!")
        return []

    client = ElevenLabs(api_key=api_key)

    try:
        response = client.voices.get_all()
        voices = []
        for voice in response.voices:
            voices.append({
                "voice_id": voice.voice_id,
                "name": voice.name,
                "category": voice.category,
            })
            console.print(f"  🎙️ {voice.name} ({voice.category}) → ID: {voice.voice_id}")
        return voices
    except Exception as e:
        print_error(f"Ses listesi alınamadı: {e}")
        return []


# Doğrudan çalıştırma testi
if __name__ == "__main__":
    from scripts.utils import ensure_directories
    ensure_directories()

    # Test: Mevcut sesleri listele
    print_header("Kullanılabilir Sesler")
    list_available_voices()
