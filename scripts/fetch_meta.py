# Fetch authoritative arXiv metadata for a list of ids, in batches of 100 (id_list).
# This is how title / abstract / v1 date / categories enter the catalogue: from the API,
# never from an agent's recall. Cheap enough to re-run whenever the roster changes.
# Usage: python scripts/fetch_meta.py --ids-from raw/roster_ids.json --out raw/meta.json

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
ARX = "{http://arxiv.org/schemas/atom}"
API = "http://export.arxiv.org/api/query?"
BATCH = 100


def fetch(ids, attempt=0):
    url = API + urllib.parse.urlencode({"id_list": ",".join(ids), "max_results": len(ids)})
    try:
        with urllib.request.urlopen(url, timeout=90) as r:
            return r.read()
    except Exception as e:  # noqa: BLE001
        if attempt >= 4:
            print(f"  !! batch failed: {e}", file=sys.stderr)
            return None
        time.sleep(10 * (attempt + 1))
        return fetch(ids, attempt + 1)


def parse(xml_bytes):
    out = {}
    if not xml_bytes:
        return out
    root = ET.fromstring(xml_bytes)
    for e in root.findall(ATOM + "entry"):
        m = re.search(r"abs/([^v]+)v(\d+)", e.findtext(ATOM + "id", ""))
        if not m:
            continue
        pub = e.findtext(ATOM + "published", "")[:10]
        cats = [c.get("term") for c in e.findall(ATOM + "category")]
        pc = e.find(ARX + "primary_category")
        out[m.group(1)] = {
            "arxiv_id": m.group(1),
            "latest_version": int(m.group(2)),
            "title": " ".join((e.findtext(ATOM + "title") or "").split()),
            "abstract": " ".join((e.findtext(ATOM + "summary") or "").split()),
            "arxiv_date_full": pub,
            "arxiv_date": pub[:7],
            "updated": e.findtext(ATOM + "updated", "")[:10],
            "authors": [a.findtext(ATOM + "name") for a in e.findall(ATOM + "author")],
            "primary_category": pc.get("term") if pc is not None else "",
            "categories": cats,
            "comment": " ".join((e.findtext(ARX + "comment") or "").split()),
            "journal_ref": " ".join((e.findtext(ARX + "journal_ref") or "").split()),
            "doi": e.findtext(ARX + "doi", ""),
            "url": f"https://arxiv.org/abs/{m.group(1)}",
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids-from", required=True, help="JSON list of arXiv ids, or list of objects with arxiv_id")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    data = json.loads((ROOT / args.ids_from).read_text(encoding="utf-8"))
    ids = []
    for x in data:
        v = x if isinstance(x, str) else (x.get("arxiv_id") or "")
        m = re.search(r"(\d{4}\.\d{4,5})", str(v))
        if m and m.group(1) not in ids:
            ids.append(m.group(1))
    print(f"fetching metadata for {len(ids)} arXiv ids")

    meta = {}
    for i in range(0, len(ids), BATCH):
        chunk = ids[i:i + BATCH]
        got = parse(fetch(chunk))
        meta.update(got)
        print(f"  batch {i // BATCH + 1}: asked {len(chunk)}, got {len(got)}, total {len(meta)}")
        time.sleep(3.2)

    missing = [i for i in ids if i not in meta]
    (ROOT / args.out).write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {len(meta)} -> {args.out}")
    if missing:
        print(f"!! {len(missing)} ids returned nothing (bad id?): {missing[:20]}")


if __name__ == "__main__":
    main()
