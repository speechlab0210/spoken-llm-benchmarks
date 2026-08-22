# Mechanical arXiv harvester for spoken-LLM benchmark candidates.
# No model in the loop: queries the arXiv API, dedupes, scores by keyword, writes JSONL.
# Usage: python scripts/harvest_arxiv.py [--start 2025-01] [--end 2026-08] [--out raw/candidates.jsonl]

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

ATOM = "{http://www.w3.org/2005/Atom}"
ARX = "{http://arxiv.org/schemas/atom}"
API = "http://export.arxiv.org/api/query?"
PAGE = 200
SLEEP = 3.2  # arXiv asks for >=3s between requests

# ---- query templates. {D} is replaced by a submittedDate range clause. ----
QUERIES = [
    # 1. speech/audio primary categories, benchmark-ish language
    '(cat:eess.AS OR cat:cs.SD) AND (abs:benchmark OR ti:benchmark OR abs:evaluation OR ti:evaluation OR abs:evaluating OR ti:evaluating OR abs:"test set" OR abs:testbed OR ti:testbed) AND {D}',
    # 2. NLP category, speech-flavoured + benchmark-ish
    'cat:cs.CL AND (abs:speech OR abs:audio OR abs:spoken OR abs:voice OR abs:acoustic) AND (abs:benchmark OR ti:benchmark OR abs:evaluation OR ti:evaluation OR abs:testbed) AND {D}',
    # 3. the model-class terms themselves, any category
    '(abs:"speech language model" OR abs:"spoken language model" OR abs:"audio language model" OR abs:"speech LLM" OR abs:"audio LLM" OR abs:"spoken LLM" OR abs:"speech-language model" OR abs:"audio-language model" OR ti:"speech language model" OR ti:"spoken language model" OR ti:"audio language model") AND {D}',
    # 4. conversational / duplex / omni / voice-assistant model terms
    '(abs:"spoken dialogue" OR abs:"speech-to-speech" OR abs:"full-duplex" OR abs:"full duplex" OR abs:"voice assistant" OR abs:"voice agent" OR abs:"omni-modal" OR abs:"omni modal" OR abs:"end-to-end spoken" OR abs:"speech interaction" OR abs:"voice interaction") AND {D}',
    # 5. multimodal LLM + audio, other categories (AI/LG/MM)
    '(cat:cs.AI OR cat:cs.LG OR cat:cs.MM OR cat:cs.HC) AND (abs:audio OR abs:speech OR abs:spoken) AND (abs:benchmark OR ti:benchmark OR abs:"large language model" OR abs:LALM OR abs:SpeechLM) AND {D}',
    # 6. named capability probes that often skip the word "benchmark"
    '(abs:paralinguistic OR abs:prosody OR abs:"emotion recognition" OR abs:"audio question answering" OR abs:"spoken question answering" OR abs:"speech instruction" OR abs:"instruction-following" OR abs:"audio reasoning" OR abs:"speech reasoning") AND (cat:eess.AS OR cat:cs.SD OR cat:cs.CL) AND {D}',
    # 7. trustworthiness axis (safety / jailbreak / hallucination / bias / deepfake) on audio models
    '(abs:jailbreak OR abs:hallucination OR abs:toxicity OR abs:bias OR abs:fairness OR abs:safety OR abs:deepfake OR abs:"spoofing") AND (abs:audio OR abs:speech OR abs:spoken OR abs:voice) AND (cat:eess.AS OR cat:cs.SD OR cat:cs.CL OR cat:cs.CR OR cat:cs.AI) AND {D}',
]

# ---- scoring: cheap local triage so agents read the plausible ones first ----
MODEL_TERMS = [
    "speech language model", "spoken language model", "audio language model",
    "speech-language model", "audio-language model", "large audio language model",
    "speech llm", "audio llm", "spoken llm", "lalm", "salmonn", "qwen-audio", "qwen2-audio",
    "qwen2.5-omni", "gpt-4o", "gpt-4o-audio", "moshi", "glm-4-voice", "speechgpt",
    "spokengpt", "audioflamingo", "audio flamingo", "gemini", "omni", "speechlm",
    "spoken dialogue model", "voice assistant", "speech-to-speech", "full-duplex",
    "end-to-end speech", "voice agent", "audio-llm", "slm", "avlm", "multimodal llm",
]
BENCH_TERMS = [
    "benchmark", "evaluation suite", "evaluation framework", "test suite", "testbed",
    "we introduce", "we present", "we propose", "new dataset", "evaluation benchmark",
    "leaderboard", "eval set", "diagnostic", "probing",
]
NEG_TERMS = [
    "text-to-speech synthesis system", "speech enhancement", "speech separation",
    "voice conversion", "speaker verification", "acoustic model training",
    "automatic speech recognition system for", "asr system for low-resource",
]


