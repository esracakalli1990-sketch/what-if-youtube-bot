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


def select_video_scene_numbers(scenes: list[dict], max_videos: int = MAX_VIDEO_SCENES) -> list[int]:
    """
    Long videoda hangi sahnelerin gerçek video klip olacağını seç.

    Kural:
    - Karakter (tavşan) geçen sahneler GÖRSEL kalır (karakter tutarlılığı için).
    - Kalan sahneler (atmosfer/olay anları) video adayıdır.
    - En fazla `max_videos` sahne seçilir (kota ve emek koruması).

    Returns:
        list[int]: Video olacak sahnelerin scene_number listesi.
    """
    candidates = []
    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            continue
        visual = scene.get("visual_prompt", "").lower()
        if "rabbit" in visual:
            continue  # Karakter sahnesi → görsel kalır
        candidates.append(scene.get("scene_number", i + 1))
    return candidates[:max_videos]


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
        user_prompt = f"""Create a complete 45-60 second "What If" YouTube Shorts script for the following topic:

TOPIC: {topic}

Requirements:
- Follow ALL rhythm rules in your system instructions
- The first sentence must hook within 2 seconds — start with the most shocking consequence
- Exactly 3-4 scenes, ONE big twist at the 60-70% mark, loop-bait ending
- Each scene visual prompt must be detailed enough for AI image generation in VERTICAL 9:16 format
- The time-traveling rabbit scientist character narrates and appears in at least one scene
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
- The time-traveling rabbit scientist character narrates and appears in key scenes
- Output valid JSON only, no extra text

ADDITIONAL REQUIRED FIELDS (add these to the root JSON):
- "clickbait_title": A curiosity-gap YouTube title (max 70 chars). Use CAPS for emphasis. Examples: "What If You Could BREATHE Underwater? (It's Terrifying)", "I Simulated Humans With GILLS... It Got DARK"
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

    for model_name, temp in models_to_try:
        console.print(f"  🤖 Model: [bold]{model_name}[/bold]")

        for attempt in range(1, 4):  # 3 deneme
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
                    "JSON parse hatası (model=%s, deneme=%d/3): %s",
                    model_name, attempt, e
                )
                console.print(f"  [yellow]⚠ JSON parse hatası (deneme {attempt}/3)[/yellow]")
                if attempt < 3:
                    import time
                    time.sleep(2 ** attempt)
            except Exception as e:
                last_error = e
                logger.warning(
                    "API hatası (model=%s, deneme=%d/3): %s",
                    model_name, attempt, e
                )
                console.print(f"  [yellow]⚠ API hatası (deneme {attempt}/3): {e}[/yellow]")
                if attempt < 3:
                    import time
                    time.sleep(2 ** attempt)

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
