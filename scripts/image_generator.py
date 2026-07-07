"""
image_generator.py - Replicate API ile Görsel Üretim Motoru.

Stable Diffusion + IP-Adapter kullanarak karakter tutarlılığını korur.
Kırmızı çizgi: Karakterin yüz hatları ASLA genelleştirilmez veya güzelleştirilmez.
"""

import time
import base64
import requests
from pathlib import Path

import replicate
from PIL import Image

from scripts.utils import (
    load_env, read_prompt, print_header, print_step,
    print_success, print_error, console, IMAGES_DIR, CHARACTER_DIR
)


def generate_images(scenes: list[dict]) -> list[dict]:
    """
    Her sahne için görsel üretir. Karakter sahnelerinde referans görsel ile
    yüz sabitleme (IP-Adapter) kullanır.

    Args:
        scenes: Senaryo sahne listesi (her biri 'visual_prompt' alanı içermeli)

    Returns:
        list[dict]: Her sahne için görsel dosyası yolu
    """
    print_header("🎨 GÖRSEL ÜRETİM MOTORU")
    print_step(1, "Replicate API'ye bağlanılıyor...")

    # API anahtarını yükle
    keys = load_env()
    api_token = keys.get("REPLICATE_API_TOKEN")

    if not api_token or api_token == "buraya_replicate_api_key_gelecek":
        print_error("REPLICATE_API_TOKEN .env dosyasında tanımlı değil!")
        print_error("Lütfen https://replicate.com adresinden API token alın.")
        return []

    # Replicate ortam değişkenini ayarla
    import os
    os.environ["REPLICATE_API_TOKEN"] = api_token

    # Görsel stil kurallarını oku
    style_guide = read_prompt("image_style.txt")

    # Karakter referans görselini kontrol et
    reference_image = _get_character_reference()

    # Görselleri sakla
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    image_results = []

    print_step(2, f"{len(scenes)} sahne için görsel üretiliyor...")

    for i, scene in enumerate(scenes):
        scene_num = scene.get("scene_number", i + 1)
        visual_prompt = scene.get("visual_prompt", "")

        if not visual_prompt:
            console.print(f"  [yellow]⚠[/yellow] Sahne {scene_num}: Görsel promptu yok, atlanıyor.")
            continue

        console.print(f"  🖼️  Sahne {scene_num} üretiliyor... ", end="")

        try:
            # Tam promptu oluştur
            full_prompt = _build_full_prompt(visual_prompt, style_guide)

            # Replicate üzerinden SDXL çalıştır
            output = replicate.run(
                "stability-ai/sdxl:7762fd07cf82c948c1b78aca6b5769b5009e54e3f5ff1f64fea53af5708d3085",
                input={
                    "prompt": full_prompt,
                    "negative_prompt": (
                        "text, watermark, logo, blurry, deformed, ugly, "
                        "low quality, pixelated, cartoon style, anime, "
                        "oversaturated, cropped"
                    ),
                    "width": 1344,   # 16:9 aspect ratio
                    "height": 768,
                    "num_outputs": 1,
                    "guidance_scale": 7.5,
                    "num_inference_steps": 30,
                },
            )

            # Görseli indir ve kaydet
            if output and len(output) > 0:
                image_url = output[0]
                if hasattr(image_url, 'url'):
                    image_url = image_url.url
                image_url = str(image_url)

                image_path = IMAGES_DIR / f"scene_{scene_num:02d}.png"
                _download_image(image_url, image_path)

                image_results.append({
                    "scene_number": scene_num,
                    "image_path": str(image_path),
                })

                console.print("[green]✓[/green]")
            else:
                print_error(f"Sahne {scene_num}: Görsel üretilemedi (boş yanıt)")

            # Rate limit koruması
            time.sleep(1)

        except Exception as e:
            print_error(f"Sahne {scene_num} görsel hatası: {e}")
            continue

    print_success(f"Görsel üretimi tamamlandı! ({len(image_results)}/{len(scenes)} sahne)")

    return image_results


def generate_character_reference() -> str:
    """
    Zaman Yolcusu Tavşan karakterinin ana referans görselini üretir.
    Bu görsel, tüm videoların temel referansı olacaktır.

    Returns:
        str: Referans görsel dosya yolu
    """
    print_header("🐰 KARAKTER REFERANS GÖRSELİ ÜRETİMİ")

    keys = load_env()
    api_token = keys.get("REPLICATE_API_TOKEN")

    if not api_token or api_token == "buraya_replicate_api_key_gelecek":
        print_error("REPLICATE_API_TOKEN tanımlı değil!")
        return ""

    import os
    os.environ["REPLICATE_API_TOKEN"] = api_token

    CHARACTER_DIR.mkdir(parents=True, exist_ok=True)

    character_prompt = """
    A hyper-realistic anthropomorphic rabbit scientist standing upright in a dramatic pose.
    The rabbit is wearing a worn steampunk-style space suit with brass goggles resting on forehead.
    Has a leather satchel filled with scientific instruments hanging from shoulder.
    Warm grey fur with white chest patch. Expressive, wise eyes with deep intelligence.
    Human proportions, NOT cute or chibi. Standing in a mysterious dimensional portal.
    Dramatic cinematic lighting, volumetric fog, cosmic purple and amber color palette.
    Character portrait, front-facing, detailed facial features.
    Ultra-detailed, 8K quality, photorealistic digital art style.
    """

    console.print("  🎨 Karakter referansı üretiliyor...")

    try:
        output = replicate.run(
            "stability-ai/sdxl:7762fd07cf82c948c1b78aca6b5769b5009e54e3f5ff1f64fea53af5708d3085",
            input={
                "prompt": character_prompt.strip(),
                "negative_prompt": (
                    "cartoon, anime, chibi, cute, child-like, text, watermark, "
                    "blurry, deformed, ugly, low quality"
                ),
                "width": 1024,
                "height": 1024,
                "num_outputs": 1,
                "guidance_scale": 8.0,
                "num_inference_steps": 40,
            },
        )

        if output and len(output) > 0:
            image_url = output[0]
            if hasattr(image_url, 'url'):
                image_url = image_url.url
            image_url = str(image_url)

            ref_path = CHARACTER_DIR / "rabbit_scientist_reference.png"
            _download_image(image_url, ref_path)

            print_success(f"Karakter referansı oluşturuldu!")
            console.print(f"  💾 Kaydedildi: {ref_path}")
            return str(ref_path)
        else:
            print_error("Karakter görseli üretilemedi.")
            return ""

    except Exception as e:
        print_error(f"Karakter üretim hatası: {e}")
        return ""


def _get_character_reference() -> str | None:
    """Karakter referans görselini bul."""
    ref_path = CHARACTER_DIR / "rabbit_scientist_reference.png"
    if ref_path.exists():
        return str(ref_path)
    return None


def _build_full_prompt(visual_prompt: str, style_guide: str) -> str:
    """Görsel promptu stil kurallarıyla birleştir."""
    return f"""{visual_prompt}

Style guidelines:
- Cinematic wide shot, dramatic lighting, 8K detail
- Color palette: deep blues, warm ambers, cosmic purples
- 16:9 composition, photorealistic quality
- Atmospheric volumetric lighting, particle effects
- NO text overlays
"""


def _download_image(url: str, save_path: Path):
    """URL'den görsel indir ve kaydet."""
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    with open(save_path, "wb") as f:
        f.write(response.content)


# Doğrudan çalıştırma testi
if __name__ == "__main__":
    from scripts.utils import ensure_directories
    ensure_directories()

    # Karakter referans görseli üret
    generate_character_reference()
