"""
utils.py - Yardımcı fonksiyonlar ve ortak araçlar.

İçerir:
- Dizin yönetimi
- Env / prompt yükleme
- JSON I/O
- Rich terminal çıktıları
- Retry (exponential backoff) dekoratörü
- Checkpoint / resume sistemi
- Dosyaya loglama
"""

import os
import json
import time
import shutil
import logging
import functools
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# ──────────────────────────────────────
# Rich Console
# ──────────────────────────────────────
console = Console()

# ──────────────────────────────────────
# Proje Dizin Yapısı
# ──────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent

TEMP_DIR = PROJECT_ROOT / "temp"
AUDIO_DIR = TEMP_DIR / "audio"
IMAGES_DIR = TEMP_DIR / "images"
CLIPS_DIR = TEMP_DIR / "clips"
OUTPUT_DIR = PROJECT_ROOT / "output"
CHARACTER_DIR = PROJECT_ROOT / "character" / "reference"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
ASSETS_DIR = PROJECT_ROOT / "assets" / "music"
LOGS_DIR = PROJECT_ROOT / "logs"
THUMBNAILS_DIR = TEMP_DIR / "thumbnails"

# Checkpoint dosya yolu
CHECKPOINT_FILE = TEMP_DIR / "pipeline_checkpoint.json"


# ──────────────────────────────────────
# Dosya Loglama Sistemi
# ──────────────────────────────────────
def setup_logger(name: str = "whatif") -> logging.Logger:
    """Hem dosyaya hem terminale yazan logger oluştur."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    # Birden fazla handler eklenmesini önle
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Dosya handler — detaylı log
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(
        LOGS_DIR / f"pipeline_{timestamp}.log",
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger


# Global logger
logger = setup_logger()


# ──────────────────────────────────────
# Env ve Prompt Yükleme
# ──────────────────────────────────────
def load_env() -> dict:
    """API anahtarlarını .env dosyasından yükle."""
    env_path = PROJECT_ROOT / ".env"
    load_dotenv(env_path)

    keys = {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
        "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY", ""),
        "CHARACTER_VOICE_ID": os.getenv("CHARACTER_VOICE_ID", ""),
        "REPLICATE_API_TOKEN": os.getenv("REPLICATE_API_TOKEN", ""),
    }

    logger.info("Env yüklendi — key durumları: %s",
                {k: ("✓ SET" if v and "buraya" not in v else "✗ MISSING") for k, v in keys.items()})

    return keys


def read_prompt(filename: str) -> str:
    """prompts/ klasöründen prompt dosyası oku."""
    filepath = PROMPTS_DIR / filename
    if not filepath.exists():
        console.print(f"[red]✗[/red] Prompt dosyası bulunamadı: {filename}")
        logger.error("Prompt dosyası bulunamadı: %s", filepath)
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()
    logger.debug("Prompt yüklendi: %s (%d karakter)", filename, len(content))
    return content


# ──────────────────────────────────────
# Dizin Yönetimi
# ──────────────────────────────────────
def ensure_directories():
    """Gerekli tüm klasörleri oluştur."""
    dirs = [TEMP_DIR, AUDIO_DIR, IMAGES_DIR, CLIPS_DIR,
            OUTPUT_DIR, CHARACTER_DIR, PROMPTS_DIR, ASSETS_DIR,
            LOGS_DIR, THUMBNAILS_DIR]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    console.print("[green]✓[/green] Tüm dizinler hazır.")
    logger.info("Dizin yapısı doğrulandı.")


def clean_temp():
    """Geçici dosyaları temizle (checkpoint hariç)."""
    for subdir in [AUDIO_DIR, IMAGES_DIR, CLIPS_DIR, THUMBNAILS_DIR]:
        if subdir.exists():
            shutil.rmtree(subdir)
            subdir.mkdir(parents=True, exist_ok=True)
    console.print("[green]✓[/green] Geçici dosyalar temizlendi.")
    logger.info("Temp dizinleri temizlendi (checkpoint korundu).")


# ──────────────────────────────────────
# JSON I/O
# ──────────────────────────────────────
def save_json(data: dict, filepath: Path):
    """JSON dosyasına kaydet."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    console.print(f"[green]✓[/green] JSON kaydedildi: {filepath.name}")
    logger.info("JSON kaydedildi: %s", filepath)


def load_json(filepath: Path) -> dict:
    """JSON dosyasından oku."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────────────────
# Terminal Çıktıları
# ──────────────────────────────────────
def print_header(title: str):
    """Güzel başlık yazdır."""
    console.print()
    console.print(Panel(f"[bold cyan]{title}[/bold cyan]",
                        border_style="bright_blue"))
    logger.info("═" * 40)
    logger.info(title)
    logger.info("═" * 40)


def print_step(step_num: int, description: str):
    """Adım bilgisi yazdır."""
    console.print(f"\n[bold yellow]▶ Adım {step_num}:[/bold yellow] {description}")
    logger.info("▶ Adım %d: %s", step_num, description)


def print_success(message: str):
    """Başarı mesajı yazdır."""
    console.print(f"[bold green]✓ {message}[/bold green]")
    logger.info("✓ %s", message)


def print_error(message: str):
    """Hata mesajı yazdır."""
    console.print(f"[bold red]✗ {message}[/bold red]")
    logger.error("✗ %s", message)


def print_warning(message: str):
    """Uyarı mesajı yazdır."""
    console.print(f"[bold yellow]⚠ {message}[/bold yellow]")
    logger.warning("⚠ %s", message)


# ──────────────────────────────────────
# Episode Numarası
# ──────────────────────────────────────
def get_episode_number(prefix: str = "episode") -> int:
    """output/ klasöründeki son bölüm numarasını bul ve bir sonrakini döndür.

    Args:
        prefix: Dosya öneki — "episode" (uzun video) veya "short" (Shorts)
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    existing = list(OUTPUT_DIR.glob(f"{prefix}_*.mp4"))
    if not existing:
        return 1
    numbers = []
    for f in existing:
        try:
            num = int(f.stem.split("_")[1])
            numbers.append(num)
        except (IndexError, ValueError):
            continue
    return max(numbers, default=0) + 1


