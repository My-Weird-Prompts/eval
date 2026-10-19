"""Run the censorship track (plans/004) on a roster from models.yaml.

    python scripts/run_censorship.py --tag pool                  # the production round robin
    python scripts/run_censorship.py --tag candidate --tag pool
    python scripts/run_censorship.py --model openai/gpt-5.6-luna --limit 5
    python scripts/report_censorship.py logs/censorship-<date>

Pool entries in models.yaml carry production's OpenRouter routing
(monorepo pipeline/llm/openrouter_client.py _MODEL_PROVIDER_ORDER), because the
hard rule is about what production would get. Resumable, like run.py.
Cost: generation for ~155 short answers plus ~155 cheap classifier calls per model.
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

from mwp_eval.censorship import CLASSIFIER_DEFAULT, censorship_short  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", action="append")
    ap.add_argument("--model", action="append")
    ap.add_argument("--splits", default="deccp,ccp,xstest")
    ap.add_argument("--classifier", default=CLASSIFIER_DEFAULT)
    ap.add_argument("--log-dir", default=str(ROOT / "logs" / f"censorship-{date.today().isoformat()}"))
    ap.add_argument("--limit", type=int)
    ap.add_argument("--max-connections", type=int, default=12)
    args = ap.parse_args()

    load_dotenv(ROOT / ".env", override=True)
    roster = yaml.safe_load((ROOT / "models.yaml").read_text())["models"]
    # The censorship section wins over earlier entries for the same id.
    by_id: dict[str, dict] = {}
    for e in roster:
        if args.tag and set(e.get("tags", [])) & set(args.tag):
            by_id[e["id"]] = e
    for m in args.model or []:
        by_id.setdefault(m, next((e for e in reversed(roster) if e["id"] == m), {"id": m, "args": {}}))
    if not by_id:
        sys.exit("no models selected")
    models = [get_model(e["id"] if e["id"].startswith("mockllm/") else f"openrouter/{e['id']}",
                        config=GenerateConfig(**(e.get("config") or {})), **(e.get("args") or {}))
              for e in by_id.values()]
    print(f"{len(models)} model(s) -> {args.log_dir}; classifier {args.classifier}")
    ok, _ = eval_set(censorship_short(splits=args.splits), model=models,
                     model_roles={"classifier": args.classifier}, log_dir=args.log_dir, limit=args.limit,
                     max_connections=args.max_connections, retry_attempts=3, fail_on_error=0.2)
    print("complete" if ok else "incomplete — re-run the same command to resume")


if __name__ == "__main__":
    main()
