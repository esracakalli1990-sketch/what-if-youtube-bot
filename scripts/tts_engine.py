"""
tts_engine.py - ElevenLabs API ile Seslendirme Motoru.

Senaryo sahnelerinin metin-konuşma dönüşümünü yapar.
Sabit bir karakter sesi (Voice ID) kullanarak tutarlı ses kimliği sağlar.
"""

import time
from pathlib import Path

from elevenlabs import ElevenLabs
from mutagen.mp3 import MP3

from scripts.utils import (
    load_env, print_header, print_step, print_success,
    print_error, console, AUDIO_DIR
)


def generate_audio(scenes: list[dict]) -> list[dict]:
    """
    Her sahne için seslendirme üretir.

    Args:
        scenes: Senaryo sahne listesi (her biri 'narration' alanı içermeli)

    Returns:
        list[dict]: Her sahne için ses dosyası yolu ve süre bilgisi
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

    print_step(2, f"{len(scenes)} sahne için seslendirme üretiliyor...")

    for i, scene in enumerate(scenes):
        scene_num = scene.get("scene_number", i + 1)
        narration = scene.get("narration", "")

        if not narration:
            console.print(f"  [yellow]⚠[/yellow] Sahne {scene_num}: Metin yok, atlanıyor.")
            continue

        console.print(f"  🔊 Sahne {scene_num} seslendiriliyor... ", end="")

        try:
            # ElevenLabs TTS çağrısı
            audio_generator = client.text_to_speech.convert(
                voice_id=voice_id,
                text=narration,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )

            # Ses dosyasını kaydet
            audio_path = AUDIO_DIR / f"scene_{scene_num:02d}.mp3"
            with open(audio_path, "wb") as f:
                for chunk in audio_generator:
                    f.write(chunk)

            # Ses süresini ölç
            audio_info = MP3(str(audio_path))
            duration_seconds = audio_info.info.length

            audio_results.append({
                "scene_number": scene_num,
                "audio_path": str(audio_path),
                "duration_seconds": round(duration_seconds, 2),
            })

            console.print(f"[green]✓[/green] ({duration_seconds:.1f}s)")

            # Rate limit koruması
            time.sleep(0.5)

        except Exception as e:
            print_error(f"Sahne {scene_num} seslendirme hatası: {e}")
            continue

    # Toplam süre
    total_duration = sum(r["duration_seconds"] for r in audio_results)
    print_success(f"Seslendirme tamamlandı!")
    console.print(f"  ⏱️  Toplam ses süresi: [bold]{total_duration:.1f}[/bold] saniye "
                  f"({total_duration / 60:.1f} dakika)")

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
