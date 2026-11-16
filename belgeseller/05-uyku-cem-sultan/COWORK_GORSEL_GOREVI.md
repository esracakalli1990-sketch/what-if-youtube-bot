# COWORK GÖREVİ: Cem Sultan uyku belgeseli, 50 çizim (Gemini · Nano Banana Pro)

Bu dosya, bilgisayarınızda **tarayıcıyı kullanabilen bir Claude'a** verilmek için yazıldı (Claude in Chrome ya da tarayıcı/bilgisayar kullanımı açık Claude masaüstü sohbeti).
Ona şunu yazın: **"Bu dosyadaki görevi baştan sona kendi başına yap. Bana yalnızca bitince ya da gerçekten takılırsan yaz."**

---

## 0. Senin görevin (Claude için)

Gemini'de (https://gemini.google.com) aşağıdaki **2 karakter sayfasını, 46 sahne çizimini ve 2 kapak görselini** tek tek üret, indir ve doğru adla kaydet. Kullanıcı Gemini'de zaten oturum açmış ve Pro üyeliği var. Açık sekmeyi kullan; yeni hesap açma, şifre girme.

### Klasörler (kullanıcının bilgisayarı)
- **Çıktı:** `Belgeler/Cem_Sultan_Gorseller/`. Klasör yoksa oluştur.
- **İlerleme dosyası:** `Belgeler/Cem_Sultan_Gorseller/rapor.md`. Her görselden sonra güncelle. Görev yarıda kesilirse bu dosyaya bakıp **kaldığın yerden** devam et. `TAMAM` olanları tekrar üretme.

### Gemini ayarları
- **Model:** Görsel üretimde **Nano Banana Pro**'yu seç. Model seçicide "Thinking"/"Pro" ile görsel aracı ya da "Create image" seçeneği olabilir. Bulamazsan raporda yaz ve varsayılan görsel üretimiyle devam et.
- **Oran: 16:9 yatay.** Gemini oran seçeneği sunmuyorsa, komutun başına şunu ekle: `Wide 16:9 landscape image.` Kare ya da dikey görsel çıkarsa **aynı komutla bir kez yeniden üret**. Yine olmazsa kaydet ve raporda `KARE` yaz.
- Her komut için **tek görsel** yeterli.
- **Sohbet düzeni:** Karakter tutarlılığı için tek bir uzun sohbet yerine, **her 10–12 görselde yeni bir sohbet** aç ve referans görseli tekrar yükle. Uzun sohbetlerde Gemini yavaşlıyor ve tarz kayıyor.

### Referanslar (karakter tutarlılığı)
1. **İlk iş** `K_cem` ve `K_bayezid` karakter sayfalarını üret ve kaydet.
2. "Ref" sütununda `K_cem` ya da `K_bayezid` yazan her görselde, o karakter sayfasını **görsel olarak yükle** ve komutun başına şunu ekle: `Use the attached character sheet: same face, same turban and same clothes.`
3. `g06`'da Cem çocuktur. Referansı yükle ama komuttaki "as a child" ifadesini koru.

### Stil cümlesi (HER komutun sonuna ekle)
> Detailed graphic-novel illustration, clean ink linework with soft watercolor shading, muted warm palette (amber, ochre, deep blue, candlelight gold), calm and dreamy atmosphere, cinematic 16:9 composition, gentle light, historically accurate late 15th century; NO text, NO letters, NO logos, NO watermark, no crosses, no star-and-crescent flags, no modern objects.

### Her görsel için adımlar
1. `rapor.md`'de bu görsel `TAMAM` ise atla.
2. Gerekiyorsa referans görseli yükle.
3. Komutu **olduğu gibi** yapıştır (İngilizce, değiştirme) ve sonuna stil cümlesini ekle.
4. Görsel gelince **kontrol et**. Şunlardan biri varsa **bir kez yeniden üret**:
   - görselde yazı ya da harf var,
   - modern bir nesne var,
   - haç ya da ay-yıldız bayrak var,
   - Cem ya da Bayezid'in yüzü referanstan belirgin şekilde farklı,
   - görsel fotoğraf gerçekçiliğinde, çizim değil.
5. Görseli **tam çözünürlükte indir** ve `g01.png`, `g02.png` … adıyla çıktı klasörüne kaydet. Gemini .jpg verirse uzantı .jpg kalabilir, adı doğru olsun.
6. `rapor.md`'ye bir satır ekle: `g01 — TAMAM` (yeniden üretildiyse `TAMAM (2. deneme)`, sorunluysa `SORUNLU: …`).

