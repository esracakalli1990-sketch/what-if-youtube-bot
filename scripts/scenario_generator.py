"""
scenario_generator.py - Gemini API ile Senaryo Üretim Motoru.

Konu alır, ritim kurallarına uygun yapılandırılmış JSON senaryo üretir.
Her sahne: hook/twist/outro mantığıyla kurgulanır.

Özellikler:
- Senaryo JSON validation
- Retry with exponential backoff
- Fallback model desteği
- Detaylı loglama
"""

import json
from pathlib import Path

from google import genai
from google.genai import types

from scripts.utils import (
    load_env, read_prompt, save_json, load_json, print_header,
    print_step, print_success, print_error, print_warning,
    console, logger, retry, TEMP_DIR
)

# Gerekli sahne alanları
REQUIRED_SCENE_FIELDS = {"scene_number", "narration", "visual_prompt"}
OPTIONAL_SCENE_FIELDS = {"scene_type", "duration_seconds", "twist_element", "asset_type"}

# Bir long videoda kaç sahnenin gerçek video klip olacağı (üst sınır)
MAX_VIDEO_SCENES = 5


def validate_scenario(scenario: dict) -> tuple[bool, list[str]]:
    """
    Senaryo JSON yapısını doğrula.

    Returns:
        tuple: (geçerli_mi, hata_listesi)
    """
    errors = []

    if not isinstance(scenario, dict):
        return False, ["Senaryo bir dict olmalı."]

    if "title" not in scenario:
        errors.append("'title' alanı eksik.")

    scenes = scenario.get("scenes", [])
    if not scenes:
        errors.append("'scenes' listesi boş veya eksik.")
        return False, errors

    if not isinstance(scenes, list):
        errors.append("'scenes' bir liste olmalı.")
        return False, errors

    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            errors.append(f"Sahne {i + 1}: dict olmalı.")
            continue

        for field in REQUIRED_SCENE_FIELDS:
            if field not in scene:
                errors.append(f"Sahne {i + 1}: '{field}' alanı eksik.")
            elif field in ("narration", "visual_prompt") and not scene[field].strip():
                errors.append(f"Sahne {i + 1}: '{field}' boş olamaz.")

    # Sahne numarası sıralaması
    scene_numbers = [s.get("scene_number", 0) for s in scenes if isinstance(s, dict)]
    if scene_numbers != sorted(scene_numbers):
        errors.append("Sahne numaraları sıralı değil.")

    is_valid = len(errors) == 0
    return is_valid, errors


def fix_scenario(scenario: dict, mode: str = "long") -> dict:
    """
    Eksik alanları otomatik tamamla.
    Gemini bazen bazı alanları atlarsa düzeltmeye çalış.
    """
    scenes = scenario.get("scenes", [])
    hook_duration = 10 if mode == "shorts" else 30
    default_duration = 15 if mode == "shorts" else 120

    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            continue

        # Sahne numarası yoksa ekle
        if "scene_number" not in scene:
            scene["scene_number"] = i + 1

        # Sahne tipi yoksa tahmin et
        if "scene_type" not in scene:
            if i == 0:
                scene["scene_type"] = "hook"
            elif i == len(scenes) - 1:
                scene["scene_type"] = "outro"
            else:
                scene["scene_type"] = "development"

        # Süre yoksa varsayılan ekle
        if "duration_seconds" not in scene:
            if scene.get("scene_type") == "hook":
                scene["duration_seconds"] = hook_duration
            else:
                scene["duration_seconds"] = default_duration

        # Varlık tipi yoksa varsayılan: görsel. Video seçimi ayrı adımda yapılır.
        if "asset_type" not in scene:
            scene["asset_type"] = "image"

    scenario["scenes"] = scenes
    return scenario


# Karaktere işaret eden anahtar kelimeler (isim SABİT: "Roli").
# Prompt'lar Roli'yi 1-2 sahnede baş özne yapar, kalan sahnelerde hiç anmaz.
CHARACTER_KEYWORDS = ("roli", "rabbit")


def mentions_character(visual: str) -> bool:
    """Sahne görselinde karakter (Roli/tavşan) anılıyor mu?"""
    text = visual.lower()
    return any(kw in text for kw in CHARACTER_KEYWORDS)


