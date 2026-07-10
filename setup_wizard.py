"""
setup_wizard.py - İnteraktif Kurulum Sihirbazı.

Sistemi aktifleştirmek için gereken TÜM adımları tek komutla, sırayla yürütür:

    python setup_wizard.py

Her adımda ne yapmanız gerektiğini söyler, girdiğiniz her anahtarı anında
test eder, YouTube yetkilendirmesini başlatır, Telegram chat ID'nizi otomatik
bulur ve sonunda GitHub'a eklenecek secret değerlerini hazır şekilde gösterir.

Yeniden çalıştırmak güvenlidir: tamamlanmış adımlar atlanır.
"""

import os
import sys
import base64
import subprocess
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
ENV_FILE = PROJECT_ROOT / ".env"

try:
    import requests
    from rich.console import Console
    from rich.panel import Panel
except ImportError:
    print("Önce bağımlılıkları kurun:  pip install -r requirements.txt")
    sys.exit(1)

console = Console()


# ──────────────────────────────────────
# Yardımcılar
# ──────────────────────────────────────
def header(text: str):
    console.print()
    console.print(Panel(f"[bold cyan]{text}[/bold cyan]", border_style="bright_blue"))


def ok(text: str):
    console.print(f"  [green]✓[/green] {text}")


def warn(text: str):
    console.print(f"  [yellow]⚠[/yellow] {text}")


def fail(text: str):
    console.print(f"  [red]✗[/red] {text}")


def ask(prompt: str) -> str:
    """Kullanıcıdan girdi al (baş/son boşlukları temizle)."""
    console.print(f"  [bold]{prompt}[/bold]", end=" ")
    return input().strip()


def open_browser(url: str):
    """Tarayıcıda sayfa aç (başarısız olursa linki yazdır)."""
    console.print(f"  🌐 {url}")
    try:
        webbrowser.open(url)
    except Exception:
        pass


def load_existing_env() -> dict:
    """Mevcut .env değerlerini oku."""
    values = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                values[key.strip()] = val.strip()
    return values


def save_env(values: dict):
    """Değerleri .env dosyasına yaz."""
    lines = [
        "# What-If YouTube Bot - setup_wizard.py tarafından oluşturuldu",
        f"GEMINI_API_KEY={values.get('GEMINI_API_KEY', '')}",
        f"ELEVENLABS_API_KEY={values.get('ELEVENLABS_API_KEY', '')}",
        f"CHARACTER_VOICE_ID={values.get('CHARACTER_VOICE_ID', '')}",
        f"REPLICATE_API_TOKEN={values.get('REPLICATE_API_TOKEN', '')}",
        f"YOUTUBE_PLAYLIST_ID={values.get('YOUTUBE_PLAYLIST_ID', '')}",
        f"TELEGRAM_BOT_TOKEN={values.get('TELEGRAM_BOT_TOKEN', '')}",
        f"TELEGRAM_CHAT_ID={values.get('TELEGRAM_CHAT_ID', '')}",
    ]
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok(f".env kaydedildi: {ENV_FILE}")


def is_set(value: str) -> bool:
    """Değer gerçekten dolu mu (placeholder değil)?"""
    return bool(value) and "buraya" not in value.lower()


def b64_file(path: Path) -> str:
    """Dosyayı GitHub secret için base64'e çevir."""
    return base64.b64encode(path.read_bytes()).decode("ascii")


# ──────────────────────────────────────
# Anahtar Doğrulayıcılar
# ──────────────────────────────────────
def validate_gemini(key: str) -> bool:
    """Gemini anahtarını gerçek bir API çağrısıyla test et."""
    try:
        r = requests.get(
            "https://generativelanguage.googleapis.com/v1beta/models",
            params={"key": key, "pageSize": 1},
            timeout=20,
        )
        return r.status_code == 200
    except Exception:
        return False


def validate_elevenlabs(key: str) -> list[dict]:
    """ElevenLabs anahtarını test et; geçerliyse ses listesini döndür."""
    try:
        r = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": key},
            timeout=20,
        )
        if r.status_code == 200:
            return r.json().get("voices", [])
    except Exception:
        pass
    return []


