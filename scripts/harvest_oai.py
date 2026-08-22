# Bulk arXiv harvest via OAI-PMH — the interface arXiv actually intends for date-range sweeps.
# Independent of the query API (different endpoint, different quota, honours Retry-After),
# so it doubles as a coverage cross-check on harvest_arxiv.py.
#
# Usage: python scripts/harvest_oai.py --from 2026-06-01 --until 2026-09-01 --sets cs,eess
#        -> raw/oai_<from>_<until>.jsonl  (only records whose categories look speech/audio/NLP)

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
OAI = "https://export.arxiv.org/oai2?"
NS = {"oai": "http://www.openarchives.org/OAI/2.0/",
      "arx": "http://arxiv.org/OAI/arXiv/"}

# keep only records touching these categories — everything else is noise for us
KEEP_CATS = {"eess.AS", "cs.SD", "cs.CL", "cs.MM", "cs.AI", "cs.LG", "cs.HC", "cs.CR", "cs.CV"}
CORE_CATS = {"eess.AS", "cs.SD", "cs.CL", "cs.MM"}

MODALITY = re.compile(
    r"\b(speech|spoken|audio|voice|acoustic|auditory|paralinguistic|prosod|"
    r"utterance|dialogue|dialog|conversation|sound|music|speaker|listen)\w*", re.I)
SIGNAL = re.compile(
    r"\b(benchmark|evaluat|assess|testbed|suite|leaderboard|probe|probing|diagnos|"
    r"llm|language model|gpt|multimodal|omni|lalm|slm|instruction|agent)\w*", re.I)


def request(url, attempt=0):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "spoken-llm-benchmark-atlas/1.0 (research index; contact speechlab0210@gmail.com)"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code == 503:
            wait = int(e.headers.get("Retry-After", "20"))
            print(f"    503 flow control, sleeping {wait}s", flush=True)
            time.sleep(wait + 1)
            return request(url, attempt)
        if attempt >= 4:
            raise
        time.sleep(10 * (attempt + 1))
        return request(url, attempt + 1)
    except Exception:  # noqa: BLE001
        if attempt >= 4:
            raise
        time.sleep(10 * (attempt + 1))
        return request(url, attempt + 1)


def records(setspec, frm, until):
    params = {"verb": "ListRecords", "metadataPrefix": "arXiv",
              "set": setspec, "from": frm, "until": until}
    url = OAI + urllib.parse.urlencode(params)
    page = 0
    while True:
        raw = request(url)
        root = ET.fromstring(raw)
        err = root.find(".//oai:error", NS)
        if err is not None:
            code = err.get("code", "?")
            if code == "noRecordsMatch":
                print(f"  [{setspec}] no records in window", flush=True)
                return
            # a silent empty result would look like "nothing to find" — refuse to fake success
            raise RuntimeError(f"OAI error [{code}]: {(err.text or '').strip()}")
        page += 1
        got = 0
        for rec in root.findall(".//oai:record", NS):
            meta = rec.find(".//arx:arXiv", NS)
            if meta is None:
                continue
            got += 1
            cats = (meta.findtext("arx:categories", "", NS) or "").split()
            yield {
                "id": meta.findtext("arx:id", "", NS),
                "title": " ".join((meta.findtext("arx:title", "", NS) or "").split()),
                "abstract": " ".join((meta.findtext("arx:abstract", "", NS) or "").split()),
                "published": meta.findtext("arx:created", "", NS),
                "categories": cats,
                "primary_category": cats[0] if cats else "",
                "authors": [
                    " ".join(x for x in [a.findtext("arx:forenames", "", NS),
                                         a.findtext("arx:keyname", "", NS)] if x)
                    for a in meta.findall(".//arx:author", NS)][:10],
                "url": f"https://arxiv.org/abs/{meta.findtext('arx:id','',NS)}",
            }
        token_el = root.find(".//oai:resumptionToken", NS)
        token = (token_el.text or "").strip() if token_el is not None else ""
        size = token_el.get("completeListSize") if token_el is not None else None
        print(f"  [{setspec}] page {page}: +{got} records"
              + (f" (of ~{size})" if size else ""), flush=True)
        if not token:
            return
        url = OAI + urllib.parse.urlencode({"verb": "ListRecords", "resumptionToken": token})
        time.sleep(5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="frm", required=True)
    ap.add_argument("--until", required=True)
    ap.add_argument("--sets", default="cs,eess")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    # arXiv rejects an `until` in the future ("until date too late") — clamp to yesterday
    from datetime import date, timedelta
    cap = (date.today() - timedelta(days=1)).isoformat()
    if args.until > cap:
        print(f"clamping --until {args.until} -> {cap} (arXiv rejects future dates)")
        args.until = cap

    out = ROOT / (args.out or f"raw/oai_{args.frm}_{args.until}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)

    seen, kept = {}, 0
    for setspec in args.sets.split(","):
        setspec = setspec.strip()
        if not setspec:
            continue
        print(f"== set {setspec} {args.frm}..{args.until}", flush=True)
        try:
            for r in records(setspec, args.frm, args.until):
                if r["id"] in seen:
                    continue
                cats = set(r["categories"])
                if not (cats & KEEP_CATS):
                    continue
                blob = r["title"] + " " + r["abstract"]
                if not MODALITY.search(blob):
                    continue
                # outside the core speech categories, demand an evaluation/LLM signal too
                if not (cats & CORE_CATS) and not SIGNAL.search(blob):
                    continue
                seen[r["id"]] = r
                kept += 1
        except Exception as e:  # noqa: BLE001
            print(f"  !! set {setspec} aborted: {e}", flush=True)

    with out.open("w", encoding="utf-8") as f:
        for r in sorted(seen.values(), key=lambda x: x["published"]):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nwrote {kept} speech-relevant records -> {out}")


if __name__ == "__main__":
    main()
