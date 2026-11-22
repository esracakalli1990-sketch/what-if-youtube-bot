# COWORK GÖREVİ: Kösem Sultan uyku belgeseli, 59 çizim (Gemini · Nano Banana Pro)

Bu dosya, bilgisayarınızda **tarayıcıyı kullanabilen bir Claude'a** verilmek için yazıldı (Claude in Chrome ya da tarayıcı/bilgisayar kullanımı açık Claude masaüstü sohbeti).
Ona şunu yazın: **"Bu dosyadaki görevi baştan sona kendi başına yap. İlk 4 karakter sayfasından sonra bana göster ve onay al; sonrasını kendi başına bitir. Sorun çıkarsa beklet ve bana yaz."**

---

## 0. Senin görevin (Claude için)

Gemini'de (https://gemini.google.com) aşağıdaki **4 karakter sayfasını, 53 sahne çizimini ve 2 kapak görselini** tek tek üret, indir ve doğru adla kaydet. Kullanıcı Gemini'de zaten oturum açmış ve Pro üyeliği var. Açık sekmeyi kullan; yeni hesap açma, şifre girme.

### Klasörler (kullanıcının bilgisayarı)
- **Çıktı:** `Belgeler/Kosem_Sultan_Gorseller/`. Klasör yoksa oluştur.
- **İlerleme dosyası:** `Belgeler/Kosem_Sultan_Gorseller/rapor.md`. Her görselden sonra güncelle. Görev yarıda kesilirse bu dosyaya bakıp **kaldığın yerden** devam et. `TAMAM` olanları tekrar üretme.

### Gemini ayarları
- **Model:** Görsel üretimde **Nano Banana Pro**. Bulamazsan raporda yaz ve varsayılan görsel üretimiyle devam et.
- **Oran: 16:9 yatay.** Gemini oran seçeneği sunmuyorsa komutun başına `Wide 16:9 landscape image.` ekle. Kare ya da dikey çıkarsa **aynı komutla bir kez yeniden üret**. Yine olmazsa kaydet ve raporda `KARE` yaz.
- **İndirme: en yüksek çözünürlük** (2K varsa 2K).
- Her komut için **tek görsel** yeterli.
- **Her 10–12 görselde yeni bir sohbet** aç ve gereken referans görseli tekrar yükle (uzun sohbette tarz kayıyor).

### ÖNEMLİ: Gerçek kişiye benzememe kuralı
Kösem Sultan hakkında ünlü bir TV dizisi var. Model, isim duyarsa dizideki oyuncuları çizebilir. Bu yüzden:
- Komutlarda **"Kösem", "Kosem", "Mahpeyker" ve padişah adları hiçbir zaman geçmez.** Komutları olduğu gibi kullan, isim ekleme.
- Bir yüz **bilinen bir oyuncuya ya da diziye benziyorsa** aynı komutla bir kez yeniden üret. Hâlâ benziyorsa dur ve kullanıcıya yaz.

### Referanslar (karakter tutarlılığı)
1. **İlk iş** 4 karakter sayfasını üret: `K_genc`, `K_yasli`, `K_ahmed`, `K_murad`. **Kullanıcıya göster ve onay al.** Onaydan sonra devam et.
2. "Ref" sütununda bir karakter yazan her görselde o sayfayı **görsel olarak yükle** ve komutun başına şunu ekle: `Use the attached character sheet: same face, same clothes.`

### Stil cümlesi (HER komutun sonuna ekle)
> Detailed graphic-novel illustration, clean ink linework with soft watercolor shading, muted warm palette (amber, ochre, deep blue, turquoise tile, candlelight gold), calm and dreamy atmosphere, cinematic 16:9 composition, gentle light, historically accurate early 17th century Ottoman Istanbul; NO text, NO letters, NO logos, NO watermark, no crosses, no star-and-crescent flags, no modern objects, no violence.

