# İstanbul'un Fethi — Çekim Senaryosu (v2)

Bu belge, her paragraf okunurken **ekranda ne görüneceğini** gösterir. Senaryo ve ses aynen kalıyor; yalnızca görüntü baştan kuruluyor.

## İşaretler
| İşaret | Anlamı | Kim hazırlar |
|---|---|---|
| 🎥 | **Gerçek mekân videosu.** İstanbul'da çekilmiş gerçek görüntü (Pexels; numara Pexels kimliği) | Ben (seçildi) |
| 🎬 K1–K12 | Elimizdeki 12 Gemini klibi, **her biri yalnızca 1 kez** | Hazır |
| 🎬 Y1–Y21 | **Yeni Gemini klipleri** (komutlar: `klip_promptlari_v2.md`) | Siz |
| 🖼️ T1–T5 | **Canlandırılmış tarihi tablo** (gerçek tablo + Gemini ile hafif hareket) | Siz |
| 🗺️ | Harita / bilgi grafiği / kişi kartı (Remotion) | Ben |
| 📷 | Gerçek eser fotoğrafı (yalnızca eserin kendisi: portre, top, mozaik, harita) | Ben |

## Kurallar
1. Önceki videolardan (Hitit, Mısır) **hiçbir görüntü kullanılmaz.** Ateş, mum, sis ve kıvılcım katmanları tamamen kaldırıldı.
2. Gerçek videonun **gerçekten o yerde çekilmiş** olması gerekir. Aramada çıkan Verona, Çin ve Bodrum görüntüleri elendi. "Eski top" ve "taş sur" aramalarından İstanbul'a ait tek bir görüntü çıkmadı; o sahneler klip ya da haritayla çözüldü.
3. Bir gerçek video en fazla 2 kez kullanılır ve iki kullanım birbirinden uzak yerlerde olur. Bir Gemini klibi 1 kez, bir fotoğraf en fazla 2 kez kullanılır. Uzun bir klip iki parçaya bölünebilir, ama aynı saniyeler iki kez gösterilmez.
4. **1453 anlatılırken modern görüntü yok.** İstanbul'un gerçek görüntülerinde hemen her zaman köprü, vapur ya da sonradan yapılmış camiler var. Bu yüzden gerçek görüntüler yalnızca şu anlarda kullanılıyor:
   - "Bu yer neresi / bugün nasıl" anları: giriş, şehrin tanıtımı, surların tanıtımı, fetih sonrası, kapanış. Bu anlarda ekranda "BUGÜN" yazar.
   - Modern hiçbir şey görünmeyen kadrajlar: açık deniz, ay tutulması, Rumeli Hisarı'nın köprüsüz yakın çekimi.
5. **Kişi kartı yalnızca gerçek portresi olana yapılır:** Fatih (Bellini) ve Konstantin (15. yüzyıl minyatürü). Diğerleri temsili klipte, ekranın altında isim yazısıyla tanıtılır.

## Dürüst not: oranlar
Hedefim gerçek mekân videosunu %35'e çıkarmaktı. Bunu ancak 1453 sahnelerine modern İstanbul görüntüsü koyarak yapabilirdim; bu da izleyiciyi yanıltır. Gerçekçi oranlar şöyle:

| Katman | Pay |
|---|---|
| 🎬🖼️ Gemini (eski 12 + yeni 21 + 5 tablo) | ~%35 |
| 🗺️ Harita / grafik | ~%25 |
| 🎥 Gerçek mekân videosu (44 çekim) | ~%22 |
| 📷 Gerçek eser fotoğrafı | ~%18 |

Durağan fotoğraf payı %55'ten %18'e iniyor. Hititler'i sinematik yapan "hareketli görüntü" duygusu bu kez Gemini klipleri ve canlandırılmış tablolardan gelecek.

---

## GİRİŞ

**0.0** *"Yirmi iki Nisan… gemiler karada ilerliyor…"*
- 🎬 **K1** gemiler karadan iniyor · yazı "22 NİSAN 1453 · GALATA SIRTLARI · TEMSİLİ CANLANDIRMA"
- 🎬 **Y10** (ilk yarı) yelkenleri açık gemi tepeye tırmanıyor

**0.1** *"Sabah… Bizans nöbetçileri gözlerine inanamadı…"*
- 🎬 **K2** surdaki nöbetçi
- 🎥 **19671347** şafakta tarihî yarımada ve Haliç, puslu geniş kadraj

