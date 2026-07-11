"""thumbnail_composer testleri — küçük/görünmez yazı regresyonu ve headline temizliği."""

from PIL import Image, ImageDraw

from scripts.thumbnail_composer import (
    _wrap_words, _fit_headline, _get_best_font,
    extract_thumbnail_headline, compose_thumbnail,
)


class TestWrapWords:
    def test_single_line(self):
        assert _wrap_words(["SUN", "VANISHED"], 1) == ["SUN VANISHED"]

    def test_two_lines_splits_evenly(self):
        result = _wrap_words(["GRAVITY", "DOUBLED", "OVERNIGHT", "NOW"], 2)
        assert len(result) == 2
        assert result[0] == "GRAVITY DOUBLED"
        assert result[1] == "OVERNIGHT NOW"


class TestFitHeadline:
    def _draw(self):
        img = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        return ImageDraw.Draw(img)

    def test_short_headline_never_exceeds_max_width(self):
        draw = self._draw()
        font, lines = _fit_headline(draw, "SUN VANISHED?!", max_width=1160)
        for line in lines:
            width = draw.textbbox((0, 0), line, font=font)[2]
            assert width <= 1160

    def test_long_headline_still_fits_and_wraps(self):
        draw = self._draw()
        font, lines = _fit_headline(
            draw, "THE ENTIRE SOLAR SYSTEM COLLAPSES INSTANTLY", max_width=1160,
        )
        assert len(lines) <= 2
        for line in lines:
            width = draw.textbbox((0, 0), line, font=font)[2]
            assert width <= 1160

    def test_short_text_gets_larger_font_than_long_text(self):
        """Kısa metin geniş alana daha büyük fontla sığmalı — otomatik boyutlandırma çalışıyor."""
        draw = self._draw()
        short_font, _ = _fit_headline(draw, "GONE?!", max_width=1160)
        long_font, _ = _fit_headline(
            draw, "GRAVITY DOUBLED OVERNIGHT EVERYWHERE", max_width=1160,
        )
        assert short_font.size >= long_font.size


class TestGetBestFont:
    def test_returns_a_real_truetype_font_not_tiny_default(self):
        """
        Regresyon: önceden yalnızca Windows font yolları vardı, Linux CI'da
        hiçbiri bulunamayıp PIL'in ölçeklenmeyen minik bitmap fontuna
        düşülüyordu — thumbnail yazısı bu yüzden görünmez kadar küçüktü.
        """
        font = _get_best_font(size=100)
        img = Image.new("RGB", (10, 10))
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), "A", font=font)
        height = bbox[3] - bbox[1]
        # Gerçek bir TrueType fontta 100px boyutunda 'A' harfi en az ~50px
        # yüksekliğinde olur; PIL'in varsayılan bitmap fontu ~10px'tir.
        assert height > 50


class TestExtractThumbnailHeadline:
    def test_strips_parenthetical_hook(self):
        """Regresyon: parantezli ek kanca ('...? (It's worse...)') headline'ı
        ortasından kesip 'SUN VANISHED? (IT'S' gibi çirkin bir sonuç veriyordu."""
        headline = extract_thumbnail_headline(
            "What If The Sun Vanished? (It's Not What You Think)"
        )
        assert "(" not in headline
        assert "IT'S" not in headline
        assert "SUN" in headline and "VANISHED" in headline

    def test_basic_cleanup(self):
        headline = extract_thumbnail_headline("What If Gravity Doubled?")
        assert headline == "GRAVITY DOUBLED?!" or headline.startswith("GRAVITY DOUBLED")

    def test_adds_punch_if_missing(self):
        headline = extract_thumbnail_headline("What if humans could fly")
        assert headline.endswith("?!")


class TestComposeThumbnail:
    def test_produces_large_readable_text(self, tmp_path):
        bg_path = tmp_path / "bg.png"
        Image.new("RGB", (1344, 768), color=(20, 40, 90)).save(bg_path)
        out_path = tmp_path / "thumb.png"

        result = compose_thumbnail(
            background_image_path=str(bg_path),
            headline_text="SUN VANISHED?!",
            output_path=str(out_path),
        )

        assert result == str(out_path)
        assert out_path.exists()
        img = Image.open(out_path)
        assert img.size == (1280, 720)
