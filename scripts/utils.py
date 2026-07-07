"""
utils.py - Yardımcı fonksiyonlar ve ortak araçlar.
Tüm modüller tarafından kullanılır.
"""

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

# Rich console - güzel terminal çıktıları
console = Console()

# Proje kök dizini
PROJECT_ROOT = Path(__file__).parent.parent

# Dizin yolları
TEMP_DIR = PROJECT_ROOT / "temp"
AUDIO_DIR = TEMP_DIR / "audio"
IMAGES_DIR = TEMP_DIR / "images"
CLIPS_DIR = TEMP_DIR / "clips"
OUTPUT_DIR = PROJECT_ROOT / "output"
CHARACTER_DIR = PROJECT_ROOT / "character" / "reference"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
ASSETS_DIR = PROJECT_ROOT / "assets" / "music"


def load_env():
    """API anahtarlarını .env dosyasından yükle."""
    env_path = PROJECT_ROOT / ".env"
    load_dotenv(env_path)

    keys = {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),
        "CHARACTER_VOICE_ID": os.getenv("CHARACTER_VOICE_ID"),
        "REPLICATE_API_TOKEN": os.getenv("REPLICATE_API_TOKEN"),
    }

    return keys


def ensure_directories():
    """Gerekli tüm klasörleri oluştur."""
    dirs = [TEMP_DIR, AUDIO_DIR, IMAGES_DIR, CLIPS_DIR,
            OUTPUT_DIR, CHARACTER_DIR, PROMPTS_DIR, ASSETS_DIR]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    console.print("[green]✓[/green] Tüm dizinler hazır.")


def save_json(data: dict, filepath: Path):
    """JSON dosyasına kaydet."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    console.print(f"[green]✓[/green] JSON kaydedildi: {filepath.name}")


def load_json(filepath: Path) -> dict:
    """JSON dosyasından oku."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def read_prompt(filename: str) -> str:
    """prompts/ klasöründen prompt dosyası oku."""
    filepath = PROMPTS_DIR / filename
    if not filepath.exists():
        console.print(f"[red]✗[/red] Prompt dosyası bulunamadı: {filename}")
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()


def print_header(title: str):
    """Güzel başlık yazdır."""
    console.print()
    console.print(Panel(f"[bold cyan]{title}[/bold cyan]",
                        border_style="bright_blue"))


def print_step(step_num: int, description: str):
    """Adım bilgisi yazdır."""
    console.print(f"\n[bold yellow]▶ Adım {step_num}:[/bold yellow] {description}")


def print_success(message: str):
    """Başarı mesajı yazdır."""
    console.print(f"[bold green]✓ {message}[/bold green]")


def print_error(message: str):
    """Hata mesajı yazdır."""
    console.print(f"[bold red]✗ {message}[/bold red]")


def get_episode_number() -> int:
    """output/ klasöründeki son bölüm numarasını bul ve bir sonrakini döndür."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    existing = list(OUTPUT_DIR.glob("episode_*.mp4"))
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


def clean_temp():
    """Geçici dosyaları temizle."""
    import shutil
    for subdir in [AUDIO_DIR, IMAGES_DIR, CLIPS_DIR]:
        if subdir.exists():
            shutil.rmtree(subdir)
            subdir.mkdir(parents=True, exist_ok=True)
    console.print("[green]✓[/green] Geçici dosyalar temizlendi.")
