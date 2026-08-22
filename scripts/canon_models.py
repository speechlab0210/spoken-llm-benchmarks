# Canonicalise extracted table rows into stable model ids + resolve benchmark ids,
# then emit data/results.json and data/models.json.
#
# Design rules:
#  - Extraction agents copy the model string verbatim; identity mapping happens HERE, once,
#    reviewably, so no table row depends on an agent's judgement about who is who.
#  - NO generic "cascade" catch-all: different cascade systems are different systems, and
#    collapsing them silently invents comparisons that were never made.
#  - Non-model rows (Human, Random, Ours, Baseline...) are dropped, not mapped.
#  - When the same (benchmark, model, metric) has two values, prefer the number reported by
#    the benchmark's OWN paper over one quoted in a model's technical report.
#
# Usage: python scripts/canon_models.py --cells raw/cells_raw.json \
#            --out-cells data/results.json --out-models data/models.json

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]

# rows that are not a model at all
DROP = [
    r"^human", r"^random", r"^chance", r"^majority", r"^baseline$", r"^ours$", r"^\+",
    r"^cascade", r"^cascaded", r"^pipeline$", r"^upper ?bound", r"^oracle", r"^gt$",
    r"^ground ?truth", r"^google$", r"^openai$", r"^xai$", r"^meta$", r"^alibaba$",
    r"^average", r"^overall$", r"^all$", r"^-$", r"^n/?a$", r"^\d+$",
    # whisper / ASR-only systems and TTS-only systems are not spoken LLMs
    r"^whisper[\s\-]*(large|v\d|small|medium|base|tiny)?$", r"^cosyvoice", r"^seed-?tts",
    r"^f5-?tts", r"^fish-?speech", r"^sensevoice$",
    # column-header truncations too ambiguous to attribute
    r"^(sal|qwa|sifl|step-?fun|qwen-?a|bal|ds\d?)$",
]
DROP_RE = [re.compile(p, re.I) for p in DROP]

