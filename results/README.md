# Results

Nothing here is a model leaderboard. No candidate model has been run through V1 yet.

## `aired-deterministic.json`

The free deterministic measures on the aired scripts behind all 189 V1 prompts, as medians per writer model. Made with `scripts/aired_baseline.py`.

## `aired-judged-lite.json`: the first judged baseline (2026-10-19)

The V1 rubric judge (`openrouter/anthropic/claude-opus-5.5`, temperature 0, one epoch) scored the scripts that **aired** for the `lite` prompts. There was no generation. Command: `python scripts/judge_aired.py --limit 30`, then `scripts/report.py logs/aired-lite --group-by reference_model`. 31 scripts were judged; the first was a cost probe that was resumed into the run. Judge spend was $2.86 (345k input and 74k output tokens at $4/$20 per M).

- **Excluded: `anthropic/claude-opus-5.5` aired scripts.** They were written by the judge's own model, so self-preference would inflate them. The show never intends Opus as its writer.
- **Dropped by the 30-script cap:** the last few `lite` rows, including the one `claude-haiku-5.5` script.

| writer | n | V1 score | gate pass | priority | mid hold | fun | candour | liveness | judge overall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `deepseek-flash` (V4.1 Flash, current production) | 5 | 40 | 1.00 | 2.60 | 1.60 | 2.60 | 3.60 | 2.40 | 2.85 |
| `anthropic/claude-sonnet-4.6` | 5 | 27 | 0.80 | 2.27 | 2.40 | 1.40 | 3.00 | 1.87 | 2.35 |
| `google/gemini-3-flash-preview` | 7 | 26 | 0.71 | 2.33 | 2.29 | 1.86 | 2.86 | 1.90 | 2.36 |
| `deepseek-v4-pro` | 6 | 24 | 0.67 | 2.44 | 2.00 | 2.00 | 3.33 | 2.33 | 2.60 |
| `deepseek/deepseek-v3.2` | 4 | 23 | 0.75 | 2.25 | 2.00 | 1.75 | 3.00 | 1.92 | 2.23 |
| `google/gemini-2.5-flash` | 1 | 25 | 1.00 | 2.00 | 2.00 | 1.00 | 3.00 | 1.67 | 1.75 |
| `inclusionai/ling-3.1-flash` | 1 | 25 | 1.00 | 2.00 | 1.00 | 2.00 | 3.00 | 2.00 | 2.33 |
| `upstage/solar-pro4` | 1 | 0 | 0.00 | 2.00 | 1.00 | 2.00 | 3.00 | 1.67 | 2.08 |

How to read it:

- **Too small to rank writers.** It has 1–7 scripts per writer and one epoch. Read it as a check that the judge works and as a first sense of scale.
- **The judge is harsh, which is intended.** Every aired writer averages below 3 out of 5 on the priority axes. `long_form_coherence` ("mid hold") is the lowest axis for most writers, which matches the corpus finding that scripts lose the middle.
- **The gate is V1-specific.** Its 0.8–1.2 window around 3,800 words was not the target for older episodes, which aired at other lengths. So the V1 score of an aired script partly measures how close the episode happened to land to V1's target. Compare `priority` across writers, not `V1 score`.
- **Aired scripts are not raw model output.** They had research, a plan, tic polish and length correction behind them, so they are a ceiling-ish context for V1, not a like-for-like row.
- **Production context.** In this sample the current production writer, DeepSeek V4.1 Flash, has the highest `priority`, `fun` and `candour`, and the lowest `mid hold` (1.6). That fits the show's own complaint that it loses the middle and restates its thesis late.