**0.2** *"…yirmi bir yaşında bir sultan… Fatih… elli üç günün hikâyesi."*
- 🎬 **Y1** Fatih ordugâhtan surlara bakıyor
- 📷 Bellini portresi, yavaş yaklaşma
- 🎥 **32304331** Yedikule ve kara surları, havadan

**0.3** *"Bu videoda: hisar, dev toplar, karadan yürüyen gemiler…"* (hızlı fragman)
- 🎥 **31639721** Rumeli Hisarı, alacakaranlıkta havadan → 📷 şahi topu → 🗺️ gemiler_karadan (kısa) → 🎬 **K8** (ilk 3 sn)

## I. KIZIL ELMA

**1.0** *"İki denizin, iki kıtanın birleştiği nokta…"*
- 🎥 **34432985** tarihî yarımada denizden, puslu
- 🎥 **37789039** Sarayburnu: Boğaz, Haliç ve Marmara'nın birleştiği yer
- 📷 Buondelmonti haritası (1422) · yazı "KONSTANTİNOPOLİS"

**1.1** *"Araplar… Yıldırım Bayezid… Anadolu Hisarı…"*
- 🗺️ eski_kusatmalar
- 🎥 **32220990** Anadolu Hisarı, havadan · yazı "ANADOLU HİSARI · 1394"

**1.2** *"Ebu Eyyub el-Ensari…"*
- 🎥 **29217883** Eyüp Sultan Camii · yazı "EYÜP SULTAN · BUGÜN"

**1.3** *"Bizans eski gücünün gölgesiydi…"*
- 🗺️ bizans_kuculme
- 🎬 **Y2** yarı boş Konstantinopolis

**1.4** *"Kızıl Elma…"*
- 🎥 **35615255** Kız Kulesi önünde gün doğumu, martılar

**1.5** *"Surlar bin yıldır hiç yıkılmamıştı… Bambaşka bir şey."*
- 🎥 **34490200** kara surlarında bir kapı, yavaş yaklaşma

## II. GENÇ SULTAN

**2.0** *"Edirne'de doğdu… Büyük İskender'i okumayı seviyordu."*
- 🗺️ **Fatih kişi kartı** (Bellini)
- 🎬 **Y3** (ilk yarı) genç Mehmed mum ışığında okuyor

**2.1** *"On iki yaşında tahta çıktı…"*
- 📷 Osmanlı saray minyatürü (1498), kaydırma
- 📷 Costanzo madalyası

**2.2** *"Varna…"*
- 🗺️ varna_1444
- 🖼️ **T4** Matejko'nun Varna tablosu

**2.3** *"Manisa'da sancakbeyi…"*
- 🎬 **Y3** (ikinci yarı)

**2.4** *"…on dokuz yaşında ikinci kez tahta çıktı…"*
- 🎥 **31774009** Edirne, Meriç üzerinde köprü (Selimiye görünmüyor) · yazı "EDİRNE · BUGÜN"
- 📷 Bellini portresi (2. ve son kullanım)

**2.5** *"Çandarlı… Zağanos… geceleri planlar çiziyordu."*
- 🎬 **Y4** Fatih gece planı çiziyor
- 🗺️ sehir_plani

**2.6** *"İlk adım, şehrin can damarını kesmekti."*
- 🎥 **37191274** Boğaz'ın açık suyu

## III. BOĞAZKESEN

**3.0** *"Anadolu Hisarı… tam karşısına…"*
- 🗺️ bogazkesen
- 🎥 **33294992** Rumeli Hisarı denizden

**3.1** *"Binlerce usta… dört buçuk ayda…"*
- 🎬 **Y5** hisar inşaatı
- 🎥 **33294993** Rumeli Hisarı kuleleri, köprüsüz kadraj · yazı "RUMELİ HİSARI · BOĞAZKESEN · 1452"
- 🗺️ g_hisar

**3.2** *"Boğazkesen… Venedik gemisi batırıldı…"*
- 🎬 **K3** hisardan top atışı

**3.3** *"Bizans imparatoru… Avrupa'ya mektuplar…"*
- 🗺️ **Konstantin kişi kartı** (15. yy minyatürü)
- 🎥 **35977724** gri, sisli Boğaz

**3.4** *"Gelibolu'da büyük bir donanma…"*
- 🗺️ donanma_gelibolu
- 🎥 **39394631** açık deniz

**3.5** *"Kışın Edirne'de… zayıf noktalar…"*
- 📷 Schreiber gravürü, kaydırma
- 🗺️ kusatma_dizilis (ilk kısım)

## IV. SURLARI YIKACAK TOP

