# Daily arXiv crawl for the Spoken LLM Benchmark Atlas.
# ZERO AI: pure arXiv API + regex scoring. Scripts do not hallucinate.
# Writes data/latest.json (the "New on arXiv" feed) and appends raw/seen.jsonl for dedup.
# Anything flagged here is a CANDIDATE only; promotion into data/benchmarks.json is a
# separate reviewed step (see DAILY-RUN.md).
#
# Usage: python scripts/daily_crawl.py [--days 3] [--rebuild]

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAWD = ROOT / "raw"
LOGS = ROOT / "logs"
ATOM = "{http://www.w3.org/2005/Atom}"
ARX = "{http://arxiv.org/schemas/atom}"
API = "http://export.arxiv.org/api/query?"
SLEEP = 3.2

QUERIES = [
    '(cat:eess.AS OR cat:cs.SD) AND (abs:benchmark OR ti:benchmark OR abs:evaluation OR ti:evaluation OR abs:testbed) AND {D}',
    'cat:cs.CL AND (abs:speech OR abs:audio OR abs:spoken OR abs:voice) AND (abs:benchmark OR ti:benchmark OR abs:evaluation) AND {D}',
    '(abs:"speech language model" OR abs:"spoken language model" OR abs:"audio language model" OR abs:"speech LLM" OR abs:"audio LLM" OR abs:"spoken dialogue" OR abs:"speech-to-speech" OR abs:"full-duplex" OR abs:"voice assistant" OR abs:"voice agent" OR abs:"omni-modal") AND {D}',
    '(cat:cs.AI OR cat:cs.LG OR cat:cs.MM OR cat:cs.HC OR cat:cs.CR) AND (abs:audio OR abs:speech OR abs:spoken) AND (abs:benchmark OR abs:LALM OR abs:SpeechLM OR abs:"audio-language") AND {D}',
]

MODEL_TERMS = [
    "speech language model", "spoken language model", "audio language model",
    "speech-language model", "audio-language model", "large audio language model",
    "speech llm", "audio llm", "spoken llm", "lalm", "salmonn", "qwen-audio", "qwen2-audio",
    "qwen2.5-omni", "qwen3-omni", "gpt-4o", "moshi", "glm-4-voice", "speechgpt", "kimi-audio",
    "step-audio", "minicpm-o", "audio flamingo", "gemini", "omni", "speechlm", "voxtral",
    "spoken dialogue model", "voice assistant", "speech-to-speech", "full-duplex",
    "end-to-end speech", "voice agent", "multimodal llm", "phi-4-multimodal",
]
BENCH_TERMS = [
    "benchmark", "evaluation suite", "evaluation framework", "test suite", "testbed",
    "we introduce", "we present", "we propose", "evaluation benchmark", "leaderboard",
    "diagnostic", "probing", "we release", "eval",
]
NEG_TERMS = [
    "speech enhancement", "speech separation", "voice conversion", "speaker verification",
    "anti-spoofing countermeasure", "acoustic echo", "beamforming", "hearing aid",
]


def fetch(query, attempt=0):
    url = API + urllib.parse.urlencode({
        "search_query": query, "start": 0, "max_results": 200,
        "sortBy": "submittedDate", "sortOrder": "descending",
    })
    try:
        with urllib.request.urlopen(url, timeout=90) as r:
            return r.read()
    except Exception as e:  # noqa: BLE001
        if attempt >= 3:
            raise
        time.sleep(8 * (attempt + 1))
        return fetch(query, attempt + 1)


def parse(xml_bytes):
    root = ET.fromstring(xml_bytes)
    out = []
    for e in root.findall(ATOM + "entry"):
        m = re.search(r"abs/([^v]+)v(\d+)", e.findtext(ATOM + "id", ""))
        if not m:
            continue
        out.append({
            "id": m.group(1),
            "title": " ".join((e.findtext(ATOM + "title") or "").split()),
            "abstract": " ".join((e.findtext(ATOM + "summary") or "").split()),
            "published": e.findtext(ATOM + "published", ""),
            "authors": [a.findtext(ATOM + "name") for a in e.findall(ATOM + "author")][:8],
            "primary_category": (e.find(ARX + "primary_category").get("term")
                                 if e.find(ARX + "primary_category") is not None else ""),
            "url": f"https://arxiv.org/abs/{m.group(1)}",
        })
    return out


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
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=3, help="look-back window in days")
    ap.add_argument("--threshold", type=int, default=18, help="min score to flag")
    ap.add_argument("--rebuild", action="store_true", help="run build.mjs afterwards")
    args = ap.parse_args()

    LOGS.mkdir(exist_ok=True)
    RAWD.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc)
    lo = (now - timedelta(days=args.days)).strftime("%Y%m%d%H%M")
    hi = now.strftime("%Y%m%d%H%M")
    dclause = f"submittedDate:[{lo} TO {hi}]"

    pool, warnings = {}, []
    for q in QUERIES:
        try:
            for r in parse(fetch(q.replace("{D}", dclause))):
                pool.setdefault(r["id"], r)
        except Exception as e:  # noqa: BLE001
            warnings.append(f"query failed: {str(e)[:90]}")
        time.sleep(SLEEP)

    # dedup against everything ever seen (harvest pool + previous crawls + catalogued benchmarks)
    seen_path = RAWD / "seen.jsonl"
    seen = set()
    if seen_path.exists():
        for line in seen_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    seen.add(json.loads(line)["id"])
                except Exception:  # noqa: BLE001
                    pass
    bench_path = DATA / "benchmarks.json"
    if bench_path.exists():
        for b in json.loads(bench_path.read_text(encoding="utf-8")).get("entries", []):
            if b.get("arxiv_id"):
                seen.add(b["arxiv_id"])

    fresh = []
    for r in pool.values():
        if r["id"] in seen:
            continue
        r["score"] = score(r)
        if r["score"] >= args.threshold:
            r["status"] = "new — under review"
            fresh.append(r)

    fresh.sort(key=lambda r: (-r["score"], r["published"]))

    prev_path = DATA / "latest.json"
    prev = json.loads(prev_path.read_text(encoding="utf-8")) if prev_path.exists() else {}
    keep = [c for c in prev.get("candidates", []) if c.get("id") not in {f["id"] for f in fresh}]
    candidates = (fresh + keep)[:60]

    latest = {
        "fetched_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "window_days": args.days,
        "scanned": len(pool),
        "flagged_today": len(fresh),
        "candidates": candidates,
        "warnings": warnings,
    }
    prev_path.write_text(json.dumps(latest, ensure_ascii=False, indent=2), encoding="utf-8")

    if fresh:
        with seen_path.open("a", encoding="utf-8") as f:
            for r in fresh:
                f.write(json.dumps({"id": r["id"], "title": r["title"],
                                    "published": r["published"], "score": r["score"]},
                                   ensure_ascii=False) + "\n")

    if args.rebuild:
        subprocess.run(["node", str(ROOT / "scripts" / "build.mjs")], check=True)

    status = f"WARN({'; '.join(warnings)})" if warnings else "OK"
    with (LOGS / "daily.log").open("a", encoding="utf-8") as f:
        f.write(f"{latest['fetched_at']} scanned={len(pool)} flagged={len(fresh)} "
                f"shown={len(candidates)} {status}\n")
    print(f"[atlas] crawl: scanned {len(pool)}, flagged {len(fresh)} new, "
          f"feed now {len(candidates)}. {status}")
    for r in fresh[:15]:
        print(f"  {r['score']:>3}  {r['id']}  {r['title'][:96]}")


if __name__ == "__main__":
    main()
