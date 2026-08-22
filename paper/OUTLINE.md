# Overview paper — working outline

**Working title:** *What We Measure When We Measure Spoken LLMs: A Survey of Benchmarks, 2025–2026*

**Audience:** speech + NLP researchers who know what a spoken LLM is and want to know which
benchmark to use, what it actually tests, and what nobody is testing.

**Positioning against the two anchors** (state this explicitly in §1):
- Yang, Ho & Lee (EMNLP 2025) — taxonomy of LALM evaluation by capability dimension. Coverage
  effectively ends early 2025.
- Arora et al. (TMLR 2025) — taxonomy of SLMs by architecture/training/evaluation *paradigm*;
  evaluation is one section of a broader survey and explicitly excludes ASR/TTS-style tasks.
- **This paper's delta:** (a) it covers the 2025-01 → 2026-08 wave, which is where most of the
  benchmarks now live; (b) it merges the paradigm axis and the capability axis into one working
  taxonomy; (c) it is paired with a machine-maintained, daily-updated catalogue, so the survey
  states a position and the site carries the moving parts.

## Structure

**1. Introduction**
- The definitional move that created the problem: a universal model has no single number.
- Growth curve — benchmarks per quarter, from the harvest. Cite the actual counts.
- What the paper contributes.

**2. Scope and method**
- The inclusion rule (general-purpose speech-in/speech-out; ASR-only and TTS-only excluded) and
  why it is the right cut.
- How the catalogue was built: two surveys read in full, then a systematic arXiv API sweep
  (query families × monthly windows), then triage, then per-paper verification.
- Honest limits: English-language arXiv bias, benchmarks that never preprint, the recall ceiling
  of keyword search, and what the cross-checks were meant to catch.

**3. A taxonomy that reconciles the two existing ones**
- Six groups (see `data/taxonomy.json`). For each: the question it answers, the metric family,
  the representative benchmarks, and the failure mode it is blind to.
- Argue the two additions: **audio-grounding diagnostics** as a first-class category, and
  **coverage** (language/length/domain) as a cross-cutting axis rather than a capability.

**4. The 2025–2026 wave — what changed** ← *the heart of the paper*
Organise as shifts, each backed by counts + named benchmarks:
- 4.1 From "can it do the task" to "is it listening at all" — the rise of text-prior and
  audio-ablation diagnostics. The uncomfortable finding they keep producing.
- 4.2 Timing became measurable — full-duplex, turn-taking, barge-in, latency. Before 2025 the
  turn structure was assumed; after, it is the object of study.
- 4.3 Paralinguistics moved from a label-classification task to a *conversational* requirement.
- 4.4 Trustworthiness grew its own literature, with attack surfaces that are audio-specific.
- 4.5 Reasoning benchmarks arrived, and immediately inherited the text field's contamination problem.
- 4.6 Holistic suites consolidated — and the aggregate scores they report started to hide more
  than they reveal.

**5. Cross-cutting methodological problems**
- **The TTS-rendering pattern**: most spoken knowledge/reasoning benchmarks are text benchmarks
  read aloud. Cheap, scalable, and quietly changes what is being measured (and imports the
  source benchmark's contamination). Both a strength and the main validity threat.
- **Judge dependence**: LLM-as-judge is now the default metric; judge choice moves scores.
- **Comparability**: same model, same benchmark, different numbers across sources. Quantify from
  the catalogue where the same cell has conflicting published values.
- **Cascade vs end-to-end**: what the comparison does and does not establish.
- **Contamination and leakage.**

**6. What has no benchmark yet** (the section people will actually cite)
- Candidates: long-horizon spoken interaction; personalisation and memory across sessions;
  simultaneous/overlapping multi-party speech; low-resource and dialectal coverage at scale;
  the interaction between paralinguistic understanding and safety; evaluation of *speech output*
  quality in task settings rather than in isolation; cost/latency-aware evaluation.
- Each with a one-line sketch of what a benchmark would have to do.

**7. Recommendations**
- For benchmark builders: report per-task breakdowns, publish the audio, state the judge, include
  a text-only baseline, version the benchmark.
- For model builders: report which version, which prompt, which judge.
- For readers: how to read an aggregate score.

**8. Conclusion**

## Rules while writing
- Every number traceable to the catalogue or a named paper. No number from memory.
- Every claim about a benchmark checked against that benchmark's own paper.
- No claim that a model is "best" — the tables are aggregated published numbers, not a controlled study.
- Do not attribute opinions to any named researcher; cite papers, not people's views.
- AI authorship disclosed in the paper itself, as on the site.
