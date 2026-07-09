"""
notifier.py - Telegram Bildirim Sistemi.

Otomasyonun her adımını Telegram'a raporlar:
- Video üretildi / YouTube'a yüklendi / planlı yayın
- Pipeline hataları
- Konu havuzu güncellemeleri
- Kanal performans raporu

Kurulum:
1. Telegram'da @BotFather'a /newbot yazıp bot oluşturun → token'ı alın
2. Botunuza herhangi bir mesaj atın, sonra chat ID'nizi öğrenin:
   python scripts/notifier.py --chat-id
3. .env dosyasına ekleyin:
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
   TELEGRAM_CHAT_ID=123456789
4. Test: python scripts/notifier.py --test

Telegram yapılandırılmamışsa tüm fonksiyonlar sessizce atlanır —
bot bildirimsiz de sorunsuz çalışır.
"""

import sys
from pathlib import Path

# Doğrudan çalıştırma desteği: python scripts/notifier.py
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

from scripts.utils import logger, load_env, console

TELEGRAM_API = "https://api.telegram.org"


def _config() -> tuple[str, str]:
    """Token ve chat ID'yi .env'den oku."""
    keys = load_env()
    return keys.get("TELEGRAM_BOT_TOKEN", ""), keys.get("TELEGRAM_CHAT_ID", "")


def is_configured() -> bool:
    """Telegram bildirimleri aktif mi?"""
    token, chat_id = _config()
    return bool(token and chat_id and "buraya" not in token)


