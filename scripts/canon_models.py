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
    # Out of scope by the site's own inclusion rule: audio-text retrieval encoders,
    # representation encoders, VAD, and TTS systems are not general-purpose spoken LLMs.
    r"clap", r"^wavlm", r"^ssast", r"^ast$", r"^hubert", r"^wav2vec", r"^whisperx",
    r"vad\b", r"^maskgct", r"^e2[- ]?tts", r"^vall-?e", r"^xtts", r"^styletts",
    r"^mmt$", r"^ml-?act$", r"^stela",
    # ablation / hyper-parameter rows, not systems
    r"^\(?\s*(α|alpha|β|beta|λ|lambda|k|n|temp)\s*=", r"^\(.*\)$",
    r"topline", r"upper[- ]?bound", r"lower[- ]?bound",
    # text-only LLM baselines quoted for reference; the site is about spoken models
    r"^vicuna", r"^llama-?[23](\.\d)?-?\d*b?-?(chat|instruct|ins\.)",
    r"^qwen-?\d*\.?\d*-?\d*b-?(chat|instruct)", r"^gemma-?\d*b?$", r"^qwen$", r"^gemma$",
    r"^qwen\d?$", r"^qwen-?\d+(\.\d+)?-?\d*b$", r"^mistral", r"^chatgpt$", r"^asr-?chatgpt$",
]
DROP_RE = [re.compile(p, re.I) for p in DROP]

