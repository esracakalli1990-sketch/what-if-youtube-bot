# PROJE DEVİR NOTU — What-If YouTube Bot

> Yeni Claude oturumu: Bu dosya projeyi hızlı kavraman içindir. Detay gerektikçe
> ilgili dosyayı aç; baştan her şeyi okuma (token tasarrufu).

## Ne bu proje?
Otonom YouTube kanalı botu: "What If" senaryolu bilim videoları üretir.
Pipeline: Gemini (senaryo) → ElevenLabs/edge-tts (ses) → görsel → FFmpeg (montaj) → YouTube yükleme → Telegram bildirim.
Kanal CANLI: **"What If with Roli"**. İlk Short yayınlandı (199+ görüntüleme). Sistem tam otonom çalışıyor.

## Kullanıcı profili
- Teknik değil, körü körüne uyguluyor. Türkçe konuşuyor. Talimatları net, adım adım ver.
- Kullanıcı adına sen yönetiyorsun: kod yaz, PR aç, CI yeşilse master'a merge et (yerleşik onay var).
- API anahtarları/hesap işlemleri kullanıcıda; sen bulut ortamındasın (yerel makinesine erişemezsin).

## AKTİF MOD: Manuel görsel akışı (IMAGE_MODE=manual)
Görsel API'lerinin hepsi ücretli/kapalı çıktı (Replicate faturasız, Gemini görsel free-tier kota 0, Pollinations 403). Çözüm: kullanıcı görselleri KENDİ üretiyor (Google Flow / Nano Banana Pro), maliyet sıfır.
Akış: Bot senaryoyu üretir → her sahnenin görsel prompt'unu + **Türkçe bilgi notunu** Telegram'a gönderir → kullanıcı görselleri Flow'da üretip sırayla bota fotoğraf yollar → saatlik işleyici görselleri alıp videoyu tamamlar, YouTube'a yükler.
Ana dosya: `scripts/manual_images.py` (durum: `pending_production.json`).

## Mimari / kritik dosyalar
- `main.py` — orkestratör, `run_pipeline(topic, mode, privacy, publish_at)`. Manuel modda görsel yoksa "pending" döner.
- `scripts/scenario_generator.py` — Gemini senaryo (`_call_gemini` yeniden kullanılır), long/shorts modu, cache: `temp/scenario[_shorts].json`
- `scripts/tts_engine.py` — ElevenLabs + edge-tts fallback
- `scripts/image_generator.py` — API görsel (FLUX/SDXL/Gemini/Pollinations zinciri) + `generate_thumbnail(…, background_image=)`
- `scripts/video_assembler.py` — FFmpeg montaj, dikey(1080x1920)/yatay, altyazı, `get_episode_number(prefix)`
- `scripts/manual_images.py` — manuel görsel akışı + `build_turkish_brief` (Türkçe bilgi notu)
- `scripts/youtube_uploader.py` — yükleme, playlist, ilk yorum, `uploads.json`, `next_optimal_publish_time`
- `scripts/scheduler.py` — konu havuzu (`topics.json`), `--refill`(Gemini konu üretir), `run_short`, `run_batch`
- `scripts/analytics.py` — istatistik + `format_report_text`
- `scripts/notifier.py` — Telegram bildirim (`send_message`, `notify_video_completed`, `notify_error`)
- `scripts/telegram_bot.py` — komut işleyici (getUpdates offset: `telegram_state.json`), foto yönlendirme
- `setup_wizard.py` — interaktif ilk kurulum

## Otomasyon (GitHub Actions, .github/workflows/)
- `ci.yml` — her push/PR'da pytest
- `daily-video.yml` — günlük 09:00 UTC Short, Pzt&Per uzun video, Pazar konu doldurma+rapor; `workflow_dispatch` ile `job_type: short|long|refill`
- `telegram-bot.yml` — SAATLİK (:30) komut işleyici + manuel görsel tamamlama
- Durum dosyaları (topics.json, uploads.json, pending_production.json, telegram_state.json) her koşuda tek tek `git add` ile commit edilir (toplu add BUG'ıydı, düzeltildi).

## Telegram komutları
`/durum` `/rapor` `/konular` `/konu <metin>` `/short` `/video [konu]` `/iptal` `/yardim`
Komutlar saatlik işlenir (kullanıcı bunu kabul etti). Acil için: kullanıcı söyler, sen `telegram-bot.yml`'i elle tetiklersin.

## Kullanıcı kararları (değiştirme, sorMADAN)
- Short'lar **public** yüklenir (büyüme için; onaylandı).
- Komut hızı: **kapalı repo + saatlik** (kota koruması; onaylandı).
- Manuel görsel akışı tüm videolar için; görsel gelmezse süresiz bekle + 24s hatırlatma.

## Yapılandırma
GitHub Secrets: GEMINI_API_KEY, ELEVENLABS_API_KEY, CHARACTER_VOICE_ID, REPLICATE_API_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, YOUTUBE_CLIENT_SECRETS_B64, YOUTUBE_TOKEN_B64.
GitHub Variables: **IMAGE_PRIMARY** ve **IMAGE_MODE=manual** (aktif). Opsiyonel: GEMINI_IMAGE_MODEL, YOUTUBE_PLAYLIST_ID.
Repo: `esracakalli1990-sketch/what-if-youtube-bot` (private). Çalışma dalı: **claude/project-continuation-7dj6wg**. Telegram bot: @what_if_roli_bot.

## İş akışı kuralları
- Değişiklik → dala commit → PR aç → CI (pytest) yeşil → master'a merge. Test: `python -m pytest tests/ -q` (şu an 81 test). FFmpeg entegrasyon testleri lokalde FFmpeg yoksa atlanır.
- Model kimliğini commit/PR'a yazma. Türkçe iletişim.
- Görsel API'sini yeniden faturalandırmaya çalışma; manuel mod bilinçli tercih.

## Sıradaki olası işler (kullanıcı isterse)
- İçerik kalitesi ince ayarı (altyazı, tempo, ses tonu, prompt tarzı)
- Kanal büyüdükçe API görsel moduna geçiş (IMAGE_MODE variable'ını sil)
- Daha hızlı komut yanıtı (repo public → 5 dk cron)
