# PROJE PLANI — Türkçe Uzun Tarih Belgeseli Serisi

Tarih: 31 Ekim 2026 · Kanal: mevcut kanal (şu an "Roli's Doomsday Files", 3 abone, 473 toplam izlenme) · Durum: **Faz 1 tamamlandı ve master'da (PR #43). Faz 1b (gerçek video katmanı) onaylandı, 31 Ekim.**

---

# FAZ 1b — GERÇEK VİDEO KATMANI (31 Ekim, onaylandı)

## Bağlam
Kullanıcının haklı tespiti: 43 dakikalık bir video yalnızca fotoğraflardan oluşursa, hareket eklense bile "slayt gösterisi" hissi verir. Konuyla birebir ilgili yerlerde gerçek video belgesel hissini artırır.
- Kullanıcının kararları: Pexels kullanılacak; Wikimedia'daki Hattuşa videosundan kesitler alınacak; Gemini klipleri şimdilik 8 ile sınırlı; kullanıcı kendisi de video araştıracak.
- Hedef karışım (43 dk): **~%30 gerçek video** + ~%15 hareketli harita + ~%55 fotoğraf. Fotoğraflar da "atmosfer katmanı" ile canlandırılacak.

## Kaynaklar ve durumları
| Kaynak | Ne | Lisans | Durum |
|---|---|---|---|
| **Wikimedia: "HATTUŞAŞ ANTİK KENTİ ÇORUM" videosu** | Hattuşa'da çekilmiş 29 dakikalık gerçek görüntü, 720p | CC BY 3.0 (sahibi: GÖLGE ADAM YILDIRIM; açıklamada atıf zorunlu) | Bulundu. 1,8 GB; Actions'ta indirilecek. 720p olduğu için kısa kesitler (5–8 sn) ve renk düzeltmesiyle kullanılacak |
| **Pexels** | Atmosfer görüntüleri: bozkır, gökyüzü time-lapse, nehir, ateş, toz, kil işleyen eller, mum ışığı… | Pexels lisansı: ticari kullanım serbest, atıf gerekmez (açıklamaya yine de eklenecek) | Kullanıcı `PEXELS_API_KEY` secret'ını ekleyecek. Bu ortamdan erişim kapalı, Actions'tan erişiliyor |
| **Gemini klipleri** | 8 canlandırma (`klip_promptlari.md`) | Kullanıcı üretiyor | Bekleniyor |
| **Kullanıcının bulduğu videolar** | — | Yalnızca uygun lisans (aşağıda) | Kullanıcı araştırıyor |
| NASA arşivi | Uzaydan görüntü | Kamu malı | Denendi; uygun görüntü yok, kullanılmayacak |

## Yeni "formül": atmosfer katmanları
Fotoğrafların üzerine Pexels'ten alınan **toz zerreleri, sis, kıvılcım, ışık hüzmesi** gibi şeffaf hareketli katmanlar "screen" karışımıyla bindirilir. Örnekler:
- Yangın anlatılırken Hattuşa fotoğrafının üstünde uçuşan kıvılcımlar
- Müze eserinin üstünde süzülen toz

Ucuzdur (Pexels ücretsiz), fotoğrafı "canlı çekim" gibi gösterir ve tarihsel hata riski taşımaz.

## Uygulama
1. **`scripts/stock_video.py` (yeni):** Pexels arama ve indirme.
   - Yatay, ≥1920 px ve yeterli süreli görüntüler seçilir.
   - Seçilen ID ve çekenin adı `build/stock/credits.json`'a yazılır.
   - Plandaki her sahne bir arama sorgusu taşır. İnceleme sonrası beğenilen ID planda **sabitlenir**; sonraki çalışmalarda aynı görüntü gelir.
2. **Yeni çekim türleri:** `doc_timeline.chapter_shots` ve `validate` genişletilir.
   - `{"stock": {"q": "...", "id": 123}}` → Pexels videosu
   - `{"film": "hattusa_video", "start": 312.5}` → Commons videosundan, verilen saniyeden başlayan kesit
   - Fotoğraf çekiminde `"overlay": "toz" | "sis" | "kivilcim" | "isik"` → atmosfer katmanı
3. **`doc_render.py`:**
   - `VideoSource` başlangıç saniyesi (`-ss`) alabilecek, 720p kaynağı kaliteli büyütecek.
   - Klip çekimden kısaysa donmak yerine yavaşlatılacak, olmazsa son kare kullanılacak.
   - Fotoğraf çekimlerine katman karışımı (`cv2.add` ile screen benzeri, opaklık ayarlı) eklenecek.
