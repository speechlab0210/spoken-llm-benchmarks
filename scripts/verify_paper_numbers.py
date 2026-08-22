# Recompute every headline number in paper/PAPER.md directly from data/*.json.
# This is the paper's audit trail: a reviewer runs this and compares to the text.
# It also writes results_manifest.json, mapping each claim to the file it comes from.
#
# Usage: python scripts/verify_paper_numbers.py [--write-manifest]

import argparse
import collections
import json
import re
import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-manifest", action="store_true")
    args = ap.parse_args()

    bms = load("data/benchmarks.json")["entries"]
    cells = load("data/results.json")["cells"]
    models = load("data/models.json")["entries"]
    tax = load("data/taxonomy.json")["categories"]
    bm = {b["id"]: b for b in bms}

    def own(c):
        a = bm.get(c["benchmark"], {}).get("arxiv_id")
        return bool(a) and c.get("source_url", "").endswith(a)

    claims = []

    def claim(key, value, how):
        claims.append({"claim": key, "value": value, "recompute": how})

    # --- catalogue shape
    claim("benchmarks_total", len(bms), "len(data/benchmarks.json.entries)")
    yr = collections.Counter(b["arxiv_date"][:4] for b in bms)
    claim("by_year", dict(sorted(yr.items())), "Counter(arxiv_date[:4])")
    claim("pre_2025", sum(1 for b in bms if b["arxiv_date"] < "2025-01"), "arxiv_date < 2025-01")
    claim("since_2025", sum(1 for b in bms if b["arxiv_date"] >= "2025-01"), "arxiv_date >= 2025-01")
    q = collections.Counter()
    for b in bms:
        y, m = b["arxiv_date"].split("-")
        q[f"{y}Q{(int(m)-1)//3+1}"] += 1
    claim("by_quarter_2024plus", {k: q[k] for k in sorted(q) if k >= "2024Q1"}, "quarter of arxiv_date")
    claim("multi_category", sum(1 for b in bms if len(b["categories"]) > 1), "len(categories) > 1")
    claim("categories", len(tax), "len(data/taxonomy.json.categories)")
    grp = collections.Counter()
    T = {c["id"]: c for c in tax}
    for b in bms:
        for c in b["categories"]:
            grp[T[c]["group"]] += 1
    claim("category_slots_by_group", dict(grp.most_common()), "count of (benchmark, category) pairs per group")

    # --- results shape
    claim("result_cells", len(cells), "len(data/results.json.cells)")
    claim("models", len(models), "len(data/models.json.entries)")
    withres = {c["benchmark"] for c in cells}
    claim("benchmarks_with_results", len(withres), "distinct cells[].benchmark")
    claim("benchmarks_without_results", len(bms) - len(withres), "benchmarks minus the above")
    claim("distinct_source_papers", len({c.get("source_url") for c in cells}), "distinct cells[].source_url")
    claim("cells_every_one_sourced", all(c.get("source") for c in cells), "all cells carry a source")

    # --- adoption: the paper's section 5.6 argument
    third = collections.defaultdict(set)
    for c in cells:
        if not own(c):
            third[c["benchmark"]].add(c.get("source_url"))
    claim("cells_from_third_party", sum(1 for c in cells if not own(c)),
          "cells whose source_url is NOT the benchmark's own arXiv id")
    claim("benchmarks_run_by_others", len(third),
          "benchmarks with >=1 cell from a paper other than their own")
    claim("benchmarks_only_self_reported", len(withres) - len(third),
          "have results, but every cell is from their own paper")
    d = collections.Counter(len(v) for v in third.values())
    claim("benchmarks_used_by_5plus_papers", sum(n for k, n in d.items() if k >= 5), "third-party source count >= 5")
    top = sorted(third.items(), key=lambda x: -len(x[1]))[:6]
    claim("most_reused_benchmarks", {bm[k]["name"]: len(v) for k, v in top}, "top benchmarks by third-party paper count")

    # --- concentration
    mc = collections.Counter(c["model"] for c in cells)
    nm = {m["id"]: m["name"] for m in models}
    top9 = mc.most_common(9)
    claim("top9_models", {nm[k]: v for k, v in top9}, "Counter(cells[].model).most_common(9)")
    claim("top9_share_pct", round(sum(v for _, v in top9) / len(cells) * 100), "share of cells held by the top 9 models")
    cov = [len({c["model"] for c in cells if c["benchmark"] == b}) for b in withres]
    claim("median_models_per_benchmark", statistics.median(cov), "median distinct models per benchmark with results")
    claim("matrix_density_pct", round(len(cells) / (len(withres) * len(models)) * 100, 1),
          "cells / (benchmarks_with_results * models)")

    # --- aggregate-vs-component spread (section 4.6 / 5.3 / 7.1)
    AGG = re.compile(r"(overall|average|\bavg\b|\bmean\b|\btotal\b|composite|aggregate|macro)", re.I)
    claim("benchmarks_reporting_an_aggregate",
          len({c["benchmark"] for c in cells if AGG.search(c["metric"])}),
          "benchmarks with >=1 aggregate-named metric")
    g = collections.defaultdict(list)
    for c in cells:
        try:
            v = float(c["value"])
        except (TypeError, ValueError):
            continue
        g[(c["benchmark"], c["model"], c.get("source_url", ""))].append((c["metric"], v))
    spreads = []
    for _, vs in g.items():
        agg = [v for m, v in vs if AGG.search(m)]
        comp = [v for m, v in vs if not AGG.search(m)]
        if agg and len(comp) >= 4 and min(comp) >= 0 and max(comp) <= 100:
            spreads.append(max(comp) - min(comp))
    claim("aggregate_pairs_with_4plus_components", len(spreads),
          "(benchmark, model, source) groups with an aggregate + >=4 in-range components")
    claim("median_component_spread", round(statistics.median(spreads), 1) if spreads else None,
          "median of (max-min) over those components")

    for c in claims:
        v = c["value"]
        print(f"  {c['claim']:<36} {v if not isinstance(v, dict) else json.dumps(v, ensure_ascii=False)}")

    if args.write_manifest:
        manifest = {
            "schema": "airr/results_manifest/v1",
            "paper": "paper/PAPER.md",
            "regenerate": "python scripts/verify_paper_numbers.py --write-manifest",
            "note": ("Every number in the paper is recomputed from data/*.json by this script. "
                     "The data files are themselves derived: data/benchmarks.json from the arXiv API "
                     "(harvest_arxiv.py, harvest_oai.py, fetch_meta.py) plus agent triage, and "
                     "data/results.json from tables copied out of the papers listed in each cell's "
                     "source_url (fetch_paper.py, canon_models.py). No number was produced by running "
                     "a model on a benchmark; every cell is a published claim by the cited paper."),
            "inputs": {
                "data/benchmarks.json": "catalogue, one entry per benchmark",
                "data/results.json": "flat model x benchmark cells; every cell carries source + source_url",
                "data/models.json": "model registry (row labels)",
                "data/taxonomy.json": "19 categories in 6 groups",
            },
            "claims": claims,
        }
        (ROOT / "results_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nwrote results_manifest.json ({len(claims)} claims)")


if __name__ == "__main__":
    main()