### Her görsel için adımlar
1. `rapor.md`'de bu görsel `TAMAM` ise atla.
2. Gerekiyorsa referans görseli yükle.
3. Komutu **olduğu gibi** yapıştır (İngilizce, değiştirme) ve sonuna stil cümlesini ekle.
4. Görsel gelince **kontrol et**. Şunlardan biri varsa **bir kez yeniden üret**:
   - yazı ya da harf var,
   - modern nesne var,
   - haç ya da ay-yıldız bayrak var,
   - yüz referanstan belirgin şekilde farklı ya da bilinen bir oyuncuya benziyor,
   - fotoğraf gerçekçiliğinde, çizim değil,
   - **Sultanahmet Camii çiziliyorsa minare sayısı 6 değil** (g02, g13, g14 dışında kubbe yakın planda olabilir).
5. **Tam çözünürlükte indir**, `g01.png`, `g02.png` … adıyla kaydet (.jpg de olur, ad doğru olsun).
6. `rapor.md`'ye satır ekle: `g01 — TAMAM` / `TAMAM (2. deneme)` / `SORUNLU: …`.

### Bitince
- `rapor.md`'ye özet yaz: kaç görsel `TAMAM`, kaç `SORUNLU`/`KARE`.
- Klasörü **tek bir zip** yap: `Kosem_Sultan_Gorseller.zip`. Drive'a yükle, paylaşımı **"Bağlantıya sahip herkes görüntüleyebilir"** yap ve **dosya bağlantısını** (klasör değil) kullanıcıya ver.

### Takılırsan
- Gemini bir görseli reddederse komutu biraz yumuşat (ör. "palace" yerine "Ottoman mansion") ve bir kez dene; olmazsa atla, raporda yaz.
- Günlük sınır uyarısı gelirse dur, raporda kaldığın yeri yaz ve kullanıcıya haber ver.

---

## 1. Karakter sayfaları (önce bunlar → kullanıcı onayı)

| Dosya | Komut |
|---|---|
| `K_genc` | Character sheet of an original fictional young woman of about twenty in an early 17th century Ottoman palace: oval face, light olive skin, dark brown hair partly covered by a small round embroidered cap and a sheer cream veil, large dark eyes, calm intelligent and reserved expression with closed lips; deep blue silk kaftan with small gold floral patterns over a white dress, a thin pearl necklace. Original face that does not resemble any actress, celebrity, TV series or film character. Front view, three-quarter view and full-body view on a plain parchment background. |
| `K_yasli` | Character sheet of the SAME woman about forty years later, around sixty: same oval face and dark eyes, now with soft wrinkles, grey hair under a tall dignified headdress with a long dark veil, wise and tired expression; heavy dark green and gold brocade kaftan with a sable fur collar, a ring with a green stone. Original face that does not resemble any actress or TV character. Front view, three-quarter view and full-body view on a plain parchment background. |
| `K_ahmed` | Character sheet of a young Ottoman sultan of about twenty: slim gentle face, thin dark moustache and a very short young beard, kind thoughtful eyes, large white turban with a small jewelled aigrette, light blue and gold kaftan with fur trim. Original face that does not resemble any actor. Front view, three-quarter view and full-body view on a plain parchment background. |
| `K_murad` | Character sheet of a tall strong young Ottoman sultan in his early twenties: stern determined face, thick dark eyebrows, short dark beard, intense eyes, large white turban with a feather aigrette, crimson kaftan with gold embroidery and fur collar, a sword at his belt. Original face that does not resemble any actor. Front view, three-quarter view and full-body view on a plain parchment background. |

## 2. Sahne çizimleri

