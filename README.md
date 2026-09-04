# Spoken LLM Benchmark Atlas

A living index of **spoken LLM benchmarks** — what each one measures, how they classify, when they
appeared on arXiv, and how models score where scores have been published.

**Site:** https://speechlab0210.github.io/spoken-llm-benchmarks/
**Part of [SCOOT 2.0](https://speechlab0210.github.io/scoot/#benchmark-atlas)** — the speech-communication
learning-resources & SIG-activities page (since 31 Aug 2026).
**Corrections and additions:** speechlab0210@gmail.com (put `[Atlas]` in the subject line)

The catalogue is rebuilt daily from a fresh crawl of new arXiv postings. It is built and maintained
by an AI agent (Claude Fable 5) — it exists because Hung-yi Lee casually prompted the agent to see
what AI agents can do. **No human has verified the content**, and it is not an official publication
of ISCA or any other body; see *Provenance* below for what that means and how to check it.

## Scope rule

A **spoken LLM** takes speech in and/or produces speech out **and is a general-purpose model**.
A system that only does ASR or only does TTS is not a spoken LLM, and a benchmark that only measures
transcription or synthesis quality is out of scope. Audio-understanding benchmarks (sounds, scenes,
music) *are* in scope when the system under test is a general audio-language model rather than a
dedicated classifier.

That rule is doing real work: it is what separates this field from the decades of speech research
before it, and applying it removed a large number of otherwise plausible candidates.

## What is here

| | |
|---|---|
| `data/taxonomy.json` | 19 capability categories in 6 groups — the site's classification backbone |
| `data/benchmarks.json` | the catalogue, one entry per benchmark |
| `data/models.json` | the spoken LLMs that appear as table rows |
| `data/results.json` | flat model × benchmark cells; **every cell carries a source** |
| `data/latest.json` | output of the daily arXiv crawl (generated — do not hand-edit) |
| `data/institutions.json` | canonical organisations behind the benchmarks and models: type, country, sites (city, lat, lon), raw aliases |
| `data/affiliations.json` | per benchmark: the institutions on its paper with lead/last-author flags; per model: the releasing organisation(s) with an evidence URL |
| `data/world.json` | country outlines for the map (world-atlas 110m, Natural Earth, public domain), pre-projected |
| `site/index.html` | the built site: a single file, no external requests, no build step |
| `paper/` | an accompanying survey of the 2025–2026 wave |

## Reproducing it

```bash
node scripts/build.mjs                              # rebuild the site from data/
python scripts/daily_crawl.py --days 3 --rebuild    # daily arXiv scan (no model in the loop)
python scripts/fetch_paper.py 2410.17196            # pull a paper's text, tables preserved
python scripts/harvest_oai.py --from 2025-01-01 --until 2026-08-21 --sets eess
```

`build.mjs` validates before it writes and **fails the build** on: an unknown category, a malformed
arXiv id or date, a duplicate id, a non-http link, a result cell with no `source`, or an affiliation
record that points at an unknown benchmark, model or institution. A catalogue entry with no affiliation
record yet is allowed (new entries arrive daily) and is reported as *not yet attributed*.

```bash
node scripts/make_world.mjs raw/countries-110m.json data/world.json   # regenerate the map outlines
python scripts/build_affiliations.py ...                             # workflow output -> institutions.json + affiliations.json
```

## Data contract

**Benchmark entry** — required: `id`, `name`, `summary`, `categories` (≥1, must exist in the
taxonomy). Optional: `full_title`, `arxiv_id`, `arxiv_date`, `venue`, `url`, `code`, `data`,
`leaderboard`, `tasks[]`, `languages[]`, `metrics[]`, `io`, `size`, `aka[]`, `note`.
A benchmark may sit in up to three categories; most do sit in more than one, deliberately.

**Result cell** — required: `benchmark`, `model`, `metric`, `value`, `source`.
`source` is a human-readable citation ("VoiceBench Table 3", "Qwen3-Omni technical report Table 7");
`source_url` makes it clickable.

> **A number without a source cannot enter the site.** This is the most important rule in the repo.
> The tables are only worth anything if every cell is traceable.

**Institution** — required: `id`, `name`, `type` (`academia` | `industry` | `government` | `nonprofit` | `other` | `unresolved`),
`country` (ISO 3166-1 alpha-2), `sites[]` (`city`, `lat`, `lon`), `aliases[]` (the raw strings that map here), `confidence`.
Optional: `short`, `parent` (umbrella body such as the Chinese Academy of Sciences).

**Affiliation record** — `affiliations.benchmarks[<id>]`: `status`, `institutions[]` (`inst`, `unit`, `city`, `lead`, `last`,
`evidence` = `printed` | `email_domain` | `footnote`, `raw`), `verified` (`confirmed` | `corrected` | `cannot_verify`).
`affiliations.models[<id>]`: `status` (`ok` | `unknown` | `composite`), `builders[]` (`inst`, `unit`, `lead`), `evidence_url`.
*Lead* means the first author's affiliation(s). Cascades of third-party parts are `composite` and carry no builder.

## How to read the tables

They aggregate **published** numbers; nothing was re-run. Scores for the same model on the same
benchmark differ between sources because the prompt, decoding settings, judge model, audio rendering
and checkpoint all vary. Two safeguards are applied mechanically:

- **One metric per column.** A column uses a single metric — the best-covered one, preferring an
  aggregate over a sub-score — so a column never blends incommensurable quantities. The `(+n)` in a
  header counts the other metrics reported for that benchmark that are *not* shown.
- **Scale-collision guard.** Where the same metric name appears on two scales (a 1–5 judge score and
  the same thing normalised to 100), the cells are relabelled and kept in separate columns. The
  split requires seeing one model reported at both magnitudes by two different sources; a low
  score on a single published scale is a low score, not a different unit, and is left alone.

A blank cell means **not reported**, never zero.

## Provenance

- **Pre-2025** seeded from two surveys read end to end: Yang, Ho & Lee, *Towards Holistic Evaluation
  of Large Audio-Language Models* (arXiv 2505.15957, EMNLP 2025), and Arora et al., *On The Landscape
  of Spoken Language Models* (arXiv 2504.08528, TMLR 2025).
- **2025-01 → 2026-08** collected independently, by two *different* arXiv interfaces — the query API
  and the OAI-PMH bulk interface — so coverage does not depend on one endpoint or on model recall.
  Roughly 25,000 speech-relevant records were scanned.
- **Cross-checks** that keyword search misses: community index repos, spoken-LLM technical reports
  (a reverse index of which benchmarks matter), live leaderboards, and capability-specific sweeps
  for paralinguistics, interactivity, trustworthiness and non-English coverage.
- **Every arXiv identifier** was read off the arXiv API or the paper's own abstract page. None were
  filled in from model memory. Titles matched by automatic search were re-checked against the paper,
  which is how several bad matches were caught and discarded rather than published.

- **Institutions** were read off each paper's own author block (arXiv HTML, or the PDF first page where the
  HTML omits affiliations), then independently re-read by a second pass that tried to refute the first. Raw
  affiliation strings were mapped to canonical organisations (whole university; parent company; member
  institute for umbrella bodies) with a recorded confidence, and placed at the campus or lab site named on
  the paper. Model builders come from the model's own paper, report or model card, with the evidence URL
  kept in `affiliations.json`. Counting is whole, not fractional: a benchmark counts once per distinct
  institution on its paper, or once for its first author's institution in *lead* mode.

**Known limits.** Discovery is biased toward English-language arXiv preprints; benchmarks that never
preprint, or that appear only in non-English venues, are under-represented. Keyword-driven search has
a recall ceiling, and a triage pass over an independently harvested pool was run specifically to
measure and partly close it. Result coverage is uneven: most catalogued benchmarks have no published
cross-model comparison to extract.

Corrections are genuinely welcome, and are what keep this honest. Every applied edit appears in the
changelog on the site.

## Licence

Catalogue data (`data/`) is offered under CC BY 4.0; code under MIT. The underlying papers belong to
their authors — this is an index, and every entry links back to the source.
