"""
image_generator.py - Çoklu AI Model ile Görsel Üretim Motoru.

FLUX, Stable Diffusion veya Gemini Imagen kullanarak sahne görselleri üretir.
Karakter referans görseli ile tutarlı görsel üretimi hedeflenir.

Özellikler:
- FLUX 1.1 Pro model desteği (varsayılan — daha kaliteli, daha hızlı)
- SDXL fallback (Replicate)
- Gemini 3.1 Flash Image fallback (ücretsiz, Google AI)
- Karakter referans görseli (IP-Adapter) desteği
- Retry mekanizması
- Görsel kalite ve boyut doğrulama
- Cached görselleri atla (resume desteği)
"""

import time
import os
import requests
import base64
from pathlib import Path

import replicate
from PIL import Image
from google import genai

from scripts.utils import (
    load_env, read_prompt, print_header, print_step,
    print_success, print_error, print_warning, console,
    logger, retry, IMAGES_DIR, CHARACTER_DIR, THUMBNAILS_DIR
)


# ──────────────────────────────────────
# Görsel Doğrulama
# ──────────────────────────────────────
def _validate_image(image_path: Path, min_width: int = 512, min_height: int = 512) -> bool:
    """
    İndirilen görselin geçerliliğini kontrol et.

    Returns:
        bool: Görsel geçerli mi?
    """
    try:
        if not image_path.exists():
            return False

        # Minimum dosya boyutu (10KB)
        if image_path.stat().st_size < 10240:
            logger.warning("Görsel çok küçük: %s (%d bytes)", image_path, image_path.stat().st_size)
            return False

        # Pillow ile aç ve boyutları kontrol et
        with Image.open(image_path) as img:
            w, h = img.size
            if w < min_width or h < min_height:
                logger.warning("Görsel çözünürlüğü yetersiz: %s (%dx%d)", image_path, w, h)
                return False

        return True
    except Exception as e:
        logger.warning("Görsel doğrulama hatası: %s — %s", image_path, e)
        return False


# ──────────────────────────────────────
# Görsel İndirme
# ──────────────────────────────────────

# Bazı CDN'ler (Pollinations dahil) python-requests kimliğini engelliyor
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )
}


def _download_image(url: str, save_path: Path, max_retries: int = 3) -> bool:
    """URL'den görsel indir ve kaydet."""
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=120, stream=True, headers=_BROWSER_HEADERS)
            response.raise_for_status()

            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.debug("Görsel indirildi: %s → %s", url[:80], save_path.name)
            return True

        except Exception as e:
            last_error = e
            logger.warning("Görsel indirme hatası (deneme %d/%d): %s", attempt, max_retries, e)
            if save_path.exists():
                save_path.unlink()
            if attempt < max_retries:
                time.sleep(2 ** attempt)

    # Actions logunda görünsün — teşhis için
    if last_error:
        console.print(f"[dim]indirme: {str(last_error)[:120]}[/dim] ", end="")
    return False


# ──────────────────────────────────────
# Prompt Hazırlama
# ──────────────────────────────────────
def _build_full_prompt(visual_prompt: str, style_guide: str = "", vertical: bool = False) -> str:
    """Görsel promptu stil kurallarıyla birleştir. Pollinations/FLUX için optimize."""
    composition = (
        "9:16 vertical portrait composition, subject centered for mobile fullscreen"
        if vertical else "16:9 composition"
    )
    base_style = f"""
Ultra realistic, cinematic wide shot, dramatic volumetric lighting, 8K resolution.
Color palette: deep ocean blues, warm amber highlights, bioluminescent neon accents.
{composition}, photorealistic quality, trending on ArtStation, masterpiece.
Atmospheric volumetric lighting, depth of field, lens flares, particle effects.
Professional digital art, Unreal Engine 5 render quality.
Hyper-detailed textures, sharp focus, dramatic contrast.
NO text overlays, NO watermarks, NO UI elements, NO borders.
"""
    # Stil kılavuzunu ekle (varsa)
    extra = f"\n{style_guide}" if style_guide else ""
    return f"{visual_prompt}\n\n{base_style.strip()}{extra}"


