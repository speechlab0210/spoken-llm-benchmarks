#!/usr/bin/env python3
"""Turn the affiliation-extraction workflow output into the two data files the site reads.

Input : the JSON returned by the `atlas-institutions` workflow (benchFinal / models / canonEntries / merge),
        optionally merged with a gap-fill run (same shape) — pass one combined JSON
        + models_index.json (which models are cascade composites)
Output: data/institutions.json  — one entry per canonical organisation (type, country, sites, aliases with context)
        data/affiliations.json  — per benchmark: institutions with lead flags and a publishable state; per model: builders
        report.json             — every issue a human (or the next agent) must look at before publishing

Hard rules (the script exits non-zero when they fail — nothing publishable is written):
  * every benchmark in the catalogue appears exactly once in the workflow output (missing ids may be
    whitelisted with --allow-missing to become "not yet attributed")
  * every raw organisation string has exactly one canonical entry
  * every merge target exists and there are no merge cycles
  * a benchmark record is *publishable* only when verified == confirmed, or corrected WITH a correction;
    cannot_verify / unverified records are kept in the file but flagged and never counted
  * a model builder is *publishable* only with status ok, >=1 builder and a real evidence URL

Soft checks (reported, publication decided by a human): site outside country bbox, low-confidence
canonicalisation, multi-country canonical names, unresolved types, merge reviewer's "suspicious" list.

Usage: python build_affiliations.py <wf_result.json> <models_index.json> <world.json> <atlas_root> <report.json> [--allow-missing id,id]
"""
import json, re, sys, os, unicodedata
from collections import defaultdict, Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from country_iso import iso_of, norm_city

wf_path, midx_path, world_path, ROOT, report_path = sys.argv[1:6]
allow_missing = set()
if "--allow-missing" in sys.argv:
    allow_missing = set(sys.argv[sys.argv.index("--allow-missing") + 1].split(","))
# independently geocoded (printed city, country) pairs, produced by geocode_printed.py
printed_sites = {}
if "--printed-sites" in sys.argv:
    printed_sites = json.load(open(sys.argv[sys.argv.index("--printed-sites") + 1], encoding="utf-8"))
wf = json.load(open(wf_path, encoding="utf-8"))
midx = json.load(open(midx_path, encoding="utf-8"))
world = json.load(open(world_path, encoding="utf-8"))
benchmarks = json.load(open(os.path.join(ROOT, "data/benchmarks.json"), encoding="utf-8"))["entries"]
models = json.load(open(os.path.join(ROOT, "data/models.json"), encoding="utf-8"))["entries"]
bench_ids = {b["id"] for b in benchmarks}
model_ids = {m["id"] for m in models}

ISO_NUM = {"US": "840", "CN": "156", "TW": "158", "JP": "392", "KR": "410", "GB": "826", "DE": "276", "FR": "250", "IT": "380",
    "ES": "724", "NL": "528", "BE": "056", "CH": "756", "AT": "040", "SE": "752", "NO": "578", "DK": "208", "FI": "246", "PL": "616",
    "CZ": "203", "PT": "620", "IE": "372", "GR": "300", "HU": "348", "RO": "642", "IL": "376", "AE": "784", "SA": "682", "QA": "634",
    "IN": "356", "PK": "586", "BD": "050", "LK": "144", "TH": "764", "VN": "704", "MY": "458", "ID": "360", "PH": "608", "AU": "036",
    "NZ": "554", "CA": "124", "MX": "484", "BR": "076", "AR": "032", "CL": "152", "CO": "170", "RU": "643", "UA": "804", "TR": "792",
    "EG": "818", "ZA": "710", "NG": "566", "KE": "404", "MA": "504", "IR": "364", "KZ": "398", "LU": "442", "EE": "233", "LV": "428",
    "LT": "440", "SI": "705", "HR": "191", "RS": "688", "BG": "100", "SK": "703", "IS": "352", "CY": "196", "NP": "524", "MN": "496",
    "UZ": "860", "GE": "268", "AM": "051", "AZ": "031", "ET": "231", "GH": "288", "TZ": "834", "CM": "120", "SN": "686", "TN": "788",
    "DZ": "012", "JO": "400", "LB": "422", "KW": "414", "OM": "512", "PE": "604", "VE": "862", "UY": "858", "EC": "218", "BO": "068",
    "CU": "192", "DO": "214", "CR": "188", "PA": "591", "GT": "320", "PR": "630", "KP": "408", "MM": "104", "KH": "116", "LA": "418",
    "BN": "096", "PG": "598", "FJ": "242", "IQ": "368", "SY": "760", "YE": "887", "AF": "004", "BT": "064", "MD": "498", "BY": "112",
    "AL": "008", "MK": "807", "BA": "070", "ME": "499", "RW": "646", "PS": "275", "UG": "800", "XK": None, "HK": None, "MO": None, "SG": None, "MT": None, "BH": None, "MV": None}
