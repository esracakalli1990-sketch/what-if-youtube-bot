# 🐰 What-If YouTube Bot (v2)

Otonom YouTube video üretim sistemi. "What If" senaryoları için yapay zeka (Gemini, ElevenLabs, FLUX/SDXL) ve FFmpeg kullanan otonom pipeline.

## 🎬 Nasıl Çalışır?

```
Konu Girişi → Gemini (Senaryo) → ElevenLabs (Ses) → Replicate (Görsel) → FFmpeg (Montaj) → Final Video + Thumbnail → YouTube Uploader
```

## 🚀 Hızlı Başlangıç

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
`.env` dosyasını oluşturun veya düzenleyin:
- **Gemini**: https://aistudio.google.com
- **ElevenLabs**: https://elevenlabs.io (Bir Voice ID seçin)
- **Replicate**: https://replicate.com

### 4. YouTube API Kurulumu (İsteğe bağlı - otomatik yükleme için)
1. Google Cloud Console'da bir proje oluşturun.
2. YouTube Data API v3'ü etkinleştirin.
3. OAuth 2.0 Client ID (Desktop App) oluşturup `client_secrets.json` olarak projenin ana klasörüne kaydedin.
4. İlk yetkilendirme için: `python scripts/youtube_uploader.py --auth`

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
│   ├── scenario_generator.py   # Gemini senaryo motoru
│   ├── tts_engine.py           # ElevenLabs ses motoru
│   ├── image_generator.py      # FLUX/SDXL görsel ve thumbnail motoru
│   ├── video_assembler.py      # FFmpeg montaj motoru (crossfade, altyazı)
│   ├── scheduler.py            # Konu havuzu ve zamanlama
│   ├── youtube_uploader.py     # YouTube Data API v3 yükleyici
│   └── utils.py                # Yardımcı fonksiyonlar, retry, checkpoint
├── prompts/                # AI prompt şablonları
├── character/reference/    # Karakter referans görseli
├── output/                 # Üretilen videolar
└── temp/                   # Geçici dosyalar (kaldığı yerden devam desteği)
```

## 🔧 Komutlar

| Komut | Açıklama |
|-------|----------|
| `python main.py "konu"` | Tam pipeline - video üret |
| `python main.py --resume` | Yarıda kalan pipeline'ı devam ettir |
| `python main.py --test` | Sistem kontrolü |
| `python main.py --character` | Karakter referans görseli üret |
| `python main.py --voices` | ElevenLabs seslerini listele |
| `python scripts/scheduler.py --list` | Konu havuzunu listele |
| `python scripts/scheduler.py --batch 3` | Toplu 3 video üret |

## 💰 Aylık Tahmini Maliyet: ~$35-60

| Araç | Model / Hizmet | Maliyet Tahmini |
|------|----------------|-----------------|
| Gemini API | 2.5 Flash / 2.0 Flash | Ücretsiz / ~$2-5 |
| ElevenLabs | Multilingual v2 | ~$11-22 |
| Replicate | FLUX 1.1 Pro / SDXL | ~$15-20 |
| FFmpeg | Lokal İşlemci | $0 |