def validate_replicate(token: str) -> bool:
    """Replicate token'ını test et."""
    try:
        r = requests.get(
            "https://api.replicate.com/v1/account",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )
        return r.status_code == 200
    except Exception:
        return False


def validate_telegram_token(token: str) -> str:
    """Telegram bot token'ını test et; geçerliyse bot adını döndür."""
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=20)
        if r.status_code == 200 and r.json().get("ok"):
            return r.json()["result"].get("username", "bot")
    except Exception:
        pass
    return ""


# ──────────────────────────────────────
# Kurulum Adımları
# ──────────────────────────────────────
def step_dependencies() -> bool:
    """Adım 1: Bağımlılık ve FFmpeg kontrolü."""
    header("ADIM 1/6 — Bağımlılık Kontrolü")

    all_ok = True
    for module, pip_name in [
        ("google.genai", "google-genai"), ("replicate", "replicate"),
        ("elevenlabs", "elevenlabs"), ("PIL", "Pillow"),
        ("mutagen", "mutagen"), ("googleapiclient", "google-api-python-client"),
    ]:
        try:
            __import__(module)
            ok(pip_name)
        except ImportError:
            fail(f"{pip_name} eksik → pip install -r requirements.txt")
            all_ok = False

    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=10)
        if result.returncode == 0:
            ok("FFmpeg kurulu")
        else:
            raise FileNotFoundError
    except (FileNotFoundError, subprocess.TimeoutExpired):
        fail("FFmpeg bulunamadı → winget install Gyan.FFmpeg (sonra terminali yeniden açın)")
        all_ok = False

    return all_ok


def step_api_keys(env: dict):
    """Adım 2: API anahtarlarını topla ve doğrula."""
    header("ADIM 2/6 — API Anahtarları")

    # Gemini
    if is_set(env.get("GEMINI_API_KEY", "")) and validate_gemini(env["GEMINI_API_KEY"]):
        ok("Gemini anahtarı zaten tanımlı ve çalışıyor")
    else:
        console.print("\n  [bold]Gemini API anahtarı[/bold] (senaryo + konu üretimi, ücretsiz)")
        console.print("  Açılan sayfada 'Get API key' → 'Create API key' deyin:")
        open_browser("https://aistudio.google.com/apikey")
        while True:
            key = ask("Gemini anahtarını yapıştırın:")
            if not key:
                continue
            console.print("  ⏳ Test ediliyor...")
            if validate_gemini(key):
                ok("Gemini anahtarı geçerli!")
                env["GEMINI_API_KEY"] = key
                break
            fail("Anahtar çalışmadı — kopyaladığınızdan emin olup tekrar deneyin.")

    # ElevenLabs
    if is_set(env.get("ELEVENLABS_API_KEY", "")) and validate_elevenlabs(env["ELEVENLABS_API_KEY"]):
        ok("ElevenLabs anahtarı zaten tanımlı ve çalışıyor")
    else:
        console.print("\n  [bold]ElevenLabs API anahtarı[/bold] (seslendirme)")
        console.print("  Sol menü → Profil → API Keys → Create:")
        open_browser("https://elevenlabs.io/app/settings/api-keys")
        voices = []
        while True:
            key = ask("ElevenLabs anahtarını yapıştırın:")
            if not key:
                continue
            console.print("  ⏳ Test ediliyor...")
            voices = validate_elevenlabs(key)
            if voices:
                ok(f"ElevenLabs anahtarı geçerli! ({len(voices)} ses bulundu)")
                env["ELEVENLABS_API_KEY"] = key
                break
            fail("Anahtar çalışmadı — tekrar deneyin.")

        # Ses seçimi — otomatik listele
        if voices and not is_set(env.get("CHARACTER_VOICE_ID", "")):
            console.print("\n  [bold]Anlatıcı sesi seçin:[/bold]")
            for i, v in enumerate(voices[:10], 1):
                console.print(f"    {i}. {v.get('name', '?')}")
            while True:
                choice = ask(f"Numara girin (1-{min(len(voices), 10)}):")
                if choice.isdigit() and 1 <= int(choice) <= min(len(voices), 10):
                    selected = voices[int(choice) - 1]
                    env["CHARACTER_VOICE_ID"] = selected["voice_id"]
                    ok(f"Ses seçildi: {selected.get('name')}")
                    break

    # Replicate
    if is_set(env.get("REPLICATE_API_TOKEN", "")) and validate_replicate(env["REPLICATE_API_TOKEN"]):
        ok("Replicate token'ı zaten tanımlı ve çalışıyor")
    else:
        console.print("\n  [bold]Replicate API token[/bold] (görsel üretimi)")
        console.print("  'Create token' deyin:")
        open_browser("https://replicate.com/account/api-tokens")
        while True:
            key = ask("Replicate token'ını yapıştırın:")
            if not key:
                continue
            console.print("  ⏳ Test ediliyor...")
            if validate_replicate(key):
                ok("Replicate token'ı geçerli!")
                env["REPLICATE_API_TOKEN"] = key
                break
            fail("Token çalışmadı — tekrar deneyin.")

    save_env(env)