def select_video_scene_numbers(scenes: list[dict], max_videos: int = MAX_VIDEO_SCENES) -> list[int]:
    """
    Long videoda hangi sahnelerin gerçek video klip olacağını seç.

    Kural (muhafazakâr — karakter asla video'ya girmesin):
    - Karakteri (Roli/tavşan) ANAN her sahne GÖRSEL kalır (tutarlılık +
      Veo karakter kayması riski yok).
    - Karakter geçmeyen sahneler (saf atmosfer/olay) video adayıdır.
    - En fazla `max_videos` sahne seçilir (kota ve emek koruması).

    Returns:
        list[int]: Video olacak sahnelerin scene_number listesi.
    """
    candidates = []
    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            continue
        if mentions_character(scene.get("visual_prompt", "")):
            continue  # Karakter sahnesi → görsel kalır
        candidates.append(scene.get("scene_number", i + 1))
    return candidates[:max_videos]


def mark_video_scenes(scenario: dict, mode: str = "long") -> dict:
    """
    Sahnelerin asset_type'ını belirle.

    - SHORTS: TÜM sahneler 'video' (Roli dahil). Kullanıcı 3-4 kısa klibi
      Omni Flash'ta üretir; tam-video short en profesyonel/hareketli formattır.
    - LONG: hibrit — karakter (Roli) sahneleri 'image' (tutarlılık/kayma riski),
      seçili atmosfer sahneleri 'video'. Uzun videoda çok klip gerektiği için
      hibrit kalır.

    Her sahneye asset_type garanti edilir.
    """
    scenes = scenario.get("scenes", [])
    if mode == "shorts":
        for i, scene in enumerate(scenes):
            if isinstance(scene, dict):
                scene["asset_type"] = "video"
        return scenario

    video_nums = set(select_video_scene_numbers(scenes))
    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            continue
        num = scene.get("scene_number", i + 1)
        scene["asset_type"] = "video" if num in video_nums else "image"
    return scenario


def _extract_json(raw_text: str) -> dict:
    """
    Gemini yanıtından JSON'ı çıkar.
    Markdown code block içinde gelebilir.
    """
    text = raw_text.strip()

    # ```json ... ``` formatını temizle
    if text.startswith("```"):
        lines = text.split("\n")
        # İlk satırı (```json) ve son satırı (```) kaldır
        start = 1
        end = len(lines)
        for j in range(len(lines) - 1, 0, -1):
            if lines[j].strip() == "```":
                end = j
                break
        text = "\n".join(lines[start:end]).strip()

    return json.loads(text)


def _call_gemini(
    client: genai.Client,
    system_prompt: str,
    user_prompt: str,
    model: str = "gemini-2.5-flash",
    temperature: float = 0.8,
) -> dict:
    """
    Gemini API çağrısı yap ve JSON parse et.
    retry dekoratörü dışarıda uygulanacak.
    """
    logger.info("Gemini API çağrısı: model=%s, temp=%.1f", model, temperature)

    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=8000,
            response_mime_type="application/json",
        ),
    )

    raw_text = response.text.strip()
    logger.debug("Gemini ham yanıt uzunluğu: %d karakter", len(raw_text))

    scenario = _extract_json(raw_text)
    return scenario


def _scenario_cache_path(mode: str) -> Path:
    """Moda göre senaryo cache dosyası (uzun video ve shorts çakışmasın)."""
    return TEMP_DIR / ("scenario_shorts.json" if mode == "shorts" else "scenario.json")


