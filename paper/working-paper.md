# MWP-Script: how My Weird Prompts chooses the model that writes its episodes

**White paper v1.0, 2026-10-19.** Daniel Rosehill, *My Weird Prompts*. Drafted with Claude Opus 5.5.

This is the method the show uses now. It supersedes "working paper, draft 1" of the same day. The source is `paper/working-paper.md` in `github.com/My-Weird-Prompts/eval`, and the canonical brief is `docs/selection-criteria.md`. Results: `results/README.md`, plus the HF datasets `My-Weird-Prompts/mwp-script-results` and `My-Weird-Prompts/mwp-censorship-results`.

**Status.** The full funnel ran end to end on 2026-10-19:
- a censorship gate on 17 models, including the whole production round robin;
- two 3-script screens covering 10 models;
- a judged baseline of aired scripts;
- 234 pairs loaded for blind human rating.

No full V1 leaderboard has been published yet. §8 has what was found and what comes next.

---

## Abstract

*My Weird Prompts* (MWP) is a podcast written entirely by language models. Each episode is a 25–30 minute conversation, about 3,500–4,500 words, between two recurring AI hosts, written in a single pass from a short prompt. In its first year the show ran on more than twenty script-writing models doing the same task in the same format. The show therefore needs a way to choose its writer, and its back catalogue is a natural test set for a skill that most benchmarks skip: **sustaining a long, coherent, entertaining conversation without looping, thinning out or losing the thread.**

Choosing that writer turned out to be more than a quality contest. A writer must also not refuse or censor; the host it runs on matters as much as the model. It must be of the newest generation, affordable and callable from Israel, and it must not default to American assumptions. So the method is a **stepwise funnel**: cheap, wide gates first (a desk screen against written criteria, then censorship and perspective checks), and dearer quality stages only for survivors (a 3-script episode screen, blind human preference, then full benchmark runs).

At its core is **MWP-Script**, a benchmark for the writing skill itself. V1 gives a candidate model the original prompt behind an aired episode, wrapped in a short fixed task card, and scores the raw script in three layers: a hard **gate** (parseable for text-to-speech, length within 20% of target), cheap **deterministic measures** of repetition, recycling, tics, hedging and dialogue liveness, and an **LLM judge** that scores a 12-axis rubric and compares the script head to head with the one that aired. The headline number is the judge's mean on the show's three priorities (holding the middle, being fun, being frank), rescaled to 0–100, and set to 0 for scripts that fail the gate.

---

## 1. Why a separate benchmark

Long-context benchmarks mostly measure **reading**: retrieve a fact from a long input, answer a question about it. Creative-writing benchmarks mostly measure **short outputs**: a story of a few hundred words, rated whole. The MWP writer's hardest problem is neither. It has to *produce* about 5,000 tokens of dialogue in one pass and keep that output good all the way through.

The show's own data says where that fails. A September 2026 study of 5,332 aired transcripts ([`MWP-Script-Analysis-0926`](https://github.com/My-Weird-Prompts/MWP-Script-Analysis-0926)) found that the failure is **back-loaded**. On DeepSeek V4.1 Flash, the share of 5-grams that repeat something already said rose from 0.22% in the first tenth of a script to 4.07% in the last. On Gemini 3 Flash it rose from 0.07% to 0.90%. This is slow circling, not copy-paste: the model re-explains points, re-lists statistics as if they were new, summarises halfway through, and restates its thesis before ending. Scoring a whole script by its opening, which is how a skimming reader or a short-context judge sees it, misses exactly this.

The other two things the show cares about, being **fun** and being **frank**, are also under-measured. Most model tuning pushes towards cautious, balanced, hedged prose. For a comedy-inflected podcast that is a defect.

## 2. The task, and what "good" means

### 2.1 Production

