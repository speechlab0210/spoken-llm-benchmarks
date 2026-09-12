# Inclusion notes, 2026-08-22

These are the reader's notes from the day the catalogue was built, reproduced verbatim apart from this header. Candidate names were read against the inclusion rule in batches of 24, from each paper's arXiv abstract page (title, abstract, comment and journal reference); each batch ends with the borderline calls, the case for the other side, and the names corrected against the paper. The verdicts themselves are in `benchmarks.json` (admitted) and `rejected-2026-08-22.json` (rejected). Internal ids such as `voxprofile` are the working keys of that build, not the catalogue ids. How the rule is applied is described in the Method section of the site.

---

24 items in, 24 entries out; 3 marked OUT (hallulens = text-only; audiojailbreak = attack-method paper; simbabench = African ASR/TTS/SLID suite plus Simba model family, not a general-purpose speech-LLM evaluation).

Borderline calls worth a second look:
- voxprofile (Vox-Profile): kept IN as a paralinguistics benchmark, but the abstract says the systems under test are "speech foundation models" (trait classifiers/encoders), not LALMs/SLMs. If the site's scope is strictly spoken-LLM systems under test, this one could flip to OUT.
- rulistening (RUListening): part method (Perceptual Index metric + distractor generation), part resource (filtered MuchoMusic). Kept IN because the primary contribution is an evaluation-hardening framework and a released filtered benchmark; categorised audio-grounding first since it is explicitly a text-prior / noise-ablation diagnostic.
- audioinjectionrobustnessstudy: an empirical study that states "This work introduces a benchmark framework"; kept IN on that basis. It has no real name in the title, so I used the descriptive "Audio Injection Robustness Benchmark".
- dailyomni (Daily-Omni): audio-visual, not audio-only; kept IN because omni models are in scope and it carries an explicit audio-ablation / text-only-leakage diagnostic suite.
- s2sbench: perplexity-based plausible-vs-implausible pairwise protocol maps onto "likelihood"; io listed as speech-in/speech-out because the models under test are end-to-end speech-to-speech LLMs, though the evaluation itself contrasts audio input against text input.

