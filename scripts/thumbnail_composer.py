"""
thumbnail_composer.py - YouTube-Optimized Thumbnail Composer.

AI'dan gelen ham görseli alıp üzerine YouTube standartlarına uygun
büyük yazı, glow efektleri ve kontrast katmanları ekler.

YouTube 2026 Thumbnail Kuralları:
- 3 saniye kuralı: kullanıcı 3 saniyede tıklamalı
- Dev yazı: 2-4 kelime MAX, şok/merak uyandıran
- Yüksek kontrast: sarı/beyaz yazı + koyu outline
- Mobil-first: %70 görüntüleme mobilden
- 1280x720 çıktı boyutu
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from pathlib import Path
import textwrap

from scripts.utils import logger


def compose_thumbnail(
    background_image_path: str,
    headline_text: str,
    output_path: str,
    accent_color: tuple = (255, 255, 0),  # Sarı
    text_position: str = "center",  # center, bottom, top
    add_vignette: bool = True,
    add_gradient_overlay: bool = True,
) -> str:
    """
    AI görseli üzerine YouTube-optimized metin ve efektler ekler.

    Args:
        background_image_path: AI üretimi ham görsel
        headline_text: Thumbnail üzerindeki büyük yazı (2-4 kelime)
        output_path: Çıktı dosyası yolu
        accent_color: Yazı rengi (RGB tuple)
        text_position: Yazı konumu
        add_vignette: Kenar karartma efekti
        add_gradient_overlay: Alt gradient overlay

    Returns:
        str: Çıktı dosya yolu
    """
    try:
        # Arka plan görselini aç ve resize et
        bg = Image.open(background_image_path).convert("RGBA")
        bg = bg.resize((1280, 720), Image.LANCZOS)

        # Kontrast ve parlaklık artır
        enhancer = ImageEnhance.Contrast(bg)
        bg = enhancer.enhance(1.3)
        enhancer = ImageEnhance.Color(bg)
        bg = enhancer.enhance(1.2)

        # Vignette efekti (kenar karartma)
        if add_vignette:
            bg = _apply_vignette(bg)

        # Gradient overlay (alt kısım karartma — yazı okunabilirliği için)
        if add_gradient_overlay:
            bg = _apply_gradient_overlay(bg)

        # Metin katmanı oluştur
        txt_layer = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        draw = ImageDraw.Draw(txt_layer)

        # Font yükle (sistem fontu)
        font = _get_best_font(size=90)
        small_font = _get_best_font(size=40)

        # Metni hazırla
        lines = _prepare_headline(headline_text)

        # Metin konumunu hesapla
        y_offset = _calculate_y_offset(text_position, lines, font, draw)

        # Her satır için glow + outline + text çiz
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (1280 - text_width) // 2

            # 1. Glow efekti (büyük bulanık gölge)
            _draw_glow(draw, x, y_offset, line, font, glow_color=(0, 0, 0), glow_size=8)

            # 2. Kalın outline (siyah kenar)
            _draw_outline(draw, x, y_offset, line, font, outline_color=(0, 0, 0), thickness=5)

            # 3. Ana metin (parlak renk)
            draw.text((x, y_offset), line, font=font, fill=accent_color)

            line_height = bbox[3] - bbox[1]
            y_offset += line_height + 10

        # Katmanları birleştir
        result = Image.alpha_composite(bg, txt_layer)
        result = result.convert("RGB")

        # Kaydet
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        result.save(output_path, "PNG", quality=95)

        logger.info("Thumbnail composed: %s → %s", headline_text, output_path)
        return output_path

    except Exception as e:
        logger.error("Thumbnail compose hatası: %s", e)
        return ""


def _apply_vignette(image: Image.Image) -> Image.Image:
    """Kenar karartma efekti."""
    w, h = image.size
    vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vignette)

    # Oval gradient — köşeler karanlık, merkez açık
    for i in range(40):
        alpha = int(255 * (i / 40) * 0.5)
        margin = i * max(w, h) // 200
        draw.ellipse(
            [margin, margin, w - margin, h - margin],
            outline=(0, 0, 0, 0),
            fill=None,
        )

    # Basit yaklaşım: yarı saydam siyah katman + gaussian blur
    dark_layer = Image.new("RGBA", (w, h), (0, 0, 0, 80))
    mask = Image.new("L", (w, h), 0)
    mask_draw = ImageDraw.Draw(mask)
    # Oval beyaz alan (merkez aydınlık)
    mask_draw.ellipse([w // 6, h // 6, w - w // 6, h - h // 6], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=80))

    # Karartmayı uygula (maske tersine çevrilmiş)
    inverted_mask = Image.eval(mask, lambda x: 255 - x)
    image.paste(dark_layer, mask=inverted_mask)

    return image


def _apply_gradient_overlay(image: Image.Image) -> Image.Image:
    """Alt kısımda karartma gradienti — metin okunabilirliği için."""
    w, h = image.size
    gradient = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)

    # Alt %40 bölgeye gradient
    start_y = int(h * 0.5)
    for y in range(start_y, h):
        progress = (y - start_y) / (h - start_y)
        alpha = int(180 * progress)
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))

    image = Image.alpha_composite(image, gradient)
    return image


def _get_best_font(size: int = 80) -> ImageFont.FreeTypeFont:
    """Sistemde mevcut en iyi kalın fontu bul."""
    font_paths = [
        "C:/Windows/Fonts/impact.ttf",         # Impact — YouTube klasik
        "C:/Windows/Fonts/arialbd.ttf",         # Arial Bold
        "C:/Windows/Fonts/calibrib.ttf",        # Calibri Bold
        "C:/Windows/Fonts/verdanab.ttf",        # Verdana Bold
        "C:/Windows/Fonts/arial.ttf",           # Arial
    ]

    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue

    # Fallback: default font
    logger.warning("Kalın font bulunamadı, varsayılan kullanılıyor")
    return ImageFont.load_default()


def _prepare_headline(text: str) -> list[str]:
    """
    Headline metnini YouTube thumbnail'a uygun satırlara böl.
    Maks 2 satır, kelime başı büyük harf.
    """
    # Büyük harfe çevir
    text = text.upper()

    # Çok uzunsa kısalt
    words = text.split()
    if len(words) > 6:
        words = words[:6]
    text = " ".join(words)

    # 2 satıra böl
    if len(text) > 20:
        mid = len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        return [line1, line2]

    return [text]


def _calculate_y_offset(position: str, lines: list, font, draw) -> int:
    """Metin konumunu hesapla."""
    total_height = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        total_height += bbox[3] - bbox[1] + 10

    if position == "top":
        return 40
    elif position == "bottom":
        return 720 - total_height - 60
    else:  # center
        return (720 - total_height) // 2


def _draw_glow(draw, x, y, text, font, glow_color=(0, 0, 0), glow_size=6):
    """Metin etrafına glow (bulanık gölge) efekti."""
    for offset in range(glow_size, 0, -1):
        alpha = int(100 * (offset / glow_size))
        color = (*glow_color, alpha) if len(glow_color) == 3 else glow_color
        for dx in range(-offset, offset + 1):
            for dy in range(-offset, offset + 1):
                if dx * dx + dy * dy <= offset * offset:
                    draw.text((x + dx, y + dy), text, font=font,
                              fill=(glow_color[0], glow_color[1], glow_color[2], alpha))


def _draw_outline(draw, x, y, text, font, outline_color=(0, 0, 0), thickness=4):
    """Metin etrafına kalın outline çiz."""
    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if abs(dx) + abs(dy) > 0:
                draw.text((x + dx, y + dy), text, font=font,
                          fill=(*outline_color, 255))


def extract_thumbnail_headline(title: str) -> str:
    """
    Video başlığından thumbnail için 2-4 kelimelik şok headline çıkar.

    Örnekler:
    "What If Humans Could Breathe Underwater?" → "BREATHE UNDERWATER?!"
    "What Would Happen If Gravity Doubled?" → "GRAVITY DOUBLED?!"
    "What If The Sun Suddenly Went Out?" → "SUN WENT OUT?!"
    """
    # "What If" ve benzeri kalıpları temizle
    cleaners = [
        "what if ", "what would happen if ", "what happens when ",
        "what would happen when ", "what if the ", "what if a ",
        "what would ", "i simulated ",
    ]

    lower = title.lower().strip().rstrip("?").rstrip("!")
    for c in cleaners:
        if lower.startswith(c):
            lower = lower[len(c):]
            break

    # İlk 4 kelimeyi al
    words = lower.split()
    if len(words) > 4:
        words = words[:4]

    headline = " ".join(words).upper()

    # Soru/ünlem işareti ekle
    if "?" not in headline and "!" not in headline:
        headline += "?!"

    return headline


# Doğrudan test
if __name__ == "__main__":
    # Test
    test_title = "What If Humans Could Breathe Underwater?"
    headline = extract_thumbnail_headline(test_title)
    print(f"Title: {test_title}")
    print(f"Headline: {headline}")