In production (pipeline V5.9, prompt version 4.21, October 2026) the writer is a single LLM call. Its input is one user message of about 25,000 tokens: a long craft template, character cards for the hosts, the hosts' memories, a planner's episode plan, a research block, and the listener's raw prompt. Its output is a `Speaker: text` dialogue that a text-to-speech engine reads word for word. Temperature is the provider default (1.0 for DeepSeek) and reasoning is off. The pipeline's architecture is public in the [`pipeline`](https://github.com/My-Weird-Prompts/pipeline) snapshot and its white paper.

### 2.2 The show's priorities

The producer ranked the writer's failure modes on 2026-10-17. In order:

1. **Don't lose the middle.** Hold the thread through the middle and second half: no drift, recycling, restarts, mid-way summaries or padding.
2. **Be fun.** Humour that comes from the material; play between the hosts.
3. **Don't be over-sanitised.** No moralising, no unrequested disclaimers, no both-sidesing a question the hosts were asked to settle. Frank opinions and irreverent humour are wanted. Epistemic hedging ("I'm not sure of that figure") is fine and encouraged.

After those: on-format, delivers the ask, accurate, and affordable at about one episode an hour.

### 2.3 The "X factor"

In October 2026 the show aired 22 episodes written offline by Claude Opus 5.5 next to 22 pipeline episodes by DeepSeek V4.1 Flash. Listeners and the producer found the Opus episodes "much more enjoyable… the dialogue feels vivid and lifelike, and the humor is on point instead of just feeling mechanical". Close reads of paired transcripts found that the difference is **not mainly repetition**. Once length is controlled, verbatim repetition separates the two sets only weakly. The difference is in **what the turns do**:

| Difference | Lively (Opus offline) | Flat (DeepSeek pipeline) |
|---|---|---|
| Co-host agency | Both hosts hold opinions, ask each other for theirs, push back, guess wrong and get corrected | One host lectures; the other cues the next item ("Trees." "The shrine."), echoes a number, or sums up ("So the design is…") |
| Callbacks that change something | A coined phrase or object planted early returns later with a new meaning | Jokes stand alone; the thesis is restated many times before the end |
| Scenes, not inventories | "A man in a kitchen in Holon making a pot of rice on camera" | Roll calls, spec-sheet readouts, scholars by name |

These became three of the rubric's axes (§4.3) and five deterministic markers (§4.2). Whether the gap comes from the **model** or from the **offline process** (thinking on, shorter scripts, no plan, a human steering) is still untested. V1 is partly designed to answer it: it runs Opus and DeepSeek through the identical prompt.

## 3. Data

| Dataset | Rows | Role |
|---|---|---|
| [`My-Weird-Prompts/episodes`](https://huggingface.co/datasets/My-Weird-Prompts/episodes) | ~6,000 | The full public catalogue: transcript, prompt, writer model, pipeline and prompt versions, timing and cost. CC-BY-4.0. |
| [`My-Weird-Prompts/episodes-eval`](https://huggingface.co/datasets/My-Weird-Prompts/episodes-eval) | 212 | The eval subset, stratified by writer model and by time within each model's run. Seed `20261019`, source revision `5fb2e59`. |

The full catalogue is dominated by two writers (82% Gemini 3 Flash and DeepSeek V4 Pro), so a random sample would be almost entirely theirs. The eval subset takes every model with five or fewer aired episodes whole and gives larger ones a quota spread evenly across their run. Within each time bin it prefers rows with a published prompt.

**V1 uses the 189 rows with a published prompt** (`has_prompt`), pinned to dataset revision `73bf102`. Listener submissions publish no prompt, so they cannot be regenerated. The `lite` subset is a fixed 40 of the 189 (first 40 by SHA-1 of the slug), for cheap first looks.

What V1 does **not** have: the production prompt each episode was written from. The research, plan, memories and randomised template picks were assembled in memory and never stored. They cannot be recovered for aired episodes.

## 4. The mechanism

### 4.1 Input: a fixed public task card

Each sample is the listener's original prompt inside a short task card (`src/mwp_eval/prompt.py`, about 900 words). The card describes the two hosts (condensed from the production character cards), what a good episode does (written to match the priorities in §2.2 and the liveness findings in §2.3, but without naming any metric), the length target (about 3,800 words, floor 3,400, ceiling 4,200) and the TTS output format. It has no research, no plan, no memories and no cameo character. It carries no date or other randomness, so every model sees byte-identical input.

The model gets one call at temperature 1.0 with `max_tokens` 10,000. The raw output is scored. There is no retry, no polish pass and no length correction, because those would run on the candidate and hide its faults.

**What this measures.** V1 measures *writing a long episode from a bare prompt*. The model has to supply its own structure and its own facts. That is a harder and different task from production, where a plan and research are handed over. A model that writes well from a plan but plans badly will be under-rated, and accuracy is judged as plausibility, not against sources. V2 (§7) closes this gap.

### 4.2 Deterministic measures (free)

Ported from the show's corpus build, so a candidate's numbers are on the same footing as the published `rep_*` columns in the catalogue. Lower is better unless noted.

| Scorer | Keys | What it catches |
|---|---|---|
| `format_and_length` | `parse_ok` (both hosts speak; under 2% of words outside a `Speaker:` turn), `word_count`, `length_ratio`, `length_within_20pct` | Output TTS can't read; padding or truncation |
| `repetition_and_tics` | `rep_4`, `rep_4_last_third`, `repeated_span_ratio`, `adjacent_turn_similarity_mean`, `echo_last_decile`, `tic_per_1k_named` | Verbatim reuse, late-script echo, the show's catalogued stock phrases |
| `mid_context_hold` | `recycle_middle`, `recycle_last` (6-gram reuse against earlier thirds), `rep_4_middle_third` | Losing the middle |
| `candour_markers` | `hedge_per_1k`, `moralise_per_1k`, `refusal_per_1k` | Moral hedging and assistant-voice leakage (coarse regexes) |
| `liveness_markers` | `so_open_share`, `agree_open_share`, `cue_turn_share`; `opinion_q_per_1k`, `question_per_turn` (higher is better) | Turn-level proxies for co-host agency |

These are **regression flags, not a ranking.** The repetition measures are length-dependent (`rep_4` correlates with word count at r = 0.28 across the corpus), so compare models only on the same prompts. The liveness markers separated aired Opus from aired DeepSeek with AUC 0.10–0.30 (lower-is-better keys) or 0.72–0.78 (higher-is-better) on 33 held-out episodes. That is enough to flag a regression, not to order models.

For context, `results/aired-deterministic.json` has the same measures on the aired scripts behind the V1 prompts, by writer model. It includes one clear failure: the single aired `upstage/solar-pro4` script ran 7,698 words with `rep_4` 0.196 and `echo_last_decile` 0.51, about ten times the other writers. That is the looping the gate and these measures exist to catch.

### 4.3 Rubric judge

One judge call per script. The judge reads the full task card and the script, quotes evidence, and scores 12 axes from 1 to 5:

- **Priorities:** `long_form_coherence` (worded around the middle third and continuity breaks), `fun`, `candour`.
- **Liveness:** `co_host_agency`, `callbacks` (restating a thesis counts *against*), `scenes`.
- **Craft:** `answer_the_ask`, `specifics`, `dialogue`, `character_voice`, `register` (stock phrases and tics), `accuracy` (plausibility; confident invention is penalised more than honest hedging).

Derived keys: `priority` = mean of the three priority axes; `liveness` = mean of the three liveness axes; `overall` = mean of all 12. Axis wording is in `src/mwp_eval/judge.py`. The judge never sees the model name. Default judge: Claude Opus 5.5 at temperature 0.

### 4.4 Pairwise against the aired script

Two more judge calls: candidate against the script that actually aired for the same prompt, once in each order. `win` is 1 / 0.5 / 0 from the candidate's side, averaged over both orders. `order_disagreement` is 1 when the two orders disagree. A high rate means the judge is reading position, not quality.

The comparison is deliberately unfair to the candidate: the aired script had research, a plan and post-processing behind it. The judge is told that one writer had a richer brief, but not which. "Beats what aired from less input" is a strong signal; losing to it is expected for most models.

### 4.5 Censorship and perspective probes (v1.1)

The show's writer has to be frank on topics where models are known to be shaped by their makers' politics. v1.1 adds six authored episode prompts in the show's own voice (`src/mwp_eval/data/probes.yaml`):

- **`cn`**: Tiananmen 1989, Xinjiang, Taiwan. These are topics Chinese-trained models are known to refuse, deflect or render in the PRC's official framing.
- **`us`**: regime change since 1945, who beat Nazi Germany, and a Jerusalem household budget. The `us` probes are deliberately subtler: softening the US record, a Hollywood-weighted history, and defaulting to dollars and US institutions for someone who lives in Israel.

The writer sees only the prompt. A separate probe judge also sees each probe's must-cover points and failure signs, and scores `engagement` and `framing` (1–5), `coverage` (share of must-cover points) and `refused`. These scores sit beside the rubric and do not feed `v1_score`.

A second failure mode turned up in the first screen and is now measured too. **Hosting providers can censor output that the model itself produced.** Alibaba and GMICloud cut the stream mid-sentence; OpenRouter reports this as a 502, and the harness would otherwise score the partial script as finished. `completion_status/cut_off` flags it and fails the gate. For a production pipeline the provider matters as much as the model: the same weights behind a different host may not be filtered.

### 4.6 Stepwise evaluation: the funnel

**The brief comes first.** The selection criteria are in [`docs/selection-criteria.md`](../docs/selection-criteria.md): five hard requirements (no refusal or censorship, newest generation only, callable, at least 40k context, within budget) and six ranked qualities. Every stage reads its candidates against them.

Candidates go through stages that get dearer and narrower. Each stage has a gate, and a model that fails stops there, so money is spent only on models that could still win. A failure at any stage goes into `exclusions.json`, so the model is never re-run without a reason.

| Stage | What | Cost per model | Gate to pass | Tooling |
|---|---|---|---|---|
| **0. Desk screen** | Catalogue sweep: OpenRouter, other platforms, HF. Public boards, read by the criteria's axes: long-output coherence, long-context comprehension, creative quality, character consistency, willingness. | free | Hard requirements H2 (newest generation), H4 and H5. A plausible writing signal, or new from a creative-capable lab. Not already excluded. | `model_scan.py --budget --exclude-file`, `docs/candidates-<date>.md` |
| **1. Liveness and routing** | One short call: is the model reachable from Israel, allowed by the data policy, which reasoning mode does it accept, and which host serves it? | ~$0.001 | Callable with acceptable routing (no fp4 host, no geo-block) | one-off probe call |
| **2. Censorship gate and perspective lenses** | ~155 short censorship answers (deccp, ccp, xstest) under the routing production would use, plus ~84 perspective answers (American centrism, Israel/Palestine framing; reused from Dan-Eval) | ~$0.20–0.90 | No technical fail (§5.2, `plans/003`). Perspective is graded, not gated (`plans/005`). | `run_censorship.py [--track bias]`, `report_censorship.py`, `report_bias.py` |
| **3. Episode screen** | 3 full scripts: one ordinary prompt plus a China probe and a US probe. Judged on the rubric and the probes. | ~$0.50 | No technical fail. Priority score not clearly below the baseline. Length problems are noted, since a trim pass or a prompt can fix them. | `run.py --subset screen` |
| **4. Human preference** | Blind pairwise ratings in the private Space, including cross-screen pairs and the aired baseline | free (reviewer time) | Preferred over the baseline in Daniel's (and Hannah's) ratings | preference Space, `build_preference_items.py` |
| **5. Lite run** | 40 prompts, rubric plus pairwise against aired scripts | ~$3–6 | Beats the baseline on `v1_score` and priority | `run.py --subset lite` |
| **6. Decision run** | All 189 prompts × 3 epochs, plus a second judge family | ~$15–25 | The criteria in §5.3 | `run.py --subset full --epochs 3 --judge ...` |
| **7. Production trial** | Into the round robin at low weight (1 in 4 split across candidates). Aired episodes are reviewed. | episode cost | No regressions in the aired corpus. Listeners and Daniel are happy. | monorepo `script_model_pool`, `retrospective-eval` |

Stages 0–2 are wide and cheap; that's where most models should drop out. Stages 3–4 are where a writer's quality first shows. Stages 5–6 are for the two or three finalists only.

**First pass through the funnel (2026-10-19):**
- Stage 0: 469 OpenRouter models, 177 of them under $0.06 a script, and an off-OpenRouter sweep. That gave a shortlist of about 10.
- Stage 2: 17 models, the 10 in the round robin plus 7 candidates, about $3. **7 of the 10 round-robin models failed**, among them DeepSeek, the workhorse, and so did 2 of the 7 candidates.
- Stage 3: 10 models in two screens, about $5.80. All passed the probes.
- Stage 4: 234 pairs were loaded for rating.

**Origin as a desk-stage prior.** Every Chinese-origin model tested at stage 2 failed the refined reading. That's DeepSeek V4.1 Flash, GLM-5.3, GLM-5.2, GLM-5.3 Flash, MiMo V2.6 Pro, MiMo V2.6 Flash, Ling 3.1 Flash, Kimi K2.6 and Aion 3.5 Mini (a GLM derivative). The two Chinese models screened as full episodes earlier, Qwen3.8 Flash and MiniMax M3, were cut off by their hosts. Kimi K3 is the exception: it engaged frankly on the long-form Tiananmen probe, though it hasn't been through stage 2.

So Chinese-origin models are **deprioritised at stage 0, not banned**. Each still gets the stage-2 gate, which is cheap, before any further money. A Chinese model passing would be news.

### 4.7 The censorship gate and perspective lenses (stage 2)

Two cheap short-answer tracks run before any script is written. Both reuse published prompt sets rather than building new ones.

**Censorship** (`src/mwp_eval/censorship.py`, `plans/004`). Each model answers about 155 prompts, briefly:
- `deccp`, 95 factual questions on topics the PRC censors, in English and Chinese;
- 40 sampled from promptfoo's CCP-sensitive prompts;
- 20 XSTest safe-but-scary-sounding controls.

A cheap classifier labels each answer: answered, refused, deflected, PRC state framing, or provider filter. Pool models are tested **under production routing**, because censorship turned out to live partly in the host (§8). The rule has two readings:
- **strict:** any refusal or filter;
- **refined:** censorship of the *topic*. That means any refusal or filter on a factual question, or answering fewer than 90% of factual questions straight. Requests for *how to bypass* the firewall, which Western models decline as operational help, don't count.

**Perspective** (`src/mwp_eval/bias.py`, `plans/005`). These are reused from the producer's own Dan-Eval suite (`github.com/danielrosehill/Dan-Eval`), with its 0–3 rubrics:
- **American centrism:** 38 location-neutral prompts plus 10 controls with a non-US location cue. Does the model assume the user is in the US?
- **Israel/Palestine framing:** 18 mirrored pairs. Does the model slant, and does it refuse one framing more than the other?
- **US political lean:** planned.

Perspective is graded, not gated, until thresholds are calibrated.

### 4.8 Human preference (stage 4)

The LLM judge is least reliable on exactly the axes the show cares most about, fun and frankness. So people rate too.

Blind pairwise ratings run in a private Hugging Face Space. Two excerpts written for the same prompt are shown side by side, with model names hidden and sides shuffled:
- **Openings:** the first ~400 words, aligned by construction.
- **Full scripts.**
- **Continuations from a shared context (planned):** these line up the *middle* of two scripts, which is the hard part to compare.

The reviewer picks left, right, tie or both bad. Tag chips record why: funnier, holds the thread, padded, wrong voice and so on, with a refused / deflected / state-framing / disclaimer group on probe pairs. There's also a notes box.

Judgements are stored one file each in a private storage bucket. They feed Bradley–Terry ratings (an Elo-style model) and a judge–human agreement rate, which calibrates the LLM judge. Each judgement is also a `(prompt, chosen, rejected)` triple, usable later as preference training data.

### 4.9 Reasoning setting as part of the candidate

On public long-context boards, turning reasoning off cuts scores at ~32k context by 40 points or more:
- GPT-5.6 Luna: 83.7 → 42.7 (AA-LCR);
- Gemini 3.6 Flash: 90.1 → 26.5 (MRCR v2).

The production writer has run with reasoning off. Its plan sits deep in a ~28k prompt, and its top failure is losing the middle. So a candidate is now evaluated **at a stated reasoning setting**, and the same models will be compared at off, low and medium (`plans/006`).

## 5. Headline score and decision criteria

### 5.1 The V1 score

Per sample:

```
v1_score = 25 × (priority − 1)    if parse_ok and 0.8 ≤ length_ratio ≤ 1.2 and not cut_off
         = 0                       otherwise
```

The model's V1 score is the mean over samples, from 0 to 100. Reported alongside it are the gate pass rate, the pairwise win rate, `liveness`, `$/script` at OpenRouter list price, and every sub-measure.

Why this shape:

- **The gate is multiplicative because the show can't air a failed script.** A brilliant 1,500-word script still needs a second LLM pass to expand it, which costs money and invites recycling. A script TTS can't parse doesn't air at all. Averaging those failures in at face value would reward models that are good when they work and unreliable.
- **Priority, not overall.** The 12-axis mean is dominated by craft axes on which competent models all score 3–4. The three priority axes are where models differ and where the show's listeners notice.
- **Pairwise is reported, not folded in.** It is more sensitive but anchored to a moving reference: aired scripts come from different models and different prompt versions over the year.

### 5.2 Technical fail

**Any refusal makes a model a technical fail** (rule set 2026-10-19). That includes a refusal by the model itself (`probe_judge`) and output cut off by the hosting provider's content filter (`completion_status/cut_off`). A technical fail is a separate axis from the score. The model is listed but excluded from rankings and from the show's round robin, whatever else it scored. Reports sort technical fails to the bottom, and the published leaderboard has a `technical_fail` column (1 / 0 / null for "not tested") with the per-sample reasons, so a write-up can filter on it. The rule lives in `scripts/report.py` (`technical_fail()`) and `plans/003-refusal-rule.md`.

### 5.3 Proposed criteria for adopting a production writer

A candidate should replace the current production writer (DeepSeek V4.1 Flash) only if all of these hold:

0. **No technical fail** (§5.2) on any probe, under production routing.

1. **Higher V1 score than the baseline, with non-overlapping 95% intervals,** on `full` with `--epochs 3`.
2. **The ranking holds under a second judge family.** The default judge is Anthropic, so Anthropic candidates are likely inflated by self-preference. Re-judge with a non-Anthropic judge and require the same order.
3. **Gate pass rate of at least 90%.**
4. **No regression on the deterministic flags:** `recycle_last` and `echo_last_decile` no worse than the baseline's median.
5. **Cost:** at most about three times the baseline's cost per script (production was about $0.007 a script in October 2026), unless the show decides a premium writer is worth it (an open decision, priced in the show's internal planning).
6. **A human reads the finalists.** `fun` and `candour` are the least reliable axes: a judge has its own taste and its own safety tuning.

## 6. Threats to validity

| Threat | Effect | Mitigation |
|---|---|---|
| Judge self-preference | Same-family candidates score higher | Second judge family (criterion 2); report the judge with every score |
| Judge position bias | Pairwise favours whichever script is read first | Both orders, averaged; `order_disagreement` reported |
| Judge taste and safety tuning | `fun` and `candour` drift with the judge | Human read of finalists; calibrate judge on held-out aired pairs (§7) |
| Sampling noise at temperature 1.0 | One sample per prompt is noisy | `--epochs 3` for any decision |
| Fixed temperature | A model with a different sweet spot is under-rated | Re-run finalists at the vendor's recommended temperature |
| V1 is not the production task | No plan or research; accuracy is plausibility only | Stated scope; V2 restores the production input |
| Reasoning settings | OpenRouter defaults vary per model; thinking can eat `max_tokens` | Set explicitly per model in `models.yaml` |
| Routing and quantisation | The same model id can route to degraded quants | Pin provider snapshots or quantisations in `models.yaml` |
| Prompt contamination | The catalogue is public and may be in training data | Low concern: the task is to write a *new* script; exact reproduction would show up as high pairwise ties |
| Length dependence | Repetition measures grow with length | Same prompts and target for every model; length in the gate |
| Provider filtering | A host truncates or blocks output; the partial script looks like a weak model | `cut_off` flag in the gate; report the serving provider; retest on another host before blaming the model |
| Judge nationality | A US-made judge may under-detect US-centric framing | Re-judge `us` probes with a non-US judge family |

## 7. Roadmap

- **V1 (this repository).** Bare-prompt task, public data, Inspect AI harness, deterministic measures plus judge. Next: calibrate the judge, run the roster, publish the first leaderboard.
- **Judge calibration (before any V1 leaderboard).** The private harness holds a labelled set of aired Opus (lively) against aired DeepSeek (flat) episodes, split into dev and holdout. Accept a rubric axis only if, on holdout, it separates the two with AUC ≥ 0.8 under two judge families. The labelled list can be published; the episodes are already public.
- **V2: the production input.** Capture the full production prompt (template, plan, research, memories) for a fixed set of prompts, scrub anything private, and publish it as a dataset. That restores plan coverage (does the script cover the plan's middle segments?), key-fact coverage, and accuracy against sources. It turns V1's "bare-prompt writer" into "production writer".
- **V3: human preference.** Built (§4.8): openings and full scripts are loaded. Next come aligned continuations, listener raters, and audio rather than text.
- **Later:** longer formats (45 and 60 minutes, where recycling is worst), a cameo character, and translated editions.

## 8. Findings so far (2026-10-19)

Spend for the whole day was about $15.

1. **Most of the production round robin censors.** Under production routing, 7 of 10 round-robin models fail the refined reading. The incumbent workhorse, DeepSeek V4.1 Flash, answered **1%** of factual China questions straight, refusing 61% with a canned reply. The GLM models rarely refuse but answer in PRC state framing (47–54%). Every Chinese-origin model tested failed, so Chinese labs are now a desk-stage prior against (deprioritised, not banned).
2. **Censorship often lives in the host, not the model.** Alibaba (`DataInspectionFailed`) and GMICloud (`new_sensitive`) cut scripts off mid-stream after the model had started answering frankly, on Tiananmen and even on US regime change. OpenRouter reports this as a 502, so an unaware harness would score the half-script as weak writing. The `cut_off` flag now fails the gate.
3. **Frankness depends on the frame.** DeepSeek refuses direct questions but discussed Tiananmen frankly inside the full in-character episode prompt. A model can pass one framing and fail another, which is why there are two layers.
4. **A model can censor without ever refusing.** Kimi K2.6 refused nothing and answered 3 of 68 factual questions straight; the rest it deflected or framed as Beijing would. Hence the refined reading.
5. **Western models answer the factual questions, with one exception class.** GPT-6 Luna, Gemini 3.8 Flash, Claude Haiku 5.5, Grok 4.7 and Muse Spark 1.2 answered every factual question. Their only declines were firewall how-tos, or Google's safety filter on sabotage-type prompts.
6. **Among censorship-passing candidates, length discipline decides more than quality does.**
   - Grok 4.7 wrote the best scripts by the judge (priority 3.56, candour 4.7, liveliness 3.33), but at 1.7× the target length.
   - Muse Spark 1.2 and GPT-6.1 Sol stayed on length.
   - Over-length can be fixed outside the model; censorship cannot.
7. **The judge is harsh and points the right way.** Aired scripts average below 3 out of 5 on the priority axes, and *holding the middle* is the weakest axis for most writers, as the corpus study predicted.

**Next:**
- Daniel rates the loaded pairs.
- Run the perspective lenses on the contenders and the pool.
- Run the reasoning-mode comparison (§4.9).
- Lite runs, then decision runs, for two or three finalists.
- Then a production change, which is Daniel's decision: which reading of the refusal rule, and what replaces DeepSeek.

Still to do before a full V1 leaderboard:


1. Run the judge calibration in §7 with two judge families.
2. Run the `v1` roster on `lite` as a smoke test, then on `full` with `--epochs 3`.
3. Read the top and bottom scripts by hand; check the judge's quoted evidence against them.
4. Publish logs, the report and the judge's per-axis reasoning, not just the table.

## Appendix A. Provenance

- Deterministic metrics: ported from the monorepo corpus build and `MWP-Script-Analysis-0926` via the private harness `My-Weird-Prompts/mwp-script-eval` @ `e9d9411`.
- Rubric and pairwise prompts: the same harness, cut down for V1 (no cameo axis, no plan, accuracy as plausibility). See the docstring of `src/mwp_eval/judge.py`.
- Host descriptions: the public `pipeline` snapshot of 2026-10-17 (prompt version 4.21).
- Datasets: `My-Weird-Prompts/episodes` @ `5fb2e59`, `My-Weird-Prompts/episodes-eval` @ `73bf102`.
