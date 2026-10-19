"""Perspective-lens report (plans/005): American centrism and Israel/Palestine framing.

    python scripts/report_bias.py logs/bias-<date> [--json out.json]

Per model:
* **American-centrism index**: mean 0-3 judge score on the 38 location-neutral
  prompts (0 = no US default; Dan-Eval rubric). Also the share of answers that
  asked where the user is or covered several countries, and the mean score on the
  10 location-cue controls (should be about 0: can it move off the default when told?).
* **Israel/Palestine framing**: mean 0-3 lean score, mean signed lean
  (-1 pro-Palestinian … +1 pro-Israel), refusal rate, and refusal asymmetry
  between the pro-Israel- and pro-Palestinian-framed halves of the 18 mirrored pairs.

Graded, not pass/fail, until thresholds are calibrated (docs/selection-criteria.md).
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log


def mean(xs):
    xs = [x for x in xs if x == x]
    return sum(xs) / len(xs) if xs else math.nan


def summarise(log_dir: str) -> list[dict]:
    by = defaultdict(list)
    for info in sorted(list_eval_logs(log_dir), key=lambda i: i.mtime or 0):
        log = read_eval_log(info)
        model = log.eval.model.removeprefix("openrouter/")
        for s in log.samples or []:
            sc = (s.scores or {}).get("bias_lens")
            if s.error or not sc or sc.value.get("judge_parse_failed"):
                continue
            by[model].append((s.metadata, sc.value))
    rows = []
    for model, items in by.items():
        amc = [v for m, v in items if m["split"] == "amc" and not m.get("is_control")]
        ctl = [v for m, v in items if m["split"] == "amc" and m.get("is_control")]
        ipf = [(m, v) for m, v in items if m["split"] == "ipf"]
        ref = lambda fr: mean([v["ipf_refused"] for m, v in ipf if m.get("framing") == fr])
        rows.append({
            "model": model, "n": len(items),
            "amc_index": mean([v["amc_score"] for v in amc]),
            "amc_asked_or_global": mean([v["amc_asked_location"] for v in amc]),
            "amc_control": mean([v["amc_control_score"] for v in ctl]),
            "ipf_score": mean([v["ipf_score"] for _, v in ipf]),
            "ipf_lean": mean([v["ipf_lean"] for _, v in ipf]),
            "ipf_refused": mean([v["ipf_refused"] for _, v in ipf]),
            "ipf_refusal_asymmetry": ref("pro_israel") - ref("pro_palestinian"),
            "cut_off": sum(v["cut_off"] == 1.0 for _, v in items),
        })
    rows.sort(key=lambda r: (r["amc_index"] if r["amc_index"] == r["amc_index"] else 9))
    return rows


def markdown(rows: list[dict]) -> str:
    f = lambda v, p=2: "—" if v is None or v != v else f"{v:.{p}f}"
    lines = ["| model | n | US-centrism index (0-3, ↓) | asked / global | controls (↓) | IL/PS lean score (0-3, ↓) "
             "| signed lean (−1 pro-PS … +1 pro-IL) | IL/PS refused | refusal asymmetry (IL−PS framing) | cut off |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        lines.append(f"| {r['model']} | {r['n']} | {f(r['amc_index'])} | {f(r['amc_asked_or_global'])} | "
                     f"{f(r['amc_control'])} | {f(r['ipf_score'])} | {f(r['ipf_lean'])} | {f(r['ipf_refused'])} | "
                     f"{f(r['ipf_refusal_asymmetry'])} | {r['cut_off']} |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("log_dir")
    ap.add_argument("--json")
    args = ap.parse_args()
    rows = summarise(args.log_dir)
    print(markdown(rows))
    if args.json:
        Path(args.json).write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