4. **`archive_images.py`:** Commons video dosyası indirme. İndirme dosyası bu video için webm.
5. **`belgesel.yml`'e `inceleme` modu:**
   - Commons videosundan 15 saniyede bir kare ve plandaki her Pexels sorgusu için 4 aday kare çıkarır.
   - Bunları küçük JPG temas sayfalarına dizer ve `inceleme/hititler` dalına commit'ler. Bu ortam Actions artifact'larını indiremiyor, git dalını ise okuyabiliyor.
   - Ben sayfalara bakıp kesitleri ve ID'leri seçerim.
   - Ayrıca Telegram'a gönderilir, kullanıcı da görsün.
6. **Açıklama:** "Video kaynakları" bölümü eklenecek. Commons videosu için CC BY atfı zorunlu; Pexels çekenleri de nezaketen eklenecek.
7. **Testler:** Yeni çekim türleri, katman karışımı, `-ss` ile kesit süresi, Pexels yanıt ayrıştırma (sahte yanıtla).

## Kullanıcının kendi araştırması için kurallar (kanalı korumak için)
- **Kullanılabilir:** Pexels, Pixabay, Mixkit, Coverr, Wikimedia Commons'taki CC0/CC BY/CC BY-SA/kamu malı videolar.
- **Kullanılamaz:** Başka kanalların YouTube videoları, TV belgeselleri, film sahneleri ("telif yok" yazsa bile), lisansı belirsiz her şey.
- YouTube'daki "Creative Commons" filtreli videolar lisans olarak uygun olabilir, ama YouTube'dan video indirmek YouTube'un kurallarına aykırı. Bu yüzden bunları ancak Wikimedia'ya aktarılmış kopyası varsa kullanırız. Bulduğu her linki önce bana göndersin, lisansını ben kontrol edeyim.
- Bulduğu videoları sohbete yükleyebilir ya da linkini atabilir. Ben lisansı kontrol edip `klipler/` klasörüne alırım.

## Sıra
1. Kod (yukarıdaki 1–7) → test → PR → CI → birleştirme
2. Kullanıcı `PEXELS_API_KEY` ekler
3. `inceleme` modu çalışır → ben kesitleri ve görüntüleri seçerim → tam çekim planı yazılır
4. `ornek` modu (giriş + Bölüm I, ~7 dk) → kullanıcı izler
5. Gemini klipleri ve kullanıcının bulduğu videolar geldikçe plandaki ilgili çekimler değiştirilir; yalnızca etkilenen bölüm yeniden render edilir

## Riskler
- Commons videosu 720p ve amatör çekim olabilir; yazı, filigran veya titrek kamera içerebilir. İnceleme sayfasında temiz kesitler seçilecek, kötüyse az kullanılacak.
- Pexels'te "Anadolu"ya özgü görüntü sınırlı. Yer belirten değil, genel atmosfer görüntüleri kullanılacak (gökyüzü, toz, ateş, su, eller). Yanıltıcı yer iddiası yapılmayacak.
- 1,8 GB indirme Actions'ta birkaç dakika sürer; önbelleğe alınır.

## Doğrulama
- `pytest` (yeni testler dahil) yeşil.
- Yerelde sentetik bir video ile `-ss` kesiti ve katman karışımı denenir; kareler gözle kontrol edilir.
- `inceleme` modu çalışınca temas sayfaları dalda görünür.
- `ornek` çıktısında video oranı ve geçişler kontrol edilir.

---

## 1. Bağlam: neden bu proje

- What If formatı tutmadı. Kanalın 13 videosu toplam 473 izlenme aldı. Korunacak bir izleyici kitlesi yok, yani format değiştirmenin bir kaybı da yok.
- Niş taraması (30–31 Ekim, 72 anahtar kelime, YouTube Data API) Türkçe tarihi en güçlü Türkçe niş olarak gösterdi. Ölçüt: küçük kanalların (10 binden az abone) son 2 yıldaki uzun videoları.

| Niş | Medyan izlenme | Tipik video uzunluğu | Video başına tahmini izlenme saati |
|---|---|---|---|
| Türkçe Osmanlı / Türk tarihi | 4.663 | 52 dk | ~1.370 |
| Türkçe dünya tarihi | 4.020 | 31 dk | ~1.120 |
| İngilizce What If (bugünkü format) | 655 | 8 dk | ~70 |