# tiny territories with no polygon at 110 m: hand bounding boxes so their sites are still checked
SMALL_BBOX = {"SG": [103.6, 1.2, 104.1, 1.5], "HK": [113.8, 22.1, 114.5, 22.6], "MO": [113.5, 22.1, 113.7, 22.3],
              "MT": [14.1, 35.7, 14.7, 36.1], "BH": [50.3, 25.5, 50.9, 26.4], "LU": [5.7, 49.4, 6.6, 50.2],
              "MV": [72.6, -0.8, 73.8, 7.2], "XK": [20.0, 41.8, 21.8, 43.3]}
COUNTRY_NAME = {"HK": "Hong Kong", "MO": "Macau", "SG": "Singapore", "MT": "Malta", "BH": "Bahrain", "MV": "Maldives", "XK": "Kosovo",
    "US": "United States", "GB": "United Kingdom", "KR": "South Korea", "TW": "Taiwan", "CZ": "Czechia", "RU": "Russia", "IR": "Iran",
    "VN": "Vietnam", "AE": "United Arab Emirates", "BA": "Bosnia and Herzegovina", "MK": "North Macedonia", "LA": "Laos", "SY": "Syria"}
num2name = {c["id"]: c["name"] for c in world["countries"] if c.get("id")}
bbox = {c["id"]: c["bbox"] for c in world["countries"] if c.get("id")}
lon_unreliable = {c["id"] for c in world["countries"] if c.get("id") and c.get("bbox_lon_unreliable")}
for iso, num in ISO_NUM.items():
    if num and num in num2name and iso not in COUNTRY_NAME:
        COUNTRY_NAME[iso] = num2name[num]

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "x"

def norm(s):
    s = unicodedata.normalize("NFKC", s or "").strip()
    return re.sub(r"\s+", " ", s)

hard = []          # hard failures -> exit 1
issues = defaultdict(list)

# ---------------- 0. completeness of the workflow output ----------------
seen_b = Counter(r["id"] for r in wf["benchFinal"])
dups = [k for k, v in seen_b.items() if v > 1]
if dups: hard.append(f"duplicate benchmark records in workflow output: {dups[:10]}")
missing_b = sorted(bench_ids - set(seen_b))
unexpected_b = sorted(set(seen_b) - bench_ids)
if unexpected_b: hard.append(f"workflow returned ids not in the catalogue: {unexpected_b[:10]}")
not_allowed = [m for m in missing_b if m not in allow_missing]
if not_allowed: hard.append(f"{len(not_allowed)} catalogue benchmarks have no workflow record (pass --allow-missing to publish them as 'not yet attributed'): {not_allowed[:10]}")
seen_m = Counter(r["id"] for r in wf.get("models") or [])
dups_m = [k for k, v in seen_m.items() if v > 1]
if dups_m: hard.append(f"duplicate model records: {dups_m[:10]}")

