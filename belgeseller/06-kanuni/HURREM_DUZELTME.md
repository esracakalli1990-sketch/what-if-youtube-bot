# DÜZELTME GÖREVİ — Hürrem karakter görseli (K_hurrem) ve c36 klibi

**Sorun:** Üretilen `K_hurrem` görseli, Türk TV dizisindeki Hürrem Sultan karakterini (gerçek bir oyuncuyu) andırıyor. Gerçek bir kişiye benzeyen görsel kullanılmayacak.

**Neden oluyor:** Komuttaki "Hürrem / Roxelana" adı ve "kızıl saç" tarifi, modeli dizideki tanıdık görünüme yönlendiriyor. Yeni komutta **isim ve kızıl saç yok**. Yüz tamamen özgün olarak tarif ediliyor ve 16. yüzyıl Venedik portrelerindeki görünüme yaklaştırılıyor.

Ajana şunu yazın: **"Bu dosyadaki düzeltmeyi yap; sorun çıkarsa beklet ve bana yaz."**

---

## 1. Yeni `K_hurrem` (Gemini · Nano Banana Pro, 16:9, en yüksek çözünürlük)

Eski `referans/K_hurrem` dosyasını silme. Adını `K_hurrem_ESKI` yap. Yenisini `referans/K_hurrem` adıyla kaydet.

**Komut (olduğu gibi yapıştır):**
> Wide 16:9 landscape image. Character reference sheet of an original fictional woman, a 16th century Ottoman palace consort around thirty years old, inspired by 16th century Venetian Renaissance portrait paintings: soft oval face, light chestnut-brown hair almost completely covered by a small round gold-embroidered cap and a long sheer ivory veil, grey-green eyes, a few light freckles, fair skin, calm intelligent and reserved expression with closed lips, no smile; modest high-necked dark green and gold brocade kaftan over a cream silk dress, a simple string of pearls. Original face that does not resemble any actress, celebrity, TV series or film character. Front view and three-quarter view side by side, soft even studio light on a plain dark background, photorealistic, sharp facial details, NO text, NO letters, NO logos, NO watermark.

**Kontrol:**
- Yüz bilinen bir oyuncuya ya da dizideki Hürrem'e **benziyorsa**: aynı komutla bir kez yeniden üret.
- Hâlâ benziyorsa: komuttaki `grey-green eyes, a few light freckles` kısmını `dark brown eyes, a slightly longer face` ile değiştirip bir kez daha dene.
- Yine olmazsa dur ve kullanıcıya yaz.
- **İlk indirmeden sonra görseli kullanıcıya göster ve onay al.**

## 2. `c36` klibini yeniden üret (Google Flow · Omni Flash 1.1)

`c36` daha önce eski görselle üretildiyse: eski dosyanın adını `c36_ESKI.mp4` yap ve yeni `K_hurrem`'i malzeme olarak ekleyerek yeniden üret. Ayarlar ana görevdekiyle aynı: 16:9, Ingredients to video, 2K/1080p indirme.

**Komut:**
> The woman from the reference walking slowly in a Topkapı Palace garden among tulips and cypress trees, then stopping and looking toward the camera with a calm, reserved, determined expression.

Sonuna ana görevdeki stil cümlesini ekle:
> Photorealistic cinematic film shot, shot on ARRI Alexa with anamorphic lens, natural motivated lighting, subtle film grain, historically accurate early 16th century Ottoman Empire and Central Europe, slow deliberate camera movement, natural ambient sound only, NO dialogue, NO speech, NO music, NO text, NO subtitles, NO logos, NO watermark, no modern objects, no star-and-crescent flags, no crosses or religious symbols on flags and armor.

## 3. Bitince
- `rapor.md`'ye ekle: `K_hurrem — YENİDEN (özgün yüz)`, `c36 — YENİDEN`.
- `_ESKI` dosyalarını **zip'e koyma**.
- Ardından ana görevdeki gibi `Belgeler/Kanuni/` klasörünü **tek bir zip** yap, Drive'a yükle ve paylaşımı "Bağlantıya sahip herkes görüntüleyebilir" olarak ayarla.