def daterange_clauses(start, end):
    """Yield monthly submittedDate clauses from YYYY-MM to YYYY-MM inclusive."""
    sy, sm = (int(x) for x in start.split("-"))
    ey, em = (int(x) for x in end.split("-"))
    y, m = sy, sm
    while (y, m) <= (ey, em):
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        lo = f"{y:04d}{m:02d}010000"
        hi = f"{ny:04d}{nm:02d}010000"
        yield f"{y:04d}-{m:02d}", f"submittedDate:[{lo} TO {hi}]"
        y, m = ny, nm


def fetch(query, start_idx, attempt=0):
    url = API + urllib.parse.urlencode({
        "search_query": query,
        "start": start_idx,
        "max_results": PAGE,
        "sortBy": "submittedDate",
        "sortOrder": "ascending",
    })
    try:
        with urllib.request.urlopen(url, timeout=90) as r:
            return r.read()
    except Exception as e:  # noqa: BLE001 - network flakiness is expected, retry
        if attempt >= 4:
            print(f"    !! give up after {attempt} retries: {e}", flush=True)
            return None
        wait = 8 * (attempt + 1)
        print(f"    .. retry {attempt + 1} in {wait}s ({e})", flush=True)
        time.sleep(wait)
        return fetch(query, start_idx, attempt + 1)


def parse(xml_bytes):
    root = ET.fromstring(xml_bytes)
    total = root.find("{http://a9.com/-/spec/opensearch/1.1/}totalResults")
    total = int(total.text) if total is not None else 0
    out = []
    for e in root.findall(ATOM + "entry"):
        raw_id = e.findtext(ATOM + "id", "")
        m = re.search(r"abs/([^v]+)v(\d+)", raw_id)
        if not m:
            continue
        cats = [c.get("term") for c in e.findall(ATOM + "category")]
        out.append({
            "id": m.group(1),
            "version": int(m.group(2)),
            "title": " ".join((e.findtext(ATOM + "title") or "").split()),
            "abstract": " ".join((e.findtext(ATOM + "summary") or "").split()),
            "published": e.findtext(ATOM + "published", ""),
            "updated": e.findtext(ATOM + "updated", ""),
            "authors": [a.findtext(ATOM + "name") for a in e.findall(ATOM + "author")][:12],
            "primary_category": (e.find(ARX + "primary_category").get("term")
                                 if e.find(ARX + "primary_category") is not None else ""),
            "categories": cats,
            "comment": " ".join((e.findtext(ARX + "comment") or "").split()),
            "url": f"https://arxiv.org/abs/{m.group(1)}",
        })
    return total, out


def score(rec):
    text = (rec["title"] + " " + rec["abstract"]).lower()
    ti = rec["title"].lower()
    s = 0
    s += 6 * sum(1 for t in MODEL_TERMS if t in text)
    s += 3 * sum(1 for t in BENCH_TERMS if t in text)
    if "benchmark" in ti or "eval" in ti or "-bench" in ti or "bench" in ti:
        s += 12
    if re.search(r"\b[A-Z][A-Za-z0-9]*-?Bench\b", rec["title"]):
        s += 15
    s -= 5 * sum(1 for t in NEG_TERMS if t in text)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-01")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--out", default="raw/candidates.jsonl")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    out_path = root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    seen = {}
    months = list(daterange_clauses(args.start, args.end))
    print(f"harvest {args.start}..{args.end}  {len(months)} months x {len(QUERIES)} queries", flush=True)

    for label, dclause in months:
        for qi, tmpl in enumerate(QUERIES):
            q = tmpl.replace("{D}", dclause)
            start_idx, total = 0, None
            while True:
                xml = fetch(q, start_idx)
                time.sleep(SLEEP)
                if xml is None:
                    break
                try:
                    total, recs = parse(xml)
                except ET.ParseError as e:
                    print(f"    !! parse error {e}", flush=True)
                    break
                if not recs:
                    break
                for r in recs:
                    if r["id"] not in seen:
                        r["score"] = score(r)
                        r["found_by"] = [qi]
                        seen[r["id"]] = r
                    elif qi not in seen[r["id"]]["found_by"]:
                        seen[r["id"]]["found_by"].append(qi)
                start_idx += PAGE
                if start_idx >= min(total or 0, 2000):
                    break
            print(f"  {label} q{qi}: total={total} pool={len(seen)}", flush=True)

    recs = sorted(seen.values(), key=lambda r: (-r["score"], r["published"]))
    with out_path.open("w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    hi = sum(1 for r in recs if r["score"] >= 20)
    mid = sum(1 for r in recs if 8 <= r["score"] < 20)
    print(f"\nwrote {len(recs)} -> {out_path}  (score>=20: {hi}, 8..19: {mid})", flush=True)


if __name__ == "__main__":
    main()