# ──────────────────────────────────────
# Replicate Model Çağrıları
# ──────────────────────────────────────
def _generate_with_flux(prompt: str, width: int = 1344, height: int = 768) -> str | None:
    """
    FLUX 1.1 Pro ile görsel üret.

    Returns:
        str | None: Görsel URL'si veya None
    """
    try:
        aspect_ratio = "9:16" if height > width else "16:9"
        output = replicate.run(
            "black-forest-labs/flux-1.1-pro",
            input={
                "prompt": prompt,
                "width": width,
                "height": height,
                "aspect_ratio": aspect_ratio,
                "output_format": "png",
                "safety_tolerance": 2,
                "prompt_upsampling": True,
            },
        )

        # FLUX çıktısı direkt URL string olabilir
        if isinstance(output, str):
            return output
        if hasattr(output, 'url'):
            return output.url
        if isinstance(output, list) and len(output) > 0:
            item = output[0]
            return item.url if hasattr(item, 'url') else str(item)

        logger.warning("FLUX beklenmeyen çıktı formatı: %s", type(output))
        return None

    except Exception as e:
        logger.warning("FLUX üretim hatası: %s", e)
        raise


def _generate_with_sdxl(prompt: str, width: int = 1344, height: int = 768) -> str | None:
    """
    SDXL ile görsel üret (fallback model).

    Returns:
        str | None: Görsel URL'si veya None
    """
    try:
        output = replicate.run(
            "stability-ai/sdxl:7762fd07cf82c948c1b78aca6b5769b5009e54e3f5ff1f64fea53af5708d3085",
            input={
                "prompt": prompt,
                "negative_prompt": (
                    "text, watermark, logo, blurry, deformed, ugly, "
                    "low quality, pixelated, cartoon style, anime, "
                    "oversaturated, cropped"
                ),
                "width": width,
                "height": height,
                "num_outputs": 1,
                "guidance_scale": 7.5,
                "num_inference_steps": 30,
            },
        )

        if output and len(output) > 0:
            item = output[0]
            if hasattr(item, 'url'):
                return item.url
            return str(item)

        return None

    except Exception as e:
        logger.warning("SDXL üretim hatası: %s", e)
        raise


def _generate_with_pollinations(prompt: str, save_path: Path, width: int = 1344, height: int = 768) -> bool:
    """
    Pollinations.ai (ücretsiz, API anahtarsız) kullanarak görsel üretir.
    """
    import urllib.parse
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
        return _download_image(url, save_path)
    except Exception as e:
        logger.warning("Pollinations üretim hatası: %s", e)
        return False


def _generate_with_gemini_image(prompt: str, save_path: Path, vertical: bool = False) -> bool:
    """
    Gemini görsel modeli (gemini-2.5-flash-image) ile görsel üret.

    Replicate'in aksine ücretsiz katmanda çalışır — Replicate faturalandırması
    kapalıyken ana yedek görevi görür.
    """
    keys = load_env()
    api_key = keys.get("GEMINI_API_KEY", "")
    if not api_key or "buraya" in api_key:
        return False

    try:
        from google.genai import types as genai_types

        client = genai.Client(api_key=api_key)

        # aspect_ratio destekleyen SDK'larda dikey/yatay iste; desteklemiyorsa düz config
        try:
            config = genai_types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=genai_types.ImageConfig(
                    aspect_ratio="9:16" if vertical else "16:9"
                ),
            )
        except Exception:
            config = genai_types.GenerateContentConfig(response_modalities=["IMAGE"])

        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
            config=config,
        )

        for candidate in response.candidates or []:
            for part in candidate.content.parts or []:
                inline = getattr(part, "inline_data", None)
                if inline and inline.data:
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(save_path, "wb") as f:
                        f.write(inline.data)
                    logger.info("Gemini görsel üretildi: %s", save_path.name)
                    return True

        logger.warning("Gemini görsel yanıtında resim yok.")
        return False

    except Exception as e:
        logger.warning("Gemini görsel üretim hatası: %s", e)
        console.print(f"[dim]{str(e)[:100]}[/dim] ", end="")
        return False


