# COWORK GÖREVİ — Kanuni Sultan Süleyman: karakter görselleri (Gemini) + 52 klip (Google Flow)

Bu dosya, bilgisayarınızda **tarayıcıyı kullanabilen bir Claude'a** verilmek için yazıldı (Claude in Chrome ya da tarayıcı/bilgisayar kullanımı açık Claude masaüstü sohbeti).
Ona şunu yazın: **"Bu dosyadaki görevi baştan sona kendi başına yap. Bana yalnızca bitince ya da gerçekten takılırsan yaz."**

Görev iki bölüm: **A)** Gemini'de karakter ve kapak görselleri, **B)** Google Flow'da 52 klip. **Önce A'yı bitir**, çünkü B'deki kliplerin bir kısmı A'daki görselleri referans olarak kullanıyor.

---

## 0. Genel kurallar (Claude için)

> **Kullanıcının ek talimatları (önemli):**
> 1. Bütün görselleri ve videoları **2K / 1080p** (en yüksek) çözünürlükte indir.
> 2. **İlk indirmeden sonra dur ve kullanıcıdan onay al.** İlk görseli (`K_genc`) üretip indirince kullanıcıya göster ve "devam edeyim mi?" diye sor. Onay gelince işin geri kalanını **kendi kendine, bitene kadar** sürdür.
> 3. Herhangi bir **sorun çıkarsa** (kredi biter, Flow/Gemini hata verir, model bulunamaz, bir klip iki denemede de olmaz…) **işi beklet ve kullanıcıya yaz.** Tahminle devam etme.

- Kullanıcı Gemini'de ve Flow'da (https://labs.google/fx/tools/flow) zaten oturum açmış. Açık sekmeleri kullan, yeni hesap açma, şifre girme.
- **Çıktı klasörü:** `Belgeler/Kanuni/`. Alt klasörler: `referans/` (A bölümü), `klipler/` (B bölümü). Yoksa oluştur.
- **İlerleme dosyası:** `Belgeler/Kanuni/rapor.md`. Her görselden/klipten sonra bir satır ekle: `c01 — TAMAM`, `c07 — TAMAM (2. deneme)`, `c19 — SORUNLU: …`. Görev yarıda kesilirse bu dosyaya bakıp **kaldığın yerden** devam et. `TAMAM` olanları tekrar üretme.
- **Kredi:** Flow'da kullanıcının ayda 1000 kredisi var. Omni Flash 1.1 klibi ~15 kredi. 52 klip ≈ 780 kredi. **Bir klibi en fazla 2 kez** yeniden üret. Kredi biterse dur, raporda kaçıncı klipte kaldığını yaz ve kullanıcıya haber ver.
- **Bitince:** `Belgeler/Kanuni/` klasörünü zip'le (ya da Google Drive'a yükleyip "bağlantıya sahip herkes görüntüleyebilir" yap) ve kullanıcıya bağlantıyı ver. Kullanıcı bunu Claude Code oturumuna gönderecek.

---

## A) GEMİNİ — karakter ve kapak görselleri (Nano Banana Pro)

**Ayarlar:** Görsel üretiminde **Nano Banana Pro** seç. Oran **16:9**. Gemini oran seçeneği sunmuyorsa komutun başına `Wide 16:9 landscape image.` ekle. Her komuttan 1 görsel yeterli. Tam çözünürlükte indir, aşağıdaki adla `referans/` klasörüne kaydet.

**Her komutun sonuna ekle:**
> Photorealistic cinematic character reference, soft even studio light on a plain dark background, front view and three-quarter view side by side, historically accurate 16th century Ottoman costume, sharp facial details, NO text, NO letters, NO logos, NO watermark.

| Dosya | Komut |
|---|---|
| `K_genc` | Young Ottoman Sultan Süleyman at age 26: tall and slender, long thin pale face, distinctive aquiline hooked nose, thin dark mustache and very short beard, calm serious dark eyes; very large white turban wrapped around a tall red cap, rich crimson and gold silk kaftan with a fur-lined collar. |
| `K_yasli` | The same Ottoman Sultan Süleyman at age 70: very thin, gaunt pale face, aquiline nose, long thin white beard and mustache, tired but dignified eyes; enormous white turban, dark green and gold kaftan with sable fur collar. Same facial structure as a younger version of himself. |
| `K_ibrahim` | Pargalı İbrahim Pasha, Ottoman grand vizier in his thirties: handsome, sharp intelligent face, short dark beard, confident proud expression; tall white turban with a jeweled aigrette, luxurious blue and gold brocade kaftan. |
| `K_hurrem` | Hürrem Sultan (Roxelana), Ottoman royal consort in her twenties: Eastern European features, auburn red hair partly covered by a small jeweled cap and a light silk veil, bright intelligent eyes, a slight determined smile; elegant pink and gold 16th century Ottoman palace dress. |
| `K_mustafa` | Şehzade Mustafa, Ottoman prince in his thirties: handsome, strong and noble face, short dark beard, warm brave eyes; white turban with a red cap, dark red kaftan with gold embroidery, a sword belt. |
| `K_sokullu` | Sokullu Mehmed Pasha, Ottoman grand vizier around sixty: tall, long grey beard, wise calm stern face; very tall white vizier turban, dark blue kaftan with fur collar. |

