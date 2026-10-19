"""Build pairwise preference items for the private preference Space (plans/002).

    python scripts/build_preference_items.py logs/screen-2026-10-19 --out build/preference/items-screen-2026-10-19.jsonl
    python scripts/build_preference_items.py logs/screen-2026-10-19 --push   # upload to the private bucket

For every prompt in the log dir, every pair of models that wrote a usable script
(models with any technical fail are left out entirely) becomes items of two kinds:

* `opening`: the first ~OPENING_WORDS words, cut at a turn boundary. Openings
  are aligned by construction (same prompt, same start), so they are quick to
  compare. They say nothing about holding the middle.
* `full_script`: the whole script. Slow to rate; use for finalists.

When the prompt has an aired episode (dataset rows), the aired script joins the
pool as model `aired:<writer>`. Aligned mid-script comparisons need generated
continuations, a separate builder (plans/002, step 2).

Items go to the private Storage Bucket My-Weird-Prompts/mwp-preference under
items/. Nothing is uploaded without --push.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

from huggingface_hub import batch_bucket_files
from inspect_ai.log import list_eval_logs, read_eval_log

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from report import technical_fail  # noqa: E402

BUCKET = "My-Weird-Prompts/mwp-preference"
OPENING_WORDS = 400


def opening(script: str, words: int = OPENING_WORDS) -> str:
    out, n = [], 0
    for line in script.strip().splitlines():
        out.append(line)
        n += len(line.split())
        if n >= words and line.strip():
            break
    return "\n".join(out)


def scripts_by_prompt(log_dir: str) -> dict[str, dict]:
    by: dict[str, dict] = {}
    logs = [read_eval_log(i) for i in list_eval_logs(log_dir)]
    # A technical fail on any sample removes the model entirely (plans/003).
    failed = {log.eval.model for log in logs for s in log.samples or [] if technical_fail(s.scores or {})}
    for log in logs:
        if log.eval.model in failed:
            continue
        model = log.eval.model.removeprefix("openrouter/")
        for s in log.samples or []:
            if s.error or not s.output:
                continue
            text = s.output.completion or ""
            if len(text.split()) < 800:
                continue
            p = by.setdefault(str(s.id), {"prompt": s.metadata.get("listener_prompt", ""), "scripts": {}})
            p["scripts"][model] = text
            ref = s.metadata.get("reference_script")
            if ref:
                p["scripts"][f"aired:{s.metadata.get('reference_model')}"] = ref
    return by


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("log_dir")
    ap.add_argument("--out")
    ap.add_argument("--kinds", default="opening,full_script")
    ap.add_argument("--push", action="store_true")
    args = ap.parse_args()
    run = Path(args.log_dir).name
    out = Path(args.out or ROOT / "build" / "preference" / f"items-{run}.jsonl")
    items = []
    for prompt_id, p in sorted(scripts_by_prompt(args.log_dir).items()):
        for (ma, ta), (mb, tb) in itertools.combinations(sorted(p["scripts"].items()), 2):
            for kind in args.kinds.split(","):
                cut = opening if kind == "opening" else (lambda t: t.strip())
                items.append({
                    "pair_id": f"{run}--{prompt_id}--{kind}--{ma}--{mb}".replace("/", "_").replace(":", "_"),
                    "kind": kind, "prompt": p["prompt"], "context": "",
                    "a": {"model": ma, "text": cut(ta)}, "b": {"model": mb, "text": cut(tb)},
                    "meta": {"run": run, "prompt_id": prompt_id},
                })
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(i) + "\n" for i in items))
    print(f"{len(items)} items -> {out}")
    if args.push:
        batch_bucket_files(BUCKET, add=[(str(out), f"items/{out.name}")])
        print(f"uploaded to hf://buckets/{BUCKET}/items/{out.name}")


if __name__ == "__main__":
    main()
