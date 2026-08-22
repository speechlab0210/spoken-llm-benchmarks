# What We Measure When We Measure Spoken LLMs: A Survey of Benchmarks, 2025–2026

## Abstract

Spoken large language models are evaluated by a literature that has roughly quintupled in two years and that now contains more benchmarks than any single research group can read. This survey describes a catalogue of 360 benchmarks for general-purpose spoken and audio language models, of which 313 were first posted to arXiv in January 2025 or later. It contributes five things: a taxonomy of nineteen categories in six groups that reconciles the two existing taxonomies of the area, adding audio-grounding diagnostics as a first-class category and treating coverage as a cross-cutting condition rather than a capability; an account of the 2025–2026 wave organised as six substantive shifts, each backed by counts and named benchmarks; a treatment of six cross-cutting methodological problems, from synthetic stimuli to text-prior leakage; an inventory of what the evidence does not support, including a set of capabilities for which no benchmark could be found; and recommendations for benchmark builders, model builders and readers of leaderboards. The recurring finding is uncomfortable: a substantial share of reported spoken-LLM performance is recoverable without the audio, the aggregate scores most often quoted conceal substantial per-task variance, and the same model on the same benchmark is published with materially different numbers by different papers. The survey was written by an AI system working over a machine-maintained catalogue; section 2 states what that implies for how it should be read.

---

## 1. Introduction

The problem this literature is trying to solve was created by a definitional move. When a speech system was an automatic speech recogniser, it had a number: word error rate on a named test set. When it was a synthesiser, it had a number: a mean opinion score. A spoken language model is defined by the claim that it does not have one job, and a system with no single job has no single number. Every capability that a text language model is asked to demonstrate must be re-asked of it, and then a second set of questions must be asked that text evaluation never had to pose — whether the model heard the sigh, whether it knew when to stop talking, whether it treated a speaker with one accent differently from a speaker with another.

The field's response has been to build benchmarks, quickly. The catalogue underlying this survey holds 360 of them as of 2026-08-22. Forty-seven were first posted before 2025: one in 2020, two in 2021, one in 2022, eleven in 2023 and thirty-two in 2024. The remaining 313 arrived from January 2025 onward — 147 during 2025 and 166 in January through August 2026 alone. The quarterly series locates the inflection more precisely than the annual one: five postings in 2024Q2, ten in Q3, fifteen in Q4; then twenty, twenty-eight, forty-six and fifty-three through the four quarters of 2025; then sixty-eight in 2026Q1 and seventy-two in 2026Q2, with 2026Q3 standing at twenty-six for July and August alone and still incomplete. Roughly six out of seven benchmarks in this area are less than twenty months old.

Counts of this kind are easy to over-read. A curve like that is equally consistent with a field producing a great deal more of the same thing, and part of what follows is an argument that it did not: three of the nineteen categories in the taxonomy below have zero or one member older than 2025, and one category — the minimal-pair likelihood protocol — is the only one that has been displaced rather than expanded.

### 1.1 Position relative to existing surveys

Two surveys already organise this area, and this one is built to sit between them rather than to replace either.

Yang, Ho and Lee, *Towards Holistic Evaluation of Large Audio-Language Models* (arXiv 2505.15957, EMNLP 2025), organises evaluation of large audio-language models by capability dimension — auditory awareness and processing, knowledge and reasoning, dialogue-oriented ability, and fairness, safety and trustworthiness — and is, within the period it covers, the finest-grained account of what individual benchmarks test. Its coverage extends to early 2025, which is to say up to the period in which most of the benchmarks catalogued here were published.

Arora et al., *On The Landscape of Spoken Language Models* (arXiv 2504.08528, TMLR 2025), organises the models rather than the tests, by architecture, training regime and evaluation paradigm; its evaluation axis distinguishes likelihood-based, generative, interactivity-oriented and trustworthiness-oriented protocols. Evaluation is one section of a broader survey, and it explicitly excludes ASR- and TTS-style tasks from scope.

The delta of the present survey is threefold. First, coverage: the window from 2025-01 to 2026-08 is where 313 of 360 catalogued benchmarks live, including entire sub-literatures — full-duplex timing, audio-grounding diagnostics, voice-agent task completion, meta-evaluation — that either did not exist or existed as isolated examples when the two anchor surveys were written. Second, taxonomy: the paradigm axis and the capability axis are not competitors, and section 3 merges them, using the paradigm split as the outer arc and capability dimensions as the resolution inside it, with two additions argued from the evidence. Third, maintenance: the survey is paired with a machine-maintained, daily-updated public catalogue, so that the fixed text can state a position while the moving parts — new arrivals, new result cells — are carried by the site rather than by a revision cycle.

### 1.2 Contributions

- A described and defended taxonomy of nineteen benchmark categories in six groups, reconciling capability-based and paradigm-based schemes, with audio-grounding diagnostics promoted to a category and coverage (language, length, domain) demoted from a capability to a condition.
- A structured account of the 2025–2026 wave as six shifts — grounding diagnostics, timing, conversational paralinguistics, trustworthiness, reasoning, and holistic consolidation — each with counts and named benchmarks.
- A treatment of six cross-cutting methodological problems: synthetic stimuli, judge dependence, aggregation, comparability, text-prior leakage, and redundancy, with quantities drawn from the catalogue's own extracted results.
- An inventory of gaps in which the count is zero or near-zero, and which are therefore claims about absence rather than about scarcity.
- Concrete recommendations for benchmark builders, model builders and readers of leaderboards.

---

## 2. Scope and method

### 2.1 Inclusion rule

A benchmark is included if it evaluates a general-purpose spoken or audio language model — a system that takes audio as input, or produces audio as output, or both, and is expected to handle instructions and tasks not fixed in advance. Benchmarks whose sole object is transcription accuracy or synthesis quality of a dedicated ASR or TTS system are excluded, following the scope decision of arXiv 2504.08528. The cut is imperfect at the edges and deliberately so: intrinsic generation quality is retained, because a spoken LLM's own output is part of what the model is, and speech-recognition-derived robustness suites are retained where the system under test is a general model rather than a recogniser.

The rule matters because it determines what the growth curve in section 1 is a curve of. Included in a wider cut, ASR benchmarks would dominate by count and by age, and the 2025–2026 shift would be much less visible.

### 2.2 How the catalogue was built

Construction had four stages. The two anchor surveys were read in full and every benchmark they name was entered. A systematic sweep of the arXiv API followed, crossing query families (spoken language model, audio language model, speech LLM, full duplex, voice agent, paralinguistic, audio understanding, and cognates) with monthly windows across the covered period, so that recall did not depend on a single ranking. Candidates were then triaged against the inclusion rule, and surviving entries were verified against the benchmark's own paper for name, arXiv identifier, first-posting date, task description, metric family and category assignment. Each entry carries up to three of the nineteen categories.

Results were extracted separately: 2,433 sourced cells, each a (benchmark, model, metric, value, source) tuple copied from a published table, covering 69 models and 89 benchmarks with at least one cell. No number in the results tables was produced by running a model; every cell is a published claim by some paper, and cells from different papers on the same benchmark and model are stored separately rather than reconciled — a decision that turns out to be load-bearing for section 5.4.

The catalogue is live, and this paper is dated. Every count below is stated as of 2026-08-22, the date of the last recall pass — a sweep over an independently harvested arXiv pool that added 91 entries keyword-driven discovery had missed and took the catalogue from 269 to 360. All catalogue-wide totals, per-category counts, quarterly figures and co-occurrence counts in this paper are computed against that build. The site continues to update daily and will drift ahead of the text: figures read there will be larger than figures read here, and the gap widens with the age of this paper. Where the two disagree, the site is current and this paper is a snapshot with a date on it.

### 2.3 Limits, stated plainly