# ──────────────────────────────────────
# Retry Mekanizması (Exponential Backoff)
# ──────────────────────────────────────
def retry(
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
    on_retry=None,
):
    """
    Exponential backoff ile retry dekoratörü.

    Args:
        max_retries: Maksimum deneme sayısı
        base_delay: İlk bekleme süresi (saniye)
        max_delay: Maksimum bekleme süresi
        exceptions: Yakalanacak exception türleri
        on_retry: Her retry'da çağrılacak callback(attempt, exception, delay)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            "Fonksiyon %s %d denemeden sonra başarısız: %s",
                            func.__name__, max_retries, e
                        )
                        raise

                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    logger.warning(
                        "Fonksiyon %s deneme %d/%d başarısız (%s). "
                        "%.1f saniye sonra tekrar denenecek...",
                        func.__name__, attempt, max_retries, e, delay
                    )

                    if on_retry:
                        on_retry(attempt, e, delay)
                    else:
                        console.print(
                            f"  [yellow]⚠ Deneme {attempt}/{max_retries} başarısız. "
                            f"{delay:.0f}s sonra tekrar...[/yellow]"
                        )

                    time.sleep(delay)

            raise last_exception
        return wrapper
    return decorator


# ──────────────────────────────────────
# Checkpoint / Resume Sistemi
# ──────────────────────────────────────
class PipelineCheckpoint:
    """
    Pipeline'ın ilerleme durumunu kaydeder.
    Yarıda kalan pipeline kaldığı yerden devam edebilir.

    Checkpoint yapısı:
    {
        "topic": "...",
        "started_at": "...",
        "updated_at": "...",
        "completed_steps": ["scenario", "audio", "images", "video"],
        "current_step": "audio",
        "scenario_path": "temp/scenario.json",
        "audio_results": [...],
        "image_results": [...],
        "final_video": "...",
        "episode_title": "..."
    }
    """

    STEPS = ["scenario", "audio", "images", "video"]

    def __init__(self):
        self.data = {}
        self._load()

    def _load(self):
        """Checkpoint dosyasını yükle (varsa)."""
        if CHECKPOINT_FILE.exists():
            try:
                with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                logger.info("Checkpoint yüklendi: %s", CHECKPOINT_FILE)
            except (json.JSONDecodeError, IOError):
                self.data = {}
                logger.warning("Checkpoint dosyası okunamadı, sıfırdan başlanıyor.")

    def _save(self):
        """Checkpoint dosyasını kaydet."""
        self.data["updated_at"] = datetime.now().isoformat()
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        logger.debug("Checkpoint güncellendi.")

    def start(self, topic: str):
        """Yeni pipeline başlat."""
        self.data = {
            "topic": topic,
            "started_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "completed_steps": [],
            "current_step": None,
        }
        self._save()
        logger.info("Yeni pipeline checkpoint oluşturuldu: '%s'", topic)

    def is_step_completed(self, step: str) -> bool:
        """Adım tamamlanmış mı?"""
        return step in self.data.get("completed_steps", [])

    def get_current_step(self) -> str | None:
        """Şu anki adımı döndür."""
        return self.data.get("current_step")

    def set_current_step(self, step: str):
        """Şu anki adımı ayarla."""
        self.data["current_step"] = step
        self._save()

    def complete_step(self, step: str, **extra_data):
        """Adımı tamamlandı olarak işaretle ve ek veri kaydet."""
        completed = self.data.get("completed_steps", [])
        if step not in completed:
            completed.append(step)
        self.data["completed_steps"] = completed
        self.data["current_step"] = None
        self.data.update(extra_data)
        self._save()
        logger.info("Adım tamamlandı: %s", step)

    def can_resume(self, topic: str) -> bool:
        """Bu konu için devam edilebilir checkpoint var mı?"""
        if not self.data:
            return False
        return (
            self.data.get("topic") == topic
            and len(self.data.get("completed_steps", [])) > 0
            and len(self.data.get("completed_steps", [])) < len(self.STEPS)
        )

    def get_resume_info(self) -> str:
        """Devam bilgisi özeti."""
        completed = self.data.get("completed_steps", [])
        total = len(self.STEPS)
        done = len(completed)
        next_step = None
        for s in self.STEPS:
            if s not in completed:
                next_step = s
                break
        return (
            f"İlerleme: {done}/{total} adım tamamlandı. "
            f"Sonraki adım: {next_step or 'Tamamlandı'}"
        )

    def clear(self):
        """Checkpoint'i sil."""
        self.data = {}
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()
        logger.info("Checkpoint silindi.")


# ──────────────────────────────────────
# İlerleme Çubuğu Yardımcısı
# ──────────────────────────────────────
def create_progress_bar() -> Progress:
    """Rich progress bar oluştur."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=30),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    )