# ---------------- 1. canonical map (raw -> entry), then merges ----------------
# pseudo-organisations that appear in author blocks but are not institutions (kept out of every count)
EXCLUDE_CANON = {"independent researcher", "independent", "association for computing machinery", "acm", "none", "n/a"}
canon = {}
for e in wf["canonEntries"]:
    e = dict(e)
    e["raw"] = norm(e["raw"]); e["canonical"] = norm(e["canonical"])
    if e["canonical"].lower() in EXCLUDE_CANON or e["raw"].lower() in EXCLUDE_CANON:
        issues["excluded_pseudo_organisation"].append({"raw": e["raw"], "canonical": e["canonical"]}); e["canonical"] = "__EXCLUDED__"
    if e.get("country"): e["country"] = e["country"].upper()
    if e["raw"] in canon and (canon[e["raw"]]["canonical"] != e["canonical"] or canon[e["raw"]].get("country") != e.get("country")):
        hard.append(f"raw string '{e['raw']}' canonicalised two different ways: {canon[e['raw']]['canonical']}/{canon[e['raw']].get('country')} vs {e['canonical']}/{e.get('country')}")
    canon.setdefault(e["raw"], e)
canon_names = {e["canonical"] for e in canon.values()}
merge_to = {}
for m in (wf.get("merge") or {}).get("merges", []):
    f, t = norm(m["from"]), norm(m["to"])
    if f == t: continue
    if t not in canon_names:
        hard.append(f"merge target does not exist as a canonical name: '{f}' -> '{t}'"); continue
    merge_to[f] = t
def resolve(name):
    seen = [name]
    while name in merge_to:
        name = merge_to[name]
        if name in seen:
            hard.append(f"merge cycle: {' -> '.join(seen + [name])}"); return seen[0]
        seen.append(name)
    return name
for e in canon.values():
    e["canonical"] = resolve(e["canonical"])
for s in (wf.get("merge") or {}).get("suspicious", []):
    issues["merge_reviewer_suspicious"].append(s)

# ---------------- 2. institution registry ----------------
# identity key = canonical name. One organisation may have sites in several countries (Meta: Menlo Park
# and FAIR Paris) and must stay one row; each occurrence still carries its own site country. The cost is
# that two different organisations sharing an English name would collapse — reported here for review.
groups = defaultdict(list)
for e in canon.values():
    groups[(e["canonical"], "")].append(e)
for (nm, _), es in groups.items():
    ccs = {e.get("country") for e in es if e.get("country")}
    if len(ccs) > 1: issues["same_name_multiple_countries_review"].append({"name": nm, "countries": sorted(ccs), "raws": [(e["raw"], e.get("country"), e.get("city")) for e in es]})
