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

        # Metni canvas'a göre otomatik boyutlandır — her zaman DEV ve okunaklı,
        # asla taşmaz (sabit 90px önceden hem çok küçük hem taşabiliyordu)
        margin = 60
        max_text_width = 1280 - 2 * margin
        font, lines = _fit_headline(draw, headline_text, max_width=max_text_width)

        # Metin konumunu hesapla
        y_offset = _calculate_y_offset(text_position, lines, font, draw)

        # Okunabilirlik için metin bloğunun arkasına yarı saydam koyu panel
        _draw_text_backdrop(txt_layer, draw, lines, font, y_offset, margin=margin)

        # Her satır için glow + outline + text çiz
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (1280 - text_width) // 2

            # 1. Glow efekti (büyük bulanık gölge)
            _draw_glow(draw, x, y_offset, line, font, glow_color=(0, 0, 0), glow_size=10)

            # 2. Kalın outline (siyah kenar)
            _draw_outline(draw, x, y_offset, line, font, outline_color=(0, 0, 0), thickness=7)

            # 3. Ana metin (parlak renk)
            draw.text((x, y_offset), line, font=font, fill=accent_color)

            line_height = bbox[3] - bbox[1]
            y_offset += line_height + 14

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
    """
    Sistemde mevcut en iyi kalın fontu bul.

    Üretim ortamı Linux (GitHub Actions) — bu yollar ÖNCE denenir. Daha önce
    yalnızca Windows yolları vardı; Linux'ta hiçbiri bulunamayıp PIL'in
    ölçeklenmeyen minik varsayılan bitmap fontuna sessizce düşülüyordu (bu
    yüzden thumbnail yazısı görünmez kadar küçük çıkıyordu).
    """
    font_paths = [
        # Linux (CI/production)
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        # Windows (yerel geliştirme)
        "C:/Windows/Fonts/impact.ttf",         # Impact — YouTube klasik
        "C:/Windows/Fonts/arialbd.ttf",         # Arial Bold
        "C:/Windows/Fonts/calibrib.ttf",        # Calibri Bold
        "C:/Windows/Fonts/verdanab.ttf",        # Verdana Bold
        "C:/Windows/Fonts/arial.ttf",           # Arial
        # macOS (yerel geliştirme)
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]

    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue

    # Son çare: ölçeklenebilir varsayılan (Pillow ≥10.1); yoksa sabit boyutlu bitmap
    logger.warning("Kalın TrueType font bulunamadı, varsayılan kullanılıyor")
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _wrap_words(words: list[str], n_lines: int) -> list[str]:
    """Kelime listesini n_lines satıra olabildiğince eşit böl."""
    if n_lines <= 1 or len(words) <= 1:
        return [" ".join(words)]
    per_line = -(-len(words) // n_lines)  # yukarı yuvarlama
    lines = []
    for i in range(0, len(words), per_line):
        lines.append(" ".join(words[i:i + per_line]))
    return lines


def _fit_headline(
    draw, text: str, max_width: int,
    max_lines: int = 2, max_size: int = 170, min_size: int = 60,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """
    Headline'ı canvas'a göre EN BÜYÜK okunaklı boyutta, taşmadan yerleştir.

    Önceden font boyutu sabit 90px'ti — hem çok küçük kalabiliyor (uzun
    metinde taşma riski hiç kontrol edilmiyordu) hem de kısa metinde
    gereksiz küçük duruyordu. Burada büyükten küçüğe deneyerek canvas
    genişliğine sığan en büyük boyut seçilir — çarpıcı, dev, pro görünüm.
    """
    text = text.upper().strip()
    words = text.split()
    if len(words) > 6:
        words = words[:6]

    for size in range(max_size, min_size - 1, -6):
        font = _get_best_font(size)
        for n_lines in (1, 2) if max_lines >= 2 else (1,):
            lines = _wrap_words(words, n_lines)
            widest = max(
                draw.textbbox((0, 0), line, font=font)[2] for line in lines
            )
            if widest <= max_width:
                return font, lines

    # Son çare: minimum boyutta iki satıra böl (yine de taşarsa en azından
    # en küçük fontla en okunaklı hali budur)
    font = _get_best_font(min_size)
    return font, _wrap_words(words, min(2, max_lines))


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


def _draw_text_backdrop(layer, draw, lines, font, y_offset, margin=60):
    """
    Metin bloğunun arkasına yarı saydam koyu bir panel çizer.

    Parlak/karışık arka planlarda dahi yazının okunaklılığını garanti eder —
    büyük kanalların "pro" thumbnail'lerinde standart bir teknik. Panel
    ayrıca Gaussian blur ile yumuşatılıp doğal bir vinyet gibi görünür.
    """
    if not lines:
        return
    widest = max(draw.textbbox((0, 0), line, font=font)[2] for line in lines)
    total_height = sum(
        draw.textbbox((0, 0), line, font=font)[3] + 14 for line in lines
    )
    pad_x, pad_y = 36, 22
    x0 = (1280 - widest) // 2 - pad_x
    x1 = (1280 + widest) // 2 + pad_x
    y0 = y_offset - pad_y
    y1 = y_offset + total_height + pad_y

    panel = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    panel_draw = ImageDraw.Draw(panel)
    panel_draw.rounded_rectangle([x0, y0, x1, y1], radius=24, fill=(0, 0, 0, 130))
    panel = panel.filter(ImageFilter.GaussianBlur(radius=2))
    layer.alpha_composite(panel)


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

    # Parantezli ek kanca varsa ("...? (It's worse than you think)") önce onu at —
    # aksi halde kelime bazlı kesme parantezin ortasında durup "(IT'S" gibi
    # yarım/çirkin bir headline üretiyordu.
    title = title.split("(")[0].strip()

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