| Dosya | Ref | Komut |
|---|---|---|
| `g01` | — | Night, view from inside a palace room in Topkapı: a tall arched window with a wooden lattice, a single burning candle on the marble sill, the moonlit Bosphorus outside. |
| `g02` | — | Wide view of the great Ottoman imperial mosque beside the old Hippodrome in Istanbul at dusk: one large central dome with cascading half domes and EXACTLY SIX slender pencil-shaped minarets, seagulls in a pink sky. |
| `g03` | — | A small Aegean island at dawn: white-washed stone houses on a hill, olive trees, fishing boats in a calm bay, soft morning mist. |
| `g04` | — | The second courtyard of Topkapı Palace in the morning: huge old plane trees, stone paths, low domed buildings with chimneys, peaceful light. |
| `g05` | — | A little girl of about eight sitting on rocks at the seashore of a Greek island, simple dress, hair blowing in the wind, looking at the horizon at sunset. |
| `g06` | — | An Ottoman galley sailing on a calm sea at morning, the distant skyline of Istanbul with domes and minarets slowly appearing through the mist. |
| `g07` | — | The heavy wooden gate of the Harem in Topkapı Palace, decorated with iron studs, two oil lamps glowing on the tiled walls, quiet evening. |
| `g08` | — | A tiled room in the Ottoman palace Harem: several teenage girls in simple kaftans sitting at low wooden desks, reading and writing with reed pens, an older woman teacher watching. |
| `g09` | K_ahmed | The young sultan walking slowly among tulip beds in the palace garden, cypress trees, morning light, two servants following at a distance. |
| `g10` | K_ahmed | The young sultan sitting in an elegant Ottoman caique rowed by oarsmen on the calm Bosphorus, wooden waterside mansions on the shore. |
| `g11` | K_genc | The young woman holding a newborn baby wrapped in white silk, sitting by a lattice window, warm morning light on her face, tender expression. |
| `g12` | — | Small children in little kaftans playing in a palace garden beside a marble fountain, a nanny watching them, spring flowers. |
| `g13` | — | A great Ottoman mosque under construction in early 17th century Istanbul: wooden scaffolding around a half-built dome, hundreds of masons carrying stones, morning mist. |
| `g14` | — | Interior of a great Ottoman mosque: walls covered with thousands of blue and white İznik tiles with tulip and carnation patterns, sunlight through many small windows, carpets on the floor, empty and quiet. |
| `g15` | K_ahmed | The young sultan bent over papers at a low writing desk at night, candlelight, a reed pen in his hand, tired face. |
| `g16` | — | Night: the entrance of an Ottoman domed tomb (türbe) with two oil lamps glowing, tall cypress trees around it, quiet. |
| `g17` | — | The Imperial Council hall (Kubbealtı) of Topkapı Palace in dim light, an empty throne-like seat on a raised platform, gilded lattice window above. |
| `g18` | — | A thoughtful middle-aged Ottoman prince with a dark beard and white turban standing at a palace window, looking outside with a distant, absent gaze. |
| `g19` | — | The stone walls and old trees of the Old Palace in Istanbul in autumn, fallen yellow leaves in a quiet courtyard with a fountain. |
| `g20` | K_genc | The young woman, now about thirty, sitting by a window in a quiet room of the Old Palace, holding a folded letter, thoughtful, evening light. |
| `g21` | — | A boy sultan of about eleven sitting on a large golden throne, a big white turban, Ottoman statesmen in tall turbans standing around him, formal hall. |
| `g22` | K_genc | The woman, now about thirty-five, sitting behind a gilded lattice window, listening to a council meeting below, her face half in shadow, serious and attentive. |
| `g23` | — | An Ottoman grand vizier in a tall white turban reading a letter at a desk with a seal and reed pens, candlelight. |
| `g24` | K_murad | The young sultan on a strong horse in the palace courtyard, determined look, morning light, guards standing in rows. |
| `g25` | — | A long Ottoman army column marching across a desert at sunset, camels and horses, dust, distant domes on the horizon. |
| `g26` | — | The walls of Baghdad seen from a distance across the Tigris river at golden hour, palm trees, calm water. |
| `g27` | — | Celebration in Istanbul: decorated caiques on the Golden Horn, minarets lit with rows of oil lamps at night, crowds on the shore. |
| `g28` | K_yasli | The woman, about forty-five, sitting alone in a dark room at night, a single oil lamp in front of her, deep sorrow, head slightly bowed. |
| `g29` | — | A closed apartment in the palace: lattice windows, heavy curtains, the dim silhouette of a young man sitting alone inside, melancholic. |
| `g30` | — | A nervous young Ottoman prince with a short beard standing at a palace door, statesmen bowing behind him, uncertain expression. |
| `g31` | K_yasli | The woman, about fifty, walking slowly in the palace garden among roses, two servants behind her, evening light. |
| `g32` | — | A luxurious Ottoman palace room filled with sable furs, golden incense burners with thin smoke, silk cushions, jewels on a low table, nobody in it. |
| `g33` | — | A large crowd of people and janissaries gathered in front of a palace gate in the morning mist, seen from a distance, calm but tense. |
| `g34` | K_yasli | A very small boy sultan of about six on a throne with a big white turban, the elderly woman standing beside him with her hand on his shoulder. |
| `g35` | K_yasli | The elderly woman looking out of a palace window over the city of Istanbul at evening, domes and minarets in golden light. |
| `g36` | — | A young Ottoman mother of about twenty-five with fair skin and a light veil, sitting in another palace room beside her small son, proud and watchful. |
| `g37` | — | A busy covered bazaar in 17th century Istanbul: shops with fabrics, copper pots and spices, merchants and customers, morning light through the vaults. |
| `g38` | — | Night: a long empty corridor in Topkapı Palace, tiled walls, a single oil lamp on the wall, shadows, silent. |
| `g39` | — | The domes and chimneys of Topkapı Palace under moonlight, drifting clouds, silent night. |
| `g40` | — | Morning in an Istanbul street: people gathered quietly, shops closed, heads bowed, soft grey light. |
| `g41` | — | A small elegant Ottoman mosque on a hill in Üsküdar with a single minaret, a courtyard with a tiled fountain, morning light. |
| `g42` | — | A large stone caravanserai (han) in Istanbul: a courtyard with arches on two floors, camels and merchants resting, lanterns glowing. |
| `g43` | — | The door of an Ottoman domed tomb in a mosque garden, morning light, birds on the path, cypress trees. |
| `g44` | — | Night: the calm Bosphorus with silver moonlight on the water, the distant lights of Topkapı Palace on the hill. |
| `g45` | — | Evening on a Greek island: a family courtyard with a small fire, a simple dinner table with bread and olives, candlelight, stars above. |
| `g46` | — | The marble courtyard of the palace Harem with a central pool and cypress trees, morning light, quiet. |
| `g47` | K_genc | The young woman (about fifteen, younger version) looking out through a wooden lattice window at the palace garden at dusk, wistful. |
| `g48` | K_ahmed + K_genc | The young sultan and the young woman sitting by a window in an elegant palace kiosk, a mother-of-pearl inlaid reading stand between them, the Bosphorus at sunset outside. |
| `g49` | K_genc | The woman, about thirty-five, writing a letter at night by candlelight, a seal beside the paper, focused. |
| `g50` | — | A narrow Istanbul street at night: a night watchman holding a lantern, closed wooden shops, cobblestones. |
| `g51` | — | A small elegant tiled kiosk in Topkapı Palace with a pool in front, view of the Golden Horn, evening light. |
| `g52` | K_yasli | Small children playing in a palace garden, a nanny with them, the elderly woman watching from a bench and smiling gently. |
| `g53` | — | A long ceremonial procession through the streets of Istanbul: decorated covered carriages, mounted guards, statesmen on horseback, crowds watching from both sides. |

## 3. Kapak görselleri

Kapağın sol alt kısmına büyük "UYKU BELGESELİ" yazısı gelecek; bu yüzden **yüz SAĞDA, sol taraf koyu ve boş** olmalı.

| Dosya | Ref | Komut |
|---|---|---|
| `kapak1` | K_genc | Close portrait of the young woman at a palace window at night, candlelight on her face, calm dark eyes looking at the viewer, the domes of a great mosque glowing faintly behind her. Her face on the RIGHT, dark empty space on the LEFT. |
| `kapak2` | K_yasli | The elderly woman in a dark palace corridor at night, holding a small oil lamp, warm light on her face, serene and wise expression. Her figure on the RIGHT, dark empty corridor on the LEFT. |