Name corrections vs the discovery pass: "AJailBench (Audio Jailbreak)" -> AJailBench; "Spoken math reasoning benchmark" -> Spoken-MQA (per the alias and the paper's own name); "LALM-Temporal-Bench" -> TREA (the paper names its dataset TREA, not LALM-Temporal-Bench); "DCASE 2025 Audio QA Challenge" -> DCASE 2025 Task 5 Audio QA; "Audio Injection robustness study" -> descriptive name as above.

Possible near-duplicate pair in this batch: ajailbench (2505.15406, AJailBench) and audiojailbreak (2505.14103, AudioJailbreak) are distinct papers with confusingly similar names — do not merge.

Venues copied verbatim from the comment field, including stresstest's "Accepted to ACL 2026" and dcase's "Accepted to ICASSP 2026", which look forward-dated relative to the arXiv dates but are what the metadata says. No sizes, language counts or model names were added beyond what the abstracts state; msteb has no explicit language count so I recorded it as "massively multilingual (count not stated)".

=====

24 items in, 24 entries out; 8 marked OUT.

Borderline calls worth a second opinion:
- clothoaqa: OUT. It is an audio-QA evaluation set widely reused by AIR-Bench/AudioBench, but the paper proposes it as a task dataset (train+test) with LSTM classifier baselines, predating audio LLMs, and the scope rule explicitly names Clotho-family corpora as component data. If the site wants reused eval sets, flip to IN with ["spoken-qa","auditory-perception"].
- voicejailbreak: OUT as a method paper (its contribution is the fictional-storytelling attack against GPT-4o voice mode, not a released suite), but it IS a systematic safety measurement of a voice LLM, so a curator could reasonably flip it to IN with ["safety"].
- sdqa: IN, though the systems under test are ASR+QA cascades rather than end-to-end speech LLMs; kept because the primary contribution is a spoken-QA evaluation resource now used as the dialect/fairness axis in speech-LLM evals.
- compa: IN, though the models under test are contrastive audio-language models (CLAP-style) rather than generative LALMs; the paper's primary contribution is the two benchmarks, with CompA-CLAP secondary.
- emphassess: IN, but the systems under test are speech-to-speech resynthesis/translation models, not chat-style speech LLMs.
- codecsuperb and dasb both OUT for the same reason (tokenizer/codec component benchmarks); if the site keeps a "component/tokenizer" shelf they belong there, not under the LLM categories.
- The earlier discovery pass used a different category vocabulary ("task-understanding", "trustworthiness", "reasoning-knowledge", "agentic", "intrinsic-quality", "other"); I ignored those strings and re-derived categories from the given ID list.
- Two entries have no real benchmark name in the paper, so I coined short descriptive ones: "LALM object hallucination probe (Kuan et al.)" (2406.08402) and "Speech-Specific Risk Benchmark" (2406.17430).
- No duplicates spotted within this file. Sizes/languages/venues left null wherever the abstract, comment and journal_ref were silent (e.g. AudioBench has no venue in the metadata, and no language counts were stated for most items).

=====

24 items in, 24 entries out. 8 marked OUT: advwave, bestofnjailbreaking, guptaetaluniversalaudiojailbreakevaluation (all attack/method papers with no released evaluation resource), asrec (Chinese ASR error-correction benchmark; system under test is a text LLM over transcripts), codecfakeomni (anti-spoofing/deepfake-detection corpus), audioflan (instruction-TUNING corpus, framed as training data), linetalgpt4ovoicemodeexploration (GPT-4o evaluation report reusing existing tasks, no new benchmark), personabench (text-only personalization benchmark, no audio).

Borderline calls worth a second look:
- worldsense: an omni-modal VIDEO benchmark (cs.CV) rather than a speech-LM benchmark, but audio is required by construction and omni models are explicitly in scope, so IN. If the site is speech-only, this is the most likely one to drop.
- adiff: dual contribution (two difference-explanation datasets + the ADIFF model). Abstract explicitly says "propose benchmark, baselines for the task", so IN, but the title-named artifact is the model.
- wangetalsinglishevaluationdatasets (MNSC): also dual — corpus + SingAudioLLM model — but standardized splits and a human-verified test set are released and AudioLLMs/cascades are compared on it, so IN. Renamed from the clumsy discovery-pass name to MNSC.
- linetalgpt4ovoicemodeexploration: closest OUT bullet is "survey/position paper with no new benchmark"; it is an empirical report, not a survey, so the fit is imperfect. Flip to IN only if the site wants evaluation studies without new resources.
- evalsift: the arXiv entry is titled after SIFT-50M (a training corpus); only EvalSIFT is the benchmark, so I scoped the entry to EvalSIFT.

Names corrected from discovery-pass guesses: "Xiao et al. (2025) audio modality-specific edit jailbreak evaluation" -> Jailbreak-AudioBench; "Li et al. (2025) interactive arena evaluation" -> TalkArena; "Roh et al. (2025) multilingual/multi-accent audio jailbreak evaluation" -> Multi-AudioJail; "Wang et al. (2025b) Singlish evaluation datasets" -> MNSC; "ADIFF (Deshmukh et al., 2025b)" -> ADIFF. Note the codecfakeomni key names "CodecFake-Omni" but the fetched metadata is for CodecFake+ (2501.08238) — possible key/paper mismatch upstream; either way it is OUT.

Language/size fields left empty where the abstract does not state them (e.g. VoxEval's 56 tasks and URO-Bench's English/Chinese/code-switching appear only in the discovery-pass agent notes, not the abstract, so I did not copy them). io left null for contextdialog and set conservatively for talkarena, where the abstracts do not state the output modality.

=====

24 items in, 24 entries out; no additions or skips.

Three OUT calls, all judgement calls worth a second look:
- speechcaps (2408.13891): contribution is a multi-talker speaking-style captioning task used for pre-training plus a trained model; evaluation runs on the existing Dynamic-SUPERB. Called OUT as training corpus/model paper. If the site wants training-task datasets listed, this is the closest to flippable of the three (it does report a new multi-talker QA probe).
- spokentriviaqa (2410.00037): the arXiv id is the Moshi model paper. The "Spoken TriviaQA" name came from the discovery pass, not the paper; the abstract never mentions TriviaQA. Clear OUT.
- beanszero (2411.07186): the arXiv id is the NatureLM-audio model paper; BEANS-Zero is named as "a novel benchmark" in one sentence but the paper is model-centric. Called OUT under the "benchmark is incidental" rule. Note the tension with mae (2409.18680), which I kept IN because there the benchmark is the lead contribution and the MALLM model is the follow-on. If the project prefers to list BEANS-Zero anyway, it would be domain + auditory-perception.

Other judgement notes:
- openmubench (2410.15573): borderline IN. The abstract frames OpenMU-Bench as addressing training data scarcity, so it is simultaneously a training set and an evaluation suite, and the paper also introduces the OpenMU model. Kept IN because it is explicitly proposed and named as a benchmark suite.
- Names corrected away from discovery-pass descriptive labels: "Salmon" -> SALMon; "Can Large Audio-Language Models Truly Hear?" given the short descriptive name "Audio Hallucination Benchmark" (github repo is audio-hallucination) since the paper names no benchmark; "Red teaming audio LMMs" -> "Audio Is the Achilles' Heel"; "Speaker-in-dialogue understanding study" -> the paper's released dataset name "What Do You Like?".
- The earlier agent_cats used a coarser vocabulary (trustworthiness, task-understanding, reasoning-knowledge) that does not exist in the target category list; I re-derived all categories from title+abstract. Notably the four "trustworthiness" items split into fairness (2), hallucination (3) and safety/robustness (2).
- Sizes I deliberately did NOT copy from agent_notes because the abstracts do not state them: CAA (agent note claims 360 attack sets / 1,680 samples), Spoken StereoSet, ADU-Bench sub-counts beyond what the abstract lists. For OmniBench I left size null on purpose — the 84.5K figure is the OmniInstruct training set, not benchmark items.
- Three items are audio-visual / tri-modal rather than speech-only (avhbench, curseofmultimodalities, avodysseybench, plus omnibench). Kept IN as omni-model evaluations, but if the site is strictly speech/audio-in, these four are the ones to reconsider as a group.
- Venues taken only from journal_ref/comment. VoiceBench, MMAU, SAGI, OpenMU-Bench, CMM, red-teaming and AV-Odyssey have no venue stated in the provided metadata even though some were later published.

=====

24 items in, 24 entries out; 20 IN, 4 OUT.

Borderline calls worth a second look:
- maeb (MAEB): marked OUT. It is unquestionably a benchmark, but the systems under test are audio embedding models / encoders scored as representations in the MTEB ecosystem, not general-purpose audio LLMs. The abstract itself notes MAEB scores correlate with the same encoders' downstream performance inside audio LLMs, so a more permissive reading would put it IN under holistic + multilingual.
- interspeech2026audioencodercapabilitychallenge: marked IN, and it is the mirror image of MAEB. I split them because this challenge evaluates submitted encoders through XARES-LLM, an explicitly generative LALM evaluation harness (encoder + LLM produces text), whereas MAEB scores embeddings directly. If the parent wants consistency, both should move the same way.
- cascadeequivalencehypothesis: marked IN as an "evaluation framework" (matched-backbone testing) per the scope rule, but no dataset is released and half the paper is mechanistic interpretability (logit lens, LEACE). Defensible as OUT if you want dataset-bearing benchmarks only. It is a strong audio-grounding diagnostic either way.
- dailytalkedit: the input key/name is the benchmark (DailyTalkEdit) but the paper is titled and led by the model (HoliAntiSpoof). Marked OUT as a model paper plus anti-spoofing corpus; if anti-spoofing awareness in audio LLMs counts, it would be IN under robustness + safety.
- lostinspeech: earlier pass guessed "multilingual"; the actual system under test is text LLMs doing UD dependency parsing on transcripts, so OUT.
- spatialaqa: earlier pass called it a benchmark, but the abstract lists only an augmentation framework, a finetuning approach and a separation study, so OUT as a method paper.

Data quirks:
- koalabench: arxiv_id "2604.19782" does not match arxiv_date "2026-03" / date_full "2026-03-30". Copied the id verbatim as instructed, but the pair looks inconsistent — worth verifying upstream.
- Venue left null wherever the comment said only "Submitted to" / "Under Review" (alice, parsabench, voxemo, cascadeequivalencehypothesis, koalabench, wordsatplay). audiorag's comment says only "Accepted by Audio-AAAI", recorded verbatim as "Audio-AAAI".
- Sizes given in agent_notes but NOT in the abstract were dropped: stylebench ("14.4K multi-turn QA dialogues"), mugen ("35 tasks over seven dimensions, best-of-five candidates"), tauvoice (domain list retail/airline/telecom), biasinear (specific accent list). Only abstract-stated figures were kept.
- alme's earlier guess "paralinguistic" is wrong; it is an audio-grounding / text-prior diagnostic.
- Two near-identical text-dominance diagnostics appear in this batch: ALME (2602.11488, 8 languages, TDR) and DEAF (2603.18048, three acoustic dimensions). They are distinct papers, not duplicates, but they will read very similarly on the site.

=====

24 items in, 24 entries out; one OUT (stepaudioparalinguistic).

Borderline calls worth a second look by the curator:
- stepaudioparalinguistic (2507.16632): ruled OUT. The arXiv id resolves to the Step-Audio 2 technical report, a model paper. The discovery pass named it after StepEval-Audio-Paralinguistic, an eval set that is not mentioned anywhere in the supplied abstract. If the site wants StepEval-Audio-Paralinguistic as a benchmark entry it needs a different source, and the "550 Chinese samples / 11 dimensions" figure in agent_notes is NOT in this abstract.
- audiosafe (2508.02175): ruled IN, but the paper's headline contribution is the HIN backdoor attack framework; AudioSafe is the accompanying evaluation set. Defensible as OUT under the "method paper" bullet. Kept IN because AudioSafe is a named, described evaluation resource for ALLM safety.
- ap / AP^2 (2507.10016): ruled IN for the same reason — benchmark dataset plus the Gifts agent framework in one paper. Category is privacy leakage, which the taxonomy folds into "robustness".
- sagelm (2508.20916): ruled IN as an "evaluation framework", but note it is a JUDGE MODEL, not a test set — there are no benchmark items to run a model against. If the catalog is strictly test sets, drop it. SpeechFeedback is a training preference dataset, not an eval set.
- omnieval (2506.20960): audio-visual video QA for omni models. In scope per the "omni model" clause, but it is more video-centric than the rest of the list.
- cmibench: music-only. In scope because the systems under test are general audio-text LLMs (LTU, Qwen-Audio, SALMONN), not music-specific models.
- realtalkcn: framed as a dataset in the abstract but titled a benchmark and used to evaluate speech LLMs on disfluency/speaker/domain robustness, so IN rather than "plain component corpus".

Sizes/languages/metrics were taken only from the supplied abstracts. Where agent_notes carried numbers absent from the abstract (MSU-Bench "2,300 QA instances", MCR-Bench "Text Influence Rate up to ~98%", MMAU-Pro "up to 10 min", MCIF "IWSLT 2026 shared task", Step-Audio "550 samples"), those were deliberately omitted.

Names corrected from the discovery pass: "SpeechIQ (Speech-IQ)" -> SpeechIQ; "AP² (audio private-attribute profiling)" -> AP²; "AudioSafe (HIN backdoor benchmark)" -> AudioSafe.

Two full-duplex entries (fdbench 2507.19040, fullduplexbenchv15 2507.23159) are distinct papers from different groups, not duplicates — both kept.

=====

24 items in, 24 entries out. 22 IN, 2 OUT.

OUT calls:
- mlcslmchallenge (2509.13785): clear OUT — Interspeech 2025 shared task whose two tasks are multilingual conversational ASR and diarization+ASR, plus a 1,604-hour training/eval corpus. Pure ASR benchmark bullet.
- audiorole (2509.23435): BORDERLINE OUT, flagging for override. Title and framing are "an audio dataset"; the paper's demonstration is training GLM-4-Voice into ARP-Models on it, and ARP-Eval is introduced "to demonstrate the effectiveness of the dataset". I treated the eval as instrumental to a training corpus + model paper. If the site prefers to be inclusive about release-with-evaluation-protocol papers, this is the one to flip to IN (categories would be dialogue, paralinguistics).

Other borderline IN calls worth a second look:
- dobiasbenchmarksgeneralise (2510.01254): a meta-evaluation, not a conventional benchmark; kept IN because it explicitly proposes an evaluation suite for behaviour transferability. It has no benchmark name in the title, so I coined "SpeechLLM Bias Transferability Suite".
- speechcontinuationbiasprobe (2509.22061): a diagnostic probe / systematic evaluation rather than a packaged released suite; kept IN as a diagnostic evaluation resource. Name is descriptive ("Speech Continuation Bias Probe") — no official name in the paper.
- musicrs (2509.19469): domain-narrow (music conversational recommendation) but audio-LLMs are among the systems under test and the audio-only / query-only / audio+query configuration is a genuine audio-grounding ablation.
- cs3bench (2510.07881): "Evaluating AND Enhancing" — the paper also proposes training methods (Chain of Recognition, Keyword Highlighting), but the named benchmark leads the title and is released, so IN.

Naming discrepancy: voiceagentevaloutboundeval (2510.21244) is titled "VoiceAgentEval" but the abstract consistently calls the artifact "OutboundEval". I used "VoiceAgentEval (OutboundEval)" with id voiceagenteval; consider swapping if the community settles on OutboundEval.

Modality unknowns left null rather than guessed: io for vcbbench (abstract does not state output modality) and for voiceagentevaloutboundeval (abstract says "LLMs" throughout and never states audio in/out, despite the voice-agent title — this is also the weakest evidence that any speech is actually involved). vocalbenchdf given only "speech in" for the same reason.

Near-duplicate topics (not duplicates): VoxRole vs AudioRole (both speech role-play, different resources); VoiceAgentBench vs VoiceAgentEval (both voice agents, different scopes: tool-calling vs outbound calling); FLEXI vs Full-Duplex-Bench-v2 (both full-duplex, distinct papers).

Category-cap note: several items had a 4th defensible tag I had to drop under the 3-max rule — vcbbench (multilingual, Chinese-only; captured in languages), voiceassistanteval (safety/robustness gaps mentioned), fullduplexbenchv2 (safety is one of its four task families), vocalbenchdf (fairness/inclusivity angle).

=====

24 items in, 24 entries out; 5 marked OUT.

OUT calls and why: audiospecialistheadsarealmslistening (steering method, uses existing MMAU), timestampgroundedspeechreasoning (RL training method, four existing benchmarks), loasrbench (pure ASR benchmark - explicit OUT bullet, even though the systems under test are SpeechLMs; the discovery pass also flagged it borderline), whospokewhatwhen (conversational ASR + new WER-family metric tcpSemER over existing datasets), mosbias (MOS annotation-bias analysis + gender-aware MOS predictor; speech-quality assessment, not a spoken-LLM benchmark).

Borderline IN calls a reviewer may want to re-check - all are papers where a method/model shares the headline with a genuinely new, released evaluation resource:
- ermminmaxgap: title leads with "Benchmarking and Mitigating"; the benchmark is a repurposing of MELD-ST and the named contribution ERM-MinMaxGAP is a training objective. Called IN because the abstract explicitly introduces a fairness benchmark for speech LLMs, but it could defensibly be OUT as a method paper. Note the "name" is the method's name - the benchmark itself is unnamed.
- sdiareward: primary contribution is a reward model; ESDR-Bench is the benchmark. Called IN because a reward model for spoken dialogue is an evaluation framework and general-purpose audio LLMs are the compared baselines. Listed under the composite name "SDiaReward / ESDR-Bench".
- spokenelyza: primary contribution is a DPO alignment recipe, but SpokenElyza is a named, native-expert-verified benchmark that will be released, so IN.
- multieventaudiogroundingsensitivityanalysis: an evaluation study rather than a packaged, named benchmark; the constructed query sets over AudioCapsV2 make it a diagnostic resource, so IN. Descriptive name kept (paper gives none).
- textprioraudioreliancediagnostic: no benchmark name in the paper - a diagnostic framework applied to existing benchmarks. Kept IN as a diagnostic/meta-evaluation resource; short descriptive name used.
- akb2000: partly probes text-only LLM backbones rather than LALMs, but the audio-grounded arm evaluates fine-tuned LALMs, so IN.
- omdbench: omni-modal (video+audio+text); included as an omni-model benchmark, but it is not audio-centric.

Other notes:
- "venue" filled only where the comment says accepted/presented (ERM-MinMaxGAP: INTERSPEECH 2026; multi-event: Interspeech 2026; PolyBench: INTERSPEECH 2026; SDiaReward: ACL 2026 Main; HalluAudio: ACL 2026). Items whose comment only says "submitted to" (MOS-Bias, timestamp-grounded, whospokewhatwhen, VIBE) were left null.
- HumDial-EIBench and HumDial-FDBench are two distinct papers from the same ICASSP 2026 HumDial Challenge (emotional-intelligence track vs full-duplex track) - related but not duplicates.
- EchoChain, Full-Duplex-Bench-v3 and HumDial-FDBench all cover full-duplex/interruption; they are separate benchmarks with different focuses (state-update reasoning, tool use under disfluency, dual-channel human corpus).
- VoxSafeBench says "bilingual coverage" without naming the two languages, so the language entry is deliberately vague rather than guessed.
- All arXiv ids copied verbatim; note they are 2603.*/2604.* (2026 numbering), which looks unusual but matches the input.

=====

24 items in, 24 out; 21 IN, 3 OUT.

OUT calls and why:
- speechllmasjudges (2510.14664): borderline. SpeechEval is a real 32,207-clip / 128,754-annotation resource, but the system under test is generated/synthetic speech quality (MOS-style scoring, pairwise comparison, deepfake detection), not a general-purpose speech/audio LM — and the headline artifact is the SQ-LLM judge model. Ruled OUT under the "pure TTS quality benchmark" + "model paper" bullets. Easy to flip to IN under `generation-quality` if the site wants judge/quality resources.
- afrispeechmultibench (2511.14255): title itself says "for African Accented English ASR". Transcription-centric, so OUT under the pure-ASR bullet, even though it does benchmark multimodal LLM-based speech systems and adds a hallucination-robustness vertical. The earlier pass already flagged it BORDERLINE.
- seabenchaudio (2511.01670): the paper is the SeaLLMs-Audio model; SeaBench-Audio is introduced in the last two sentences to automate its evaluation. OUT under "mainly proposes a model". If the site wants SEA-language coverage, SeaBench-Audio would be the entry, categories would be multilingual + holistic.

Three IN items are evaluation-methodology / diagnostic studies rather than newly released datasets — hearingtheorder (2510.00628), robustnessassessment (2510.04584), whensilencematters (2510.00626). None ships a named benchmark corpus; they diagnose LALM evaluation reliability on existing benchmarks and propose protocols. I kept all three IN under "evaluation framework / diagnostic", categorized as `robustness`. They are near-duplicates of each other in topic (2510.00628 and 2510.04584 both study MCQA option-order sensitivity, posted five days apart by different groups) — worth cross-linking on the site rather than listing as unrelated.

emis (2510.25054) and listen (2510.10444) are also strongly overlapping: both are cue-conflict emotion probes concluding that LALMs lean on lexical semantics over acoustics. Kept separate since both release distinct resources.

paras2s (2511.08723) is half benchmark (ParaS2SBench) half RL method (ParaS2SAlign); I used the benchmark as the entry name and marked IN because benchmarking is named first in the title and the judge is a released component.

spokendialogsum (2512.14687) is the weakest IN — it is framed as a "corpus" and is TTS-synthesized from DialogSum, so it sits close to the "plain component corpus" OUT bullet. Kept IN because it is new, explicitly aimed at audio LLMs, and reports audio-LLM vs cascaded baselines.

Venue field: I filled it only where the comment says accepted/to appear (Interspeech 2026, ICASSP 2026, ACL 2026 Findings, ICLR 2026, AAAI 2026, ACL 2026, IJCNLP-AACL 2025). Left null for the several "Submitted to ICASSP 2026 / Interspeech 2026" comments, since submission is not a venue — flag if you want those recorded instead.

vocalbenchzh (2511.08230): the arXiv comment says it will serve as an extension of the earlier VocalBench paper (arXiv:2505.15727), and the discovery pass noted the posting was withdrawn on 17 Nov 2025 and folded back into that paper. Nothing in the abstract confirms withdrawal, so I did not encode it, but the site should probably merge or cross-reference it with VocalBench.

Category-taxonomy notes: MAC-SLU has no clean fit (intent extraction / SLU is not a listed category) — I used `domain` + `voice-agent` on the grounds that it is task-oriented dialog for downstream execution. MULTI-Bench's output modality is not stated in the abstract, so io says "response modality unspecified".

=====

24 items in, 24 entries out; 4 marked OUT (aqascore, mclp, nowyouhearme, prism).

Borderline / judgment calls:
- nowyouhearme (2601.23255): ruled OUT as an attack-method paper — it designs a narrative TTS jailbreak and reports a 98.26% success rate on models including Gemini 2.0 Flash, but the primary contribution is the attack, not a released evaluation suite. If the collection wants audio-jailbreak evaluations as safety entries, this is the one to reconsider (would be ["safety","robustness"]).
- prism (2601.14046): ruled OUT as a phone-recognition (ASR-style) benchmark; systems under test are PR models/encoders, LALMs appear only as a comparison point ("specialized PR models still outperform Large Audio Language Models"). Would be ["multilingual","domain"] if reclassified IN.
- aqascore (2601.14728): the audio LLM is the judge and the text-to-audio generator is the system under test, so OUT under the pure audio-generation-metric rule.
- mclp (2601.22661): metric + RL reward for role-play TTS, plus a dataset and improved model. OUT under the pure-TTS rule.
- phostream (2601.22575): kept IN because the system under test is an omnimodal assistant and the headline finding is a timing failure ("when to speak"), but it is as much a streaming video benchmark as an audio one.
- speechcmmluspeechhsk: the input key names two sub-benchmarks; the paper itself is UltraEval-Audio, so I used that as the canonical name. It is a framework/harness that also contributes two new Chinese benchmarks, hence "holistic" plus "multilingual".
- humdialchallenge and interspeech2026audioreasoningchallenge are shared-task summary papers rather than standalone datasets, but both introduce evaluation resources/protocols (HumDial dataset and tracks; MMAR-Rubrics), so both are IN.

Data oddity (not a classification issue): the last entry has arxiv_id 2603.13262 while arxiv_date is "2026-02" and date_full is 2026-02-25 — id month and date disagree in the source file. I copied the id verbatim as instructed.

Metrics/sizes/languages were left empty wherever the abstract did not state them (HumDial's "sizable dataset", AGL1K's language coverage; VoxPrivacy's two languages are unnamed, recorded as "bilingual (languages not stated)").

=====

24 items in, 24 out; nothing skipped or added.

Six marked OUT, four of them judgement calls worth a second look:
- dollmdecoderslistenfairly (2604.21276) and afrivoxv2 (2605.03590): both are recognition-centric (WER/insertion rate on existing corpora), so they fall under the "pure ASR benchmark" OUT bullet even though LLM-decoder ASR systems are the subject. If the site wants ASR-fairness resources, the first would be fairness+robustness and the second multilingual+domain.
- nvvsuperbench (2604.16211) and ceaeval (2605.09413): both evaluate expressive speech GENERATION. NVV-SuperBench benchmarks 15 TTS-style speech generation systems (prompt- and tag-based control); CEAEval builds a Mandarin annotated dataset plus a trained evaluator model. I applied the "pure TTS benchmark" OUT bullet to both for consistency, but the taxonomy does contain a generation-quality category, so a reviewer could reasonably flip both to IN (NVV-SuperBench: generation-quality + paralinguistics; CEAEval: generation-quality + paralinguistics + multilingual/Mandarin).
- audiojailbreaktaxonomycostawareevaluation (2605.30031): self-described as a taxonomy over prior work plus a controlled re-evaluation; no new dataset, so OUT under the survey bullet. It does propose a cost-aware evaluation protocol, so it is arguable.
- duplexslabench (2605.20755): clearly a model paper (DuplexSLA) with the benchmark constructed to evaluate it; OUT under "benchmark is incidental". If included it would be interactivity + voice-agent.

Two model+benchmark papers I kept IN because the benchmark is a named headline contribution: listeningwithtime (LAT-Bench, "the first human-verified benchmark supporting audio up to 30 minutes") and finegrainedmultidimensional (FMSU-Bench, one of three declared pillars). Same reasoning applied to audiosafetybench (AudioSafetyBench named as the first policy-based audio safety benchmark, alongside the AudioGuard guardrail) and voxparadox (benchmark first, PCLM/DPO mitigation second). These are the mirror-image of the DuplexSLA call, so if the parent tightens the model-paper rule they should be revisited together.

Name corrections vs the discovery pass:
- "HUMANS (efficient LAM evaluation)" -> HUMANS.
- "Listening with Time" -> LAT-Bench (the benchmark's actual name; LAT-Chronicle is the dataset, LAT-Audio the model).
- "Multilingual distractor / selective auditory attention evaluation" -> MUSA (the alias was right).
- "Fine-Grained Multi-Dimensional Speech Understanding Benchmark" -> FMSU-Bench.
- "NVV-SuperBench (a.k.a. NVBench)" -> the abstract only ever says NVV-SuperBench; the "NVBench" alias is unsupported (and NVBench is an unrelated NL2VIS benchmark).
- rolejudge: RoleJudge is the framework, RoleChat the dataset.
- kvoicebench: kept the three-way name since the paper releases three separate benchmarks under one paper; slug uses kvoicebench.

Sizes/languages/metrics filled only where the abstract states them. audiosafetybench's "10K+ instances / 17 languages / 50+ speakers" and afrispeechsemantics' language list came from discovery notes, not the abstract, so I left them out. VoiceGiraffe says "languages" without naming any. arXiv ids copied verbatim, including the ones whose id month (2606.x) is ahead of the recorded arxiv_date (2026-05) — I did not alter them.

=====

24 items in, 24 out. 18 IN, 6 OUT.

Borderline calls the parent may want to override:
- speechdx (SpeechDx): marked OUT only because the abstract says it evaluates "12 state-of-the-art audio encoders", i.e. representation models, not LALMs/SLMs. If the site wants domain-specific (clinical) speech benchmarks regardless of whether the SUT is an LLM, flip it to IN with categories ["domain","holistic"].
- mseb (MSEB): the paper does NOT introduce MSEB — MSEB already existed for encoders; this paper contributes an LLM benchmarking study on it. Kept IN because MSEB is a named benchmark and the systems under test here are audio-native LLMs (Gemini/GPT). If the rule is strictly "introduces a new resource", this becomes OUT.
- indiccontexteval (IndicContextEval): the underlying task is transcription, which brushes against the "pure ASR benchmark" exclusion, but the contribution is a 7-level diagnostic of whether AudioLLMs use supplied textual context vs parametric knowledge, so I kept it IN. Note the category "audio-grounding" was deliberately NOT used: it probes use of TEXT context, not use of audio.
- prosodicunderuseprobeladder: mostly a mechanistic-interpretability paper (probes + causal interventions) with matched-content contrast sets rather than a released benchmark; kept IN as a diagnostic framework. No official name in the paper — descriptive name used.
- anyaudiojudge: dual contribution (benchmark + trained evaluator model with SFT/GRPO). Kept IN because "AnyAudio-Judge Bench" (7,920 samples) is explicitly a benchmark. Its sibling jastin was ruled OUT because that one introduces only a trained evaluator model and no dataset — the two were judged on this exact distinction.
- gigaspeechbench: high-quality multilingual resource but scored on ASR/AST only, so it falls under the pure-ASR exclusion.

Name changes from the discovery pass:
- "From Sounds to Scenes" -> CASU (the abstract calls the resource "the CASU benchmark"); id "casu".
- "Japanese dialect robustness evaluation (no named benchmark)" -> OUT, no name assigned.
- "Real-Time Voice AI Hears but Does Not Listen" -> descriptive name "Voice AI Emotional Intelligence Gap" (the paper coins "the emotional intelligence gap of voice AI"); no formal benchmark name exists.
- "MSEB (LLM benchmarking)" -> "MSEB".

arXiv id / date inconsistencies in the input (ids copied verbatim, unaltered): instructfd has arxiv_id 2607.20460 but arxiv_date 2026-05; prosodicunderuseprobeladder has arxiv_id 2608.19211 but arxiv_date 2026-06. Worth a sanity check upstream.

Sizes, language counts and venues were taken only from the abstract/comment fields. Several agent_notes carried extra detail not present in the abstract (e.g. GlobeAudio's specific six language/locale pairs, SpeechJBB's "nine LALMs", IndicContextEval's specific language list) — I did not use those.

=====

24 items in, 24 entries out. Two OUT: spokenlanguageadherenceevaluation (2606.17281, method paper for ASR output-language adherence) and textbiasconflictanalysisinaudiollms (2606.18924, mechanistic interpretability plus back-patching intervention, no benchmark).

Borderline calls worth a second look:
- steb (2606.25529): a speech-to-speech TRANSLATION expressiveness benchmark. Kept IN because speech LLMs are among the six systems evaluated and the axes are paralinguistic/generation-quality, but if the site excludes task-specific S2ST/TTS suites it should flip to OUT.
- lalmaudiojudgereliabilityassessment (2607.07985) and lalmjudgeshortcutaudit (2607.13477): both are META-evaluations of LALMs used as judges rather than benchmarks of speech-LLM capability. I kept both IN under "evaluation framework"; the shortcut audit is the stronger IN (it is a genuine audio-grounding diagnostic), the reliability assessment is the weaker one (a validation study of one proprietary judge family, unclear whether the 209-session set is released).
- finegrainedintentbenchmark (2608.03054): renamed to ParaIntent, the actual benchmark name from the abstract. Co-primary with the ALPO RL method; kept IN because ParaIntent is presented as filling a benchmark gap.
- arena (2608.15578): an attack/red-teaming framework rather than a static benchmark; kept IN because the safety category explicitly covers audio adversarial attacks.
- slt2026smartglasseschallenge (2608.12034): partly a speaker-attributed ASR shared task, kept IN because the SLU track is evaluated with audio-language models.
- inspire (2608.16203): speech RETRIEVAL, not generation or QA; kept IN because LALMs are one of the four evaluated paradigms and instructions define relevance.

Names changed from the discovery pass: "Fine-Grained Intent Benchmark" to ParaIntent; "EmoSBench (EmoS framework)" to EmoSBench (EmoS is the evaluator model, not the benchmark); "Semantic-aware fairness estimation for LALMs" to "Semantic-Aware Bias Estimation for LALMs"; UniVerse to UniVerseBench (UniVerse is the whole solution, UniVerseBench is the benchmark).

Venue left null where the comment only says "Submitted to SLT 2026" (m3duplexbench, soundsymbolismperceptualalignmenteval) or "Under review" (escucha), since submission is not acceptance.

emosbench: the abstract calls EmoDialogue bilingual but does not say which languages, and that is the training set, not the benchmark, so languages is left empty.

stancebench and spearbench are both built on the Seamless Interaction corpus and both score interpersonal stance; they overlap and may want cross-linking on the site. vamosbench and duplexworld also overlap heavily (end-to-end voice-agent task completion).