# id, display, org, kind, patterns.  ORDER MATTERS — most specific first.
REGISTRY = [
    # --- OpenAI
    ("gpt-realtime", "GPT-Realtime", "OpenAI", "e2e", [r"gpt-?realtime", r"gpt-?4o-?realtime"]),
    ("gpt-4o-mini-audio", "GPT-4o-mini-Audio", "OpenAI", "e2e", [r"gpt-?4o[- ]?mini[- ]?audio"]),
    ("gpt-audio-mini", "GPT-Audio-mini", "OpenAI", "e2e", [r"gpt-?audio-?mini"]),
    ("gpt-audio", "GPT-Audio", "OpenAI", "e2e", [r"gpt-?audio(-?\d[\.\d]*)?\b"]),
    ("gpt-4o-audio", "GPT-4o-Audio", "OpenAI", "e2e",
     [r"gpt-?4o[- ]?audio", r"gpt-?4o \(audio\)", r"gpt-?4o-?voice", r"gpt-?4o-?s2s"]),
    ("gpt-4o", "GPT-4o", "OpenAI", "text", [r"^gpt-?4o(-\d{4}-\d{2}-\d{2})?$", r"^gpt-?4o-?mini$"]),
    # --- Google. Gemini is written a dozen ways across papers ("Gemini Live 2.5",
    # "Gemini-2.5", "Gemini Pro v1.5"), so match the version token wherever it lands.
    ("gemini-live-3", "Gemini Live 3.x", "Google", "e2e", [r"gemini[- ]?live[- ]?3[\.\d]*"]),
    ("gemini-live-2-5", "Gemini Live 2.5", "Google", "e2e", [r"gemini[- ]?live[- ]?2\.5"]),
    ("gemini-live", "Gemini Live", "Google", "e2e",
     [r"gemini[- ]?live\b", r"gemini[- ]?\d[\.\d]*[- ]?(pro|flash)?[- ]?live"]),
    ("gemini-3-pro", "Gemini 3 Pro", "Google", "e2e", [r"gemini[- ]?3(\.\d)?[- ]?pro"]),
    ("gemini-3-flash", "Gemini 3 Flash", "Google", "e2e", [r"gemini[- ]?3(\.\d)?[- ]?flash"]),
    ("gemini-3", "Gemini 3", "Google", "e2e", [r"gemini[- ]?3(\.\d)?\b"]),
    ("gemini-2-5-pro", "Gemini 2.5 Pro", "Google", "e2e", [r"gemini[- ]?2\.5[- ]?pro"]),
    ("gemini-2-5-flash", "Gemini 2.5 Flash", "Google", "e2e", [r"gemini[- ]?2\.5[- ]?flash"]),
    ("gemini-2-5", "Gemini 2.5", "Google", "e2e", [r"gemini[- ]?2\.5\b"]),
    ("gemini-2-flash", "Gemini 2.0 Flash", "Google", "e2e", [r"gemini[- ]?2\.?0?[- ]?flash"]),
    ("gemini-2", "Gemini 2.0", "Google", "e2e", [r"gemini[- ]?2\.0\b"]),
    ("gemini-1-5-pro", "Gemini 1.5 Pro", "Google", "e2e",
     [r"gemini[- ]?1\.5[- ]?pro", r"gemini[- ]?pro[- ]?v?1\.5"]),
    ("gemini-1-5-flash", "Gemini 1.5 Flash", "Google", "e2e", [r"gemini[- ]?1\.5[- ]?flash"]),
    ("gemini-flash", "Gemini Flash (version unstated)", "Google", "e2e", [r"gemini[- ]?flash"]),
    ("gemma-3n", "Gemma-3n", "Google", "e2e", [r"gemma-?3n", r"gemma-?e[24]b"]),
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
    # "SALAMONN" is how the MMAU paper spells it; same model, and dropping it lost 5 cells
    ("salmonn", "SALMONN", "Tsinghua/ByteDance", "e2e", [r"^sala?monn(?!-omni)"]),
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
    # --- pure speech LMs (no instruction tuning). These are what likelihood-based
    # benchmarks (SALMon, sWUGGY, sBLIMP, spoken StoryCloze) actually evaluate, and they
    # are a different family from the instruction-following LALMs above. Size variants are
    # kept DISTINCT here because these papers compare sizes deliberately.
    ("spirit-lm-expressive", "SpiRit-LM Expressive", "Meta", "speech-lm",
     [r"spirit[- ]?lm[- ]?(expr|expressive)"]),
    ("spirit-lm", "SpiRit-LM", "Meta", "speech-lm", [r"spirit[- ]?lm"]),
    ("twist-7b", "TWIST 7B", "HUJI", "speech-lm", [r"twist[- ]?7b"]),
    ("twist-1-3b", "TWIST 1.3B", "HUJI", "speech-lm", [r"twist[- ]?1\.3b"]),
    ("twist-350m", "TWIST 350M", "HUJI", "speech-lm", [r"twist[- ]?350m"]),
    ("twist", "TWIST", "HUJI", "speech-lm", [r"^twist\b"]),
    ("last-1-3b", "LAST 1.3B", "HUJI", "speech-lm", [r"^last[- ]?1\.3b"]),
    ("last-350m", "LAST 350M", "HUJI", "speech-lm", [r"^last[- ]?350m"]),
    ("pgslm", "pGSLM", "Meta", "speech-lm", [r"^p-?gslm"]),
    ("dgslm", "dGSLM", "Meta", "speech-lm", [r"^d-?gslm"]),
    ("gslm", "GSLM", "Meta", "speech-lm", [r"^gslm\b"]),
    ("audiolm", "AudioLM", "Google", "speech-lm", [r"^audiolm"]),
    ("spectron", "Spectron", "Google", "speech-lm", [r"^spectron"]),
    ("moshi-base", "Moshi (base LM)", "Kyutai", "speech-lm", [r"moshi[- ]?(base|bert)"]),
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
    ("mu-llama", "MU-LLaMA", "—", "e2e", [r"mu-?llama"]),
    # --- second sweep: real spoken/omni models the first registry missed
    ("j-moshi", "J-Moshi", "Nagoya", "e2e", [r"^j-?moshi"]),
    ("llm-jp-moshi", "LLM-jp-Moshi", "LLM-jp", "e2e", [r"llm-?jp-?moshi"]),
    ("megrez-omni", "Megrez-3B-Omni", "Infinigence", "e2e", [r"megrez-?(3b-?)?omni"]),
    ("grok", "Grok", "xAI", "e2e", [r"^grok"]),
    ("fun-audio-chat", "Fun-Audio-Chat", "Alibaba", "e2e", [r"fun-?audio-?chat"]),
    ("doubao", "Doubao (realtime)", "ByteDance", "e2e", [r"^doubao"]),
    ("ixc-omnilive", "IXC2.5-OmniLive", "Shanghai AI Lab", "e2e", [r"ixc-?2\.5-?omnilive"]),
    ("anygpt", "AnyGPT", "Fudan", "e2e", [r"^anygpt"]),
    ("mio-instruct", "MIO-Instruct", "—", "e2e", [r"^mio-?instruct"]),
    ("unified-io-2", "UnifiedIO2", "AI2", "e2e", [r"unified-?io-?2"]),
    ("macaw-llm", "Macaw-LLM", "Tencent", "e2e", [r"macaw-?llm"]),
    ("reka-core", "Reka Core", "Reka", "e2e", [r"^reka-?core"]),
    ("openmu", "OpenMU", "Sony", "e2e", [r"^openmu(?!-bench)"]),
    ("r1-aqa", "R1-AQA", "Xiaomi", "e2e", [r"^r1-?aqa"]),
    ("bat", "BAT", "CMU", "e2e", [r"^bat$"]),
    ("sonic", "Sonic", "Cartesia", "e2e", [r"^sonic(\s?\d)?$"]),
    ("desta", "DeSTA", "NTU", "e2e", [r"^desta(?!-?2)"]),
    ("step-2-mini", "Step-2-mini", "StepFun", "e2e", [r"step-?2-?mini"]),
    ("speechjudge", "SpeechJudge", "—", "e2e", [r"speechjudge"]),
    ("stresslm", "StresSLM", "—", "e2e", [r"stresslm"]),
    ("phi-4", "Phi-4", "Microsoft", "e2e", [r"^phi-?4$"]),
    ("qwen3-5-omni", "Qwen3.5-Omni", "Alibaba", "e2e", [r"qwen-?3\.5-?omni"]),
    ("balsa", "BALSa", "NTU", "e2e", [r"^balsa"]),
    # named cascades: specific pairings are real systems and belong in the table; the
    # generic word "cascade" is still dropped, because it names no system in particular.
    ("whisper-gpt4o", "Whisper + GPT-4o (cascade)", "—", "cascade",
     [r"whisper.{0,6}\+.{0,6}gpt-?4o", r"asr.{0,3}\+.{0,3}gpt-?4o"]),
    ("whisper-gpt4", "Whisper + GPT-4 (cascade)", "—", "cascade", [r"whisper.{0,6}\+.{0,6}gpt-?4\b"]),
    ("whisper-llama3", "Whisper + LLaMA-3 (cascade)", "—", "cascade", [r"whisper.{0,6}\+.{0,6}llama-?3"]),
    # text-only LLM baselines: an upper bound on the text channel, useful as a reference row
    ("qwen2-7b-instruct", "Qwen2-7B-Instruct (text)", "Alibaba", "text", [r"qwen-?2-?7b-?instruct"]),
    ("qwen2-5-7b-instruct", "Qwen2.5-7B-Instruct (text)", "Alibaba", "text", [r"qwen-?2\.5-?7b-?instruct"]),
    # bare "Gemini" with no version — last resort, after every specific Gemini entry above
    ("gemini-unversioned", "Gemini (version unstated)", "Google", "e2e", [r"^gemini$"]),
]

