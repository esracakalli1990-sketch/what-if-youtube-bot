"""Mısır çekim planını üretir: python belgeseller/02-misir/araclar/plan_kur.py belgeseller/02-misir/cekim_plani.json"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from haritalar import M
from cekimler import SHOTS
from gorseller import IMAGES

HITIT = json.load(open(ROOT / "belgeseller/01-hititler/cekim_plani.json", encoding="utf-8"))
for k in ["amarna_mektup2", "ankhesenamun", "ebu_simbel", "ebu_simbel_salon", "kades_parca", "kades_tablet", "karnak",
          "medinet_habu", "medinet_habu_2", "ramesseum_kades", "ramses_heykel", "ramses_turin"]:
    IMAGES.setdefault(k, HITIT["images"][k])
IMAGES["dunya"] = {"commons": "File:Whole world - land and oceans 12000.jpg", "original": True}

STOCK = {
 "gize_safak": {"q": "giza pyramids sunrise", "id": 10717893}, "gize_gunbatimi": {"q": "pyramids sunset desert", "id": 4205790},
 "nil_gunbatimi": {"q": "nile river sunset felucca", "id": 12277989}, "nil_akis": {"q": "nile river water flowing", "id": 20663017},
 "bugday_ruzgar": HITIT["stock"]["bugday_ruzgar"], "yildizli_gece": HITIT["stock"]["yildizli_gece"],
 "gunes_dogus": {"q": "sun rising over desert", "id": 29660258}, "kum_ruzgar": {"q": "sand blowing desert dunes wind", "id": 8865223},
 "kurak_toprak": HITIT["stock"]["kurak_toprak"], "tas_doku": HITIT["stock"]["tas_doku"],
 "ekmek_firin": HITIT["stock"]["ekmek_firin"], "deniz_safak": HITIT["stock"]["deniz_safak"],
 "mum_isigi": HITIT["stock"]["mum_isigi"], "ates_gece": HITIT["stock"]["ates_gece"],
 "at_dortnala": HITIT["stock"]["at_dortnala"], "katman_toz": HITIT["stock"]["katman_toz"],
}
MUSIC_SOURCES = {
 "gizem": {"commons": "File:Heart of Nowhere (MacLeod, Kevin) (ISRC USUAN1400045).oga"},
 "agir": {"commons": "File:Earth Prelude (MacLeod, Kevin) (ISRC USUAN1100247).oga"},
 "karanlik": {"commons": "File:Kevin MacLeod - Ritual.ogg"},
 "huzun": {"commons": "File:Kevin MacLeod - 06 - Impact Lento.ogg"},
 "tapinak": {"commons": "File:Kevin MacLeod - Temple of the Manes.ogg"},
 "ses": {"commons": "File:The Voices (MacLeod, Kevin) (ISRC USUAN1100046).oga"},
 "isik": {"commons": "File:Kevin MacLeod - Bathed in the Light.ogg"},
 "derin": {"commons": "File:Kevin MacLeod - Silver Blue Light.ogg"},
}
MUSIC = {"0": "gizem", "1": "isik", "2": "agir", "3": "karanlik", "4": "ses", "5": "tapinak", "6": "gizem",
         "7": "agir", "8": "karanlik", "9": "derin", "10": "huzun", "11": "isik", "12": "huzun"}
CARDS = {"1": "nil_feluka", "2": "sakkara", "3": "senusret", "4": "araba_kabartma", "5": "deyr_bahri",
         "6": "nefertiti", "7": "ebu_simbel", "8": "medinet_habu", "9": "iskender", "10": "kleopatra_bust",
         "11": "rosetta"}

plan = {
 "slug": "02-misir",
 "title": "Antik Mısır'ın Tam Hikâyesi | Piramitlerden Kleopatra'ya 3000 Yıl",
 "description": ("Kleopatra, Büyük Piramit'e bizden daha uzaktı. Üç bin yıl boyunca aynı tanrılara tapan, aynı dili konuşan "
   "ve her çöküşten sonra yeniden doğan bir uygarlık: Antik Mısır.\n\n"
   "Bu belgeselde Narmer'in iki tacı birleştirmesinden piramitleri yapan işçilere, kendini firavun ilan eden Hatşepsut'tan "
   "tanrıları yasaklayan Ahenaton'a, Kadeş'teki Ramses'ten tarihin ilk grevine, Kleopatra'nın son savaşından "
   "hiyeroglifleri çözen Champollion'a kadar Mısır'ın tam hikâyesini, müze eserleri ve arşiv belgeleri eşliğinde anlatıyoruz. "
   "Tartışmalı bilgiler anlatımda öyle belirtilmiştir.\n\n"
   "Serinin önceki bölümü: Hitit İmparatorluğu'nun Tam Hikâyesi → https://youtu.be/ibuMFDr7rmI"),
 "tags": ["antik mısır", "mısır tarihi", "firavunlar", "piramitler", "tarih belgeseli", "kleopatra", "tutankamon",
          "ramses", "hatşepsut", "ahenaton", "nefertiti", "rosetta taşı", "kadeş savaşı", "antik tarih", "belgesel",
          "türkçe belgesel", "uyku için tarih"],
 "hashtags": ["#AntikMısır", "#Tarih", "#Belgesel", "#Firavun", "#Piramitler"],
 "ai_disclosure": HITIT["ai_disclosure"],
 "sources": [
   "Ian Shaw (ed.), The Oxford History of Ancient Egypt, Oxford University Press, 2000",
   "Mark Lehner, The Complete Pyramids, Thames & Hudson, 1997",
   "Mark Lehner & Zahi Hawass, Giza and the Pyramids, 2017",
   "Pierre Tallet, Les papyrus de la mer Rouge I: Le journal de Merer, IFAO, 2017",
   "Miriam Lichtheim, Ancient Egyptian Literature, Vol. I–II, University of California Press",
   "Joyce Tyldesley, Hatchepsut: The Female Pharaoh, 1996; Nefertiti, 1998",
   "William L. Moran, The Amarna Letters, Johns Hopkins University Press, 1992",
   "Howard Carter, The Tomb of Tut.ankh.Amen, 1923",
   "Kenneth A. Kitchen, Pharaoh Triumphant: The Life and Times of Ramesses II, 1982",
   "Eric H. Cline, 1177 B.C.: The Year Civilization Collapsed, Princeton University Press, 2014",
   "John Romer, Ancient Lives: The Story of the Pharaohs' Tombmakers, 1984",
   "Plutarkhos, Antonius ve Sezar biyografileri",
   "Richard Parkinson, Cracking Codes: The Rosetta Stone and Decipherment, British Museum Press, 1999",
   "UNESCO Dünya Mirası: Nubian Monuments from Abu Simbel to Philae"],
 "tts_model": "eleven_v4",
 "pronunciations": {"Champollion": "Şampolyon", "Jean-François": "Jan-Fransuva", "Thomas": "Tomas", "Young": "Yang",
                    "Howard": "Havırd", "Eratosthenes": "Eratostenes", "Theodosius": "Teodosius"},
 "voice_settings": HITIT["voice_settings"],
 "thumbnails": [
   {"sablon": "v2", "odak": "tut_maske", "odak_x": 0.74, "odak_y": 0.55, "odak_boy": 1.25, "karisim": "lighten",
    "hale": "#ffb030", "line1": "3000 yıllık", "line2": "sır", "vurgu": "#FFC83D"},
   {"sablon": "v2", "odak": "nefertiti", "odak_x": 0.75, "odak_y": 0.58, "odak_boy": 1.3, "karisim": "lighten",
    "hale": "#2fa4c8", "line1": "Mısır nasıl", "line2": "çöktü?", "vurgu": "#FFC83D"},
   {"sablon": "v2", "arka_plan": "nefertari_tapinak", "arka_plan_kadraj": "55% 60%", "hale": "#ff7a1a",
    "line1": "Firavunların", "line2": "sonu", "vurgu": "#FFC83D"}],
 "images": IMAGES, "cards": CARDS, "music": MUSIC, "shots": SHOTS, "stock": STOCK, "films": {}, "maps": M,
 "music_sources": MUSIC_SOURCES,
 "klip_yerleri": {"_not": "Gemini klipleri gelince bu paragraflardaki ilgili çekimin yerine {\"clip\": \"klipler/klipN.mp4\"} konur.",
                  "klip1": "2.7", "klip2": "1.1", "klip3": "4.4", "klip4": "5.3", "klip5": "6.7", "klip6": "7.5",
                  "klip7": "8.3", "klip8": "10.5"},
}
# kullanılmayan görselleri at, eksikleri bildir
used = {s["image"] for v in SHOTS.values() for s in v if "image" in s} | set(CARDS.values()) | {"tut_maske", "nefertiti", "nefertari_tapinak", "dunya"}
missing = sorted(used - set(IMAGES))
plan["images"] = {k: v for k, v in sorted(IMAGES.items()) if k in used}
stock_used = {s.get("stock") for v in SHOTS.values() for s in v} | {s.get("overlay") for v in SHOTS.values() for s in v}
print("eksik görsel:", missing); print("eksik stok:", sorted(x for x in stock_used - set(STOCK) if x))
json.dump(plan, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