- Hedef YPP (YouTube İş Ortağı Programı). Bunun için **izlenme saati** gerekiyor. Uzun tarih videosu, video başına What If'in yaklaşık 15–20 katı saat getiriyor.
- Kural: Yalnızca yasal yollar ve YouTube kurallarına uygun yöntemler. Sahte izlenme ya da abone yok, kopya içerik yok.

## 2. Hedef ve dürüst beklenti

**Tam YPP eşiği:** 1.000 abone + 12 ayda 4.000 saat izlenme. *(Hafızamdan; resmi YouTube sayfasından doğrulanmalı.)*

| Senaryo | 2 hafta sonra | 3 ay sonra |
|---|---|---|
| Kötü (videolar küçük kanal medyanının altında kalır) | <100 saat, <50 abone | ~500 saat |
| Orta (medyan civarı) | 200–600 saat | 4.000 saate yaklaşır |
| İyi (en az 1 video patlar) | Eşik mümkün | Eşik geçilir |

- **2 haftada eşik ancak "iyi" senaryoda mümkün.** Plan bu ihtimali en üste çıkarmak için kuruldu, ama bunu garanti edemem.
- **Muhtemel darboğaz abone sayısı.** Uzun tarih videolarında izleyicilerin genelde %1–2'si abone oluyor (doğrulanmamış genel gözlem). 1.000 abone için kabaca 50–100 bin izlenme gerekir.
- **Ölçülemeyenler:** izleyici tutma oranı, öneri (keşfet) trafiği, abone dönüşümü. Kanal bunları ilk videolardan sonra gösterecek.

## 3. Format tanımı

- **Seri adı (öneri):** "Anadolu'nun ve Dünyanın İmparatorlukları". Tek bir oynatma listesi, her video bir sonrakine bağlanır.
- **Uzunluk:** İlk video **30–40 dk** (yaklaşık 4.500–5.500 kelime, dakikada ~140 kelime). Sonrakiler 40–60 dk. Süre metin sayılarak hesaplanır, tahmin edilmez.
- **Yapı:** Kanca (0–30 sn) → Yol haritası (30–60 sn) → 7–10 bölüm (her biri 3–6 dk, kendi alt kancasıyla) → Final (vaat teslim edilir) → Kapanış (tek çağrı: sıradaki video).
### 3.1 Kalite standardı (31 Ekim kararları)

Alınan kararlar: ses ElevenLabs, yapay zekâ video sınırlı, önce kalite, 1440p.

**Ses**
- ElevenLabs Türkçe ses. Önce 2–3 aday sesle 1 dakikalık deneme yapılır, sesi siz seçersiniz.
- Ses parça parça değil, **bağlamlı** üretilir: her parça önceki ve sonraki metni bilir. Böylece ton parçadan parçaya değişmez.
- Telaffuz sözlüğü tutulur (Hattuşa, Şuppiluliuma…). Sayılar ve tarihler metne yazıyla girilir. Cümle ve bölüm aralarına bilinçli duraklar konur.
- Kelime zaman damgaları alınır. Bunlar kesme noktalarını ve altyazıyı belirler.
- Mastering: ses seviyesi -14 LUFS'a eşitlenir (YouTube standardı), hafif sıkıştırma ve "s" sesi yumuşatma uygulanır.
- Fon müziği telifsiz sinematik müzik olur. Anlatım sırasında müzik otomatik alçalır. Her bölüme ruh haline uygun ayrı müzik seçilir.
- Ses efektleri az ve yerinde kullanılır (YouTube Ses Kitaplığı, CC0 arşivler).

