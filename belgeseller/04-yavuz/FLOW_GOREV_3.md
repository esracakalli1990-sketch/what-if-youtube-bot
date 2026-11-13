# FLOW GÖREVİ 3 — Yavuz belgeseli, kalan 26 klip (Google Flow · Omni Flash 1.1)

Bu dosya, bilgisayarınızda **tarayıcıyı kullanabilen bir Claude'a** verilmek için yazıldı (Claude in Chrome ya da tarayıcı/bilgisayar kullanımı açık Claude masaüstü sohbeti).
Ona şunu yazın: **"Bu dosyadaki görevi baştan sona kendi başına yap. Bana yalnızca bitince ya da gerçekten takılırsan yaz."**

> Higgsfield'da zaten üretilen 6 klip bu listede YOK: w01, w04, w05, w08, w09, w11. Bunlara dokunma, üzerine yazma.

---

## 0. Senin görevin (Claude için)

Google Flow'da (https://labs.google/fx/tools/flow) aşağıdaki **26 klibi** tek tek üret, indir ve doğru adla kaydet. Kullanıcı Flow'da zaten oturum açmış; açık sekmeyi kullan, yeni hesap açma, şifre girme.

### Klasörler (kullanıcının bilgisayarı)
- **Çıktı:** `Belgeler/Yavuz_Klipler/` (Görev 1–2 klipleriyle aynı klasör).
- **Karakter referansları:** Cowork Görev 1 ve 2'de üretilen görseller bilgisayarda: `k1`, `k4`, `k5`, `k6` (uzantı .png/.jpg/.webp olabilir). Önce `Belgeler/Yavuz_Klipler/` içinde ara; yoksa İndirilenler (Downloads), Masaüstü ve Belgeler'in alt klasörlerinde `k1` vb. adla ara. **Bulamazsan dur ve kullanıcıya hangi görseli bulamadığını yaz** (referanssız üretme — yüzler tutarsız olur).
- **İlerleme dosyası:** `Belgeler/Yavuz_Klipler/flow_rapor.md` — her klipten sonra güncelle. Görev yarıda kesilirse buna bakıp **kaldığın yerden** devam et; `TAMAM` olanları tekrar üretme.

### Referans gereken klipler
| Klip | Referans görsel |
|---|---|
| `w14.mp4` | k1 — Yavuz (44 yaş) |
| `w16.mp4` | k1 — Yavuz (44 yaş) |
| `w30.mp4` | k1 — Yavuz (44 yaş) |
| `w32.mp4` | k1 — Yavuz (44 yaş) |
| `w02.mp4` | k5 — genç Selim |
| `w03.mp4` | k5 — genç Selim |
| `w10.mp4` | k1 — Yavuz (44 yaş) |

Diğer klipler referanssız (yalnız komutla) üretilir.

### Flow ayarları (her klip için)
- **Model: Omni Flash 1.1** (model seçicide bu ada en yakın olanı seç; yoksa raporda yaz ve en yakın hızlı modelle devam et).
- **Oran: 16:9 (yatay).** Dikey (9:16) asla seçme.
- **Mod:** Referans varsa "Ingredients to video / Malzemelerden video" (karakter görselini malzeme olarak ekle); yoksa "Text to video / Metinden video".
- **Çıktı sayısı:** klip başına **1** (kredi tasarrufu). Flow birden fazla üretirse en iyisini seç.
- **Süre:** Flow'un verdiği klip hedef süreden kısaysa (ör. 8 sn), **Extend / Uzat** ile bir kez uzat; uzatma komutu: `Continue the same shot seamlessly, same camera movement, same lighting, no new characters, no text, no dialogue.` Uzatma yoksa ya da başarısızsa kısa haliyle kaydet, raporda `KISA` yaz.
- **Konuşma ve müzik istenmiyor** (komutlarda yazıyor).

### Her klip için adımlar
1. `flow_rapor.md`'de bu klip `TAMAM` ise atla.
2. Yeni üretimi aç, ayarları yap.
3. Referans gerekiyorsa ilgili `k` görselini malzeme olarak yükle.
4. Komutu **olduğu gibi** yapıştır (İngilizce, değiştirme).
5. Üret, bitmesini bekle (sekmeyi kapatma).
6. **Kontrol et** (videoyu baştan sona izle):
   - Ekranda **yazı, altyazı, logo, filigran** var mı?
   - **Hilal-yıldızlı bayrak, haç, kartal** gibi yanlış simgeler var mı?
   - **Camlı lamba/fener, modern eşya** var mı? (Yalnızca açık alevli kandil, mum, meşale kabul.)
   - **Bozuk yüz/el**, eriyen nesne var mı?
   - **Dikey** mi çıktı, kenarlarda **siyah bant/çerçeve** var mı?
   - Referanslı klipte yüz referansa **benziyor mu**?
   - Biri **anlaşılır şekilde konuşuyor** mu?
   Sorun varsa **bir kez** yeniden üret. İkincisi de sorunluysa daha iyi olanı kaydet, sorunu raporda yaz.
