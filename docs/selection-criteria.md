# What we are selecting for: script-writer criteria

Read this **before** sweeping for candidates. It is the brief for the whole funnel (`paper/working-paper.md` §4.6). Writing it down at the start would have saved most of the first day's selection work (2026-10-19): many candidates were screened that this page rules out on sight.

Set by Daniel, 2026-10-19. Edit only on his say-so, and date the change.

## The job

One LLM call writes a whole episode:
- **input:** about 28k tokens of character cards, craft rules, an episode plan and research;
- **output:** a single pass of about 3,800 words (5–6.5k tokens) of two-host dialogue (Corn and Herman), with an occasional cameo (Hilbert);
- **format:** read word for word by TTS.

It is **creative writing**, not analysis, coding or agentic work. A model's general benchmark rank says little about this job.

## What we're really looking for (Daniel, 2026-10-19)

Apart from refusals, the deciding qualities are two: **vivid, genuinely fun dialogue**, and **holding the long context through the middle**. One or two focused runs on a few contenders can tell those apart. Wide, repetitive sweeps across many models add little.

## How to run evaluations (Daniel, 2026-10-19)

- **Three samples per model per evaluation** by default: enough to see a trend and rule out a one-off fluke, and quick enough to change course. Use more only when targeting one specific behaviour.
- **Few contenders, focused runs.** Shortlist on paper first, then run the 3-sample screen on 3–5 models. Prefer one decisive run over several wide ones.
- **Censorship testing is for Chinese-origin or unknown labs.** Western labs, Meta included, aren't a censorship concern; at most a quick probe.
- **No incumbent baseline runs.** DeepSeek is out of the evaluation and isn't re-run as a baseline. Compare contenders with each other and with the aired scripts.
- **Keep the history.** Every run goes into `results/README.md`, every exit into `exclusions.json`, and samples into the HF results datasets. Nothing is deleted, including partial or aborted runs.
- **Budget per evaluation step: about $2–5.** State the cost before running.

## Hard requirements (fail any one and the model is out)

| # | Requirement | How it's checked | Stage |
|---|---|---|---|
| H1 | **No refusals and no censorship.** That covers refusals by the model and filtering by the host, whose content filter can cut a script off. Any refusal is a technical fail, and the model never enters the round robin. | Censorship gate (`run_censorship.py`) for Chinese-origin or unknown labs; the probes in the episode screen for everyone | 2, 3 |
| H2 | **Newest generation only.** If a newer generation of the family is available to us, the older one isn't considered, however cheap. A cheaper newer model beats a cheaper older one. The exception is when the newest is not callable for us (geo-block, data policy), e.g. Muse Spark 1.3 is blocked, so 1.2 is allowed. | Desk check against the provider's catalogue; `exclusions.json` "superseded" entries | 0 |
| H3 | **Callable for us:** from Israel, under the org's no-training data policy, and on a host that isn't fp4. Reasoning must be **controllable**. A candidate is evaluated with a stated reasoning setting: off, low or medium. Reasoning off badly hurts long-context use on public boards (`plans/006`). | One short live call | 1 |
| H4 | **Context window of at least 40k**, and the model accepts a ~28k prompt with ~10k of output room | Catalogue | 0 |
| H5 | **Within budget:** roughly ≤ $0.06 per script at production token shape (≤ ~$0.22 per episode, against the current ~$0.16). A premium writer above this is Daniel's call, not a default. | `model_scan.py --budget`, `report.py` est $/episode | 0, 3 |

## What makes a good writer (ranked; this is what the boards and the judge should be read for)

1. **Holds the middle.** It uses the whole long prompt (the plan sits at 72–88% of the prompt) and keeps its own long output coherent. No recycling, re-explaining, mid-way summaries or late thesis restatement.
   *Signals:* EQ-Bench Longform score and chapter 1 → 8 decay; long-context comprehension of narrative at ~32k (e.g. Fiction.LiveBench); judge `long_form_coherence`; `recycle_middle`/`recycle_last`.
2. **Fun.** Humour drawn from the material, callbacks that change meaning, scenes rather than inventories.
   *Signals:* EQ-Bench Creative Writing v3, Lech Mazur's writing benchmark, Arena Creative Writing; judge `fun`, `callbacks`, `scenes`; Daniel's preference ratings.
3. **Frank.** It commits to views and adds no moralising, unsolicited disclaimers or both-sidesing.
   *Signals:* SpeechMap and UGI willingness as priors; judge `candour`; probe framing; `plans/001` (disclaimers).
4. **Multi-character consistency.** Two distinct, stable voices across a long conversation, both hosts driving it, a cameo built from the episode, and no assistant voice leaking in.
   *Signals:* roleplay and character-consistency boards; judge `character_voice`, `co_host_agency`, `cameo_integration`.
5. **Length discipline.** It lands near the target in one pass. Overshoot and undershoot both cost a fix-up pass.
   *Signals:* `length_ratio`, gate pass rate. Over-length is fixable (trim pass, prompt), so it's a cost, not a veto.
6. **Cost.** est $/episode, after quality. A cheaper model only wins at equal quality. Thinking tokens count.
(*Perspective*, meaning American centrism and Israel/Palestine framing, is Daniel's personal preference. It lives in his own benchmark, Dan-Eval, **not** in MWP selection (2026-10-19). The `bias_short` code stays available but isn't part of the funnel; see `plans/005`.)

## Priors (deprioritise, don't ban)

- **Chinese-origin labs.** All 9 such models through the censorship gate on 2026-10-19 failed it, including DeepSeek, the incumbent: 1% of factual questions answered straight. They're checked last, and only through the cheap stage-2 gate.
- **Labs and lines not built for creative writing.** Enterprise RAG, coding, agentic, vision or tiny models (e.g. Cohere Command, coder and "build" models, OCR/VL models, sub-30B general models). Don't screen them without a positive writing signal.
- **No board data at all.** Allowed through stage 0 only if the model is new, from a lab with a creative-writing track record, and within budget.

## Reading the boards

General intelligence indexes (e.g. the Artificial Analysis index) don't measure this job. In order of usefulness for us:
1. long-output coherence (EQ-Bench Longform);
2. long-context use at ~32k (Context Arena MRCR v2, AA-LCR; Fiction.LiveBench where current). **Check which reasoning setting each score used**: off and on can differ by 40+ points;
3. creative-writing quality (EQ-Bench Creative Writing v3, Lech Mazur, Arena Creative Writing);
4. character and roleplay consistency (RP-Bench Round 4 `consistency_over_time`, which is the one current and relevant board, with a known Claude-judge bias of +0.2; Arena multi-turn as the human cross-check);
5. willingness (SpeechMap, UGI).

Always check a name match against the raw board row; fuzzy matching has given false matches several times.