**Kapak görselleri (yalnızca küçük resim için, yazı yok):** Bunlarda stil cümlesi olarak şunu ekle:
> Ultra-detailed cinematic photograph, 16:9, 85mm lens, shallow depth of field, dramatic high-contrast lighting with bright well-exposed face and warm rim light, vivid gold and crimson colors against a dark background, NO text, NO letters, NO logos, NO watermark, no star-and-crescent flags, no crosses.

| Dosya | Ref | Komut |
|---|---|---|
| `kapak1` | K_yasli | Extreme close-up portrait of the old Ottoman sultan from the reference, lying awake at night in a dark imperial tent, a single candle lighting half of his gaunt face, eyes looking directly at the camera, deep shadows. His face on the RIGHT two-thirds, the LEFT third dark empty space. |
| `kapak2` | — | Low-angle epic shot: Ottoman sipahi cavalry charging from left to right across a misty Hungarian plain at golden hour, red banners without symbols, dust and mud flying, cannon smoke behind. Action on the RIGHT half, open smoky sky on the LEFT. |
| `kapak3` | K_genc | The young Ottoman sultan from the reference on a white horse in the foreground, seen from the chest up, looking at the camera; behind him the medieval walls and church spires of 16th century Vienna under a stormy autumn sky, smoke rising. Sultan on the RIGHT, walls on the LEFT. |

Referansla üretilen görsellerde karakter sayfasını **görsel olarak yükle** ve komutun başına şunu yaz: `Use the attached character sheet: same face, same turban and same clothes.`

---

## B) GOOGLE FLOW — 52 klip (Omni Flash 1.1)

### Ayarlar (her klip)
- **Model: Omni Flash 1.1.** Bulamazsan en yakın hızlı modeli seç ve raporda yaz.
- **Oran: 16:9 yatay.** Dikey asla seçme.
- **Mod:** "Ref" sütununda bir görsel yazıyorsa **Ingredients to video / Malzemelerden video** seç ve `referans/` klasöründeki o görseli malzeme olarak ekle. Ref yoksa **Text to video / Metinden video**.
- **Çıktı:** klip başına **1**.
- **İndirme:** En yüksek çözünürlük (Pro üyelikte 2K/1080p). Dosya adı: `c01.mp4`, `c02.mp4` … → `klipler/` klasörü.

### Her komutun sonuna ekle
> Photorealistic cinematic film shot, shot on ARRI Alexa with anamorphic lens, natural motivated lighting, subtle film grain, historically accurate early 16th century Ottoman Empire and Central Europe, slow deliberate camera movement, natural ambient sound only, NO dialogue, NO speech, NO music, NO text, NO subtitles, NO logos, NO watermark, no modern objects, no star-and-crescent flags, no crosses or religious symbols on flags and armor.

### Ekran yönü kuralı
Osmanlı ordusu ve gemileri **soldan sağa**, karşı taraf (Macarlar, Habsburglar, Haçlı donanması) **sağdan sola** hareket etmeli. Ters çıkarsa bir kez yeniden üret. Yine ters çıkarsa kaydet, raporda `TERS` yaz; kurguda aynalanır.

### Kontrol (her klipten sonra)
Şunlardan biri varsa **bir kez yeniden üret**:
- konuşan biri ya da müzik var,
- yazı ya da harf var,
- modern bir nesne var,
- ay-yıldızlı bayrak ya da haç var,
- referanslı karakterin yüzü belirgin şekilde farklı,
- görüntüde bozuk el ya da yüz var.

### Klipler (önemli olanlar önce: listeyi yukarıdan aşağıya üret)

