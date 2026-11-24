"""Sümerler: Commons görselleri ve Pexels stok videoları (inceleme sonrası sabitlenir)."""
import json
from pathlib import Path

_HITIT = json.loads((Path(__file__).resolve().parents[2] / "01-hititler" / "cekim_plani.json").read_text(encoding="utf-8"))

IMAGES = {
    "dunya": {"commons": "File:Whole world - land and oceans 12000.jpg", "original": True},
}

STOCK = {
    "bugday_ruzgar": _HITIT["stock"]["bugday_ruzgar"],
    "yildizli_gece": _HITIT["stock"]["yildizli_gece"],
    "kurak_toprak": _HITIT["stock"]["kurak_toprak"],
    "mum_isigi": _HITIT["stock"]["mum_isigi"],
    "katman_toz": _HITIT["stock"]["katman_toz"],
    # inceleme ile seçilecekler (id yok → Pexels adayları)
    "nehir_kamis": {"q": "river reeds marsh sunrise"},
    "kamis_kayik": {"q": "wooden boat reeds marsh"},
    "col_ruzgar": {"q": "desert wind sand dunes sunset"},
    "kil_eller": {"q": "hands clay pottery wheel"},
    "sulama_kanali": {"q": "irrigation canal field water"},
    "nehir_gunbatimi": {"q": "wide river sunset calm water"},
    "harabe_gunbatimi": {"q": "ancient mud brick ruins desert"},
    "saat_yelkovan": {"q": "clock second hand close up"},
}