# id, display, org, kind, patterns.  ORDER MATTERS — most specific first.
REGISTRY = [
    # --- OpenAI
    ("gpt-realtime", "GPT-Realtime", "OpenAI", "e2e", [r"gpt-?realtime", r"gpt-?4o-?realtime"]),
    ("gpt-4o-mini-audio", "GPT-4o-mini-Audio", "OpenAI", "e2e", [r"gpt-?4o[- ]?mini[- ]?audio"]),
    ("gpt-4o-audio", "GPT-4o-Audio", "OpenAI", "e2e",
     [r"gpt-?4o[- ]?audio", r"gpt-?4o \(audio\)", r"gpt-?4o-?voice", r"gpt-?4o-?s2s"]),
    ("gpt-4o", "GPT-4o", "OpenAI", "text", [r"^gpt-?4o(-\d{4}-\d{2}-\d{2})?$", r"^gpt-?4o-?mini$"]),
    # --- Google
    ("gemini-3-pro", "Gemini 3 Pro", "Google", "e2e", [r"gemini[- ]?3[- ]?pro"]),
    ("gemini-2-5-pro", "Gemini 2.5 Pro", "Google", "e2e", [r"gemini[- ]?2\.5[- ]?pro"]),
    ("gemini-2-5-flash", "Gemini 2.5 Flash", "Google", "e2e", [r"gemini[- ]?2\.5[- ]?flash"]),
    ("gemini-2-flash", "Gemini 2.0 Flash", "Google", "e2e", [r"gemini[- ]?2\.?0?[- ]?flash"]),
    ("gemini-1-5-pro", "Gemini 1.5 Pro", "Google", "e2e", [r"gemini[- ]?1\.5[- ]?pro"]),
    ("gemini-1-5-flash", "Gemini 1.5 Flash", "Google", "e2e", [r"gemini[- ]?1\.5[- ]?flash"]),
    ("gemma-3n", "Gemma-3n", "Google", "e2e", [r"gemma-?3n"]),
    # --- Alibaba / Qwen
    ("qwen3-omni", "Qwen3-Omni", "Alibaba", "e2e", [r"qwen-?3[.\-]?omni"]),
    ("qwen2-5-omni", "Qwen2.5-Omni", "Alibaba", "e2e",
     [r"qwen-?2\.5[.\-]?omni", r"qwen2\.5-?o\b", r"qwen-?omni-?turbo"]),
    ("qwen2-audio", "Qwen2-Audio", "Alibaba", "e2e",
     [r"qwen-?2-?audio", r"qwen2-?a-?inst"]),
    ("qwen-audio", "Qwen-Audio", "Alibaba", "e2e", [r"^qwen-?audio(-chat)?"]),
    ("minmo", "MinMo", "Alibaba", "e2e", [r"^minmo"]),
    # --- Moonshot / StepFun / Zhipu / OpenBMB / Baichuan
    ("kimi-audio", "Kimi-Audio", "Moonshot", "e2e", [r"kimi-?audio"]),
    ("step-audio-r1", "Step-Audio-R1", "StepFun", "e2e", [r"step-?audio-?r1"]),
    ("step-audio-2", "Step-Audio 2", "StepFun", "e2e", [r"step-?audio-?2"]),
    ("step-audio", "Step-Audio", "StepFun", "e2e", [r"step-?audio"]),
    ("glm-4-voice", "GLM-4-Voice", "Zhipu", "e2e", [r"glm-?4-?voice"]),
    ("minicpm-o", "MiniCPM-o", "OpenBMB", "e2e", [r"minicpm-?o", r"^minicpm$"]),
    ("baichuan-omni", "Baichuan-Omni", "Baichuan", "e2e", [r"baichuan-?omni"]),
    ("baichuan-audio", "Baichuan-Audio", "Baichuan", "e2e", [r"baichuan-?(audio|chat)"]),
    ("mimo-audio", "MiMo-Audio", "Xiaomi", "e2e", [r"mi?mo-?audio"]),
    ("moss-audio", "MOSS-Audio", "Fudan", "e2e", [r"moss-?audio"]),
    # --- academic / open e2e
    ("salmonn", "SALMONN", "Tsinghua/ByteDance", "e2e", [r"^salmonn(?!-omni)"]),
    ("salmonn-omni", "SALMONN-omni", "Tsinghua/ByteDance", "e2e", [r"salmonn-?omni"]),
    ("video-salmonn", "video-SALMONN", "Tsinghua/ByteDance", "e2e", [r"video-?salmonn"]),
    ("llama-omni2", "LLaMA-Omni2", "ICT/CAS", "e2e", [r"llama-?omni-?2"]),
    ("llama-omni", "LLaMA-Omni", "ICT/CAS", "e2e", [r"llama-?omni"]),
    ("freeze-omni", "Freeze-Omni", "Tencent", "e2e", [r"freeze-?omni"]),
    ("vita-audio", "VITA-Audio", "Tencent", "e2e", [r"vita-?audio"]),
    ("vita", "VITA", "Tencent", "e2e", [r"^vita(-1\.5)?\b"]),
    ("moshi", "Moshi", "Kyutai", "e2e", [r"^moshi"]),
    ("mini-omni2", "Mini-Omni2", "Tsinghua", "e2e", [r"mini-?omni-?2"]),
    ("mini-omni", "Mini-Omni", "Tsinghua", "e2e", [r"mini-?omni"]),
    ("slam-omni", "SLAM-Omni", "SJTU", "e2e", [r"slam-?omni"]),
    ("speechgpt2", "SpeechGPT-2", "Fudan", "e2e", [r"speechgpt-?2"]),
    ("speechgpt", "SpeechGPT", "Fudan", "e2e", [r"^speechgpt"]),
    ("opens2s", "OpenS2S", "—", "e2e", [r"opens2s"]),
    ("vocalnet", "VocalNet", "—", "e2e", [r"vocalnet"]),
    ("lucy", "LUCY", "—", "e2e", [r"^lucy\b"]),
    ("lyra", "Lyra", "—", "e2e", [r"^lyra\b"]),
    ("diva", "DiVA", "Stanford", "e2e", [r"^diva"]),
    ("ultravox", "Ultravox", "Fixie", "e2e", [r"ultravox"]),
    ("phi-4-multimodal", "Phi-4-multimodal", "Microsoft", "e2e", [r"phi-?4-?(multimodal|mm)"]),
    ("voxtral", "Voxtral", "Mistral", "e2e", [r"voxtral"]),
    ("ola", "Ola", "Tsinghua", "e2e", [r"^ola\b"]),
    ("ming-omni", "Ming-Omni", "Ant Group", "e2e", [r"ming-?(lite-)?omni"]),
    ("megrez-o", "Megrez-O", "Infinigence", "e2e", [r"megrez-?o"]),
    ("typhoon-audio", "Typhoon-Audio", "SCB10X", "e2e", [r"typhoon-?(2-?)?audio"]),
    ("meralion", "MERaLiON", "A*STAR", "e2e", [r"meralion"]),
    ("desta2", "DeSTA2", "NTU", "e2e", [r"desta-?2"]),
    ("blsp", "BLSP", "Alibaba", "e2e", [r"^blsp"]),
    ("spirit-lm", "SpiRit-LM", "Meta", "e2e", [r"spirit[- ]?lm"]),
    ("audio-reasoner", "Audio-Reasoner", "—", "e2e", [r"audio-?reasoner"]),
    ("sensedialog", "SenseDialog", "SenseTime", "e2e", [r"sensedialog"]),
    ("personaplex", "PersonaPlex", "—", "e2e", [r"personaplex"]),
    # --- audio-understanding LALMs
    ("audio-flamingo-3", "Audio Flamingo 3", "NVIDIA", "e2e", [r"audio[- ]?flamingo[- ]?3", r"^af3"]),
    ("audio-flamingo-2", "Audio Flamingo 2", "NVIDIA", "e2e", [r"audio[- ]?flamingo[- ]?2", r"^af2"]),
    ("audio-flamingo", "Audio Flamingo", "NVIDIA", "e2e", [r"audio[- ]?flamingo"]),
    ("ltu-as", "LTU-AS", "MIT", "e2e", [r"^ltu-?as"]),
    ("ltu", "LTU", "MIT", "e2e", [r"^ltu\b"]),
    ("pengi", "Pengi", "Microsoft", "e2e", [r"^pengi"]),
    ("gama", "GAMA", "UMD", "e2e", [r"^gama(-it)?\b"]),
    ("mellow", "Mellow", "—", "e2e", [r"^mellow"]),
    ("wavllm", "WavLLM", "Microsoft", "e2e", [r"wavllm"]),
    ("musilingo", "MusiLingo", "—", "e2e", [r"musilingo"]),
    ("m2ugen", "M2UGen", "NUS", "e2e", [r"m2ugen"]),
    ("nextgpt", "NExT-GPT", "NUS", "e2e", [r"next-?gpt"]),
    ("pandagpt", "PandaGPT", "—", "e2e", [r"pandagpt"]),
    ("imagebind-llm", "ImageBind-LLM", "—", "e2e", [r"imagebind-?llm"]),
    ("bert-gslm", "BERT-GSLM", "—", "e2e", [r"bert-?gslm"]),
]

