"""
doc_pipeline.py - Türkçe tarih belgeseli üretim hattı (aşamalı).

    python -m scripts.doc_pipeline belgeseller/01-hititler <aşama> [--bolum N]

Aşamalar (her biri bir öncekinin çıktısını <klasör>/build/ altından okur;
GitHub Actions'ta ayrı işlerde, bölümler paralel çalışabilir):

    ses        Tüm paragrafları seslendir (bağlamlı, önbellekli)
    gorseller  Arşiv görsellerini indir, lisansları kaydet
    kartlar    Remotion ile bölüm kartları ve 3 kapak
    bolum      Bölüm(ler)i 1440p render et (--bolum N ile tek bölüm)
    birlestir  Bölümleri birleştir, ses mastering, altyazı, açıklama
    yukle      YouTube'a GİZLİ yükle (--yayin ile planlı yayın)
    hepsi      yukle hariç tümü sırayla
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from scripts import doc_audio, doc_render, doc_timeline
from scripts.archive_images import fetch_images
from scripts.utils import load_env, logger, PROJECT_ROOT

REMOTION_DIR = PROJECT_ROOT / "remotion"
MUSIC_DIR = PROJECT_ROOT / "assets" / "music"
LOCAL_CHROMIUM = Path("/opt/pw-browsers/chromium")


def _env(name: str) -> str:
    """.env dosyasını yükle ve değişkeni oku (load_env sabit anahtar listesi döndürür)."""
    load_env()
    return os.getenv(name, "").strip()


class Production:
    def __init__(self, folder: str, sample: int | None = None):
        """sample=N: yalnızca ilk N bölümle "örnek" üret (kalite onayı için;
        tüm videoya ses kredisi harcanmaz). Ses önbelleği tam üretimle ortak."""
        self.folder = Path(folder).resolve()
        self.data = doc_timeline.load_scenario(self.folder)
        self.sample = sample
        if sample:
            self.data = {**self.data, "chapters": self.data["chapters"][:sample]}
        self.build = self.folder / "build"
        self.build.mkdir(exist_ok=True)
        self.final_name = "ornek.mp4" if sample else "final.mp4"

    # ── yardımcılar ──────────────────────────
    def path(self, *parts) -> Path:
        p = self.build.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def paragraphs(self) -> list[tuple[int, int, str]]:
        return [(ci, pi, p["text"]) for ci, ch in enumerate(self.data["chapters"])
                for pi, p in enumerate(ch["paragraphs"])]

    def _manifest_name(self) -> str:
        return "manifest-ornek.json" if self.sample else "manifest.json"

    def audio_manifest(self) -> list[list[dict]]:
        return json.loads(self.path("audio", self._manifest_name()).read_text(encoding="utf-8"))

    def image_manifest(self) -> dict:
        return json.loads(self.path("images", "manifest.json").read_text(encoding="utf-8"))

    def layouts(self) -> list[doc_timeline.ChapterLayout]:
        audio = self.audio_manifest()
        return [doc_timeline.layout_chapter(ch, [a["duration"] for a in audio[ci]])
                for ci, ch in enumerate(self.data["chapters"])]

    # ── aşamalar ─────────────────────────────
    def stage_ses(self):
        flat = self.paragraphs()
        results = doc_audio.synthesize(
            [t for _, _, t in flat], self.path("audio", "x").parent,
            voice_id=_env("TTS_VOICE_ID_TR"),
            api_key=_env("ELEVENLABS_API_KEY"),
            pronunciations=self.data.get("pronunciations", {}),
            engine=os.getenv("DOC_TTS_ENGINE", "auto"),
            voice_settings=self.data.get("voice_settings"),
        )
        manifest = [[] for _ in self.data["chapters"]]
        for (ci, _, _), r in zip(flat, results):
            r = {**r, "path": str(Path(r["path"]).relative_to(self.build))}
            manifest[ci].append(r)
        self.path("audio", self._manifest_name()).write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        total = sum(l.total for l in self.layouts())
        logger.info("Ses hazır: %d paragraf, toplam video ~%.1f dk", len(results), total / 60)

    def stage_gorseller(self):
        specs = {k: ({**v, "file": str(self.folder / v["file"])} if v.get("file") else v)
                 for k, v in self.data["images"].items()}   # yerel dosyalar senaryo klasörüne göre
        result = fetch_images(specs, self.path("images", "x").parent)
        manifest = {k: {"path": os.path.relpath(Path(v["path"]).resolve(), self.build),
                        "credit": v["credit"]} for k, v in result.items()}
        self.path("images", "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def _remotion(self, args: list[str]):
        cmd = ["npx", "remotion", *args]
        if LOCAL_CHROMIUM.exists():
            cmd += [f"--browser-executable={LOCAL_CHROMIUM}"]
        subprocess.run(cmd, cwd=REMOTION_DIR, check=True)

    def _stage_image(self, key: str) -> str:
        """Görseli Remotion public/ klasörüne kopyala, dosya adını döndür."""
        if not key:
            return ""
        src = self.build / self.image_manifest()[key]["path"]
        public = REMOTION_DIR / "public"
        for font in (PROJECT_ROOT / "assets" / "fonts").glob("*.ttf"):
            shutil.copy2(font, public / font.name)
        shutil.copy2(src, public / src.name)
        return src.name

    def stage_kartlar(self):
        for ci, ch in enumerate(self.data["chapters"]):
            card = ch.get("card")
            if not card:
                continue
            props = {"kicker": card.get("kicker", ""), "title": ch["title"],
                     "date": card.get("date", ""), "image": self._stage_image(card.get("image", ""))}
            self._remotion(["render", "src/index.ts", "ChapterCard",
                            str(self.path("cards", f"c{ci:02d}.mp4")),
                            f"--props={json.dumps(props, ensure_ascii=False)}", "--crf=16"])
        for name, props in self.data.get("maps", {}).items():
            props = {**props, "image": self._stage_image(props.get("image", ""))}
            self._remotion(["render", "src/index.ts", "MapMoves",
                            str(self.path("maps", f"{name}.mp4")),
                            f"--props={json.dumps(props, ensure_ascii=False)}", "--crf=16"])
        for ti, th in enumerate(self.data.get("thumbnails", [])):
            props = {"image": self._stage_image(th.get("image", "")), "line1": th.get("line1", ""),
                     "line2": th.get("line2", ""), "badge": th.get("badge", "TAM HİKÂYE"),
                     "focusX": th.get("focus_x", 0.6)}
            self._remotion(["still", "src/index.ts", "Thumbnail",
                            str(self.path("thumbs", f"kapak{ti + 1}.jpg")),
                            f"--props={json.dumps(props, ensure_ascii=False)}",
                            "--image-format=jpeg", "--jpeg-quality=90"])

    def stage_bolum(self, only: int | None = None):
        audio = self.audio_manifest()
        images = {k: str(self.build / v["path"]) for k, v in self.image_manifest().items()}
        layouts = self.layouts()
        look = doc_render.Look()
        for ci, ch in enumerate(self.data["chapters"]):
            if only is not None and ci != only:
                continue
            card = self.path("cards", f"c{ci:02d}.mp4")
            shots = doc_timeline.chapter_shots(
                ch, audio[ci], layouts[ci], images, self.folder,
                card_clip=str(card) if ch.get("card") else None)
            fades = dict(fade_in=0.0 if ch.get("card") else 0.6)
            doc_render.render_chapter([doc_render.Shot(**s) for s in shots],
                                      str(self.path("chapters", f"c{ci:02d}.mp4")),
                                      look=look, **fades)

    def stage_birlestir(self):
        chapters = self.data["chapters"]
        layouts = self.layouts()
        audio = self.audio_manifest()
        starts, t = [], 0.0
        for lay in layouts:
            starts.append(round(t, 3))
            t += lay.total
        total = t

        listing = self.path("chapters", "liste.txt")
        listing.write_text("".join(f"file 'c{ci:02d}.mp4'\n" for ci in range(len(chapters))))

        # Ses: paragraflar zaman çizelgesindeki yerlerine
        clips, cues = [], []
        for ci, lay in enumerate(layouts):
            for pi, a in enumerate(audio[ci]):
                at = starts[ci] + lay.para_starts[pi]
                clips.append((str(self.build / a["path"]), at))
                cues += doc_timeline.subtitle_cues(a["words"], offset=at)
        voice = self.path("ses", "anlatim.wav")
        doc_audio.write_wav(doc_audio.place(clips, total), voice)
        segments = [(self._music_for(ch.get("music")), starts[ci], layouts[ci].total)
                    for ci, ch in enumerate(chapters)]
        music = None
        if any(s[0] for s in segments):
            music = self.path("ses", "muzik.wav")
            doc_audio.write_wav(doc_audio.music_bed(segments, total), music)
        mastered = doc_audio.master(voice, music, self.path("ses", "master.m4a"))

        # Bölümler aynı kodlayıcı ayarıyla üretildi: yeniden kodlamadan birleştir ve
        # sesi tek adımda ekle (ara kopya yok — Actions diskinde yer sınırlı)
        final = self.path(self.final_name)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                        "-i", str(listing), "-i", str(mastered), "-map", "0:v", "-map", "1:a",
                        "-c", "copy", "-movflags", "+faststart", str(final)], check=True)
        if self.sample:
            logger.info("Örnek hazır: %s (%.1f dk, %.1f LUFS)", final, total / 60,
                        doc_audio.measure_lufs(final))
            return
        doc_timeline.write_srt(cues, self.path("altyazi.srt"))
        chapters_text = doc_timeline.youtube_chapters([c["title"] for c in chapters], starts)
        self.path("aciklama.txt").write_text(self.description(chapters_text), encoding="utf-8")
        meta = {"total_seconds": total, "chapter_starts": starts,
                "lufs": doc_audio.measure_lufs(final), "music": bool(music)}
        self.path("ozet.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        logger.info("Belgesel hazır: %s (%.1f dk, %.1f LUFS)", final, total / 60, meta["lufs"])

    def _music_for(self, mood: str | None) -> str | None:
        if not mood or not MUSIC_DIR.exists():
            return None
        files = sorted(MUSIC_DIR.glob(f"{mood}*.mp3")) + sorted(MUSIC_DIR.glob(f"{mood}*.wav"))
        return str(files[0]) if files else None

    def description(self, chapters_text: str) -> str:
        """Açıklama: giriş, bölümler, kaynaklar, görsel lisansları (≤5000 karakter)."""
        d = self.data
        parts = [d.get("description", "").strip(), "", "📍 Bölümler", chapters_text]
        if d.get("sources"):
            parts += ["", "📚 Kaynaklar"] + [f"• {s}" for s in d["sources"]]
        credits = []
        for key, v in self.image_manifest().items():
            c = v.get("credit") or {}
            if c.get("title"):
                name = c["title"].removeprefix("File:").rsplit(".", 1)[0]
                credits.append(f"• {name} — {c.get('artist', '')} ({c.get('license', '')}), Wikimedia Commons")
        uses_clips = any("clip" in s for ch in d["chapters"] for p in ch["paragraphs"] for s in p["shots"])
        if d.get("ai_disclosure") and uses_clips:
            parts += ["", f"ℹ️ {d['ai_disclosure']}"]
        if d.get("hashtags"):
            parts += ["", " ".join(d["hashtags"])]
        head = "\n".join(parts)
        tail_title = "\n\n🖼️ Görsel kaynakları (lisanslı arşiv görselleri)\n"
        room = 5000 - len(head) - len(tail_title) - 60
        shown, used = [], 0
        for line in dict.fromkeys(credits):
            if used + len(line) + 1 > room:
                shown.append("• … tam liste sabit yorumda")
                break
            shown.append(line)
            used += len(line) + 1
        return head + tail_title + "\n".join(shown)

    def stage_yukle(self, publish_at: datetime | None):
        from scripts.youtube_uploader import upload_documentary, last_upload_error
        thumbs = sorted(self.build.glob("thumbs/kapak*.jpg"))
        synthetic = any("clip" in s for ch in self.data["chapters"]
                        for p in ch["paragraphs"] for s in p["shots"])
        video_id = upload_documentary(
            str(self.path("final.mp4")), self.data["title"],
            self.path("aciklama.txt").read_text(encoding="utf-8"),
            self.data.get("tags", []),
            thumbnail_path=str(thumbs[0]) if thumbs else None,
            captions_path=str(self.path("altyazi.srt")),
            publish_at=publish_at,
            playlist_id=_env("DOC_PLAYLIST_ID") or None,
            synthetic_media=synthetic,
        )
        if not video_id:
            raise RuntimeError(f"Yükleme başarısız: {last_upload_error().get('message')}")
        self.path("yukleme.json").write_text(json.dumps(
            {"video_id": video_id, "url": f"https://youtu.be/{video_id}",
             "publish_at": publish_at.isoformat() if publish_at else None}, indent=2))
        return video_id


def main(argv=None):
    ap = argparse.ArgumentParser(description="Türkçe tarih belgeseli üretim hattı")
    ap.add_argument("klasor")
    ap.add_argument("asama", choices=["ses", "gorseller", "kartlar", "bolum", "birlestir",
                                      "yukle", "hepsi", "dogrula"])
    ap.add_argument("--bolum", type=int, default=None, help="yalnızca bu bölümü render et")
    ap.add_argument("--yayin", default=None, help="planlı yayın, ISO-8601 (ör. 2026-11-04T16:00:00Z)")
    ap.add_argument("--ornek", type=int, default=None,
                    help="yalnızca ilk N bölümle örnek üret (build/ornek.mp4)")
    args = ap.parse_args(argv)

    prod = Production(args.klasor, sample=args.ornek)
    if args.ornek and args.asama == "yukle":
        ap.error("örnek YouTube'a yüklenmez")
    if args.asama == "dogrula":
        print("Senaryo geçerli:", prod.data["title"])
        return 0
    if args.asama in ("ses", "hepsi"):
        prod.stage_ses()
    if args.asama in ("gorseller", "hepsi"):
        prod.stage_gorseller()
    if args.asama in ("kartlar", "hepsi"):
        prod.stage_kartlar()
    if args.asama in ("bolum", "hepsi"):
        prod.stage_bolum(args.bolum)
    if args.asama in ("birlestir", "hepsi"):
        prod.stage_birlestir()
    if args.asama == "yukle":
        when = datetime.fromisoformat(args.yayin.replace("Z", "+00:00")) if args.yayin else None
        prod.stage_yukle(when)
    return 0


if __name__ == "__main__":
    sys.exit(main())
