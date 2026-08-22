# Merge benchmark mentions from many discovery agents into one deduped roster.
# Dedup key: arXiv id when present, else a normalised name. Keeps every distinct
# arXiv id ever asserted for a name so conflicts are visible rather than silently resolved.
# Usage: python scripts/merge_mentions.py --infile raw/mentions.json --out raw/roster.json

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]

# names that are not benchmarks (models, orgs, generic words) sometimes leak in
NOT_A_BENCHMARK = {
    "gpt-4o", "qwen2-audio", "qwen2.5-omni", "moshi", "salmonn", "whisper",
    "llm", "lalm", "slm", "n/a", "none", "unknown", "various",
}


def norm(name):
    s = (name or "").strip().lower()
    s = re.sub(r"\s*\(.*?\)\s*", " ", s)        # drop parentheticals
    s = re.sub(r"[‐-―]", "-", s)       # unicode dashes -> hyphen
    s = re.sub(r"[^a-z0-9]+", "", s)             # AIR-Bench == AIR Bench == airbench
    return s


def clean_id(v):
    if not v:
        return None
    m = re.search(r"(\d{4}\.\d{4,5})", str(v))
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    mentions = json.loads((ROOT / args.infile).read_text(encoding="utf-8"))
    if isinstance(mentions, dict):
        mentions = mentions.get("mentions", [])
    print(f"raw mentions: {len(mentions)}")

    # pass 1: group by normalised name
    by_name = {}
    for m in mentions:
        name = (m.get("name") or "").strip()
        if not name or norm(name) in {norm(x) for x in NOT_A_BENCHMARK}:
            continue
        k = norm(name)
        if not k:
            continue
        by_name.setdefault(k, []).append(m)

    # pass 2: if two names share a confirmed arXiv id, they are the same benchmark
    id_to_key = {}
    alias_of = {}
    for k, group in by_name.items():
        for m in group:
            aid = clean_id(m.get("arxiv_id"))
            if not aid:
                continue
            if aid in id_to_key and id_to_key[aid] != k:
                alias_of[k] = id_to_key[aid]
            else:
                id_to_key.setdefault(aid, k)

    merged = {}
    for k, group in by_name.items():
        target = alias_of.get(k, k)
        merged.setdefault(target, []).extend(group)

    roster = []
    for k, group in merged.items():
        names = Counter((m.get("name") or "").strip() for m in group)
        display = names.most_common(1)[0][0]
        aliases = sorted({n for n in names if n and n != display})
        ids = Counter(clean_id(m.get("arxiv_id")) for m in group if clean_id(m.get("arxiv_id")))
        titles = Counter((m.get("full_title") or "").strip() for m in group
                         if (m.get("full_title") or "").strip())
        cats = Counter(m.get("category_guess") for m in group if m.get("category_guess"))
        urls = Counter((m.get("url") or "").strip() for m in group if (m.get("url") or "").strip())
        years = Counter((m.get("year") or "").strip() for m in group if (m.get("year") or "").strip())
        lines = [m.get("one_line") for m in group if m.get("one_line")]

        roster.append({
            "key": k,
            "name": display,
            "aliases": aliases,
            "full_title": titles.most_common(1)[0][0] if titles else None,
            "arxiv_id": ids.most_common(1)[0][0] if ids else None,
            "arxiv_id_conflicts": [i for i, _ in ids.most_common()[1:]] if len(ids) > 1 else [],
            "url": urls.most_common(1)[0][0] if urls else None,
            "year": years.most_common(1)[0][0] if years else None,
            "category_guesses": [c for c, _ in cats.most_common()],
            "one_lines": lines[:4],
            "mention_count": len(group),
            "sources": sorted({(m.get("evidence") or "")[:110] for m in group})[:5],
        })

    roster.sort(key=lambda r: (-r["mention_count"], r["name"].lower()))
    (ROOT / args.out).write_text(json.dumps(roster, ensure_ascii=False, indent=2), encoding="utf-8")

    with_id = sum(1 for r in roster if r["arxiv_id"])
    conflicts = [r["name"] for r in roster if r["arxiv_id_conflicts"]]
    print(f"unique benchmarks: {len(roster)}  (with arXiv id: {with_id}, needing resolution: {len(roster)-with_id})")
    if conflicts:
        print(f"!! arXiv id conflicts to adjudicate ({len(conflicts)}): {', '.join(conflicts[:12])}")
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
