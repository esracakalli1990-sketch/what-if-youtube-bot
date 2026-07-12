"""
shorts_queue.py - Short üretim kuyruğu.

Kullanıcı istediği kadar Short'u kuyruğa atabilir (ör. /short 5). Manuel görsel
akışı aynı anda TEK üretimi taşır (aynı IMAGES_DIR'e yazıldığı için birden fazla
üretim çakışır); bu yüzden kuyruk yalnızca bir KONU listesi tutar. Bot boşta
kaldıkça (bekleyen üretim yokken) sıradaki konuyu otomatik başlatır, prompt'ları
gönderir, kullanıcı görselleri üretip yollar, tamamlanınca sıradakine geçilir.

Durum dosyası: shorts_queue.json (workflow'larca commit edilir — topics.json gibi).
"""

import json
from pathlib import Path

from scripts.utils import PROJECT_ROOT, logger

QUEUE_FILE = PROJECT_ROOT / "shorts_queue.json"


def load_queue() -> list[str]:
    """Kuyruktaki konuları oku (yoksa boş liste)."""
    if not QUEUE_FILE.exists():
        return []
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        topics = data.get("topics", []) if isinstance(data, dict) else data
        return [t for t in topics if isinstance(t, str) and t.strip()]
    except (json.JSONDecodeError, IOError):
        return []


def _save(topics: list[str]):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump({"topics": topics}, f, ensure_ascii=False, indent=2)


def enqueue(topics: list[str]) -> int:
    """
    Konuları kuyruğa ekle (zaten kuyrukta olanları atlar).

    Returns:
        int: Eklenen konu sayısı
    """
    q = load_queue()
    added = 0
    for t in topics:
        t = (t or "").strip()
        if t and t not in q:
            q.append(t)
            added += 1
    if added:
        _save(q)
        logger.info("Short kuyruğuna %d konu eklendi (toplam %d).", added, len(q))
    return added


def pop_next() -> str | None:
    """Sıradaki konuyu al ve kuyruktan çıkar (yoksa None)."""
    q = load_queue()
    if not q:
        return None
    topic = q.pop(0)
    _save(q)
    return topic


def length() -> int:
    """Kuyruktaki konu sayısı."""
    return len(load_queue())


def clear() -> int:
    """Kuyruğu boşalt. Returns: silinen konu sayısı."""
    n = length()
    if QUEUE_FILE.exists():
        QUEUE_FILE.unlink()
    return n
