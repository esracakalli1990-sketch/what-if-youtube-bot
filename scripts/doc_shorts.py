"""
doc_shorts.py - Belgeselden dikey Shorts (1080×1920) üretimi.

    python -m scripts.doc_shorts <klasör> [--yukle] [--sadece kimlik]

Her Short, <klasör>/shorts.json'daki paragraf seçiminden yeniden kurgulanır:
- Ses: belgeselin önbellekteki ElevenLabs paragrafları (yeni kredi harcanmaz)
  + bölüm müziği + Gemini kliplerinin doğal sesi, -14 LUFS.
- Görüntü: aynı çekim planı (Ken Burns, film kesitleri, klipler) yatay çizilir,
  dikey kadraja yerleştirilir: bulanık arka plan + ortada geniş görüntü.
- Üstte kanca başlığı, ortada iri altyazı (kelime zamanlarından), sonda
  "Tam belgesel kanalda" çağrısı.
- Açıklamada tam belgesel bağlantısı ve bu Short'ta kullanılan görsel/film/
  müzik eserlerinin CC atıfları (lisans şartı).
Yükleme her zaman GİZLİ + planlı yayın (publish); hiçbir şey herkese açık yüklenmez.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

from scripts import doc_audio, doc_render, doc_timeline
from scripts.utils import PROJECT_ROOT, logger

W, H = 1080, 1920
FG_H = 760                     # ortadaki yatay görüntünün yüksekliği
FG_Y = 520
FONTS = PROJECT_ROOT / "assets" / "fonts"
CTA_SECONDS = 3.0


# ─────────────────────────────────────────────
# Saf yardımcılar
# ─────────────────────────────────────────────

def select_paragraphs(data: dict, keys: list[str]) -> list[tuple[int, int]]:
    """'ci.pi' anahtarlarını (bölüm, paragraf) çiftlerine çevir ve doğrula."""
    out = []
    for k in keys:
        ci, pi = (int(x) for x in k.split("."))
        if ci >= len(data["chapters"]) or pi >= len(data["chapters"][ci]["paragraphs"]):
            raise ValueError(f"Short paragrafı yok: {k}")
        out.append((ci, pi))
    return out


def caption_chunks(words: list[dict], offset: float, max_words: int = 3,
                   max_chars: int = 18) -> list[tuple[float, float, str]]:
    """Kelime zamanlarından kısa altyazı parçaları (Shorts tarzı: 2–3 kelime)."""
    chunks, cur = [], []
    for w in words:
        text = " ".join(x["word"] for x in cur + [w])
        if cur and (len(cur) >= max_words or len(text) > max_chars):
            chunks.append(cur)
            cur = []
        cur.append(w)
        if w["word"].endswith((".", "?", "!", ":")):
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return [(round(c[0]["start"] + offset, 3), round(c[-1]["end"] + offset, 3),
             " ".join(x["word"] for x in c)) for c in chunks]


def _ass_time(t: float) -> str:
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def ass_subtitles(chunks: list[tuple[float, float, str]]) -> str:
    """İri, kalın, siyah kenarlı altyazı; görüntünün hemen altında."""
    y = FG_Y + FG_H + 190
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n"
            "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, "
            "Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Alt,Source Sans 3 ExtraBold,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,"
            f"100,100,0,0,1,7,3,8,50,50,{y},1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    lines = [f"Dialogue: 0,{_ass_time(a)},{_ass_time(b)},Alt,,0,0,0,,{t}" for a, b, t in chunks]
    return head + "\n".join(lines) + "\n"


def short_description(spec: dict, full_url: str, credits: list[str], ai_note: str = "",
                      tags: list[str] | None = None) -> str:
    from scripts.social import hashtags
    parts = [spec.get("aciklama", "").strip(), "", f"▶️ Tam belgesel: {full_url}", ""]
    if ai_note:
        parts += [f"ℹ️ {ai_note}", ""]
    parts += [" ".join(hashtags(tags or [], limit=4) + ["#shorts"]), ""]
    if credits:
        parts += ["Kaynaklar ve lisanslar:"] + [f"• {c}" for c in dict.fromkeys(credits)]
    return "\n".join(parts)[:4900]


# ─────────────────────────────────────────────
# Üretim
# ─────────────────────────────────────────────

def build_short(prod, spec: dict, out_dir: Path) -> dict:
    """Tek bir Short: yatay kurgu → ses → dikey kompozisyon. Dosya yollarını döndürür."""
    data = prod.data
    pairs = select_paragraphs(data, spec["paragraflar"])
    audio_all = prod.audio_manifest()
    paras = [data["chapters"][ci]["paragraphs"][pi] for ci, pi in pairs]
    audio = [{**audio_all[ci][pi], "path": str(prod.build / audio_all[ci][pi]["path"])} for ci, pi in pairs]
    pseudo = {"title": spec["id"], "paragraphs": paras}
    layout = doc_timeline.layout_chapter(pseudo, [a["duration"] for a in audio])

    images = {k: str(prod.build / v["path"]) for k, v in prod.image_manifest().items()}
    videos = prod.video_manifest()
    stock = {k: str(prod.build / v["path"]) for k, v in videos["stock"].items()}
    films = {k: str(prod.build / v["path"]) for k, v in videos["films"].items()}
    shots = doc_timeline.chapter_shots(pseudo, audio, layout, images, prod.folder,
                                       stock_paths=stock, film_paths=films, kurgu=data.get("kurgu"))
    for s in shots:
        s["label"] = None            # dikey kadrajda alt bant okunmaz; bilgi altyazıda
    out_dir.mkdir(parents=True, exist_ok=True)
    wide = out_dir / f"{spec['id']}_yatay.mp4"
    doc_render.render_chapter([doc_render.Shot(**s) for s in shots], str(wide),
                              look=doc_render.Look(), fade_in=0.3, fade_out=0.0)

    # Ses: anlatım + müzik + doğal ses → master
    total = layout.total + CTA_SECONDS
    voice = out_dir / f"{spec['id']}_anlatim.wav"
    doc_audio.write_wav(doc_audio.place([(a["path"], t) for a, t in zip(audio, layout.para_starts)], total), voice)
    bed = doc_audio.sfx_bed(doc_audio.shot_sfx_events(shots), total)
    music_file = prod._music_for(spec.get("muzik"))
    if music_file:
        bed = bed + doc_audio.music_bed([(music_file, 0.0, total)], total, fade=2.0)
    music = None
    if np.abs(bed).max() > 0:
        music = out_dir / f"{spec['id']}_alt.wav"
        doc_audio.write_wav(np.clip(bed, -1, 1), music)
    master = doc_audio.master(voice, music, out_dir / f"{spec['id']}_ses.m4a")

    # Altyazı ve başlık
    chunks = []
    for a, start in zip(audio, layout.para_starts):
        chunks += caption_chunks(a["words"], start)
    ass = out_dir / f"{spec['id']}.ass"
    ass.write_text(ass_subtitles(chunks), encoding="utf-8")
    hook_lines = []
    for i, line in enumerate(spec["kanca"].split("\n")[:2]):
        p = out_dir / f"{spec['id']}_kanca{i}.txt"
        p.write_text(line, encoding="utf-8")
        hook_lines.append(p)
    cta = out_dir / "cta.txt"
    cta.write_text("Tam belgesel kanalda ▶", encoding="utf-8")

    final = out_dir / f"{spec['id']}.mp4"
    serif, sans = FONTS / "Cinzel-ExtraBold.ttf", FONTS / "SourceSans3-ExtraBold.ttf"
    hook_draw = "".join(
        f"drawtext=fontfile={serif}:textfile={p}:fontsize=66:fontcolor=0xF3ECDD:"
        f"x=(w-text_w)/2:y={250 + i * 92}:shadowcolor=black@0.85:shadowx=3:shadowy=3,"
        for i, p in enumerate(hook_lines))
    graph = (
        f"[0:v]split=2[a][b];"
        f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=28:2,"
        f"eq=brightness=-0.22:saturation=0.8[bg];"
        f"[b]scale=-2:{FG_H},crop={W}:{FG_H}[fg];"
        f"[bg][fg]overlay=0:{FG_Y},tpad=stop_mode=clone:stop_duration={CTA_SECONDS},"
        f"{hook_draw}"
        f"drawbox=x=(iw-160)/2:y=215:w=160:h=5:color=0xC9A45C:t=fill,"
        f"subtitles={ass}:fontsdir={FONTS},"
        f"drawtext=fontfile={sans}:textfile={cta}:fontsize=64:fontcolor=0xC9A45C:"
        f"x=(w-text_w)/2:y={FG_Y + FG_H + 60}:enable='gte(t,{layout.total - 0.5:.2f})':"
        f"box=1:boxcolor=black@0.55:boxborderw=22[v]"
    )
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wide), "-i", str(master),
                    "-filter_complex", graph, "-map", "[v]", "-map", "1:a", "-r", "30",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", str(final)],
                   check=True)

    used_images = {s["path"] for s in shots if s["kind"] == "image"}
    credits = []
    for v in prod.image_manifest().values():
        if str(prod.build / v["path"]) in used_images and v.get("credit", {}).get("title"):
            c = v["credit"]
            credits.append(f"{c['title'].removeprefix('File:').rsplit('.', 1)[0]} — "
                           f"{c.get('artist', '')} ({c.get('license', '')}), Wikimedia Commons")
    used = {s["path"] for s in shots}
    for v in videos["films"].values():
        if str(prod.build / v["path"]) in used:
            c = v["credit"]
            credits.append(f"Video: {c['title'].removeprefix('File:').rsplit('.', 1)[0]} — "
                           f"{c['artist']} ({c['license']}), Wikimedia Commons")
    if any(str(prod.build / v["path"]) in used for v in videos["stock"].values()):
        credits.append("Video: Pexels")
    if music_file:
        m = videos["music"].get(spec.get("muzik"), {}).get("credit")
        if m:
            from scripts.doc_pipeline import _track_name
            credits.append(f"Müzik: \"{_track_name(m['title'])}\" — {m['artist']} ({m['license']})")
    uses_clip = any("klipler" in s["path"] for s in shots)
    return {"id": spec["id"], "video": str(final), "seconds": round(total, 1),
            "credits": credits, "uses_clip": uses_clip}


def main(argv=None):
    from scripts.doc_pipeline import Production
    ap = argparse.ArgumentParser(description="Belgeselden dikey Shorts")
    ap.add_argument("klasor")
    ap.add_argument("--yukle", action="store_true", help="YouTube'a gizli + planlı yükle")
    ap.add_argument("--sadece", default=None, help="yalnızca bu Short kimliği")
    ap.add_argument("--sosyal", action="store_true",
                    help="TikTok/Instagram/Facebook paketi de hazırla (build/sosyal)")
    args = ap.parse_args(argv)
    folder = Path(args.klasor).resolve()
    cfg = json.loads((folder / "shorts.json").read_text(encoding="utf-8"))
    prod = Production(str(folder))
    prod.stage_gorseller()            # önbellekte olanlar yeniden inmez; videos.json yenilenir
    out_dir = prod.build / "shorts"
    results = []
    for spec in cfg["shorts"]:
        if args.sadece and spec["id"] != args.sadece:
            continue
        r = build_short(prod, spec, out_dir)
        if args.yukle:
            from scripts.youtube_uploader import upload_documentary, last_upload_error
            when = datetime.fromisoformat(spec["yayin"].replace("Z", "+00:00"))
            desc = short_description(spec, cfg["tam_video"], r["credits"],
                                     prod.data.get("ai_disclosure", "") if r["uses_clip"] else "",
                                     cfg.get("etiketler", []))
            vid = upload_documentary(r["video"], spec["baslik"], desc, cfg.get("etiketler", []),
                                     publish_at=when, synthetic_media=r["uses_clip"])
            if not vid:
                raise RuntimeError(f"{spec['id']} yüklenemedi: {last_upload_error().get('message')}")
            r.update(url=f"https://youtu.be/{vid}", yayin=spec["yayin"])
        results.append(r)
        logger.info("Short hazır: %s (%.0f sn)", r["id"], r["seconds"])
    (out_dir / "shorts.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    if args.sosyal:
        from scripts.social import package
        package(folder, cfg, results, prod.data.get("ai_disclosure", ""))
    print(json.dumps(results, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
