# 🐰 What-If YouTube Bot

Otonom YouTube video üretim sistemi. "What If" senaryoları için AI destekli video üretim hattı.

## 🎬 Nasıl Çalışır?

```
Konu Girişi → Gemini (Senaryo) → ElevenLabs (Ses) → Replicate (Görsel) → FFmpeg (Montaj) → Final Video
```

## 🚀 Hızlı Başlangıç

### 1. Bağımlılıkları Kur
```bash
pip install -r requirements.txt
```

### 2. FFmpeg Kur
```bash
winget install FFmpeg
```

### 3. API Anahtarlarını Tanımla
`.env` dosyasını düzenle ve API key'lerini ekle:
- **Gemini**: https://aistudio.google.com
- **ElevenLabs**: https://elevenlabs.io
- **Replicate**: https://replicate.com

### 4. Sistem Kontrolü
```bash
python main.py --test
```

### 5. Video Üret!
```bash
python main.py "What would happen if the Sun suddenly went out?"
```

## 📁 Proje Yapısı

```
what-if-youtube-bot/
├── main.py                 # Ana orkestratör
├── scripts/
│   ├── scenario_generator.py   # Gemini senaryo motoru
│   ├── tts_engine.py           # ElevenLabs ses motoru
│   ├── image_generator.py      # Stable Diffusion görsel motoru
│   ├── video_assembler.py      # FFmpeg montaj motoru
│   └── utils.py                # Yardımcı fonksiyonlar
├── prompts/                # AI prompt şablonları
├── character/reference/    # Karakter referans görseli
├── output/                 # Üretilen videolar
└── temp/                   # Geçici dosyalar
```

## 🔧 Komutlar

| Komut | Açıklama |
|-------|----------|
| `python main.py "konu"` | Tam pipeline - video üret |
| `python main.py --test` | Sistem kontrolü |
| `python main.py --character` | Karakter referans görseli üret |

## 💰 Aylık Tahmini Maliyet: ~$35-60

| Araç | Maliyet |
|------|---------|
| Gemini API | ~$2-5 |
| ElevenLabs | ~$11-22 |
| Replicate | ~$15-20 |
| FFmpeg | $0 (lokal) |