7. **İndir** (en yüksek kalite, MP4) ve `Belgeler/Yavuz_Klipler/` içine **tam olarak** klibin adıyla kaydet (`w02.mp4` gibi).
8. `flow_rapor.md`'ye satır ekle, sonraki klibe geç.

### Rapor biçimi (`flow_rapor.md`)
```
| Dosya | Durum | Süre | Not |
|---|---|---|---|
| w02.mp4 | TAMAM | 10 sn | — |
| w14.mp4 | KISA | 8 sn | uzatma başarısız |
| w17.mp4 | SORUNLU | 8 sn | sancakta yazı var |
```
Durum: `TAMAM`, `KISA`, `SORUNLU`, `ATLANDI`.

### Durma kuralları
- **Flow kredisi / günlük sınır biterse:** dur, raporu kaydet, kullanıcıya kaç klip kaldığını yaz.
- **Oturum düşerse / giriş isterse:** dur, kullanıcıya yaz (şifre girme).
- **Referans görseli bulunamazsa:** dur, kullanıcıya hangisini bulamadığını yaz.
- Bir klip 3 kez üst üste hata verirse `ATLANDI` yaz, sonrakine geç.
- Sıra: **önce A öncelikliler (1–17)**, sonra B'ler (18–26).

### Bitince kullanıcıya yaz
"26 klipten X tamam, Y kısa, Z sorunlu/atlandı. Dosyalar Belgeler/Yavuz_Klipler/ klasöründe."

---

## 1. Klipler (sıra: önce A, sonra B)

Her komutun sonunda stil cümlesi zaten ekli; komutu **tamamıyla** yapıştır.

### 1. `w12.mp4` — öncelik A, hedef süre 12 sn, referans: yok

```
Dusk, an empty Ottoman prince's campaign tent on a hill, its banner slowly lowered by a soldier, wind, long shadows, melancholic and quiet, wide static shot. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 2. `w13.mp4` — öncelik A, hedef süre 14 sn, referans: yok

```
Night in a barren highland army camp, exhausted hungry Ottoman soldiers sitting around a small fire sharing a single piece of bread, cold breath visible, firelight on tired faces. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 3. `w14.mp4` — öncelik A, hedef süre 10 sn, referans: k1 — Yavuz (44 yaş)

```
The sultan from the reference image riding slowly in front of the lined-up army, turning his horse to face the soldiers, moving left to right, the soldiers silently watching him, wide then medium shot. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 4. `w15.mp4` — öncelik A, hedef süre 12 sn, referans: yok

```
A Persian envoy in a rich robe dismounting at the edge of a large Ottoman army camp, carrying a sealed letter, guards escorting him between the tents, dusty afternoon light. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 5. `w16.mp4` — öncelik A, hedef süre 10 sn, referans: k1 — Yavuz (44 yaş)

```
Inside his tent, the sultan from the reference image reading a letter, his face hardening, then slowly crushing the paper in his fist, lamp light, close-up. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 6. `w17.mp4` — öncelik A, hedef süre 8 sn, referans: yok

```
Close shot of red-capped Persian horsemen crashing into a wall of chained wooden wagons, moving right to left, horses rearing, smoke and dust, slow motion. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 7. `w19.mp4` — öncelik A, hedef süre 10 sn, referans: yok

```
The Mamluk battle lines breaking apart: colorful heavy cavalry turning back and fleeing through thick cannon smoke, moving right to left, slow motion, wide shot. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 8. `w20.mp4` — öncelik A, hedef süre 8 sn, referans: yok

```
Dawn in the desert, silhouettes of an army on a dune ridge looking toward a distant city with many slender minarets and domes rising out of the haze by a green river valley. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 9. `w21.mp4` — öncelik A, hedef süre 8 sn, referans: yok

