# MWP-Script: benchmarking language models on long-form two-host dialogue

**Working paper, draft 1 — 2026-10-19.** Daniel Rosehill, *My Weird Prompts*. Drafted with Claude Opus 5.5.

Status: proposal. The V1 harness in this repository runs end to end. No V1 model scores have been published yet; §8 lists what has to happen before any are.

---

## Abstract

*My Weird Prompts* (MWP) is a podcast written entirely by language models. Each episode is a 25–30 minute conversation, about 3,500–4,500 words, between two recurring AI hosts, written in a single pass from a short prompt. In its first year the show ran on more than twenty script-writing models doing the same task in the same format. The show therefore needs a way to choose its writer, and its back catalogue is a natural test set for a skill that most benchmarks skip: **sustaining a long, coherent, entertaining conversation without looping, thinning out or losing the thread.**

This paper proposes **MWP-Script**, a benchmark for that skill. V1 gives a candidate model the original prompt behind an aired episode, wrapped in a short fixed task card, and scores the raw script in three layers: a hard **gate** (parseable for text-to-speech, length within 20% of target), cheap **deterministic measures** of repetition, recycling, tics, hedging and dialogue liveness, and an **LLM judge** that scores a 12-axis rubric and compares the script head to head with the one that aired. The headline number is the judge's mean on the show's three priorities (holding the middle, being fun, being frank), rescaled to 0–100, and set to 0 for scripts that fail the gate.

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

## 5. Headline score and decision criteria

### 5.1 The V1 score

Per sample:

```
v1_score = 25 × (priority − 1)    if parse_ok and 0.8 ≤ length_ratio ≤ 1.2
         = 0                       otherwise
```

The model's V1 score is the mean over samples, from 0 to 100. Reported alongside it are the gate pass rate, the pairwise win rate, `liveness`, `$/script` at OpenRouter list price, and every sub-measure.

Why this shape:

- **The gate is multiplicative because the show can't air a failed script.** A brilliant 1,500-word script still needs a second LLM pass to expand it, which costs money and invites recycling. A script TTS can't parse doesn't air at all. Averaging those failures in at face value would reward models that are good when they work and unreliable.
- **Priority, not overall.** The 12-axis mean is dominated by craft axes on which competent models all score 3–4. The three priority axes are where models differ and where the show's listeners notice.
- **Pairwise is reported, not folded in.** It is more sensitive but anchored to a moving reference: aired scripts come from different models and different prompt versions over the year.

### 5.2 Proposed criteria for adopting a production writer

A candidate should replace the current production writer (DeepSeek V4.1 Flash) only if all of these hold:

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

## 7. Roadmap

- **V1 (this repository).** Bare-prompt task, public data, Inspect AI harness, deterministic measures plus judge. Next: calibrate the judge, run the roster, publish the first leaderboard.
- **Judge calibration (before any V1 leaderboard).** The private harness holds a labelled set of aired Opus (lively) against aired DeepSeek (flat) episodes, split into dev and holdout. Accept a rubric axis only if, on holdout, it separates the two with AUC ≥ 0.8 under two judge families. The labelled list can be published; the episodes are already public.
- **V2: the production input.** Capture the full production prompt (template, plan, research, memories) for a fixed set of prompts, scrub anything private, and publish it as a dataset. That restores plan coverage (does the script cover the plan's middle segments?), key-fact coverage, and accuracy against sources. It turns V1's "bare-prompt writer" into "production writer".
- **V3: human preference.** Pairwise listening judgements from the producer and listeners on the same prompts, to check and eventually replace parts of the LLM judge.
- **Later:** longer formats (45 and 60 minutes, where recycling is worst), a cameo character, and translated editions.

## 8. Before the first published score

1. Run the judge calibration in §7 with two judge families.
2. Run the `v1` roster on `lite` as a smoke test, then on `full` with `--epochs 3`.
3. Read the top and bottom scripts by hand; check the judge's quoted evidence against them.
4. Publish logs, the report and the judge's per-axis reasoning, not just the table.

## Appendix A. Provenance

- Deterministic metrics: ported from the monorepo corpus build and `MWP-Script-Analysis-0926` via the private harness `My-Weird-Prompts/mwp-script-eval` @ `e9d9411`.
- Rubric and pairwise prompts: the same harness, cut down for V1 (no cameo axis, no plan, accuracy as plausibility). See the docstring of `src/mwp_eval/judge.py`.
- Host descriptions: the public `pipeline` snapshot of 2026-10-17 (prompt version 4.21).
- Datasets: `My-Weird-Prompts/episodes` @ `5fb2e59`, `My-Weird-Prompts/episodes-eval` @ `73bf102`.