**Language and venue bias.** The sweep is over English-language arXiv postings. Benchmarks published only in non-English venues, only as a dataset release, only as a shared-task website, or behind a company blog post are invisible to it. The nine challenge-derived entries in the catalogue are there because someone wrote them up as a preprint.

**Recall ceiling.** Keyword search over titles and abstracts cannot reach a benchmark that describes itself in vocabulary the query families do not contain. Cross-checking against the two anchor surveys was intended to catch systematic blind spots in the query design, and did catch several; the recall pass of 2026-08-22 caught 91 more; neither can bound the residual.

**Summary-derived counts.** Several counts in sections 4 and 6 come from keyword or regex passes over catalogue summaries rather than over full papers. Summaries are truncated. A pass of this kind can only undercount: a benchmark that tests reverberation robustness without saying so in its abstract will be recorded as not testing it. Every "zero" reported below should be read as "not named anywhere the catalogue can see", which is a weaker claim than "does not exist", and a stronger one than "rare".

**No re-running.** Nothing here is a controlled comparison. The result tables aggregate published numbers produced under different prompts, harnesses, decoding settings and judges. They support statements about the *state of reported evidence* — how thin it is, how inconsistent it is, where it concentrates — and they do not support statements about which model is better. No such statement is made.

### 2.4 Authorship

This survey was written by an AI system. The catalogue was assembled by automated sweeps with automated verification; the analysis passes over it were performed by a language model; the prose was drafted by a language model; and the paper is maintained alongside a catalogue that updates daily without human intervention in the loop.

Three consequences follow for how it should be read. First, almost every benchmark name in this paper carries an arXiv identifier precisely so that any claim can be checked at its source in one step, and readers are asked to do that for anything they intend to rely on. Second, the failure mode of a machine-written survey is not usually a wild invention but a plausible-looking misattribution — the right claim assigned to the wrong benchmark, or a number carried across from a neighbouring row — so identifiers and counts deserve more suspicion than arguments. Third, the interpretive claims in sections 4 to 7 are the output of a language model — the same broad family as the text backbones inside the spoken models evaluated here, and as the LLM judges audited in section 5 — and no part of the design controls for that. The counts are auditable; the framing is not.

---

## 3. A taxonomy that reconciles the two existing ones

The nineteen categories below are grouped by the question each interrogates, running from the most model-internal to the most deployment-facing. The outer arc — model-internal measures, perception, use, interaction, trust — follows the evaluation-paradigm split of arXiv 2504.08528; the resolution inside each group follows the capability dimensions of arXiv 2505.15957. Benchmarks carry up to three category labels, and the great majority carry more than one: 344 of the 360 entries belong to more than one category. Group totals below are counts of category slots, not of distinct benchmarks.

### Group 1 · Is it a good model of speech? (43 slots)

Measures that need no task and no instruction — the closest available analogue to perplexity for speech.

**Likelihood-based judgment** presents a natural and an unnatural version of the same utterance and checks which receives higher likelihood, reported as pairwise accuracy. Speech has no shared tokenizer, so raw perplexity is not comparable across models and minimal pairs are the workaround. Representative: the Zero Resource Speech Benchmark 2021 (2011.11588), BabySLM (2306.01506), the Zero Resource Code-switched benchmark (2310.03018), SALMon (2409.07437). **Blind to:** anything requiring instruction-following, and anything the model can do but does not prefer.

**Intrinsic generation quality** scores produced speech without reference to a task: naturalness, intelligibility, and consistency of speaker identity, acoustics and sentiment with the prompt. Metrics run from MOS and UTMOS through generative perplexity and VERT to speaker and emotion consistency. Representative: EmphAssess (2312.14069), QualiSpeech (2503.20290), ParaS2SBench (2511.08723), STEB (2606.25529). **Blind to:** whether the speech accomplished anything, a gap quantified in section 6.1.

### Group 2 · Can it hear? (263 slots)

**Auditory awareness and scene understanding** asks whether the model notices what is in the audio — events, environments, music, multiple sources, and the boundary between speech and everything else. Metrics: accuracy, captioning scores, LLM-as-judge. This is the foundation layer on which the capability groups that follow are built. **Blind to:** whether noticing changes behaviour.

**Paralinguistic and speaker attributes** covers what is carried by *how* something is said: emotion, intonation, stress, accent, age, gender, timbre, volume, rate, laughter, sarcasm, persona. At 96 entries it is among the largest categories in the catalogue. It is the clearest dividing line between a spoken LLM and a transcription pipeline. **Blind to:** use — see the probe ladder result in section 4.1.

**Audio-grounding diagnostics** constructs cases in which a text prior, a plausible guess or the transcript alone would produce the right answer, and measures how much of a reported score survives removal of that shortcut. Metrics are differences rather than levels: accuracy drop under audio ablation, text-only baseline gap. Representative: "What Do You Like?" (2409.04927), RUListening (2504.00369), MCR-Bench (2508.15407), ALME (2602.11488), the text-prior/audio-reliance framework (2604.24401). **Blind to:** nothing in particular; the category's function is to bound the credibility of the other categories.

### Group 3 · Can it think? (235 slots)

**Spoken QA and world knowledge** delivers knowledge questions by voice or asks about the content of a clip. Frequently built by rendering an existing text benchmark to speech, which makes the category a direct measure of capability lost in the move from text input to speech input — and, as section 5.1 argues, imports the source benchmark's contamination.

**Reasoning over audio** requires multi-step inference for which the audio is necessary: temporal and compositional relations between sounds, causal chains, multi-hop questions, and inference combining acoustic evidence with linguistic content.

**Speech instruction following** tests obedience to instructions arriving as speech, including format and style constraints. Distinct from knowing the answer: models frequently know it and ignore the constraint. Metrics: strict and loose instruction accuracy, constraint satisfaction rate.

**Holistic multi-task suites** bundle many tasks into one score to make general-purpose claims comparable. Their aggregates are the numbers most often quoted and the ones that most reward reading the per-task breakdown; section 5.3 quantifies what the breakdown hides.

### Group 4 · Can it hold a conversation? (144 slots)

**Spoken dialogue quality** judges multi-turn conversation as conversation: coherence, context retention, response appropriateness, and reaction to the speaker's emotional state rather than only to their words.

**Real-time interaction and full duplex** covers the timing layer — when to start speaking, when to stop, how to handle an interruption, whether to backchannel, how long the user waits. Turn-based evaluation cannot see any of this, because it assumes the turns are already segmented. Metrics: latency, turn-taking F1, barge-in success, backchannel timing.

**Voice agents and task completion** scores whether the user's goal was achieved: tool and function calling from voice, multi-turn completion, form filling, grounded assistance.

### Group 5 · Can it be trusted? (155 slots)

**Safety, jailbreak and toxicity**; **bias and fairness**; **hallucination and faithfulness**; **robustness, spoofing and privacy**. Section 4.4 and section 6 treat these in detail. The structural point is that trustworthiness is largely a secondary property here: of the 117 distinct trust-tagged benchmarks, only 19 carry no capability label at all.

### Group 6 · Where does it work? (102 slots)

**Multilingual and dialectal coverage**, **long-form and multi-audio**, and **domain-specific evaluation**. These re-test every other capability under a changed condition rather than testing a new capability.

### 3.1 Why audio-grounding is a category and not a note

Two arguments support promotion.

