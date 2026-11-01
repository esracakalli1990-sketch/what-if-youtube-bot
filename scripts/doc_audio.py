"""
doc_audio.py - Belgesel anlatım sesi: üretim, zaman damgaları, miksaj, mastering.

- Paragraf başına ElevenLabs isteği; önceki/sonraki paragraf metni bağlam olarak
  gider, böylece ton paragraftan paragrafa kopmaz.
- Kelime zaman damgaları (kesme noktaları ve altyazı için) kaydedilir.
- Üretilen her paragraf diske yazılır; tekrar çalıştırmada kredi harcanmaz.
- ElevenLabs yoksa/kota bittiyse edge-tts Türkçe ses (tr-TR-AhmetNeural) yedeği.
  Bir videoda tek motor kullanılır (yarısı bir ses, yarısı başka ses olmaz).
- Mastering: anlatım zinciri + müzik alçaltma (sidechain) + -14 LUFS.
"""

import asyncio
import base64
import hashlib
import json
import re
import subprocess
from pathlib import Path

import numpy as np

from scripts.utils import logger

SR = 48000
ELEVEN_MODEL = "eleven_multilingual_v2"
# 128 kbps her ElevenLabs paketinde var (192 kbps yalnızca Creator ve üstü);
# ses zaten mastering'de 320k AAC'ye çevriliyor.
ELEVEN_FORMAT = "mp3_44100_128"
EDGE_VOICE = "tr-TR-AhmetNeural"
SENTENCE_END = re.compile(r"[.!?…:]['\"”’)]*$")


class TTSError(Exception):
    pass


# ─────────────────────────────────────────────
# Metin hazırlığı
# ─────────────────────────────────────────────

def apply_pronunciations(text: str, pronunciations: dict) -> str:
    """
    Seslendirme metninde zor adları okunuşlarıyla değiştir.

    Okunuş tek kelime olmalı (boşluksuz; tire serbest): altyazı, kelime
    sırasıyla eşlendiği için kelime sayısı değişmemeli.
    """
    # Uzun anahtar önce: "Hattuşili" kuralı "Hattuşa"dan önce uygulanmalı.
    # Ekler ("Hattuşa'nın", "Hattuşa'da") korunur: yalnızca kelime başı eşlenir.
    for word in sorted(pronunciations, key=len, reverse=True):
        spoken = pronunciations[word]
        if " " in spoken.strip():
            raise ValueError(f"Okunuş tek kelime olmalı: {word!r} → {spoken!r}")
        text = re.sub(rf"(?<!\w){re.escape(word)}", spoken, text)
    return text


def words_from_alignment(alignment: dict, display_text: str) -> list[dict]:
    """
    ElevenLabs karakter hizalamasından kelime zamanları üret.

    Kelime metni seslendirilen metin yerine ekranda gösterilecek (orijinal)
    metinden alınır; okunuş değişikliği kelime sayısını korur.
    """
    chars = alignment.get("characters", [])
    starts = alignment.get("character_start_times_seconds", [])
    ends = alignment.get("character_end_times_seconds", [])
    spans, cur = [], None
    for ch, s, e in zip(chars, starts, ends):
        if ch.isspace():
            if cur:
                spans.append(cur)
                cur = None
            continue
        if cur is None:
            cur = [s, e]
        else:
            cur[1] = e
    if cur:
        spans.append(cur)
    shown = display_text.split()
    if len(shown) != len(spans):
        logger.warning("Kelime sayısı uyuşmuyor (gösterilen %d, hizalanan %d); "
                       "hizalanan metin kullanılıyor", len(shown), len(spans))
        shown = "".join(chars).split()
    return [{"word": w, "start": round(s, 3), "end": round(e, 3)}
            for w, (s, e) in zip(shown, spans)]


def sentence_starts(words: list[dict]) -> list[int]:
    """Cümle başlarındaki kelimelerin indeksleri (ilk kelime dahil)."""
    idx = [0] if words else []
    for i in range(1, len(words)):
        if SENTENCE_END.search(words[i - 1]["word"]):
            idx.append(i)
    return idx


# ─────────────────────────────────────────────
# Ses üretimi
# ─────────────────────────────────────────────

def _probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True)
    return float(out.stdout.strip() or 0)