**Görsel**
- Ana malzeme müze ve arşiv fotoğrafları (Wikimedia Commons, kamu malı veya CC lisanslı). En az 1920 piksel genişlik, filigransız.
- Tüm görsellere aynı renk tonu uygulanır: sıcak ton, hafif film greni, kenar karartması. Farklı kaynaklardan gelen görseller tek bir film gibi görünür.
- Grafik paketi HTML şablonlarından otomatik üretilir (Chromium hazır): bölüm başlık kartı, yer ve tarih etiketi, alıntı kartı, zaman çizelgesi şeridi. Bütün seride tutarlı kimlik sağlar.
- Haritalar: Wikimedia'daki tarihi haritaların üzerine hareketli ok, işaret ve yakınlaştırma. Hareketli sınır haritaları sonraki faza bırakılır.
- **Yapay zekâ video, sınırlı:** Video başına 10–15 kısa klip, yalnızca kilit anlarda (Kadeş Savaşı, Hattuşa'nın yanışı gibi). Higgsfield veya Replicate ile üretilir. Ekranda "temsili canlandırma" yazar ve YouTube'un "değiştirilmiş içerik" kutusu işaretlenir. Her klip tarihsel hata açısından elle kontrol edilir (dönem kıyafeti, mimari). Önce kredi ve maliyet teklifi alınır, size gösterilir.
- 2.5D derinlik efekti (ön ve arka planı ayrılmış fotoğraf): Replicate'te denenir. İşe yararsa açılışta ve kilit karelerde kullanılır.

**Kurgu ve ritim**
- **5–10 saniyede bir yeni çekim** (önceki plandaki 20–40 sn hatalıydı). 35 dakikalık videoda 200–300 çekim eder. Aynı yüksek çözünürlüklü fotoğrafın farklı detaylarına yakınlaşmak da yeni bir çekim sayılır.
- Kesmeler cümle başlarına senkronlanır (kelime zaman damgalarından).
- Geçişler: düz kesme ve kısa çapraz geçiş. Siyaha kararma yalnızca bölüm aralarında.
- Açılış (ilk 60 sn): en güçlü görsellerden montaj, müzik vuruşu ve kanca cümlesi.

**Render**
- 2560×1440, 30 fps, H.264, yüksek bit hızı, 48 kHz ses. 1440p'ye YouTube daha iyi sıkıştırma (VP9) uygular, 1080p'de izleyen de daha net görür.
- Yumuşak Ken Burns: görsel önce büyütülür, hareket kayan noktalı hesaplanır. Bu, mevcut `create_scene_clip`'teki titreşimi giderir.
- Render bölüm bölüm paralel yapılır (GitHub Actions matrix, her bölüm ayrı iş), sonda birleştirilir. Tek işin 6 saatlik sınırı sorun olmaz.

**Kapak**
- Seriye özel sabit şablon: tek güçlü odak görseli, 2–3 kelime, yüksek kontrast.
- Her video için 3 kapak üretilir. Studio'daki "Test ve karşılaştır" özelliğiyle hangisinin daha çok tıklandığı ölçülür (bunu siz yaparsınız).

**Altyazı:** Türkçe .srt dosyası kelime zaman damgalarından üretilir ve YouTube'a ayrıca yüklenir. Videoya gömülmez.
- **Başlık kalıbı:** "X'in Tam Hikâyesi | Kuruluştan Yıkılışa" / "Tüm X Tarihi". Kapakta 2–4 kelimelik büyük Türkçe yazı.
- **"Uyku için Tarih" sürümü:** Ayrı bir format olarak sonra değerlendirilir. Aynı videonun kopyası "tekrarlanan içerik" riski taşır.

## 4. Fark yaratma (rakiplerden ayrışma)

1. **Kaynaklı doğruluk:** Her olgu en az 2 bağımsız kaynakla doğrulanır. Açıklamada "Kaynaklar" ve "Görsel kaynakları/lisanslar" listesi olur. Rakip çeviri kanalları bunu yapmıyor gibi görünüyor (doğrulanmadı).
2. **Anadolu bakış açısı:** Türk izleyiciye yakın bağlantılar. Örnek: "Hattuşa bugün Çorum'da", "Kadeş Antlaşması İstanbul Arkeoloji Müzesi'nde".
3. **Gerçek eser görüntüleri:** Stok video yok, müze ve arşiv görüntüleri var.
4. **Seri ve oynatma listesi:** Bitiş ekranı ve sabit yorum sıradaki videoya yönlendirir.
5. **Bölümlü (chapters) uzun anlatı:** İzleyici istediği yere atlayabilir.

## 5. Yayın takvimi (ilk 2 hafta)

Konular, taramada güçlü çıkan kelimelerden seçildi. Örnek sayıları küçük, bu yüzden sıra değişebilir.

"Önce kalite" kararı nedeniyle video 1, 2 Kasım'dan 1–3 gün kayabilir. Tarihler bu yüzden **hedeftir**.

| # | Hedef yayın (TR saati) | Konu | Neden |
|---|---|---|---|
| 1 | **3–5 Kasım, 19:00** | Hitit İmparatorluğu'nun Tam Hikâyesi | Taramada küçük kanal videosu 237 bin; Anadolu bağlantısı güçlü |
| 2 | +3–4 gün | Antik Mısır'ın Tam Hikâyesi | Kelime medyanı ~146 bin (n=3) |
| 3 | +3–4 gün | Sümerler: Yazıyı İcat Eden İnsanlar | Medyan ~27 bin |
| 4 | +3–4 gün | 36 Padişah: Osmanlı Hanedanının Tam Hikâyesi | Küçük kanal videosu 1,4 milyon |
| 5 | +3–4 gün | Bizans'ın Tam Hikâyesi | 17 küçük kanal videosu, tutarlı sonuç |

- Tempo: hedef 3–4 günde bir uzun video. Kalite paketi üretim süresini uzatıyor; ilk 2 videodan sonra gerçek süre ölçülüp tempo kesinleşir.
- Yayın saati 19:00 TR (16:00 UTC). Bu bir tahmin; Türk izleyicinin akşam saatine göre seçildi, ölçülmedi.

## 6. Üretim hattı (mevcut sistemin yeniden kullanımı)

### 6.1 Video başına akış
```
1. Konu + kaynak listesi                     (Claude, oturumda)
2. Senaryo + "Doğrula" tablosu (JSON + .md)  (Claude yazar → Gemini'ye ikinci göz → SİZ onaylarsınız)
3. Görsel listesi (Wikimedia Commons dosya adları + lisans)  (Claude seçer)
4. GitHub Actions "belgesel" işi:
   ses (ElevenLabs Türkçe) → görsel indirme → montaj (FFmpeg) → kapak → YouTube'a GİZLİ yükleme
5. Telegram: "video hazır, gizli link" → SİZ izlersiniz → yayın (planlı saat)
```

İlk videolarda senaryoyu ben bu oturumda yazarım. Bu, en yüksek kaliteyi ve en hızlı yolu verir. Gemini ile otomatik senaryo, format oturduktan sonra gelir (Faz 3).

### 6.2 Kod değişiklikleri (Faz 1: video 1 için tam kalite paketi)

| Dosya | Değişiklik | Yeniden kullanılan |
|---|---|---|
| `belgeseller/01-hititler/senaryo.json` (yeni) | Bölümler → paragraflar (ses birimi) → çekimler (5–10 sn, her biri: görsel, kırpma bölgesi, hareket, grafik etiketi, gerekirse yapay zekâ klibi). Ayrıca kaynaklar, lisanslar, telaffuz sözlüğü, başlık, açıklama, 3 kapak yazısı | `scenario_generator.validate_scenario` biçimi |
| `scripts/archive_images.py` (yeni) | Commons API'den indir, ≥1920 px ve lisans kontrolü, yazar ve lisans kaydı | `manual_images.center_crop_to_aspect` |
| `scripts/doc_grade.py` (yeni) | Ortak renk dokusu: ton, gren, kenar karartması (FFmpeg filtre zinciri) | — |
| `scripts/doc_graphics.py` (yeni) | HTML şablonu → Playwright ile şeffaf PNG: bölüm kartı, yer ve tarih etiketi, alıntı kartı, zaman çizelgesi | Kurulu Chromium/Playwright |
| `main.py` | `--belgesel <klasör> [--bolum N]`: senaryoyu dosyadan okur (Gemini atlanır), manuel Telegram görsel akışını atlar, bölüm bölüm çalışır | `run_pipeline`, `PipelineCheckpoint` |
| `scripts/tts_engine.py` | ElevenLabs Türkçe ses (`TTS_VOICE_ID_TR`), önceki/sonraki metinle bağlamlı üretim, kelime zaman damgaları, telaffuz sözlüğü. Yedek: edge-tts `tr-TR-AhmetNeural` | `eleven_multilingual_v2` (Türkçe destekliyor), retry ve kota mantığı |
| `scripts/audio_master.py` (yeni) | -14 LUFS (`loudnorm`), sıkıştırma, "s" yumuşatma, müziğin anlatımda alçalması (`sidechaincompress`), bölüm müziği | `video_assembler.add_background_music` mantığı |
| `scripts/video_assembler.py` | Yumuşak Ken Burns (büyütme + kayan noktalı hareket), 1440p ayarı, çekim kesmelerinin kelime zaman damgasına senkronu, düz kesme + çapraz geçiş, bölüm arası siyaha kararma, grafik bindirme, yapay zekâ klibi yerleştirme, bölüm dosyalarını birleştirme | `create_scene_clip`, `create_scene_clip_from_video` (tpad), `probe_duration`, `concatenate_clips_simple`, `generate_srt` |
| `scripts/youtube_uploader.py` | `defaultLanguage`/`defaultAudioLanguage` = `tr`, kategori 27 (Eğitim), Türkçe açıklama şablonu (kaynaklar + görsel lisansları + bölümler), Türkçe etiketler, .srt altyazı yükleme, Türkçe ilk yorum, oynatma listesi | `_sanitize_tags`, `_add_to_playlist`, `_generate_timestamps` (Türkçe bölüm adlarıyla) |
| `scripts/thumbnail_composer.py` | Türkçe karakter testi (DejaVu Bold destekliyor), tarih teması renkleri | `compose_thumbnail` |
| `.github/workflows/belgesel.yml` (yeni) | Yalnızca `workflow_dispatch` (zamanlayıcı yok). İş 1: ses (tek iş, bağlamlı). İş 2: bölümleri paralel render (matrix). İş 3: birleştirme, mastering, kapak, gizli yükleme. Ara dosyalar Actions artifact olarak taşınır. Mevcut workflow'lara dokunulmaz | `daily-video.yml` kurulum adımları, secrets |
| Yapay zekâ video klipleri | Higgsfield ile oturumda üretilir, önce maliyet teklifi size gösterilir. Onaylanan klipler `belgeseller/01-hititler/klipler/` klasörüne konur (Git LFS gerekmez, klipler küçük; gerekirse Actions artifact) | `create_scene_clip_from_video` |
| `tests/` | Yeni yol için testler: senaryo dosyası, Türkçe açıklama, bölüm zaman damgaları (0:00 ile başlar, ≥3 bölüm, her biri ≥10 sn), arşiv indirme (sahte istekle) | mevcut test kalıpları |

Dokunulmayanlar: Shorts ve What If yolu (silinmez, kullanılmaz), Telegram bot zamanlayıcıları.

### 6.3 Sonraki fazlar
- **Faz 2 (video 2–5 sırasında):** Telegram onay kapısı ("/onay" ile yayınla), senaryonun Telegram'a gönderilmesi, haftalık izlenme saati ve abone raporu (`analytics.py`'ye 4.000 saat ve 1.000 abone ilerlemesi).
- **Faz 3 (format oturunca):** Gemini ile taslak → bölüm bölüm senaryo, otomatik "Doğrula" tablosu, Commons'ta otomatik görsel araması. İnsan onayı her zaman kalır.