def send_message(text: str, chat_id: str | None = None) -> bool:
    """
    Telegram'a mesaj gönder (HTML biçimli).

    Yapılandırma yoksa veya gönderim başarısızsa sessizce False döner —
    bildirim hatası pipeline'ı asla durdurmaz.
    """
    token, default_chat = _config()
    chat_id = chat_id or default_chat

    if not token or not chat_id or "buraya" in token:
        logger.debug("Telegram yapılandırılmamış, bildirim atlandı.")
        return False

    try:
        response = requests.post(
            f"{TELEGRAM_API}/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text[:4096],  # Telegram mesaj limiti
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        if response.status_code == 200:
            logger.info("Telegram bildirimi gönderildi.")
            return True
        logger.warning("Telegram API hatası (%d): %s", response.status_code, response.text[:200])
        return False
    except Exception as e:
        logger.warning("Telegram gönderim hatası: %s", e)
        return False


def send_photo(photo_path: str, caption: str = "") -> bool:
    """Telegram'a fotoğraf gönder (ör. thumbnail önizlemesi)."""
    token, chat_id = _config()
    if not token or not chat_id or "buraya" in token:
        return False

    try:
        with open(photo_path, "rb") as f:
            response = requests.post(
                f"{TELEGRAM_API}/bot{token}/sendPhoto",
                data={"chat_id": chat_id, "caption": caption[:1024], "parse_mode": "HTML"},
                files={"photo": f},
                timeout=60,
            )
        return response.status_code == 200
    except Exception as e:
        logger.warning("Telegram fotoğraf gönderim hatası: %s", e)
        return False


# ──────────────────────────────────────
# Mesaj Oluşturucular (saf fonksiyonlar — test edilebilir)
# ──────────────────────────────────────
def build_video_message(
    title: str,
    mode: str = "long",
    video_path: str = "",
    duration_text: str = "",
    video_id: str | None = None,
    publish_at=None,
) -> str:
    """Video tamamlanma bildirimi metni oluştur."""
    kind = "📱 Short" if mode == "shorts" else "🎬 Uzun video"
    lines = [f"✅ <b>{kind} hazır!</b>", "", f"📝 {title}"]

    if duration_text:
        lines.append(f"⏱ Üretim süresi: {duration_text}")
    if video_path:
        lines.append(f"📹 Dosya: <code>{Path(video_path).name}</code>")

    if video_id:
        lines.append(f"🔗 https://youtu.be/{video_id}")
        if publish_at:
            lines.append(f"📅 Planlı yayın: {publish_at.strftime('%d.%m.%Y %H:%M UTC')}")
        else:
            lines.append("📤 YouTube'a yüklendi")
    else:
        lines.append("⚠️ YouTube'a yüklenmedi (yetkilendirme yok veya --no-upload)")

    return "\n".join(lines)


def build_error_message(context: str, error: str) -> str:
    """Hata bildirimi metni oluştur."""
    return (
        f"🚨 <b>HATA — {context}</b>\n\n"
        f"<code>{str(error)[:1000]}</code>\n\n"
        f"Detay için logs/ klasörüne veya GitHub Actions çıktısına bakın."
    )


# ──────────────────────────────────────
# Olay Bildirimleri
# ──────────────────────────────────────
def notify_video_completed(
    title: str,
    mode: str = "long",
    video_path: str = "",
    duration_text: str = "",
    video_id: str | None = None,
    publish_at=None,
    thumbnail_path: str | None = None,
) -> bool:
    """Video üretimi tamamlandığında bildirim gönder (varsa thumbnail ile)."""
    text = build_video_message(title, mode, video_path, duration_text, video_id, publish_at)

    if thumbnail_path and Path(thumbnail_path).exists():
        if send_photo(thumbnail_path, caption=text):
            return True
    return send_message(text)


def notify_error(context: str, error) -> bool:
    """Pipeline hatasını bildir."""
    return send_message(build_error_message(context, error))


def notify_topics_refilled(added: int, total_pending: int) -> bool:
    """Konu havuzu güncellemesini bildir."""
    return send_message(
        f"💡 <b>Konu havuzu güncellendi</b>\n\n"
        f"➕ {added} yeni konu eklendi\n"
        f"⏳ Bekleyen toplam konu: {total_pending}"
    )


def send_analytics_report() -> bool:
    """Kanal performans raporunu Telegram'a gönder."""
    from scripts.analytics import format_report_text
    return send_message(format_report_text())


# ──────────────────────────────────────
# Doğrudan çalıştırma
# ──────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Telegram Bildirim Sistemi")
    parser.add_argument("--test", action="store_true", help="Test mesajı gönder")
    parser.add_argument("--report", action="store_true", help="Analitik raporu gönder")
    parser.add_argument("--chat-id", action="store_true",
                        help="Bota mesaj atan son kullanıcının chat ID'sini göster")

    args = parser.parse_args()

    if args.test:
        if send_message("🐰 <b>What-If Bot bağlantı testi</b>\n\nTelegram bildirimleri çalışıyor! ✅"):
            console.print("[green]✓ Test mesajı gönderildi![/green]")
        else:
            console.print("[red]✗ Gönderilemedi — TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID kontrol edin.[/red]")

    elif args.report:
        if send_analytics_report():
            console.print("[green]✓ Rapor gönderildi![/green]")
        else:
            console.print("[red]✗ Rapor gönderilemedi.[/red]")

    elif args.chat_id:
        token, _ = _config()
        if not token:
            console.print("[red]✗ Önce TELEGRAM_BOT_TOKEN tanımlayın.[/red]")
        else:
            resp = requests.get(f"{TELEGRAM_API}/bot{token}/getUpdates", timeout=15).json()
            results = resp.get("result", [])
            if results:
                chat = results[-1].get("message", {}).get("chat", {})
                console.print(f"  💬 Chat ID: [bold cyan]{chat.get('id')}[/bold cyan] "
                              f"({chat.get('first_name', '?')})")
                console.print("  Bu değeri .env dosyasına TELEGRAM_CHAT_ID olarak ekleyin.")
            else:
                console.print("[yellow]⚠ Önce botunuza Telegram'dan bir mesaj gönderin, sonra tekrar deneyin.[/yellow]")

    else:
        parser.print_help()
