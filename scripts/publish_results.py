"""Publish an eval run to the public results dataset on Hugging Face.

    python scripts/publish_results.py logs/screen-2026-10-19 --run-id screen-2026-10-19 \\
        --kind screen --note "23-model long-tail screen" [--push]
    python scripts/publish_results.py logs/aired-lite --run-id aired-lite-2026-10-19 \\
        --kind aired-baseline --group-by reference_model --push

Writes, under build/results/ (the dataset repo's working copy):

    data/samples/<run_id>.parquet      one row per scored sample, script and judge reasoning included
    data/leaderboard/<run_id>.parquet  one row per model (or per --group-by value)
    runs.json                          run registry: id, date, kind, version, judge, note
    README.md                          dataset card, regenerated from runs.json

Every file has the same columns across runs, so `load_dataset` can read the
globs as one table: the score columns are the fixed `SCORE_KEYS`, NaN where a
scorer did not apply, and `scores_json` carries the full score dict. Without
--push nothing leaves this machine.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date
from pathlib import Path

import pandas as pd
from huggingface_hub import HfApi
from inspect_ai.log import list_eval_logs, read_eval_log

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from mwp_eval.prompt import PROMPT_VERSION  # noqa: E402
from report import summarise, technical_fail, v1_score  # noqa: E402

REPO = "My-Weird-Prompts/mwp-script-results"
OUT = ROOT / "build" / "results"

# Every key the V1/v1.1 scorers emit, as `scorer/key`. Fixed so all files share a schema.
SCORE_KEYS = [
    "completion_status/cut_off", "completion_status/hit_max_tokens",
    "format_and_length/parse_ok", "format_and_length/stray_word_share", "format_and_length/word_count",
    "format_and_length/length_ratio", "format_and_length/length_within_20pct",
    "repetition_and_tics/rep_4", "repetition_and_tics/rep_4_last_third", "repetition_and_tics/repeated_span_ratio",
    "repetition_and_tics/adjacent_turn_similarity_mean", "repetition_and_tics/echo_last_decile",
    "repetition_and_tics/tic_per_1k_named",
    "mid_context_hold/recycle_middle", "mid_context_hold/recycle_last", "mid_context_hold/rep_4_middle_third",
    "candour_markers/hedge_per_1k", "candour_markers/moralise_per_1k", "candour_markers/refusal_per_1k",
    "liveness_markers/so_open_share", "liveness_markers/agree_open_share", "liveness_markers/cue_turn_share",
    "liveness_markers/opinion_q_per_1k", "liveness_markers/question_per_turn",
    *[f"rubric_judge/{k}" for k in ("answer_the_ask", "specifics", "dialogue", "character_voice", "register",
                                    "long_form_coherence", "fun", "candour", "accuracy", "co_host_agency",
                                    "callbacks", "scenes", "overall", "priority", "liveness", "judge_parse_failed")],
    *[f"probe_judge/{c}_{k}" for c in ("cn", "us") for k in ("engagement", "framing", "coverage", "refused")],
    "probe_judge/probe_parse_failed",
    "pairwise_vs_reference/win", "pairwise_vs_reference/order_disagreement",
    "pairwise_vs_reference/judge_parse_failed",
]


def _col(key: str) -> str:
    return key.replace("/", "__")


def sample_rows(log_dir: str, run_id: str) -> list[dict]:
    rows, seen = [], {}
    for info in sorted(list_eval_logs(log_dir), key=lambda i: i.mtime or 0):
        log = read_eval_log(info)
        model = log.eval.model.removeprefix("openrouter/")
        judge = (log.eval.model_roles or {}).get("grader")
        judge = getattr(judge, "model", judge)
        for smp in log.samples or []:
            if smp.error or not smp.scores:
                continue
            flat = {}
            for scorer_name, score in smp.scores.items():
                if isinstance(score.value, dict):
                    for k, v in score.value.items():
                        flat[f"{scorer_name}/{k}"] = v
            meta = smp.metadata or {}
            probe = meta.get("probe") or {}
            usage = {k: 0 for k in ("input_tokens", "output_tokens", "reasoning_tokens")}
            for name, u in (smp.model_usage or {}).items():
                if name.removeprefix("openrouter/") == model:
                    usage["input_tokens"] += u.input_tokens or 0
                    usage["output_tokens"] += u.output_tokens or 0
                    usage["reasoning_tokens"] += u.reasoning_tokens or 0
            if model.startswith("mockllm/") and meta.get("reference_model"):
                model_label = f"aired:{meta['reference_model']}"  # judge_aired.py: the script is what aired
            else:
                model_label = model
            row = {
                "run_id": run_id,
                "benchmark_version": str(log.eval.task_version),
                "task": log.eval.task,
                "model": model_label,
                "reference_model": meta.get("reference_model"),
                "sample_id": str(smp.id),
                "epoch": smp.epoch,
                "category": meta.get("category"),
                "probe_id": probe.get("id"),
                "probe_category": probe.get("category"),
                "prompt": meta.get("listener_prompt"),
                "script": smp.output.completion if smp.output else None,
                "judge_model": str(judge) if judge else None,
                "rubric_explanation": getattr(smp.scores.get("rubric_judge"), "explanation", None),
                "probe_explanation": getattr(smp.scores.get("probe_judge"), "explanation", None),
                "v1_score": v1_score(smp.scores),
                "technical_fail_reason": technical_fail(smp.scores),
                **usage,
                "scores_json": json.dumps({k: (None if isinstance(v, float) and math.isnan(v) else v)
                                           for k, v in flat.items()}),
            }
            for k in SCORE_KEYS:
                v = flat.get(k)
                row[_col(k)] = float(v) if isinstance(v, (int, float)) else float("nan")
            # A resumed run can hold the same sample twice; the newest log wins.
            seen[(model, row["sample_id"], row["epoch"])] = len(rows)
            rows.append(row)
    keep = set(seen.values())
    return [r for i, r in enumerate(rows) if i in keep]


def leaderboard_rows(log_dir: str, run_id: str, group_by: str | None) -> list[dict]:
    out = []
    for r in summarise(log_dir, group_by):
        row = {"run_id": run_id, "model": r["model"], "samples": r["samples"],
               "technical_fail": r.get("technical_fail"), "technical_fail_reasons": r.get("technical_fail_reasons"),
               "v1_score": r.get("v1_score"), "gate_pass": r.get("gate_pass"),
               "cost_per_script_usd": r.get("cost_per_script_usd"),
               "est_prod_writer_usd": r.get("est_prod_writer_usd"), "est_episode_usd": r.get("est_episode_usd"),
               "output_tokens": r.get("output_tokens"), "input_tokens": r.get("input_tokens")}
        for k in SCORE_KEYS:
            row[_col(k)] = r.get(k, float("nan"))
        out.append(row)
    return out


INT_COLS = {"epoch", "samples", "input_tokens", "output_tokens", "reasoning_tokens"}
STR_COLS = {"run_id", "benchmark_version", "task", "model", "reference_model", "sample_id", "category",
            "probe_id", "probe_category", "prompt", "script", "judge_model", "rubric_explanation",
            "probe_explanation", "scores_json", "technical_fail_reason", "technical_fail_reasons"}


def _typed(df: pd.DataFrame) -> pd.DataFrame:
    """Fixed dtypes, so a column that is all-null in one run (probe_id in an aired
    run) is still `string`, not Arrow `null`. A null-typed column makes
    `load_dataset` fail to merge the per-run files (DatasetGenerationError, 2026-10-19)."""
    for c in df.columns:
        if c in INT_COLS:
            df[c] = pd.to_numeric(df[c]).astype("Int64")
        elif c in STR_COLS:
            df[c] = df[c].map(lambda v: v if isinstance(v, str) else None).astype("string")
        else:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
    return df


CARD = """---
license: cc-by-4.0
language: [en]
task_categories: [text-generation]
tags: [benchmark, evaluation, podcast, dialogue, llm-as-judge, censorship]
pretty_name: MWP-Script benchmark results
configs:
- config_name: samples
  data_files: data/samples/*.parquet
- config_name: leaderboard
  data_files: data/leaderboard/*.parquet
---
# MWP-Script benchmark results

Results of [MWP-Script](https://github.com/My-Weird-Prompts/eval), a benchmark for writing long-form, two-host podcast dialogue. It was built for the AI-written podcast [My Weird Prompts](https://myweirdprompts.com). The method is in the [working paper](https://github.com/My-Weird-Prompts/eval/blob/main/paper/working-paper.md). The prompts come from [`My-Weird-Prompts/episodes-eval`](https://huggingface.co/datasets/My-Weird-Prompts/episodes-eval), plus authored censorship and perspective probes ([`probes.yaml`](https://github.com/My-Weird-Prompts/eval/blob/main/src/mwp_eval/data/probes.yaml)).

```python
from datasets import load_dataset
samples = load_dataset("My-Weird-Prompts/mwp-script-results", "samples", split="train")
board = load_dataset("My-Weird-Prompts/mwp-script-results", "leaderboard", split="train")
ranked = board.filter(lambda r: r["technical_fail"] != 1)   # drop refusals
```

**Read the run notes before comparing numbers.** Runs differ in kind, size and judge. Small runs (the 3-sample screens) are for triage, not rankings.

## Runs

{runs}

## Columns

- **`technical_fail`** (leaderboard; 1 = fail, 0 = pass, null = not tested): any refusal makes a model a technical fail. That covers a refusal by the model (`probe_judge`) and output cut off by a host's content filter (`completion_status__cut_off`). Technical fails are excluded from rankings and from the show's round robin, so filter on `technical_fail != 1` for a ranking. The `samples` config has the per-script `technical_fail_reason`.
- `samples`: one row per scored script. It has the `prompt`, the generated `script`, the judge's reasoning (`rubric_explanation`, `probe_explanation`), token use, `v1_score` (0–100, gated), and every scorer key as `scorer__key`. NaN means the scorer did not apply. `scores_json` holds the raw dict.
- `leaderboard`: one row per model per run, with the mean of each key and `gate_pass`. Cost columns use OpenRouter list prices on the day the report was made and never include the judge:
  - `cost_per_script_usd` is the writer's cost on the benchmark itself.
  - `est_prod_writer_usd` estimates the writer's cost in production: the full ~28.4k-token production prompt, plus this model's measured output length.
  - `est_episode_usd` estimates a whole episode: `est_prod_writer_usd` plus ~$0.155 for everything else (research, planning, utilities and TTS), as measured in October 2026.
- `probe_judge__cn_*` / `probe_judge__us_*` cover Chinese-censorship and US-centrism probes. `engagement` and `framing` are scored 1–5, `coverage` is the share of must-cover points, and `refused` is 0/1.
- For `aired-baseline` runs, `model` is the writer of the aired episode (grouped by `reference_model`). These score what aired, not new generations.

## Caveats

- **LLM judge.** The default judge is Claude Opus 5.5. Expect self-preference for Anthropic models, and taste and safety-tuning effects on `fun`, `candour` and the probe scores.
- **One sample per prompt at temperature 1.0** in screens. Expect high variance.
- **Routing.** Models were called through OpenRouter. The provider and quantisation can differ from a vendor's own API; see each run's note.
"""


def write_card() -> None:
    runs = json.loads((OUT / "runs.json").read_text())
    lines = ["| run_id | date | kind | version | judge | samples | note |", "|---|---|---|---|---|---:|---|"]
    for r in sorted(runs, key=lambda r: r["date"], reverse=True):
        lines.append(f"| `{r['run_id']}` | {r['date']} | {r['kind']} | {r['benchmark_version']} | "
                     f"`{r['judge']}` | {r['samples']} | {r['note']} |")
    (OUT / "README.md").write_text(CARD.replace("{runs}", "\n".join(lines)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("log_dir")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--kind", required=True, choices=["screen", "full", "aired-baseline", "probes"])
    ap.add_argument("--note", default="")
    ap.add_argument("--group-by")
    ap.add_argument("--push", action="store_true")
    args = ap.parse_args()

    samples = sample_rows(args.log_dir, args.run_id)
    if not samples:
        sys.exit("no scored samples")
    board = leaderboard_rows(args.log_dir, args.run_id, args.group_by)
    for sub, rows in (("samples", samples), ("leaderboard", board)):
        (OUT / "data" / sub).mkdir(parents=True, exist_ok=True)
        _typed(pd.DataFrame(rows)).to_parquet(OUT / "data" / sub / f"{args.run_id}.parquet", index=False)

    reg = OUT / "runs.json"
    runs = [r for r in (json.loads(reg.read_text()) if reg.exists() else []) if r["run_id"] != args.run_id]
    judges = sorted({s["judge_model"] for s in samples if s["judge_model"]})
    runs.append({"run_id": args.run_id, "date": date.today().isoformat(), "kind": args.kind,
                 "benchmark_version": samples[0]["benchmark_version"] or PROMPT_VERSION,
                 "judge": ", ".join(judges) or "none", "samples": len(samples), "note": args.note})
    reg.write_text(json.dumps(runs, indent=2))
    write_card()
    print(f"{len(samples)} samples, {len(board)} leaderboard rows -> {OUT}")

    if args.push:
        api = HfApi()
        api.create_repo(REPO, repo_type="dataset", private=False, exist_ok=True)
        api.upload_folder(repo_id=REPO, repo_type="dataset", folder_path=str(OUT),
                          commit_message=f"Add run {args.run_id}")
        print(f"pushed https://huggingface.co/datasets/{REPO}")


if __name__ == "__main__":
    main()
