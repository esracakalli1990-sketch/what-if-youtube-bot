"""
main.py - What-If YouTube Bot Ana Orkestratör.

Tek komutla konu al → senaryo yaz → seslendir → görsel üret → montajla → video çıkar.

Kullanım:
    python main.py "What would happen if the Sun suddenly went out?"
    python main.py --resume          # Yarıda kalan pipeline'ı devam ettir
    python main.py --character       # Sadece karakter referans görseli üret
    python main.py --test            # Sistem kontrolü çalıştır
    python main.py --voices          # ElevenLabs seslerini listele
    python main.py --scenario-only "konu"  # Sadece senaryo üret
"""

import sys
import time
import argparse
from pathlib import Path

from scripts.utils import (
    ensure_directories, clean_temp, print_header,
    print_step, print_success, print_error, print_warning,
    console, logger, load_env, PipelineCheckpoint,
    TEMP_DIR, OUTPUT_DIR
)
from scripts.scenario_generator import generate_scenario, load_scenario
from scripts.tts_engine import generate_audio, list_available_voices
from scripts.image_generator import generate_images, generate_character_reference, generate_thumbnail
from scripts.video_assembler import assemble_video, check_ffmpeg
from scripts.youtube_uploader import upload_video, check_youtube_setup
from scripts.notifier import notify_video_completed, notify_error


