# 🐰 What-If YouTube Bot (v3)

Otonom YouTube video üretim sistemi. "What If" senaryoları için yapay zeka (Gemini, ElevenLabs, FLUX/SDXL) ve FFmpeg kullanan otonom pipeline. Uzun video **ve YouTube Shorts** üretir, konu havuzunu Gemini ile kendisi doldurur, performans verisini konu seçimine geri besler.

## 🎬 Nasıl Çalışır?

```
Konu Girişi → Gemini (Senaryo) → ElevenLabs (Ses) → Replicate (Görsel) → FFmpeg (Montaj) → Final Video + Thumbnail → YouTube Uploader
                    ↑                                                                              ↓
             Konu Motoru (--refill)  ←──────  Analytics (izlenme verisi)  ←──────  uploads.json kaydı
```

İki format:
- **Uzun video** (varsayılan): 10 dk, 1920x1080, 5-6 sahne, thumbnail'li
- **Shorts** (`--shorts`): 45-60 sn, 1080x1920 dikey, 3-4 sahne, büyük altyazı, #Shorts etiketli

## 🚀 Hızlı Başlangıç

### ⚡ Tek Komutla Kurulum (Önerilen)

```bash
pip install -r requirements.txt
python setup_wizard.py
```

Sihirbaz tüm kurulumu adım adım yürütür: API anahtarlarını ister ve anında test eder, YouTube yetkilendirmesini çalıştırır, Telegram botunuzu bağlar (chat ID'yi otomatik bulur) ve GitHub'a eklenecek secret değerlerini hazır olarak verir. Yarıda kalırsa tekrar çalıştırın — kaldığı yerden devam eder.

Elle kurulum tercih ederseniz aşağıdaki adımları izleyin:

### 1. Bağımlılıkları Kur
```bash
pip install -r requirements.txt
```

### 2. FFmpeg Kur
```bash
winget install Gyan.FFmpeg
# Kurulumdan sonra terminali yeniden başlatmayı unutmayın!
```

### 3. API Anahtarlarını Tanımla
```bash
cp .env.example .env   # sonra içindeki placeholder'ları doldurun
```
- **Gemini**: https://aistudio.google.com
- **ElevenLabs**: https://elevenlabs.io (Bir Voice ID seçin)
- **Replicate**: https://replicate.com
- **YOUTUBE_PLAYLIST_ID** (opsiyonel): uzun videolar otomatik bu oynatma listesine eklenir

### 4. YouTube API Kurulumu (İsteğe bağlı - otomatik yükleme için)
1. Google Cloud Console'da bir proje oluşturun.
2. YouTube Data API v3'ü etkinleştirin.
3. OAuth 2.0 Client ID (Desktop App) oluşturup `client_secrets.json` olarak projenin ana klasörüne kaydedin.
4. İlk yetkilendirme için: `python scripts/youtube_uploader.py --auth`

> ⚠️ v3'te yorum atabilmek için `youtube.force-ssl` scope'u eklendi. Daha önce yetkilendirme yaptıysanız `youtube_token.pickle` dosyasını silip `--auth` komutunu tekrar çalıştırın.

### 5. Docker Desktop Kurulumu (İsteğe bağlı - n8n entegrasyonu için)
1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) uygulamasını indirip kurun.
2. Ayarlardan WSL2 backend'inin aktif olduğundan emin olun.
3. n8n başlatmak için: `docker-compose up -d`

### 6. Sistem Kontrolü
```bash
python main.py --test
```

### 7. Video Üret!
```bash
python main.py "What would happen if gravity doubled?"
```

## 📁 Proje Yapısı

