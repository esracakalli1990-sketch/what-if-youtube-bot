# COWORK GÖREVİ 1: Yavuz Sultan Selim belgeseli, karakterler ve 36 sahne

Bu dosyayı Claude Cowork'e verip şunu yazın:
**"Bu dosyadaki görevi baştan sona, kurallara uyarak yap."**

---

## Cowork için kurallar (lütfen harfiyen uygula)

1. **Kredi harcama yasak.** Her üretimde Higgsfield'ın sınırsız (unlim) hakkını kullan.
   - Bir üretim kredi isteyecekse o üretimi **yapma**, atla ve raporda "KREDİ İSTEDİ" diye yaz.
   - `max_credits` her zaman 0 olsun. Kredili yedeğe asla geçme.
2. **Ayarlar**
   - Görseller (bölüm A): model **Nano Banana Pro**, 2k, oran **3:4**.
   - Videolar (bölüm B): model **Seedance 2.5**, çözünürlük **720p**, oran **16:9**, süre tabloda yazdığı kadar.
     - 1080p seçme; sınırsız kapsamda değil.
     - **Seedance 2.5 Flash kullanma**; kredi harcar.
     - Ses açık (ortam sesi). Konuşma ve müzik olmasın.
3. **Her komutu bir kez üret.** Kendi kendine tekrar deneme yapma. Seçimi ben (Claude Code) kare kare inceleyerek yapacağım.
   - Tek istisna: üretim hata verirse (zaman aşımı, sunucu hatası) bir kez daha dene. Yine olmazsa atla, raporda "HATA" yaz.
4. **Karakter referansı:** Tabloda "Ref" sütununda K1–K4 yazan videolarda, bölüm A'da üretilen ilgili görseli **görsel referansı (omni_reference / image reference)** olarak ekle.
5. **Dosyalar:** Hepsini bilgisayarda `Belgeler/Yavuz_Klipler/` klasörüne indir, **tam olarak tablodaki adla** kaydet (`k1.png`, `y01.mp4` …).
6. **Sıra:** Önce bölüm A'nın 4 görseli, sonra B. Videoları 5–10'luk gruplar halinde toplu (batch) gönderebilirsin.
7. **Rapor:** Her 10 videoda bir kısa durum yaz. Sonunda bir tablo ver: dosya adı, durum (TAMAM / HATA / KREDİ İSTEDİ), süre.
8. Sınırsız hakkın bitiş saati: **15 Kasım 2026, 20:18 (İstanbul)**. Bu saatten sonra hiçbir şey üretme.

---

## A) Karakter referans görselleri (Nano Banana Pro, 3:4, 2k)

Bu görseller videolarda yüzlerin tutarlı kalması için. Hepsi: düz, sade arka plan, belden yukarı, yüz net, doğal ışık.

| Dosya | Komut |
|---|---|
| `k1.png` | Character reference portrait, waist-up, front three-quarter view. An Ottoman sultan of the early 16th century, about 44 years old, stern and intense, piercing dark eyes, strong hooked nose, **clean-shaven chin with no beard**, a very long thick dark drooping mustache, a single small gold hoop earring in one ear. He wears a tall white cylindrical Ottoman turban wrapped around a red felt cap, a dark crimson silk kaftan with gold brocade over a white inner robe, a jeweled belt. Neutral plain warm-grey studio background, soft natural window light, photorealistic, cinematic, high detail, no text. |
| `k2.png` | Character reference portrait, waist-up, front three-quarter view. A young Persian Safavid shah of the early 16th century, about 27 years old, slim and charismatic, fair skin, sharp features, a long thin dark mustache and **no beard**. He wears a white turban wrapped around a tall **red twelve-gored baton cap** rising from its center (the Safavid "Qizilbash" headgear), a richly embroidered blue and gold Persian silk robe. Neutral plain warm-grey studio background, soft natural light, photorealistic, cinematic, high detail, no text. |
| `k3.png` | Character reference portrait, waist-up, front three-quarter view. An elderly Mamluk sultan of Egypt in the early 16th century, about 75 years old, dignified but tired, deep wrinkles, a full **long white beard**. He wears a very large white Mamluk ceremonial turban with two horn-like folds on top, a heavy dark green and gold brocade robe over a mail shirt. Neutral plain warm-grey studio background, soft natural light, photorealistic, cinematic, high detail, no text. |
| `k4.png` | Character reference portrait, waist-up, front three-quarter view. A Mamluk military commander of Egypt in the early 16th century, about 40 years old, brave and determined, sun-tanned skin, short dark beard, scar on one cheek. He wears a white turban wound around a steel helmet, a shirt of mail with a red sash, a curved sword at his side. Neutral plain warm-grey studio background, soft natural light, photorealistic, cinematic, high detail, no text. |

---

## B) Videolar (Seedance 2.5 · 720p · 16:9 · ses açık, konuşma ve müzik yok)