The first is that the group has a distinct construction methodology, and it is small and recombinable: a text-only or transcript-substituted control that establishes the shortcut ceiling (ALME's matched control, 2602.11488; MusiCRS's query-only configuration, 2509.19469; the text-only/audio-only/multimodal split of LALM-as-a-Judge, 2602.04796; VoxSafeBench's matched text and audio inputs, 2604.14548); a mismatched pair that forces a choice of evidence; an ablation or corruption that isolates each channel's contribution (OMD-Bench, 2603.27187, which begins from congruent modalities and corrupts them precisely so that reliance is not confounded with informativeness; SSEU-Bench, 2509.13148, which varies speech and non-speech energy); and shortcut-free stimulus design, which builds material for which no linguistic prior exists (WoW-Bench, 2508.20976, on marine-mammal vocalisations; SonicBench, 2601.11039, PitchBench, 2605.26176, and STAR-Bench, 2510.24693, on procedurally generated or physically simulated sound; ParaPairAudioBench, 2606.24648, contrasting same-transcript against cross-transcript pairs).

The second is that the technique is retrofittable. DoWhatISay (2603.09881) is designed to attach to an existing benchmark rather than to replace it. That is what makes grounding a lens rather than a domain: of the 83 audio-grounding benchmarks, 82 carry at least one other category tag, the single exception being the text-prior/audio-reliance framework (2604.24401). Co-tags concentrate on precisely the categories from which headline claims are drawn — reasoning 24, auditory perception 17, paralinguistics 17, hallucination 14. A scheme that files grounding as a property of individual papers loses the ability to say that a capability result was or was not accompanied by a control.

### 3.2 Why coverage is a condition, not a capability

Multilinguality, long-form audio and professional domain are not abilities a model has in the way that turn-taking is an ability it has. They are conditions under which every other ability is re-tested, and treating them as capability categories produces two errors. It makes "multilingual" look like a solved-or-not property when the interesting question is which capabilities survive the language change — and section 6.4 shows they mostly do not, since multilingual meets interactivity once in the whole catalogue, voice-agent twice, and hallucination once. And it obscures the fact that a long-form benchmark and a short-form benchmark of the same capability are the same test at different scale, which is exactly the comparison worth making. Filing them as a cross-cutting group makes the empty and near-empty intersections visible, and those intersections are the most informative cells in the whole scheme.

---

## 4. The 2025–2026 wave: what changed

The category-level breakdown shows that the growth documented in section 1 was not uniform expansion. Three of the nineteen categories are effectively creations of the new wave. Domain-specific evaluation has 25 entries and none at all before 2025, beginning with FinAudio (2503.20990). Real-time interaction and full duplex has 39 entries, of which exactly one predates 2025 — the dGSLM turn-taking statistics (2203.16502) — with 25 of the 39 dated 2026. Voice agents and task completion has 26, of which exactly one predates 2025 — SpokenWOZ (2305.13040) — with no successor until MultiVox (2507.10859) in July 2025, and 19 of 26 posted in 2026. Intrinsic generation quality narrowly misses the same description: 33 entries with two pre-2025 members, the dGSLM turn-taking statistics (2203.16502) and EmphAssess (2312.14069).

Conversely, categories that already existed grew without changing character as sharply: auditory awareness held 16 pre-2025 entries of 84, reasoning 12 of 97, holistic suites 12 of 64, instruction following 5 of 31. Paralinguistics, among the largest categories, expanded rather than being invented, with 12 pre-2025 entries against 38 in 2025 and 46 in 2026.

Exactly one category has a pre-2025 majority, and it is the one displaced rather than expanded. Likelihood-based judgment has ten entries, seven of them older than 2025 (2011.11588, 2104.14700, 2302.12057, 2305.13009, 2306.01506, 2310.03018, 2409.07437), with only S2SBench (2505.14438), TurnNat (2607.01345) and one further 2026 arrival since. The minimal-pair protocol was native to the era when spoken language models were self-supervised encoders without instruction interfaces; generative and judged protocols have largely replaced it.

### 4.1 From "can it do the task" to "is it listening at all"

The defining feature of audio-grounding work is negative: these are not tests of a capability but tests of whether a reported capability was exercised, and they exist because the answer has repeatedly turned out to be no.

The line begins in the second half of 2024. MuChoMusic (2408.01337), JASCO (2409.14526) and "What Do You Like?" (2409.04927) are the earliest tagged entries, and the third states the founding observation without hedging: many Gaokao listening-comprehension items are answerable from the conversation transcript alone. AV-Odyssey Bench (2412.02611) closes that year reporting that its motivating probe finds multimodal models failing tasks as elementary as judging which of two sounds is louder. Growth is then steep: 8 such benchmarks in 2024, 30 in 2025, 45 in the first eight months of 2026 — nineteen in 2026Q1 alone. Roughly one 2026 arrival in four carries the tag, against about one in five in 2025.

The findings converge on four claims.

*Established benchmarks leak.* RUListening (2504.00369) hardens music question answering with a Perceptual Index derived from text-only language-model log-probabilities, and reports text-only models reaching 56.4 per cent on MuchoMusic without any audio. The text-prior/audio-reliance framework (2604.24401) generalises this into two axes — answerability from text and general knowledge alone, and actual dependency on the acoustic signal — and applied to eight models across three existing benchmarks finds them retaining 60 to 72 per cent of their full-audio scores with no audio input, with only 3.0 to 4.2 per cent of audio-requiring items needing the complete clip. AKB-2000 (2603.19195) measures how much auditory knowledge a text-only pre-trained backbone already carries, comparing direct text probing, captioner cascade and audio-grounded settings.

*Where audio and text disagree, text usually wins.* MCR-Bench (2508.15407) presents deliberately inconsistent audio-text pairs and reports pronounced bias toward the textual input. ALME (2602.11488) quantifies this with a Text Dominance Ratio counting how often a model follows conflicting text despite being instructed to trust the audio, reporting ratios an order of magnitude or more above a transcript-substituted baseline. DEAF (2603.18048) escalates textual influence across emotional prosody, background sound and speaker identity, separating content-driven bias from prompt-induced sycophancy. VoxParadox (2605.27772) constructs 2,000 items in which the transcript's claim contradicts the actual speaking style. EMIS (2510.25054) and LISTEN (2510.10444) apply the same design to emotion; CMM (2410.12787) attributes the pattern to unimodal priors and spurious inter-modality correlations; SYAUDIO (2601.23149) finds it surviving as sycophancy, with models conceding to a user assertion that contradicts the acoustic evidence.

*Perception and use are separable.* The Prosodic Underuse Probe Ladder (2608.19211) localises whether prosodic information is lost in the audio path, misinterpreted internally, or represented but not used in the answer, combining matched-content contrasts with layerwise probing and hidden-state intervention. Hear2Act (2608.19515) tests whether prosodic evidence changes a downstream decision rather than whether it can be reported. This matters for interpretation: a low score on a paralinguistic benchmark does not establish that the model did not hear.

*Audio can subtract.* S2SBench (2505.14438) quantifies intelligence degradation under audio input; Speech-IFEval (2505.19037) measures catastrophic forgetting relative to the underlying text LLM; When Silence Matters (2510.00626) shows that irrelevant audio — silence, synthetic noise, environmental sound — interferes with text-only reasoning that does not require it.

The uncomfortable implication is stated in section 5.5. A number reported without a text-only control and an audio-ablated control is not a measurement of audio understanding; it is an upper bound of unknown tightness.

### 4.2 Timing became measurable

Before 2025, the turn structure of a spoken exchange was supplied by the harness, with one isolated precedent. The model received a segmented utterance and returned a response, and the score was a property of that response; onset time, overlap, yielding behaviour and silence were not merely unmeasured but unrepresentable.

The pivot is datable to within a week. Talking Turns (arXiv 2503.01174) scores turn-taking using a supervised predictor of human turn-taking events as judge; Full-Duplex-Bench (arXiv 2503.04721) reports pause handling, backchannelling, turn-taking and interruption management under automatic metrics. Two taxonomies formalised the shift shortly after: arXiv 2505.15957 names full-duplex dialogue management with four members, and a dedicated full-duplex survey (arXiv 2509.14515) proposes temporal dynamics, behavioural arbitration, semantic coherence and acoustic performance. The dialogue slice by contrast reaches back to SpokenWOZ (2305.13040) and had accumulated SD-Eval (2406.13340), Chat-Audio Attacks (2411.14842) and ADU-Bench (2412.05167) before any timing-aware benchmark existed.

The sub-field grows faster than the field: within the interactivity section, 13 entries in 2025 against 25 in the first eight months of 2026, a step of roughly 1.9×, against a catalogue-wide step of about 1.13×. Its sub-dimensions have stabilised into roughly nine groups, and coverage across them is markedly uneven. Turn transition itself is dense (Talking Turns, TurnNat 2607.01345, M3-DuplexBench 2607.29125); user-initiated interruption and barge-in is dense (Full-Duplex-Bench v1.5, 2507.23159; FD-Bench, 2507.19040; SID-Bench, 2603.24144); model-initiated interruption and proactivity has several entries (FLEXI, 2509.22243; SocialOmni, 2603.16859; ProVoice-Bench, 2604.15037). Against that, backchannelling is named only by Full-Duplex-Bench and its v1.5 overlap scenarios; post-interruption recovery has exactly one dedicated benchmark, IHBench (2606.19595), whose own framing distinguishes recovery from barge-in detection, endpointing and turn-taking; and tempo and synchronisation has one, Game-Time (2509.26388). State maintenance across duplex turns is covered by EchoChain (2604.16456) and MTR-DuplexBench (2511.10262); policy-conditioned turn management by Instruct-FD (2607.20460); the visual extension by VideoFDB (2605.30256).

Latency is the instructive failure. It is measured everywhere and standardised nowhere: across the catalogue's one-line descriptions only two name it as a headline dimension, FLEXI (2509.22243) and SPEARBench (2607.05365), and in both it is one dimension among several. arXiv 2504.08528 records two competing terms for the same quantity — first-packet latency and response latency — defines it as the delay from user offset to model speech onset, notes dependence on hyperparameters, hardware and network, and gives roughly 200 ms as the human reference. Its collected table makes the incomparability concrete: vendor-reported figures such as Moshi 7B at 200 ms, GPT-4o at 320 ms and Qwen3-Omni-30B-A3B at 234 ms sit far below third-party measurements, and one model measured by two harnesses on two GPUs differs by a factor of two, GLM-4-Voice appearing at 3,244 ms under one protocol on an A40 and 1,563 ms under another on an L40 in the same table. Within a single rig the spread remains large — 347 to 5,588 ms on the L40 set, 399 to 3,675 ms on the A40 set. A metric-design fork is now opening on top of that: SID-Bench's Average Penalty Time prices false alarms and late responses in a common temporal currency rather than reporting bare milliseconds, which makes it incomparable to millisecond reporting in turn.

Two reflexive problems close the picture. Having abandoned turn segmentation in order to see timing, MTR-DuplexBench (2511.10262) reintroduced it to score content, cutting continuous duplex dialogue back into discrete turns because the boundaries are otherwise blurred; Full-Duplex-Bench-v2 (2510.07838) instead imposes structure externally via an automated examiner enforcing staged goals. And the judges are themselves under audit: an audio-judge reliability study (2607.07985) validates Gemini-family scoring of full-duplex conversations from raw stereo against three calibrated human raters over 209 sessions.

Interactivity is also converging with voice-agent evaluation, and the merged cluster is overwhelmingly though not exclusively a 2026 phenomenon: eleven of the 39 interactivity benchmarks also carry the voice-agent tag, ten of the eleven dated 2026 and the earliest 2025-09. Among them are tau-Voice (2603.13686), Full-Duplex-Bench-v3 (2604.04847), ProVoice-Bench (2604.15037), EVA-Bench (2605.13841), IHBench (2606.19595), the audio-judge reliability assessment (2607.07985) and DuplexWorld (2608.10716). The same widening is visible inside a single family: Full-Duplex-Bench went from four conversational behaviours (2503.04721) to overlap scenarios (2507.23159) to multi-turn streaming examination (2510.07838) to disfluent real audio with chained tool calls (2604.04847) in thirteen months.

### 4.3 Paralinguistics became a conversational requirement

Paralinguistics did not appear in this period; it changed what it asks. The earlier form is label classification — identify the emotion, the accent, the speaker's age — and it remains the bulk of the category. The new form asks whether the paralinguistic information changes the model's conduct.

Hear2Act (2608.19515) is the clearest instance: 480 persona-grounded scenarios with verifiable outcomes in which prosodic evidence must alter a decision, not merely be reportable. The probe ladder (2608.19211) attacks the same distinction from the mechanistic side. Speaker-emotion safety evaluation (2510.16893) renders identical malicious instructions across speaker emotions and intensities to test whether alignment survives paralinguistic variation. FairDialogue (2510.02352) traces how age, accent and gender enter decisions and recommendations and compound across turns rather than appearing in a single labelled judgment. On the output side, ParaS2SBench (2511.08723), SpeechParaling-Bench (2604.20842) and STEB (2606.25529) score whether the model's own delivery matches what the situation calls for.

The unfinished part of this shift is that the conversational and paralinguistic strands remain administratively separate. Section 6.5 records that the intersection of paralinguistics with generated-speech safety is empty, and section 6.6 that the intersection of real-time interaction with safety, fairness and hallucination is empty in all three cases.

### 4.4 Trustworthiness grew its own literature, with audio-specific attack surfaces

Trust-tagged work accounts for 117 of the 360 benchmarks, occupying 155 category slots across robustness (71), safety (33), fairness (22) and hallucination (29). Its share of new releases is flat rather than rising — roughly 10 of 32 benchmarks first posted in 2024, 50 of 147 in 2025, 56 of 166 in January–August 2026 — so the area has grown with the field rather than ahead of it. Only 19 of the 117 carry no capability label at all; trustworthiness is mostly a secondary property of benchmarks built for something else.

What distinguishes it from text-side safety work is the attack surface, and four surfaces recur that text evaluation structurally cannot cover.

The waveform is an instruction channel transcript-based content moderation cannot inspect: AudioSafe (2508.02175) plants backdoor triggers in acoustic features rather than in what is said. Harm can be distributed across simultaneous sources with no single harmful utterance: SACRED-Bench (2511.10222) composes auditory scenes — overlapping harmful and benign speech, benign speech mixed with harmful non-speech audio, multi-speaker dialogue — phrasing questions so that no harmful information appears in the text prompt at all, and ARENA (2608.15578) formalises this as the audio-grounded setting, where a text query safe in isolation elicits harm only jointly with the audio. The speaker is an attack parameter: 2510.16893 varies delivery rather than content, and the gaslighting benchmark (2509.19858) treats manipulative delivery as the attack; the catalogue's earliest safety entry (2406.17430) already named malicious imitation of age, gender and ethnicity as a harm with no textual analogue. And the microphone captures people who never consented to be inputs: AP² (2507.10016) profiles private attributes from covertly captured audio, SH-Bench (2512.06380) tests refusal to process incidental bystander speech, HearSay (2601.03783) probes leakage from voiceprints alone, and VoxPrivacy (2601.19956) asks whether a model adapts what it discloses to whom. All four privacy entries are dated July 2025 or later.

Audio jailbreaking passes through three phases. Textual attacks are rendered to speech to ask whether text-side alignment transfers (2410.23861; Jailbreak-AudioBench, 2501.13772; AJailBench, 2505.15406, which converts ten policy-violating categories by TTS then perturbs the audio under a semantic-consistency constraint). Attacks then originate in audio: JALMBench (2505.17568) makes the distinction explicit with four text-transferred and four audio-originated methods alongside five defences, and Multi-AudioJail (2504.01094) couples reverberation, echo and whisper effects with cross-lingual phonetics. From late 2025, optimisation gives way to composition and automation: SACRED-Bench attacks black-box by composing scenes rather than optimising perturbations, ARENA trains a closed-loop controller, SpeechJBB (2606.06037) uses code-switched harmful speech with phonologically plausible pseudo-words, and AudioSafetyBench (2604.08867) organises large-scale red teaming into a policy-grounded taxonomy.

Defences now ship with the benchmarks — at least 14 of the 117 trust papers propose a mitigation — but guard models that inspect the audio itself rather than a transcript appear only from November 2025 (2511.10222, 2604.08867). The false-positive question arrived last: AOR-Bench (2606.21147), dated June 2026, is the catalogue's only over-refusal benchmark, against six whose stated object is audio jailbreaking.

Bias benchmarks exploit what a text prompt cannot supply: speaker identity that is involuntary, continuous and impossible to redact. Spoken StereoSet (2408.07665) fixed the design — identical content, different speakers — and later work varied what only the signal carries. The Speech Continuation Bias Probe (2509.22061) manipulates phonation type alongside gender; MedVoiceBias (2511.06592) renders 170 clinical cases through 36 voice profiles against identical text input, the load-bearing control; VoxSafeBench (2604.14548) generalises that control across two tiers. Two validity warnings attach, and both are internal to the literature: multiple-choice bias scores may not transfer to long-form behaviour (2510.01254), and measuring voice-driven bias on synthesised voices risks measuring the synthesiser, which VIBE (2604.17248) and RedVox (2606.26968) answer with human recordings. Because acoustic subgroups also differ in recognisability, a fairness gap may be a recognition gap: BiasInEar (2602.01030) separates demographic from structural perturbation, and a semantic-aware estimator (2608.13624) treats speaker as a random effect with semantic covariates.

Hallucination is among the most sharply accelerating categories in the catalogue — four benchmarks in 2024, nine across 2025 (among them SpeechIQ, 2507.19361, and MCR-Bench, 2508.15407), then sixteen in the first eight months of 2026 — and it converges on substitution rather than invention. Fourteen of its 29 members are also audio-grounding diagnostics, among them AVHBench (2410.18325), CMM (2410.12787), MCR-Bench (2508.15407), AQUA-Bench (2601.12248), AHA-Eval (2603.29263), the multi-event grounding sensitivity analysis (2603.03855), OMD-Bench (2603.27187) and HalluAudio (2604.19300), and the shared frontier reports the same mechanism: the text prior displaces acoustic evidence. Genuinely audio-specific failure types do exist — temporal order and sound-source attribution (2410.16130), false alarms rising with scene complexity (2603.03855), speech-vision temporal misalignment (SVHalluc, 2606.02642). January 2026 produced a cluster on abstention, with AQUA-Bench (2601.12248), the EAR score (2601.12973) and SYAUDIO (2601.23149) all asking whether a model recognises that no answer is supported — a shift from wrong answers to unwarranted ones.

### 4.5 Reasoning arrived, and inherited the text field's problems

Reasoning over audio is not new as a category — 12 of its 97 entries predate 2025 — but two things changed. Scoring moved from final answers to intermediate process, a pattern with no pre-2025 precedent: the Interspeech 2026 Audio Reasoning Challenge and its MMAR-Rubrics protocol (2602.14224) score the factuality and logic of chain-of-thought traces rather than the answer; AudioProcessBench (2606.09925) annotates step-level process errors in audio-grounded reasoning traces; AnyAudio-Judge Bench (2606.03116) decomposes captions into variable numbers of verifiable binary rubric items instead of holistic scoring.

And the construction convention that made rapid growth possible — voicing an existing text benchmark — imported the source benchmark's contamination alongside its items. Hearing the Order (2510.00628) and When Silence Matters (2510.00626) both attach audio to text reasoning benchmarks; the second finds that the audio interferes. Section 5 treats the general problem.

### 4.6 Holistic suites consolidated, and their aggregates started hiding more

Holistic multi-task suites number 64, 12 of them pre-2025, and their aggregate scores are the numbers most often quoted in model reports. Roughly a quarter of the catalogue's sourced result cells carry an aggregate-style metric name, and 36 of the 89 benchmarks with results report at least one. Among the 42 model-benchmark pairs reporting an aggregate plus four or more in-range components, the median component spread is 24.2 points. MMAU (2410.19168) with Qwen2.5-Omni reports, within a single source (2507.08128), a test-mini average of 71.5 over sound, music and speech splits spanning 65.9 to 78.1, a range of 12.2 points. SpeechR (2508.02018) with SALMONN reports an average of 34.73 over components ranging from 12.5 to 50.7. VoiceBench (2410.17196) aggregates components on incompatible scales, mixing 1-to-5 judge scores with 0-to-100 accuracies under a single average.

Alongside consolidation came a genre with no pre-2025 instance at all: meta-evaluation. Four entries clustered in October 2025 — bias-benchmark transferability (2510.01254), answer-order position bias (2510.00628), multiple-choice fragility (2510.04584), instruction-phrasing sensitivity (2510.23558) — followed by matched-backbone comparison against cascades (2602.17598), subset substitutability (HUMANS, 2605.00022), score-reconciliation work (SURE, 2605.30899), in-context demonstration effects (ALICE, 2603.20433) and two judge audits (2607.07985, 2607.13477). Around twenty catalogued entries are meta-evaluations or protocol audits rather than capability tests, and all but three date from 2025-09 onward. Five of the sixteen single-category benchmarks in the entire catalogue belong to this cluster, which is a way of saying that a paper about how badly the instruments work does not fit the capability scheme — a property of the scheme worth noting.

---

## 5. Cross-cutting methodological problems

Six problems recur across the catalogue independently of what each benchmark was built to measure. They present less as isolated defects than as design conventions adopted collectively, and because the overwhelming majority of entries occupy more than one capability category, a convention established in one area propagates readily into others.

### 5.1 The TTS-rendering pattern

The most widespread convention is to construct spoken evaluation data by synthesising it. A keyword sweep over each entry's name, summary, task list and note for TTS, text-to-speech, synthesis, re-render, voice conversion and cognates returns at least 36 entries; four mention synthesis only to disavow it and one refers to a TTS component of the system under test, leaving roughly 31 whose audio is wholly or partly synthesised. At least twelve state outright that an existing text corpus was voiced: BiasInEar (2602.01030) re-renders Global MMLU Lite; SpokenElyza (2603.12565) derives from ELYZA-tasks-100; Audio MultiChallenge (2512.14865) ports the text MultiChallenge axes; AJailBench (2505.15406) converts textual jailbreak prompts; Spoken DialogSum (2512.14687) voices rewritten scripts; SYAUDIO (2601.23149) adds synthesised arithmetic and moral items to existing audio sets; the Korean suite of 2605.27984 transfers source-language spoken-QA benchmarks; Hearing the Order (2510.00628) and When Silence Matters (2510.00626) attach audio to text reasoning benchmarks; VoiceBench (2410.17196), WildSpeech-Bench (2506.21875) and MedVoiceBias (2511.06592) build stimuli by synthesis. These counts are floors, since catalogue summaries are truncated.

The pattern is genuinely a strength. It is what made the 2025 expansion possible at all: rendering a validated text benchmark to speech reuses items whose text-side quality has already been vetted, and supplies a ready-made text baseline.

Two costs follow. Synthetic speech occupies a narrower distribution than any deployment condition, so robustness, prosody and paralinguistic conclusions inherit the synthesiser's biases — which is precisely the objection VIBE (2604.17248) and RedVox (2606.26968) raise about measuring voice-driven bias on synthesised voices. And the underlying text is by construction already published, placing both stimulus and answer inside the pretraining distribution of the model under test and of any text-based judge.

A counter-movement is visible and recent: roughly thirteen entries advertise human recordings as the design choice, including VCB Bench (2510.11098), VIBE (2604.17248), HumDial-EIBench (2604.11594), Full-Duplex-Bench-v3 (2604.04847) and RedVox (2606.26968), all dated 2025-10 or later. That the alternative was always available is shown by SD-QA (2109.12072), which recorded human speakers over an existing QA set in 2021.

### 5.2 Judge dependence

At least 30 entries obtain their score from a model rather than from a reference. The dependence is explicit enough to have generated its own nomenclature — SageLM (2508.20916) as the earliest purpose-built speech judge, then LALM-as-a-Judge (2602.04796), RoleJudge (2604.13804), AnyAudio-Judge Bench (2606.03116), ParaPairAudioBench (2606.24648), SpeakerSleuth (2601.04029), SDiaReward and ESDR-Bench (2603.14889), StanceBench (2607.22658) — and its own audits.

Those audits are unflattering. The LALM Judge Shortcut Audit (2607.13477) reports that supplying incorrect specialist labels drives five judges' emotion accuracy to 0.10 or below, and that one judge selects the same slot irrespective of A/B ordering, concluding that aggregate agreement overstates validity. The reliability study of Gemini-family audio judges (2607.07985), calibrated against three human raters over 209 stereo sessions, finds that rank ordering transfers across model versions while calibration does not — which means judge-scored leaderboards may preserve orderings while the absolute numbers drift with the judge's version.

The implication is structural rather than fixable by better prompting: judge-scored benchmarks measure with a moving instrument, and the model families supplying judges are largely the families being judged. Against 14 summaries describing LALM-as-a-judge protocols, only two entries in the whole catalogue — TalkArena (2502.15919) and Talking Turns (2503.01174), both from early 2025 — put human users in the loop of the interaction itself.

### 5.3 Aggregation

Section 4.6 gives the numbers. The structural point is that an aggregate is a claim that its components are commensurable, and in several widely quoted cases they demonstrably are not — a 1-to-5 judge score and a 0-to-100 accuracy averaged under one figure is not an average of anything. Where components are commensurable, a median spread of 24.2 points across components still means that the aggregate is a weighted opinion about which sub-task matters, presented as a measurement.

### 5.4 Comparability

Storing published cells without reconciliation makes the incoherence measurable. After normalising metric names, ten (benchmark, model, metric) triples in the results tables are reported by more than one paper with differing values, and all ten fall on the two most-quoted benchmarks, MMAU (2410.19168) and VoiceBench (2410.17196).

The MMAU speech split for Qwen2.5-Omni appears as 53.92, 59.76, 68.9 and 70.6 across the Qwen2.5-Omni report (2503.20215), the Kimi-Audio report (2504.18425) and the Audio Flamingo 3 report (2507.08128) — a spread of 16.7 points, larger than the gaps that model comparisons routinely turn on. The same model's MMAU average appears as 65.6, 71.0 and 71.5. Its VoiceBench AlpacaEval score appears as 4.49 (2503.20215) and as 4.33 (Audio Flamingo 3 report, 2507.08128), and its headline VoiceBench metric is named "Avg" and stands at 74.12 in one report against "Overall" at 73.6 in another (2509.17765). The raw-versus-rescaled mismatch is visible on GPT-4o-Audio, whose VoiceBench AlpacaEval appears as 4.78 (2410.17196) and as 95.6 (2509.17765) — the same quantity on two different scales, presented in both cases without the scale. SURE (2605.30899) attributes the incoherence to mismatched post-processing rather than to disagreement about the models.

The reason this is not a longer list is that replication is rare, not that agreement is common: only nine of the benchmarks with results draw numbers from more than one source paper at all. Discrepancy is detectable only where someone bothered to repeat the measurement.

A related instability sits below the discrepancies. Hearing the Order (2510.00628) reports that shuffling answer options causes swings of up to 24 per cent and can change model rankings, across six models and three benchmarks. The MCQA robustness assessment (2510.04584) finds sensitivity to both ordering and paraphrasing over MMAU, MMAR (2505.13032) and MMSU (2506.04779), arguing that single-number accuracies hide substantial variability. ISA-Bench (2510.23558) finds marked degradation under instruction-phrasing variation, and reports that fine-tuning for instruction robustness induces catastrophic forgetting. ALICE (2603.20433) finds in-context audio demonstrations improve format compliance while often degrading task accuracy.

### 5.5 Contamination, leakage and the cascade question

The dominant validity threat in this literature is not deliberate test-set contamination but text-prior recoverability, and the two are structurally coupled: voicing published text places stimulus and answer inside the pretraining distribution and simultaneously guarantees that a text prior exists which can answer without listening. The quantities are in section 4.1 — 60 to 72 per cent of scores retained with no audio in the eight-model study of 2604.24401; 56.4 per cent for text-only models on MuchoMusic per 2504.00369; text dominance an order of magnitude above a transcript-substituted baseline in 2602.11488.

On the architecture question, the evidence is thinner than the rhetoric surrounding it. Seven catalogue entries name a cascade comparison explicitly — Fleurs-SLU (2501.06117), Spoken-MQA (2505.15000), SageLM (2508.20916), matched-backbone testing (2602.17598), the ALLM fairness and safety framework (2603.13262), AKB-2000 (2603.19195) and VAmoS Bench (2607.27453) — and none carries the interactivity tag, so the comparison is being settled almost entirely on non-timing tasks. Where head-to-head numbers exist they are collated rather than generated: the appendix of 2505.15957 lists eight benchmarks on which ASR-plus-LLM cascades beat end-to-end models against four on which end-to-end wins, explicitly restricted to papers that ran the comparison at all — which is a selection-biased tally by construction. On interactivity specifically, 2504.08528 argues that end-to-end architectures enable smoother turn-taking and backchannelling while cascades incur higher latency; the single user study it cites, Talking Turns (2503.01174), reports the opposite ordering on interruption, with a VAD-based cascade yielding the turn better than an end-to-end model, and both rarely backchannelling.

Matched-backbone testing (2602.17598) supplies the reason to distrust any aggregate here: unless the text backbone is held fixed, an architecture comparison is partly a backbone comparison. Its own reported result is that clean-condition advantages can reverse by up to 7.6 per cent at 0 dB SNR.

### 5.6 Redundancy and thin adoption

Growth is concentrated in clusters that re-instantiate one design. A keyword pass finds at least 23 entries addressing full-duplex behaviour, seven carrying "duplex" in the name; at least 42 addressing emotion, empathy or emotional intelligence; at least 15 addressing jailbreaking and audio attacks; at least 17 realising the audio-text conflict design separately.

Adoption has not kept pace with production. Of 360 catalogued benchmarks, 89 have at least one sourced result cell, leaving 271 — about three-quarters — with no extracted cross-model number at all. Median coverage is five models against a 69-model roster, and the model-by-benchmark matrix is roughly a tenth dense. Nine models account for about 40 per cent of the 2,433 cells: Qwen2-Audio 150, Qwen2.5-Omni 147, SALMONN 132, GPT-4o-Audio 119, Kimi-Audio 92, Freeze-Omni 88, Qwen3-Omni 84, MiniCPM-o 82, Moshi 81. The single most-measured system is Qwen2-Audio, a 2024 model. Eight of the nine are open-weight, the sole exception being GPT-4o-Audio, which is the plausible explanation: comparability rests on what can be downloaded and re-run.

HUMANS (2605.00022) supplies the sharpest indictment of the resulting information content. Over ten subset-selection methods, eighteen audio models and forty tasks, it reports that 50-example subsets reproduce full-benchmark scores at Pearson r above 0.93 — while both the subsets and the full benchmarks correlate only about 0.85 with 776 human preference ratings.

---

## 6. What has no benchmark yet

With 360 benchmarks indexed, absence becomes measurable. The counts below are taken over benchmark names and catalogue summaries and therefore understate coverage; a count of zero indicates a topic that is not merely under-served but unnamed in anything the catalogue can see. Each gap is stated with a one-line sketch of what a benchmark would have to do.

### 6.1 Speech output that accomplishes something

The sharpest asymmetry in the taxonomy is between hearing and speaking: 263 category slots for "Can it hear?" against 43 for "Is it a good model of speech?", a ratio of about 6.1 to 1. Only 33 benchmarks judge generated speech at all, and their co-occurrence pattern is diagnostic. Generation quality meets paralinguistics eighteen times and dialogue twelve times, but voice-agent, robustness, safety and long-form exactly zero times each, and spoken-QA, reasoning and hallucination once each. Generated speech is scored for naturalness, expressiveness and style match — EmphAssess (2312.14069), ParaS2SBench (2511.08723), STEB (2606.25529), SPEARBench (2607.05365), SpeechParaling-Bench (2604.20842) — and almost never for whether it accomplished anything. Listenability or speech-worthiness is named in two summaries only, SpokenElyza (2603.12565) and WavBench (2602.12135), neither tied to a verifiable outcome.

*Sketch.* Set tasks whose success is observable only through the audio — a confirmation code read back, a route, a dosage — and score them by whether an independent receiver who never sees the reference can act on the recording correctly.

### 6.2 Memory and personalisation across sessions

Memory beyond a single conversation does not exist in the catalogue. "Session" appears in one summary, the audio-judge reliability assessment (2607.07985), where it denotes a recorded stereo file. "Memory" appears in one, Audio MultiChallenge (2512.14865), which ports the text MultiChallenge inference-memory and instruction-retention axes into a single spoken dialogue. At least twenty-five entries mention multi-turn or multi-round interaction and all are bounded by one conversation: ContextDialog (2502.19759) measures recall of earlier utterances, MTR-DuplexBench (2511.10262) segments a continuous duplex stream, SpeakerSleuth (2601.04029) checks speaker consistency within a dialogue.

Personalisation is named twice — PALM-Bench (2601.03531), on recognising personal concepts such as which speaker is a named friend, and VIBE (2604.17248), where personalised recommendation serves as a bias probe. A regex over user-profile, adapt-to-the-user and preference-over-time phrasing returns zero. VoxRole (2509.03940) covers persona consistency, but of the model's assumed character rather than the user's.

*Sketch.* Sessions separated by days, a voice-identified user whose corrections and constraints must persist, and scoring for appropriate forgetting as well as for recall.

### 6.3 Multi-party and overlapping speech with the model as participant

At least seven summaries mention multi-party, multi-speaker or overlapping speech, and in most the model is an observer: MSU-Bench (2508.08155) on speaker-centric understanding, SH-Bench (2512.06380) on suppressing bystander speech, SACRED-Bench (2511.10222) on overlap as an attack surface, MUSA (2605.17225) on cocktail-party distractors. All 39 real-time benchmarks are dyadic — Full-Duplex-Bench v1.5 (2507.23159) treats "the user talking to someone else" as an interference condition, and HumDial-FDBench (2604.21406) is dual-channel by construction — with SocialOmni (2603.16859) closest, covering speaker separation and interruption timing. The one genuine multi-party participation track, in the SLT 2026 SmartGlasses Challenge (2608.12034), appeared in the final month the catalogue covers. Diarisation is named once, in ART (2601.19673), and only as something it declines to test in isolation.

*Sketch.* Place the model in a three-or-more-speaker conversation requiring it to infer whether it is being addressed, attribute claims to speakers, and take the floor without displacing a human.

### 6.4 Coverage beyond the four-language core

The multilingual label overstates its contents. Of its 49 members, 22 name only English, Chinese, Japanese or Korean; ten name a language outside that set — Singlish in MNSC (2501.01034), German in ERM-MinMaxGAP (2603.21050), Persian in PARSA-Bench (2603.14456), Spanish in MUSA (2605.17225) and ESCUCHA (2607.17812), German and Italian in MCIF (2507.19634), Arabic and Bengali in SD-QA (2109.12072), French in RedVox (2606.26968), and Arabic and Hindi in two further entries — and 17 name none. Across all entries English is named sixteen times and Chinese sixteen, against four for Korean, three for Japanese, two each for German, Mandarin and Spanish, and one each for Singlish, Persian and Italian. Swahili, Yoruba, Vietnamese, Thai, Turkish, Portuguese and Russian appear nowhere by name; Arabic, Bengali, Hindi and French appear once or twice each, Arabic and Bengali in SD-QA (2109.12072) and French in RedVox (2606.26968). Only four benchmarks exceed roughly eleven languages — Fleurs-SLU (2501.06117), mSTEB (2506.08400), PolySpeech-100 (2606.01016) and, for music, UniVerseBench (2608.17852) — and none evaluates interaction.

What coverage exists stops almost entirely at static understanding. Multilingual meets interactivity once, in M3-DuplexBench (2607.29125, English and Japanese); voice-agent twice, in VoiceAgentBench (2510.07978) and one 2026 form-filling agent benchmark; long-form once, in MCIF (2507.19634); and hallucination once.

*Sketch.* Take one existing interaction or agent benchmark and instantiate it in ten languages outside the core, holding the task fixed so the language change is the only variable.

### 6.5 Delivery as a safety surface

The intersection of paralinguistics (96) and safety (33) is six benchmarks, all on the input side: the Speech-Specific Risk Benchmark (2406.17430), AP² (2507.10016), speaker-emotion safety evaluation (2510.16893), HearSay (2601.03783), LALM-as-a-Judge (2602.04796) and one prosody-driven jailbreak benchmark posted in July 2026. The intersection of generation quality and safety is zero. No benchmark asks whether a model's own delivery — calm, warm, authoritative — makes bad advice more persuasive, although exactly that property is what a synthesised voice is optimised for.

*Sketch.* Hold content fixed, vary the model's synthesis along delivery axes, and measure listener compliance or credibility attribution rather than the model's own output score.

### 6.6 Trust under real-time conditions

Across the 39 interactivity-tagged benchmarks, the intersection with safety is zero, with fairness zero, and with hallucination zero. No catalogued benchmark is tagged for refusal robustness under interruption or mid-utterance escalation. The nearest overlap is Full-Duplex-Bench-v2 (2510.07838), which lists safety among four task families but is catalogued under interactivity, dialogue and instruction-following. Only two of twenty-six voice-agent benchmarks carry safety at all (2510.07978, 2607.27453).

Fairness and hallucination are likewise measured almost entirely on isolated inputs. Fairness meets voice-agent, interactivity, instruction-following and long-form zero times each; only FairDialogue (2510.02352) and MedVoiceBias (2511.06592) embed bias in a decision-bearing setting, and both are recommendation studies. Hallucination meets paralinguistics and voice-agent zero times each, long-form three times and multilingual once — so hallucination under duration and under language change is represented by a handful of entries rather than by a literature.

*Sketch.* Run an existing refusal set through a full-duplex harness in which the user interrupts, escalates and repeats, and score whether the refusal holds across the interaction rather than at the first turn.

### 6.7 Deployment conditions the robustness category names but does not contain

The robustness category header names packet loss, codec artefacts, and recognising synthetic and spoofed audio. Across all summaries, packet, telephony and far-field return zero matches; reverberation matches once, in Multi-AudioJail (2504.01094), and codec once, in UltraEval-Audio (2601.01373), referring to the model's own audio codec. Spoofing, cloning or impersonation appears in one summary, AudioSafetyBench (2604.08867), as a misuse category rather than a detection task; authentication appears once, as one of six dimensions of AudioTrust (2505.16211). No record matches deepfake detection, replay attack or watermarking in any field. Only eleven summaries mention noise, SNR or degradation at all, with RSA-Bench (2601.10384) and ESCUCHA (2607.17812) the strongest, and both environmental rather than channel-based.

*Sketch.* A channel suite: the same task set passed through telephony codecs, packet loss profiles, far-field reverberation and device pickup, reported as a degradation curve rather than a single score.

### 6.8 Speakers outside the typical range

Child speech as input is represented by ChildVox (2605.29257) alone; BabySLM (2306.01506) concerns developmentally plausible training data and AudioSafetyBench (2604.08867) treats child voice as a misuse surface. Disfluency or impairment appears in five summaries, with VocalBench-DF (2510.15406) the only one making it the subject, and Full-Duplex-Bench-v3 (2604.04847), WildSpeech-Bench (2506.21875), RealTalk-CN (2508.10015) and SCENEBench (2603.09853) touching it incidentally. Dysarthria, aphasia and deaf or hard-of-hearing speech are named nowhere. The domain category has twenty-five members, at least four of which are commercial voice agents; clinical terms appear in two summaries and legal terms in one.

*Sketch.* Recruit atypical speakers rather than simulating them, and report per-speaker rather than pooled accuracy, so that the distribution rather than the mean is the result.

### 6.9 Cost, and staleness

A regex over price, dollar, USD, API cost and budget returns no matches at all. Latency appears in eight summaries, seven of them in the real-time cluster where timing is the phenomenon rather than a resource; only AudioMarathon (2510.07293) pairs understanding accuracy with inference efficiency. Compute appears as an evaluated axis exactly once, in AudioMarathon, which pairs understanding accuracy with inference efficiency; monetary cost appears nowhere, although cost is an axis on which deployment decisions are actually made.

Nothing addresses staleness either. Item refresh, expiry and declared versioning policy are named in zero summaries; ISA-Bench (2510.23558) is the only entry described as dynamic, and its dynamism is over instruction phrasings. The field's response to ageing is republication — Full-Duplex-Bench in four versions (2503.04721, 2507.23159, 2510.07838, 2604.04847), VocalBench in three (2505.15727, 2510.15406, 2511.08230), HumDial in three (2601.05564, 2604.11594, 2604.21406), Dynamic-SUPERB (2309.09510, 2411.05361) and MMAU (2410.19168, 2508.13992) in two each — which resets comparability each time it happens.

### 6.10 A note on the shape of the gaps

Read together, the empty cells share a structure. Almost every one is an intersection: paralinguistics × output, safety × timing, fairness × task completion, multilinguality × interaction, hallucination × duration. The categories themselves are well populated; what is missing is the product. That is a predictable consequence of how benchmarks are built — a paper proposes one axis and holds the others at their most convenient setting — and it suggests that the highest-yield unbuilt benchmarks are not new capabilities but existing ones re-instantiated under a second varied condition.

---

## 7. Recommendations

### 7.1 For benchmark builders

**Ship a text-only control and an audio-ablated control.** Given that eight models were found retaining 60 to 72 per cent of their scores without audio (2604.24401), a benchmark that reports only the full-audio number cannot distinguish a grounded result from a shortcut. The techniques are cheap and catalogued in section 3.1, and at least one (2603.09881) is designed to be attached to a benchmark that already exists.

**Report per-task breakdowns alongside any aggregate, and never average incompatible scales.** The median component spread across the 42 aggregate-reporting model-benchmark pairs is 24.2 points; the aggregate is a claim about commensurability and should be defended as one.

**State the judge, its version, and its prompt.** Rank ordering transfers across judge versions while calibration does not (2607.07985), so an absolute score without a judge version is not reproducible. Where feasible, report agreement against human raters on a subsample rather than only inter-judge agreement.

**Publish the audio, or the exact synthesis recipe.** If stimuli are synthesised, name the system and the voices, because conclusions about prosody, robustness and speaker bias may be conclusions about the synthesiser (2604.17248, 2606.26968).

**Version the benchmark, and say what changed.** Republication under a new name resets comparability. A version number with a changelog does not.

**Test one nuisance perturbation before release.** Shuffling answer options moved scores by up to 24 per cent and changed rankings in one study (2510.00628); a benchmark that has not checked its own order sensitivity does not know its own resolution.

### 7.2 For model builders

**Report which model version, which prompt template, which decoding settings and which judge.** The 16.7-point spread across published MMAU speech-split values for one model (section 5.4) is a reporting failure, not a modelling disagreement.

**Name the scale as well as the number.** The same VoiceBench AlpacaEval quantity for one model is published as 4.78 and as 95.6 (section 5.4); a score without its range is not a score.

**Reproduce the baseline numbers rather than copying them.** Copied cells inherit the post-processing of their source, which SURE (2605.30899) identifies as the cause of the observed incoherence.

**Report the text-input counterpart of any spoken result.** It costs one extra run and it converts an unbounded claim about audio understanding into a bounded one.

### 7.3 For readers of leaderboards

Treat a single aggregate as a hypothesis about a per-task table that has not been shown. Ask whether a text-only baseline is reported; if it is not, read the number as an upper bound. Check whether a benchmark's numbers come from one source paper or several — for most benchmarks here, the answer is one. Note the date of the models being compared: the most-measured system in the catalogue is a 2024 model, which means much of the comparability backbone is aged. And treat differences smaller than the reported per-task spread as not established, which for aggregate-reporting benchmarks means differences under roughly twenty-four points.

---

## 8. Conclusion

The 2025–2026 wave changed what spoken-LLM evaluation is about, not merely how much of it there is. Timing became an object of study rather than an assumption of the harness, going from a single isolated precedent before 2025 to a sub-field growing at roughly twice the rate of the field. Task completion with verifiable outcomes grew from a single pre-2025 entry to 26, 19 of them posted in 2026. Trustworthiness acquired attack surfaces with no textual analogue — waveform-level instruction channels, harm composed across simultaneous sources, delivery as an attack parameter, and bystanders captured without consent. And a genre appeared that had no pre-2025 instance at all: benchmarks whose subject is other benchmarks.

The most consequential result of that last genre is negative. A substantial share of reported spoken-LLM performance is recoverable without the audio; under deliberate audio-text conflict, models follow the text; scores move by up to a quarter under nuisance perturbations that have nothing to do with listening; aggregate scores conceal a median per-task spread of 24.2 points; and the same model on the same benchmark is published with materially different numbers by different papers. None of this is evidence that spoken LLMs do not work. It is evidence that the field does not currently know how well they work, because the dominant reporting format cannot distinguish a score earned by listening from a score earned by inference from the prompt.

The gaps are as informative as the counts, and they share a shape: the missing benchmarks are not missing capabilities but missing intersections. Speech output is scored for beauty and almost never for whether it accomplished anything. Memory stops at the end of the conversation. Real-time interaction and trustworthiness have not met. Coverage beyond four languages stops at static understanding. Monetary cost is measured nowhere. Each of these is buildable by taking an existing benchmark and varying a second condition.

This paper was written by an AI system, over a catalogue assembled and maintained by automated processes. Its counts are auditable — almost every benchmark carries the arXiv identifier under which its claims can be checked in one step — and readers are asked to check anything they intend to rely on, with particular suspicion reserved for identifiers and numbers rather than for arguments, since the characteristic failure of a machine-written survey is a plausible misattribution rather than an obvious invention. Its framing is not auditable in the same way, and it was produced by a system belonging to the class of systems under discussion. The counts state the catalogue as it stood on 2026-08-22; the catalogue is updated daily and will diverge from them; the arguments are meant to outlast them, and where they do not, the catalogue is the thing to trust.
