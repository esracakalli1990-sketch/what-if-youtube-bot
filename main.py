"""
main.py - What-If YouTube Bot Ana Orkestratör.

Tek komutla konu al → senaryo yaz → seslendir → görsel üret → montajla → video çıkar.

Kullanım:
    python main.py "What would happen if the Sun suddenly went out?"
    python main.py --character   # Sadece karakter referans görseli üret
    python main.py --test        # Sistem kontrolü çalıştır
"""

import sys
import time
from pathlib import Path

from scripts.utils import (
    ensure_directories, clean_temp, print_header,
    print_step, print_success, print_error, console, load_env
)
from scripts.scenario_generator import generate_scenario, load_scenario
from scripts.tts_engine import generate_audio
from scripts.image_generator import generate_images, generate_character_reference
from scripts.video_assembler import assemble_video, check_ffmpeg


def run_pipeline(topic: str):
    """
    Tam video üretim pipeline'ını çalıştır.

    1. Senaryo üretimi (Gemini Pro)
    2. Seslendirme (ElevenLabs)
    3. Görsel üretimi (Stable Diffusion / Replicate)
    4. Video montaj (FFmpeg)
    """
    start_time = time.time()

    print_header("🚀 WHAT-IF YOUTUBE BOT - OTONOM VİDEO ÜRETİM")
    console.print(f"  📌 Konu: [bold cyan]{topic}[/bold cyan]")
    console.print(f"  ⏰ Başlangıç: {time.strftime('%H:%M:%S')}")
    console.print()

    # Dizinleri hazırla
    ensure_directories()
    clean_temp()

    # ═══════════════════════════════════════
    # ADIM 1: SENARYO ÜRETİMİ
    # ═══════════════════════════════════════
    scenario = generate_scenario(topic)
    if not scenario:
        print_error("Pipeline durdu: Senaryo üretilemedi.")
        return

    scenes = scenario.get("scenes", [])
    if not scenes:
        print_error("Pipeline durdu: Senaryoda sahne bulunamadı.")
        return

    title = scenario.get("title", "Untitled Episode")

    # ═══════════════════════════════════════
    # ADIM 2: SESLENDİRME
    # ═══════════════════════════════════════
    audio_results = generate_audio(scenes)
    if not audio_results:
        print_error("Pipeline durdu: Seslendirme yapılamadı.")
        return

    # ═══════════════════════════════════════
    # ADIM 3: GÖRSEL ÜRETİMİ
    # ═══════════════════════════════════════
    image_results = generate_images(scenes)
    if not image_results:
        print_error("Pipeline durdu: Görseller üretilemedi.")
        return

    # ═══════════════════════════════════════
    # ADIM 4: VİDEO MONTAJ
    # ═══════════════════════════════════════
    final_video = assemble_video(scenes, audio_results, image_results, title)

    if final_video:
        elapsed = time.time() - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        console.print()
        print_header("🎉 VİDEO ÜRETİMİ TAMAMLANDI!")
        console.print(f"  📹 Video: [bold green]{final_video}[/bold green]")
        console.print(f"  📝 Başlık: [bold]{title}[/bold]")
        console.print(f"  ⏱️  Toplam süre: {minutes}dk {seconds}sn")
        console.print()
        console.print("[bold cyan]YouTube'a yüklemeye hazır! 🚀[/bold cyan]")
    else:
        print_error("Video üretimi başarısız oldu.")


def run_system_check():
    """Tüm bağımlılıkları ve API bağlantılarını kontrol et."""
    print_header("🔍 SİSTEM KONTROLÜ")

    all_ok = True

    # Python modülleri
    print_step(1, "Python modülleri kontrol ediliyor...")
    modules = [
        ("google.genai", "google-genai"),
        ("replicate", "replicate"),
        ("elevenlabs", "elevenlabs"),
        ("dotenv", "python-dotenv"),
        ("PIL", "Pillow"),
        ("rich", "rich"),
        ("mutagen", "mutagen"),
        ("pydantic", "pydantic"),
    ]

    for module_name, pip_name in modules:
        try:
            __import__(module_name)
            console.print(f"  [green]✓[/green] {pip_name}")
        except ImportError:
            console.print(f"  [red]✗[/red] {pip_name} - kurulu değil! → pip install {pip_name}")
            all_ok = False

    # FFmpeg
    print_step(2, "FFmpeg kontrol ediliyor...")
    if check_ffmpeg():
        console.print("  [green]✓[/green] FFmpeg kurulu")
    else:
        console.print("  [red]✗[/red] FFmpeg bulunamadı → winget install FFmpeg")
        all_ok = False

    # API anahtarları
    print_step(3, "API anahtarları kontrol ediliyor...")
    keys = load_env()
    api_checks = {
        "GEMINI_API_KEY": "https://aistudio.google.com",
        "ELEVENLABS_API_KEY": "https://elevenlabs.io",
        "REPLICATE_API_TOKEN": "https://replicate.com",
    }

    for key_name, url in api_checks.items():
        value = keys.get(key_name, "")
        placeholder_values = ["", "buraya_gemini_api_key_gelecek",
                              "buraya_elevenlabs_api_key_gelecek",
                              "buraya_replicate_api_key_gelecek",
                              "buraya_voice_id_gelecek"]
        if value in placeholder_values:
            console.print(f"  [red]✗[/red] {key_name} - tanımlı değil → {url}")
            all_ok = False
        else:
            masked = value[:8] + "..." + value[-4:]
            console.print(f"  [green]✓[/green] {key_name} ({masked})")

    # Dizinler
    print_step(4, "Dizin yapısı kontrol ediliyor...")
    ensure_directories()

    # Sonuç
    console.print()
    if all_ok:
        print_success("Tüm sistemler hazır! Pipeline çalıştırılabilir. ✅")
    else:
        print_error("Bazı bileşenler eksik. Yukarıdaki hataları düzeltin. ❌")

    return all_ok


def main():
    """Ana giriş noktası."""
    if len(sys.argv) < 2:
        console.print()
        console.print("[bold cyan]What-If YouTube Bot[/bold cyan] - Otonom Video Üretim Sistemi")
        console.print()
        console.print("Kullanım:")
        console.print('  python main.py [bold]"Konu başlığı"[/bold]          → Video üret')
        console.print("  python main.py [bold]--test[/bold]                  → Sistem kontrolü")
        console.print("  python main.py [bold]--character[/bold]             → Karakter referans görseli üret")
        console.print()
        console.print("Örnek:")
        console.print('  python main.py "What would happen if the Sun suddenly went out?"')
        return

    arg = sys.argv[1]

    if arg == "--test":
        run_system_check()
    elif arg == "--character":
        ensure_directories()
        generate_character_reference()
    else:
        # Konu olarak al ve pipeline'ı çalıştır
        topic = " ".join(sys.argv[1:])
        run_pipeline(topic)


if __name__ == "__main__":
    main()
