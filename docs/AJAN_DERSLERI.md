# AJAN DERSLERİ — Başka projelerden alınan ve bu projeye uyan bilgiler

Son güncelleme: 2026-10-30. Kaynak: kullanıcının verdiği üç belge (Unfoldables otomasyon ajanı devir belgesi, kanal büyüme analisti skill'i, YouTube niş ve içerik yetenekleri). Burada yalnızca bu projeye uyan kısımlar ve onlara itirazlar var. `DEVIR_NOTU.md` ile birlikte okunur.

## 1. Çalışma ilkeleri (öncekilere ek)
- **Veriye dayan, onaylayıcı olma.** Kullanıcının fikri veriyle çelişiyorsa sayıyla göster, kararı yine kullanıcıya bırak.
- **Her bulguya güven düzeyi yaz** (yüksek / orta / düşük + neden). Ölçülemeyenleri ayrıca listele.
- **Hafızadan gelen bilgi kanıt değildir.** YouTube politikası, YPP eşikleri, RPM, tarihsel olgular: "doğrulanmadı" etiketi + kaynak önerisi. Uydurma sayı yok.
- **Kendi hatanı söyle.** Yanlış tahmin ettiysen (süre, sayı) düzelt ve açıkça belirt. Metni say, tahmin etme.
- **Rapor sırası:** ne oldu → ne anlama geliyor → kullanıcının yapması gereken. Kısa, tablolu, Türkçe. Saatleri UTC + Türkiye saati (UTC+3) ile yaz.
- **Boş bildirim yok;** arıza kesinti başına bir kez bildirilir.
- **Karar anında tek net öneri** + gerekçe + güven düzeyi; uzun seçenek listesiyle boğma.
- **Konu dışı iş bitince ana işe dön** ve bunu söyle.

## 2. Strateji dersleri (yön kararı için en önemlisi)
- **Yönü veriyle sına.** "Türkçe, gerçek görüntülü, nasıl oldu belgeseli" kararı henüz veriyle sınanmadı. Otomasyona yatırım yapmadan önce niş ölçümü yapılır (§4).
- **Politika riski:** "Yüzsüz + yapay zekâ senaryosu + yapay zekâ sesi + stok görüntü" YouTube'un "özgün olmayan / tekrarlanan içerik" kuralı (Temmuz 2025 sıkılaştırması) açısından yüksek risk. Azaltanlar: kaynaklı ve doğrulanmış senaryo, insan katkısı (mümkünse kendi ses), her videoda özgün değer, şablon tekrarından kaçınma. *(Politika ayrıntısı hafızadan; resmi sayfadan doğrula.)*
- **Belgeselde olgu doğruluğu şart.** Senaryodaki her tarih, sayı, isim, neden-sonuç ilişkisi kaynakla doğrulanana kadar "Doğrula" tablosunda işaretli kalır. En az iki bağımsız kaynak yoksa o konu işlenmez. Emin olunmayan ifade "anlatımlara göre" ile yumuşatılır.
- **Uzun video iskeleti:** Kanca (0–15 sn: başlığın vaadini doğrula, kapanmamış bir soru aç) → Yön (15–45 sn, kanal tanıtımı yok) → Gövde (her bölümde ekran notu) → Ödül (vaadi açıkça teslim et) → Kapanış (tek çağrı). 5 kanca yaz, en iyi 2'sini seç; abartılı "hiç duymadınız" iddiası kullanma.
- **Hit'i kontrol eden bir kol bulunamayabilir.** Büyük bir Shorts kanalında hiçbir meta veri (konu, başlık, saat, emoji) hit'i açıklamadı. Elde kalan kollar: konu seçimi, üretim kalitesi, hacim. Format üzerinde küçük oynamalarla mucize bekleme.

## 3. YouTube verisi ve ölçüm
- **Shorts:** `views` her oynatmayı sayar. YPP eşiği ve gerçek erişim için `engagedViews` bakılır (başka kanalda views'in ~%42–45'i). `scripts/analytics.py` şu an yalnızca `views` çekiyor → Shorts yorumları iyimser.
- **Gecikme:** Analytics ~2–3 gün geriden gelir; günler Pasifik saatine göredir. Studio uygunluk kartı daha da geride.
- **API tuzakları:** `dimensions=video` sorgusu `maxResults` olmadan boş döner. Impressions/CTR API'de yok (bkz. DEVIR_NOTU §6.5). API yorum sabitleyemez.
- **Videolar aynı yaşta karşılaştırılır** (yayın günü + k gün). Kanal büyürken ham izlenme yanıltır.
- **İstatistik kuralları:** p-değeri olmadan "işe yaradı" denmez; çoklu test → Holm; grup başına en az 8 olgun video, yoksa sonuç "yeterli veri yok" (meşru bir sonuç). Bu kanalda şu an hiçbir format sonucu kanıtlanmış değildir.
- **Deney kuralları başlamadan dosyaya yazılır,** eşikler sonradan değiştirilmez.

## 4. Niş ölçümü yöntemi (YouTube Data API)
- Soru: *Küçük bir kanalın uzun videosu bu nişte aramada çıkıp izlenebiliyor mu?*
- Ölçüt: abone < 10.000, süre > 180 sn (Shorts hariç), son 730 gün. Metrikler: örnek sayısı, medyan izlenme, bootstrap %80 güven aralığı, 1.000+ / 10.000+ payı, yeni kanal (≤540 gün) kırılımı, büyük kanal (100k+) payı.
- Her niş için ~8 anahtar kelime (izleyicinin gerçekten yazacağı ifadeler).
- Kota: `search.list` 100 birim, günlük 10.000 → günde ~95 kelime. Kota bitince `429` gelir; yanıtlar önbelleğe alınır.
- Tuzaklar: Shorts izlenmeyi şişirir; küçük örneklem (aralıklar çakışıyorsa sıralama yok); hayatta kalan yanlılığı (rakamlar iyimser üst sınır); geniş ifade ≠ niş; mevsimsellik. **Arama verisi önerilen video trafiğini ölçmez.**
- Bu oturumda `www.googleapis.com` proxy ile bağlı (YouTube Data API); anahtar sohbete yazılmaz.
- Önceki projeden bulgu (Ekim 2026, başka depo, doğrulanmamış): İngilizce tarih (ortaçağ/imparatorluklar, antik Yakın Doğu) küçük kanallar için güçlü; kalıp "The ENTIRE History of X", 20–45 dk. Türkçe tarih/belgesel için veri yok.

## 5. Bu depoya dair tespitler (kodda görüldü)
| Tespit | Yer | Durum |
|---|---|---|
| Shorts için `engagedViews` yok | `scripts/analytics.py` | Öneri, onay bekliyor |
| `git pull --rebase … \|\| true`: çakışmada rebase yarım kalabilir, durum kaybolabilir | `daily-video.yml`, `telegram-bot.yml` commit adımı | Olası risk, canlıda doğrulanmadı |
| Gemini yedek modeli var (2.5-flash → 2.0-flash) | `scripts/scenario_generator.py` | Tamam |
| "Önce kaydet sonra bildir": `complete_production` içindeki erken mesaj yalnız bilgilendirme | `scripts/manual_images.py` | Sorun yok |
| Senaryoda olgu doğrulama adımı yok | `scripts/scenario_generator.py` | Belgesel formatı için gerekli |

## 6. Belgelere itirazlar (körü körüne alma)
- **YPP eşikleri:** Bir belge "alt kademe 1.000 abone + 3M" diyor. Hafızama göre alt kademe 500 abone + 3M Shorts izlenmesi (veya 3.000 saat); tam YPP 1.000 abone + 10M Shorts izlenmesi (veya 4.000 saat). Resmi sayfadan doğrulanmalı.
- **5,5 saatlik yoklama döngüsü** yüksek hacimli kanal içindir; bizim düşük hacmimizde gereksiz Actions dakikası harcar.
- **Özel JSON merge driver** yalnız iki iş aynı dosyayı sık yazıyorsa gerekir; bizde `concurrency: video-bot` zaten işleri sıraya koyuyor.
- Dış görüşler (uzman, başka ajan, bu belgeler dahil) hesapla doğrulanır.

## 7. Araç: Graphify (kod bilgi haritası)
- Kullanıcının fork'u: `esracakalli1990-sketch/graphify` (Apache-2.0, Graphify-Labs). Kodu harita haline getirir; kod kısmı yerel çalışır, yapay zekâ kullanmaz.
- Kurulum (her yeni oturumda, konteyner geçici):
  ```bash
  git clone --depth 1 https://github.com/esracakalli1990-sketch/graphify /home/user/esracakalli1990-sketch/graphify
  uv tool install /home/user/esracakalli1990-sketch/graphify
  graphify update .
  ```
- Kullanım: `graphify explain "complete_production"`, `graphify path "A" "B"`, genel bakış için `graphify-out/GRAPH_REPORT.md`. Kod değiştikten sonra `graphify update .`.
- `graphify-out/` commit edilmez (`.gitignore`'da).

## 8. GitHub Actions kotası (20 Kasım 2026)
- Hesabın ücretsiz Actions dakikaları (private depolar için ayda 2.000, tüm depolar ortak) 14 Kasım'da bitti; tüketimin çoğu başka bir depodan.
- **Bu depo public kalmalı.** Public depolarda standart runner ücretsiz ve kotaya sayılmaz. Private yapılırsa tek bir belgesel üretimi (1–3 saat) kotanın büyük kısmını yer ve hesaptaki diğer depoları da durdurur.
- Yeni cron eklerken aylık dakikayı hesapla: günlük çalışma × 30 × ortalama dakika (en az 1). Şu an tek cron `sosyal.yml` (günde 1).
- Her iş akışında `timeout-minutes` ve `concurrency` olmalı.
- Uyku belgeseli kapakları: büyük yazı her zaman "UYKU BELGESELİ" (rakip uyku kanallarındaki gibi), konu adı köşede küçük etiket. `doc_timeline.validate` slugında "uyku" geçen senaryoda bunu denetler.