def run_pipeline(
    topic: str,
    resume: bool = False,
    no_upload: bool = False,
    mode: str = "long",
    privacy: str = "private",
    publish_at=None,
):
    """
    Tam video üretim pipeline'ını çalıştır.

    1. Senaryo üretimi (Gemini)
    2. Seslendirme (ElevenLabs)
    3. Görsel üretimi (FLUX/SDXL via Replicate)
    4. Video montaj (FFmpeg)
    5. Thumbnail üretimi (sadece uzun video)

    Args:
        topic: Video konusu
        resume: True ise checkpoint'tan devam et
        mode: "long" (10 dk yatay) veya "shorts" (45-60 sn dikey)
        privacy: YouTube gizlilik (private/unlisted/public)
        publish_at: Planlı yayın zamanı (datetime, opsiyonel)

    Returns:
        str | None: Final video yolu (başarılıysa) veya None
    """
    start_time = time.time()
    is_shorts = mode == "shorts"

    header = "🚀 WHAT-IF YOUTUBE BOT - OTONOM VİDEO ÜRETİM"
    if is_shorts:
        header += " (SHORTS)"
    print_header(header)
    console.print(f"  📌 Konu: [bold cyan]{topic}[/bold cyan]")
    console.print(f"  ⏰ Başlangıç: {time.strftime('%H:%M:%S')}")
    console.print()

    # Dizinleri hazırla
    ensure_directories()

    # Checkpoint yönetimi
    checkpoint = PipelineCheckpoint()

    if resume and checkpoint.can_resume(topic):
        console.print(f"  [cyan]♻ Resume modu: {checkpoint.get_resume_info()}[/cyan]")
        logger.info("Pipeline resume edildi: %s", checkpoint.get_resume_info())
        mode = checkpoint.data.get("mode", mode)
        is_shorts = mode == "shorts"
    else:
        if not resume:
            clean_temp()
        checkpoint.start(topic)
        checkpoint.data["mode"] = mode
        checkpoint._save()

    # ═══════════════════════════════════════
    # ADIM 1: SENARYO ÜRETİMİ
    # ═══════════════════════════════════════
    scenario = None
    if checkpoint.is_step_completed("scenario"):
        console.print("\n  [cyan]♻ Senaryo: Checkpoint'tan yükleniyor...[/cyan]")
        scenario = load_scenario(mode=mode)
    else:
        checkpoint.set_current_step("scenario")
        scenario = generate_scenario(topic, mode=mode)

    if not scenario:
        print_error("Pipeline durdu: Senaryo üretilemedi.")
        notify_error(f"Senaryo üretimi ({topic})", "Gemini senaryo üretemedi — API anahtarını ve kotayı kontrol edin.")
        return

    scenes = scenario.get("scenes", [])
    if not scenes:
        print_error("Pipeline durdu: Senaryoda sahne bulunamadı.")
        notify_error(f"Senaryo üretimi ({topic})", "Senaryoda sahne bulunamadı.")
        return

    title = scenario.get("title", "Untitled Episode")

    if not checkpoint.is_step_completed("scenario"):
        checkpoint.complete_step("scenario", episode_title=title)

    # ═══════════════════════════════════════
    # MANUEL GÖRSEL AKIŞI (IMAGE_MODE=manual)
    # Görseller hazır değilse prompt'ları Telegram'a gönder ve bekle
    # ═══════════════════════════════════════
    from scripts.manual_images import (
        is_manual_mode, images_ready, start_pending, load_pending
    )
    if is_manual_mode() and not images_ready(scenes, vertical=is_shorts):
        pending = load_pending()
        if pending:
            if pending.get("topic") == topic:
                console.print("  🎨 [cyan]Görseller Telegram'dan bekleniyor "
                              f"({len(pending['image_file_ids'])}/{pending['expected_images']} geldi)[/cyan]")
            else:
                print_warning(f"Başka bir üretim görsel bekliyor: '{pending.get('topic')}' — "
                              "önce onu tamamlayın veya Telegram'dan /iptal yazın.")
            return "pending"
        if start_pending(topic, mode, scenario, privacy=privacy):
            console.print("  🎨 [cyan]Görsel prompt'ları Telegram'a gönderildi — "
                          "görseller gelince üretim otomatik devam edecek.[/cyan]")
            return "pending"
        print_error("Manuel görsel akışı başlatılamadı (Telegram yapılandırmasını kontrol edin).")
        return None

    # ═══════════════════════════════════════
    # ADIM 2: SESLENDİRME
    # ═══════════════════════════════════════
    audio_results = None
    if checkpoint.is_step_completed("audio"):
        console.print("\n  [cyan]♻ Seslendirme: Checkpoint'tan yükleniyor...[/cyan]")
        audio_results = checkpoint.data.get("audio_results", [])
    else:
        checkpoint.set_current_step("audio")
        audio_results = generate_audio(scenes)

    if not audio_results:
        print_error("Pipeline durdu: Seslendirme yapılamadı.")
        notify_error(f"Seslendirme ({topic})", "TTS üretimi başarısız — ElevenLabs/edge-tts kontrol edin.")
        return

    if not checkpoint.is_step_completed("audio"):
        checkpoint.complete_step("audio", audio_results=audio_results)

    # ═══════════════════════════════════════
    # ADIM 3: GÖRSEL ÜRETİMİ
    # ═══════════════════════════════════════
    image_results = None
    if checkpoint.is_step_completed("images"):
        console.print("\n  [cyan]♻ Görseller: Checkpoint'tan yükleniyor...[/cyan]")
        image_results = checkpoint.data.get("image_results", [])
    else:
        checkpoint.set_current_step("images")
        image_results = generate_images(scenes, vertical=is_shorts)

    if not image_results:
        print_error("Pipeline durdu: Görseller üretilemedi.")
        notify_error(f"Görsel üretimi ({topic})", "Hiçbir görsel üretilemedi — Replicate/Pollinations kontrol edin.")
        return

    if not checkpoint.is_step_completed("images"):
        checkpoint.complete_step("images", image_results=image_results)

    # ═══════════════════════════════════════
    # ADIM 4: VİDEO MONTAJ
    # ═══════════════════════════════════════
    checkpoint.set_current_step("video")
    final_video = assemble_video(scenes, audio_results, image_results, title, vertical=is_shorts)

    if final_video:
        checkpoint.complete_step("video", final_video=final_video)

        # ═══════════════════════════════════
        # ADIM 5: THUMBNAIL ÜRETİMİ
        # Uzun video: AI/manuel arka plandan. Short: ilk sahne görselinden 16:9.
        # ═══════════════════════════════════
        thumbnail = None
        thumb_output = None
        thumbnail_concept = scenario.get("thumbnail_concept", "")
        display_title = scenario.get("clickbait_title", title)

        if is_shorts:
            # Short: kullanıcı ayrı thumbnail görseli göndermez — ilk sahneyi kullan
            first_scene = image_results[0]["image_path"] if image_results else None
            thumbnail = generate_thumbnail(display_title, thumbnail_concept, background_image=first_scene)
        else:
            thumbnail = generate_thumbnail(display_title, thumbnail_concept)

        # Thumbnail'i output'a kopyala
        if thumbnail:
            import shutil
            prefix = "short" if is_shorts else "episode"
            ep_num_str = Path(final_video).stem.split("_")[1]
            thumb_output = OUTPUT_DIR / f"{prefix}_{ep_num_str}_thumbnail.png"
            try:
                shutil.copy2(thumbnail, str(thumb_output))
                console.print(f"  🖼️  Thumbnail: {thumb_output}")
            except Exception:
                pass

        # ═══════════════════════════════════
        # ADIM 6: YOUTUBE YÜKLEME
        # ═══════════════════════════════════
        video_id = None
        upload_failed = False
        if not no_upload:
            youtube_status = check_youtube_setup()
            if youtube_status.get("authenticated"):
                video_id = upload_video(
                    video_path=final_video,
                    title=title,
                    thumbnail_path=str(thumb_output) if thumb_output else None,
                    privacy=privacy,
                    publish_at=publish_at,
                    scenario=scenario,
                    audio_results=audio_results,
                    is_short=is_shorts,
                )
                if not video_id:
                    upload_failed = True
            else:
                print_warning("YouTube yetkilendirmesi yok. Otomatik yükleme atlandı.")

        elapsed = time.time() - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        # Telegram bildirimi
        if upload_failed:
            notify_error(
                f"YouTube yükleme ({topic})",
                "Video başarıyla üretildi ama YouTube'a yüklenemedi (loglara bakın). "
                "Konu 'tamamlandı' sayılmadı — tekrar denenebilir.",
            )
        else:
            notify_video_completed(
                title=scenario.get("clickbait_title", title),
                mode=mode,
                video_path=final_video,
                duration_text=f"{minutes}dk {seconds}sn",
                video_id=video_id,
                publish_at=publish_at,
                thumbnail_path=str(thumb_output) if thumb_output else None,
            )

        console.print()
        print_header("🎉 VİDEO ÜRETİMİ TAMAMLANDI!")
        console.print(f"  📹 Video: [bold green]{final_video}[/bold green]")
        console.print(f"  📝 Başlık: [bold]{title}[/bold]")
        console.print(f"  ⏱️  Toplam süre: {minutes}dk {seconds}sn")
        if thumbnail:
            console.print(f"  🖼️  Thumbnail: [bold green]Hazır[/bold green]")
        console.print()
        console.print("[bold cyan]YouTube'a yüklemeye hazır! 🚀[/bold cyan]")

        logger.info("Pipeline tamamlandı: %s (%ddk %dsn)", final_video, minutes, seconds)

        # Checkpoint temizle
        checkpoint.clear()

        if upload_failed:
            # Video başarıyla üretildi ama YouTube'a yüklenemedi (ör. geçersiz
            # etiket/metadata). Konuyu "tamamlandı" SAYMA — aksi halde bir daha
            # asla denenmez ve kanalda o bölüm hiç yayınlanmaz.
            print_error("YouTube yüklemesi başarısız — konu tamamlanmadı sayılacak (tekrar denenebilir).")
            logger.error("Pipeline: video üretildi ama YouTube yüklemesi başarısız: %s", topic)
            return None

        return final_video
    else:
        print_error("Video üretimi başarısız oldu.")
        logger.error("Pipeline başarısız: video montaj aşamasında hata.")
        notify_error(f"Video montaj ({topic})", "FFmpeg montaj aşamasında hata — loglara bakın.")
        return None


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
        console.print("  [red]✗[/red] FFmpeg bulunamadı → winget install Gyan.FFmpeg")
        all_ok = False

    # API anahtarları
    print_step(3, "API anahtarları kontrol ediliyor...")
    keys = load_env()
    api_checks = {
        "GEMINI_API_KEY": "https://aistudio.google.com",
        "ELEVENLABS_API_KEY": "https://elevenlabs.io",
        "CHARACTER_VOICE_ID": "https://elevenlabs.io → Voice ID",
        "REPLICATE_API_TOKEN": "https://replicate.com",
    }

    placeholder_values = [
        "", "buraya_gemini_api_key_gelecek",
        "buraya_elevenlabs_api_key_gelecek",
        "buraya_replicate_api_key_gelecek",
        "buraya_voice_id_gelecek",
    ]

    for key_name, url in api_checks.items():
        value = keys.get(key_name, "")
        if value in placeholder_values:
            console.print(f"  [red]✗[/red] {key_name} - tanımlı değil → {url}")
            all_ok = False
        else:
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            console.print(f"  [green]✓[/green] {key_name} ({masked})")

    # Dizinler
    print_step(4, "Dizin yapısı kontrol ediliyor...")
    ensure_directories()

    # Karakter referansı
    from scripts.image_generator import _get_character_reference
    ref = _get_character_reference()
    if ref:
        console.print(f"  [green]✓[/green] Karakter referans görseli mevcut")
    else:
        console.print(f"  [yellow]⚠[/yellow] Karakter referansı yok → python main.py --character")

    # Arka plan müziği
    from scripts.utils import ASSETS_DIR
    music_files = list(ASSETS_DIR.glob("*.mp3")) + list(ASSETS_DIR.glob("*.wav"))
    if music_files:
        console.print(f"  [green]✓[/green] Arka plan müziği: {music_files[0].name}")
    else:
        console.print(f"  [yellow]⚠[/yellow] Arka plan müziği yok (opsiyonel) → assets/music/ klasörüne ekleyin")

    # Sonuç
    console.print()
    if all_ok:
        print_success("Tüm sistemler hazır! Pipeline çalıştırılabilir. ✅")
    else:
        print_error("Bazı bileşenler eksik. Yukarıdaki hataları düzeltin. ❌")

    return all_ok


