# Assemble data/benchmarks.json from classified entries + authoritative arXiv metadata.
# Agent output supplies judgement (in/out of scope, categories, prose summary).
# arXiv metadata supplies facts (title, date, id, venue). Facts always win.
# Usage: python scripts/assemble.py

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]


def slug(s):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (s or "").strip().lower()).strip("-")
    return re.sub(r"-{2,}", "-", s) or "unnamed"


def venue_from(meta):
    """Extract a venue string from journal_ref / comment, or None."""
    jr = (meta.get("journal_ref") or "").strip()
    if jr:
        return jr[:90]
    cm = (meta.get("comment") or "")
    m = re.search(
        r"\b(Accepted (?:to|at|by)|To appear (?:in|at)|Published (?:in|at)|Camera[- ]ready for)\s+([^.;]{3,70})",
        cm, re.I)
    if m:
        return m.group(2).strip().rstrip(",")
    m = re.search(
        r"\b((?:ICASSP|INTERSPEECH|Interspeech|ACL|EMNLP|NAACL|NeurIPS|ICLR|ICML|SLT|ASRU|AAAI|IJCAI|COLING|TMLR|ISMIR|WASPAA|EUSIPCO|ICME|MM)\s*'?\s*20\d\d)",
        cm)
    return m.group(1) if m else None


def main():
    classified = json.loads((ROOT / "raw/classified.json").read_text(encoding="utf-8"))
    meta = json.loads((ROOT / "raw/meta.json").read_text(encoding="utf-8"))
    roster = {r["key"]: r for r in json.loads((ROOT / "raw/roster.json").read_text(encoding="utf-8"))}
    tax = json.loads((ROOT / "data/taxonomy.json").read_text(encoding="utf-8"))
    valid_cats = {c["id"] for c in tax["categories"]}

    entries, dropped, badcat = [], [], Counter()
    used_ids = set()

    for e in classified:
        if not e.get("in_scope"):
            dropped.append((e.get("name") or e.get("key"), e.get("out_reason", "")))
            continue
        aid = e.get("arxiv_id")
        m = meta.get(aid)
        if not m:
            dropped.append((e.get("name"), "no arXiv metadata — refusing to publish an unverified entry"))
            continue

        cats = [c for c in (e.get("categories") or []) if c in valid_cats]
        for c in (e.get("categories") or []):
            if c not in valid_cats:
                badcat[c] += 1
        if not cats:
            dropped.append((e.get("name"), f"no valid category (agent said {e.get('categories')})"))
            continue

        bid = slug(e.get("id") or e.get("name"))
        base, n = bid, 2
        while bid in used_ids:
            bid = f"{base}-{n}"
            n += 1
        used_ids.add(bid)

        r = roster.get(e.get("key"), {})
        aliases = [a for a in (r.get("aliases") or []) if a and a.lower() != (e.get("name") or "").lower()]

        entry = {
            "id": bid,
            "name": e.get("name") or r.get("name") or m["title"][:40],
            "full_title": m["title"],                    # from arXiv, not the agent
            "arxiv_id": aid,
            "arxiv_date": m["arxiv_date"],               # v1 month, from arXiv
            "arxiv_date_full": m["arxiv_date_full"],
            "url": m["url"],
            "summary": e.get("summary") or "",
            "categories": cats[:3],
        }
        v = venue_from(m)
        if v:
            entry["venue"] = v
        for k_src, k_dst in [("tasks", "tasks"), ("languages", "languages"), ("metrics", "metrics")]:
            vals = [x for x in (e.get(k_src) or []) if x]
            if vals:
                entry[k_dst] = vals[:6]
        for k in ("io", "size", "notable"):
            if e.get(k):
                entry["note" if k == "notable" else k] = e[k]
        if aliases:
            entry["aka"] = aliases[:4]
        if r.get("url") and r["url"].startswith("http") and "arxiv.org" not in r["url"]:
            entry["code"] = r["url"]
        entries.append(entry)

    entries.sort(key=lambda x: (x["arxiv_date"], x["name"].lower()))

    out = {"generated": "assembled from raw/classified.json + raw/meta.json", "entries": entries}
    (ROOT / "data/benchmarks.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    cc = Counter(c for e in entries for c in e["categories"])
    yr = Counter(e["arxiv_date"][:4] for e in entries)
    print(f"wrote {len(entries)} benchmarks -> data/benchmarks.json")
    print(f"  dropped {len(dropped)}")
    print(f"  by year: {dict(sorted(yr.items()))}")
    print(f"  since 2025-01: {sum(1 for e in entries if e['arxiv_date'] >= '2025-01')}")
    print(f"  with venue: {sum(1 for e in entries if e.get('venue'))}")
    if badcat:
        print(f"  !! invalid categories seen: {dict(badcat)}")
    print("\n  category counts:")
    for k, v in cc.most_common():
        print(f"    {v:>3}  {k}")
    (ROOT / "raw/dropped.json").write_text(
        json.dumps(dropped, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