COMPILED = [(i, n, o, k, [re.compile(p, re.I) for p in ps]) for i, n, o, k, ps in REGISTRY]


def clean(raw):
    s = (raw or "").strip()
    s = re.sub(r"\s*\((?:text|speech|T\.|S\.)\)\s*$", "", s, flags=re.I)
    s = re.sub(r"\s*[†*‡§¶^]+\s*$", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def match(raw):
    s = clean(raw)
    if not s:
        return None
    for p in DROP_RE:
        if p.match(s):
            return None
    for mid, name, org, kind, pats in COMPILED:
        for p in pats:
            if p.search(s):
                return mid, name, org, kind
    return "UNMAPPED"


def build_bench_index():
    """Map an extracted benchmark id to a catalogue benchmark id, by normalised name."""
    bm = json.loads((ROOT / "data/benchmarks.json").read_text(encoding="utf-8"))["entries"]
    idx = {}
    def norm(s):
        return re.sub(r"[^a-z0-9]", "", (s or "").lower())
    for b in bm:
        for cand in [b["id"], b["name"]] + list(b.get("aka") or []):
            idx.setdefault(norm(cand), b["id"])
    return idx, {b["id"]: b.get("arxiv_id") for b in bm}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", required=True)
    ap.add_argument("--out-cells", required=True)
    ap.add_argument("--out-models", required=True)
    ap.add_argument("--min-cells", type=int, default=3)
    args = ap.parse_args()

    raw_cells = json.loads((ROOT / args.cells).read_text(encoding="utf-8"))
    bench_idx, bench_arxiv = build_bench_index()

    def nb(s):
        return re.sub(r"[^a-z0-9]", "", (s or "").lower())

    mapped, unmapped, dropped_row, unknown_bench = [], Counter(), Counter(), Counter()
    used = {}
    for c in raw_cells:
        bid = bench_idx.get(nb(c.get("benchmark")))
        if not bid:
            unknown_bench[c.get("benchmark")] += 1
            continue
        m = match(c.get("model_raw"))
        if m is None:
            dropped_row[clean(c.get("model_raw"))] += 1
            continue
        if m == "UNMAPPED":
            unmapped[clean(c.get("model_raw"))] += 1
            continue
        mid, name, org, kind = m
        used[mid] = (name, org, kind)
        own = bench_arxiv.get(bid) and c.get("source_arxiv") == bench_arxiv.get(bid)
        cell = {"benchmark": bid, "model": mid, "metric": str(c["metric"]).strip(),
                "value": c["value"], "source": c["source"], "_own": bool(own)}
        if c.get("source_arxiv"):
            cell["source_url"] = f"https://arxiv.org/abs/{c['source_arxiv']}"
        if c.get("note"):
            cell["note"] = c["note"]
        mapped.append(cell)

    # prefer the benchmark's own paper as the authority for its own numbers
    mapped.sort(key=lambda c: 0 if c["_own"] else 1)
    seen, final, conflicts = {}, [], []
    for c in mapped:
        k = (c["benchmark"], c["model"], c["metric"])
        if k in seen:
            if str(seen[k]["value"]) != str(c["value"]):
                conflicts.append((k, seen[k]["value"], c["value"]))
            continue
        seen[k] = c
        final.append(c)
    for c in final:
        c.pop("_own", None)

    # Scale-collision guard: papers report the same metric on different scales (a 1-5 GPT
    # judge score vs the same thing normalised to 100). Averaging or listing them together
    # would be meaningless, so split them into distinct metrics and let the UI keep them apart.
    groups = {}
    for c in final:
        try:
            groups.setdefault((c["benchmark"], c["metric"]), []).append(float(c["value"]))
        except (TypeError, ValueError):
            pass
    split = 0
    for c in final:
        vals = groups.get((c["benchmark"], c["metric"]))
        if not vals or len(vals) < 3:
            continue
        if min(vals) <= 10 and max(vals) >= 50:      # two incompatible scales in one metric
            try:
                v = float(c["value"])
            except (TypeError, ValueError):
                continue
            c["metric"] = f"{c['metric']} [0-10 scale]" if v <= 10 else f"{c['metric']} [0-100 scale]"
            split += 1
    if split:
        print(f"  scale-collision guard: relabelled {split} cells across mixed-scale metrics")

    counts = Counter(c["model"] for c in final)
    keep = {m for m, n in counts.items() if n >= args.min_cells}
    final = [c for c in final if c["model"] in keep]
    models = [{"id": m, "name": used[m][0], "org": used[m][1], "type": used[m][2]}
              for m in sorted(keep, key=lambda x: -counts[x])]

    (ROOT / args.out_cells).write_text(
        json.dumps({"cells": final}, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / args.out_models).write_text(
        json.dumps({"entries": models}, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"raw cells        : {len(raw_cells)}")
    print(f"  unknown benchmark : {sum(unknown_bench.values())} cells / {len(unknown_bench)} names")
    print(f"  non-model rows    : {sum(dropped_row.values())} cells / {len(dropped_row)} names")
    print(f"  unmapped models   : {sum(unmapped.values())} cells / {len(unmapped)} names")
    print(f"  mapped            : {len(mapped)}")
    print(f"  after dedup       : {len(seen)}  (conflicts resolved: {len(conflicts)})")
    print(f"  after min-cells>={args.min_cells}: {len(final)} cells, {len(models)} models")
    benches = len({c['benchmark'] for c in final})
    print(f"  covering {benches} benchmarks")
    if unmapped:
        print(f"\n  top unmapped model names (add to REGISTRY if real spoken LLMs):")
        for n, k in unmapped.most_common(25):
            print(f"    {k:>3}x  {n}")
    if unknown_bench:
        print(f"\n  top unknown benchmark ids (not in catalogue):")
        for n, k in unknown_bench.most_common(15):
            print(f"    {k:>3}x  {n}")


if __name__ == "__main__":
    main()
