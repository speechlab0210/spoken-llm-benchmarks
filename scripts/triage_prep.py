# Recall safety net: find benchmark papers the discovery agents may have missed.
# Takes the independent OAI-PMH pools, removes anything already catalogued or already
# considered, scores the rest, and writes agent-sized triage batches.
#
# The point is honesty about coverage: keyword-driven discovery has a recall ceiling, and
# this pass measures and closes part of it rather than assuming it away.
#
# Usage: python scripts/triage_prep.py [--min-score 22] [--size 120]

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"

MODEL_TERMS = [
    "speech language model", "spoken language model", "audio language model",
    "speech-language model", "audio-language model", "large audio language model",
    "speech llm", "audio llm", "spoken llm", "lalm", "salmonn", "qwen-audio", "qwen2-audio",
    "qwen2.5-omni", "qwen3-omni", "gpt-4o", "moshi", "glm-4-voice", "speechgpt", "kimi-audio",
    "step-audio", "minicpm-o", "audio flamingo", "gemini", "omni-modal", "speechlm", "voxtral",
    "spoken dialogue model", "voice assistant", "speech-to-speech", "full-duplex", "duplex",
    "end-to-end speech", "voice agent", "multimodal llm", "phi-4-multimodal", "audiolm",
    "spoken language understanding", "audio understanding",
]
BENCH_TERMS = [
    "benchmark", "evaluation suite", "evaluation framework", "test suite", "testbed",
    "we introduce", "we present", "we propose", "evaluation benchmark", "leaderboard",
    "diagnostic", "probing", "we release", "we construct", "we curate", "evaluate",
]
# these signal a component-task benchmark that our scope rule excludes
NEG_TERMS = [
    "speech enhancement", "speech separation", "voice conversion", "speaker verification",
    "beamforming", "echo cancellation", "hearing aid", "dereverberation", "packet loss",
    "text-to-speech synthesis", "tts system", "speech synthesis quality", "vocoder",
    "speaker diarization", "keyword spotting", "wake word", "audio codec", "neural codec",
    "video-to-audio", "text-to-audio generation", "音", "singing voice",
]


def score(rec):
    text = (rec.get("title", "") + " " + rec.get("abstract", "")).lower()
    ti = rec.get("title", "").lower()
    s = 0
    s += 6 * sum(1 for t in MODEL_TERMS if t in text)
    s += 3 * sum(1 for t in BENCH_TERMS if t in text)
    if "benchmark" in ti or "eval" in ti or "bench" in ti:
        s += 12
    if re.search(r"\b[A-Z][A-Za-z0-9]*-?Bench\b", rec.get("title", "")):
        s += 15
    s -= 6 * sum(1 for t in NEG_TERMS if t in text)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-score", type=int, default=22)
    ap.add_argument("--size", type=int, default=120)
    args = ap.parse_args()

    # everything we have already decided on, in either direction
    catalogued = {b["arxiv_id"] for b in
                  json.loads((ROOT / "data/benchmarks.json").read_text(encoding="utf-8"))["entries"]
                  if b.get("arxiv_id")}
    considered = set(catalogued)
    for f in ("raw/classified.json",):
        p = ROOT / f
        if p.exists():
            for e in json.loads(p.read_text(encoding="utf-8")):
                if e.get("arxiv_id"):
                    considered.add(e["arxiv_id"])

    pool = {}
    for fname in ("oai_eess.jsonl", "oai_cs.jsonl"):
        p = RAW / fname
        if not p.exists():
            print(f"  (missing {fname})")
            continue
        n = 0
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            n += 1
            if r["id"] in considered or r["id"] in pool:
                continue
            pool[r["id"]] = r
        print(f"  {fname}: {n} records")

    scored = []
    for r in pool.values():
        r["score"] = score(r)
        if r["score"] >= args.min_score:
            scored.append(r)
    scored.sort(key=lambda r: -r["score"])

    outdir = RAW / "triage"
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("t_*.json"):
        old.unlink()

    n = 0
    for i in range(0, len(scored), args.size):
        n += 1
        chunk = [{"arxiv_id": r["id"], "date": (r.get("published") or "")[:10],
                  "title": r["title"], "abstract": r["abstract"][:1200],
                  "cats": r.get("categories", [])[:4], "score": r["score"]}
                 for r in scored[i:i + args.size]]
        (outdir / f"t_{n:02d}.json").write_text(
            json.dumps(chunk, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\npool not yet considered: {len(pool)}")
    print(f"score >= {args.min_score}: {len(scored)}  ->  {n} triage batches of <= {args.size}")
    (RAW / "triage_stats.json").write_text(json.dumps(
        {"pool_unconsidered": len(pool), "above_threshold": len(scored),
         "batches": n, "min_score": args.min_score,
         "already_considered": len(considered)}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