def _eleven_paragraph(client, voice_id: str, text: str, prev_text: str, next_text: str,
                      voice_settings: dict | None):
    from elevenlabs import VoiceSettings
    settings = VoiceSettings(**(voice_settings or {
        "stability": 0.55, "similarity_boost": 0.8, "style": 0.1, "use_speaker_boost": True,
    }))
    resp = client.text_to_speech.convert_with_timestamps(
        voice_id=voice_id, text=text, model_id=ELEVEN_MODEL,
        previous_text=prev_text or None, next_text=next_text or None,
        voice_settings=settings, output_format=ELEVEN_FORMAT,
    )
    data = resp.model_dump() if hasattr(resp, "model_dump") else dict(resp)
    audio = base64.b64decode(data["audio_base_64"])
    alignment = data.get("normalized_alignment") or data.get("alignment") or {}
    return audio, alignment


async def _edge_paragraph(text: str, voice: str, mp3_path: Path) -> list[dict]:
    import edge_tts
    comm = edge_tts.Communicate(text, voice, boundary="WordBoundary")
    words = []
    with open(mp3_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7
                words.append({"word": chunk["text"], "start": round(start, 3),
                              "end": round(start + chunk["duration"] / 1e7, 3)})
    return words


# ElevenLabs çok dilli modeli uzun paragraflarda bazen birkaç saniye hızlanır.
# Kelime zamanlarından konuşma hızı ölçülür; normalden belirgin hızlı paragraflar
# daha "sabit" ayarla yeniden seslendirilir (yalnızca onlar → az kredi).
RUSH_WINDOW = 6            # kelime
RUSH_LIMIT = 1.30          # pencere hızı / genel ortanca hız
STEADY_SETTINGS = {"stability": 0.8, "similarity_boost": 0.8, "style": 0.0,
                   "use_speaker_boost": True, "speed": 0.95}


def elevenlabs_balance(api_key: str) -> dict | None:
    """Hesabın paket ve kalan karakter bilgisi (API anahtarının ait olduğu hesap)."""
    try:
        from elevenlabs import ElevenLabs
        sub = ElevenLabs(api_key=api_key).user.subscription.get()
        return {"tier": sub.tier, "used": sub.character_count, "limit": sub.character_limit}
    except Exception as e:      # rapor içindir; üretimi durdurmaz
        logger.warning("ElevenLabs bakiyesi okunamadı: %s", e)
        return None


def window_rates(words: list[dict], k: int = RUSH_WINDOW, min_span: float = 1.2) -> list[float]:
    """Ardışık k kelimelik pencerelerde saniyedeki harf sayısı."""
    rates = []
    for i in range(len(words) - k + 1):
        w = words[i:i + k]
        span = w[-1]["end"] - w[0]["start"]
        if span >= min_span:
            rates.append(sum(len(x["word"]) for x in w) / span)
    return rates


def rush_score(words: list[dict], ref_rate: float) -> float:
    """Paragraftaki en hızlı pencerenin genel ortanca hıza oranı (1.0 = normal)."""
    rates = window_rates(words)
    return round(max(rates) / ref_rate, 3) if rates and ref_rate > 0 else 0.0


def reference_rate(all_words: list[list[dict]]) -> float:
    rates = [r for w in all_words for r in window_rates(w)]
    return float(np.median(rates)) if rates else 0.0


def synthesize(paragraphs: list[str], out_dir: Path, voice_id: str = "",
               api_key: str = "", pronunciations: dict | None = None,
               engine: str = "auto", voice_settings: dict | None = None,
               rush_budget: int = 0) -> list[dict]:
    """
    Paragrafları seslendir. Sonuç: [{"path", "duration", "words", "engine"}].

    engine: "auto" (ElevenLabs, olmazsa edge), "elevenlabs", "edge".
    Diskte hazır olan paragraflar yeniden üretilmez (kredi koruması).
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pronunciations = pronunciations or {}
    requested = engine
    if requested == "elevenlabs" and not (voice_id and api_key):
        raise TTSError("ElevenLabs zorunlu ama ses kimliği (TTS_VOICE_ID_TR) ya da "
                       "API anahtarı (ELEVENLABS_API_KEY) eksik")
    meta_path = out_dir / "engine.json"
    if (meta_path.exists() and engine != "edge" and voice_id and api_key
            and json.loads(meta_path.read_text())["engine"] == "edge"):
        # Önbellekte ücretsiz yedek ses var ama ElevenLabs artık kullanılabilir:
        # yedek kayıtlar atılır, tüm video ElevenLabs ile baştan seslendirilir.
        logger.info("Önbellekteki edge-tts sesi atılıyor; ElevenLabs ile yeniden üretilecek")
        for words_path in out_dir.glob("p*.json"):
            if isinstance(json.loads(words_path.read_text(encoding="utf-8")), dict):
                words_path.unlink()
                words_path.with_suffix(".mp3").unlink(missing_ok=True)
        meta_path.unlink()
    if meta_path.exists():
        engine = json.loads(meta_path.read_text())["engine"]  # tek motor kuralı
    elif engine == "auto":
        engine = "elevenlabs" if (voice_id and api_key) else "edge"

    client = None
    if engine == "elevenlabs":
        from elevenlabs import ElevenLabs
        client = ElevenLabs(api_key=api_key)

    spoken = [apply_pronunciations(p, pronunciations) for p in paragraphs]
    results = []
    for i, text in enumerate(paragraphs):
        mp3 = out_dir / f"p{i:03d}.mp3"
        words_path = out_dir / f"p{i:03d}.json"
        # Önbellek metnin parmak iziyle geçerli: paragraf düzeltilirse yalnızca
        # o paragraf yeniden seslendirilir (komşuların bağlamı için yeniden üretim yok).
        fp = hashlib.sha1(f"{engine}|{voice_id}|{spoken[i]}".encode("utf-8")).hexdigest()[:16]
        cached = json.loads(words_path.read_text(encoding="utf-8")) if words_path.exists() else None
        new = False
        if isinstance(cached, dict) and cached.get("fp") == fp and mp3.exists():
            words = cached["words"]
        elif isinstance(cached, list) and mp3.exists():
            words = cached          # parmak izi olmayan elle hazırlanmış ses (test/kayıt)
        elif engine == "elevenlabs":
            try:
                audio, alignment = _eleven_paragraph(
                    client, voice_id, spoken[i],
                    spoken[i - 1] if i > 0 else "",
                    spoken[i + 1] if i + 1 < len(spoken) else "",
                    voice_settings)
            except Exception as e:
                if requested == "elevenlabs":
                    # Belgeselde robot sese düşmek yok: dur ve gerçek hatayı göster
                    raise TTSError(f"ElevenLabs hatası (paragraf {i}): {e}") from e
                if i == 0 and not any(out_dir.glob("p*.mp3")):
                    logger.warning("ElevenLabs kullanılamadı (%s) — tüm video edge-tts ile", e)
                    return synthesize(paragraphs, out_dir, pronunciations=pronunciations,
                                      engine="edge")
                raise TTSError(f"ElevenLabs paragraf {i} hatası (video yarıda; "
                               f"karışık ses olmasın diye durduruldu): {e}") from e
            mp3.write_bytes(audio)
            words = words_from_alignment(alignment, text)
            new = True
        else:
            words = asyncio.run(_edge_paragraph(spoken[i], EDGE_VOICE, mp3))
            shown = text.split()
            if len(shown) == len(words):
                for w, s in zip(words, shown):
                    w["word"] = s
        if not isinstance(cached, list):
            words_path.write_text(json.dumps({"fp": fp, "words": words}, ensure_ascii=False),
                                  encoding="utf-8")
        if not meta_path.exists():
            meta_path.write_text(json.dumps({"engine": engine}))
        results.append({"path": str(mp3), "duration": _probe_duration(mp3),
                        "words": words, "engine": engine, "new": new,
                        "chars": len(spoken[i])})
        logger.info("Ses p%03d hazır (%.1f sn, %s)", i, results[-1]["duration"], engine)
    if engine == "elevenlabs" and rush_budget > 0:
        _repair_rushes(results, paragraphs, spoken, out_dir, client, voice_id, rush_budget)
    return results


def _repair_rushes(results, paragraphs, spoken, out_dir, client, voice_id, budget: int):
    """Hızlanan paragrafları sabit ayarla yeniden seslendir (en fazla `budget` karakter)."""
    ref = reference_rate([r["words"] for r in results])
    report, used = [], 0
    for i, r in enumerate(results):
        words_path = out_dir / f"p{i:03d}.json"
        meta = json.loads(words_path.read_text(encoding="utf-8"))
        if not isinstance(meta, dict):
            continue
        score = rush_score(r["words"], ref)
        if score <= RUSH_LIMIT or meta.get("repaired"):
            continue
        if used + len(spoken[i]) > budget:
            report.append({"p": i, "rush": score, "durum": "bütçe yetmedi"})
            continue
        used += len(spoken[i])
        try:
            audio, alignment = _eleven_paragraph(
                client, voice_id, spoken[i], spoken[i - 1] if i > 0 else "",
                spoken[i + 1] if i + 1 < len(spoken) else "", STEADY_SETTINGS)
        except Exception as e:
            report.append({"p": i, "rush": score, "durum": f"hata: {e}"})
            continue
        new_words = words_from_alignment(alignment, paragraphs[i])
        new_score = rush_score(new_words, ref)
        mp3 = Path(r["path"])
        if new_score < score:
            mp3.write_bytes(audio)
            r.update(words=new_words, duration=_probe_duration(mp3))
            meta.update(words=new_words)
        meta["repaired"] = True          # bir daha denenmez (kredi koruması)
        words_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        report.append({"p": i, "rush": score, "yeni": new_score,
                       "durum": "düzeltildi" if new_score < score else "eskisi kaldı"})
        logger.info("Hızlanma düzeltmesi p%03d: %.2f → %.2f", i, score, new_score)
    (out_dir / "hiz_raporu.json").write_text(json.dumps(
        {"ortanca_hiz": round(ref, 2), "sinir": RUSH_LIMIT, "kullanilan_karakter": used,
         "paragraflar": report}, ensure_ascii=False, indent=1), encoding="utf-8")


# ─────────────────────────────────────────────
# Zaman çizelgesi üzerine ses yerleştirme
# ─────────────────────────────────────────────

def decode(path: str, sr: int = SR) -> np.ndarray:
    """Ses dosyasını mono float32 dizisine çöz."""
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1",
         "-ar", str(sr), "-"], capture_output=True, check=True)
    return np.frombuffer(out.stdout, np.float32)


def write_wav(samples: np.ndarray, path: Path, sr: int = SR):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1",
         "-i", "-", "-c:a", "pcm_s24le", str(path)],
        input=samples.astype(np.float32).tobytes(), check=True)


def place(clips: list[tuple[str, float]], total: float, sr: int = SR) -> np.ndarray:
    """[(dosya, başlangıç_sn)] seslerini toplam süreli sessiz bir izde yerine koy."""
    buf = np.zeros(int(round(total * sr)), np.float32)
    for path, start in clips:
        s = decode(path, sr)
        a = int(round(start * sr))
        n = min(len(s), len(buf) - a)
        if n > 0:
            buf[a:a + n] += s[:n]
    return buf


BED_RMS_DB = -20.0   # müzik ve doğal sesler bu ortalama seviyeye eşitlenir (master'da ayrıca kısılır)


def normalize_rms(x: np.ndarray, target_db: float = BED_RMS_DB, floor: float = 1e-4) -> np.ndarray:
    """Sesi, duyulur kısımlarının ortalama gücüne göre hedef seviyeye getir.
    Parçalar çok farklı kayıt seviyelerinde olabilir (yüksek masterlanmış müzik ↔ sessiz klip)."""
    if not len(x):
        return x
    frame = 2048
    n = len(x) // frame * frame
    rms = np.sqrt(np.mean(x[:n].reshape(-1, frame) ** 2, axis=1)) if n else np.array([np.sqrt(np.mean(x ** 2))])
    audible = rms[rms > floor]
    if not len(audible):
        return x * 0.0
    level = float(np.sqrt(np.mean(audible ** 2)))
    out = x * (10 ** (target_db / 20) / level)
    return np.clip(out, -1.0, 1.0)


def _fade(seg: np.ndarray, seconds: float, sr: int) -> np.ndarray:
    f = min(int(seconds * sr), len(seg) // 2)
    if f:
        ramp = np.linspace(0, 1, f, dtype=np.float32)
        seg[:f] *= ramp
        seg[-f:] *= ramp[::-1]
    return seg


def music_bed(segments: list[tuple[str | None, float, float]], total: float,
              fade: float = 4.0, sr: int = SR) -> np.ndarray:
    """
    Bölüm müziklerinden tek iz: [(dosya|None, başlangıç, süre)].
    Her parça aynı seviyeye eşitlenir; kısa kalırsa döngüye alınır; bölüm
    sınırlarında yavaş açılıp kapanır (belgesel tarzı, ani giriş yok).
    """
    buf = np.zeros(int(round(total * sr)), np.float32)
    for path, start, dur in segments:
        if not path:
            continue
        src = normalize_rms(decode(path, sr))
        if not len(src):
            continue
        n = int(round(dur * sr))
        reps = int(np.ceil(n / len(src)))
        seg = _fade(np.tile(src, reps)[:n].copy(), fade, sr)
        a = int(round(start * sr))
        m = min(n, len(buf) - a)
        buf[a:a + m] += seg[:m]
    return buf


def decode_span(path: str, start: float, duration: float, sr: int = SR) -> np.ndarray:
    """Videonun/sesin belirli bir aralığındaki sesi (ses izi yoksa boş dizi)."""
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{duration:.3f}", "-i", str(path),
         "-vn", "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"], capture_output=True)
    return np.frombuffer(out.stdout, np.float32) if out.returncode == 0 else np.zeros(0, np.float32)


def sfx_bed(events: list[tuple[str, float, float, float]], total: float,
            level_db: float = BED_RMS_DB + 2, fade: float = 0.5, sr: int = SR) -> np.ndarray:
    """
    Doğal ses izi: [(video, videodaki başlangıç, zaman çizelgesindeki yer, süre)].
    Her klibin sesi eşitlenir, kenarları yumuşatılır. Anlatım altında master'daki
    sidechain ile müzikle birlikte alçalır.
    """
    buf = np.zeros(int(round(total * sr)), np.float32)
    for path, src_start, at, dur in events:
        seg = decode_span(path, src_start, dur, sr)
        if not len(seg):
            continue
        seg = _fade(normalize_rms(seg.copy(), level_db), fade, sr)
        a = int(round(at * sr))
        m = min(len(seg), len(buf) - a)
        if m > 0:
            buf[a:a + m] += seg[:m]
    return buf


# ─────────────────────────────────────────────
# Mastering
# ─────────────────────────────────────────────

VOICE_CHAIN = ("highpass=f=70,"
               "deesser=i=0.4:m=0.5:f=0.5,"
               "acompressor=threshold=-20dB:ratio=3:attack=15:release=250:makeup=2")


def _loudnorm_measure(path: Path, chain: str) -> dict:
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af",
         f"{chain}loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", out.stderr, re.S)
    if not m:
        raise RuntimeError("loudnorm ölçümü okunamadı")
    return json.loads(m.group(0))


def master(voice_wav: Path, music_wav: Path | None, out_path: Path,
           music_level: float = 0.16) -> Path:
    """
    Anlatım + müzik → -14 LUFS, en fazla -1.5 dBTP, AAC 320k/48k.
    Müzik, anlatım sırasında sidechain sıkıştırmayla kendiliğinden alçalır.
    """
    out_path = Path(out_path)
    mix_wav = out_path.with_suffix(".mix.wav")
    if music_wav:
        graph = (f"[0:a]{VOICE_CHAIN},asplit=2[v][sc];"
                 f"[1:a]volume={music_level}[m];"
                 "[m][sc]sidechaincompress=threshold=0.03:ratio=8:attack=40:release=600[md];"
                 "[v][md]amix=inputs=2:duration=first:normalize=0[out]")
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(voice_wav), "-i", str(music_wav),
               "-filter_complex", graph, "-map", "[out]", "-c:a", "pcm_s24le", str(mix_wav)]
    else:
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(voice_wav), "-af", VOICE_CHAIN,
               "-c:a", "pcm_s24le", str(mix_wav)]
    subprocess.run(cmd, check=True)
    m = _loudnorm_measure(mix_wav, "")
    ln = ("loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:"
          f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
          f"offset={m['target_offset']}")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mix_wav), "-af", ln,
                    "-ar", str(SR), "-ac", "2", "-c:a", "aac", "-b:a", "320k", str(out_path)], check=True)
    mix_wav.unlink(missing_ok=True)
    return out_path


def measure_lufs(path: Path) -> float:
    """Entegre ses yüksekliği (LUFS) — doğrulama için."""
    return float(_loudnorm_measure(Path(path), "")["input_i"])
