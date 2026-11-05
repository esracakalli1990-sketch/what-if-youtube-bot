"""İstanbul'un Fethi çekim planı: python belgeseller/03-istanbul/araclar/plan_kur.py belgeseller/03-istanbul/cekim_plani.json"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from haritalar import M
from cekimler import SHOTS
from gorseller import IMAGES

MISIR = json.load(open(ROOT / "belgeseller/02-misir/cekim_plani.json", encoding="utf-8"))
HITIT = json.load(open(ROOT / "belgeseller/01-hititler/cekim_plani.json", encoding="utf-8"))
IMAGES["dunya"] = {"commons": "File:Whole world - land and oceans 12000.jpg", "original": True}
STOCK = {k: HITIT["stock"][k] for k in ("ates_gece", "mum_isigi", "deniz_safak", "yildizli_gece",
                                        "katman_toz", "katman_kivilcim", "katman_sis")}
MUSIC = {"0": "karanlik", "1": "gizem", "2": "agir", "3": "derin", "4": "karanlik", "5": "ses", "6": "karanlik",
         "7": "agir", "8": "gizem", "9": "karanlik", "10": "isik", "11": "huzun"}
CARDS = {"1": "buondelmonti", "2": "fatih_bellini", "3": "rumeli_hisari", "4": "sahi_topu", "5": "surlar_genis",
         "6": "kusatma_minyatur", "7": "halic", "8": "surlar_guney", "9": "surlar_kule", "10": "ayasofya_2"}

plan = {
 "slug": "03-istanbul",
 "title": "İstanbul Nasıl Fethedildi? 53 Günün Tam Hikâyesi | Fatih Sultan Mehmed",
 "description": ("1453 baharı. Bin yıl boyunca hiçbir ordunun aşamadığı surlar, Haliç'i kapatan dev bir zincir ve "
   "karşılarında henüz 21 yaşında bir sultan: II. Mehmed.\n\n"
   "Bu belgeselde İstanbul'un fethini, Rumeli Hisarı'nın birkaç ayda yükselmesinden Urban'ın dev toplarına, "
   "gemilerin bir gecede karadan Haliç'e indirilmesinden 29 Mayıs sabahının son hücumuna kadar gün gün anlatıyoruz. "
   "Hareketli haritalar, kuşatma planları, müze eserleri ve arşiv belgeleri eşliğinde. "
   "Tartışmalı bilgiler anlatımda öyle belirtilmiştir.\n\n"
   "Serinin önceki bölümleri: Antik Mısır'ın Tam Hikâyesi → https://youtu.be/Ns-ozDX_Y6g · "
   "Hitit İmparatorluğu → https://youtu.be/ibuMFDr7rmI"),
 "tags": ["istanbul'un fethi", "fatih sultan mehmed", "1453", "osmanlı tarihi", "konstantinopolis", "bizans",
          "gemilerin karadan yürütülmesi", "ulubatlı hasan", "rumeli hisarı", "osmanlı belgeseli", "tarih belgeseli",
          "türk tarihi", "fetih 1453", "theodosius surları", "belgesel", "türkçe belgesel"],
 "hashtags": ["#İstanbulunFethi", "#FatihSultanMehmed", "#1453", "#OsmanlıTarihi", "#Belgesel"],
 "ai_disclosure": MISIR["ai_disclosure"],
 "sources": [
   "Halil İnalcık, Fatih Devri Üzerine Tetkikler ve Vesikalar, TTK",
   "Feridun M. Emecen, Fetih ve Kıyamet 1453, Timaş",
   "Steven Runciman, The Fall of Constantinople 1453, Cambridge University Press, 1965",
   "Roger Crowley, 1453: The Holy War for Constantinople and the Clash of Islam and the West, 2005",
   "Kritovulos, Tarih-i Sultan Mehmed Han-ı Sani",
   "Dukas, Bizans Tarihi",
   "Nicolo Barbaro, Konstantiniye Muhasarası Ruznamesi",
   "Georgios Sfrancis, Chronicon Minus",
   "Royal Armouries: The Great Turkish Bombard (Dardanelles Gun)"],
 "tts_model": "eleven_v4",
 "ilk_yorum": ("Sizce fethin en kritik anı hangisiydi: Rumeli Hisarı'nın yapılması mı, dev toplar mı, yoksa gemilerin "
               "bir gecede karadan Haliç'e indirilmesi mi? Yorumlarda tartışalım.\n\n"
               "🔔 Sıradaki belgesel: Yavuz Sultan Selim — Sekiz Yılda Bir İmparatorluk."),
 "pronunciations": {"Giustiniani": "Custinyani", "Giovanni": "Covanni", "Theodosius": "Teodosius",
                    "Sfrancis'in": "Sfrançis'in", "Gennadios": "Genadios"},
 "voice_settings": MISIR["voice_settings"],
 "thumbnails": [
   {"sablon": "v2", "arka_plan": "fatih_bellini", "arka_plan_kadraj": "50% 28%", "hale": "#ff7a1a",
    "line1": "53 gün", "line2": "imkânsız fetih", "vurgu": "#FFC83D"},
   {"sablon": "v2", "arka_plan": "kapak_gemiler", "arka_plan_kadraj": "60% 50%", "hale": "#ff9a2e",
    "line1": "Gemiler", "line2": "karadan yürüdü", "vurgu": "#FFC83D"},
   {"sablon": "v2", "arka_plan": "kapak_sancak", "arka_plan_kadraj": "55% 40%", "hale": "#ff4a2a",
    "line1": "İstanbul", "line2": "nasıl düştü?", "vurgu": "#FFC83D"}],
 "images": IMAGES, "cards": CARDS, "music": MUSIC, "shots": SHOTS, "stock": STOCK, "films": {}, "maps": M,
 "music_sources": MISIR["music_sources"],
}
used = {x["image"] for v in SHOTS.values() for x in v if "image" in x} | set(CARDS.values()) | {"dunya"}
used |= {t[k] for t in plan["thumbnails"] for k in ("odak", "arka_plan") if t.get(k)}
used |= {v[k] for v in M.values() for k in ("image", "background") if v.get(k)}
missing = sorted(used - set(IMAGES))
maps_used = {x["map"] for v in SHOTS.values() for x in v if "map" in x}
plan["images"] = {k: v for k, v in sorted(IMAGES.items()) if k in used}
plan["maps"] = {k: v for k, v in M.items() if k in maps_used}
stock_used = {x.get("stock") for v in SHOTS.values() for x in v} | {x.get("overlay") for v in SHOTS.values() for x in v}
print("eksik görsel:", missing, "| eksik stok:", sorted(x for x in stock_used - set(STOCK) if x),
      "| kullanılmayan harita:", sorted(set(M) - maps_used))
json.dump(plan, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
