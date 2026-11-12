"""
doc_render.py - Belgesel bölüm render motoru (1440p, titremesiz Ken Burns).

Bir bölümü tek geçişte, tek bir x264 kodlamasıyla üretir:
- Arşiv görseli → 16:9 tuval (dikey görselde bulanık arka plan) → ortak renk tonu
- OpenCV warpAffine ile alt-piksel hassasiyetinde yakınlaşma/kaydırma
  (FFmpeg zoompan'ın tam sayı yuvarlamasından doğan titreme yok)
- Kenar karartması + film greni (önceden hesaplanmış maskelerle, kare başına ucuz)
- Çekimler arası çapraz geçiş veya düz kesme, bölüm başı/sonu siyaha geçiş
- Alt bant etiketleri (yer · tarih) ve "Temsili canlandırma" notu
- Video çekimleri (Remotion grafik kartı, yapay zekâ klibi) aynı zaman çizelgesinde

Ses burada yoktur; bölüm sesi son montajda eklenir. Çekim süreleri ses
zaman damgalarından gelir (doc_timeline), toplam süre sese eşittir.
"""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scripts.utils import logger

OUT_W, OUT_H = 2560, 1440
FPS = 30
# Tuval çıktıdan biraz büyük tutulur: %12'lik yakınlaşmada bile alt-örnekleme
# yapılır (keskin görüntü), büyütme yapılmaz.
CANVAS_SCALE = 1.25

FONTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
GOLD = (92, 164, 201)      # BGR — Remotion temasındaki #c9a45c
IVORY = (216, 234, 243)    # BGR — #f3ead8

MOVES = {
    #        zoom başı, zoom sonu, merkez kayması (dx, dy) tuval oranı
    "in":    (1.00, 1.12, (0.0, 0.0)),
    "out":   (1.12, 1.00, (0.0, 0.0)),
    "left":  (1.14, 1.14, (0.05, 0.0)),    # kamera sola: merkez sağdan sola
    "right": (1.14, 1.14, (-0.05, 0.0)),
    "up":    (1.14, 1.14, (0.0, 0.05)),
    "down":  (1.14, 1.14, (0.0, -0.05)),
    "still": (1.03, 1.06, (0.0, 0.0)),
}


# ─────────────────────────────────────────────
# Renk ve doku
# ─────────────────────────────────────────────

def _grade_luts() -> list[np.ndarray]:
    """Sıcak, hafif soluk "belgesel" tonu için kanal başına LUT (BGR)."""
    x = np.arange(256, dtype=np.float32) / 255.0
    curve = x + 0.12 * np.sin(2 * np.pi * x) * (0.5 - np.abs(x - 0.5))  # yumuşak S
    curve = 0.035 + curve * 0.93                                         # siyahı hafif kaldır
    gains = (0.93, 1.0, 1.04)                                            # B, G, R → sıcak
    luts = []
    for g in gains:
        lut = np.clip(curve * g * 255.0, 0, 255).astype(np.uint8)
        luts.append(lut)
    return luts


_LUTS = _grade_luts()


