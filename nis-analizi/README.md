# Niş analizi

Küçük kanalların (abone < 10.000) son 2 yıldaki uzun videolarının (> 3 dk) aramada nasıl performans gösterdiğini ölçer. Yöntem: `docs/AJAN_DERSLERI.md` §4.

```bash
cd nis-analizi
python3 topla.py    # YouTube Data API: arama → video → kanal (önbellekli, kota bitince eldekini kaydeder)
python3 analiz.py   # niş başına medyan, %80 güven aralığı, 1k+/10k+ payı, örnek başlıklar
```

- Kelime listesi: `nisler.json` (`tr` → bölge TR, `en` → bölge US).
- `onbellek/` ve `ham_veri.json` commit edilmez; aynı komut tekrar çalışınca önbellekteki aramalar kota harcamaz.
- Arama kotası günlük; Pasifik gece yarısı sıfırlanır.

Durum (2026-10-30): 56 kelimenin 16'sı tarandı (niş 1–2). Kalanlar kota sıfırlanınca taranacak.
