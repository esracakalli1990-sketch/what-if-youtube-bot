"""
scheduler.py - Konu Havuzu ve Zamanlama Sistemi.

Otomatik video üretim döngüsü yönetir.
Konu havuzundan sırayla konu çekip pipeline'ı çalıştırır.

Özellikler:
- Konu havuzu (JSON dosyası)
- Zamanlama (günlük/haftalık)
- Konu rotasyonu (üretilen konuları işaretle)
- Pipeline çağrısı
- Webhook entegrasyonu (n8n ile)
"""

import json
import time
import random
from pathlib import Path
from datetime import datetime, timedelta

from scripts.utils import (
    print_header, print_step, print_success, print_error,
    print_warning, console, logger, PROJECT_ROOT, OUTPUT_DIR
)

# Konu havuzu dosyası
TOPICS_FILE = PROJECT_ROOT / "topics.json"

# Varsayılan konu havuzu
DEFAULT_TOPICS = [
    "What would happen if the Sun suddenly went out?",
    "What would happen if gravity doubled overnight?",
    "What would happen if the Earth stopped spinning?",
    "What would happen if all ice on Earth melted instantly?",
    "What would happen if humans could photosynthesize?",
    "What would happen if the Moon suddenly disappeared?",
    "What would happen if time moved backward for 24 hours?",
    "What would happen if all insects vanished from Earth?",
    "What would happen if the speed of light was only 100 km/h?",
    "What would happen if oxygen levels doubled?",
    "What would happen if the Earth was twice its size?",
    "What would happen if all oceans turned to freshwater?",
    "What would happen if humans had no sleep?",
    "What would happen if every volcano erupted at once?",
    "What would happen if the Earth had rings like Saturn?",
    "What would happen if we could hear radio waves?",
    "What would happen if dinosaurs never went extinct?",
    "What would happen if the Amazon rainforest disappeared?",
    "What would happen if every nuclear weapon detonated at once?",
    "What would happen if the Earth's core cooled down?",
    "What would happen if you could walk on clouds?",
    "What would happen if all satellites fell from orbit?",
    "What would happen if the atmosphere was twice as thick?",
    "What would happen if we found life on Mars?",
    "What would happen if antimatter was as common as matter?",
    "What would happen if the sun was replaced by a black hole?",
    "What would happen if photosynthesis stopped working?",
    "What would happen if the Earth's magnetic field vanished?",
    "What would happen if humans could regenerate limbs?",
    "What would happen if a rogue planet entered our solar system?",
]