```
what-if-youtube-bot/
├── main.py                 # Ana orkestratör
├── scripts/
│   ├── scenario_generator.py   # Gemini senaryo motoru (uzun + shorts modu)
│   ├── tts_engine.py           # ElevenLabs ses motoru (edge-tts fallback)
│   ├── image_generator.py      # FLUX/SDXL görsel motoru (16:9 + 9:16)
│   ├── video_assembler.py      # FFmpeg montaj motoru (yatay + dikey, altyazı)
│   ├── thumbnail_composer.py   # Thumbnail yazı/efekt overlay
│   ├── scheduler.py            # Konu havuzu, --refill konu motoru, batch
│   ├── youtube_uploader.py     # YouTube yükleyici (planlı yayın, playlist, ilk yorum)
│   ├── analytics.py            # Performans takibi ve geri besleme
│   └── utils.py                # Yardımcı fonksiyonlar, retry, checkpoint
├── prompts/                # AI prompt şablonları (uzun + shorts)
├── tests/                  # pytest test paketi
├── character/reference/    # Karakter referans görseli
├── output/                 # Üretilen videolar + uploads.json + istatistikler
└── temp/                   # Geçici dosyalar (kaldığı yerden devam desteği)
```

## 🔧 Komutlar

| Komut | Açıklama |
|-------|----------|
| `python main.py "konu"` | Tam pipeline - uzun video üret |
| `python main.py --shorts "konu"` | 45-60 sn dikey YouTube Shorts üret |
| `python main.py "konu" --publish-at auto` | Üret ve bir sonraki 15:00 UTC'de yayınlanacak şekilde planla |
| `python main.py "konu" --privacy public` | Üret ve hemen herkese açık yayınla |
| `python main.py --resume` | Yarıda kalan pipeline'ı devam ettir (Shorts modunu hatırlar) |
| `python main.py --test` | Sistem kontrolü |
| `python main.py --character` | Karakter referans görseli üret |
| `python main.py --voices` | ElevenLabs seslerini listele |
| `python scripts/scheduler.py --list` | Konu havuzunu listele |
| `python scripts/scheduler.py --refill 10` | Gemini ile havuza 10 yeni viral konu ekle |
| `python scripts/scheduler.py --batch 3 --with-shorts` | 3 uzun video + her birinden Short üret |
| `python scripts/scheduler.py --short` | Havuzdan sıradaki konuyla 1 Short üret + yükle (otomasyon komutu) |
| `python scripts/scheduler.py --batch 1 --publish-auto` | 1 uzun video üret, optimal saate planla |
| `python scripts/analytics.py --report` | Kanal performans raporu |
| `pytest tests/` | Test paketini çalıştır |

## 🤖 Tam Otomasyon (GitHub Actions)

Repo'da hazır iki iş akışı var:

- **CI** (`.github/workflows/ci.yml`): her push/PR'da test paketini çalıştırır.
- **Otonom Video Üretimi** (`.github/workflows/daily-video.yml`): bilgisayarınız kapalıyken bile kanal kendi kendine çalışır:
  - Her gün 09:00 UTC → 1 public **Short**
  - Pazartesi & Perşembe → 1 **uzun video** (bir sonraki 15:00 UTC'ye planlı yayın)
  - Pazar → konu havuzu Gemini ile doldurulur
  - Elle tetikleme: Actions sekmesi → "Otonom Video Üretimi" → Run workflow (tip ve istediğiniz konuyu seçebilirsiniz)

### Kurulum (bir kere)

GitHub → repo → **Settings → Secrets and variables → Actions** altına şu secret'ları ekleyin:

| Secret | Değer |
|--------|-------|
| `GEMINI_API_KEY` | Gemini API anahtarınız |
| `ELEVENLABS_API_KEY` | ElevenLabs API anahtarınız |
| `CHARACTER_VOICE_ID` | ElevenLabs ses ID'si |
| `REPLICATE_API_TOKEN` | Replicate token'ınız |
| `YOUTUBE_CLIENT_SECRETS_B64` | `base64 -w0 client_secrets.json` çıktısı |
| `YOUTUBE_TOKEN_B64` | Lokal `--auth` sonrası `base64 -w0 youtube_token.pickle` çıktısı |
| `YOUTUBE_PLAYLIST_ID` | (Opsiyonel) uzun videoların ekleneceği playlist |

> YouTube secret'ları eksikse video yine üretilir ve Actions **artifact**'ı olarak 5 gün saklanır — sadece yükleme atlanır. Windows'ta base64 için: `certutil -encode dosya out.txt` (başlık/son satırları silin) veya Git Bash kullanın.

Bot, üretim durumunu (`topics.json`, `output/uploads.json`) her çalışmadan sonra repoya commit'leyerek kaldığı yeri hatırlar.

## 💬 Telegram ile Takip ve Kontrol

Bot her olayı Telegram'dan size bildirir ve komutlarla kontrol edilebilir — sunucu gerekmez.

### Kurulum (5 dakika)

1. Telegram'da **@BotFather**'a `/newbot` yazın, bir isim verin → size bir **token** verir
2. Oluşan botunuza Telegram'dan herhangi bir mesaj gönderin
3. Chat ID'nizi öğrenin: `.env`'e token'ı ekledikten sonra `python scripts/notifier.py --chat-id`
4. İki değeri hem `.env` dosyanıza hem GitHub secrets'a ekleyin: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
5. Test: `python scripts/notifier.py --test`

### Neler bildirilir?

- ✅ Video üretildi (thumbnail önizlemesiyle) + YouTube linki + planlı yayın saati
- 🚨 Her türlü pipeline/workflow hatası (hangi adımda, neden)
- 💡 Konu havuzu güncellemeleri
- 📊 Haftalık performans raporu (her Pazar, izlenme/beğeni/yorum)

### Telegram komutları

Komutlar saatte bir (her saat :30'da) işlenir:

| Komut | Ne yapar |
|-------|----------|
| `/durum` | Konu havuzu + son yüklemeler |
| `/rapor` | Anlık kanal performans raporu |
| `/konular` | Bekleyen konu listesi |
| `/konu <metin>` | Havuza yeni konu ekle |
| `/short` | Hemen 1 Short üret ve yayınla |
| `/video` | Hemen 1 uzun video üret (havuzdan konu seçer) |
| `/video <konu>` | Bu konudan uzun video üret |
| `/yardim` | Komut listesi |

## 📈 Büyüme Stratejisi (Önerilen Kadans)

Yeni bir kanal için en hızlı keşif kaynağı Shorts'tur — algoritma Shorts'u abonesi olmayan kanallara da dağıtır. Önerilen ritim:

1. **Günde 1 Short** — `python main.py --shorts "konu" --privacy public`
2. **Haftada 2 uzun video** — `--publish-at auto` ile prime time'a planla (15:00 UTC ≈ ABD sabahı + Avrupa akşamı)
3. **Haftada 1 kez** `python scripts/analytics.py --report` ile neyin tuttuğuna bak; `--refill` konu motoru en iyi başlıkları otomatik olarak yeni konu üretiminde kullanır
4. Uzun videosu iyi giden konulardan Short türet (`--batch --with-shorts` bunu otomatik yapar) — Short'tan gelen izleyici kanaldaki uzun videoya akar

Her yüklemede bot otomatik olarak: SEO açıklaması + etiketler + zaman damgaları üretir, videoyu playlist'e ekler, etkileşim için ilk yorumu atar ve `output/uploads.json`'a kayıt düşer.

## 💰 Aylık Tahmini Maliyet: ~$35-60

| Araç | Model / Hizmet | Maliyet Tahmini |
|------|----------------|-----------------|
| Gemini API | 2.5 Flash / 2.0 Flash | Ücretsiz / ~$2-5 |
| ElevenLabs | Multilingual v2 | ~$11-22 |
| Replicate | FLUX 1.1 Pro / SDXL | ~$15-20 |
| FFmpeg | Lokal İşlemci | $0 |
