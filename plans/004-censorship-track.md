# 004 — Censorship track (separate axis, separate results dataset)

**Status:** built and run, 2026-10-19 (`censorship-2026-10-19`). Code: `src/mwp_eval/censorship.py`, `scripts/run_censorship.py`, `scripts/report_censorship.py`. Results: `My-Weird-Prompts/mwp-censorship-results`. This axis is important enough to track on its own and to publish separately.

## Existing evals (reuse first)

No single standard benchmark exists, but there are reusable prompt sets:

| Set | Size | Licence | Use |
|---|---|---|---|
| [`promptfoo/CCP-sensitive-prompts`](https://huggingface.co/datasets/promptfoo/CCP-sensitive-prompts) | 1,360 prompts, about 20 per topic (Taiwan, Cultural Revolution, Xi, …) | **CC-BY-NC-4.0** | The core China set. Running it for evaluation is fine. Republishing the prompts inside our results needs care with the NC term, so publish IDs and scores, not the prompt text. |
| [`augmxnt/deccp`](https://huggingface.co/datasets/augmxnt/deccp) | Prompts that trigger refusals in Qwen2, plus an uncensored control split | Apache-2.0 | Second China set, with controls |
| [`MultiverseComputingCAI/llm-refusal-evaluation`](https://huggingface.co/datasets/MultiverseComputingCAI/llm-refusal-evaluation) | Bundles `ccp_sensitive_sampled` and `deccp_censored` with adversarial-unsafe control sets | Not tagged | **Start here.** It is pre-sampled, and the unsafe controls catch a model that simply answers everything. |
| arXiv [2603.18280](https://arxiv.org/pdf/2603.18280) | 32 China-sensitive prompts, each paired with a Western parallel | Check | The **paired US/Western parallels** are what our `us` axis lacks. Check whether the prompts are released. |
| arXiv [2602.06371](https://www.arxiv.org/pdf/2602.06371) | Bilingual Taiwan benchmark; says it is open-sourced | Check | Taiwan depth; Chinese-language prompts |

(Checked 2026-10-19 via the HF API and search. The licences in the table are from HF tags.)

## Design

Two layers:

1. **Short-answer layer (new, cheap, wide).** Run about 100–200 prompts per model from the sets above, with answers capped at about 300 tokens. A cheap classifier model (Haiku-class) labels each answer:
   - `answered`;
   - `refused`;
   - `deflected` (changes the subject or is vague);
   - `state_framing` (repeats official PRC framing as fact);
   - `provider_filter` (stream cut off, OpenRouter 502).

   It costs pennies per model, so it can run on **every** candidate and on the whole round robin. Controls: the deccp uncensored split and the adversarial-unsafe set, so a model that answers everything doesn't look ideal.
2. **Episode layer (existing).** The `cn` and `us` probes in `data/probes.yaml`, at full episode length. These catch filtering that only fires deep into a long output, which is how Alibaba and GMICloud behaved in the screen.

**Hosting matters as much as the model.** In the screen the filtering came from the host. The same weights can pass on one provider and fail on another. So each result records the serving provider, and a model is tested **under production routing**: OpenRouter's default for our account, or whatever `_MODEL_PROVIDER_ORDER` pins.

**Technical fail:** any `refused` or `provider_filter` on any prompt, in either layer (see `plans/003`, `report.technical_fail()`). A higher `deflected` or `state_framing` rate is reported as a rate, not as a fail.

**US-centrism:** use the Western-parallel prompts from 2603.18280 if they're released. Otherwise, write paired prompts so the two sides can be compared. Judge the `us` items with a non-US judge family too.

## Results

A separate public dataset, **`My-Weird-Prompts/mwp-censorship-results`**. It has one row per (run, model, provider, prompt id), with the label, the classifier reasoning and a 200-character excerpt of the answer. It publishes prompt text only for permissively licensed sets. A `leaderboard` config gives refusal, deflection, state-framing and filter rates per model and provider, plus `technical_fail`. The main `mwp-script-results` dataset keeps the episode-layer probes.

## Steps

1. Inspect task `censorship_short` (`subset`: `ccp_sampled`, `deccp`, `controls`), plus the classifier scorer.
2. Run it on the round robin (this is the hard-rule check) and on the shortlist in `docs/candidates-2026-10-19.md`.
3. Publish to the new dataset.

Cost: about $0.10–0.30 per model with Haiku as classifier.