raw_count = wf.get("rawCount", {})
inst = {}
used_ids = set()
excluded_raws = {e["raw"] for e in canon.values() if e["canonical"] == "__EXCLUDED__"}
for (name, _cc), es in groups.items():
    if name == "__EXCLUDED__": continue
    w = lambda e: raw_count.get(e["raw"], 1)
    def majority(field):
        c = Counter()
        for e in es:
            if e.get(field): c[e[field]] += w(e)
        return c.most_common(1)[0][0] if c else None
    ctry = majority("country"); typ = majority("type"); parent = majority("parent")
    countries = {e["country"] for e in es if e.get("country")}
    if len(countries) > 1:
        issues["institution_multiple_countries"].append({"name": name, "countries": sorted(countries), "raws": [(e["raw"], e.get("country")) for e in es]})
    sites = []
    for e in sorted(es, key=lambda e: -w(e)):
        if e.get("lat") is None or e.get("lon") is None: continue
        s = {"city": e.get("city"), "lat": round(float(e["lat"]), 2), "lon": round(float(e["lon"]), 2), "country": e.get("country") or ctry, "n": w(e)}
        hit = next((t for t in sites if (t["city"] or "").lower() == (s["city"] or "").lower() and abs(t["lat"] - s["lat"]) < 0.3 and abs(t["lon"] - s["lon"]) < 0.3), None)
        if hit: hit["n"] += s["n"]
        else: sites.append(s)
    short = next((e.get("short") for e in sorted(es, key=lambda e: -w(e)) if e.get("short")), None)
    conf = Counter(e.get("confidence") for e in es).most_common(1)[0][0]
    base = slug(name); iid = base; k = 2
    while iid in used_ids:
        iid = f"{base}-{k}"; k += 1
    used_ids.add(iid)
    inst[iid] = {"id": iid, "name": name, "short": short, "type": typ or "unresolved", "country": ctry, "parent": parent, "confidence": conf,
                 "sites": [{"city": s["city"], "lat": s["lat"], "lon": s["lon"], "country": s["country"]} for s in sites],
                 "aliases": sorted(({"raw": e["raw"], "country": e.get("country"), "city": e.get("city"),
                                     "lat": (round(float(e["lat"]), 2) if e.get("lat") is not None else None),
                                     "lon": (round(float(e["lon"]), 2) if e.get("lon") is not None else None),
                                     "type": e.get("type"), "confidence": e.get("confidence"), "note": e.get("note") or None} for e in es), key=lambda a: a["raw"])}
    if not ctry: issues["institution_no_country"].append(name)
    if typ in (None, "unresolved"): issues["institution_unresolved_type"].append(name)
    if not sites: issues["institution_no_coordinates"].append(name)
    if conf == "low": issues["institution_low_confidence"].append({"name": name, "raws": [e["raw"] for e in es]})
    for e in es:
        if e.get("confidence") == "low": issues["alias_low_confidence"].append({"institution": name, "raw": e["raw"], "country": e.get("country"), "note": e.get("note")})
    for s in sites:
        c = s["country"] or ctry
        if c and c not in ISO_NUM: issues["unknown_country_code"].append({"name": name, "country": c}); continue
        box = None; lon_ok = True
        num = ISO_NUM.get(c) if c else None
        if num and num in bbox: box = bbox[num]; lon_ok = num not in lon_unreliable
        elif c in SMALL_BBOX: box = SMALL_BBOX[c]
        if box:
            lo, la, hi, ha = box
            inside = (la - 1.0 <= s["lat"] <= ha + 1.0) and ((not lon_ok) or (lo - 1.0 <= s["lon"] <= hi + 1.0))
            if not inside:
                issues["site_outside_country_bbox"].append({"name": name, "country": c, "city": s["city"], "lat": s["lat"], "lon": s["lon"], "bbox": box})
        elif c: issues["site_unchecked_no_bbox"].append({"name": name, "country": c, "city": s["city"]})
raw2inst = {a["raw"]: iid for iid, i in inst.items() for a in i["aliases"]}
raw2alias = {a["raw"]: a for i in inst.values() for a in i["aliases"]}