# ──────────────────────────────────────
# Ana Görsel Üretim Fonksiyonu
# ──────────────────────────────────────
def generate_images(scenes: list[dict], vertical: bool = False) -> list[dict]:
    """
    Her sahne için görsel üretir. Önce FLUX dener, başarısız olursa SDXL'e düşer.

    Args:
        scenes: Senaryo sahne listesi (her biri 'visual_prompt' alanı içermeli)
        vertical: True ise Shorts için 9:16 dikey görsel üretilir

    Returns:
        list[dict]: Her sahne için görsel dosyası yolu
    """
    print_header("🎨 GÖRSEL ÜRETİM MOTORU" + (" — DİKEY 9:16" if vertical else ""))

    img_width, img_height = (768, 1344) if vertical else (1344, 768)
    print_step(1, "Replicate API'ye bağlanılıyor...")

    # API anahtarını yükle
    keys = load_env()
    api_token = keys.get("REPLICATE_API_TOKEN")

    if not api_token or api_token == "buraya_replicate_api_key_gelecek":
        print_error("REPLICATE_API_TOKEN .env dosyasında tanımlı değil!")
        print_error("Lütfen https://replicate.com adresinden API token alın.")
        return []

    # Replicate ortam değişkenini ayarla
    os.environ["REPLICATE_API_TOKEN"] = api_token

    # Görsel stil kurallarını oku
    style_guide = read_prompt("image_style.txt")

    # Görselleri sakla
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    image_results = []
    failed_scenes = []

    total_scenes = len(scenes)
    print_step(2, f"{total_scenes} sahne için görsel üretiliyor...")
    logger.info("Görsel üretim başlıyor: %d sahne", total_scenes)

    for i, scene in enumerate(scenes):
        scene_num = scene.get("scene_number", i + 1)
        visual_prompt = scene.get("visual_prompt", "")

        if not visual_prompt:
            print_warning(f"Sahne {scene_num}: Görsel promptu yok, atlanıyor.")
            logger.warning("Sahne %d: visual_prompt boş, atlandı.", scene_num)
            continue

        # Dikey görseller ayrı dosya adı kullanır (yatay cache ile çakışmasın)
        suffix = "_vertical" if vertical else ""
        image_path = IMAGES_DIR / f"scene_{scene_num:02d}{suffix}.png"

        # Resume desteği — daha önce üretilmiş mi?
        if image_path.exists() and _validate_image(image_path):
            image_results.append({
                "scene_number": scene_num,
                "image_path": str(image_path),
            })
            console.print(f"  🖼️  Sahne {scene_num}/{total_scenes}: [cyan]♻ cached[/cyan]")
            logger.info("Sahne %d: Cached görsel kullanılıyor", scene_num)
            continue

        console.print(f"  🖼️  Sahne {scene_num}/{total_scenes} üretiliyor... ", end="")

        full_prompt = _build_full_prompt(visual_prompt, style_guide, vertical=vertical)
        image_url = None
        success = False

        # Deneme 1: FLUX
        last_replicate_error = None
        for attempt in range(1, 4):
            try:
                image_url = _generate_with_flux(full_prompt, width=img_width, height=img_height)
                if image_url:
                    break
            except Exception as e:
                last_replicate_error = e
                logger.warning("FLUX deneme %d/3 başarısız: %s", attempt, e)
                if attempt < 3:
                    time.sleep(2 ** attempt)

        # Deneme 2: SDXL (fallback)
        if not image_url:
            console.print("[yellow]FLUX→SDXL[/yellow] ", end="")
            logger.info("Sahne %d: FLUX başarısız, SDXL deneniyor", scene_num)
            for attempt in range(1, 3):
                try:
                    image_url = _generate_with_sdxl(full_prompt, width=img_width, height=img_height)
                    if image_url:
                        break
                except Exception as e:
                    last_replicate_error = e
                    logger.warning("SDXL deneme %d/2 başarısız: %s", attempt, e)
                    if attempt < 2:
                        time.sleep(2 ** attempt)

        # Replicate tamamen başarısızsa nedenini Actions logunda göster
        if not image_url and last_replicate_error:
            console.print(f"[dim]Replicate: {str(last_replicate_error)[:120]}[/dim] ", end="")

        # Görseli indir ve doğrula (Replicate modelleri)
        min_w, min_h = (512, 768) if vertical else (768, 512)
        if image_url:
            if _download_image(image_url, image_path):
                if _validate_image(image_path, min_width=min_w, min_height=min_h):
                    image_results.append({
                        "scene_number": scene_num,
                        "image_path": str(image_path),
                    })
                    console.print("[green]✓[/green]")
                    success = True
                else:
                    console.print("[red]✗ doğrulama hatası[/red]")
                    if image_path.exists():
                        image_path.unlink()
            else:
                console.print("[red]✗ indirme hatası[/red]")

        # Deneme 3: Gemini görsel modeli (ücretsiz — Replicate faturasız hesaplarda ana yedek)
        if not success:
            console.print("[yellow]→Gemini[/yellow] ", end="")
            logger.info("Sahne %d: Replicate başarısız, Gemini görsel deneniyor", scene_num)
            for attempt in range(1, 3):
                if _generate_with_gemini_image(full_prompt, image_path, vertical=vertical):
                    if _validate_image(image_path, min_width=512, min_height=512):
                        image_results.append({
                            "scene_number": scene_num,
                            "image_path": str(image_path),
                        })
                        console.print("[green]✓[/green]")
                        success = True
                        break
                    else:
                        if image_path.exists():
                            image_path.unlink()
                if attempt < 2:
                    time.sleep(3)

        # Deneme 4: Pollinations (ücretsiz fallback)
        if not success:
            console.print("[yellow]→Pollinations[/yellow] ", end="")
            logger.info("Sahne %d: Gemini başarısız, Pollinations deneniyor", scene_num)
            for attempt in range(1, 3):
                if _generate_with_pollinations(full_prompt, image_path, width=img_width, height=img_height):
                    if _validate_image(image_path, min_width=512, min_height=512):
                        image_results.append({
                            "scene_number": scene_num,
                            "image_path": str(image_path),
                        })
                        console.print("[green]✓[/green]")
                        success = True
                        break
                    else:
                        if image_path.exists():
                            image_path.unlink()
                if attempt < 2:
                    time.sleep(3)

        if not success:
            console.print("[red]✗ üretim hatası[/red]")
            failed_scenes.append(scene_num)

        # Rate limit koruması
        if i < total_scenes - 1:
            time.sleep(1.5)

    # Sonuç özeti
    console.print()
    if image_results:
        print_success(f"Görsel üretimi tamamlandı! ({len(image_results)}/{total_scenes} sahne)")
    if failed_scenes:
        print_warning(f"Başarısız sahneler: {failed_scenes}")
    if not image_results:
        print_error("Hiçbir görsel üretilemedi!")

    logger.info("Görsel üretim sonucu: %d/%d başarılı", len(image_results), total_scenes)
    return image_results


