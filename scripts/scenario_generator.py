"""
scenario_generator.py - Gemini Pro API ile Senaryo Üretim Motoru.

Konu alır, PDF'teki ritim kurallarına uygun yapılandırılmış JSON senaryo üretir.
Her sahne: hook/twist/outro mantığıyla kurgulanır.
"""

import json
from pathlib import Path

from google import genai
from google.genai import types

from scripts.utils import (
    load_env, read_prompt, save_json, print_header,
    print_step, print_success, print_error, console, TEMP_DIR
)


def generate_scenario(topic: str) -> dict:
    """
    Verilen konuya göre yapılandırılmış video senaryosu üretir.

    Args:
        topic: Video konusu (örn: "What would happen if the Sun suddenly went out?")

    Returns:
        dict: Sahne bazlı JSON senaryo
    """
    print_header("🧠 SENARYO ÜRETİM MOTORU")
    print_step(1, "Gemini Pro API'ye bağlanılıyor...")

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
    system_prompt = read_prompt("system_prompt.txt")
    if not system_prompt:
        print_error("system_prompt.txt bulunamadı!")
        return {}

    print_step(2, f"Senaryo üretiliyor: '{topic}'")

    # Kullanıcı promptu
    user_prompt = f"""Create a complete 10-minute "What If" documentary script for the following topic:

TOPIC: {topic}

Requirements:
- Follow ALL rhythm rules in your system instructions
- The hook (first 30 seconds) must be IMPOSSIBLE to skip
- Include exactly 5-6 scenes with twists at each transition
- Each scene visual prompt must be detailed enough for AI image generation
- The time-traveling rabbit scientist character narrates and appears in key scenes
- Output valid JSON only, no extra text
"""

    try:
        # Gemini API çağrısı
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.8,
                max_output_tokens=8000,
                response_mime_type="application/json",
            ),
        )

        # JSON yanıtını parse et
        raw_text = response.text.strip()

        # JSON bloğunu çıkar (bazen markdown code block içinde gelir)
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        scenario = json.loads(raw_text)

        # Senaryoyu kaydet
        output_path = TEMP_DIR / "scenario.json"
        save_json(scenario, output_path)

        # Özet bilgi yazdır
        scene_count = len(scenario.get("scenes", []))
        title = scenario.get("title", "Başlıksız")

        print_success(f"Senaryo üretildi!")
        console.print(f"  📝 Başlık: [bold]{title}[/bold]")
        console.print(f"  🎬 Sahne sayısı: [bold]{scene_count}[/bold]")
        console.print(f"  💾 Kaydedildi: {output_path}")

        return scenario

    except json.JSONDecodeError as e:
        print_error(f"JSON parse hatası: {e}")
        # Ham yanıtı yine de kaydet (debug için)
        debug_path = TEMP_DIR / "scenario_raw.txt"
        debug_path.write_text(raw_text, encoding="utf-8")
        console.print(f"  Ham yanıt kaydedildi: {debug_path}")
        return {}

    except Exception as e:
        print_error(f"Gemini API hatası: {e}")
        return {}


def load_scenario() -> dict:
    """Daha önce üretilmiş senaryoyu dosyadan yükle."""
    path = TEMP_DIR / "scenario.json"
    if not path.exists():
        print_error("Kaydedilmiş senaryo bulunamadı. Önce generate_scenario() çalıştırın.")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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
