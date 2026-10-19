"""Leaderboard from an eval log directory.

    python scripts/report.py logs/2026-10-19            # markdown table to stdout
    python scripts/report.py logs/2026-10-19 --json out.json

One row per model: the V1 headline score (`v1_score`, defined in
`v1_score()` below and in the working paper §5), the mean of every scorer
sub-measure, and cost and token use. Reads the logs only; never calls a model.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import urllib.request

from inspect_ai.log import list_eval_logs, read_eval_log

_PRICES: dict | None = None


def _price(model_id: str) -> tuple[float, float] | None:
    """($/token in, $/token out) from OpenRouter's public model list, fetched once.

    Inspect doesn't receive a cost back from OpenRouter, so cost is rebuilt from
    tokens x list price on the day the report is made. That ignores provider
    routing and peak-hour pricing (DeepSeek doubles at peak), so it's a list-price
    comparison, not an invoice.
    """
    global _PRICES
    if _PRICES is None:
        try:
            with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as r:
                _PRICES = {m["id"]: m.get("pricing", {}) for m in json.load(r)["data"]}
        except Exception:
            _PRICES = {}
    p = _PRICES.get(model_id)
    try:
        return float(p["prompt"]), float(p["completion"])
    except (TypeError, KeyError, ValueError):
        return None

# Estimated production cost per episode (monorepo PLAN-034, measured 2026-10-18):
# a pipeline episode costs about $0.16 in total, of which the writer is $0.0051
# (28.4k tokens in, 5.6k out on DeepSeek). Everything else (research, Exa,
# planner, utilities, TTS GPU) is held fixed at the difference. In production
# the writer reads the full ~28.4k-token prompt, not V1's ~1.4k task card, so
# the estimate prices PROD_WRITER_INPUT_TOKENS of input plus the model's OWN
# measured output tokens per script (reasoning tokens bill as output).
EPISODE_TOTAL_USD = 0.16
BASELINE_WRITER_USD = 0.0051
NON_WRITER_USD = EPISODE_TOTAL_USD - BASELINE_WRITER_USD
PROD_WRITER_INPUT_TOKENS = 28_400


def technical_fail(scores: dict) -> str | None:
    """Why this sample is a technical fail, or None. A refusal of any kind is one.

    Daniel's hard rule (2026-10-19, plans/003-refusal-rule.md): a model with a
    technical fail on any sample is excluded from the production round robin
    and is filtered out of benchmark write-ups as `technical_fail`, whatever its
    other scores. Reasons:

    * `refused`: the probe judge marked the script a refusal (`probe_judge/*_refused`).
    * `provider_filter`: the host cut the output off mid-stream
      (`completion_status/cut_off`, e.g. Alibaba DataInspectionFailed).

    Computed from logged scores, so older logs get it without re-scoring.
    """
    reasons = []
    probe = scores.get("probe_judge")
    if probe and isinstance(probe.value, dict) and any(
            probe.value.get(f"{c}_refused") == 1.0 for c in ("cn", "us")):
        reasons.append("refused")
    status = scores.get("completion_status")
    if status and isinstance(status.value, dict) and status.value.get("cut_off") == 1.0:
        reasons.append("provider_filter")
    return "+".join(reasons) or None


# Gate for the headline score: a script the show could not air scores 0.
GATE_LENGTH = (0.8, 1.2)


def v1_score(scores: dict) -> float | None:
    """Per-sample headline score, 0-100. None when the judge did not score it.

    `rubric_judge/priority` (1-5, mean of long_form_coherence, fun, candour)
    rescaled to 0-100, or 0 when the script fails the gate: unparseable for
    TTS, more than 20% off the target length, or cut off mid-generation
    (`completion_status/cut_off`, v1.1). Pairwise win rate is reported
    alongside, not folded in (working paper §5).
    """
    fmt = scores.get("format_and_length")
    rub = scores.get("rubric_judge")
    if not fmt or not rub or not isinstance(rub.value, dict):
        return None
    priority = rub.value.get("priority")
    if priority is None or math.isnan(priority) or rub.value.get("judge_parse_failed"):
        return None
    return 25.0 * (priority - 1.0) if _gated(scores) else 0.0


# Column order and direction for the markdown table; JSON carries everything.
COLUMNS = [
    ("v1_score", "V1 score", "high"),
    ("gate_pass", "gate pass", "high"),
    ("completion_status/cut_off", "cut off", "low"),
    ("rubric_judge/priority", "priority", "high"),
    ("rubric_judge/long_form_coherence", "mid hold", "high"),
    ("rubric_judge/fun", "fun", "high"),
    ("rubric_judge/candour", "candour", "high"),
    ("rubric_judge/liveness", "liveness", "high"),
    ("rubric_judge/co_host_agency", "co-host", "high"),
    ("rubric_judge/callbacks", "callbacks", "high"),
    ("rubric_judge/overall", "judge", "high"),
    ("mid_context_hold/recycle_middle", "recycle mid", "low"),
    ("candour_markers/moralise_per_1k", "moralise/1k", "low"),
    ("candour_markers/refusal_per_1k", "refusal/1k", "low"),
    ("pairwise_vs_reference/win", "win vs aired", "high"),
    ("pairwise_vs_reference/order_disagreement", "judge order flip", "low"),
    ("format_and_length/parse_ok", "parse ok", "high"),
    ("format_and_length/length_ratio", "len ratio", "1"),
    ("repetition_and_tics/rep_4", "rep_4", "low"),
    ("repetition_and_tics/echo_last_decile", "echo last 10%", "low"),
    ("repetition_and_tics/adjacent_turn_similarity_mean", "adj sim", "low"),
    ("repetition_and_tics/tic_per_1k_named", "tics/1k", "low"),
]


def summarise(log_dir: str, group_by: str | None = None) -> list[dict]:
    """One row per model, built from the per-sample scores.

    Built from samples rather than `log.results`, so a log that errored at the
    final reduction still reports what it scored. NaN means "not applicable"
    and is skipped. Errored samples
    are left out. When a model has several logs (a resumed run), every sample
    in them counts, de-duplicated by (sample id, epoch) with the newest log
    winning. `n_<scorer>` is how many samples contributed to each mean.
    """
    by_model: dict[str, dict] = {}
    for info in sorted(list_eval_logs(log_dir), key=lambda i: i.mtime or 0):
        log = read_eval_log(info)
        model = log.eval.model.removeprefix("openrouter/")
        entry = by_model.setdefault(model, {"samples": {}, "usage": defaultdict(int), "status": set()})
        entry["status"].add(log.status)
        for smp in log.samples or []:
            if smp.error or not smp.scores:
                continue
            entry["samples"][(smp.id, smp.epoch)] = smp
    if group_by:
        # Regroup by a sample metadata key (e.g. reference_model for judge_aired.py runs).
        regrouped: dict[str, dict] = {}
        for entry in by_model.values():
            for key, smp in entry["samples"].items():
                g = regrouped.setdefault(str(smp.metadata.get(group_by)),
                                         {"samples": {}, "status": entry["status"]})
                g["samples"][key] = smp
        by_model = regrouped
    rows = []
    for model, entry in by_model.items():
        vals: dict[str, list[float]] = defaultdict(list)
        usage = defaultdict(int)
        fails: list[str] = []
        for smp in entry["samples"].values():
            for scorer_name, score in smp.scores.items():
                if isinstance(score.value, dict):
                    for k, v in score.value.items():
                        if isinstance(v, (int, float)) and not math.isnan(v):
                            vals[f"{scorer_name}/{k}"].append(float(v))
            headline = v1_score(smp.scores)
            if headline is not None:
                vals["v1_score"].append(headline)
            if "format_and_length" in smp.scores:
                vals["gate_pass"].append(1.0 if _gated(smp.scores) else 0.0)
            fail = technical_fail(smp.scores)
            if fail:
                fails.append(f"{smp.id}:{fail}")
            for model_name, u in (smp.model_usage or {}).items():
                if model_name.removeprefix("openrouter/") == model:
                    usage["input_tokens"] += u.input_tokens
                    usage["output_tokens"] += u.output_tokens
        # Probed = at least one sample could have been judged a refusal or cut off.
        probed = any("probe_judge" in smp.scores or "completion_status" in smp.scores
                     for smp in entry["samples"].values())
        row = {"model": model, "status": "+".join(sorted(entry["status"])), "samples": len(entry["samples"]),
               "technical_fail": (1.0 if fails else 0.0) if probed else None,
               "technical_fail_reasons": "; ".join(sorted(fails)) or None}
        for k, v in vals.items():
            row[k] = sum(v) / len(v)
            if len(v) > 1:
                sd = math.sqrt(sum((x - row[k]) ** 2 for x in v) / (len(v) - 1))
                row[f"{k}_stderr"] = sd / math.sqrt(len(v))
            row[f"n_{k}"] = len(v)
        row.update(usage)
        price = _price(model)
        if price and row["samples"]:
            row["cost_usd"] = usage["input_tokens"] * price[0] + usage["output_tokens"] * price[1]
            row["cost_per_script_usd"] = row["cost_usd"] / row["samples"]
            out_per_script = usage["output_tokens"] / row["samples"]
            row["est_prod_writer_usd"] = PROD_WRITER_INPUT_TOKENS * price[0] + out_per_script * price[1]
            row["est_episode_usd"] = NON_WRITER_USD + row["est_prod_writer_usd"]
        rows.append(row)
    return rows


def _gated(scores: dict) -> bool:
    fmt = scores["format_and_length"].value
    ratio = fmt.get("length_ratio", float("nan"))
    status = scores.get("completion_status")
    cut = status is not None and status.value.get("cut_off") == 1.0
    return fmt.get("parse_ok") == 1.0 and GATE_LENGTH[0] <= ratio <= GATE_LENGTH[1] and not cut


def _lookup(row: dict, key: str):
    return row.get(key)


def markdown(rows: list[dict]) -> str:
    head = ["model", "n", "TECH FAIL", *[c[1] for c in COLUMNS], "out tok/script", "$/script", "est $/episode"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    ok = [r for r in rows if r.get("samples")]
    # Technical fails sink to the bottom whatever they scored.
    ok.sort(key=lambda r: (r.get("technical_fail") == 1.0, -(_lookup(r, "v1_score") or 0)))
    for r in ok:
        tf = r.get("technical_fail")
        cells = [r["model"], str(r["samples"]),
                 "—" if tf is None else f"**FAIL** ({r['technical_fail_reasons']})" if tf else "pass"]
        for key, _, _ in COLUMNS:
            v = _lookup(r, key)
            cells.append("—" if v is None else f"{v:.3f}" if abs(v) < 10 else f"{v:.0f}")
        cells.append(str(round(r["output_tokens"] / r["samples"])) if r.get("output_tokens") else "—")
        cells.append(f"{r['cost_per_script_usd']:.4f}" if r.get("cost_per_script_usd") else "—")
        cells.append(f"{r['est_episode_usd']:.3f}" if r.get("est_episode_usd") else "—")
        lines.append("| " + " | ".join(cells) + " |")
    for r in rows:
        if not r.get("samples") or r.get("status") != "success":
            lines.append(f"\n- `{r['model']}`: {r.get('samples', 0)} scored samples, log status {r['status']}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("log_dir")
    ap.add_argument("--json")
    ap.add_argument("--group-by", help="sample metadata key to group rows by instead of model")
    args = ap.parse_args()
    rows = summarise(args.log_dir, args.group_by)
    print(markdown(rows))
    if args.json:
        Path(args.json).write_text(json.dumps(rows, indent=2, default=str))


if __name__ == "__main__":
    main()
