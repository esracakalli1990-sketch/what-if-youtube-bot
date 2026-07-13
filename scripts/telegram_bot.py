"""
telegram_bot.py - Telegram Komut İşleyici.

Telegram'dan gelen komutları okur ve çalıştırır. GitHub Actions'ta saatlik
çalışacak şekilde tasarlanmıştır (sunucu gerektirmez): her çalıştığında
bekleyen mesajları getUpdates ile çeker, işler ve offset'i kaydeder.

Komutlar:
    /durum   — konu havuzu + son yüklemeler
    /rapor   — kanal performans raporu
    /konular — bekleyen konuların listesi
    /konu <metin>  — havuza yeni konu ekle
    /short   — hemen 1 Short üret ve yükle
    /video [konu]  — hemen 1 uzun video üret (konu verilmezse havuzdan)
    /yardim  — komut listesi

Güvenlik: yalnızca TELEGRAM_CHAT_ID'de tanımlı kullanıcının mesajları işlenir.

Kullanım:
    python scripts/telegram_bot.py --poll    # bekleyen komutları bir kez işle
"""

import sys
import json
from pathlib import Path

# Doğrudan çalıştırma desteği: python scripts/telegram_bot.py
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

from scripts.utils import (
    print_header, print_success, print_error, print_warning,
    console, logger, load_env, PROJECT_ROOT
)
from scripts.notifier import TELEGRAM_API, send_message, is_configured

# getUpdates offset durumu — workflow tarafından commit'lenir
STATE_FILE = PROJECT_ROOT / "telegram_state.json"

HELP_TEXT = """🐰 <b>What-If Bot Komutları</b>

/durum — konu havuzu + son yüklemeler + bekleyen görseller
/rapor — kanal performans raporu
/konular — bekleyen konular
/konu &lt;metin&gt; — havuza yeni konu ekle
/short — 1 Short'u kuyruğa ekle
/short &lt;sayı&gt; — bu kadar Short'u kuyruğa ekle (ör. /short 5)
/short &lt;konu&gt; — bu konuyu Short olarak kuyruğa ekle
/kuyruk — Short kuyruğunda kaç konu var
/kuyruk temizle — kuyruğu boşalt
/video — hemen 1 uzun video üret (havuzdan)
/video &lt;konu&gt; — bu konudan uzun video üret
/iptal — görsel bekleyen üretimi iptal et
/yardim — bu liste

Kaç Short istersen kuyruğa at; bot boştaysa hemen başlar, değilse sırayla
otomatik ilerler. Her Short için bot prompt'ları gönderir, görselleri sırayla
bu sohbete yollarsın, video otomatik tamamlanır. Komutlar saatte bir işlenir."""


def _load_offset() -> int:
    """Son işlenen update ID'sini oku."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("offset", 0)
        except (json.JSONDecodeError, IOError):
            pass
    return 0


def _save_offset(offset: int):
    """Update offset'ini kaydet."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"offset": offset}, f)


def get_updates(token: str, offset: int) -> list[dict]:
    """Telegram'dan bekleyen mesajları çek."""
    try:
        response = requests.get(
            f"{TELEGRAM_API}/bot{token}/getUpdates",
            params={"offset": offset, "timeout": 0},
            timeout=30,
        )
        if response.status_code == 200:
            return response.json().get("result", [])
        logger.warning("getUpdates hatası (%d): %s", response.status_code, response.text[:200])
    except Exception as e:
        logger.warning("getUpdates bağlantı hatası: %s", e)
    return []


