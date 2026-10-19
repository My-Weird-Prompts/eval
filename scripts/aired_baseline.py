"""Deterministic V1 metrics on the AIRED scripts, per writer model. Free: no model calls.

    python scripts/aired_baseline.py                    # markdown to stdout
    python scripts/aired_baseline.py --json results/aired-deterministic.json

What the show actually aired, measured with the same deterministic scorers a
candidate gets. It is context, not a target: aired scripts were written from
the full production prompt (research, plan, cameo) and went through tic polish
and length correction, so they are not comparable 1:1 with raw V1 output.
Rows are the `full` V1 set (episodes with a published prompt).
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mwp_eval.liveness import liveness_markers  # noqa: E402
from mwp_eval.metrics import script_metrics  # noqa: E402
from mwp_eval.priorities import candour_markers, recycling  # noqa: E402
from mwp_eval.task import DATASET_REVISION, load_dataset  # noqa: E402

# Aired scripts can include the producer cameo and older guest characters, so
# every label that has spoken on the show opens a turn here.
AIRED_SPEAKERS = {"Corn", "Herman", "Hilbert", "Daniel", "Larry", "Jim"}

KEYS = ["word_count", "rep_4", "rep_4_last_third", "echo_last_decile", "tic_per_1k_named",
        "recycle_middle", "recycle_last", "moralise_per_1k", "so_open_share", "cue_turn_share",
        "question_per_turn"]


def measure(script: str) -> dict:
    m = script_metrics(script, AIRED_SPEAKERS)
    c = candour_markers(script, AIRED_SPEAKERS)
    c.pop("hits")
    return {**m, **recycling(script, AIRED_SPEAKERS), **c, **liveness_markers(script, AIRED_SPEAKERS)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    args = ap.parse_args()
    by_model: dict[str, list[dict]] = defaultdict(list)
    for s in load_dataset("full"):
        by_model[s.metadata["reference_model"]].append(measure(s.metadata["reference_script"]))
    rows = []
    for model, ms in sorted(by_model.items(), key=lambda kv: -len(kv[1])):
        row = {"writer_model": model, "n": len(ms)}
        for k in KEYS:
            vals = [m[k] for m in ms if m.get(k) is not None]
            row[k] = statistics.median(vals) if vals else None
        rows.append(row)
    print(f"Aired scripts, V1 full set, dataset revision {DATASET_REVISION[:7]}. Medians.\n")
    print("| writer_model | n | " + " | ".join(KEYS) + " |")
    print("|---|---:|" + "---:|" * len(KEYS))
    for r in rows:
        cells = ["—" if r[k] is None else f"{r[k]:.0f}" if k == "word_count" else f"{r[k]:.4f}" for k in KEYS]
        print(f"| `{r['writer_model']}` | {r['n']} | " + " | ".join(cells) + " |")
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps({"dataset_revision": DATASET_REVISION, "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