**4.0** *"Urban…"* — 🎬 **Y6** (ilk yarı) dökümhane · yazı "URBAN · TOP DÖKÜMCÜSÜ (TEMSİLİ)"
**4.1** *"…Dökebilirim."* — 🎬 **Y6** (ikinci yarı)
**4.2** *"Sekiz metre… deneme atışı…"* — 🗺️ g_top · 🎬 **K4** dev topun ateşlenmesi
**4.3** *"Onlarca çift öküz…"* — 🗺️ topun_yolu · 🎬 **Y7** öküzler topu çekiyor
**4.4** *"…bugün İngiltere'de bir müzede…"* — 📷 şahi topu · yazı "OSMANLI TOPU · 1464" · 📷 yakın plan
**4.5** *"Onlarca top gruplar hâlinde…"* — 🗺️ top_mevzileri · 📷 kuşatma maketi (Askerî Müze)

## V. BİN YILLIK SURLAR

**5.0** *"Theodosius surları…"*
- 🎥 **32304330** surlar boyunca uzun hava çekimi · yazı "THEODOSİUS SURLARI · BUGÜN"
- 🎥 **32304332** Yedikule kuleleri

**5.1** *"Hendek… dış sur… iç sur…"* — 🗺️ g_sur_kesiti · 🎥 **32304336** sur hattı, yakından

**5.2** *"Haliç'in ağzına zincir…"* — 🗺️ sehir_plani (zincir) · 🎥 **19057675** Haliç'in suyu

**5.3** *"Konstantin… Giustiniani…"* — 🎬 **Y8** Ceneviz gemileri · yazı "GİOVANNİ GİUSTİNİANİ (TEMSİLİ)" · 🗺️ g_iki_taraf

**5.4** *"Kiliselerin birleşmesi… Notaras…"* — 🎥 **10716775** Ayasofya'daki Bizans mozaiği · 🎥 **38530731** Ayasofya'nın içi, ışık huzmeleri

**5.5** *"Haçlı ordusu hiç gelmedi."* — 🎥 **30734481** bomboş ufuk

**5.6** *"Altı Nisan… toplar mevzide."* — 🗺️ kusatma_dizilis · 🎬 **K12** (ilk yarı) yeniçeriler

## VI. KUŞATMA BAŞLIYOR

**6.0** *"Toplar konuşmaya başladığında…"* — 🎬 **Y9** gülleler surlara çarpıyor · 🎥 **32304336** (2. kesit) bugünkü sur hattı
**6.1** *"Gedikleri geceleri kapatıyorlardı…"* — 🖼️ **T3** Le Tavernier minyatürü (uzun kaydırma)
**6.2** *"On sekiz Nisan gecesi…"* — 🎬 **K8** gece hücumu
**6.3** *"Zinciri kırmayı denedi…"* — 🗺️ sehir_plani (zincir saldırısı) · 🎥 **19671347** (2. kesit)
**6.4** *"Dört gemi…"* — 🗺️ deniz_savasi · 🎬 **Y11** deniz savaşı
**6.5** *"…atını denize sürdü."* — 🎬 **K5**
**6.6** *"…kimsenin aklına gelmeyecek bir hamle."* — 🎥 **31822117** Galata'nın arkasındaki sırtlar, havadan · yazı "GALATA SIRTLARI · BUGÜN"

## VII. GEMİLER KARADAN YÜRÜYOR

**7.0** *"Gemiler denizden giremiyorsa…"* — 🗺️ gemiler_karadan · 🎥 **14441647** Haliç, havadan
**7.1** *"Kalaslar yağlandı… kızaklar…"* — 🎬 **K6** · 🗺️ g_gemiler
**7.2** *"Yirmi iki Nisan gecesi… yelkenleri açık…"* — 🎬 **Y10** (ikinci yarı) · 🖼️ **T1** Zonaro'nun gemiler tablosu
**7.3** *"Sabah olduğunda Haliç'in içinde…"* — 🎬 **Y12** surlarda şaşkınlık, çan
**7.4** *"Askerî tarihin en cesur manevrası…"* — 🎥 **34432939** Galata ve Beyoğlu sırtları · yazı "GEMİLERİN YOLU · BUGÜN BEYOĞLU" · 📷 Costanzo madalyası (2. ve son)
**7.5** *"Venedik gece baskını…"* — 🗺️ venedik_baskini · 🎬 **Y13**
**7.6** *"Yüzer köprü…"* — 🗺️ yuzer_kopru · 🎬 **Y14**

## VIII. TOPRAK ALTINDA SAVAŞ