## 7. Video 1 zaman çizelgesi (önce kalite; hedef yayın 3–5 Kasım)

| Adım | İş | Kim | Onay kapısı |
|---|---|---|---|
| 0 | 3 Türkçe ElevenLabs sesiyle 1 dakikalık deneme | Claude | **Sesi siz seçersiniz** |
| 1 | Faz 1 kodu + testler → PR → CI yeşil → birleştirme | Claude | — |
| 2 | Hititler senaryosu (~5.000 kelime) + Doğrula tablosu + kaynaklar | Claude | **Senaryoyu okuyup onaylarsınız** |
| 3 | Görsel listesi (çekim planı) + yapay zekâ klip listesi ve maliyet teklifi | Claude | **Klip maliyetini onaylarsınız** |
| 4 | **2 dakikalık örnek bölüm** (açılış): tam kalite paketiyle render | Claude | **Kaliteyi siz onaylarsınız.** Beğenmezseniz tam render'dan önce düzeltilir |
| 5 | Tam render → gizli yükleme, 3 kapak | Actions | **Videoyu izleyip onaylarsınız** |
| 6 | Planlı yayın 19:00 TR | Otomatik | — |

**Riskler:** Kalite paketi kapsamlı. Bir adım takılırsa yayın kayar; bunu saklamam, hemen söylerim. 4. adımdaki örnek bölüm, büyük render'a girmeden kaliteyi görmenizi sağlar.

