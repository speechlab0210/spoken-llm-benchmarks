# Split the harvested candidate pool into agent-sized triage batches.
# Mechanical pre-filter is RECALL-oriented: it only drops papers with no speech/audio/LLM
# signal at all. Precision is the agents' job.
# Usage: python scripts/make_batches.py [--size 140] [--min-score 0]

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]

# must mention some speech/audio modality...
MODALITY = re.compile(
    r"\b(speech|spoken|audio|voice|acoustic|auditory|paralinguistic|prosod|phonet|"
    r"utterance|listener|listening|dialogue|dialog|conversation|sound|music|speaker)\b", re.I)
# ...and some model-ish or evaluation-ish signal
SIGNAL = re.compile(
    r"\b(benchmark|evaluat|assess|test\s?set|testbed|suite|leaderboard|probe|probing|"
    r"diagnos|llm|language model|gpt|multimodal|omni|lalm|slm|foundation model|"
    r"instruction|zero-shot|in-context|agent)\b", re.I)
# hard drops: clearly a component-system paper with no general-purpose model in sight
HARD_DROP = re.compile(
    r"\b(speech enhancement|speech separation|voice conversion|speaker verification|"
    r"beamform|echo cancellation|hearing aid|cochlear|packet loss concealment|"
    r"bandwidth extension|dereverberation|source separation)\b", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=140)
    ap.add_argument("--min-score", type=int, default=0)
    ap.add_argument("--infile", default="raw/candidates.jsonl")
    args = ap.parse_args()

    src = ROOT / args.infile
    recs = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"pool: {len(recs)}")

    kept, dropped = [], {"no_modality": 0, "no_signal": 0, "hard_drop": 0, "low_score": 0}
    for r in recs:
        blob = r["title"] + " " + r["abstract"]
        if r.get("score", 0) < args.min_score:
            dropped["low_score"] += 1
            continue
        if not MODALITY.search(blob):
            dropped["no_modality"] += 1
            continue
        if not SIGNAL.search(blob):
            dropped["no_signal"] += 1
            continue
        # hard-drop only when there is ALSO no general-model signal (keep e.g. "LALM robustness to noise")
        if HARD_DROP.search(blob) and not re.search(
                r"\b(llm|language model|lalm|slm|gpt|omni|multimodal|benchmark)\b", blob, re.I):
            dropped["hard_drop"] += 1
            continue
        kept.append(r)

    kept.sort(key=lambda r: (-r.get("score", 0), r.get("published", "")))
    print(f"kept: {len(kept)}   dropped: {dropped}")

    outdir = ROOT / "raw" / "batches"
    for old in outdir.glob("batch_*.txt"):
        old.unlink()
    outdir.mkdir(parents=True, exist_ok=True)

    n = 0
    for i in range(0, len(kept), args.size):
        chunk = kept[i:i + args.size]
        n += 1
        lines = []
        for r in chunk:
            cats = ",".join(r.get("categories", [])[:4])
            abstract = r["abstract"]
            if len(abstract) > 1400:
                abstract = abstract[:1400] + " …"
            lines.append(
                f"### {r['id']}  [{r.get('published','')[:10]}]  ({cats})\n"
                f"TITLE: {r['title']}\n"
                f"ABSTRACT: {abstract}\n"
            )
        (outdir / f"batch_{n:03d}.txt").write_text(
            f"# batch {n} — {len(chunk)} arXiv papers\n"
            f"# Each record's arXiv ID is GROUND TRUTH from the arXiv API. Copy it exactly; never alter it.\n\n"
            + "\n".join(lines), encoding="utf-8")

    print(f"wrote {n} batches of <= {args.size} to {outdir}")
    (ROOT / "raw" / "batches" / "INDEX.json").write_text(
        json.dumps({"batches": n, "size": args.size, "kept": len(kept),
                    "pool": len(recs), "dropped": dropped}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