# ──────────────────────────────────────
# Komut İşleyiciler
# ──────────────────────────────────────
def _cmd_durum() -> str:
    """Konu havuzu ve son yüklemeler özeti."""
    from scripts.scheduler import load_topics
    from scripts.youtube_uploader import load_uploads

    data = load_topics()
    topics = data.get("topics", [])
    pending = sum(1 for t in topics if t.get("status") == "pending")
    completed = sum(1 for t in topics if t.get("status") == "completed")
    failed = sum(1 for t in topics if t.get("status") == "failed")
    shorts_done = sum(1 for t in topics if t.get("short_at"))

    from scripts import shorts_queue
    queued = shorts_queue.length()

    lines = [
        "📋 <b>Bot Durumu</b>",
        "",
        f"⏳ Bekleyen konu: {pending}",
        f"✅ Tamamlanan uzun video: {completed}",
        f"📱 Üretilen Short: {shorts_done}",
        f"📥 Short kuyruğunda: {queued}",
        f"❌ Başarısız: {failed}",
    ]

    uploads = load_uploads()
    if uploads:
        lines += ["", "<b>Son yüklemeler:</b>"]
        for u in uploads[-3:]:
            icon = "📱" if u.get("kind") == "short" else "🎬"
            lines.append(f"{icon} {u.get('title', '?')[:50]}")
            lines.append(f"    https://youtu.be/{u.get('video_id')}")
    else:
        lines += ["", "Henüz yükleme yok."]

    # Görsel bekleyen üretim varsa göster
    from scripts.manual_images import get_pending_status_text
    lines.append(get_pending_status_text())

    return "\n".join(lines)


def _cmd_rapor() -> str:
    """Kanal performans raporu."""
    from scripts.analytics import format_report_text
    return format_report_text()


def _cmd_konular() -> str:
    """Bekleyen konuları listele."""
    from scripts.scheduler import load_topics

    data = load_topics()
    pending = [t["topic"] for t in data.get("topics", []) if t.get("status") == "pending"]

    if not pending:
        return "⏳ Bekleyen konu yok! /konu ile ekleyin veya Pazar otomatik doldurulmasını bekleyin."

    lines = [f"💡 <b>Bekleyen Konular ({len(pending)})</b>", ""]
    for i, t in enumerate(pending[:15], 1):
        lines.append(f"{i}. {t}")
    if len(pending) > 15:
        lines.append(f"... ve {len(pending) - 15} konu daha")
    return "\n".join(lines)


def _cmd_konu_ekle(topic: str) -> str:
    """Havuza yeni konu ekle."""
    if not topic:
        return "Kullanım: /konu What would happen if ...?"

    from scripts.scheduler import load_topics, add_topic

    before = len(load_topics().get("topics", []))
    add_topic(topic)
    after = len(load_topics().get("topics", []))

    if after > before:
        return f"➕ Konu eklendi:\n<i>{topic}</i>"
    return f"⚠️ Bu konu zaten havuzda var:\n<i>{topic}</i>"


def _cmd_short(arg: str = "") -> str:
    """
    Short(lar)ı kuyruğa ekle. Kullanım:
      /short           → havuzdan 1 Short kuyruğa ekle
      /short 5         → havuzdan 5 Short kuyruğa ekle
      /short <konu>    → bu konuyu Short olarak kuyruğa ekle

    Bot boştaysa sıradaki hemen başlar; değilse mevcut üretim bitince
    otomatik sıraya geçer. Her Short için görselleri sırayla gönderirsiniz.
    """
    from scripts import shorts_queue
    from scripts.scheduler import get_next_short_topics

    arg = arg.strip()
    if arg.isdigit():
        count = max(1, min(int(arg), 50))  # makul üst sınır
        already = set(shorts_queue.load_queue())
        topics = get_next_short_topics(count, exclude=already)
        if not topics:
            return "⏳ Havuzda Short üretilmemiş konu kalmadı. /konu ile ekleyin veya Pazar otomatik doldurmayı bekleyin."
        added = shorts_queue.enqueue(topics)
    elif arg:
        added = shorts_queue.enqueue([arg])
        if not added:
            return "Bu konu zaten kuyrukta."
    else:
        already = set(shorts_queue.load_queue())
        topics = get_next_short_topics(1, exclude=already)
        if not topics:
            return "⏳ Havuzda Short üretilmemiş konu kalmadı. /konu ile ekleyebilirsiniz."
        added = shorts_queue.enqueue(topics)

    total = shorts_queue.length()
    started = _advance_shorts_queue()
    if started:
        return (f"✅ {added} Short kuyruğa eklendi (kuyrukta {total}).\n"
                f"İlkinin promptlarını gönderiyorum — görselleri sırayla yollayın. "
                f"Her biri bitince sıradaki otomatik başlar.")
    return (f"✅ {added} Short kuyruğa eklendi (kuyrukta {total}).\n"
            f"Şu an bekleyen bir üretim var; o bitince sıradaki otomatik başlayacak.")