## 8. Ölçüm ve karar kuralları (baştan yazılı, sonradan değişmez)

- **Takip, video başına:** gün+3 ve gün+7 izlenme, ortalama izleme süresi, izlenme saati, abone kazancı. Analytics 2–3 gün geriden gelir.
- **Kanal geneli:** toplam saat (4.000 hedefi) ve abone (1.000 hedefi), haftalık rapor.
- **Sınırlama:** İlk 5 videoda istatistiksel test yapılmaz (n çok küçük). Sonuçlar yalnızca betimleyici olarak raporlanır.
- **Gözden geçirme kuralı:** 5. videodan sonra gün+7 medyan izlenme 300'ün altındaysa, veya ortalama izleme süresi 4 dk'nın altındaysa, başlık, kapak ve konu stratejisi yeniden ele alınır. Bu eşikler bir başlangıç kuralıdır.
- **Durdurma:** YouTube'dan gelen telif ya da topluluk kuralları uyarısı. Bu durumda üretim durur ve size hemen bildirilir.

## 9. Riskler ve önlemler

| Risk | Önlem |
|---|---|
| "Özgün olmayan / tekrarlanan içerik" (yapay zekâ ses + senaryo) | Kaynaklı ve özgün senaryo, her video farklı yapı, gerçek eser görüntüleri, insan onayı. Mümkünse sizin sesiniz |
| Olgu hatası | Doğrula tablosu; emin olunmayan ifade "kaynaklara göre / tartışmalı" diye yazılır |
| Telif | Yalnızca kamu malı ve CC lisanslı görseller, lisans kaydı tutulur, film veya belgesel klibi kullanılmaz |
| ElevenLabs kotası | 35 dk ≈ 40 bin karakter. Paketinize göre aylık video sayısı belli olur. Kota yetmezse edge-tts Türkçe yedeği var ama kalite düşer; önerim paketi yükseltmek |
| Uzun render süresi (1440p, 200–300 çekim) | Bölüm bölüm paralel render; her iş 6 saat sınırının çok altında. 2 dakikalık örnekle süre ölçülür |
| Yapay zekâ klibinde tarih hatası | Her klip elle kontrol edilir, "temsili" etiketi, değiştirilmiş içerik beyanı |
| Yapay zekâ kredisi | Önce teklif, onay olmadan üretim yok |
| Kanal kimliği karışıklığı | Kanal adı, görsel ve açıklama değişikliği (Studio'da, siz). Eski What If videoları gizli yapılabilir (silinmez) |

## 10. Kararlar

**Verilenler (31 Ekim):** ses ElevenLabs · yapay zekâ video sınırlı · önce kalite · 1440p · bu kanalda Türkçe tarih serisi.

**Bekleyenler:**
1. **ElevenLabs paketiniz** ve aylık karakter kotanız (aylık video sayısını belirler). Sesi deneme sonrası seçeceğiz.
2. **Kanal adı:** Örnekler: "Tarih Dosyaları", "İmparatorluklar", "Anadolu'dan Dünyaya". Değişikliği siz Studio'da yaparsınız.
3. **Eski What If videoları:** Gizli yapılsın mı (önerim), yoksa kalsın mı?
4. **İlk video süresi:** 30–40 dk (önerim) mı, 60 dk mı?
5. **Yayın saati:** 19:00 TR uygun mu?
6. **Yapay zekâ video bütçesi:** Video başına üst sınır ne olsun? Teklifi ben çıkarırım, siz onaylarsınız.

## 11. Doğrulama (iş bitince nasıl kontrol edilir)

- `pytest` tüm testler yeşil olmalı (CI).
- Yerel kuru çalıştırma: `python main.py --belgesel belgeseller/01-hititler --bolum 1 --no-upload` (ElevenLabs yerine edge-tts ile) bir bölüm üretir. Kontroller: çekim kesmeleri cümle başlarında mı, Ken Burns titremiyor mu, renk tutarlı mı, grafikler okunaklı mı.
- Ses ölçümü: `ffmpeg -af ebur128` ile -14 LUFS (±1) doğrulanır.
- Teknik ölçüm: `ffprobe` ile 2560×1440, 30 fps, 48 kHz doğrulanır.
- Gerçek çalışma: Actions'ta `belgesel` işi → gizli yükleme → başlık, açıklama, bölümler, altyazı ve kapak Studio'da kontrol edilir → siz onaylarsınız → yayın.
- Bu plan onaylanınca `docs/PROJE_PLANI_TARIH_SERISI.md` olarak depoya da eklenir; gelecek oturumlar bu belgeden devam eder.