# ---------------- 3. benchmarks ----------------
PUBLISHABLE_VERDICTS = {"confirmed", "corrected"}
aff_b = {}
for r in wf["benchFinal"]:
    bid = r["id"]
    if bid not in bench_ids: continue
    lead_list = [norm(x) for x in (r.get("lead_institutions") or []) if norm(x)]
    last_list = [norm(x) for x in (r.get("last_author_institutions") or []) if norm(x)]
    out = []
    for i in r.get("institutions") or []:
        raw = norm(i.get("name"))
        if not raw or raw in excluded_raws: continue
        iid = raw2inst.get(raw)
        if not iid:
            hard.append(f"benchmark {bid}: raw organisation '{raw}' has no canonical entry"); continue
        al = raw2alias.get(raw, {})
        ins = inst[iid]
        printed_city = i.get("city") or None
        pc_iso = iso_of(i.get("country"))
        if not pc_iso and printed_city and "," in printed_city:      # "Toronto, ON, Canada" printed as one city string
            pc_iso = iso_of(printed_city.split(",")[-1])
        # the paper wins: a printed country overrides the canonical entry's country; a printed city places the
        # occurrence at that city (geocoded independently); only when the paper names no city does the
        # organisation's default site apply — and never in a different country than the one printed
        country = pc_iso or al.get("country") or ins["country"]
        city = lat = lon = None; placed = "none"
        if printed_city:
            c = norm_city(printed_city)
            if c and c.lower().startswith("hong kong"): c, country = "Hong Kong", "HK"
            if c and c.lower().startswith("maca"): c, country = "Macau", "MO"
            g = printed_sites.get(f"{c}|{country}") if c else None
            if not g and c and country in ("HK", "MO", "SG"):
                g = {"HK": {"city": "Hong Kong", "lat": 22.32, "lon": 114.17}, "MO": {"city": "Macau", "lat": 22.2, "lon": 113.55}, "SG": {"city": "Singapore", "lat": 1.35, "lon": 103.82}}[country]
            if g:
                city, lat, lon, placed = g.get("city") or c, g["lat"], g["lon"], "named"
            elif al.get("lat") is not None and al.get("city") and c and (c.lower() in al["city"].lower() or al["city"].lower() in c.lower()) and (not pc_iso or pc_iso == al.get("country")):
                city, lat, lon, placed = al["city"], al["lat"], al["lon"], "named"
            else:
                issues["printed_city_not_geocoded"].append({"benchmark": bid, "raw": raw, "printed_city": printed_city, "country": country})
                city = c
                if al.get("lat") is not None and (not pc_iso or pc_iso == al.get("country")):
                    lat, lon, placed = al["lat"], al["lon"], "default"
        elif al.get("lat") is not None and (not pc_iso or pc_iso == al.get("country")):
            city, lat, lon, placed = al.get("city"), al["lat"], al["lon"], "default"
        elif pc_iso and al.get("country") and pc_iso != al.get("country"):
            issues["printed_country_differs_from_alias_site_unplaced"].append({"benchmark": bid, "raw": raw, "printed_country": pc_iso, "alias_country": al.get("country")})
        if any(o["inst"] == iid and o["country"] == country and (o["city"] or "").lower() == (city or "").lower() for o in out):
            continue   # the same organisation at the same site printed twice (two departments) — one occurrence
        out.append({"inst": iid, "unit": i.get("unit") or None, "raw": raw,
                    "country": country, "city": city, "lat": lat, "lon": lon, "placed": placed,
                    "printed_city": printed_city, "printed_country": i.get("country") or None,
                    "lead": False, "first_author": raw in lead_list, "last": raw in last_list, "evidence": i.get("evidence") or "printed"})
    # lead = the FIRST-LISTED affiliation of the FIRST author; one per benchmark, never inferred from order of `institutions`
    lead_iid = raw2inst.get(lead_list[0]) if lead_list else None
    if lead_iid:
        for o in out:
            if o["inst"] == lead_iid: o["lead"] = True; break
        else:
            issues["lead_not_in_institutions"].append({"benchmark": bid, "lead": lead_list[0]})
    verified = r.get("_verify") or "unverified"
    if verified == "corrected" and not r.get("_verify_reason"):
        verified = "unverified"; issues["corrected_without_reason"].append(bid)
    status = r.get("status") or ("ok" if out else "no_affiliation_text")
    publishable = bool(out) and verified in PUBLISHABLE_VERDICTS and status != "no_affiliation_text"
    if out and verified not in PUBLISHABLE_VERDICTS: issues["record_not_publishable_verification"].append({"benchmark": bid, "verified": verified})
    if out and not lead_iid: issues["record_without_lead"].append(bid)
    # complete only when every occurrence's country came from its own canonical entry (not the registry majority)
    aff_b[bid] = {"status": status, "verified": verified, "publishable": publishable, "institutions": out,
                  "countries_complete": bool(out) and all(iso_of(o["printed_country"]) or raw2alias.get(o["raw"], {}).get("country") for o in out),
                  "verify_note": (r.get("_verify_reason") or "")[:300] or None, "note": (r.get("notes") or "")[:300] or None,
                  "n_authors": len(r.get("authors") or [])}
    if not out and status != "no_affiliation_text": issues["benchmark_without_institution"].append({"benchmark": bid, "status": status})

# ---------------- 4. models ----------------
aff_m = {}
composite = set(midx.get("composite", []))
for mid in composite:
    if mid in model_ids:
        aff_m[mid] = {"status": "composite", "publishable": False, "builders": [], "evidence_url": None, "evidence_quote": None,
                      "note": "cascade of third-party components; no single builder is attributed"}