def load_topics() -> dict:
    """
    Konu havuzunu yükle.

    Yapı:
    {
        "topics": [
            {"topic": "...", "status": "pending|completed|failed", "episode": null|1, "completed_at": null|"..."}
        ],
        "settings": {
            "shuffle": true,
            "auto_advance": true
        }
    }
    """
    if TOPICS_FILE.exists():
        try:
            with open(TOPICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Konu dosyası okunamadı: %s", e)

    # Varsayılan havuz oluştur
    data = {
        "topics": [
            {"topic": t, "status": "pending", "episode": None, "completed_at": None}
            for t in DEFAULT_TOPICS
        ],
        "settings": {
            "shuffle": False,
            "auto_advance": True,
        },
        "created_at": datetime.now().isoformat(),
    }
    save_topics(data)
    logger.info("Varsayılan konu havuzu oluşturuldu: %d konu", len(DEFAULT_TOPICS))
    return data


def save_topics(data: dict):
    """Konu havuzunu kaydet."""
    with open(TOPICS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_next_topic() -> str | None:
    """
    Sıradaki bekleyen konuyu döndür.

    Returns:
        str | None: Konu metni veya None (tüm konular tamamlanmışsa)
    """
    data = load_topics()
    topics = data.get("topics", [])
    settings = data.get("settings", {})

    pending = [t for t in topics if t.get("status") == "pending"]

    if not pending:
        logger.info("Tüm konular tamamlandı.")
        return None

    if settings.get("shuffle"):
        return random.choice(pending)["topic"]

    return pending[0]["topic"]


def mark_topic_completed(topic: str, episode_number: int | None = None):
    """Konuyu tamamlandı olarak işaretle."""
    data = load_topics()
    for t in data.get("topics", []):
        if t["topic"] == topic:
            t["status"] = "completed"
            t["episode"] = episode_number
            t["completed_at"] = datetime.now().isoformat()
            break
    save_topics(data)
    logger.info("Konu tamamlandı: '%s' (Episode %s)", topic, episode_number)


def mark_topic_failed(topic: str, error: str = ""):
    """Konuyu başarısız olarak işaretle."""
    data = load_topics()
    for t in data.get("topics", []):
        if t["topic"] == topic:
            t["status"] = "failed"
            t["failed_at"] = datetime.now().isoformat()
            t["error"] = error
            break
    save_topics(data)
    logger.warning("Konu başarısız: '%s' — %s", topic, error)


def add_topic(topic: str):
    """Yeni konu ekle."""
    data = load_topics()
    # Duplikat kontrolü
    existing = [t["topic"].lower() for t in data.get("topics", [])]
    if topic.lower() in existing:
        print_warning(f"Bu konu zaten var: {topic}")
        return

    data["topics"].append({
        "topic": topic,
        "status": "pending",
        "episode": None,
        "completed_at": None,
    })
    save_topics(data)
    print_success(f"Konu eklendi: {topic}")
    logger.info("Yeni konu eklendi: '%s'", topic)


def list_topics():
    """Konu havuzunu listele."""
    data = load_topics()
    topics = data.get("topics", [])

    pending = [t for t in topics if t.get("status") == "pending"]
    completed = [t for t in topics if t.get("status") == "completed"]
    failed = [t for t in topics if t.get("status") == "failed"]

    print_header("📋 KONU HAVUZU")
    console.print(f"  Toplam: [bold]{len(topics)}[/bold] | "
                  f"Bekleyen: [yellow]{len(pending)}[/yellow] | "
                  f"Tamamlanan: [green]{len(completed)}[/green] | "
                  f"Başarısız: [red]{len(failed)}[/red]")
    console.print()

    for i, t in enumerate(topics, 1):
        status = t.get("status", "pending")
        if status == "completed":
            icon = "✅"
            ep = f" (Episode {t.get('episode', '?')})"
        elif status == "failed":
            icon = "❌"
            ep = ""
        else:
            icon = "⏳"
            ep = ""

        console.print(f"  {icon} {i:2d}. {t['topic']}{ep}")


def refill_topics(count: int = 10) -> int:
    """
    Gemini ile konu havuzuna yeni, viral-potansiyelli konular ekle.

    Mevcut havuzu (duplikat önleme) ve varsa en iyi performans gösteren
    videoların başlıklarını (benzer içerik üretimi) prompta dahil eder.

    Args:
        count: Üretilecek yeni konu sayısı

    Returns:
        int: Havuza eklenen konu sayısı
    """
    import json as _json
    from google import genai
    from scripts.utils import load_env
    from scripts.scenario_generator import _call_gemini

    print_header(f"💡 KONU MOTORU — {count} yeni konu üretiliyor")

    keys = load_env()
    api_key = keys.get("GEMINI_API_KEY")
    if not api_key or "buraya" in api_key:
        print_error("GEMINI_API_KEY tanımlı değil!")
        return 0

    client = genai.Client(api_key=api_key)

    data = load_topics()
    existing = [t["topic"] for t in data.get("topics", [])]

    # En iyi performans gösteren videolar (analytics varsa)
    top_titles = []
    try:
        from scripts.analytics import get_top_performers
        top_titles = [p["title"] for p in get_top_performers(5)]
    except Exception:
        pass

    performance_hint = ""
    if top_titles:
        titles_block = "\n".join(f"- {t}" for t in top_titles)
        performance_hint = (
            "\nOur channel's BEST performing videos so far (generate topics with "
            f"similar viral appeal):\n{titles_block}\n"
        )

    existing_block = "\n".join(f"- {t}" for t in existing[-60:])

    system_prompt = (
        "You are a YouTube growth strategist for a science channel that makes "
        "\"What If\" thought-experiment videos. You know exactly which hypothetical "
        "scenarios trigger mass curiosity: personal stakes, apocalyptic scale, "
        "counterintuitive physics, body horror, time, money, space. "
        "Output ONLY a valid JSON array of topic strings, no extra text."
    )

    user_prompt = f"""Generate exactly {count} NEW "What If" video topics with maximum viral potential.

Rules:
- Each topic starts with "What would happen if" or "What if"
- Concrete, visual, high-stakes scenarios (a viewer must instantly picture it)
- Mix scales: personal body, city, planet, universe
- NO duplicates of these existing topics:
{existing_block}
{performance_hint}
Output format: JSON array of strings only. Example: ["What would happen if ...", ...]"""

    topics_json = None
    for model_name in ("gemini-2.5-flash", "gemini-2.0-flash"):
        try:
            topics_json = _call_gemini(client, system_prompt, user_prompt, model=model_name, temperature=1.0)
            break
        except Exception as e:
            logger.warning("Konu üretimi hatası (model=%s): %s", model_name, e)

    if not isinstance(topics_json, list):
        print_error("Konu üretilemedi (geçersiz yanıt).")
        return 0

    existing_lower = {t.lower() for t in existing}
    added = 0
    for topic in topics_json:
        if not isinstance(topic, str) or not topic.strip():
            continue
        topic = topic.strip()
        if topic.lower() in existing_lower:
            continue
        data["topics"].append({
            "topic": topic,
            "status": "pending",
            "episode": None,
            "completed_at": None,
        })
        existing_lower.add(topic.lower())
        added += 1
        console.print(f"  ➕ {topic}")

    save_topics(data)
    print_success(f"{added} yeni konu havuza eklendi.")
    logger.info("Konu havuzu dolduruldu: %d yeni konu", added)
    return added


def run_batch(count: int = 1, delay_minutes: int = 5, with_shorts: bool = False):
    """
    Toplu video üretimi — birden fazla konu için sırayla pipeline çalıştır.

    Args:
        count: Üretilecek video sayısı
        delay_minutes: Videolar arasındaki bekleme süresi (dakika)
        with_shorts: True ise her uzun videodan sonra aynı konudan bir Short üret
    """
    # Lazy import — circular dependency önle
    from main import run_pipeline

    print_header(f"🔄 TOPLU ÜRETİM — {count} video" + (" + Shorts" if with_shorts else ""))

    for i in range(count):
        topic = get_next_topic()
        if not topic:
            print_warning("Bekleyen konu kalmadı!")
            break

        console.print(f"\n{'═' * 50}")
        console.print(f"  📌 Video {i + 1}/{count}: [bold cyan]{topic}[/bold cyan]")
        console.print(f"{'═' * 50}")

        try:
            run_pipeline(topic)
            # Episode numarası
            from scripts.utils import get_episode_number
            ep_num = get_episode_number() - 1  # Son üretilen
            mark_topic_completed(topic, ep_num)

            # Aynı konudan Short üret (keşif trafiği için)
            if with_shorts:
                console.print(f"\n  📱 Aynı konudan Short üretiliyor...")
                try:
                    run_pipeline(topic, mode="shorts")
                except Exception as e:
                    print_warning(f"Shorts üretimi başarısız (uzun video tamamlandı): {e}")
                    logger.warning("Batch shorts hatası: %s — %s", topic, e)

        except Exception as e:
            mark_topic_failed(topic, str(e))
            print_error(f"Pipeline hatası: {e}")
            logger.error("Batch pipeline hatası: %s — %s", topic, e)

        # Videolar arasında bekleme
        if i < count - 1 and delay_minutes > 0:
            console.print(f"\n  ⏳ {delay_minutes} dakika bekleniyor...")
            time.sleep(delay_minutes * 60)

    print_header("🏁 TOPLU ÜRETİM TAMAMLANDI")
    list_topics()


def reset_failed():
    """Başarısız konuları tekrar beklemeye al."""
    data = load_topics()
    count = 0
    for t in data.get("topics", []):
        if t.get("status") == "failed":
            t["status"] = "pending"
            t["error"] = None
            t["failed_at"] = None
            count += 1
    save_topics(data)
    print_success(f"{count} başarısız konu tekrar sıraya alındı.")


# ──────────────────────────────────────
# Doğrudan çalıştırma
# ──────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Konu Havuzu ve Zamanlama")
    parser.add_argument("--list", action="store_true", help="Konu havuzunu listele")
    parser.add_argument("--next", action="store_true", help="Sıradaki konuyu göster")
    parser.add_argument("--add", metavar="TOPIC", help="Yeni konu ekle")
    parser.add_argument("--batch", type=int, metavar="N", help="N video üret")
    parser.add_argument("--delay", type=int, default=5, help="Videolar arası bekleme (dakika)")
    parser.add_argument("--with-shorts", action="store_true",
                        help="Batch'te her uzun videodan sonra aynı konudan Short üret")
    parser.add_argument("--reset-failed", action="store_true", help="Başarısız konuları sıfırla")
    parser.add_argument("--refill", type=int, metavar="N",
                        help="Gemini ile havuza N yeni viral konu ekle")

    args = parser.parse_args()

    if args.list:
        list_topics()
    elif args.next:
        topic = get_next_topic()
        if topic:
            console.print(f"  📌 Sıradaki: [bold cyan]{topic}[/bold cyan]")
        else:
            print_warning("Bekleyen konu yok!")
    elif args.add:
        add_topic(args.add)
    elif args.batch:
        run_batch(count=args.batch, delay_minutes=args.delay, with_shorts=args.with_shorts)
    elif args.reset_failed:
        reset_failed()
    elif args.refill:
        refill_topics(args.refill)
    else:
        parser.print_help()