def generate_scenario(topic: str, force_new: bool = False, mode: str = "long") -> dict:
    """
    Verilen konuya göre yapılandırılmış video senaryosu üretir.

    Args:
        topic: Video konusu
        force_new: True ise cached senaryo varsa bile yeniden üret
        mode: "long" (10 dk video) veya "shorts" (45-60 sn dikey video)

    Returns:
        dict: Sahne bazlı JSON senaryo
    """
    print_header("🧠 SENARYO ÜRETİM MOTORU" + (" — SHORTS" if mode == "shorts" else ""))

    # Cached senaryo kontrolü
    cached_path = _scenario_cache_path(mode)
    if not force_new and cached_path.exists():
        try:
            cached = load_json(cached_path)
            if cached.get("_topic") == topic:
                print_success("Önceden üretilmiş senaryo bulundu, tekrar kullanılıyor.")
                logger.info("Cached senaryo kullanılıyor: %s", topic)
                return cached
        except (json.JSONDecodeError, IOError):
            pass

    print_step(1, "Gemini API'ye bağlanılıyor...")

    # API anahtarını yükle
    keys = load_env()
    api_key = keys.get("GEMINI_API_KEY")

    if not api_key or api_key == "buraya_gemini_api_key_gelecek":
        print_error("GEMINI_API_KEY .env dosyasında tanımlı değil!")
        print_error("Lütfen https://aistudio.google.com adresinden API key alın.")
        return {}

    # Gemini istemcisini başlat
    client = genai.Client(api_key=api_key)

    # Sistem promptunu oku
    prompt_file = "shorts_prompt.txt" if mode == "shorts" else "system_prompt.txt"
    system_prompt = read_prompt(prompt_file)
    if not system_prompt:
        print_error(f"{prompt_file} bulunamadı!")
        return {}

    print_step(2, f"Senaryo üretiliyor: '{topic}'")

    # Kullanıcı promptu
    if mode == "shorts":
        user_prompt = f"""Create a complete 30-45 second "What If" YouTube Shorts script for the following topic:

TOPIC: {topic}

Requirements:
- Follow ALL rhythm/retention rules in your system instructions to the letter
- SCENE 1 IS EVERYTHING: hook in the first 1 second, first word must shock, start mid-catastrophe. FORBIDDEN in scene 1: "What if", "Imagine", greetings, setup, or the rabbit character. Pure visceral consequence, happening now.
- Exactly 3 scenes (4 only if truly necessary). Each scene 18-35 words, present tense, second person.
- Every scene must ESCALATE ("but it gets worse") and end scenes 1-2 on an open loop; ONE big twist at ~60-70%; final line loops back into the opening line
- Roli (the time-traveling rabbit scientist) appears in scene 2 or 3 only, never in the hook, and it is ROLI who delivers the big twist — as someone who has already witnessed this timeline (his signature "I've seen how this ends" tone)
- Each scene visual prompt must be detailed enough for AI image generation in VERTICAL 9:16 format; scene 1's visual is the single most striking image, instantly readable on a phone
- Output valid JSON only, no extra text

ADDITIONAL REQUIRED FIELDS (add these to the root JSON):
- "clickbait_title": A curiosity-gap YouTube title (max 70 chars). Use CAPS for emphasis. Examples: "Gravity DOUBLED for 24 Hours... (You Wouldn't Survive)", "The Sun Went Out. Here's Minute One."
- "youtube_tags": Array of 15-20 topic-specific tags for YouTube SEO. Include long-tail keywords.
- "seo_description": First 2 lines of YouTube description, packed with search keywords (max 200 chars).
- "thumbnail_headline": 2-4 word SHOCKING phrase for thumbnail text overlay. ALL CAPS.
"""
    else:
        user_prompt = f"""Create a complete 10-minute "What If" documentary script for the following topic:

TOPIC: {topic}

Requirements:
- Follow ALL rhythm rules in your system instructions
- The hook (first 30 seconds) must be IMPOSSIBLE to skip
- Include exactly 5-6 scenes with twists at each transition
- Each scene visual prompt must be detailed enough for AI image generation
- Roli (the time-traveling rabbit scientist) narrates and PERSONALLY delivers the biggest reveal, as someone who has already witnessed this timeline — his signature recurring moment
- Output valid JSON only, no extra text

ADDITIONAL REQUIRED FIELDS (add these to the root JSON):
- "clickbait_title": A curiosity-gap YouTube title (max 70 chars). Use CAPS for emphasis. Examples: "What If You Could BREATHE Underwater? (It's Terrifying)", "I Simulated Humans With GILLS... It Got DARK". NEVER put a specific duration or minute/second count in the title (NO "8-Minute", "10-Minute", "in 60 Seconds", "The 8-Minute Truth", etc.) — the real video length varies and a mismatched claim misleads viewers and hurts retention.
- "youtube_tags": Array of 15-20 topic-specific tags for YouTube SEO. Include long-tail keywords. Example: ["what if humans could breathe underwater", "underwater breathing", "human gills", "aquatic humans", "evolution", ...]
- "seo_description": First 2 lines of YouTube description, packed with search keywords (max 200 chars). This appears in search results.
- "thumbnail_headline": 2-4 word SHOCKING phrase for thumbnail text overlay. ALL CAPS. Examples: "BREATHE UNDERWATER?!", "GRAVITY DOUBLED?!"
"""

    # Modeller — ilk başarısız olursa fallback dene
    models_to_try = [
        ("gemini-2.5-flash", 0.8),
        ("gemini-2.0-flash", 0.8),
    ]

    scenario = None
    last_error = None

    import time

    # Gemini ücretsiz katmanı dakika başına istek (RPM) sınırlar. Sınıra
    # takılınca pencere ~1 dakikada sıfırlanır; kısa backoff (2-4sn) aynı dolu
    # pencerede kalıp 6 denemeyi de ~12sn'de tüketiyordu (kullanıcı canlıda tam
    # bunu yaşadı: patladı, 1dk sonra elle deneyince çalıştı). Rate-limit
    # hatalarında uzun backoff ile pencerenin sıfırlanmasını yakalıyoruz.
    RATE_LIMIT_BACKOFF = [10, 20, 40]  # saniye (deneme 1, 2, 3...)
    MAX_ATTEMPTS = 4

    def _is_rate_limit(err) -> bool:
        s = str(err).lower()
        return any(k in s for k in (
            "429", "quota", "rate limit", "rate_limit", "ratelimit",
            "resource_exhausted", "resourceexhausted", "exhausted",
            "too many requests",
        ))

    for model_name, temp in models_to_try:
        console.print(f"  🤖 Model: [bold]{model_name}[/bold]")

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                scenario = _call_gemini(
                    client=client,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model=model_name,
                    temperature=temp,
                )
                break  # Başarılı
            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(
                    "JSON parse hatası (model=%s, deneme=%d/%d): %s",
                    model_name, attempt, MAX_ATTEMPTS, e
                )
                console.print(f"  [yellow]⚠ JSON parse hatası (deneme {attempt}/{MAX_ATTEMPTS})[/yellow]")
                if attempt < MAX_ATTEMPTS:
                    time.sleep(2 ** attempt)
            except Exception as e:
                last_error = e
                is_rl = _is_rate_limit(e)
                # Rate-limit ise dakikalık pencere sıfırlansın diye uzun bekle;
                # diğer geçici API hatalarında kısa backoff yeterli.
                if is_rl:
                    wait = RATE_LIMIT_BACKOFF[min(attempt - 1, len(RATE_LIMIT_BACKOFF) - 1)]
                    label = "kota/rate-limit"
                else:
                    wait = 2 ** attempt
                    label = "API"
                logger.warning(
                    "%s hatası (model=%s, deneme=%d/%d): %s",
                    label, model_name, attempt, MAX_ATTEMPTS, e
                )
                console.print(
                    f"  [yellow]⚠ {label} hatası (deneme {attempt}/{MAX_ATTEMPTS}) — "
                    f"{wait}sn bekleniyor[/yellow]"
                )
                if attempt < MAX_ATTEMPTS:
                    time.sleep(wait)

        if scenario:
            break
        else:
            console.print(f"  [red]✗ {model_name} başarısız, sonraki model deneniyor...[/red]")

    if not scenario:
        print_error(f"Senaryo üretilemedi! Son hata: {last_error}")
        return {}

    # Validation
    is_valid, errors = validate_scenario(scenario)
    if not is_valid:
        logger.warning("Senaryo validation hataları: %s", errors)
        console.print("  [yellow]⚠ Senaryo düzeltiliyor...[/yellow]")
        for err in errors:
            console.print(f"    → {err}")
        scenario = fix_scenario(scenario, mode=mode)
        is_valid, errors = validate_scenario(scenario)
        if not is_valid:
            print_error("Senaryo düzeltilemedi!")
            for err in errors:
                print_error(f"  → {err}")

            # Ham veriyi debug için kaydet
            debug_path = TEMP_DIR / "scenario_debug.json"
            save_json(scenario, debug_path)
            return {}

    # Hibrit video: long videoda seçili sahneleri 'video' olarak işaretle
    scenario = mark_video_scenes(scenario, mode=mode)

    # Metadata ekle
    scenario["_topic"] = topic
    scenario["_mode"] = mode
    scenario["_generated_at"] = __import__("datetime").datetime.now().isoformat()

    # Senaryoyu kaydet
    save_json(scenario, cached_path)

    # Özet bilgi yazdır
    scene_count = len(scenario.get("scenes", []))
    title = scenario.get("title", "Başlıksız")

    print_success("Senaryo üretildi!")
    console.print(f"  📝 Başlık: [bold]{title}[/bold]")
    console.print(f"  🎬 Sahne sayısı: [bold]{scene_count}[/bold]")
    console.print(f"  💾 Kaydedildi: {cached_path}")

    logger.info("Senaryo üretildi: '%s' — %d sahne", title, scene_count)

    return scenario


def load_scenario(mode: str = "long") -> dict:
    """Daha önce üretilmiş senaryoyu dosyadan yükle."""
    path = _scenario_cache_path(mode)
    if not path.exists():
        print_error("Kaydedilmiş senaryo bulunamadı. Önce generate_scenario() çalıştırın.")
        return {}

    try:
        return load_json(path)
    except (json.JSONDecodeError, IOError) as e:
        print_error(f"Senaryo yüklenemedi: {e}")
        return {}


# Doğrudan çalıştırma testi
if __name__ == "__main__":
    from scripts.utils import ensure_directories
    ensure_directories()

    test_topic = "What would happen if the Sun suddenly went out?"
    result = generate_scenario(test_topic)

    if result:
        console.print("\n[bold green]✓ Senaryo motoru başarıyla çalışıyor![/bold green]")
    else:
        console.print("\n[bold red]✗ Senaryo üretimi başarısız.[/bold red]")