def _advance_shorts_queue() -> bool:
    """
    Bekleyen üretim yoksa kuyruktaki sıradaki Short'u başlat (prompt'ları gönderir).

    Returns:
        bool: Yeni bir Short başlatıldı mı?
    """
    from scripts import manual_images, shorts_queue
    from scripts.scheduler import run_short

    # Zaten görsel bekleyen bir üretim varsa dokunma (tek slot — çakışma olmasın)
    if manual_images.load_pending() is not None:
        return False
    topic = shorts_queue.pop_next()
    if not topic:
        return False
    try:
        run_short(privacy="public", topic=topic)
        return True
    except Exception as e:
        logger.error("Kuyruktan Short başlatma hatası: %s — %s", topic, e)
        send_message(f"🚨 Kuyruktaki Short başlatılamadı ('{topic[:50]}'): "
                     f"<code>{str(e)[:200]}</code>")
        return False


def _cmd_video(topic: str) -> str:
    """Hemen bir uzun video üret."""
    send_message("🎬 Uzun video üretimi başladı... (~30-45 dk, bitince bildirim gelecek)")

    from main import run_pipeline
    from scripts.scheduler import get_next_topic, mark_topic_completed, mark_topic_failed

    from_pool = False
    if not topic:
        topic = get_next_topic()
        from_pool = True
        if not topic:
            return "⏳ Havuzda bekleyen konu yok. /konu ile ekleyin veya /video <konu> deneyin."

    try:
        result = run_pipeline(topic, privacy="public")
    except Exception as e:
        if from_pool:
            mark_topic_failed(topic, str(e))
        return f"🚨 Video üretimi hatası: <code>{str(e)[:300]}</code>"

    if result == "pending":
        return ""  # Manuel görsel akışı — prompt'lar gönderildi

    if result and from_pool:
        from scripts.utils import get_episode_number
        mark_topic_completed(topic, get_episode_number() - 1)

    return "" if result else "🚨 Video üretimi başarısız oldu — loglara bakın."


def handle_command(text: str) -> str:
    """
    Tek bir komutu işle ve yanıt metnini döndür.

    Boş string dönerse ek yanıt gerekmiyordur (pipeline kendi bildirimini atar).
    """
    text = text.strip()
    parts = text.split(maxsplit=1)
    command = parts[0].lower().split("@")[0]  # /durum@BotAdi biçimini destekle
    arg = parts[1].strip() if len(parts) > 1 else ""

    if command in ("/start", "/yardim", "/help"):
        return HELP_TEXT
    if command == "/durum":
        return _cmd_durum()
    if command == "/rapor":
        return _cmd_rapor()
    if command == "/konular":
        return _cmd_konular()
    if command == "/konu":
        return _cmd_konu_ekle(arg)
    if command == "/short":
        return _cmd_short(arg)
    if command == "/video":
        return _cmd_video(arg)
    if command == "/iptal":
        from scripts.manual_images import cancel_pending
        if cancel_pending():
            return "🗑 Görsel bekleyen üretim iptal edildi. Konu havuzda kaldı, istediğinizde tekrar üretebilirsiniz."
        return "İptal edilecek bekleyen üretim yok."
    if command == "/kuyruk":
        from scripts import shorts_queue
        n = shorts_queue.length()
        if arg.strip().lower() in ("temizle", "sil", "iptal"):
            cleared = shorts_queue.clear()
            return f"🗑 Short kuyruğu temizlendi ({cleared} konu çıkarıldı)."
        return (f"📋 Short kuyruğunda {n} konu bekliyor." if n
                else "📋 Short kuyruğu boş. /short <sayı> ile ekleyebilirsiniz.")

    return "❓ Bilinmeyen komut. /yardim yazarak komutları görebilirsiniz."


