import json, random, re, statistics as st
from datetime import datetime, timezone
D = json.load(open("ham_veri.json")); V, C = D["videos"], D["channels"]
NOW = datetime.now(timezone.utc)
def dur(s):
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    d,h,mi,se = (int(x or 0) for x in m.groups()); return d*86400+h*3600+mi*60+se
def age(ts): return (NOW - datetime.fromisoformat(ts.replace("Z","+00:00"))).days
def boot(xs, n=2000):
    random.seed(1); meds = sorted(st.median(random.choices(xs, k=len(xs))) for _ in range(n))
    return meds[int(.1*n)], meds[int(.9*n)]
for nis, kws in D["results"].items():
    small, allv, big, cov, kwmed = {}, set(), 0, 0, {}
    for kw, ids in kws.items():
        k = 0; kv=[]
        for vid in ids:
            v = V.get(vid); 
            if not v: continue
            c = C.get(v["snippet"]["channelId"], {}); subs = int(c.get("statistics",{}).get("subscriberCount", 0) or 0)
            if vid not in allv:
                allv.add(vid); big += subs >= 100_000
            if subs < 10_000 and dur(v["contentDetails"].get("duration")) > 180 and age(v["snippet"]["publishedAt"]) <= 730:
                views = int(v["statistics"].get("viewCount", 0))
                small[vid] = dict(views=views, ch=v["snippet"]["channelTitle"], title=v["snippet"]["title"],
                                  chage=age(c["snippet"]["publishedAt"]) if c else 9999, subs=subs, dur=dur(v["contentDetails"]["duration"]), kw=kw)
                k += 1; kv.append(views)
        cov += k >= 2; kwmed[kw] = (k, int(st.median(kv)) if kv else 0)
    xs = [x["views"] for x in small.values()]
    new = [x["views"] for x in small.values() if x["chage"] <= 540]
    print(f"\n=== {nis} ===")
    print(f"tüm benzersiz video: {len(allv)}, büyük kanal (100k+) payı: {big/len(allv):.0%}")
    if xs:
        lo, hi = boot(xs)
        print(f"küçük kanal uzun video (son 2 yıl): n={len(xs)}, kanal sayısı={len({x['ch'] for x in small.values()})}")
        print(f"medyan={int(st.median(xs))}  %80 GA=[{int(lo)}, {int(hi)}]  1k+={sum(x>=1000 for x in xs)/len(xs):.0%}  10k+={sum(x>=10000 for x in xs)/len(xs):.0%}")
        print(f"yeni kanal (≤540 gün): n={len(new)} medyan={int(st.median(new)) if new else '-'}")
        print(f"kelime kapsamı (≥2 küçük kanal videosu): {cov}/{len(kws)}")
        for kw,(k,m) in kwmed.items(): print(f"   {kw}: n={k} medyan={m}")
        print("  en çok izlenen küçük kanal videoları:")
        for x in sorted(small.values(), key=lambda x:-x["views"])[:6]:
            print(f"   {x['views']:>8} | {x['subs']:>5} abone | {x['dur']//60} dk | {x['title'][:70]}")
