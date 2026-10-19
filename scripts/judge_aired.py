"""Judge the scripts that aired with the V1 rubric: a baseline, no generation.

    python scripts/judge_aired.py                         # lite, Opus 5.5 rows excluded
    python scripts/judge_aired.py --subset full --limit 5
    python scripts/report.py logs/aired-lite --group-by reference_model

Only the judge is billed (one rubric call per script; about $0.09 with Claude
Opus 5.5 at $4/$20 per M, 2026-10-19). Writers in the judge's own family are
excluded by default to avoid self-preference. Resumable: re-run the same command.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
from inspect_ai import eval_set

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mwp_eval.task import mwp_script_v1_aired  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subset", choices=["lite", "full"], default="lite")
    ap.add_argument("--judge", help="override judge model (Inspect name)")
    ap.add_argument("--exclude", default="anthropic/claude-opus-5.5",
                    help="comma-separated writer_model values to skip")
    ap.add_argument("--log-dir")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--max-connections", type=int, default=6)
    args = ap.parse_args()

    load_dotenv(ROOT / ".env", override=True)
    judge = args.judge or yaml.safe_load((ROOT / "models.yaml").read_text())["judge"]
    log_dir = args.log_dir or str(ROOT / "logs" / f"aired-{args.subset}")
    ok, _ = eval_set(
        mwp_script_v1_aired(subset=args.subset, exclude_writers=args.exclude),
        model="mockllm/model",
        model_roles={"grader": judge},
        log_dir=log_dir,
        limit=args.limit,
        max_connections=args.max_connections,
        retry_attempts=3,
        fail_on_error=0.2,
    )
    print("complete" if ok else "incomplete — re-run the same command to resume")


if __name__ == "__main__":
    main()