def process_pending_commands() -> int:
    """
    Bekleyen tüm Telegram mesajlarını işle.

    Returns:
        int: İşlenen komut sayısı
    """
    if not is_configured():
        print_warning("Telegram yapılandırılmamış (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID).")
        return 0

    keys = load_env()
    token = keys["TELEGRAM_BOT_TOKEN"]
    authorized_chat = str(keys["TELEGRAM_CHAT_ID"])

    offset = _load_offset()
    updates = get_updates(token, offset)

    # Manuel görsel akışı: hatırlatma + (önceki koşuda indirilemeyen) tamamlama denemesi
    from scripts import manual_images
    manual_images.send_reminder_if_due()

    if not updates:
        if manual_images.is_complete():
            manual_images.complete_production()
        else:
            console.print("  💤 Bekleyen komut yok.")
        # Boşta isek kuyruktaki sıradaki Short'u başlat
        _advance_shorts_queue()
        return 0

    processed = 0
    for update in updates:
        offset = max(offset, update.get("update_id", 0) + 1)

        message = update.get("message") or {}
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "")
        photos = message.get("photo") or []
        video = message.get("video") or {}
        document = message.get("document") or {}
        # Flow klibi "video" ya da video mime'lı "document" olarak gelebilir
        is_video_doc = str(document.get("mime_type", "")).startswith("video/")

        # Güvenlik: yalnızca yetkili kullanıcı
        if chat_id != authorized_chat:
            if text or photos or video or document:
                logger.warning("Yetkisiz Telegram mesajı yok sayıldı: chat=%s", chat_id)
            continue

        # Fotoğraf — manuel görsel akışına ekle (en büyük boyutun file_id'si)
        if photos:
            _save_offset(offset)
            from scripts.manual_images import add_photo
            reply = add_photo(photos[-1]["file_id"])
            if reply:
                send_message(reply)
            processed += 1
            continue

        # Video klip — manuel akışa ekle ("video" mesajı veya video mime'lı belge)
        if video or is_video_doc:
            _save_offset(offset)
            from scripts.manual_images import add_video
            file_id = video.get("file_id") or document.get("file_id")
            reply = add_video(file_id)
            if reply:
                send_message(reply)
            processed += 1
            continue

        if not text or not text.startswith("/"):
            continue

        console.print(f"  📨 Komut: [bold cyan]{text}[/bold cyan]")
        logger.info("Telegram komutu işleniyor: %s", text)

        # Offset'i komutu çalıştırmadan ÖNCE kaydet — uzun süren komut
        # yarıda kesilirse bir sonraki çalışmada aynı komut tekrarlanmasın
        _save_offset(offset)

        try:
            reply = handle_command(text)
        except Exception as e:
            reply = f"🚨 Komut işlenirken hata: <code>{str(e)[:300]}</code>"
            logger.error("Telegram komut hatası: %s — %s", text, e)

        if reply:
            send_message(reply)
        processed += 1

    _save_offset(offset)

    # Tüm görseller geldiyse videoyu tamamla (uzun sürer — offset zaten kayıtlı)
    if manual_images.is_complete():
        manual_images.complete_production()

    # Üretim bittiyse (veya hiç yoksa) kuyruktaki sıradaki Short'u başlat
    _advance_shorts_queue()

    print_success(f"{processed} komut işlendi.")
    return processed


# ──────────────────────────────────────
# Doğrudan çalıştırma
# ──────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Telegram Komut İşleyici")
    parser.add_argument("--poll", action="store_true", help="Bekleyen komutları bir kez işle")

    args = parser.parse_args()

    if args.poll:
        print_header("💬 TELEGRAM KOMUT İŞLEYİCİ")
        process_pending_commands()
    else:
        parser.print_help()
