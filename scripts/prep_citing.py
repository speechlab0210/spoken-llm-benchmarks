# Turn the citation graph into a work list of CITING papers worth reading for results.
#
# Organised by paper, not by (benchmark, paper) pair: a paper that reports on one of our
# benchmarks usually reports on several, so it should be fetched and read exactly once.
#
# Ranking favours papers that cite MANY of our benchmarks and look like they carry a
# results table. Surveys are demoted: they cite everything and report nothing.
#
# Usage: python scripts/prep_citing.py [--top 0]   (0 = all)

import argparse
import collections
import json
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]

SURVEY = re.compile(r"\b(a survey|survey of|systematic review|literature review|an overview of)\b", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=0)
    ap.add_argument("--size", type=int, default=4)
    args = ap.parse_args()

    cites = json.loads((ROOT / "raw/citations.json").read_text(encoding="utf-8"))
    bms = {b["id"]: b for b in
           json.loads((ROOT / "data/benchmarks.json").read_text(encoding="utf-8"))["entries"]}
    already = {b["arxiv_id"] for b in bms.values() if b.get("arxiv_id")}

    by = collections.defaultdict(lambda: {"benchmarks": [], "meta": None})
    for bid, v in cites.items():
        for c in v["citations"]:
            e = by[c["arxiv_id"]]
            e["benchmarks"].append({"id": bid, "name": bms[bid]["name"] if bid in bms else bid})
            if e["meta"] is None:
                e["meta"] = c

    work = []
    for aid, e in by.items():
        if aid in already:
            continue                      # its own results were extracted in the earlier passes
        m = e["meta"]
        title = m.get("title") or ""
        score = len(e["benchmarks"]) * 2 + m.get("reports_score", 0) * 3
        if SURVEY.search(title):
            score -= 12                   # surveys cite everything and report nothing
        work.append({
            "arxiv_id": aid,
            "title": title,
            "year": m.get("year"),
            "n_benchmarks": len(e["benchmarks"]),
            "benchmarks": sorted(e["benchmarks"], key=lambda x: x["name"])[:40],
            "rank": score,
        })

    work.sort(key=lambda w: (-w["rank"], -(w["year"] or 0)))
    if args.top:
        work = work[:args.top]

    (ROOT / "raw/citing_worklist.json").write_text(
        json.dumps(work, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "raw/citing_ids.txt").write_text(
        " ".join(w["arxiv_id"] for w in work), encoding="utf-8")

    outdir = ROOT / "raw/citing"
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("c_*.json"):
        old.unlink()
    n = 0
    for i in range(0, len(work), args.size):
        n += 1
        chunk = []
        for w in work[i:i + args.size]:
            chunk.append({
                "arxiv_id": w["arxiv_id"],
                "title": w["title"],
                "paper_text": f"C:/Users/tlkag/.openclaw/workspace/spoken-llm-benchmarks/raw/papers/{w['arxiv_id']}.txt",
                "look_for": [{"benchmark_id": b["id"], "name": b["name"]} for b in w["benchmarks"]],
            })
        (outdir / f"c_{n:03d}.json").write_text(
            json.dumps(chunk, ensure_ascii=False, indent=1), encoding="utf-8")

    cached = sum(1 for w in work if os.path.exists(ROOT / f"raw/papers/{w['arxiv_id']}.txt"))
    print(f"citing papers to read : {len(work)}")
    print(f"  already downloaded  : {cached}")
    print(f"  batches of {args.size}       : {n}")
    print(f"  cites >=5 of ours   : {sum(1 for w in work if w['n_benchmarks']>=5)}")
    print(f"  cites 1 of ours     : {sum(1 for w in work if w['n_benchmarks']==1)}")
    print("\ntop of the work list:")
    for w in work[:10]:
        print(f"   rank {w['rank']:>3}  {w['n_benchmarks']:>2} bm  {w['arxiv_id']}  {w['title'][:60]}")


if __name__ == "__main__":
    main()
