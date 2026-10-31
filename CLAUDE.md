# CLAUDE.md

Proje devir bilgisi için önce `docs/DEVIR_NOTU.md`, sonra `docs/AJAN_DERSLERI.md` dosyasını oku
(başka projelerden alınan dersler, niş ölçümü yöntemi, Graphify kurulumu).
Güncel proje: Türkçe uzun tarih belgeseli serisi — `docs/PROJE_PLANI_TARIH_SERISI.md`.

Kısa kurallar:
- Kullanıcı Türkçe konuşur, kodlamada zayıftır; sade ve dürüst anlat.
- Sistem DURDURULMUŞTUR (zamanlayıcılar yorum satırı). Kullanıcı isteyene kadar workflow tetikleme/yeniden açma.
- Kod değişikliğinden önce onay al. Sırları sohbete yazma. Videoları silme, gizli yap.
- Git: dal → PR → CI yeşil → squash merge → `git checkout -B <dal> origin/master`. Bot state dosyalarını commit etme.
- `gh` yok; `mcp__github__*` kullan.
- Kodu incelerken Graphify bilgi haritasını kullan (kurulum: `docs/AJAN_DERSLERI.md` §7).
