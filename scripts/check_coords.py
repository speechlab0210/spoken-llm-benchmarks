"""Independent coordinate check: geocode every (city, country) in data/institutions.json with
OpenStreetMap Nominatim (1 req/s, cached) and flag sites whose agent-supplied lat/lon is farther
than THRESH_KM from the geocoded city. Also flags institutions with no city. Writes coord_report.json.
Usage: python check_coords.py <atlas_root> <cache.json> <report.json>"""
import json, sys, os, time, math, urllib.request, urllib.parse
ROOT, CACHE, REPORT = sys.argv[1:4]
THRESH_KM = 60
inst = json.load(open(os.path.join(ROOT, "data/institutions.json"), encoding="utf-8"))
cn = inst["country_names"]
cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}

def geocode(city, country):
    key = f"{city}|{country}"
    if key in cache: return cache[key]
    q = urllib.parse.urlencode({"city": city, "country": cn.get(country, country), "format": "json", "limit": 1})
    req = urllib.request.Request("https://nominatim.openstreetmap.org/search?" + q,
                                 headers={"User-Agent": "spoken-llm-benchmark-atlas coordinate check (mailto:speechlab0210@gmail.com)"})
    result = None
    try:
        d = json.load(urllib.request.urlopen(req, timeout=30))
        if d:
            result = [float(d[0]["lat"]), float(d[0]["lon"])]
            cache[key] = result            # only successful lookups are cached; misses and errors are retried next run
            json.dump(cache, open(CACHE, "w", encoding="utf-8"))
    except Exception as ex:
        result = {"error": str(ex)[:100]}
    time.sleep(1.1)
    return result

def km(a, b):
    R = 6371; p1, p2 = math.radians(a[0]), math.radians(b[0]); dp = p2 - p1; dl = math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))

far, nocity, nogeo, ok = [], [], [], 0
seen = set()
for i in inst["entries"]:
    for s in i["sites"]:
        c = s.get("country") or i.get("country")
        if not s.get("city"): nocity.append({"name": i["name"], "country": c, "lat": s["lat"], "lon": s["lon"]}); continue
        key = (s["city"], c)
        g = geocode(s["city"], c)
        if not g or isinstance(g, dict): nogeo.append({"name": i["name"], "city": s["city"], "country": c}); continue
        d = km((s["lat"], s["lon"]), g)
        if d > THRESH_KM: far.append({"name": i["name"], "city": s["city"], "country": c, "agent": [s["lat"], s["lon"]], "osm": g, "km": round(d)})
        else: ok += 1
rep = {"ok": ok, "far": sorted(far, key=lambda x: -x["km"]), "no_city": nocity, "not_geocoded": nogeo}
json.dump(rep, open(REPORT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"sites ok={ok} far={len(far)} no_city={len(nocity)} not_geocoded={len(nogeo)}")
for f in rep["far"][:30]: print("  FAR", f)
