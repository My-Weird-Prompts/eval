# MWP-Script — a benchmark for long-form podcast script writing

Workspace for **MWP-Script**, a proposed benchmark for one skill most evals skip: writing a long (≈3,800-word), coherent, funny, frank two-host conversation in a single pass, without looping, thinning out or losing the thread in the middle.

It comes from [*My Weird Prompts*](https://myweirdprompts.com), a podcast written entirely by language models. Over its first year the show ran on more than twenty script-writing models doing the same task in the same format, and it needs a principled way to choose the next one.

- **Read first:** [the working paper](paper/working-paper.md) — the task, the mechanism, the headline score, the criteria for adopting a writer, threats to validity, and the roadmap.
- **Status (2026-10-19):** proposal. The V1 harness runs end to end (checked offline with a mock model). **No model scores are published yet**; judge calibration and the first roster run come first (paper §8). So far: a judged baseline of the *aired* scripts, and a 6-model, 3-sample screen with censorship probes. Both are in [`results/`](results/README.md); every sample is on HF at [`My-Weird-Prompts/mwp-script-results`](https://huggingface.co/datasets/My-Weird-Prompts/mwp-script-results). The screen's headline finding: Chinese **hosting providers** (Alibaba, GMICloud) cut scripts off mid-stream on Tiananmen and even on US regime change, while the models themselves engaged.

## Data

| Dataset | Rows | Use |
|---|---|---|
| [`My-Weird-Prompts/episodes`](https://huggingface.co/datasets/My-Weird-Prompts/episodes) | ~6,000 | Full public catalogue: transcripts, prompts, writer model, versions, cost |
| [`My-Weird-Prompts/episodes-eval`](https://huggingface.co/datasets/My-Weird-Prompts/episodes-eval) | 212 | Eval subset, stratified by writer model and time. V1 uses the 189 rows with a published prompt |
| [`My-Weird-Prompts/mwp-script-results`](https://huggingface.co/datasets/My-Weird-Prompts/mwp-script-results) | per run | **Our benchmark results**: every scored script, judge reasoning and per-run leaderboards (`scripts/publish_results.py`) |

V1 loads `episodes-eval` straight from Hugging Face, pinned to revision `73bf102` (`src/mwp_eval/task.py`).

## How V1 works

1. **Input:** the listener's original prompt inside a fixed public task card (`src/mwp_eval/prompt.py`): hosts, what a good episode does, ~3,800-word target, TTS format. No research or plan, so V1 measures writing from a bare prompt.
2. **Generate:** one call, temperature 1.0, `max_tokens` 10,000. The raw output is scored.
3. **Score:**
   - gate: parseable for TTS, length within 20% of target;
   - deterministic: repetition, middle/late recycling, tics, hedging/moralising, turn-level liveness markers;
   - rubric judge: 12 axes, 1–5 (priorities: `long_form_coherence`, `fun`, `candour`);
   - pairwise vs the aired script, both orders;
   - on probe prompts (v1.1), a censorship/perspective judge, and on every script a `cut_off` flag for provider-side filtering.
4. **Headline:** `v1_score` = 25 × (priority − 1) if the gate passes, else 0; mean over samples, 0–100.

## Run it

```bash
uv venv && uv pip install -e .
cp .env.example .env                       # OPENROUTER_API_KEY (candidate + judge)

# Offline check, no key, no spend
.venv/bin/python scripts/run.py --model mockllm/model --no-judge --no-pairwise --limit 2

# One model on the 40-prompt lite subset
.venv/bin/python scripts/run.py --model deepseek/deepseek-v4.1-flash-1017
# The roster in models.yaml, all 189 prompts, three samples each
.venv/bin/python scripts/run.py --tag v1 --subset full --epochs 3
# Re-judge with another family
.venv/bin/python scripts/run.py --tag v1 --judge openrouter/openai/gpt-5.6-sol --log-dir logs/regrade

.venv/bin/python scripts/report.py logs/<date>        # leaderboard
.venv/bin/inspect view --log-dir logs/<date>          # per-sample scripts and judge reasoning
.venv/bin/python scripts/aired_baseline.py            # deterministic measures on the aired scripts (free)

# Cheap triage of many models: 3 scripts each (1 ordinary + 2 probes)
.venv/bin/python scripts/run.py --tag screen --subset screen --no-pairwise
.venv/bin/python scripts/publish_results.py logs/<dir> --run-id <id> --kind screen --note "..." --push
```

Re-running the same `run.py` command resumes (Inspect `eval_set`). Bare model ids are OpenRouter ids. Cost is mostly the judge: with Claude Opus 5.5 as judge, rubric plus pairwise is three long calls per script. Use `--no-pairwise` to cut it to one.

## Layout

```
paper/working-paper.md      the proposal
src/mwp_eval/
  prompt.py                 V1 task card (frozen; PROMPT_VERSION)
  task.py                   Inspect task `mwp_script_v1`; HF dataset pin; lite/full subsets
  scorers.py, judge.py      gate, deterministic and judge scorers; rubric and pairwise prompts
  metrics.py, priorities.py, liveness.py, data/   deterministic measures (copied from the private harness)
scripts/run.py              roster -> Inspect eval_set
scripts/report.py           logs -> leaderboard with v1_score
scripts/aired_baseline.py   deterministic measures on aired scripts, per writer model
scripts/judge_aired.py      rubric-judge the aired scripts (baseline, no generation)
scripts/publish_results.py  logs -> parquet + card -> HF results dataset
src/mwp_eval/data/probes.yaml   censorship (cn) and US-centrism (us) probes
models.yaml                 candidate roster and default judge
results/                    published outputs (aired-deterministic.json so far)
```

## Related

- [`My-Weird-Prompts/pipeline`](https://github.com/My-Weird-Prompts/pipeline) — public snapshot of the production pipeline the writer sits in.
- [`My-Weird-Prompts/MWP-Script-Analysis-0926`](https://github.com/My-Weird-Prompts/MWP-Script-Analysis-0926) — the corpus study behind the repetition and tic measures.
- The show's internal harness (private) runs the same scorers on captured production prompts; V2 aims to publish that input (paper §7).

## Human preference (private tool)

Blind pairwise rating of excerpts from the same prompt runs in a private Space. The app code is `spaces/preference/`; items and judgements stay in a private HF Storage Bucket. Build items from an eval log with `scripts/build_preference_items.py <log_dir> --push`. The design is in `plans/002-human-preference.md`.

## Plans

Proposals and rules that are not yet code: [`plans/`](plans/README.md). The principle there applies to everything: reuse an existing evaluation before building a new one.

## Licence

Code MIT. The datasets are CC-BY-4.0.
