# Sosyal medya kurulumu (TikTok · Instagram · Facebook)

Short'lar YouTube'da yayınlandığı akşam saat **18:05**'te sosyal medyaya da gider. Bunu `sosyal.yml` adlı otomatik iş yapar.

Platformlara göre durum şöyle:

| Platform | Nasıl çalışır | Sizin işiniz |
|---|---|---|
| **TikTok** | Bot, videoyu ve açıklamasını Telegram'a gönderir | Günde ~1 dakika: Telegram'dan kaydet, TikTok'ta paylaş |
| **Instagram Reels** | Tam otomatik | Bir kez kurulum (aşağıda) |
| **Facebook Reels** | Tam otomatik | Instagram kurulumuyla birlikte yapılır |

Kurulum bitene kadar yalnızca Telegram adımı çalışır, diğer adımlar hata vermeden atlanır. İlk paylaşım **16 Kasım**'da. Takvim şöyle:

| Tarihler | Short'lar |
|---|---|
| 16–20 Kasım | İstanbul |
| 21–25 Kasım | Mısır |
| 26–30 Kasım | Hitit |

Yeni belgesellerin Short'ları, YouTube'da yayınlandıkları gün paylaşılır.

---

## 1) TikTok (5 dakika)
1. TikTok uygulamasında yeni hesap açın. Kullanıcı adı: **@tarihdosyalari** (alınmışsa @tarih.dosyalari). Ad: **Tarih Dosyaları**.
2. Profil resmi olarak Telegram'a gelen **profil.png**'yi yükleyin.
3. Biyografi: *Anadolu'dan dünyaya imparatorlukların tam hikâyesi. Tam belgeseller YouTube'da 👇* ve altına YouTube kanal bağlantısı.
   - TikTok, biyografide bağlantıya ancak belirli bir takipçi sayısından sonra izin veriyor. O zamana kadar sadece yazı kalsın.
4. **Her gün yapılacak:**
   1. Telegram'a gelen videoya dokunun → **Kaydet**.
   2. TikTok → **+** → videoyu seçin.
   3. Telegram'daki ikinci mesajdaki açıklamayı kopyalayıp yapıştırın.
   4. Videoda temsili canlandırma varsa (açıklamada "ℹ️" satırı görünür), **Diğer seçenekler → "Yapay zekâ ile oluşturulmuş içerik"** anahtarını açın. TikTok bunu zorunlu tutuyor.

## 2) Instagram (5 dakika)
1. Yeni hesap açın: **@tarihdosyalari**, ad **Tarih Dosyaları**, profil resmi **profil.png**.
2. **Profesyonel hesaba geçin.** Otomatik paylaşım için şart, ücretsiz:
   1. Profil → ☰ → **Hesap türü ve araçlar** → **Profesyonel hesaba geç**.
   2. **İçerik üreticisi** → kategori: **Eğitim** (ya da "Dijital içerik üreticisi").
3. Biyografi: TikTok'taki metin. Bağlantı: YouTube kanalı.

## 3) Facebook Sayfası ve Instagram'a bağlama (5 dakika)
Meta, Instagram'a otomatik paylaşım için bir Facebook Sayfası istiyor.
1. Facebook → Menü → **Sayfalar** → **Yeni Sayfa oluştur**.
   - Ad: **Tarih Dosyaları**.
   - Kategori: **Eğitim web sitesi** ya da **Medya/haber şirketi**.
2. Sayfanın kendisinde: **Ayarlar** → **Bağlı hesaplar** (ya da "Instagram") → **Hesabı bağla** → Tarih Dosyaları Instagram hesabıyla giriş yapın.

## 4) Meta erişim anahtarı (bilgisayardan, 15 dakika)
Bu adım bir kere yapılır. İsterseniz bilgisayar başına geçtiğinizde ekranları birlikte adım adım yaparız.

1. **https://developers.facebook.com** → Facebook hesabınızla giriş → **Başlayın** (geliştirici olarak kaydolun).
2. **Uygulamalarım** → **Uygulama oluştur**:
   - Ad: `Tarih Dosyalari Paylasim`
   - Kullanım amacı: **Diğer** → Uygulama türü: **İşletme**
3. Uygulama panelinde **Ürün ekle**:
   - **Instagram** (Facebook Girişi ile Instagram API)
   - **Facebook Girişi (İşletme için)**
4. **Araçlar → Graph API Gezgini** (https://developers.facebook.com/tools/explorer):
   1. Sağ üstte uygulama olarak `Tarih Dosyalari Paylasim`'ı seçin.
   2. **Kullanıcı erişim anahtarı al**'a basın ve şu izinleri işaretleyin:
      `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `publish_video`, `business_management`, `instagram_basic`, `instagram_content_publish`
   3. **Oluştur** → çıkan pencerede Sayfayı ve Instagram hesabını seçip onaylayın.
5. **Uzun süreli anahtar:**
   1. **Araçlar → Erişim Anahtarı Hata Ayıklayıcı**'ya gidin.
   2. Gezgindeki anahtarı yapıştırın → **Hata ayıkla** → en altta **Erişim anahtarını uzat**.
   3. Çıkan yeni anahtarı kopyalayın.
6. **Sayfa anahtarı ve kimlikler:**
   1. Graph API Gezgini'nde yeni anahtarı yapıştırın.
   2. Sorgu kutusuna `me/accounts` yazıp **Gönder**'e basın.
   3. Sonuçta **Tarih Dosyaları** sayfasının iki değerini kopyalayın:
      - `access_token` → bu **META_PAGE_TOKEN** (süresiz)
      - `id` → bu **META_PAGE_ID**
   4. Sorgu kutusuna `<META_PAGE_ID>?fields=instagram_business_account` yazıp **Gönder**'e basın.
      - Çıkan `id` → bu **META_IG_USER_ID**
7. **GitHub'a ekleyin:**
   1. Depo → **Settings → Secrets and variables → Actions → New repository secret**.
   2. Üç secret ekleyin: `META_PAGE_TOKEN`, `META_PAGE_ID`, `META_IG_USER_ID`.
   3. ElevenLabs anahtarını eklediğiniz yöntemin aynısı.

⚠️ Bu anahtarlar şifre gibidir. Sohbete ya da Telegram'a yazmayın, yalnızca GitHub Secrets'a girin.

Bana "anahtarları ekledim" deyin. Önce bir deneme paylaşımı yapacağım, ardından otomatik paylaşım başlayacak.

## Sorun çıkarsa
- Her gün Telegram'a **"📣 Sosyal medya paylaşımı"** özeti gelir.
- Bir platformda hata olursa özetin içinde ⚠️ ile yazılır. Diğer platformlar paylaşılmaya devam eder.
- Tek bir Short'u elle yeniden paylaşmak için: GitHub → Actions → **Sosyal Medya Paylaşımı** → Run workflow → `klasor` ve `id` alanlarını doldurun.