# ──────────────────────────────────────
# Karakter Referans Görseli
# ──────────────────────────────────────
def generate_character_reference() -> str:
    """
    Zaman Yolcusu Tavşan karakterinin ana referans görselini üretir.

    Returns:
        str: Referans görsel dosya yolu
    """
    print_header("🐰 KARAKTER REFERANS GÖRSELİ ÜRETİMİ")

    keys = load_env()
    api_token = keys.get("REPLICATE_API_TOKEN")

    if not api_token or api_token == "buraya_replicate_api_key_gelecek":
        print_error("REPLICATE_API_TOKEN tanımlı değil!")
        return ""

    os.environ["REPLICATE_API_TOKEN"] = api_token
    CHARACTER_DIR.mkdir(parents=True, exist_ok=True)

    # Mevcut referans kontrolü
    ref_path = CHARACTER_DIR / "rabbit_scientist_reference.png"
    if ref_path.exists() and _validate_image(ref_path, min_width=512, min_height=512):
        print_success("Mevcut karakter referansı bulundu, yeniden üretim atlanıyor.")
        console.print(f"  💾 Mevcut: {ref_path}")
        return str(ref_path)

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
    logger.info("Karakter referans görseli üretiliyor")

    image_url = None

    # FLUX ile dene
    for attempt in range(1, 4):
        try:
            image_url = _generate_with_flux(
                character_prompt.strip(),
                width=1024,
                height=1024
            )
            if image_url:
                break
        except Exception as e:
            logger.warning("Karakter FLUX deneme %d/3: %s", attempt, e)
            if attempt < 3:
                time.sleep(2 ** attempt)

    # SDXL fallback
    if not image_url:
        logger.info("Karakter: FLUX başarısız, SDXL deneniyor")
        for attempt in range(1, 3):
            try:
                image_url = _generate_with_sdxl(
                    character_prompt.strip(),
                    width=1024,
                    height=1024
                )
                if image_url:
                    break
            except Exception as e:
                logger.warning("Karakter SDXL deneme %d/2: %s", attempt, e)
                if attempt < 2:
                    time.sleep(2 ** attempt)

    if image_url and _download_image(image_url, ref_path):
        if _validate_image(ref_path, min_width=512, min_height=512):
            print_success("Karakter referansı oluşturuldu!")
            console.print(f"  💾 Kaydedildi: {ref_path}")
            logger.info("Karakter referansı kaydedildi: %s", ref_path)
            return str(ref_path)

    # Pollinations fallback
    logger.info("Karakter: Replicate başarısız, Pollinations deneniyor")
    console.print("  🔄 Pollinations ile deneniyor...")
    for attempt in range(1, 3):
        if _generate_with_pollinations(character_prompt.strip(), ref_path, width=1024, height=1024):
            if _validate_image(ref_path, min_width=512, min_height=512):
                print_success("Karakter referansı oluşturuldu! (Pollinations)")
                console.print(f"  💾 Kaydedildi: {ref_path}")
                logger.info("Karakter referansı kaydedildi (Pollinations): %s", ref_path)
                return str(ref_path)
        if attempt < 2:
            time.sleep(3)

    print_error("Karakter görseli üretilemedi.")
    return ""


