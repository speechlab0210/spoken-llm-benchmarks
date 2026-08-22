# Merge every mechanical harvest pool into one deduped candidate pool.
# Sources are independent on purpose (query API vs OAI-PMH), so the overlap statistics
# double as a coverage estimate: if OAI finds many papers the query API missed, keyword
# search alone would have under-covered the field.
# Usage: python scripts/merge_pools.py

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"

SOURCES = [
    ("queryapi", "candidates.jsonl"),
    ("queryapi", "candidates_gapfill.jsonl"),
    ("oai-eess", "oai_eess.jsonl"),
    ("oai-cs", "oai_cs.jsonl"),
]

MODEL_TERMS = [
    "speech language model", "spoken language model", "audio language model",
    "speech-language model", "audio-language model", "large audio language model",
    "speech llm", "audio llm", "spoken llm", "lalm", "salmonn", "qwen-audio", "qwen2-audio",
    "qwen2.5-omni", "qwen3-omni", "gpt-4o", "moshi", "glm-4-voice", "speechgpt", "kimi-audio",
    "step-audio", "minicpm-o", "audio flamingo", "gemini", "omni", "speechlm", "voxtral",
    "spoken dialogue model", "voice assistant", "speech-to-speech", "full-duplex",
    "end-to-end speech", "voice agent", "multimodal llm", "phi-4-multimodal", "audiolm",
]
BENCH_TERMS = [
    "benchmark", "evaluation suite", "evaluation framework", "test suite", "testbed",
    "we introduce", "we present", "we propose", "evaluation benchmark", "leaderboard",
    "diagnostic", "probing", "we release", "we construct", "we curate",
]
NEG_TERMS = [
    "speech enhancement", "speech separation", "voice conversion", "speaker verification",
    "beamforming", "echo cancellation", "hearing aid", "dereverberation",
]


def score(rec):
    text = (rec["title"] + " " + rec["abstract"]).lower()
    ti = rec["title"].lower()
    s = 0
    s += 6 * sum(1 for t in MODEL_TERMS if t in text)
    s += 3 * sum(1 for t in BENCH_TERMS if t in text)
    if "benchmark" in ti or "eval" in ti or "bench" in ti:
        s += 12
    if re.search(r"\b[A-Z][A-Za-z0-9]*-?Bench\b", rec["title"]):
        s += 15
    s -= 5 * sum(1 for t in NEG_TERMS if t in text)
    return s


def main():
    pool, per_source, first_seen = {}, Counter(), {}
    for tag, fname in SOURCES:
        p = RAW / fname
        if not p.exists():
            print(f"  (skip missing {fname})")
            continue
        n = 0
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            rid = r.get("id", "").strip()
            if not rid:
                continue
            n += 1
            if rid in pool:
                pool[rid].setdefault("found_in", []).append(tag)
                continue
            r["found_in"] = [tag]
            r["score"] = score(r)
            pool[rid] = r
            first_seen[rid] = tag
        per_source[f"{tag}:{fname}"] = n
        print(f"  {fname:<28} {n:>6} records   pool now {len(pool)}")

    recs = sorted(pool.values(), key=lambda r: (-r["score"], r.get("published", "")))
    out = RAW / "pool.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # coverage cross-check: what did each interface uniquely contribute?
    uniq = Counter(first_seen.values())
    both = sum(1 for r in recs if len(set(r["found_in"])) > 1)
    hi = sum(1 for r in recs if r["score"] >= 20)
    mid = sum(1 for r in recs if 8 <= r["score"] < 20)

    print(f"\nmerged pool: {len(recs)}  -> {out}")
    print(f"  first found by: {dict(uniq)}")
    print(f"  found by >1 interface: {both}")
    print(f"  score >=20: {hi}   8..19: {mid}   <8: {len(recs)-hi-mid}")
    (RAW / "pool_stats.json").write_text(json.dumps({
        "total": len(recs), "per_source": dict(per_source), "first_seen_by": dict(uniq),
        "multi_interface": both, "score_ge_20": hi, "score_8_19": mid,
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
