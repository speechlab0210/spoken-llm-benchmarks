# Resolve benchmark titles -> arXiv id + v1 date, MECHANICALLY (arXiv API title search).
# Never guesses: a match must clear a token-overlap threshold against the queried title.
# Input : JSON list [{"name":..., "full_title":...}, ...] on stdin or via --infile
# Output: JSON list with resolved arxiv_id / arxiv_date / matched_title / confidence
# Usage : python scripts/resolve_arxiv.py --infile raw/to_resolve.json --out raw/resolved.json

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
ATOM = "{http://www.w3.org/2005/Atom}"
API = "http://export.arxiv.org/api/query?"
SLEEP = 3.2
STOP = {"a", "an", "the", "of", "for", "and", "or", "on", "in", "to", "with", "is", "are",
        "can", "do", "does", "how", "what", "towards", "toward", "via", "using", "by"}


def toks(s):
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if w not in STOP and len(w) > 1}


def search(query, max_results=12, attempt=0):
    url = API + urllib.parse.urlencode({
        "search_query": query, "start": 0, "max_results": max_results,
        "sortBy": "relevance", "sortOrder": "descending"})
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return r.read()
    except Exception as e:  # noqa: BLE001
        if attempt >= 3:
            print(f"    !! {e}", file=sys.stderr)
            return None
        time.sleep(8 * (attempt + 1))
        return search(query, max_results, attempt + 1)


def parse(xml_bytes):
    out = []
    if not xml_bytes:
        return out
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return out
    for e in root.findall(ATOM + "entry"):
        m = re.search(r"abs/([^v]+)v(\d+)", e.findtext(ATOM + "id", ""))
        if not m:
            continue
        out.append({
            "id": m.group(1),
            "title": " ".join((e.findtext(ATOM + "title") or "").split()),
            "published": e.findtext(ATOM + "published", "")[:10],
            "abstract": " ".join((e.findtext(ATOM + "summary") or "").split())[:400],
        })
    return out


def resolve(name, full_title):
    """Return best match or None. Requires strong title overlap OR name-in-title + topical fit."""
    want = toks(full_title) if full_title else toks(name)
    tried, cands = [], {}

    if full_title:
        q = re.sub(r'["\\]', " ", full_title)[:220]
        tried.append(f'ti:"{q}"')
        tried.append(f'all:"{q}"')
    tried.append(f'ti:"{name}"')
    tried.append(f'all:"{name}" AND (cat:eess.AS OR cat:cs.SD OR cat:cs.CL)')

    for q in tried:
        for c in parse(search(q)):
            cands.setdefault(c["id"], c)
        time.sleep(SLEEP)
        if len(cands) >= 20:
            break

    best, best_score = None, 0.0
    nm = name.lower().strip()
    for c in cands.values():
        got = toks(c["title"])
        if not want or not got:
            continue
        jac = len(want & got) / len(want | got)
        cov = len(want & got) / len(want)
        score = max(jac, cov * 0.92)
        # a benchmark name appearing verbatim in the title is a strong signal
        if nm and re.search(r"(?<![a-z0-9])" + re.escape(nm) + r"(?![a-z0-9])", c["title"].lower()):
            score = max(score, 0.78)
        if score > best_score:
            best, best_score = c, score
    if best and best_score >= 0.62:
        return best, round(best_score, 3)
    return None, round(best_score, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    items = json.loads((ROOT / args.infile).read_text(encoding="utf-8"))
    out = []
    for i, it in enumerate(items, 1):
        name = it.get("name") or ""
        title = it.get("full_title") or ""
        hit, conf = resolve(name, title)
        rec = dict(it)
        if hit:
            rec.update({"arxiv_id": hit["id"], "arxiv_date": hit["published"][:7],
                        "arxiv_date_full": hit["published"], "matched_title": hit["title"],
                        "confidence": conf, "resolved": True})
            print(f"{i:>3}/{len(items)} OK   {name:<28} -> {hit['id']} ({conf}) {hit['title'][:64]}")
        else:
            rec.update({"resolved": False, "confidence": conf})
            print(f"{i:>3}/{len(items)} MISS {name:<28} (best {conf})")
        out.append(rec)

    (ROOT / args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for r in out if r.get("resolved"))
    print(f"\nresolved {ok}/{len(out)} -> {args.out}")


if __name__ == "__main__":
    main()