**Her komutun sonuna şu stil cümlesini ekle (komutlara dahil edilmedi, sen ekle):**

> Cinematic historical documentary reenactment, early 16th century, shot on 35mm anamorphic lens, natural light, muted earthy color palette, subtle film grain, realistic faces and costumes, historically accurate, no text, no subtitles, no logos, no modern objects, no star-and-crescent flags, no dialogue, no music.

### B1 · Çaldıran Savaşı (23 Ağustos 1514)

| Dosya | Süre | Ref | Komut |
|---|---|---|---|
| `y01.mp4` | 12 sn | — | Aerial drone shot slowly gliding over a vast Ottoman army marching through the dry golden highlands of eastern Anatolia in late summer, long columns of cavalry and infantry stretching to the horizon, dust clouds rising, rugged bare mountains in the distance, hot hazy light. |
| `y02.mp4` | 10 sn | — | Low-angle tracking shot beside marching Ottoman janissary infantry in white felt caps and long blue coats, carrying matchlock muskets on their shoulders, boots kicking up dust, faces tired and determined, afternoon sun. |
| `y03.mp4` | 10 sn | — | Ottoman soldiers dragging heavy bronze cannons on wooden carriages with teams of oxen up a rocky slope, ropes straining, men shouting silently, dust and sweat, epic wide shot. |
| `y04.mp4` | 12 sn | — | Ottoman soldiers chaining dozens of wooden supply wagons and bronze cannons together side by side into a defensive wall on an open plain, janissaries taking positions behind it with muskets, wide shot, early morning mist. |
| `y05.mp4` | 10 sn | K1 | The sultan from the reference image on a black war horse on top of a hill at dawn, wind moving his kaftan, looking down at the battlefield with cold calm eyes, slow push-in on his face, golden backlight, army banners in red and green behind him. |
| `y06.mp4` | 10 sn | K2 | The young shah from the reference image on a white horse at the front of his cavalry, raising a curved sword, confident and fearless, his red twelve-gored cap visible, slow-motion, dust in the air, warm sunlight. |
| `y07.mp4` | 12 sn | — | Thousands of Safavid Persian cavalrymen wearing tall red caps wrapped in white turbans charging at full gallop across a wide plain toward the camera, lances lowered, thunder of hooves, dust storm, slow motion, epic wide shot. |
| `y08.mp4` | 10 sn | — | A line of Ottoman bronze cannons firing in sequence from behind chained wagons, huge muzzle flashes and thick white smoke rolling over the field, recoil, close-up to wide pull-back. |
| `y09.mp4` | 10 sn | — | Janissaries behind a wagon barricade firing a volley of matchlock muskets, sparks and white smoke, officers raising swords to signal, shallow depth of field, smoke drifting across the frame. |
| `y10.mp4` | 10 sn | — | Chaos on the battlefield: cavalry horses rearing in panic amid thick cannon smoke, riders falling, dust and fire, handheld camera, desaturated colors, no gore. |
| `y11.mp4` | 10 sn | K2 | The young shah from the reference image, slightly wounded on the arm, being pulled away from the battle by his loyal guards on horseback, looking back at the lost field with shock, smoke behind, late afternoon light. |
| `y12.mp4` | 12 sn | — | Aftermath at sunset: a silent smoky battlefield on a highland plain, abandoned weapons, broken lances and banners on the ground, a lone horse walking slowly, golden light through smoke, slow aerial pull-back. No bodies visible. |
| `y13.mp4` | 12 sn | — | The Ottoman army entering a great Persian city of the 16th century with blue-tiled domes and mud-brick walls, crowds watching silently from rooftops, cavalry riding through a huge brick gate, warm afternoon light, wide tracking shot. |

### B2 · Mercidabık (24 Ağustos 1516)

| Dosya | Süre | Ref | Komut |
|---|---|---|---|
| `y14.mp4` | 12 sn | — | A magnificent Mamluk army assembled on a flat dusty plain in northern Syria, rows of heavy cavalry in shining mail and colorful silk surcoats, tall white turbans, banners in yellow and red, war drums on camels, wide establishing shot, morning haze. |
| `y15.mp4` | 10 sn | K3 | The elderly sultan from the reference image sitting on a richly decorated horse under a large yellow parasol and banners, surrounded by his royal guard, looking across the plain with worry, slow push-in. |
| `y16.mp4` | 10 sn | — | Mamluk heavy cavalry charging with lances and curved swords, elite horsemen in mail and plumed helmets, slow motion close shots of horses' hooves and flying dust, sunlight flashing on steel. |
| `y17.mp4` | 10 sn | — | Ottoman cannons and musketeers firing at charging cavalry from a defensive line, explosions of smoke, horses swerving, the charge breaking apart, wide shot. |
| `y18.mp4` | 10 sn | K3 | The elderly sultan from the reference image suddenly collapsing and slipping from his horse in the confusion of battle, his guards rushing to catch him, his turban falling to the dust, slow motion, dramatic but not violent. |
| `y19.mp4` | 10 sn | — | The yellow royal Mamluk banner falling into the dust, trampled by horses, close-up, slow motion, smoke and sunlight. |