**8.0** *"Lağımcılar tünel kazmaya başladı…"* — 🗺️ g_tunel · 🎬 **Y15**
**8.1** *"Madenciler… duman, su, göğüs göğüse…"* — 🎬 **Y16** · 🗺️ g_tunel'in karşı tünel aşaması
**8.2** *"Kuşatma kulesi gece yakıldı…"* — 🎬 **K7** · 🖼️ **T5** Schreiber gravürü
**8.3** *"Ay tutulması… kubbede ışıklar…"* — 🎥 **11229446** gerçek ay tutulması · 🎥 **12030510** alacakaranlıkta Ayasofya
**8.4** *"Teslim teklifi… Konstantin reddetti…"* — 🎬 **K11** elçi · 📷 Konstantin minyatürü (2. kullanım)
**8.5** *"Son divan… Akşemseddin'in mektupları…"* — 🎬 **Y17** savaş divanı · yazılar "ÇANDARLI HALİL PAŞA" / "ZAĞANOS PAŞA" (TEMSİLİ) · 📷 saray minyatürü (2. ve son)
**8.6** *"Oruç, dua, meşaleler…"* — 🎬 **Y18** gece ordugâh

## IX. SON HÜCUM

**9.0** *"Davullar, zurnalar, tekbirler…"* — 🗺️ son_hucum · 🎥 **39618754** gerçek mehter takımı
**9.1** *"Yeniçeriler… Sultan hendeğin kenarında…"* — 🎬 **K12** (ikinci yarı) · 🎬 **Y19** Fatih hendek kenarında
**9.2** *"Giustiniani ağır yaralandı…"* — 🎬 **Y20** · yazı "GİUSTİNİANİ (TEMSİLİ)"
**9.3** *"Kerkoporta…"* — 🗺️ kerkoporta · 🎥 **34490200** (2. kesit) sur kapısı
**9.4** *"Ulubatlı Hasan…"* — 🎬 **K9** · yazı "ULUBATLI HASAN"
**9.5** *"Son imparator şehrini terk etmedi…"* — 🎬 **Y21** · 📷 Konstantinopolis duvar resmi
**9.6** *"Surlarda Osmanlı sancakları…"* — 🎥 **35615255** (2. kesit) şafak · yazı "29 MAYIS 1453"

## X. FETİH

**10.0** *"Genç sultan şehre girdi…"* — 🎬 **K10** · 🖼️ **T2** Zonaro "Fatih'in İstanbul'a girişi" (ilk kısım)
**10.1** *"Ayasofya camiye çevrildi…"* — 🎥 **19163087** Ayasofya, havadan · 🎥 **38530728** kubbe ve hat levhaları
**10.2** *"Rumlara güvence… patrik… Galata'ya ahitname…"* — 📷 Fatih ve Gennadios mozaiği · 🎥 **18293182** Galata Kulesi (Ceneviz yapısı, 1348)
**10.3** *"Osmanlı başkenti olarak yeniden doğdu…"* — 🗺️ osmanli_yukselis · 🎥 **34432986** Topkapı ve tarihî yarımada
**10.4** *"Topkapı… Fatih Camii… bedesten…"* — 🎥 **19312245** Topkapı Sarayı, havadan · 📷 Fatih Camii (Wikimedia hava fotoğrafı) · 🎥 **36403074** Kapalıçarşı
**10.5** *"Eyüp Sultan…"* — 🎥 **29218872** Eyüp Sultan avlusu
**10.6** *"Orta Çağ'ın sonu…"* — 🖼️ **T2** (son kısım, uzaklaşma) · 🎥 **35314400** gün batımı

## KAPANIŞ
**11.0** *"Bugün İstanbul'da yürürken…"* — 🎥 **31639721** (2. kesit) Rumeli Hisarı → 🎥 **32304331** (2. kesit) surlar → 🎥 **18293215** Ayasofya → 🎥 **34432926** gece İstanbul

---

## Özet
| | |
|---|---|
| Eski klipler K1–K12 | 12, her biri 1 kez |
| Yeni klipler Y1–Y21 | 21 |
| Tablo canlandırmaları T1–T5 | 5 |
| Gerçek mekân videosu | 44 çekim (38 farklı Pexels videosu) |
| Kişi kartı | 2 (Fatih, Konstantin) |
| Kaldırılanlar | Ateş, mum, sis ve kıvılcım; portresi olmayan 6 kişi kartı; İstanbul dışında çekilmiş görüntüler |

Bütün gerçek videolar Pexels lisanslıdır ve açıklamada çekenlerin adları yazılacaktır.