def step_youtube(env: dict) -> bool:
    """Adım 3: YouTube OAuth yetkilendirmesi."""
    header("ADIM 3/6 — YouTube Yetkilendirmesi")

    secrets_file = PROJECT_ROOT / "client_secrets.json"
    token_file = PROJECT_ROOT / "youtube_token.pickle"

    if not secrets_file.exists():
        console.print("""
  [bold]client_secrets.json gerekli.[/bold] Şu adımları izleyin (5 dk):

  1. Google Cloud Console'da yeni proje oluşturun (isim: what-if-bot)
  2. 'APIs & Services' → 'Library' → [bold]YouTube Data API v3[/bold] → Enable
  3. 'APIs & Services' → 'OAuth consent screen' → External → oluşturun
     (Test users kısmına kendi Gmail adresinizi ekleyin!)
  4. 'APIs & Services' → 'Credentials' → Create Credentials →
     [bold]OAuth client ID[/bold] → Application type: [bold]Desktop app[/bold]
  5. Oluşan client'ın JSON dosyasını indirin ve proje klasörüne
     [bold]client_secrets.json[/bold] adıyla kaydedin
""")
        open_browser("https://console.cloud.google.com/apis/credentials")
        ask("client_secrets.json dosyasını proje klasörüne koyduktan sonra ENTER'a basın")

        if not secrets_file.exists():
            fail("client_secrets.json hâlâ bulunamadı — bu adımı sonra tekrarlayın.")
            return False

    ok("client_secrets.json bulundu")

    # Eski scope'lu token varsa sil (v3'te force-ssl scope eklendi)
    if token_file.exists():
        console.print("  ♻ Mevcut token bulundu — yeni izinler için yenilenecek.")
        token_file.unlink()

    console.print("\n  🌐 Şimdi tarayıcı açılacak — YouTube kanalınızın bağlı olduğu")
    console.print("  Google hesabıyla giriş yapıp izinleri onaylayın.")
    console.print("  ('Google hasn't verified this app' uyarısı çıkarsa:")
    console.print("   Advanced → Go to what-if-bot (unsafe) deyin — kendi uygulamanız.)\n")
    ask("Hazır olduğunuzda ENTER'a basın")

    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.youtube_uploader import authenticate

    creds = authenticate()
    if creds and token_file.exists():
        ok("YouTube yetkilendirmesi tamamlandı! Token kaydedildi.")
        return True

    fail("Yetkilendirme tamamlanamadı — bu adımı sonra tekrarlayın.")
    return False