def main():
    """Ana giriş noktası."""
    parser = argparse.ArgumentParser(
        description="What-If YouTube Bot - Otonom Video Üretim Sistemi",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python main.py "What would happen if the Sun suddenly went out?"
  python main.py --shorts "What if gravity doubled?"
  python main.py --resume
  python main.py --test
  python main.py --character
  python main.py --voices
  python main.py --scenario-only "What if gravity doubled?"
        """
    )

    parser.add_argument(
        "topic",
        nargs="?",
        help="Video konusu (tam pipeline)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Sistem kontrolü çalıştır"
    )
    parser.add_argument(
        "--character",
        action="store_true",
        help="Karakter referans görseli üret"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Yarıda kalan pipeline'ı kaldığı yerden devam ettir"
    )
    parser.add_argument(
        "--voices",
        action="store_true",
        help="ElevenLabs seslerini listele"
    )
    parser.add_argument(
        "--scenario-only",
        metavar="TOPIC",
        help="Sadece senaryo üret (video oluşturma)"
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Video üretilir ancak YouTube'a yüklenmez"
    )
    parser.add_argument(
        "--shorts",
        action="store_true",
        help="YouTube Shorts modu: 45-60 sn dikey (9:16) video üret"
    )
    parser.add_argument(
        "--privacy",
        choices=["private", "unlisted", "public"],
        default="private",
        help="YouTube gizlilik durumu (varsayılan: private)"
    )
    parser.add_argument(
        "--publish-at",
        metavar="WHEN",
        help="Planlı yayın: 'auto' (bir sonraki 15:00 UTC) veya ISO tarih (2026-07-10T15:00)"
    )

    args = parser.parse_args()

    # Planlı yayın zamanını çöz
    publish_at = None
    if args.publish_at:
        from datetime import datetime, timezone
        from scripts.youtube_uploader import next_optimal_publish_time
        if args.publish_at.lower() == "auto":
            publish_at = next_optimal_publish_time()
        else:
            try:
                publish_at = datetime.fromisoformat(args.publish_at)
                if publish_at.tzinfo is None:
                    publish_at = publish_at.replace(tzinfo=timezone.utc)
            except ValueError:
                print_error(f"Geçersiz --publish-at değeri: {args.publish_at}")
                print_error("Örnek: --publish-at auto  veya  --publish-at 2026-07-10T15:00")
                sys.exit(1)
        # publishAt yalnızca private videolarda çalışır (YouTube kuralı)
        if args.privacy != "private":
            print_warning("--publish-at kullanıldığında video 'private' yüklenir, YouTube zamanı gelince yayınlar.")

    if args.test:
        run_system_check()
    elif args.character:
        ensure_directories()
        generate_character_reference()
    elif args.voices:
        print_header("🎙️ ElevenLabs Ses Listesi")
        list_available_voices()
    elif args.scenario_only:
        ensure_directories()
        result = generate_scenario(args.scenario_only)
        if result:
            print_success("Senaryo kaydedildi: temp/scenario.json")
        else:
            print_error("Senaryo üretilemedi.")
    elif args.resume:
        checkpoint = PipelineCheckpoint()
        if checkpoint.data and checkpoint.data.get("topic"):
            topic = checkpoint.data["topic"]
            mode = checkpoint.data.get("mode", "long")
            console.print(f"  📌 Devam edilen konu: [bold cyan]{topic}[/bold cyan]")
            console.print(f"  📊 {checkpoint.get_resume_info()}")
            run_pipeline(
                topic, resume=True, no_upload=args.no_upload, mode=mode,
                privacy=args.privacy, publish_at=publish_at,
            )
        else:
            print_error("Devam edilebilir checkpoint bulunamadı.")
            print_error("Yeni pipeline başlatmak için: python main.py \"konu\"")
    elif args.topic:
        run_pipeline(
            args.topic,
            no_upload=args.no_upload,
            mode="shorts" if args.shorts else "long",
            privacy=args.privacy,
            publish_at=publish_at,
        )
    else:
        parser.print_help()
        console.print()
        console.print("[bold cyan]Hızlı başlangıç:[/bold cyan]")
        console.print('  1. python main.py --test')
        console.print('  2. python main.py "What would happen if gravity doubled?"')


if __name__ == "__main__":
    main()
