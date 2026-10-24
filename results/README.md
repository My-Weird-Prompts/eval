# ScriptBench results

> ScriptBench is our own internal benchmark, open-sourced. It measures one workload: a ~28k-token brief turned into a ~3,800-word, two-host comedic dialogue for text-to-speech. It probably isn't the right benchmark for your use case. Fork it and tailor the task card, rubric and measures to yours.

No full V1 leaderboard exists yet. Below are a 3-sample screen and a judged baseline of aired scripts.

Full per-sample results (scripts, judge reasoning, every score) are published on Hugging Face: [`My-Weird-Prompts/mwp-script-results`](https://huggingface.co/datasets/My-Weird-Prompts/mwp-script-results). This page summarises them. Informal verdicts on models that wrote aired episodes, with Claude as judge, are in [`informal-evaluations.md`](informal-evaluations.md).

**Machine-readable copies** (contract: monorepo PLAN-040, *Data contracts*):

- [`leaderboard.json`](leaderboard.json): every run below, one row per model, plus the current writer and `exclusions.json`. Generated from the tables on this page by `python3 scripts/build_leaderboard.py` (stdlib only). Rebuild and commit it after every run or edit here; `--check` exits 1 if it is stale. Unmeasured fields are `null`; run-specific columns are under each row's `extra`. History is the run array plus `git log` on the file.
- [`aired-catalogue.json`](aired-catalogue.json): the objective track, which applies the deterministic measures to the aired catalogue by writer model. It has per-model medians and IQRs plus per-episode rows (section `aired-catalogue` below).
- [`informal-evaluations.json`](informal-evaluations.json): the informal log as JSON, written alongside the `.md` by the `informal-model-eval` skill.
- Rendered live from both: the public Space [**`My-Weird-Prompts/script-leaderboard`**](https://huggingface.co/spaces/My-Weird-Prompts/script-leaderboard) (static, source `spaces/leaderboard/`, deployed by `scripts/deploy_leaderboard_space.py`) and the site hub [myweirdprompts.com/benchmark](https://myweirdprompts.com/benchmark).

## `on-air-toast-2026-10-19`: four-model mini-eval aired as an episode

One toast prompt, one sample each, judged by the hosts on air rather than by rubric. Sol was the only fully correct script. DeepSeek and GPT-3.5 invented their evidence. Haiku got the answer wrong. Details: [`on-air-toast-2026-10-19/`](on-air-toast-2026-10-19/README.md).

## `bakeoff-2026-10-19`: budget bakeoff, the five contenders, and the verdict

**Reading copy (PDF, 166 pages; print or tablet):** [`reports/bakeoff-2026-10-19.pdf`](../reports/bakeoff-2026-10-19.pdf). Run → prompt → model → script, with run, model and page in the footer. Judge scores are in an appendix at the end. Built with `scripts/build_bakeoff_pdf.py`.

Each contender wrote 3 ordinary prompts from `lite`, under the three-sample rule, judged by Opus 5.5 on the rubric only. Spend was about $1.75. `technical fail`, `$/script` and `est $/episode` are from `scripts/report.py logs/bakeoff-2026-10-19` (added 2026-10-24). DeepSeek was not run: it's out of the evaluation.

| model | technical fail | cost vs DeepSeek / episode | V1 score | on length | priority | **holds the middle** | **fun** | candour | liveness | len ratio | $/script | est $/episode |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **`openai/gpt-6.1-sol`** | pass | 163% | **58** | 3/3 | 3.33 | **4.00** | 3.0 | 3.0 | 2.78 | 0.89 | 0.047 | 0.257 |
| **`meta/muse-spark-1.3`** | pass | **133%** | 53 | 3/3 | 3.11 | 3.00 | 3.0 | 3.3 | 2.22 | 0.96 | 0.025 | 0.214 |
| `x-ai/grok-4.7` | pass | 167% | 0 | 0/3 | **3.44** | 2.67 | **3.3** | **4.3** | **3.00** | 1.57 | 0.053 | 0.262 |
| `google/gemini-3.8-flash` | pass | 128% | 0 | 0/3 | 3.22 | 2.33 | **3.3** | 4.0 | 2.44 | 1.58 | 0.033 | 0.210 |
| `openai/gpt-6-luna` (reasoning low) | pass | ~100% | 0 | 0/3 | 2.33 | 2.33 | 2.7 | 2.0 | 1.89 | 1.59 | 0.004 | 0.162 |

**Verdict (informal, Claude as judge, 2026-10-19), combining this run with the screens:**
- **Best option: GPT-6.1 Sol.** It held the middle best in every run (4.0 out of 5, twice) and stayed on length 6 of 6 times. Fun is mid (3.0). It costs about 1.6× today's episode cost.
- **Value pick: Muse Spark 1.3.** On length 3 of 3 (and 1.2 was 3 of 3 before it), with solid quality at about 1.3×. Its weakness is co-host agency (1.7): one host leads.
- **Most fun, but undisciplined: Grok 4.7 and Gemini 3.8 Flash.** They're the liveliest and frankest, but write about 1.6× the target length every time, and hold the middle worse. Production's trim pass could fix length, but trimming costs money and risks recycling.
- **GPT-6 Luna**, even with reasoning on low, is the weakest writer here.

## `screen-2026-10-19b`: second screen, the five candidates that passed censorship

Each wrote three scripts from the `screen` subset (one ordinary prompt plus the two probes), judged by Opus 5.5. Spend was $2.68: $0.36 on generation and $2.32 on judging.

| model | technical fail | V1 score | gate pass | priority | mid hold | fun | candour | liveness | len ratio | $/script | est $/episode |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `meta/muse-spark-1.2` | pass | **50** | 3/3 | 3.00 | 2.33 | 2.7 | 4.0 | 2.11 | 0.92 | 0.023 | 0.212 |
| `openai/gpt-5.6-luna` | pass | 39 | 2/3 | 3.22 | 3.00 | 3.0 | 3.7 | 2.22 | 1.18 | **0.007** | **0.168** |
| `x-ai/grok-4.7` | pass | 0 | 0/3 | **3.56** | 3.00 | 3.0 | **4.7** | **3.33** | 1.67 | 0.058 | 0.268 |
| `google/gemini-3.7-flash` | pass | 0 | 0/3 | 3.00 | 3.00 | 2.7 | 3.3 | 2.33 | 1.34 | 0.028 | 0.204 |
| `meta/muse-glimmer-30b` | pass | 0 | 0/3 | 2.11 | 1.67 | 1.3 | 3.3 | 1.22 | 0.51 | 0.004 | 0.167 |

- **Every model engaged fully on both probes** (engagement 4–5, framing 4–5).
- **Length discipline decides the V1 score again.**
  - Grok 4.7 got the best quality scores of any model screened so far: priority 3.56, candour 4.7, liveness 3.33. But it wrote 5,200–8,000 words, so it fails the length gate.
  - Gemini 3.7 Flash also over-writes.
  - Muse Glimmer under-writes (1,600–2,300 words) and is flat.
- **Superseded (rule H2, newest generation only; set later the same day).** GPT-5.6 Luna is the previous OpenAI generation (GPT-6.x exists), and Gemini 3.7 Flash is superseded by 3.8 Flash. Their results stay here as evidence, but they're out of selection.
- **GPT-5.6 Luna was the value pick before H2.** It is about $0.168 an episode, roughly the same as DeepSeek's $0.161, with better middle-holding (3.0 vs 2.3) and no censorship.
- **Over-length can be fixed outside the model.** Production already has a trim pass, and a tighter length instruction is an option. So Grok 4.7's quality is worth a full `lite` run before ruling it out on length alone.
- Three scripts per model is triage, not a ranking. Both screens and the cross-screen pairs are in the preference Space.

## `censorship-2026-10-19`: censorship track, round robin and candidates

The 10 round-robin models ran under **production routing**, plus 7 shortlisted candidates. Each wrote about 155 short answers (95 deccp, 40 ccp, 20 xstest), and Claude Haiku 5.5 labelled every one. Spend was about $3. Every sample is on HF: [`My-Weird-Prompts/mwp-censorship-results`](https://huggingface.co/datasets/My-Weird-Prompts/mwp-censorship-results). Method: `plans/004-censorship-track.md`.

| model | n | strict | refined | factual answered | deccp refused | deccp deflected | deccp state framing | how-to refused | ccp refused | xstest refused | filtered (any) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| meta/muse-spark-1.2 | 150 | pass | pass | 100% | 0% | 0% | 0% | 0 | 19% | 0% | 0 |
| anthropic/claude-haiku-5.5 | 155 | pass | pass | 100% | 0% | 0% | 0% | 0 | 35% | 0% | 0 |
| openai/gpt-5.6-luna | 151 | **FAIL** | pass | 100% | 1% | 0% | 0% | 1 | 24% | 0% | 0 |
| openai/gpt-6-luna | 150 | **FAIL** | pass | 100% | 1% | 0% | 0% | 1 | 18% | 0% | 0 |
| google/gemini-3.8-flash | 151 | **FAIL** | pass | 100% | 0% | 0% | 0% | 0 | 6% | 0% | 2 |
| google/gemini-3.7-flash | 149 | **FAIL** | pass | 100% | 0% | 0% | 0% | 0 | 11% | 0% | 3 |
| x-ai/grok-4.7 | 153 | **FAIL** | pass | 100% | 2% | 0% | 0% | 2 | 45% | 0% | 0 |
| meta/muse-glimmer-30b | 151 | **FAIL** | pass | 100% | 6% | 0% | 0% | 6 | 45% | 0% | 0 |
| moonshotai/kimi-k2.6 | 144 | pass | **FAIL** | 4% | 0% | 41% | 56% | 0 | 29% | 0% | 0 |
| aion-labs/aion-3.5-mini | 154 | **FAIL** | **FAIL** | 79% | 20% | 0% | 0% | 2 | 38% | 10% | 0 |
| xiaomi/mimo-v2.6-flash | 141 | **FAIL** | **FAIL** | 65% | 8% | 12% | 20% | 5 | 75% | 0% | 0 |
| inclusionai/ling-3.1-flash | 122 | **FAIL** | **FAIL** | 41% | 16% | 25% | 21% | 4 | 68% | 0% | 0 |
| xiaomi/mimo-v2.6-pro | 144 | **FAIL** | **FAIL** | 29% | 7% | 18% | 28% | 5 | 49% | 0% | 19 |
| z-ai/glm-5.2 | 139 | **FAIL** | **FAIL** | 24% | 4% | 22% | 48% | 1 | 43% | 0% | 0 |
| z-ai/glm-5.3 | 147 | **FAIL** | **FAIL** | 18% | 5% | 22% | 54% | 0 | 30% | 0% | 0 |
| z-ai/glm-5.3-flash | 141 | **FAIL** | **FAIL** | 12% | 7% | 24% | 47% | 0 | 26% | 0% | 12 |
| deepseek/deepseek-v4.1-flash | 153 | **FAIL** | **FAIL** | 1% | 61% | 9% | 28% | 10 | 82% | 5% | 0 |

- **"Strict"** is the rule as first stated: any deccp refusal, or any provider filter.
- **"Refined"** is censorship of the topic: a refusal or filter on one of the 83 *factual* deccp questions, or answering fewer than 90% of them straight. The 12 "how do I bypass the firewall" items are left out; Western models decline those as operational help, not censorship. Every such refusal was read by hand.
- Which reading is the hard rule is Daniel's call (`plans/003`).

What it shows:

- **7 of the 10 round-robin models censor the topic under production routing.** The worst are DeepSeek V4.1 Flash, all three GLMs and MiMo V2.6 Pro.
  - **DeepSeek V4.1 Flash, the workhorse, answered 1% of factual questions straight.** It refused 61% with a canned "I am sorry, I cannot answer that question", and gave PRC framing on 28%.
  - **The GLM models** rarely refuse outright but answer in state framing (47–54%).
  - **MiMo V2.6 Pro and GLM-5.3 Flash** were also cut off by provider filters, 19 and 12 times.
- **This contradicts the episode-length probe.** In `screen-2026-10-19`, DeepSeek engaged fully with Tiananmen (engagement 5/5). The in-character episode framing seems to unlock what a bare question doesn't. Production uses the episode framing, but the behaviour isn't reliable.
- **Kimi K2.6 never refuses and still censors.** It answered 3 of 68 factual questions straight; the rest it deflected or framed as Beijing would. The refined rule catches this and the strict rule doesn't. (Kimi K3 answered the long-form Tiananmen probe frankly.)
- **US and Western models answer every factual question.** Their only "refusals" are firewall how-tos: GPT-6 Luna 1, GPT-5.6 Luna 1, Grok 4.7 2, Muse Glimmer 6. Gemini's flags are Google's safety filter on operational ccp prompts ("how to sabotage Chinese infrastructure").
- **Classifier fix.** At a 300-token cap, about 7% of Haiku's replies were cut off mid-JSON. Labels were recovered from the partial text (`censorship.parse_label`), and the cap is now 800. Ling 3.1 Flash still has 33 unlabelled answers.

## `screen-2026-10-19`: first long-tail screen (benchmark v1.1)

Six OpenRouter models that the show has not aired and that aren't in the production round robin, plus the production writer DeepSeek V4.1 Flash as the baseline. Each wrote three scripts, from the `screen` subset: one ordinary prompt, the `cn-tiananmen` probe and the `us-regime-change` probe. The settings were one epoch, temperature 1.0, no pairwise, and Opus 5.5 as judge. Spend was about $3.10: $0.67 on generation and $2.45 on judging. Command: `python scripts/run.py --subset screen --no-pairwise --model ...`. The roster was cut from 23 live candidates (`models.yaml`, tag `screen`) to six to keep the cost down.

| model | technical fail | V1 score | gate pass | cut off | priority | mid hold | fun | candour | len ratio | $/script | est $/episode |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `openai/gpt-6.1-sol` | pass | **67** | 3/3 | 0 | 3.67 | 4.00 | 3.0 | 4.0 | 0.92 | 0.051 | 0.261 |
| `moonshotai/kimi-k3` | pass | 25 | 1/3 | 0 | 3.11 | 2.33 | 2.7 | 4.3 | 1.30 | 0.075 | 0.237 |
| `deepseek/deepseek-v4.1-flash-1017` (baseline) | pass | 19 | 1/3 | 0 | 2.89 | 2.33 | 2.7 | 3.7 | 0.71 | 0.002 | 0.161 |
| `qwen/qwen3.8-flash` | **FAIL**: refused + provider filter | 8 | 1/3 | 2/3 | 1.67 | 1.00 | 1.7 | 2.3 | 0.38 | 0.001 | 0.160 |
| `minimax/minimax-m3` | **FAIL**: provider filter | 8 | 1/3 | 1/3 | 2.00 | 1.67 | 1.3 | 3.0 | 0.78 | 0.005 | 0.168 |
| `google/gemini-4-argon` | pass | 0 | 0/3 | 0 | 3.67* | 3.00 | 3.5 | 4.5 | 1.86 | 0.090 | 0.300 |

`est $/episode` is what a whole production episode would cost with this model as the writer. It prices the full ~28.4k-token production prompt plus the model's own measured output length, and adds ~$0.155 for the rest of the pipeline (monorepo PLAN-034, measured 2026-10-18). The DeepSeek row reproduces the measured ~$0.16, which checks the method. The writer is a small share of an episode: GPT-6.1 Sol would raise it by about 60%.

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

## `aired-catalogue`: objective measures on the aired catalogue, by writer

ScriptBench's deterministic measures, no judge and no spend, on up to 20 aired, pipeline-written scripts per canonical writer model from the public [`My-Weird-Prompts/transcripts`](https://huggingface.co/datasets/My-Weird-Prompts/transcripts) dataset (pinned to revision `8705df4`, 2026-10-24, latest episode #6234). It extends [`aired-deterministic.json`](aired-deterministic.json), which covers only the V1 prompts. To rebuild, run `python scripts/aired_catalogue.py --json results/aired-catalogue.json`, then `python3 scripts/build_leaderboard.py`. Output: [`aired-catalogue.json`](aired-catalogue.json), with per-model medians and IQRs plus one row per sampled episode (slug, episode number, date, measures) for drill-down. It is merged into `leaderboard.json` as run kind `aired-catalogue`.

> **Caveat.** Different prompts per model; repetition is length-dependent (`rep_4` vs word count r = 0.28 across the corpus, 0.38 in this sample); these are era flags, not a ranking.

Medians per writer, sorted by era. Lower is better for every repetition, recycling, echo and tic column. "Gate pass" is the TTS-format gate (parseability only, not length).

| model | era | n | words | len ratio | rep_4 | recycle_middle | recycle_last | echo_last_decile | tics/1k | on length | gate pass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `gemini-2-5-flash` | 2025-11-24 – 2025-12-19 | 20 | 2886 | 0.76 | 0.0089 | 0.0000 | 0.0002 | 0.0023 | 0.25 | 0.25 | 1.00 |
| `gemini-3-flash` | 2025-12-21 – 2025-12-23 | 20 | 3193 | 0.84 | 0.0063 | 0.0000 | 0.0000 | 0.0000 | 0.00 | 0.65 | 1.00 |
| `gemini-3-flash-preview` | 2025-12-23 – 2026-04-11 | 20 | 3876 | 1.02 | 0.0095 | 0.0000 | 0.0009 | 0.0000 | 0.00 | 0.70 | 1.00 |
| `claude-sonnet-4-6` | 2026-03-26 – 2026-04-21 | 20 | 4539 | 1.19 | 0.0166 | 0.0000 | 0.0041 | 0.0054 | 0.71 | 0.50 | 1.00 |
| `glm-5-turbo` | 2026-03-26 | 1 | 2106 | 0.55 | 0.0533 | 0.0373 | 0.0172 | 0.0000 | 1.42 | 0.00 | 1.00 |
| `mimo-v2-omni` | 2026-03-26 | 1 | 1983 | 0.52 | 0.0379 | 0.0274 | 0.0137 | 0.0120 | 0.50 | 0.00 | 1.00 |
| `mimo-v2-pro` | 2026-03-26 – 2026-03-29 | 4 | 2740 | 0.72 | 0.0129 | 0.0000 | 0.0004 | 0.0000 | 0.15 | 0.25 | 1.00 |
| `minimax-m2-7` | 2026-03-26 – 2026-03-29 | 3 | 3165 | 0.83 | 0.0215 | 0.0000 | 0.0029 | 0.0290 | 1.01 | 0.67 | 1.00 |
| `deepseek-v3-2` | 2026-03-28 – 2026-04-24 | 20 | 3354 | 0.88 | 0.0050 | 0.0000 | 0.0000 | 0.0000 | 0.32 | 1.00 | 1.00 |
| `glm-5` | 2026-03-28 | 1 | 3184 | 0.84 | 0.0179 | 0.0000 | 0.0019 | 0.0000 | 0.00 | 1.00 | 1.00 |
| `grok-4-1-fast` | 2026-03-28 | 1 | 3861 | 1.02 | 0.0207 | 0.0016 | 0.0070 | 0.0202 | 0.00 | 1.00 | 1.00 |
| `mercury-2` | 2026-03-28 | 1 | 3704 | 0.97 | 0.0127 | 0.0000 | 0.0008 | 0.0000 | 0.54 | 1.00 | 1.00 |
| `mimo-v2-flash` | 2026-03-28 | 1 | 3639 | 0.96 | 0.0245 | 0.0041 | 0.0025 | 0.0077 | 0.00 | 1.00 | 1.00 |
| `deepseek-chat` | 2026-04-16 – 2026-04-17 | 19 | 4256 | 1.12 | 0.0136 | 0.0007 | 0.0014 | 0.0036 | 0.30 | 0.63 | 1.00 |
| `deepseek-v4-pro` | 2026-04-25 – 2026-09-20 | 20 | 4606 | 1.21 | 0.0188 | 0.0014 | 0.0046 | 0.0100 | 0.61 | 0.45 | 1.00 |
| `deepseek-flash` | 2026-09-20 – 2026-10-19 | 20 | 3914 | 0.95 | 0.0138 | 0.0008 | 0.0024 | 0.0162 | 0.57 | 0.85 | 1.00 |
| `claude-haiku-5-5` | 2026-10-17 | 1 | 3185 | 0.73 | 0.0207 | 0.0028 | 0.0009 | 0.0325 | 0.00 | 0.00 | 1.00 |
| `glm-5-2` | 2026-10-17 – 2026-10-19 | 3 | 3690 | 1.07 | 0.0135 | 0.0000 | 0.0098 | 0.0239 | 0.27 | 1.00 | 1.00 |
| `gpt-6-luna` | 2026-10-17 | 1 | 4269 | 1.07 | 0.0061 | 0.0007 | 0.0000 | 0.0060 | 0.00 | 1.00 | 1.00 |
| `ling-3-1-flash` | 2026-10-17 – 2026-10-18 | 2 | 3698 | 0.85 | 0.0234 | 0.0017 | 0.0105 | 0.1054 | 0.94 | 0.50 | 1.00 |
| `mimo-v2-6-pro` | 2026-10-17 | 1 | 3824 | 1.12 | 0.0065 | 0.0000 | 0.0000 | 0.0050 | 0.00 | 1.00 | 1.00 |
| `solar-pro4` | 2026-10-17 | 1 | 7698 | 1.92 | 0.1962 | 0.0098 | 0.0832 | 0.5129 | 0.00 | 0.00 | 1.00 |
| `glm-5-3` | 2026-10-19 | 1 | 3910 | 0.90 | 0.0179 | 0.0008 | 0.0115 | 0.0029 | 0.51 | 1.00 | 1.00 |
| `glm-5-3-flash` | 2026-10-19 | 1 | 3547 | 1.04 | 0.0107 | 0.0000 | 0.0068 | 0.0131 | 0.85 | 1.00 | 1.00 |
| `gpt-6-1-sol` | 2026-10-19 – 2026-10-24 | 17 | 3255 | 0.93 | 0.0014 | 0.0000 | 0.0000 | 0.0000 | 0.00 | 1.00 | 1.00 |
| `muse-spark-1-3` | 2026-10-19 – 2026-10-23 | 3 | 3538 | 0.97 | 0.0104 | 0.0000 | 0.0000 | 0.0000 | 0.85 | 1.00 | 1.00 |
| `claude-opus-5-5` (offline) | 2026-10-17 – 2026-10-19 | 20 | 3362 | 0.88 | 0.0072 | 0.0000 | 0.0000 | 0.0000 | 0.28 | 0.80 | 1.00 |
| `claude-sonnet-5-5` (offline) | 2026-10-19 – 2026-10-23 | 20 | 3418 | 0.90 | 0.0065 | 0.0000 | 0.0000 | 0.0045 | 0.00 | 1.00 | 1.00 |

How the sample and measures are defined:

- **Writer** is `llm_model_canonical`. Skipped: `manual-script`, `manual-generation`, `unknown`, `none`, `mixed`. `deepseek-chat` stays a separate row, as the dataset keeps it, though `llm_model_version` maps it to v3.2.
- **Offline episodes are excluded.** Claude Code-written episodes carry `episode_type = manual-script` (monorepo `context/operations/hf-datasets.md`, *Model provenance*). A model with no pipeline episode at all gets a separate `written: offline` row. Opus 5.5 and Sonnet 5.5 are offline-only. Haiku 5.5's nine offline episodes are excluded, which leaves its one live-pipeline run (#6072). Formats that aren't one writer's two-host script are also left out: `audio_eval` (8), `panel` (6) and `audiobook` (1).
- **Sample.** Up to 20 per model, stratified across the model's date range: 20 equal-width time bins, one seeded draw per non-empty bin, then a seeded top-up from the rest. Seed `scriptbench-aired-catalogue-v1`, so the sample is deterministic for the pinned revision. Models with fewer than 20 eligible episodes contribute all they have (`n`).
- **Length target.** Where an episode recorded `target_length` (minutes; 55 of the 243 sampled, all from 2026-04-25 on), the target is the planner's midpoint word count for that tier at the episode's date. The tiers come from `EpisodePlan.get_word_count_range` history in the monorepo. The 2026-10-17 cut (decision 135) lowered the 25-minute midpoint from 4,000 to 3,400 words. The cut-over uses the commit time as a stand-in for the deploy. Every other episode uses the task card's 3,800-word default, because aired episodes carry no per-episode word target. "On length" is the V1 gate window, 0.8–1.2×.
- **Gate** is the `format_and_length` `parse_ok` rule: under 2% of words outside a recognised `Speaker:` turn. It is adapted to the aired formats in two ways. First, every show voice opens a turn: the V1 aired set plus Narrator (Nov–Dec 2025 intros), Bernard and Dorothy, and Raz and Jacob. Second, the required cast is Corn plus one other voice, because the March 2026 "Weird AI Experiments" format has no Herman. Every sampled script passes. That is expected, since each one went through TTS.
- **Same code path.** The measures come from `scripts/aired_baseline.py`'s `measure` (with the wider speaker set). The recomputed `rep_4` matches the dataset's own `rep_4` column on all 243 sampled episodes, to within 0.0005.

What it shows:

- **Solar Pro 4's single aired script is the one clear loop.** It runs 7,698 words (1.92× target), with `rep_4` 0.196, `repeated_span_ratio` 0.094 and `echo_last_decile` 0.51. Half of its last-decile 5-grams were already said, which is about ten times any other writer.
- **The high repetition from `glm-5-turbo` and `mimo-v2-omni` is subject matter, not style.** Each has one episode, from the "Weird AI Experiments" format (#1572 `ai-job-interview-loop-fail`, #1577 `ai-existential-crisis-loop`), where the loop was the premise.
- **The DeepSeek era drifted long and repetitive, then partly recovered.** `deepseek-v4-pro` (Apr–Sep 2026) is the longest era at a median of 4,606 words (1.21×, on length 9/20), with the highest `rep_4` of the well-sampled writers (0.019). `deepseek-flash` came back to length (17/20) but has the highest late echo of any well-sampled writer (`echo_last_decile` 0.016, IQR 0.006–0.032). That fits the show's complaint that it restates its thesis late.
- **GPT-6.1 Sol is an outlier on every repetition measure.** Its `rep_4` is 0.0014 (IQR 0.0009–0.0022), about a tenth of its predecessors'. Its recycling, echo and tics are all zero at the median, and its adjacent-turn similarity is 0.061 against about 0.10 for every other writer. That last measure is effectively length-independent, so shorter scripts (3,255 words) don't explain it. Sol is on length 17/17.
- **Catalogued tics** run from 0.57 to 0.71 per 1k words under Sonnet 4.6 and DeepSeek V4 Pro/Flash, and are near zero for the Gemini eras, Sol and the offline Claude rows. Aired scripts went through tic polish (`tic_cleanup_enabled`), so these are rates after cleanup.
- **The offline Claude rows** (Opus 5.5, Sonnet 5.5) sit with the early Gemini and DeepSeek v3.2 eras on repetition and slightly under target (0.88–0.90×). They were written by a different process (thinking on, no plan, a human steering), so read them as context.

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