```
A handful of elite Mamluk horsemen galloping at full speed between Ottoman army tents, moving right to left, tents collapsing, guards scattering, chaos, slow motion. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 10. `w22.mp4` — öncelik A, hedef süre 8 sn, referans: yok

```
An Ottoman grand vizier in a rich kaftan and tall turban falling from his horse amid charging riders, slow motion, dust and smoke, dramatic but no blood. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 11. `w24.mp4` — öncelik A, hedef süre 12 sn, referans: yok

```
A delegation of Arab noblemen in white robes riding camels slowly up to a great stone citadel gate of medieval Cairo, Ottoman guards at the gate, golden afternoon light. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 12. `w25.mp4` — öncelik A, hedef süre 16 sn, referans: yok

```
Extreme close-up slowly panning across an old hand-drawn 16th century world map on gazelle skin: coastlines of Africa and South America, tiny drawn ships, compass roses and handwritten notes, warm lamp light, shallow depth of field. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 13. `w28.mp4` — öncelik A, hedef süre 10 sn, referans: yok

```
Inside a dim tent at night, an old Ottoman physician in a dark robe preparing medicine with a mortar and pestle by a single oil lamp, worried face, close shot. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 14. `w29.mp4` — öncelik A, hedef süre 12 sn, referans: yok

```
Inside a tent lit by a single oil lamp, a middle-aged Ottoman courtier with a short grey beard sitting beside a bed, quietly reading from a small book, eyes wet, seen from the side, the ill man in bed not shown clearly. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 15. `w30.mp4` — öncelik A, hedef süre 12 sn, referans: k1 — Yavuz (44 yaş)

```
The sultan from the reference image standing alone on a hilltop at sunset, seen from behind as a silhouette, looking over a vast army camp in the valley below, wind, wide shot slowly pushing in. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 16. `w31.mp4` — öncelik A, hedef süre 18 sn, referans: yok

```
An empty golden Ottoman throne in a dim, silent hall, a single beam of light falling on it, dust floating in the beam, very slow push-in. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 17. `w32.mp4` — öncelik A, hedef süre 14 sn, referans: k1 — Yavuz (44 yaş)

```
Dramatic close portrait of the sultan from the reference image slowly turning his head toward the camera, stern and calm, half his face lit by warm lamp light, the other half in shadow, dark background. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 18. `w02.mp4` — öncelik B, hedef süre 10 sn, referans: k5 — genç Selim

```
The young prince from the reference image riding a horse at a gallop along a misty Black Sea shore at sunrise, moving left to right, waves breaking, tracking shot. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 19. `w03.mp4` — öncelik B, hedef süre 12 sn, referans: k5 — genç Selim

```
Inside a stone palace room with a wooden ceiling, the young prince from the reference image gently holding his newborn son wrapped in white cloth, looking at him silently, soft window light, warm and intimate. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 20. `w06.mp4` — öncelik B, hedef süre 10 sn, referans: yok

```
Night, a charismatic dervish in a simple wool cloak preaching to a large crowd of villagers and horsemen holding torches in a mountain village of southern Anatolia, faces lit by fire, slow push-in. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 21. `w07.mp4` — öncelik B, hedef süre 12 sn, referans: yok

```
A long dim corridor of an Ottoman palace, viziers in tall white turbans whispering in pairs, glancing back over their shoulders, shafts of cold light, slow tracking shot. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 22. `w10.mp4` — öncelik B, hedef süre 8 sn, referans: k1 — Yavuz (44 yaş)

```
The man from the reference image entering a great city gate on horseback with a small escort, crowds of janissaries cheering silently, moving left to right, morning light. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 23. `w18.mp4` — öncelik B, hedef süre 12 sn, referans: yok

```
In a Persian bazaar of the 16th century, Ottoman soldiers escorting master craftsmen and their families with their tools onto wagons, potters, weavers and tile makers, sad faces, warm afternoon light. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 24. `w23.mp4` — öncelik B, hedef süre 8 sn, referans: yok

```
Aftermath: an abandoned trench line with large bronze cannons half-buried and pointing the wrong way, smoke drifting, dropped banners and helmets, silent, wide shot. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 25. `w26.mp4` — öncelik B, hedef süre 12 sn, referans: yok

```
An elderly Arab scholar in black robes and black turban boarding a wooden ship in a harbor, helped by Ottoman officials, calm and dignified, sails and gulls, morning light. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
### 26. `w27.mp4` — öncelik B, hedef süre 10 sn, referans: yok

```
The inner courtyard of a 16th century Ottoman palace at dawn, cypress trees, domed pavilions, a few servants walking quietly, mist, slow aerial drift. Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.
```
