# Proje skill'leri

`remotion-*` klasörleri Remotion'ın resmi agent skill paketinden alındı:
https://github.com/remotion-dev/skills (commit 30d4553, sürüm 4.0.539, 31 Ekim 2026).

Yalnızca bu projede kullanılanlar kopyalandı: markup (animasyon, geçiş, harita, efekt),
render, captions, docs, create. Kurulumdan önce tüm dosyalar okundu; ağ erişimi veya
gizli komut çalıştıran bir şey yok (harita tekniklerindeki .mjs betikleri yalnızca yerel
GeoJSON işler; MapTiler/Mapbox/Google teknikleri API anahtarı ister, kullanılmıyor).

Remotion lisansı: bireyler ve en fazla 3 çalışanlı şirketler için ücretsiz (ticari dahil).
https://github.com/remotion-dev/remotion/blob/main/LICENSE.md

Skill'ler oturum başında yüklenir; yeni eklendiğinde bir sonraki oturumda görünür.