def step_telegram(env: dict):
    """Adım 4: Telegram botu kurulumu."""
    header("ADIM 4/6 — Telegram Botu")

    if is_set(env.get("TELEGRAM_BOT_TOKEN", "")) and is_set(env.get("TELEGRAM_CHAT_ID", "")):
        if validate_telegram_token(env["TELEGRAM_BOT_TOKEN"]):
            ok("Telegram zaten yapılandırılmış")
            return

    console.print("""
  1. Telegram'da [bold]@BotFather[/bold]'ı açın: https://t.me/BotFather
  2. [bold]/newbot[/bold] yazın
  3. Bota bir isim verin (ör: What-If Kanal Botu)
  4. Bir kullanıcı adı verin (sonu 'bot' ile bitmeli, ör: whatif_kanal_bot)
  5. BotFather'ın verdiği [bold]token[/bold]'ı kopyalayın
""")

    bot_username = ""
    while True:
        token = ask("Bot token'ını yapıştırın:")
        if not token:
            continue
        console.print("  ⏳ Test ediliyor...")
        bot_username = validate_telegram_token(token)
        if bot_username:
            ok(f"Bot bulundu: @{bot_username}")
            env["TELEGRAM_BOT_TOKEN"] = token
            break
        fail("Token çalışmadı — tekrar deneyin.")

    # Chat ID'yi otomatik yakala
    console.print(f"\n  Şimdi Telegram'da botunuza ([bold]@{bot_username}[/bold]) herhangi bir")
    console.print("  mesaj gönderin (ör: merhaba). Linki: " f"https://t.me/{bot_username}")
    ask("Mesajı gönderdikten sonra ENTER'a basın")

    chat_id = ""
    for _ in range(3):
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{env['TELEGRAM_BOT_TOKEN']}/getUpdates",
                timeout=20,
            ).json()
            results = r.get("result", [])
            if results:
                chat = results[-1].get("message", {}).get("chat", {})
                chat_id = str(chat.get("id", ""))
                if chat_id:
                    ok(f"Chat ID otomatik bulundu: {chat_id} ({chat.get('first_name', '')})")
                    break
        except Exception:
            pass
        warn("Mesaj görünmedi — botunuza mesaj attığınızdan emin olun.")
        ask("Tekrar denemek için ENTER'a basın")

    if not chat_id:
        chat_id = ask("Chat ID otomatik bulunamadı. Elle girin (@userinfobot'tan öğrenebilirsiniz):")

    env["TELEGRAM_CHAT_ID"] = chat_id
    save_env(env)

    # Test mesajı
    try:
        requests.post(
            f"https://api.telegram.org/bot{env['TELEGRAM_BOT_TOKEN']}/sendMessage",
            json={"chat_id": chat_id,
                  "text": "🐰 What-If Bot bağlandı! Kurulum tamamlanınca buradan bildirim alacaksınız. ✅"},
            timeout=20,
        )
        ok("Test mesajı gönderildi — telefonunuzu kontrol edin! 📲")
    except Exception:
        warn("Test mesajı gönderilemedi (kurulum yine de devam edebilir).")


def step_github_secrets(env: dict):
    """Adım 5: GitHub secret değerlerini hazırla ve göster."""
    header("ADIM 5/6 — GitHub Secret'ları")

    console.print("""
  Otomasyonun GitHub'da çalışması için aşağıdaki değerleri secret olarak
  ekleyeceksiniz. Açılan sayfada her biri için:
  [bold]New repository secret[/bold] → Name ve Secret alanlarını doldur → Add secret
""")

    secrets = {
        "GEMINI_API_KEY": env.get("GEMINI_API_KEY", ""),
        "ELEVENLABS_API_KEY": env.get("ELEVENLABS_API_KEY", ""),
        "CHARACTER_VOICE_ID": env.get("CHARACTER_VOICE_ID", ""),
        "REPLICATE_API_TOKEN": env.get("REPLICATE_API_TOKEN", ""),
        "TELEGRAM_BOT_TOKEN": env.get("TELEGRAM_BOT_TOKEN", ""),
        "TELEGRAM_CHAT_ID": env.get("TELEGRAM_CHAT_ID", ""),
    }

    secrets_path = PROJECT_ROOT / "client_secrets.json"
    token_path = PROJECT_ROOT / "youtube_token.pickle"
    if secrets_path.exists():
        secrets["YOUTUBE_CLIENT_SECRETS_B64"] = b64_file(secrets_path)
    if token_path.exists():
        secrets["YOUTUBE_TOKEN_B64"] = b64_file(token_path)

    # Değerleri dosyaya da yaz — kopyala-yapıştır kolaylığı
    # (İçinde gizli bilgiler var; .gitignore'daki github_secrets.txt deseni onu korur)
    out_file = PROJECT_ROOT / "github_secrets.txt"
    lines = ["GitHub → Settings → Secrets and variables → Actions → New repository secret",
             "Her satır: SECRET_ADI ile başlar, sonraki satır değeridir.", ""]
    for name, value in secrets.items():
        if value:
            lines += [f"### {name}", value, ""]
    out_file.write_text("\n".join(lines), encoding="utf-8")

    ok(f"Tüm secret değerleri dosyaya yazıldı: [bold]{out_file}[/bold]")
    console.print("  Bu dosyayı açın, her değeri GitHub'daki ilgili secret'a yapıştırın.")
    console.print("  [red]⚠ İşiniz bitince github_secrets.txt dosyasını SİLİN![/red]\n")

    open_browser("https://github.com/esracakalli1990-sketch/what-if-youtube-bot/settings/secrets/actions")
    ask("Secret'ların hepsini ekledikten sonra ENTER'a basın")