### Bitince
- `rapor.md`'ye özet yaz: kaç görsel `TAMAM`, kaç `SORUNLU`/`KARE`.
- Kullanıcıya kısa bir mesaj yaz: "Bitti. 50 görsel `Belgeler/Cem_Sultan_Gorseller/` klasöründe." Sorunlu görseller varsa listele.
- Görselleri başka bir yere yükleme. Kullanıcı klasörü zip'leyip Claude Code oturumuna kendisi gönderecek.

### Takılırsan
- Gemini görsel üretmeyi reddederse (örneğin Mekke görseli `g22`), komuttan "Kaaba" kelimesini çıkarıp "the holy city of Mecca seen from a distant hill at dawn" diye dene. Yine olmazsa atla ve raporda yaz.
- Günlük sınır uyarısı gelirse dur, raporda kaçıncı görselde kaldığını yaz ve kullanıcıya haber ver.

---

## 1. Karakter sayfaları (önce bunlar)

| Dosya | Komut |
|---|---|
| `K_cem` | Character sheet of Prince Cem, an Ottoman prince in his early twenties: slim handsome face, short dark beard, thoughtful melancholic dark eyes, large white turban wrapped around a small red cap, dark green silk kaftan with gold embroidery. Front view, three-quarter view and full-body view on a plain parchment background. |
| `K_bayezid` | Character sheet of Sultan Bayezid II, an Ottoman sultan in his mid-thirties: calm serious face, full dark beard, large white turban, simple dark blue kaftan with fur collar. Front view, three-quarter view and full-body view on a plain parchment background. |

## 2. Sahne çizimleri