| Klip | Ref | Komut |
|---|---|---|
| `c01` | — | Night, aerial drone shot slowly pushing in over a vast 16th century Ottoman army camp beside a misty Hungarian marsh: thousands of white tents, campfires and torches, a huge imperial tent in the center, a besieged fortress burning faintly in the distance. |
| `c02` | — | Inside a large Ottoman imperial tent at night: a single candle on a low table, rich carpets, an old man lying still on a cushioned bed, his face hidden in shadow, only the silhouette of a large turban visible, very slow push-in, silence. |
| `c03` | K_sokullu | Night, the grand vizier from the reference standing in front of the imperial tent in torchlight, deep in thought, then turning his head slowly; two janissary guards in white börk caps stand with their backs to the camera. |
| `c04` | — | Ottoman sipahi cavalry with lances and round shields charging from left to right across a muddy plain, low angle tracking shot, dust and mud flying, red banners without symbols, late afternoon light. |
| `c05` | — | An Ottoman army encamped before the medieval stone walls and towers of 16th century Vienna in autumn rain, rows of tents, soldiers in cloaks, grey sky; slow lateral camera move from left to right. |
| `c06` | — | Ottoman war galleys with many oars rowing fast from left to right across a blue Ionian sea, sails half furled, cannons firing smoke from the bows, sea spray, morning sun. |
| `c07` | — | Dawn over Istanbul: the great Süleymaniye Mosque with its huge central dome and four slender minarets rising above the Golden Horn, morning mist on the water, slow aerial push-in. |
| `c08` | — | Aerial shot at dawn over the old Black Sea city of Trabzon: a medieval fortress on a rocky hill above the sea, morning fog drifting, green hills behind. |
| `c09` | — | In a modest Ottoman palace room in Trabzon, morning light through a lattice window: a young mother in a white veil gently holding a newborn baby wrapped in silk, peaceful and warm. |
| `c10` | K_genc (çocuk hâli: "as a 10-year-old boy") | A 10-year-old Ottoman prince with a small white turban sitting at a low wooden table with an old bearded teacher, reading a large illuminated manuscript by candlelight, the boy listening attentively. |
| `c11` | K_genc + K_ibrahim | Spring in the garden of an Ottoman prince's palace in Manisa: the young prince and his friend İbrahim sit on cushions playing chess under a blossoming tree, smiling and talking quietly. |
| `c12` | K_genc | September 1520, early morning, the gate of Topkapı Palace in Istanbul: the young new sultan rides through on a white horse, rows of Ottoman statesmen in tall turbans bow deeply, janissaries line the path. |
| `c13` | — | The medieval fortress of Belgrade on a hill where two rivers meet, Ottoman cannons firing from the opposite bank from left to right, smoke rolling over the water, summer haze. |
| `c14` | — | Close shot of a battered fortress tower wrapped in smoke, a plain white flag being raised on the battlements, defenders lowering their weapons. |
| `c15` | — | The golden-yellow stone walls and towers of Rhodes seen from the sea, a large Ottoman fleet anchored in front, cannon smoke rising, bright Mediterranean light. |
| `c16` | — | Underground tunnel lit by torches: Ottoman sappers digging with pickaxes, wooden supports, barrels of gunpowder being stacked, dust in the air, tense atmosphere. |
| `c17` | — | Winter, grey sea, the harbor of Rhodes: knights in plain black cloaks without symbols walk in a line onto their ships, carrying their belongings; Ottoman soldiers watch quietly from a distance. |
| `c18` | — | A marshy plain at Mohács: rows of Hungarian heavy cavalry in full plate armor and plumed helmets lined up facing left, lances raised, banners without symbols, overcast sky, slow tracking shot from right to left. |
| `c19` | — | A 20-year-old Hungarian king in polished plate armor and a red cloak on a white horse, a thin crown on his helmet, looking anxious across the battlefield, his knights around him. |
| `c20` | — | A line of Ottoman bronze cannons chained together behind wooden wagons, gunners firing from left to right, huge clouds of white smoke, flashes of fire, janissaries with muskets behind them. |
| `c21` | — | Evening after a battle on a muddy plain: silence, smoke drifting, a single red Ottoman banner without symbols standing in the ground, golden sunset light, slow pull-back. |
| `c22` | — | Heavy rain on a muddy road: Ottoman soldiers and oxen straining to push a huge bronze siege cannon whose wagon wheels are stuck deep in mud, rain pouring. |
| `c23` | — | The stone city walls of 16th century Vienna: a large gunpowder explosion bursts from under the wall, dust and stones fly, but the wall still stands; defenders on the battlements. |
| `c24` | — | A long column of the Ottoman army marching from right to left on a snow-covered road through bare forests, horses, camels and wagons, cold grey light, wide shot. |
| `c25` | — | Sunny morning in the harbor of Algiers in the 16th century: rows of Ottoman galleys with red and green sails, white buildings on the hill, sailors loading the ships. |
| `c26` | — | A naval battle at sea: large European carracks and galleys with many sails turning away from right to left, smoke from cannon fire, broken oars in the water, banners without symbols. |
| `c27` | — | A single Ottoman galley sailing on the Red Sea under a hot yellow sky, desert coastline on the horizon, shimmering heat. |
| `c28` | — | The Imperial Council in the domed council hall (Kubbealtı) of Topkapı Palace: viziers in tall white turbans sit on a long cushioned bench, scribes kneel with papers, a golden lattice window above. |
| `c29` | — | Close-up: an Ottoman scribe's hand writing a long imperial decree with a reed pen in elegant calligraphy, an illuminated golden imperial monogram at the top (no readable letters), candlelight. |
| `c30` | — | A small Anatolian village courtyard: an Ottoman judge (kadı) in a large turban sits on a low platform listening to an old farmer, villagers waiting calmly, warm afternoon light. |
| `c31` | — | The Süleymaniye Mosque under construction: the huge dome half built, wooden scaffolding everywhere, hundreds of masons and workers carrying stones, cranes made of wood, dusty sunlight. |
| `c32` | — | Inside the Süleymaniye Mosque: beams of morning light pouring through rows of windows, the camera slowly rising toward the vast central dome, carpets below, peaceful. |
| `c33` | — | Night view of the Ottoman Hippodrome square in Istanbul: the stone palace of İbrahim Pasha with lit windows, torches, a few guards. |
| `c34` | K_ibrahim | The grand vizier from the reference, in a luxurious kaftan, proudly receiving a European ambassador in Renaissance clothes inside a grand palace hall, the ambassador bowing, attendants around. |
| `c35` | — | A dark corridor in Topkapı Palace at night, a single oil lamp flickering, tiled walls, a heavy wooden door slowly closing at the end of the corridor, ominous silence. |
| `c36` | K_hurrem | The young woman from the reference walking slowly in a Topkapı Palace garden among tulips and cypress trees, then stopping and looking toward the camera with a calm determined expression. |
| `c37` | K_mustafa | The prince from the reference riding a horse past rows of janissaries and sipahis who raise their arms and cheer, banners without symbols, sunny day. |
| `c38` | — | The Şehzade Mosque in Istanbul at late afternoon: domes and two slender minarets with golden light, pigeons in the courtyard, slow pan. |
| `c39` | — | October morning, a large Ottoman army camp on the plain near Ereğli in Konya: many tents, a huge imperial tent in the center, soldiers standing quietly, mountains in the background. |
| `c40` | K_mustafa | The prince from the reference, seen from behind, walking alone toward the entrance of the huge imperial tent, guards holding the curtain open, he steps inside into darkness. |
| `c41` | — | Morning in the camp: rows of silent janissaries and sipahis standing in front of the imperial tent, faces full of anger and grief, a cold wind moving their cloaks. |
| `c42` | K_yasli | The old sultan from the reference standing alone at a palace window at night, moonlight on his face, looking out over the dark city, deep sadness. |
| `c43` | K_yasli | The old sultan from the reference sitting in a covered royal carriage traveling on a dusty road with the army, pale and ill but determined, looking ahead. |
| `c44` | — | A lone Ottoman messenger galloping on horseback at night from left to right along a moonlit road, cloak flying. |
| `c45` | — | Morning near Belgrade: the whole Ottoman army assembled in silence, a man reading an announcement aloud from a paper, soldiers slowly lowering their heads in grief. |
| `c46` | — | The tomb (türbe) of Sultan Süleyman in the garden of the Süleymaniye Mosque: an octagonal domed stone building among cypress trees, soft light, calm. |
| `c47` | — | Close-up: a poet's hand writing verses on paper with a reed pen beside a burning candle at night (no readable letters), a tear falling onto the paper. |
| `c48` | — | Autumn, the castle of Buda on a hill above the Danube: the Ottoman army enters the city gate from left to right, riders and janissaries, golden leaves. |
| `c49` | K_genc | Inside a grand Topkapı Palace hall: a French ambassador in Renaissance clothes bows deeply and presents a sealed letter to the sultan from the reference, who sits on a golden throne. |
| `c50` | — | A 16th century Istanbul public soup kitchen (imaret) courtyard: servants ladle soup from large copper cauldrons into bowls for poor people waiting in line, steam rising, morning light. |
| `c51` | — | Night: a fortress in the middle of a marsh burning, flames and smoke rising from its walls, reflections in the water, Ottoman camp lights around it. |
| `c52` | — | Night: the gate of a burning fortress opens and a small group of Croatian horsemen in armor and red cloaks charge out from right to left into the smoke for a final attack. |

### Bitince
- `rapor.md`'ye özet yaz: kaç görsel/klip `TAMAM`, kaç `SORUNLU`/`TERS`, kaç kredi kaldı.
- Kullanıcıya kısa mesaj: "Bitti. Görseller ve klipler `Belgeler/Kanuni/` klasöründe." Zip ya da Drive bağlantısını ekle.