def step_final_check(env: dict, youtube_ok: bool):
    """Adım 6: Son kontrol."""
    header("ADIM 6/6 — Son Kontrol")

    checks = [
        ("Gemini", is_set(env.get("GEMINI_API_KEY", ""))),
        ("ElevenLabs", is_set(env.get("ELEVENLABS_API_KEY", ""))),
        ("Ses (Voice ID)", is_set(env.get("CHARACTER_VOICE_ID", ""))),
        ("Replicate", is_set(env.get("REPLICATE_API_TOKEN", ""))),
        ("YouTube yetkilendirme", youtube_ok),
        ("Telegram", is_set(env.get("TELEGRAM_BOT_TOKEN", "")) and is_set(env.get("TELEGRAM_CHAT_ID", ""))),
    ]

    all_ok = True
    for name, passed in checks:
        if passed:
            ok(name)
        else:
            fail(name)
            all_ok = False

    console.print()
    if all_ok:
        console.print(Panel(
            "[bold green]🎉 KURULUM TAMAMLANDI![/bold green]\n\n"
            "Sistem artık tam otonom:\n"
            "  • Her gün 1 Short, Pzt & Per uzun video üretilir\n"
            "  • Telegram'dan bildirim gelir, komutla yönetirsiniz\n\n"
            "İlk videoyu hemen denemek için Telegram botunuza şunu yazın:\n"
            "  [bold]/short[/bold]  (komutlar her saat :30'da işlenir)\n\n"
            "veya lokalden: [bold]python main.py --shorts \"What if the Moon vanished?\" --privacy public[/bold]",
            border_style="green",
        ))
    else:
        warn("Bazı adımlar eksik kaldı — sihirbazı tekrar çalıştırınca kaldığı yerden devam eder:")
        console.print("  [bold]python setup_wizard.py[/bold]")


# ──────────────────────────────────────
# Ana Akış
# ──────────────────────────────────────
def main():
    console.print(Panel(
        "[bold cyan]🐰 WHAT-IF YOUTUBE BOT — KURULUM SİHİRBAZI[/bold cyan]\n"
        "Sistemi aktifleştirmek için 6 adımı birlikte tamamlayacağız.\n"
        "Her adımda sadece istenen değeri yapıştırmanız yeterli.",
        border_style="bright_blue",
    ))

    if not step_dependencies():
        console.print("\n  Eksikleri kurup sihirbazı tekrar çalıştırın: [bold]python setup_wizard.py[/bold]")
        sys.exit(1)

    env = load_existing_env()
    step_api_keys(env)
    youtube_ok = step_youtube(env)
    step_telegram(env)
    step_github_secrets(env)
    step_final_check(env, youtube_ok)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n  Kurulum yarıda kesildi — tekrar çalıştırınca kaldığı yerden devam eder.")
        sys.exit(1)
