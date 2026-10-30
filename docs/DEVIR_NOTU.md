# DEVİR NOTU — What-If / Roli's Doomsday Files YouTube Botu

Son güncelleme: 2026-10-30. Bu belge, uzun bir oturumdan yeni bir oturuma geçiş içindir. Önce bunu oku, sonra kullanıcıya kısa özet ver ve §9'daki bekleyen kararları sor. **Kod yazmadan önce onay al.**

## 0. Yeni oturumun ilk işi
1. Bu belgeyi ve `CLAUDE.md`'yi oku.
2. `git fetch origin master && git checkout -B <çalışma-dalı> origin/master`.
3. Kullanıcıya Türkçe, kısa bir durum özeti ver (sistem DURDURULMUŞ; hibrit yükseltme planı onay bekliyor).
4. §9.3'teki kararları sor. Onaysız workflow tetikleme, kod değişikliği yapma.

## 1. TL;DR
- Proje: Gemini senaryo → TTS → manuel video/görsel (Telegram ile) → FFmpeg → YouTube yükleme → analitik.
- Durum: Kanal düşük izlenme aldığı için **sistem durduruldu** (PR #40): `daily-video.yml` ve `telegram-bot.yml` zamanlayıcıları yorum satırı, bildirim yok. Kullanıcı açmadıkça çalıştırma.
- Strateji: Roli'li "What If" formatı tutmadı. Düşünülen yön: Türkçe, gerçek görüntülü, Roli'siz, "nasıl oldu" belgeseli. OpenMontage denemesi ücretsiz kaynaklarla tam otomatiğin yetersiz kaldığını gösterdi → hibrit plan (§9).

## 2. Kullanıcı ve çalışma tarzı
- Türkçe konuşur; kodlamada zayıf. Açık, sade, dürüst/gerçekçi değerlendirme ister; abartı ve süsleme sevmez.
- Yanlış teşhis yaptığında düzeltir (ör. "ilk yorum çalışmıyor", "uzun video gizli"). Kesin olmadığın şeyi kesinmiş gibi söyleme; doğrula.
- "Kodlama yapma" dediği konuşmalarda değişiklik yapma.
- Sırlar (OAuth client secret, API anahtarları) sohbete yazılmaz.
- Videoları SİLME, gizli yap (silme kanal metriklerini bozar).

## 3. Katı git / süreç kuralları
- Geliştirme dalı: `claude/project-handoff-notes-tnt4xj` (oturum atamasına bak).
- Akış: değişiklik → commit → push (`git push -u origin <dal>`; yeniden yazımda `--force-with-lease`) → PR → CI yeşil → squash merge → `git fetch origin master && git checkout -B <dal> origin/master`.
- `gh` yok; `mcp__github__*` araçları kullanılır (ToolSearch ile yükle). Yalnızca kullanıcı isterse PR aç.
- Bot state dosyaları (`pending_production.json`, `topics.json`, `telegram_state.json`, `shorts_queue.json`, `output/`) commit edilmez; çalışma sonrası bunları master'dan geri al.
- Commit sonuna oturumun atıf satırları eklenir.
- Kullanıcı onayı olmadan workflow tetikleme.

## 4. Mimari
Akış: `main.py` (bayraklar: `--shorts`, `--refill` vb.) → `scripts/scenario_generator.py` (Gemini) → `scripts/tts_engine.py` → `scripts/manual_images.py` (Telegram'dan manuel görsel/video toplama) → `scripts/video_assembler.py` (FFmpeg) → `scripts/youtube_uploader.py` → `scripts/analytics.py`.

Dosya haritası (önemli işlevler):
- `scripts/manual_images.py`: `_remote_production_taken` (çift yayın koruması, `DUPLICATE_GUARD_HOURS=12`), `build_asset_plan`, `_add_asset` (sıra koruması), `complete_production`, `_pause_pending` / `resume_pending` (döngü kırıcı), `scene_asset_path` (video öncelikli), prompt'larda "FULL 10 SECOND" ve Roli "MUST NOT SPEAK".
- `scripts/video_assembler.py`: `SCENE_FADE_DURATION=0.3`, `_scene_fade_filter` (dip-to-black), `probe_duration`, `create_scene_clip_from_video` (tpad ile son kare dondurma), `create_scene_clip_video_then_image` (klip + görsel Ken Burns).
- `scripts/scenario_generator.py`: `mark_video_scenes`.
- `scripts/youtube_uploader.py`: `YOUTUBE_TAGS_MAX_CHARS=450`, `_sanitize_tags`, `_ROLI_OPENERS`, `_build_first_comment`, `record_upload`/`load_uploads`.
- `scripts/telegram_bot.py`: komut işleyici, `is_image_doc` (document olarak gelen görseller), tanınmayan dosya uyarısı.
- `scripts/analytics.py`: `build_deep_report`, `build_snapshot`, `traffic_sources`, `reach_summary` (API'de impressions/CTR yok; snapshot'ta "reach" alanı hata verebilir, hata yutulur).
- Workflow'lar: `.github/workflows/daily-video.yml`, `telegram-bot.yml`, `ci.yml`; `concurrency: video-bot`; commit adımında push 4 deneme.
- Promptlar: `prompts/shorts_prompt.txt`, `prompts/system_prompt.txt`.
- Testler: `tests/` (~200 test, pytest). CI bunları çalıştırır.
- Secrets/variables: GitHub Actions secrets (Gemini, ElevenLabs, Telegram, YouTube OAuth token vb.), `IMAGE_MODE=manual` variable'ı. Değerleri sohbete yazma.

## 5. Üretim kuralları
- Short: 4–5 sahne, hepsi video; sahne başı 15–20 kelime (~8 sn anlatım); klip tam ~10 sn.
- Uzun video: video sahnesi için klip + devam görseli (Ken Burns); Roli sahnesi yalnız görsel.
- Geçişler: dip-to-black 0.3 sn; ilk sahne fade-in yok, son sahne fade-out yok.
- Roli: kamerada KONUŞMAZ (TTS ile çakışır), sahne 1'de yok; kanonik `_CHARACTER_BRIEF` (mavi cep saati, kehribar gözler, steampunk).
- Telegram manuel akış: `pending_production.json` + `asset_slots`; dosyalar sırayla; `image/*` document kabul.
- YouTube etiketleri ≤450 karakter (boşluklu etiket +2).

## 6. Öğrenilen dersler
1. invalidTags: boşluklu etiket tırnakla sayılır → sınır payı.
2. Klip donması: klip süresi anlatımdan uzun olmalı (10 sn klip / ~8 sn anlatım).
3. Roli dudak uyumsuzluğu: Roli konuşturulmaz.
4. İlk yorum: iç not (`twist_element`) sızdırılmamalı; Roli girişi + soru.
5. Impressions/CTR YouTube Analytics API'de yok (HTTP 400); trafik kaynağı var.
6. Silinen video 1000 abone / 4000 saat eşiğine sayılmaz; Shorts izlenmesi izlenme saatine sayılmaz.
7. Telegram'da dosya olarak gönderilen görsel sessizce düşüyordu → düzeltildi.
8. Çift yayın: eşzamanlı run'lar → `_remote_production_taken`.
9. GitHub push `fatal error in commit_refs` → push yeniden deneme.

## 7. Durdurma / yeniden açma
- Durduruldu: workflow `schedule:` blokları yorum satırı. Yeniden açmak için yalnızca kullanıcı isterse yorumları kaldır.
- Bekleyen Short: "What would happen if the Earth had rings like Saturn?" (0/4 varlık). `/iptal` veya karar bekliyor.
- Konu havuzu: ~147 pending, 2 completed, 1 failed.

## 8. Veriler
- Kanal: çok düşük izlenme; Shorts dağıtımı soğuk; uzun video sayısı çok az.
- Analitik raporları ve kanal teşhisi önceki oturumda sohbette sunuldu; gerekirse `/analytics` benzeri komutla veya `scripts/analytics.py` ile yeniden alınır (OAuth token gerekir).

## 9. Güncel yön
### 9.1 OpenMontage deneyi (sonuç)
- Lisans AGPL-3.0: kod kopyalanmaz, fikirler yeniden yazılır.
- Ücretsiz stok (Pexels/Pixabay/Coverr/Videvo/NARA anahtar ister; Mixkit/LoC/ESA/NOAA/JAXA/NASA/Archive.org/Wikimedia anahtarsız) ile üretilen deneme videosu kullanıcıya göre "çok amatör". Archive.org keyword eşleşmesi alakasız sonuç verir. Piper Türkçe ses robotik.
- Sonuç: ücretsiz kaynaklarla tam otomatik gerçek-görüntü belgesel mümkün değil; yarı otomatik (insan onaylı) yol önerildi.

### 9.2 Kullanıcının belgesel kriterleri
Belgesel tadı; güçlü kapak ve kanca; etkileyici belgesel sesi (Türkçe, ör. ElevenLabs); gerçek görüntü ama video; sürükleyici anlatı; Roli yok; "ne olurdu" yerine "nasıl oldu".

### 9.3 Hibrit plan (6 faz, onay bekliyor) ve bekleyen kararlar
Fikir: mevcut sistemin güçlü yanları (Gemini senaryo, Telegram akışı, FFmpeg montaj, YouTube yükleme, analitik) korunur; OpenMontage'ten fikirler (kalite kapısı, kaynak çeşitliliği, planlama aşamaları) yeniden yazılır. Önerilen ilk adım: Faz 1 — Telegram kalite kapısı/onay.
Kullanıcıdan beklenen kararlar:
1. Lisans yaklaşımı: fikirleri yeniden yaz (önerilen) vs ayrı araç.
2. Faz 1 ile başlama onayı.
3. Pexels (ve istenirse ElevenLabs) API anahtarlarını GitHub secrets'a ekleme.
4. Önce Türkçe belgesel denemesi mi, yoksa doğrudan otomasyon düzenlemesi mi.
5. Bekleyen Short'u iptal et / sürdür.

## 10. Ortam notları
- Bulut konteyneri geçici; kalıcı olan yalnızca depodur. Bu yüzden bilgi burada.
- Ağ çıkışı ortam ayarındaki alan adı izin listesine bağlı (kaydetmek şart); proxy 403 aşılmaz.
- Pre-installed Chromium/Playwright var; FFmpeg için kontrol et.

## 11. Diğer
- Kullanıcı bir ara projeyi pazarlama fikrini sordu (yalnızca düşünce, karar yok).
- llm-council kurulumu istendi ve sonra silindi (maliyet nedeniyle gerek yok).