for r in wf.get("models") or []:
    mid = r["id"]
    if mid not in model_ids: hard.append(f"workflow returned model id not in the catalogue: {mid}"); continue
    if mid in composite: issues["model_composite_also_in_workflow"].append(mid); continue
    out = []
    lead = norm(r.get("lead_builder") or "")
    for b in r.get("builders") or []:
        raw = norm(b.get("name"))
        if raw in excluded_raws: continue
        iid = raw2inst.get(raw)
        if not iid: hard.append(f"model {mid}: raw organisation '{raw}' has no canonical entry"); continue
        if any(o["inst"] == iid for o in out): continue
        al = raw2alias.get(raw, {})
        out.append({"inst": iid, "unit": b.get("unit") or None, "raw": raw, "lead": raw == lead,
                    "country": al.get("country") or inst[iid]["country"], "city": al.get("city"), "lat": al.get("lat"), "lon": al.get("lon"),
                    "placed": "default" if al.get("lat") is not None else "none"})
    if out and not any(o["lead"] for o in out):
        out[0]["lead"] = True; issues["model_lead_defaulted"].append(mid)
    url = r.get("evidence_url") or None
    status = r.get("status")
    publishable = status == "ok" and bool(out) and bool(url) and str(url).startswith("http")
    if status == "ok" and out and not publishable: issues["model_ok_without_evidence"].append(mid)
    if status == "unknown" and out: issues["model_unknown_with_builders"].append(mid)
    aff_m[mid] = {"status": status if out else "unknown", "publishable": publishable, "builders": out, "evidence_url": url,
                  "evidence_quote": (r.get("evidence_quote") or "")[:200] or None, "note": (r.get("notes") or "")[:300] or None}
    if not out: issues["model_unknown_builder"].append(mid)
missing_m = [m["id"] for m in models if m["id"] not in aff_m]
if missing_m: issues["model_missing_record"].extend(missing_m)

# ---------------- 5. write ----------------
if hard:
    print("HARD FAILURES — nothing written:"); [print("  -", h) for h in hard]
    json.dump({"hard": hard, "issues": issues}, open(report_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=list)
    sys.exit(1)
inst_list = sorted(inst.values(), key=lambda i: i["name"].lower())
json.dump({"generated": "workflow atlas-institutions: paper author blocks (arXiv HTML / PDF first page) + model reports; raw strings canonicalised with a per-alias confidence; see README",
           "country_names": COUNTRY_NAME, "iso_numeric": {k: v for k, v in ISO_NUM.items() if v},
           "entries": inst_list}, open(os.path.join(ROOT, "data/institutions.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"generated": "workflow atlas-institutions; lead = first-listed affiliation of the first author; publishable = verified by an independent second read",
           "benchmarks": aff_b, "models": aff_m}, open(os.path.join(ROOT, "data/affiliations.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
summary = {"institutions": len(inst_list),
           "benchmarks_total": len(benchmarks), "benchmarks_with_record": len(aff_b), "benchmarks_missing_record": missing_b,
           "benchmarks_publishable": sum(1 for v in aff_b.values() if v["publishable"]),
           "benchmarks_no_affiliation_text": sum(1 for v in aff_b.values() if v["status"] == "no_affiliation_text"),
           "benchmarks_partial": sum(1 for v in aff_b.values() if v["status"] == "partial"),
           "verify_verdicts": Counter(v["verified"] for v in aff_b.values()),
           "models_total": len(models), "models_with_record": len(aff_m), "models_publishable": sum(1 for v in aff_m.values() if v["publishable"]),
           "models_composite": sum(1 for v in aff_m.values() if v["status"] == "composite"),
           "models_unknown": sum(1 for v in aff_m.values() if v["status"] == "unknown"),
           "sites_placed": Counter(o["placed"] for v in aff_b.values() for o in v["institutions"]),
           "issues": {k: v for k, v in issues.items()}}
json.dump(summary, open(report_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=list)
print(json.dumps({k: (v if not isinstance(v, (list, dict)) or k in ("verify_verdicts", "sites_placed") else len(v)) for k, v in summary.items()}, default=list))
print("issue counts:", {k: len(v) for k, v in issues.items()})