def grade(img: np.ndarray, saturation: float = 0.86) -> np.ndarray:
    """Ortak renk tonu: farklı kaynaklardan gelen görseller tek film gibi görünsün."""
    b, g, r = cv2.split(img)
    out = cv2.merge([cv2.LUT(b, _LUTS[0]), cv2.LUT(g, _LUTS[1]), cv2.LUT(r, _LUTS[2])])
    gray = cv2.cvtColor(cv2.cvtColor(out, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    return cv2.addWeighted(out, saturation, gray, 1.0 - saturation, 0)


class Look:
    """Kenar karartması + film greni; maskeler bir kez hesaplanır."""

    def __init__(self, w: int = OUT_W, h: int = OUT_H, vignette: float = 0.38,
                 grain: float = 5.0, grain_frames: int = 8, seed: int = 7):
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / np.sqrt(2)
        mask = 1.0 - vignette * np.clip(r, 0, 1) ** 2.2
        self.vig = cv2.merge([(mask * 255).astype(np.uint8)] * 3)
        rng = np.random.default_rng(seed)
        self.grain_pos, self.grain_neg = [], []
        for _ in range(grain_frames):
            # Gren yarım çözünürlükte üretilip büyütülür: daha organik tane
            n = rng.normal(0, grain, (h // 2, w // 2)).astype(np.float32)
            n = cv2.resize(n, (w, h), interpolation=cv2.INTER_LINEAR)
            n3 = cv2.merge([n] * 3)
            self.grain_pos.append(np.clip(n3, 0, 255).astype(np.uint8))
            self.grain_neg.append(np.clip(-n3, 0, 255).astype(np.uint8))

    def apply(self, frame: np.ndarray, n: int) -> np.ndarray:
        out = cv2.multiply(frame, self.vig, scale=1 / 255.0)
        k = n % len(self.grain_pos)
        out = cv2.add(out, self.grain_pos[k])
        return cv2.subtract(out, self.grain_neg[k])


# ─────────────────────────────────────────────
# Tuval (görsel → 16:9)
# ─────────────────────────────────────────────

def _read_image(path: str) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        # OpenCV'nin açamadığı biçimler (ör. bazı PNG/WebP) için Pillow
        img = cv2.cvtColor(np.array(Image.open(path).convert("RGB")), cv2.COLOR_RGB2BGR)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.shape[2] == 4:
        alpha = img[:, :, 3:4].astype(np.float32) / 255.0
        img = (img[:, :, :3].astype(np.float32) * alpha).astype(np.uint8)
    return img


def _cover(img: np.ndarray, w: int, h: int, focus=(0.5, 0.5)) -> np.ndarray:
    ih, iw = img.shape[:2]
    s = max(w / iw, h / ih)
    rw, rh = max(w, round(iw * s)), max(h, round(ih * s))
    interp = cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC
    big = cv2.resize(img, (rw, rh), interpolation=interp)
    x = int(np.clip(focus[0] * rw - w / 2, 0, rw - w))
    y = int(np.clip(focus[1] * rh - h / 2, 0, rh - h))
    return big[y:y + h, x:x + w]


def build_canvas(path: str, focus=(0.5, 0.5), fit: str = "auto") -> np.ndarray:
    """
    Görseli hareket için 16:9 tuvale yerleştir ve renk tonunu uygula.

    fit="cover": 16:9'a kırp (yatay görseller). fit="contain": görselin tamamı,
    boşluklar aynı görselin bulanık/karartılmış haliyle dolar (dikey eserler,
    tabletler, haritalar). "auto": en-boy oranı 1.45'in altındaysa contain.
    """
    img = _read_image(path)
    cw, ch = int(OUT_W * CANVAS_SCALE), int(OUT_H * CANVAS_SCALE)
    ih, iw = img.shape[:2]
    if fit == "auto":
        fit = "cover" if iw / ih >= 1.45 else "contain"
    if fit == "cover":
        canvas = _cover(img, cw, ch, focus)
    else:
        bg = _cover(img, cw // 8, ch // 8)
        bg = cv2.GaussianBlur(bg, (0, 0), 6)
        bg = cv2.resize(bg, (cw, ch), interpolation=cv2.INTER_CUBIC)
        bg = cv2.convertScaleAbs(bg, alpha=0.42)
        s = min(cw * 0.94 / iw, ch * 0.94 / ih)
        fw, fh = round(iw * s), round(ih * s)
        interp = cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC
        fg = cv2.resize(img, (fw, fh), interpolation=interp)
        x, y = (cw - fw) // 2, (ch - fh) // 2
        # Yumuşak gölge: görsel arka plandan "kalksın"
        shadow = np.zeros((ch, cw), np.float32)
        off = max(cw // 200, 6)
        shadow[y + off:y + fh + off, x + off:x + fw + off] = 1.0
        shadow = cv2.GaussianBlur(shadow, (0, 0), cw / 120)
        bg = (bg.astype(np.float32) * (1 - 0.6 * shadow[:, :, None])).astype(np.uint8)
        bg[y:y + fh, x:x + fw] = fg
        canvas = bg
    return grade(canvas)


# ─────────────────────────────────────────────
# Grafik bindirmeleri (Pillow → BGRA)
# ─────────────────────────────────────────────

def _font(name: str, size: int, variation: str) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONTS_DIR / name), size)
    try:
        f.set_variation_by_name(variation)
    except (OSError, ValueError):
        pass
    return f


def tr_upper(text: str) -> str:
    """Türkçe büyük harf: i→İ, ı→I (Cinzel küçük harfi büyük biçimde çizer)."""
    return text.replace("i", "İ").replace("ı", "I").upper()


def render_label(title: str, subtitle: str = "") -> tuple[np.ndarray, tuple[int, int]]:
    """Alt bant: altın çizgi + yer adı (Cinzel) + tarih/açıklama. (BGRA, (x, y))"""
    title = tr_upper(title)
    f_title = _font("Cinzel.ttf", 64, "Bold")
    f_sub = _font("SourceSans3.ttf", 40, "Regular")
    pad = 40
    tw = int(f_title.getlength(title))
    sw = int(f_sub.getlength(subtitle)) if subtitle else 0
    w = max(tw, sw, 160) + 2 * pad + 120
    h = 230 if subtitle else 170
    # Okunurluk için sola doğru yoğunlaşan yumuşak koyu zemin
    horiz = (1 - np.arange(w) / w) ** 1.5
    yy = np.arange(h) / (h - 1)
    vert = np.clip(np.minimum(yy, 1 - yy) / 0.3, 0, 1) ** 0.8   # üst/alt kenar yumuşak
    alpha = (150 * np.outer(vert, horiz)).astype(np.uint8)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    im.putalpha(Image.fromarray(alpha))
    d = ImageDraw.Draw(im)
    d.rectangle([pad, 34, pad + 110, 38], fill=(201, 164, 92, 255))
    d.text((pad, 52), title, font=f_title, fill=(243, 234, 216, 255))
    if subtitle:
        d.text((pad + 2, 140), subtitle, font=f_sub, fill=(216, 204, 180, 235))
    arr = cv2.cvtColor(np.array(im), cv2.COLOR_RGBA2BGRA)
    return arr, (110, OUT_H - h - 120)


def render_note(text: str) -> tuple[np.ndarray, tuple[int, int]]:
    """Sağ üst küçük not (ör. "Temsili canlandırma")."""
    f = _font("SourceSans3.ttf", 34, "Medium")
    w, h = int(f.getlength(text)) + 48, 64
    im = Image.new("RGBA", (w, h), (0, 0, 0, 110))
    ImageDraw.Draw(im).text((24, 12), text, font=f, fill=(243, 234, 216, 230))
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGBA2BGRA), (OUT_W - w - 80, 70)


def composite(frame: np.ndarray, overlay: np.ndarray, pos: tuple[int, int], opacity: float):
    """BGRA bindirmeyi karenin ilgili bölgesine (yerinde) karıştır."""
    if opacity <= 0:
        return
    x, y = pos
    oh, ow = overlay.shape[:2]
    roi = frame[y:y + oh, x:x + ow]
    a = overlay[:, :, 3:4].astype(np.float32) / 255.0 * opacity
    roi[:] = (overlay[:, :, :3].astype(np.float32) * a + roi.astype(np.float32) * (1 - a)).astype(np.uint8)


def _envelope(t: float, duration: float, fade_in=(0.4, 0.9), end_gap=0.3, fade_out=0.5) -> float:
    """Bindirme görünürlüğü: gir, kal, çık (yerel çekim zamanına göre).

    Kısa çekimlerde de okunabilsin diye erken girer, kesmeden hemen önce çıkar.
    """
    a, b = fade_in
    up = np.clip((t - a) / (b - a), 0, 1)
    down = np.clip((duration - end_gap - t) / fade_out, 0, 1)
    return float(min(up, down))


# ─────────────────────────────────────────────
# Çekimler
# ─────────────────────────────────────────────

@dataclass
class Shot:
    """Zaman çizelgesindeki bir çekim. kind: "image" | "video"."""
    kind: str
    path: str
    duration: float
    move: str = "in"
    focus: tuple = (0.5, 0.5)
    fit: str = "auto"
    transition: str = "dissolve"     # bu çekime GİRİŞ: "dissolve" | "cut" | "black" | "flash"
    xfade: float = 0.0               # geçiş süresi (0: türün varsayılanı)
    label: dict | None = None        # {"title": ..., "subtitle": ...}
    note: str = ""                   # sağ üst not
    grade: bool = True               # video çekimlerinde renk tonu (grafik kartlarında kapalı)
    start: float = 0.0               # video çekimi: kaynakta başlangıç saniyesi (film kesiti)
    overlay: str = ""                # atmosfer katmanı videosu (toz, sis, kıvılcım…)
    overlay_opacity: float = 0.55
    sfx: bool = False                # videonun kendi sesi doğal ses izine eklenir (birleştirmede)
    flip: bool = False               # yatay ayna: ekran yönü kuralı (ordu soldan sağa vb.)
    speed: float = 0.0               # sabit hız (ör. 0.8 ağır çekim); 0: gerekirse otomatik yavaşlat
    match: float = 0.0               # ton eşitleme gücü 0..1 (farklı kliplerin parlaklık/kontrastı)
    _state: dict = field(default_factory=dict, repr=False)


def probe_duration(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                         capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def screen_blend(base: np.ndarray, layer: np.ndarray, opacity: float) -> np.ndarray:
    """"Screen" karışımı: katmanın parlak kısımları (toz, kıvılcım) tabana eklenir, siyahı kaybolur."""
    layer = cv2.convertScaleAbs(layer, alpha=opacity)
    inv = cv2.multiply(cv2.bitwise_not(base), cv2.bitwise_not(layer), scale=1 / 255.0)
    return cv2.bitwise_not(inv)


class AtmosSource:
    """Bir çekim kaynağının üstüne döngülü atmosfer katmanı bindirir."""

    def __init__(self, base, shot: Shot):
        self.base = base
        self.layer = VideoSource(Shot("video", shot.overlay, 0), loop=True, do_grade=False)
        self.opacity = shot.overlay_opacity

    def frame(self, t: float) -> np.ndarray:
        return screen_blend(self.base.frame(t), self.layer.frame(t), self.opacity)

    def close(self):
        self.layer.close()
        if isinstance(self.base, VideoSource):
            self.base.close()


class ImageSource:
    def __init__(self, shot: Shot, span: float, canvas_cache: dict):
        key = (shot.path, tuple(shot.focus), shot.fit)
        if key not in canvas_cache:
            canvas_cache[key] = build_canvas(shot.path, shot.focus, shot.fit)
        self.canvas = canvas_cache[key]
        self.span = max(span, 1e-3)
        self.z0, self.z1, (dx, dy) = MOVES.get(shot.move, MOVES["in"])
        fx, fy = shot.focus
        # Kaydırma yolu (başlangıç → bitiş merkezi, tuval oranı) görünür alanın
        # izin verdiği aralığa sığdırılır: yol kısaltılmaz, bütün halde kaydırılır.
        # Aksi halde kenara yakın odakta merkez sınıra yapışır ve hareket kaybolur.
        zmin = min(self.z0, self.z1)
        half = (1 - 1 / zmin) / 2          # merkezin 0.5'ten en fazla sapması
        self.path = []
        for f, d in ((fx, dx), (fy, dy)):
            a, b = f + d, f - d
            d = min(abs(d), half)          # yol izin verilenden uzunsa kısalt
            a, b = (f + d, f - d) if a >= b else (f - d, f + d)
            lo, hi = 0.5 - half, 0.5 + half
            shift = max(lo - min(a, b), 0) - max(max(a, b) - hi, 0)
            self.path.append((a + shift, b + shift))

    def frame(self, t: float) -> np.ndarray:
        ch, cw = self.canvas.shape[:2]
        p = float(np.clip(t / self.span, 0, 1))
        z = self.z0 + (self.z1 - self.z0) * p
        vw, vh = cw / z, ch / z
        (ax, bx), (ay, by) = self.path
        cx = float(np.clip((ax + (bx - ax) * p) * cw, vw / 2, cw - vw / 2))
        cy = float(np.clip((ay + (by - ay) * p) * ch, vh / 2, ch - vh / 2))
        s = OUT_W / vw
        m = np.float32([[s, 0, OUT_W / 2 - s * cx], [0, s, OUT_H / 2 - s * cy]])
        return cv2.warpAffine(self.canvas, m, (OUT_W, OUT_H), flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_REFLECT)


# Sinematik hedef: orta-koyu ortalama, belirgin ama sert olmayan kontrast
TONE_TARGET = (100.0, 52.0)   # gri düzey ortalaması, standart sapması (0-255)


def tone_params(path: str, start: float = 0.0, strength: float = 0.5,
                samples: int = 6) -> tuple[float, float] | None:
    """
    Klibin genel parlaklık/kontrastını hedefe yaklaştıran sabit (kazanç, kayma).
    Kare kare değil klip başına hesaplanır: titreme olmaz. strength=1 tam eşitler,
    0.5 yarı yola getirir (gece sahnesi yine karanlık kalır, ama "başka film" gibi durmaz).
    """
    dur = probe_duration(path) - start
    if dur <= 0:
        return None
    fps = samples / dur
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", str(path),
                          "-vf", f"fps={fps:.5f},scale=320:-2,format=gray", "-frames:v", str(samples),
                          "-f", "rawvideo", "-"], capture_output=True)
    px = np.frombuffer(out.stdout, np.uint8).astype(np.float32)
    if px.size < 100:
        return None
    mean, std = float(px.mean()), max(float(px.std()), 1.0)
    tm, ts = TONE_TARGET
    gain = float(np.clip((ts / std) ** strength, 0.8, 1.25))
    new_mean = mean + strength * (tm - mean)
    beta = float(np.clip(new_mean - gain * mean, -30, 30))
    return gain, beta


def effective_speed(path: str, start: float, span: float, speed: float = 0.0) -> float:
    """Oynatma hızı: istenen hız (yoksa 1); kaynak yetmezse en fazla %40 yavaşlatılır."""
    speed = speed or 1.0
    available = probe_duration(path) - start
    if 0 < available < span * speed:
        speed = max(available / span, 0.6)
    return speed


class VideoSource:
    """
    Klibi 1440p'ye ölçekleyip sırayla okur.

    start: kaynakta başlangıç saniyesi (uzun filmden kesit). Kaynak çekimden
    kısaysa en fazla %40 yavaşlatılır; yine yetmezse son kare donar.
    loop: atmosfer katmanları gibi kısa döngülerin sonsuz tekrarı.
    """

    def __init__(self, shot: Shot, span: float = 0.0, loop: bool = False, do_grade: bool | None = None):
        self.shot = shot
        self.do_grade = shot.grade if do_grade is None else do_grade
        speed = effective_speed(shot.path, shot.start, span, shot.speed) if span and not loop else 1.0
        self.speed = speed
        flip = "hflip," if shot.flip else ""
        self.tone = tone_params(shot.path, shot.start, shot.match) if shot.match and not loop else None
        vf = (f"setpts=PTS/{speed:.4f},{flip}"
              f"scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase:flags=lanczos,"
              f"crop={OUT_W}:{OUT_H},fps={FPS}")
        cmd = ["ffmpeg", "-loglevel", "error"]
        if loop:
            cmd += ["-stream_loop", "-1"]
        if shot.start:
            cmd += ["-ss", f"{shot.start:.3f}"]
        cmd += ["-i", shot.path, "-an", "-vf", vf, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        self.pos = -1
        self.last = np.zeros((OUT_H, OUT_W, 3), np.uint8)
        self.ended = False

    def frame(self, t: float) -> np.ndarray:
        want = int(round(max(t, 0) * FPS))
        size = OUT_W * OUT_H * 3
        while self.pos < want and not self.ended:
            buf = self.proc.stdout.read(size)
            if len(buf) < size:
                self.ended = True
                break
            frame = np.frombuffer(buf, np.uint8).reshape(OUT_H, OUT_W, 3)
            if self.tone:
                frame = cv2.convertScaleAbs(frame, alpha=self.tone[0], beta=self.tone[1])
            self.last = grade(frame) if self.do_grade else frame.copy()
            self.pos += 1
        return self.last

    def close(self):
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait()


# ─────────────────────────────────────────────
# Bölüm render'ı
# ─────────────────────────────────────────────

# Geçiş türleri (çekime giriş):
#   cut      düz kesme: aynı sahnede, aksiyon devam ederken (sinemanın temel dili)
#   dissolve çapraz geçiş: zaman/mekân atlaması, sakin anlatım
#   black    siyaha inip açılma: bölüm içi büyük sahne değişimi, "aradan yıllar geçti"
#   flash    beyaz parlama + kesme: top atışı, darbe anı
TRANSITION_DEFAULTS = {"dissolve": 0.5, "black": 1.2, "flash": 0.4}
WHITE = None


def _transition(frame, i, t, starts, trans, tlen, shot_frame, n):
    """Sınırın iki yanındaki geçiş efektini uygula (çekim i'nin karesi üzerinde)."""
    global WHITE
    s0 = starts[i]
    L = tlen[i]
    if i > 0 and L:
        if trans[i] == "dissolve" and t < s0 + L / 2:
            a = 0.5 + (t - s0) / L
            frame = cv2.addWeighted(frame, a, shot_frame(i - 1, t), 1 - a, 0)
        elif trans[i] == "black" and t < s0 + L / 2:
            frame = cv2.convertScaleAbs(frame, alpha=float(np.clip((t - s0) / (L / 2), 0, 1)))
        elif trans[i] == "flash" and t < s0 + L:
            if WHITE is None or WHITE.shape != frame.shape:
                WHITE = np.full(frame.shape, 255, np.uint8)
            w = 0.85 * (1 - (t - s0) / L) ** 2
            frame = cv2.addWeighted(frame, 1 - w, WHITE, w, 0)
    if i < n - 1:
        s1, L1 = starts[i + 1], tlen[i + 1]
        if L1 and trans[i + 1] == "dissolve" and t >= s1 - L1 / 2:
            a = 0.5 - (s1 - t) / L1
            frame = cv2.addWeighted(shot_frame(i + 1, t), a, frame, 1 - a, 0)
        elif L1 and trans[i + 1] == "black" and t >= s1 - L1 / 2:
            frame = cv2.convertScaleAbs(frame, alpha=float(np.clip((s1 - t) / (L1 / 2), 0, 1)))
    return frame


def render_chapter(shots: list[Shot], out_path: str, xfade: float = 0.5,
                   fade_in: float = 0.6, fade_out: float = 0.8,
                   crf: int = 18, preset: str = "veryfast", maxrate: str = "20M",
                   look: Look | None = None) -> str:
    """
    Çekimleri tek videoya render et. Toplam süre = çekim sürelerinin toplamı
    (çapraz geçiş sınırın iki yanına yarı yarıya taşar, süreyi kısaltmaz).
    """
    if not shots:
        raise ValueError("Çekim listesi boş")
    look = look or Look()
    starts = np.cumsum([0.0] + [s.duration for s in shots])
    total = float(starts[-1])
    n_frames = int(round(total * FPS))
    # Her sınırın geçiş türü ve süresi (çekim i'ye giriş). Çapraz geçişte iki
    # kaynak üst üste biner, bu yüzden kaynak geçiş payının yarısı kadar önce başlar.
    trans = [shots[i].transition if i else "cut" for i in range(len(shots))]
    tlen = []
    for i, sh in enumerate(shots):
        if trans[i] == "cut":
            L = 0.0
        else:
            L = sh.xfade or (xfade if trans[i] == "dissolve" else TRANSITION_DEFAULTS.get(trans[i], xfade))
        if i:   # geçiş, iki komşu çekimden kısasından uzun olamaz
            L = min(L, sh.duration, shots[i - 1].duration)
        tlen.append(L)
    lead = [tlen[i] / 2 if trans[i] == "dissolve" else 0.0 for i in range(len(shots))]
    tail = lead[1:] + [0.0]
    canvas_cache: dict = {}
    sources: dict[int, object] = {}
    overlays: dict[int, list] = {}

    def source(i: int):
        if i not in sources:
            s = shots[i]
            span = s.duration + lead[i] + tail[i]
            src = VideoSource(s, span) if s.kind == "video" else ImageSource(s, span, canvas_cache)
            sources[i] = AtmosSource(src, s) if s.overlay else src
            ov = []
            if s.label:
                ov.append(render_label(s.label.get("title", ""), s.label.get("subtitle", "")))
            if s.note:
                ov.append(render_note(s.note))
            overlays[i] = ov
        return sources[i]

    def release(i: int):
        src = sources.pop(i, None)
        if isinstance(src, (VideoSource, AtmosSource)):
            src.close()
        if isinstance(src, AtmosSource):
            src = src.base
        overlays.pop(i, None)
        if isinstance(src, ImageSource):
            # Aynı görsel sonraki çekimlerde yoksa tuvali bellekten at
            key = (shots[i].path, tuple(shots[i].focus), shots[i].fit)
            if not any((s.path, tuple(s.focus), s.fit) == key for s in shots[i + 1:]):
                canvas_cache.pop(key, None)

    def shot_frame(i: int, t_global: float) -> np.ndarray:
        local = t_global - starts[i]          # çekim başlangıcına göre
        frame = source(i).frame(local + lead[i])  # kaynak, geçiş payı kadar önce başlar
        return frame

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
         "-s", f"{OUT_W}x{OUT_H}", "-r", str(FPS), "-i", "-",
         # Gren sıkıştırmayı zorlar: bit hızı YouTube'un 1440p önerisi düzeyinde
         # sınırlanır (35 dk ≈ 5 GB). "veryfast": 2 çekirdekte 35 dk ≈ 2,5 saat.
         "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
         "-maxrate", maxrate, "-bufsize", "40M",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_path)],
        stdin=subprocess.PIPE)
    i = 0
    try:
        for n in range(n_frames):
            t = n / FPS
            while i < len(shots) - 1 and t >= starts[i + 1]:
                release(i - 1) if i > 0 else None
                i += 1
            frame = shot_frame(i, t).copy()
            frame = _transition(frame, i, t, starts, trans, tlen, shot_frame, len(shots))
            frame = look.apply(frame, n)
            local = t - starts[i]
            for ov, pos in overlays.get(i, []):
                composite(frame, ov, pos, _envelope(local, shots[i].duration))
            # Bölüm başı/sonu siyaha geçiş
            k = min(1.0, t / fade_in if fade_in else 1.0, (total - t) / fade_out if fade_out else 1.0)
            if k < 1.0:
                frame = cv2.convertScaleAbs(frame, alpha=max(k, 0.0))
            enc.stdin.write(frame.tobytes())
    finally:
        enc.stdin.close()
        enc.wait()
        for j in list(sources):
            release(j)
    if enc.returncode != 0:
        raise RuntimeError(f"x264 kodlama hatası: {out_path}")
    logger.info("Bölüm render edildi: %s (%d çekim, %.1f sn)", out_path, len(shots), total)
    return str(out_path)
