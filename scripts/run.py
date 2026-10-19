"""Run MWP-Script V1 across the roster in models.yaml.

Uses Inspect's `eval_set`, so a re-run with the same --log-dir resumes: models
and samples that already finished are not regenerated or re-billed.

    python scripts/run.py --model deepseek/deepseek-v4.1-flash-1017 --limit 2   # smoke test
    python scripts/run.py --tag v1                      # lite subset (40 prompts)
    python scripts/run.py --tag v1 --subset full        # all 189 prompts
    python scripts/run.py --model z-ai/glm-5.3 --no-pairwise
    python scripts/run.py --tag v1 --epochs 3           # variance across samples

Offline check, no API key and no spend:

    python scripts/run.py --model mockllm/model --no-judge --no-pairwise --limit 2

Needs OPENROUTER_API_KEY (environment or .env).
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import yaml
from dotenv import load_dotenv
from inspect_ai import eval_set
from inspect_ai.model import GenerateConfig, get_model

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mwp_eval.task import mwp_script_v1  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", action="append", help="roster tag(s) to include")
    ap.add_argument("--model", action="append", help="explicit OpenRouter id(s)")
    ap.add_argument("--subset", choices=["lite", "full", "probes", "screen"], default="lite")
    ap.add_argument("--log-dir", default=str(ROOT / "logs" / date.today().isoformat()))
    ap.add_argument("--judge", help="override judge model (Inspect name, e.g. openrouter/...)")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--no-pairwise", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--max-connections", type=int, default=8)
    args = ap.parse_args()

    # override: a key in .env beats one already in the shell, so eval spend
    # lands on the key you meant it to.
    load_dotenv(ROOT / ".env", override=True)
    roster = yaml.safe_load((ROOT / "models.yaml").read_text())
    entries = roster["models"]
    if args.model:
        known = {e["id"]: e for e in entries}
        entries = [known.get(m, {"id": m, "args": {}}) for m in args.model]
    elif args.tag:
        entries = [e for e in entries if set(e.get("tags", [])) & set(args.tag)]
    if not entries:
        sys.exit("no models selected")

    # `config` is per-model GenerateConfig (e.g. reasoning_effort for a model
    # whose reasoning can't be turned off); `args` are provider model args.
    def name(model_id: str) -> str:
        # Bare ids are OpenRouter's; anything with a known Inspect provider prefix passes through.
        return model_id if model_id.split("/")[0] in ("mockllm", "openrouter", "hf", "vllm", "ollama") \
            else f"openrouter/{model_id}"

    models = [get_model(name(e["id"]), config=GenerateConfig(**(e.get("config") or {})),
                        **(e.get("args") or {})) for e in entries]
    judge = args.judge or roster["judge"]
    print(f"{len(models)} model(s) -> {args.log_dir}; judge {judge}")

    ok, _ = eval_set(
        mwp_script_v1(subset=args.subset, judge=not args.no_judge, pairwise=not args.no_pairwise),
        model=models,
        model_roles={"grader": judge},
        log_dir=args.log_dir,
        limit=args.limit,
        epochs=args.epochs,
        max_connections=args.max_connections,
        retry_attempts=3,
        fail_on_error=0.2,
    )
    print("complete" if ok else "incomplete — re-run the same command to resume")


if __name__ == "__main__":
    main()