| Dosya | Ref | Komut |
|---|---|---|
| `g01` | — | Night, view from inside a round stone tower room: a narrow arched window with moonlight, a single burning candle on the stone sill, a quill and paper beside it. |
| `g02` | — | Wide view of the old Ottoman city of Bursa at dusk: domed mosques and tombs among green trees, the snowy slopes of Mount Uludağ behind, soft evening mist. |
| `g03` | — | A 15th century Mediterranean galley sailing at night, oars resting, sails glowing in moonlight, calm silver sea. |
| `g04` | — | Winter night inside the Ottoman palace of Edirne: a wooden cradle with a sleeping baby beside a warm fireplace, carpets, a window showing falling snow. |
| `g05` | — | A young Ottoman noblewoman in elegant 15th century dress and a light veil, looking out of a palace window at a snowy garden, gentle melancholy. |
| `g06` | K_cem | A boy prince of about ten, Cem as a child, sitting at a low wooden table with an elderly turbaned teacher, reading a large manuscript by candlelight. |
| `g07` | K_cem | Young Prince Cem on horseback on the open plain of Konya at golden hour, Seljuk domes and minarets in the distance, a few riders behind him. |
| `g08` | — | A peaceful courtyard of a Seljuk-Ottoman palace in Konya: a marble pool, plane trees, poets in turbans sitting on cushions reading verses, evening lanterns. |
| `g09` | K_cem | Close view of Prince Cem's hands turning the pages of an illuminated manuscript with gold floral ornaments (no readable writing), candlelight. |
| `g10` | K_bayezid | Night in Amasya: an Ottoman mansion beside a river under steep rocky cliffs, Prince Bayezid standing at a lit window looking into the dark. |
| `g11` | — | Spring morning, an Ottoman army camp near Gebze: many tents in soft mist, horses grazing, quiet and still. |
| `g12` | — | A large Ottoman imperial tent at night, two janissary guards standing silently at the entrance, warm dim light inside. |
| `g13` | — | Two Ottoman messengers galloping on horses at night in opposite directions on a moonlit road, dust trailing behind. |
| `g14` | — | Morning in front of the land walls of Istanbul: a crowd of janissaries in white börk caps gathering, tense but calm scene. |
| `g15` | K_bayezid | Bayezid entering the gate of the Topkapı palace on horseback, Ottoman statesmen bowing, early morning light. |
| `g16` | K_cem | Prince Cem riding at the head of a column of horsemen, descending a green hill toward the city of Bursa. |
| `g17` | K_cem | Inside a palace room in Bursa: Prince Cem writing a letter at a desk, a wax seal and a candle beside him, evening. |
| `g18` | — | The plain of Yenişehir at dawn: thick morning mist, faint silhouettes of two distant armies, banners without symbols, quiet before battle. |
| `g19` | — | Medieval Cairo at sunset: slender minarets and domes, feluccas sailing on the Nile, warm golden sky. |
| `g20` | K_cem | A Mamluk palace hall in Cairo: the elderly Mamluk Sultan Qaitbay on a throne in a white turban, Prince Cem standing respectfully before him. |
| `g21` | — | A pilgrim caravan crossing the Arabian desert at night: camels with lanterns, a sky full of stars, soft sand dunes. |
| `g22` | — | Distant view of Mecca at dawn in the late 15th century, crowds of pilgrims in white around the Kaaba seen from far away, faces not visible, peaceful and respectful. |
| `g23` | K_cem | Prince Cem and a few horsemen in a narrow Taurus mountain pass at dusk, rocky cliffs and pine trees. |
| `g24` | — | A small quiet cove on the Mediterranean coast at night, a waiting galley anchored, a rowing boat on the shore with a lantern. |
| `g25` | — | The harbor of Rhodes in the 15th century: strong golden-yellow stone walls and towers, ships at anchor, knights in black robes waiting on the quay. |
| `g26` | — | Pierre d'Aubusson, an elderly Grand Master of the Knights of Saint John, in a plain black robe (no cross symbol), in a stone hall with tapestries, a sealed document on the table. |
| `g27` | K_cem | Prince Cem sitting alone in a stone room in Rhodes, looking out of a window at the sea, late afternoon light. |
| `g28` | — | The harbor of Nice in autumn in the late 15th century: stone houses, fishing boats, hills behind, golden leaves. |
| `g29` | — | A medieval castle on a hill at the foot of the Alps, morning mist slowly lifting, forests around. |
| `g30` | K_cem | Winter in a French castle: a snow-covered courtyard seen through a window, Prince Cem in his turban and a fur-lined kaftan watching from inside. |
| `g31` | K_cem | Prince Cem and three companions in turbans walking in an autumn castle garden, falling leaves, one holding a hunting falcon. |
| `g32` | — | A young French noblewoman in a 15th century gown standing on a castle balcony at dusk, looking toward a distant turbaned figure in the garden, soft romantic light. |
| `g33` | — | A tall round medieval stone tower in the small French town of Bourganeuf at night, a single lit window at the top, stars above. |
| `g34` | K_cem | Prince Cem writing poetry at a desk in the tower room at night, candlelight, a small window with stars. |
| `g35` | K_bayezid | Sultan Bayezid II standing at a window in Topkapı palace in the evening, holding a folded letter, the Bosphorus behind. |
| `g36` | — | Rome in spring in the late 15th century: the Tiber river, old bridges, domes and bell towers, soft morning light. |
| `g37` | K_cem | A grand Renaissance hall in Rome: Prince Cem entering in his turban and kaftan, courtiers in Renaissance clothes watching (no religious symbols). |
| `g38` | K_cem | Prince Cem standing at a window of a Renaissance palace in Rome, looking over the rooftops of the city at dawn. |
| `g39` | — | Ottoman envoys in turbans presenting open wooden chests filled with gold coins in a Renaissance palace room. |
| `g40` | K_cem | Prince Cem walking alone in a Roman garden lined with cypress trees at dusk. |
| `g41` | — | A French army of 1494 marching through a snowy Italian valley, banners without symbols, horses and carts. |
| `g42` | K_cem | Prince Cem riding in a covered carriage escorted by French horsemen on a muddy winter road. |
| `g43` | K_cem | A dimly lit room in Naples: Prince Cem lying ill in bed, his few loyal companions in turbans sitting beside him, a candle. |
| `g44` | — | The Bay of Naples at dawn in winter: a calm grey-blue sea, Mount Vesuvius in the distance, quiet and still. |
| `g45` | — | A ship sailing at sunrise through calm waters toward the Sea of Marmara, distant green coastline. |
| `g46` | — | A simple Ottoman tomb with tiles in the Muradiye complex in Bursa, under huge old plane trees, morning sunlight, pigeons on the path. |

## 3. Kapak görselleri

| Dosya | Ref | Komut |
|---|---|---|
| `kapak1` | K_cem | Close portrait of Prince Cem at the narrow window of a stone tower at night, moonlight on his face, sad dark eyes looking at the viewer, candle glow. His face on the RIGHT, dark empty space on the LEFT. |
| `kapak2` | K_cem + K_bayezid | Two brothers in profile facing each other: on the LEFT Sultan Bayezid in warm golden palace light, on the RIGHT Prince Cem in cold blue moonlight, a dark gap between them. |