### B3 · Sina Çölü geçişi (Ocak 1517)

| Dosya | Süre | Ref | Komut |
|---|---|---|---|
| `y20.mp4` | 15 sn | — | Epic aerial shot of a long Ottoman army caravan crossing the endless Sinai desert, thousands of camels loaded with water skins, cavalry and infantry in a winding line across huge sand dunes, low sun casting long shadows. |
| `y21.mp4` | 10 sn | — | Close shot of exhausted soldiers walking through deep sand under a burning sun, cracked lips, a soldier drinking the last drops from a leather water skin, heat haze, handheld camera. |
| `y22.mp4` | 12 sn | — | A massive sandstorm approaching an army caravan in the desert, camels kneeling, men covering their faces with cloth, orange sky, wind and sand filling the frame. |
| `y23.mp4` | 10 sn | — | Night in the desert: a huge army camp with hundreds of small campfires among the dunes under a sky full of stars, slow time-lapse feeling, quiet atmosphere. |
| `y24.mp4` | 10 sn | K1 | The sultan from the reference image walking alone on foot in the desert at dawn, leading his horse by the reins, looking at the horizon, wind blowing sand, wide shot then slow push-in. |

### B4 · Ridaniye ve Kahire (Ocak 1517)

| Dosya | Süre | Ref | Komut |
|---|---|---|---|
| `y25.mp4` | 12 sn | — | A Mamluk fortified line outside medieval Cairo: rows of large bronze cannons dug into earth trenches all pointing in one direction, defenders in turbans waiting nervously, palm trees and the Nile valley haze behind, wide shot. |
| `y26.mp4` | 12 sn | — | Ottoman cavalry riding fast along a rocky desert ridge above the city, circling around behind an enemy line, dust trail, aerial tracking shot, late afternoon light. |
| `y27.mp4` | 10 sn | K4 | The Mamluk commander from the reference image leading a desperate cavalry charge, sword raised, shouting silently, dust and smoke, slow motion. |
| `y28.mp4` | 15 sn | — | Medieval Cairo in the early 16th century seen from above at dawn: a dense city of sandstone houses, many slender Mamluk minarets and domes, the great citadel on the hill, the Nile glittering in the distance, slow aerial glide, mist and smoke. |
| `y29.mp4` | 10 sn | — | Narrow street of medieval Cairo with wooden mashrabiya balconies, frightened residents closing their shutters as cavalry rides past, dust in shafts of light, tense atmosphere. |
| `y30.mp4` | 12 sn | — | A huge medieval Cairo stone city gate with two tall minarets on top, a silent crowd gathering in front of it at dawn, soldiers holding back the people, somber and tense, wide shot. No violence shown. |
| `y31.mp4` | 10 sn | K1 | The sultan from the reference image riding slowly through the streets of medieval Cairo at the head of his army, people watching from balconies, his face calm and unreadable, warm light. |

### B5 · Kutsal Emanetler ve dönüş

| Dosya | Süre | Ref | Komut |
|---|---|---|---|
| `y32.mp4` | 12 sn | — | Inside a dim 16th century palace hall lit by oil lamps, servants carefully placing ornate gilded wooden chests and silk-wrapped bundles into larger travel chests, reverent atmosphere, slow dolly shot, dust in light beams. Do not show any holy figures. |
| `y33.mp4` | 12 sn | — | A long caravan of camels and horsemen leaving Cairo by the Nile, carrying covered chests under green silk cloths, palm trees and sails of feluccas, golden hour, wide tracking shot. |
| `y34.mp4` | 12 sn | — | An Ottoman fleet of galleys and sailing ships at sea in the early 16th century, oars moving in rhythm, red and green banners, sunlight on waves, aerial shot. |

### B6 · Genel atmosfer (her bölümde kullanılabilir)

| Dosya | Süre | Ref | Komut |
|---|---|---|---|
| `y35.mp4` | 10 sn | — | Close-up of Ottoman military kettle drums and long trumpets being played by musicians on horseback before battle, drumsticks hitting, dust and sunrise light, slow motion. |
| `y36.mp4` | 12 sn | K1 | Inside a large Ottoman campaign tent at night lit by oil lamps, the sultan from the reference image studying a hand-drawn parchment map on a low table with his generals kneeling around him, shadows on the tent walls, slow push-in. |

---

## Bitince

Klasördeki dosyaları (`k1–k4`, `y01–y36`) sohbete, Claude Code oturumuna 10–15'lik gruplar halinde yükleyin. Her birini kare kare inceleyeceğim:
- tarih hatası (yanlış bayrak, cami, kıyafet)
- bozuk yüz ya da el
- yazı ya da logo

Sorunlu olanlar için düzeltilmiş komutu ikinci görev dosyasıyla birlikte veririm.
