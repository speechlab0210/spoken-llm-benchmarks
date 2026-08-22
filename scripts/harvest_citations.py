# For every catalogued benchmark, find the papers that CITE it (Semantic Scholar graph),
# keep the ones on arXiv, and score how likely each is to actually REPORT results on that
# benchmark rather than merely mention it in related work.
#
# Citing != using. This script only produces candidates; whether a paper really reports
# numbers on the benchmark is decided later, by reading its tables.
#
# Usage: python scripts/harvest_citations.py [--limit-per 200] [--out raw/citations.json]

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
API = "https://api.semanticscholar.org/graph/v1/paper/arXiv:{}/citations"
FIELDS = "title,abstract,externalIds,year,venue,citationCount"
UA = {"User-Agent": "spoken-llm-benchmark-atlas/1.0 (research index; speechlab0210@gmail.com)"}

# a paper that REPORTS on a benchmark usually looks like an evaluation or a model report
REPORTS = re.compile(
    r"\b(we evaluate|we benchmark|we compare|evaluated on|results on|outperform|achiev\w+|"
    r"state-of-the-art|technical report|we present .{0,40}model|our model|we introduce .{0,40}model|"
    r"experiments? on|we report|baseline|leaderboard|zero-shot|fine-tun)", re.I)
BENCHY = re.compile(r"\b(benchmark|evaluation|eval|suite|testbed|survey)\b", re.I)


def get(url, attempt=0):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code in (429, 504) and attempt < 6:
            wait = 12 * (attempt + 1)
            print(f"      {e.code}, sleeping {wait}s", flush=True)
            time.sleep(wait)
            return get(url, attempt + 1)
        if e.code == 404:
            return None
        if attempt < 3:
            time.sleep(8 * (attempt + 1))
            return get(url, attempt + 1)
        return None
    except Exception:  # noqa: BLE001
        if attempt < 3:
            time.sleep(8 * (attempt + 1))
            return get(url, attempt + 1)
        return None


def citations_for(aid, cap):
    out, offset = [], 0
    while offset < cap:
        url = f"{API.format(aid)}?fields={FIELDS}&limit=100&offset={offset}"
        d = get(url)
        if not d:
            break
        batch = d.get("data", [])
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
        offset += 100
        time.sleep(1.2)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-per", type=int, default=300)
    ap.add_argument("--out", default="raw/citations.json")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    bms = json.loads((ROOT / "data/benchmarks.json").read_text(encoding="utf-8"))["entries"]
    bms = [b for b in bms if b.get("arxiv_id")]
    out_path = ROOT / args.out
    result = {}
    if args.resume and out_path.exists():
        result = json.loads(out_path.read_text(encoding="utf-8"))
        print(f"resuming: {len(result)} benchmarks already done")

    for i, b in enumerate(bms, 1):
        if b["id"] in result:
            continue
        cites = citations_for(b["arxiv_id"], args.limit_per)
        keep = []
        for c in cites:
            p = c.get("citingPaper") or {}
            ax = (p.get("externalIds") or {}).get("ArXiv")
            if not ax:
                continue
            blob = (p.get("title") or "") + " " + (p.get("abstract") or "")
            keep.append({
                "arxiv_id": ax,
                "title": " ".join((p.get("title") or "").split()),
                "year": p.get("year"),
                "venue": p.get("venue") or "",
                "cited_by": p.get("citationCount") or 0,
                # cheap prior on "is this a paper that would carry a results table?"
                "reports_score": (2 if REPORTS.search(blob) else 0) + (1 if BENCHY.search(blob) else 0),
            })
        result[b["id"]] = {"benchmark": b["id"], "name": b["name"],
                           "arxiv_id": b["arxiv_id"], "citations": keep}
        print(f"{i:>3}/{len(bms)}  {b['name'][:34]:<36} cited by {len(cites):>4}, "
              f"on arXiv {len(keep):>4}", flush=True)
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        time.sleep(1.2)

    tot = sum(len(v["citations"]) for v in result.values())
    uniq = len({c["arxiv_id"] for v in result.values() for c in v["citations"]})
    print(f"\n{len(result)} benchmarks; {tot} citing-arXiv pairs; {uniq} unique citing papers")


if __name__ == "__main__":
    main()