COMPILED = [(i, n, o, k, [re.compile(p, re.I) for p in ps]) for i, n, o, k, ps in REGISTRY]


def clean(raw):
    s = (raw or "").strip()
    # 🔴 Papers use non-ASCII dashes that LOOK identical to a hyphen: U+2011 non-breaking
    # hyphen, en/em dashes, minus sign. A pattern written with "-" silently fails to match
    # them, so a model already in the registry vanishes from the table. Normalise first.
    s = s.translate({0x2010: "-", 0x2011: "-", 0x2012: "-", 0x2013: "-", 0x2014: "-",
                     0x2015: "-", 0x2212: "-", 0x00AD: "-", 0xFE63: "-", 0xFF0D: "-",
                     0x00A0: " ", 0x2007: " ", 0x202F: " ", 0x2009: " "})
    s = re.sub(r"\s*\((?:text|speech|T\.|S\.)\)\s*$", "", s, flags=re.I)
    s = re.sub(r"\s*\[\d+\]\s*$", "", s)            # trailing citation markers "[27]"
    s = re.sub(r"\s*[†*‡§¶^]+\s*$", "", s)
    s = re.sub(r"\s*\((?:ours|proposed|our model)\)\s*$", "", s, flags=re.I)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


# Retrieval/encoder/VAD families whose name can sit anywhere in the string.
DROP_ANYWHERE = [re.compile(p, re.I) for p in [
    r"\bclap\b", r"\bvad\b", r"topline", r"upper[- ]?bound", r"\bhuman\b",
]]

# A cascade is "component + component". Each distinct pairing is a distinct system, so
# instead of enumerating them (or worse, merging them under one "cascade" row, which
# would invent comparisons nobody ran) generate a faithful id from the printed name.
CASCADE_RE = re.compile(
    r"^(?:(?:whisper|nova|parakeet|scribe|ink-?whisper|sensevoice|qwen\d?-?asr|asr|captions?)"
    r"[\w.\- ]*)\s*(?:\+|-|\band\b)\s*\w", re.I)
CASCADE_HINT = re.compile(r"\+|\bcap\.|\bcaption", re.I)


def slug_id(s):
    out = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return re.sub(r"-{2,}", "-", out)[:48]


def match(raw):
    s = clean(raw)
    if not s:
        return None
    for p in DROP_RE:
        if p.match(s):
            return None
    for p in DROP_ANYWHERE:
        if p.search(s):
            return None
    for mid, name, org, kind, pats in COMPILED:
        for p in pats:
            if p.search(s):
                return mid, name, org, kind
    # named cascade pipelines: keep them, each under its own id
    if CASCADE_RE.match(s) and CASCADE_HINT.search(s) or re.match(
            r"^(whisper|asr)[- ]?(llm|llama|gpt)", s, re.I):
        return "cascade:" + slug_id(s), s + " (cascade)", "—", "cascade"
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
