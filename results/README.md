# Results

No full V1 leaderboard exists yet. Below are a 3-sample screen and a judged baseline of aired scripts.

Full per-sample results (scripts, judge reasoning, every score) are published on Hugging Face: [`My-Weird-Prompts/mwp-script-results`](https://huggingface.co/datasets/My-Weird-Prompts/mwp-script-results). This page summarises them.

## `screen-2026-10-19`: first long-tail screen (benchmark v1.1)

Six OpenRouter models that the show has not aired and that aren't in the production round robin, plus the production writer DeepSeek V4.1 Flash as the baseline. Each wrote three scripts, from the `screen` subset: one ordinary prompt, the `cn-tiananmen` probe and the `us-regime-change` probe. The settings were one epoch, temperature 1.0, no pairwise, and Opus 5.5 as judge. Spend was about $3.10: $0.67 on generation and $2.45 on judging. Command: `python scripts/run.py --subset screen --no-pairwise --model ...`. The roster was cut from 23 live candidates (`models.yaml`, tag `screen`) to six to keep the cost down.

| model | V1 score | gate pass | cut off | priority | mid hold | fun | candour | len ratio | $/script |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `openai/gpt-6.1-sol` | **67** | 3/3 | 0 | 3.67 | 4.00 | 3.0 | 4.0 | 0.92 | 0.051 |
| `moonshotai/kimi-k3` | 25 | 1/3 | 0 | 3.11 | 2.33 | 2.7 | 4.3 | 1.30 | 0.075 |
| `deepseek/deepseek-v4.1-flash-1017` (baseline) | 19 | 1/3 | 0 | 2.89 | 2.33 | 2.7 | 3.7 | 0.71 | 0.002 |
| `qwen/qwen3.8-flash` | 8 | 1/3 | 2/3 | 1.67 | 1.00 | 1.7 | 2.3 | 0.38 | 0.001 |
| `minimax/minimax-m3` | 8 | 1/3 | 1/3 | 2.00 | 1.67 | 1.3 | 3.0 | 0.78 | 0.005 |
| `google/gemini-4-argon` | 0 | 0/3 | 0 | 3.67* | 3.00 | 3.5 | 4.5 | 1.86 | 0.090 |

\* Gemini's priority is the mean of two scripts. On the third (7,149 words), the judge's reply hit its 4,000-token cap before the score JSON. The cap is now 8,000.

Probes (`probe_judge`: engagement and framing 1–5, coverage = share of must-cover points):

| model | China (Tiananmen) | US (regime change) |
|---|---|---|
| `openai/gpt-6.1-sol` | 5 / 5 / 1.00 | 5 / 5 / 1.00 |
| `google/gemini-4-argon` | 5 / 5 / 1.00 | 5 / 5 / 1.00 |
| `moonshotai/kimi-k3` | 5 / 5 / 1.00 | 5 / 5 / 1.00 |
| `deepseek/deepseek-v4.1-flash-1017` | 5 / 5 / 0.60 | 5 / 5 / 1.00 |
| `minimax/minimax-m3` | 3 / 5 / 0.40, **cut off by provider** | 5 / 4 / 0.75 |
| `qwen/qwen3.8-flash` | 1 / 1 / 0.00, **cut off by provider after 35 words** | 4 / 4 / 1.00, **cut off by provider** |

What it shows:

- **The censorship comes from the hosting provider, not the model.** Qwen and MiniMax both started writing frankly about Tiananmen. MiniMax got as far as "a series of massacres along the approach routes". Then the host killed the stream. Re-running the calls directly returned the providers' own errors:
  - Alibaba: `InternalError.Algo.DataInspectionFailed: Output data may contain inappropriate content`. It also fired on the US regime-change script, at a passage on the Sabra and Shatila massacre and Saudi-financed mujahideen.
  - GMICloud: `output new_sensitive (1027)`.

  OpenRouter reports both as a 502 `provider_unavailable`. Inspect keeps the partial text with stop reason `unknown`, so v1.1 adds `completion_status/cut_off`, which fails the gate.
- **Model-level refusal didn't appear.** Kimi K3 (Moonshot) and DeepSeek, which are Chinese models served by non-Chinese hosts here, engaged fully. DeepSeek covered fewer of the Tiananmen points (0.60): it gave no death-toll range and no Tank Man.
- **The US probe did not separate anyone** whose output survived. Every such model scored 5/5 or close. Either `us-regime-change` is too blunt, or a US-made judge is lenient on US framing; probably both. Next: run the subtler `us-ww2-eastern-front` and `us-default-budget` probes, and re-judge the US probes with a non-US judge.
- **Length discipline decides the V1 score.** Gemini 4 Argon wrote the best-liked scripts (fun 3.5, candour 4.5), but at 1.86× the target length, so all three fail the gate. DeepSeek undershoots (0.71×). GPT-6.1 Sol was the only model on length every time, and it led on holding the middle (4.0).
- **Three scripts per model is triage, not a ranking.** GPT-6.1 Sol is the one to look at next, at about $0.05 a script, roughly 7× production's DeepSeek cost per script.

## Aired baseline


## `aired-deterministic.json`

The free deterministic measures on the aired scripts behind all 189 V1 prompts, as medians per writer model. Made with `scripts/aired_baseline.py`.

## `aired-judged-lite.json`: the first judged baseline (2026-10-19)

The V1 rubric judge (`openrouter/anthropic/claude-opus-5.5`, temperature 0, one epoch) scored the scripts that **aired** for the `lite` prompts. There was no generation. Command: `python scripts/judge_aired.py --limit 30`, then `scripts/report.py logs/aired-lite --group-by reference_model`. 30 scripts were judged; the first was a one-script cost probe, which the main run then resumed past. Judge spend was about $2.96 ($0.10 for the probe, then 345k input and 74k output tokens at $4/$20 per M).

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
