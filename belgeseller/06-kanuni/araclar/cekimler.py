"""Kanuni — uzun paragraflar için çekim listesi (gerçek ses süreleriyle, 19 Kasım).

Anahtar "bölüm.paragraf"; burada olmayan paragraflar senaryo.md'deki [EKRAN] satırını kullanır.
Kural: 10 sn'lik klip en fazla %40 yavaşlar (~16 sn); "start" ile ileri giriş noktası o kadar kısalır.
Aynı klip yeniden kullanılırsa farklı giriş noktası ve/veya ayna (flip) ile, uzak paragraflarda.
Durağan görsel (r_…) en fazla ~11 sn.
"""


def c(name, start=None, flip=False, **kw):
    s = {"clip": f"klipler/{name}.mp4", **kw}
    if start:
        s["start"] = float(start)
    if flip:
        s["flip"] = True
    return s


def r(name, move="in"):
    return {"image": name, "move": move}


SHOTS = {
    "0.1": [c("c03"), r("r_tugra")],
    "1.1": [c("c10"), c("c29", 1)],
    "1.2": [r("r_kanuni_genc"), r("r_lorck_kanuni", "left"), c("c49")],
    "1.3": [c("c11"), c("c34")],
    "1.4": [c("c02", 4), c("c12"), c("c19", 3, True)],
    "2.3": [c("c15", 5, True), c("c17"), c("c18", 4)],
    "2.4": [c("c17", 5), c("c26", 4), c("c06", 5, True)],
    "3.5": [c("c05", 3, True), c("c22", 3)],
    "4.4": [r("r_migferli"), c("c13", 4, True), c("c23", 4), c("c49", 4, True)],
    "5.0": [c("c25"), r("r_barbaros"), c("c06", 3, True)],
    "5.2": [c("c06"), r("r_preveze", "left"), c("c26")],
    "5.4": [c("c49"), c("c29", 2), c("c25", 2, True)],
    "6.1": [c("c30"), c("c28", 4, True), r("r_tugra2")],
    "6.2": [c("c31"), c("c16", 4)],
    "6.4": [c("c38"), c("c32", 3, True), r("r_lorck_camii")],
    "7.1": [c("c34", 3, True), c("c28", 4)],
    "7.2": [c("c35"), r("r_lorck_kanuni", "out"), c("c33", 2, True)],
    "7.3": [r("r_hurrem"), c("c36")],
    "7.4": [c("c47", 2), c("c50"), c("c31", 4, True)],
    "8.0": [c("c37"), c("c04", 4)],
    "8.1": [c("c42", 3), c("c38")],
    "8.3": [c("c35", 4), r("r_hurrem", "out"), c("c41")],
    "8.4": [c("c47"), c("c41", 4, True)],
    "8.5": [c("c44", 2), c("c42")],
    "9.4": [c("c03"), c("c44"), c("c24", 3, True)],
    "9.5": [c("c45", sfx=False), c("c46")],
    "10.0": [c("c13", 6), c("c29", 6), c("c32", 4, True), c("c06", 4, True)],
    "10.1": [c("c42"), c("c47", 2), c("c46", 3)],
}
