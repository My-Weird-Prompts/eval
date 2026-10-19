"""Printable reading copy of a bakeoff: run → prompt → model → script, as a PDF.

    python scripts/build_bakeoff_pdf.py logs/bakeoff-2026-10-19 \
        --order openai/gpt-6.1-sol,meta/muse-spark-1.3,x-ai/grok-4.7,google/gemini-3.8-flash,openai/gpt-6-luna

Writes reports/<run>.json (the scripts, word counts and judge scores) and
reports/<run>.pdf via Typst (reports/bakeoff.typ; needs `typst` and the Inter
and Libertinus Serif fonts). Each run opens with the prompt; each script starts
on a new page; the footer shows run, model and page number. Judge scores sit in
an appendix at the end, so they don't steer the reader.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log

ROOT = Path(__file__).resolve().parents[1]
NAMES = {"openai/gpt-6.1-sol": "GPT-6.1 Sol", "meta/muse-spark-1.3": "Muse Spark 1.3", "x-ai/grok-4.7": "Grok 4.7",
         "google/gemini-3.8-flash": "Gemini 3.8 Flash", "openai/gpt-6-luna": "GPT-6 Luna"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("log_dir")
    ap.add_argument("--order", help="comma-separated model ids, in reading order")
    ap.add_argument("--title", default="MWP script bakeoff")
    ap.add_argument("--date", default="19 October 2026")
    args = ap.parse_args()
    by, prompts, order = {}, {}, []
    for info in list_eval_logs(args.log_dir):
        log = read_eval_log(info)
        m = log.eval.model.removeprefix("openrouter/")
        for s in log.samples or []:
            if s.error or not s.scores:
                continue
            sid = str(s.id)
            if sid not in prompts:
                prompts[sid] = s.metadata["listener_prompt"]
                order.append(sid)
            v = s.scores["rubric_judge"].value
            by.setdefault(sid, {})[m] = {
                "script": s.output.completion, "words": int(s.scores["format_and_length"].value["word_count"]),
                "scores": {k: v[k] for k in ("long_form_coherence", "fun", "candour", "priority", "liveness")}}
    models = args.order.split(",") if args.order else sorted({m for d in by.values() for m in d})
    runs = [{"run": n, "id": sid, "prompt": prompts[sid].strip(),
             "entries": [{"model": NAMES.get(m, m), "model_id": m, **by[sid][m]} for m in models if m in by[sid]]}
            for n, sid in enumerate(order, 1)]
    name = Path(args.log_dir).name
    out = ROOT / "reports" / f"{name}.json"
    out.write_text(json.dumps({"title": args.title, "date": args.date, "runs": runs}, indent=1, ensure_ascii=False))
    subprocess.run(["typst", "compile", "--input", f"data={out.name}", "bakeoff.typ", f"{name}.pdf"],
                   cwd=ROOT / "reports", check=True)
    print(ROOT / "reports" / f"{name}.pdf")


if __name__ == "__main__":
    main()