# ──────────────────────────────────────
# Thumbnail Üretimi
# ──────────────────────────────────────
def generate_thumbnail(title: str, concept: str = "") -> str:
    """
    YouTube-optimized thumbnail üretir.

    İki aşamalı süreç:
    1. AI ile çarpıcı arka plan görseli üret
    2. thumbnail_composer ile büyük yazı, glow, kontrast overlay ekle

    Args:
        title: Video başlığı
        concept: Thumbnail konsepti (senaryodan gelir)

    Returns:
        str: Thumbnail dosya yolu
    """
    from scripts.thumbnail_composer import compose_thumbnail, extract_thumbnail_headline

    print_header("🖼️ THUMBNAIL ÜRETİMİ")

    keys = load_env()
    api_token = keys.get("REPLICATE_API_TOKEN")

    if not api_token or api_token == "buraya_replicate_api_key_gelecek":
        print_error("REPLICATE_API_TOKEN tanımlı değil!")
        return ""

    os.environ["REPLICATE_API_TOKEN"] = api_token
    THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

    # Thumbnail arka plan promptu — yazı olmadan, çarpıcı görsel
    if concept:
        thumb_prompt = concept
    else:
        thumb_prompt = f"A dramatic, eye-catching scene for: {title}"

    thumb_prompt += """
    Ultra dramatic, cinematic composition. Vivid saturated colors with extreme contrast.
    Golden hour or neon lighting, strong bokeh, depth of field.
    Photorealistic, 8K quality, epic scale, trending on ArtStation.
    Close-up emotional shot or dramatic wide scene.
    ABSOLUTELY NO text, NO watermarks, NO borders, NO letters.
    Clean background composition optimized for text overlay.
    """

    console.print("  🎨 Adım 1: Arka plan görseli üretiliyor...")
    logger.info("Thumbnail üretiliyor: %s", title)

    image_url = None
    raw_thumb_path = THUMBNAILS_DIR / "thumbnail_raw.png"

    # FLUX ile dene
    for attempt in range(1, 4):
        try:
            image_url = _generate_with_flux(
                thumb_prompt.strip(),
                width=1344,
                height=768,
            )
            if image_url:
                break
        except Exception as e:
            logger.warning("Thumbnail FLUX deneme %d/3: %s", attempt, e)
            if attempt < 3:
                time.sleep(2 ** attempt)

    thumb_generated = False

    if image_url and _download_image(image_url, raw_thumb_path):
        thumb_generated = True

    # Gemini fallback (ücretsiz)
    if not thumb_generated:
        logger.info("Thumbnail: Replicate başarısız, Gemini deneniyor")
        console.print("  🔄 Gemini ile deneniyor...")
        if _generate_with_gemini_image(thumb_prompt.strip(), raw_thumb_path, vertical=False):
            thumb_generated = True

    # Pollinations fallback
    if not thumb_generated:
        logger.info("Thumbnail: Gemini başarısız, Pollinations deneniyor")
        console.print("  🔄 Pollinations ile deneniyor...")
        for attempt in range(1, 3):
            if _generate_with_pollinations(thumb_prompt.strip(), raw_thumb_path, width=1344, height=768):
                thumb_generated = True
                break
            if attempt < 2:
                time.sleep(3)

    if thumb_generated and raw_thumb_path.exists():
        # Adım 2: Thumbnail Composer ile yazı ve efekt overlay
        console.print("  ✏️  Adım 2: Yazı ve efektler ekleniyor...")

        headline = extract_thumbnail_headline(title)
        final_path = str(THUMBNAILS_DIR / "thumbnail_youtube.png")

        result = compose_thumbnail(
            background_image_path=str(raw_thumb_path),
            headline_text=headline,
            output_path=final_path,
            accent_color=(255, 255, 0),  # Sarı — YouTube klasik
            text_position="center",
            add_vignette=True,
            add_gradient_overlay=True,
        )

        if result:
            print_success(f"Thumbnail oluşturuldu! (Headline: {headline})")
            console.print(f"  💾 Kaydedildi: {final_path}")
            logger.info("Composed thumbnail kaydedildi: %s", final_path)
            return final_path
        else:
            # Fallback: yazısız thumbnail
            logger.warning("Composer başarısız, yazısız thumbnail kullanılıyor")
            try:
                with Image.open(raw_thumb_path) as img:
                    resized = img.resize((1280, 720), Image.LANCZOS)
                    resized.save(final_path, "PNG", quality=95)
                return final_path
            except Exception as e:
                logger.error("Thumbnail resize hatası: %s", e)
                return str(raw_thumb_path)

    print_error("Thumbnail üretilemedi.")
    return ""


def _get_character_reference() -> str | None:
    """Karakter referans görselini bul."""
    ref_path = CHARACTER_DIR / "rabbit_scientist_reference.png"
    if ref_path.exists():
        return str(ref_path)
    return None


# Doğrudan çalıştırma testi
if __name__ == "__main__":
    from scripts.utils import ensure_directories
    ensure_directories()

    # Karakter referans görseli üret
    generate_character_reference()
