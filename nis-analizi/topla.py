"""Niş taraması: search -> videos -> channels, önbellekli."""
import json, hashlib, sys, time, urllib.request, urllib.parse, pathlib
API = "https://www.googleapis.com/youtube/v3/"
CACHE = pathlib.Path("onbellek"); CACHE.mkdir(exist_ok=True)
units = 0
class QuotaError(Exception): pass

def get(endpoint, params, cost):
    global units
    key = hashlib.sha1((endpoint + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    f = CACHE / f"{key}.json"
    if f.exists():
        return json.loads(f.read_text())
    url = API + endpoint + "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                data = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            if e.code in (403, 429) and "quota" in body.lower():
                raise QuotaError(body)
            if e.code >= 500 and attempt < 3:
                time.sleep(2 ** attempt); continue
            raise RuntimeError(f"{e.code} {body}")
    units += cost
    f.write_text(json.dumps(data))
    return data

nisler = json.load(open("nisler.json"))
region = {"tr": ("TR", "tr"), "en": ("US", "en")}
results = {}
vids, chans = set(), set()
stop = False
for lang, groups in nisler.items():
    if stop: break
    reg, rel = region[lang]
    for nis, kws in groups.items():
        if stop: break
        for kw in kws:
            try:
                d = get("search", {"part": "snippet", "q": kw, "type": "video", "maxResults": 50,
                               "regionCode": reg, "relevanceLanguage": rel}, 100)
            except QuotaError:
                print(f"KOTA BİTTİ: {kw} ve sonrası atlandı", flush=True); stop = True; break
            ids = [i["id"]["videoId"] for i in d.get("items", []) if i["id"].get("videoId")]
            results.setdefault(nis, {})[kw] = ids
            vids.update(ids)
            print(f"{nis} | {kw}: {len(ids)} sonuç (birim={units})", flush=True)

vinfo = {}
vl = sorted(vids)
for i in range(0, len(vl), 50):
    d = get("videos", {"part": "snippet,statistics,contentDetails", "id": ",".join(vl[i:i+50])}, 1)
    for it in d.get("items", []):
        vinfo[it["id"]] = it; chans.add(it["snippet"]["channelId"])
cinfo = {}
cl = sorted(chans)
for i in range(0, len(cl), 50):
    d = get("channels", {"part": "snippet,statistics", "id": ",".join(cl[i:i+50])}, 1)
    for it in d.get("items", []):
        cinfo[it["id"]] = it
json.dump({"results": results, "videos": vinfo, "channels": cinfo}, open("ham_veri.json", "w"))
print("Bitti. Harcanan birim:", units, "video:", len(vinfo), "kanal:", len(cinfo))
