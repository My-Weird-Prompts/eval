r"""Build results/leaderboard.json from the published result tables.

    python3 scripts/build_leaderboard.py           # write results/leaderboard.json
    python3 scripts/build_leaderboard.py --check   # exit 1 if the file is stale

Stdlib only. Sources, in order of authority:

* `results/README.md`: one `## \`<run-id>\`` section per run, each with a
  markdown table (one row per model). Extra tables in a section whose first
  column is `model` (e.g. the probe table in screen-2026-10-19) are merged
  into that run's rows under `extra`.
* `results/on-air-toast-2026-10-19/README.md`: the on-air mini-eval table.
* `results/aired-deterministic.json`: deterministic medians per aired writer.
* `results/aired-catalogue.json`: the objective track on the aired catalogue
  (`scripts/aired_catalogue.py`); one row per canonical writer, medians and IQRs
  in `extra`. Per-episode rows stay in that file for drill-down.
* `exclusions.json`: copied verbatim to `exclusions`; each row also gets the
  matching reason (exact id, or a `prefix*` / `prefix/` family key) as `exclusion`.
* `src/mwp_eval/prompt.py`: `PROMPT_VERSION`.

Run metadata that the tables don't carry (kind, judge, spend, version, a one-line
summary) lives in RUNS below. A new run = a new README section + a RUNS entry;
a README section with a table but no RUNS entry is still picked up, with its
first paragraph as the summary. Contract: monorepo PLAN-040 "Data contracts".
Fields a run didn't measure are null. `generated` only changes when the data
does, so a rebuild with no new results leaves the file untouched.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUT = RESULTS / "leaderboard.json"

OPUS = "anthropic/claude-opus-5.5"
HAIKU = "anthropic/claude-haiku-5.5"
DEEPSEEK_EPISODE_USD = 0.161  # measured production episode cost, DeepSeek writer (results/README.md)

CURRENT = {
    "writer": "openai/gpt-6.1-sol",
    "since": "2026-10-19",
    "decision": "144",
    "note": "GPT-6.1 Sol, reasoning effort low, writes every pipeline episode; randomiser off (monorepo decision 144).",
}

# Newest first (the README's order). `section` is the README heading id when it
# differs from run_id.
RUNS: list[dict] = [
    {
        "run_id": "aired-catalogue", "date": "2026-10-24", "kind": "aired-catalogue",
        "benchmark_version": None, "judge": None, "spend_usd": 0.0,
        "source": "results/aired-catalogue.json",
        "summary": "Objective track: ScriptBench's deterministic measures on up to 20 aired, pipeline-written scripts per canonical writer model "
                   "(public transcripts dataset), plus offline-only models as flagged rows. No judge, no spend. "
                   "Per-episode rows are in results/aired-catalogue.json.",
    },
    {
        "run_id": "on-air-toast-2026-10-19", "date": "2026-10-19", "kind": "on-air",
        "benchmark_version": None, "judge": None, "spend_usd": 0.01,
        "source": "results/on-air-toast-2026-10-19/README.md",
        "summary": "One toast prompt, one ~450-word sample per model, judged by the hosts on air, not by rubric. "
                   "Sol was the only fully correct script; DeepSeek and GPT-3.5 invented evidence; Haiku got the answer wrong. An anecdote, not a benchmark.",
    },
    {
        "run_id": "bakeoff-2026-10-19", "date": "2026-10-19", "kind": "bakeoff",
        "benchmark_version": "v1.1", "judge": OPUS, "spend_usd": 1.75,
        "summary": "Budget bakeoff: the five contenders wrote 3 ordinary lite prompts each (three-sample rule), rubric-judged by Opus 5.5. "
                   "GPT-6.1 Sol best (held the middle 4.0, on length 3/3); Muse Spark 1.3 the value pick; Grok 4.7 and Gemini 3.8 Flash the most fun but ~1.6x over length.",
        "pdf": "reports/bakeoff-2026-10-19.pdf",
    },
    {
        "run_id": "screen-2026-10-19b", "date": "2026-10-19", "kind": "screen",
        "benchmark_version": "v1.1", "judge": OPUS, "spend_usd": 2.68,
        "summary": "Second screen: the five candidates that passed censorship, 3 scripts each (one ordinary prompt plus the two probes). "
                   "Everyone engaged with both probes; length discipline decided the V1 score. GPT-5.6 Luna and Gemini 3.7 Flash were later superseded (rule H2).",
    },
    {
        "run_id": "censorship-2026-10-19", "date": "2026-10-19", "kind": "censorship",
        "benchmark_version": "c1.0", "judge": HAIKU, "spend_usd": 3.0,
        "summary": "Censorship track: the 10 round-robin models under production routing plus 7 candidates, ~155 short answers each (deccp, ccp, xstest), labelled by Claude Haiku 5.5. "
                   "7 of 10 round-robin models censor the topic; US and Western models answered every factual question. technical_fail here = the refined reading; the strict reading is in extra.strict.",
        "hf_dataset": "My-Weird-Prompts/mwp-censorship-results",
    },
    {
        "run_id": "screen-2026-10-19", "date": "2026-10-19", "kind": "screen",
        "benchmark_version": "v1.1", "judge": OPUS, "spend_usd": 3.10,
        "summary": "First long-tail screen: six unaired OpenRouter models plus the DeepSeek V4.1 Flash baseline, 3 scripts each (one ordinary prompt, cn-tiananmen, us-regime-change). "
                   "Chinese hosting providers cut Qwen and MiniMax off mid-stream; GPT-6.1 Sol was the only model on length every time.",
    },
    {
        "run_id": "aired-lite-2026-10-19", "section": "aired-judged-lite.json", "date": "2026-10-19", "kind": "aired-baseline",
        "benchmark_version": "v1.0", "judge": OPUS, "spend_usd": 2.96,
        "summary": "Rubric judge on 30 scripts that aired for the lite prompts (no generation). Too small to rank writers, and aired scripts had research, polish and length correction behind them. "
                   "Compare priority across writers, not V1 score. Opus-written episodes excluded (self-preference).",
    },
    {
        "run_id": "aired-deterministic", "date": "2026-10-19", "kind": "aired-baseline",
        "benchmark_version": "v1.0", "judge": None, "spend_usd": 0.0,
        "source": "results/aired-deterministic.json",
        "summary": "Free deterministic measures (word count, repetition, tics, echo) on the aired scripts behind all 189 V1 prompts, as medians per writer model. No judge, no scores.",
    },
]

# Table header (lower-cased, markdown stripped) -> contract field.
COLUMNS = {
    "model": "model", "writer": "model",
    "v1 score": "v1_score",
    "on length": "on_length", "gate pass": "on_length",
    "priority": "priority",
    "holds the middle": "mid_hold", "mid hold": "mid_hold",
    "fun": "fun", "candour": "candour", "liveness": "liveness",
    "len ratio": "len_ratio",
    "cost vs deepseek / episode": "cost_vs_baseline",
    "$/script": "usd_per_script", "cost usd": "usd_per_script",
    "est $/episode": "est_usd_per_episode",
    "technical fail": "technical_fail",
    "judge overall": "judge_overall",
    "n": "n",
    "factual verdict": "notes",
}

ROW_FIELDS = ["model", "v1_score", "on_length", "priority", "mid_hold", "fun", "candour", "liveness",
              "len_ratio", "cost_vs_baseline", "usd_per_script", "est_usd_per_episode", "judge_overall", "n",
              "technical_fail", "exclusion", "notes", "extra"]
NUMERIC = {"v1_score", "priority", "mid_hold", "fun", "candour", "liveness", "len_ratio", "usd_per_script",
           "est_usd_per_episode", "judge_overall", "n"}


def clean(cell: str) -> str:
    return re.sub(r"\*\*|`", "", cell).strip()


def number(cell: str) -> float | int | None:
    s = clean(cell).replace("~", "").replace("$", "").replace(",", "").rstrip("*").strip()
    pct = s.endswith("%")
    s = s.rstrip("%")
    try:
        v = float(s)
    except ValueError:
        return None
    if pct:
        return round(v / 100, 4)
    return int(v) if v.is_integer() and "." not in s else v


def snake(header: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", clean(header).lower()).strip("_")


def parse_tables(text: str) -> list[list[list[str]]]:
    """Every markdown table in `text` as a list of rows (header first, separator dropped)."""
    tables, cur = [], []
    for line in text.splitlines():
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            cur.append(cells)
        elif cur:
            tables.append(cur)
            cur = []
    if cur:
        tables.append(cur)
    return tables


def sections(md: str) -> dict[str, str]:
    """README sections keyed by the backticked id in their `## ` heading."""
    out = {}
    parts = re.split(r"^## ", md, flags=re.M)
    for part in parts[1:]:
        head, _, body = part.partition("\n")
        m = re.match(r"`([^`]+)`", head.strip())
        if m:
            out[m.group(1)] = body
    return out


def first_paragraph(body: str) -> str:
    for para in re.split(r"\n\s*\n", body):
        p = para.strip()
        if p and not p.startswith("|") and not p.startswith("#"):
            return re.sub(r"\s+", " ", re.sub(r"\*\*|`|\[([^\]]+)\]\([^)]+\)", lambda m: m.group(1) or "", p))
    return ""


def split_model(cell: str) -> tuple[str, str | None]:
    """`**`openai/x`** (baseline)` -> ("openai/x", "baseline")."""
    raw = re.sub(r"\*\*", "", cell).strip()
    m = re.match(r"`([^`]+)`\s*(.*)", raw)
    model, rest = (m.group(1), m.group(2)) if m else (raw.split(" (")[0], raw[len(raw.split(" (")[0]):])
    rest = rest.strip().strip("()").strip() or None
    return model.strip(), rest


def exclusion_for(model: str, exclusions: dict) -> str | None:
    if model in exclusions:
        return exclusions[model]
    best = None
    for key, reason in exclusions.items():
        if key.startswith("_"):
            continue
        prefix = key[:-1] if key.endswith("*") else key if key.endswith("/") else None
        if prefix and model.startswith(prefix) and (best is None or len(prefix) > len(best[0])):
            best = (prefix, reason)
    return best[1] if best else None


def rows_from_table(table: list[list[str]]) -> list[dict]:
    header = table[0]
    rows = []
    for cells in table[1:]:
        row: dict = {f: None for f in ROW_FIELDS}
        row["extra"] = {}
        notes = []
        for h, cell in zip(header, cells):
            key = clean(h).lower()
            field = COLUMNS.get(key)
            if field == "model":
                row["model"], note = split_model(cell)
                if note:
                    notes.append(note)
            elif field == "technical_fail":
                c = clean(cell)
                row["technical_fail"] = c.upper().startswith("FAIL")
                if ":" in c:
                    notes.append("technical fail: " + c.split(":", 1)[1].strip())
            elif field == "notes":
                notes.append(clean(cell))
            elif field == "on_length":
                row["on_length"] = clean(cell)
            elif field == "cost_vs_baseline":
                row["cost_vs_baseline"] = number(cell)
                if clean(cell).startswith("~"):
                    notes.append("cost vs baseline approximate")
            elif field in NUMERIC:
                row[field] = number(cell)
                if clean(cell).endswith("*"):
                    notes.append(f"{field}: see footnote in results/README.md")
            else:
                c = clean(cell)
                v = number(c)
                row["extra"][snake(h)] = v if v is not None and not re.search(r"[a-zA-Z/]", c) else c
        row["notes"] = "; ".join(notes) or None
        rows.append(row)
    return rows


def build_run(meta: dict, body: str | None, exclusions: dict) -> dict:
    run = {k: meta.get(k) for k in ("run_id", "date", "kind", "summary", "spend_usd", "judge", "benchmark_version")}
    for k in ("source", "pdf", "hf_dataset"):
        if meta.get(k):
            run[k] = meta[k]
    rid = meta["run_id"]
    if rid == "on-air-toast-2026-10-19":
        tables = parse_tables((RESULTS / "on-air-toast-2026-10-19" / "README.md").read_text())
        rows = rows_from_table(tables[0])
        for r in rows:
            r["extra"] = {("words" if k.startswith("words") else k): v for k, v in r["extra"].items()}
    elif rid == "aired-catalogue":
        data = json.loads((RESULTS / "aired-catalogue.json").read_text())
        run["dataset"] = data["dataset"]
        run["dataset_revision"] = data["dataset_revision"]
        run["caveat"] = data["caveat"]
        rows = []
        for d in data["models"]:
            row = {f: None for f in ROW_FIELDS}
            row["model"], row["n"] = d["model"], d["n"]
            row["len_ratio"] = d["length_ratio"]["median"]
            row["on_length"] = f"{round(d['on_length_rate'] * d['n'])}/{d['n']}"
            if d["written"] == "offline":
                row["notes"] = "written offline (Claude Code); the model never wrote a pipeline episode"
            extra = {k: d[k] for k in ("written", "first", "last", "available", "offline_episodes_excluded")}
            for k, v in d.items():
                if isinstance(v, dict) and "median" in v:
                    extra[k] = v["median"]
                    extra[f"{k}_iqr"] = [v["q1"], v["q3"]]
            extra["on_length_rate"] = d["on_length_rate"]
            extra["gate_pass_rate"] = d["parse_ok_rate"]
            row["extra"] = extra
            rows.append(row)
    elif rid == "aired-deterministic":
        data = json.loads((RESULTS / "aired-deterministic.json").read_text())
        run["dataset_revision"] = data.get("dataset_revision")
        rows = []
        for d in data["rows"]:
            row = {f: None for f in ROW_FIELDS}
            row["model"] = d["writer_model"]
            row["n"] = d.get("n")
            row["extra"] = {k: (round(v, 4) if isinstance(v, float) else v)
                            for k, v in d.items() if k not in ("writer_model", "n")}
            rows.append(row)
    else:
        tables = [t for t in parse_tables(body or "") if t and len(t) > 1]
        if not tables:
            raise SystemExit(f"{rid}: no table found in its README section")
        rows = rows_from_table(tables[0])
        by_model = {r["model"]: r for r in rows}
        for t in tables[1:]:  # side tables keyed by model (probes)
            if clean(t[0][0]).lower() != "model":
                continue
            for cells in t[1:]:
                model, _ = split_model(cells[0])
                if model in by_model:
                    for h, cell in zip(t[0][1:], cells[1:]):
                        by_model[model]["extra"][snake(h)] = clean(cell)

    for r in rows:
        if r["cost_vs_baseline"] is None and r["est_usd_per_episode"] is not None:
            r["cost_vs_baseline"] = round(r["est_usd_per_episode"] / DEEPSEEK_EPISODE_USD, 2)
        if rid == "censorship-2026-10-19":
            strict, refined = r["extra"].get("strict", ""), r["extra"].get("refined", "")
            r["technical_fail"] = refined.upper() == "FAIL"
            if strict.upper() == "FAIL" and refined.upper() != "FAIL":
                r["notes"] = "strict reading FAIL, refined pass"
        if run["kind"] == "aired-baseline" and isinstance(r["on_length"], str) and r["n"]:
            frac = number(r["on_length"])  # aired gate pass is a share, e.g. 0.80
            if frac is not None and frac <= 1:
                r["on_length"] = f"{round(frac * r['n'])}/{r['n']}"
        r["exclusion"] = exclusion_for(r["model"], exclusions)
        if not r["extra"]:
            r["extra"] = None
    run["rows"] = rows
    return run


def build() -> dict:
    md = (RESULTS / "README.md").read_text()
    secs = sections(md)
    exclusions = json.loads((ROOT / "exclusions.json").read_text())
    m = re.search(r'PROMPT_VERSION\s*=\s*"([^"]+)"', (ROOT / "src" / "mwp_eval" / "prompt.py").read_text())
    known = {r.get("section", r["run_id"]) for r in RUNS}
    runs = []
    for meta in RUNS:
        body = secs.get(meta.get("section", meta["run_id"]))
        if body is None and "source" not in meta:
            raise SystemExit(f"{meta['run_id']}: no `## \\`{meta.get('section', meta['run_id'])}\\`` section in results/README.md")
        runs.append(build_run(meta, body, exclusions))
    for sid, body in secs.items():  # sections without RUNS metadata
        if sid in known or not [t for t in parse_tables(body) if len(t) > 1]:
            continue
        d = re.search(r"\d{4}-\d{2}-\d{2}", sid)
        guess = next((k for k in ("bakeoff", "censorship", "screen", "aired") if k in sid), "screen")
        runs.insert(0, build_run({"run_id": sid, "date": d.group(0) if d else None,
                                  "kind": "aired-baseline" if guess == "aired" else guess,
                                  "summary": first_paragraph(body), "spend_usd": None, "judge": None,
                                  "benchmark_version": None}, body, exclusions))
    return {
        "generated": None,
        "benchmark_version": m.group(1) if m else None,
        "contract": "My-Weird-Prompts monorepo PLAN-040 (Data contracts); built by scripts/build_leaderboard.py",
        "current": CURRENT,
        "runs": runs,
        "exclusions": {k: v for k, v in exclusions.items() if not k.startswith("_")},
        "notes": {
            "technical_fail": "Any refusal by the model or a provider filter cut-off (plans/003-refusal-rule.md). Never rank a technical fail.",
            "v1_score": "25 x (priority - 1), gated on parse_ok and length ratio 0.8-1.2 (CHANGELOG v1.0). Comparable only within one benchmark_version.",
            "cost_vs_baseline": f"Production episode cost with this writer / DeepSeek V4.1 Flash episode (${DEEPSEEK_EPISODE_USD}). Computed from est_usd_per_episode where the run gave that instead.",
            "on_length": "Scripts that passed the length gate (screens: the whole gate, incl. parse and cut-off), as passed/total.",
            "aired_catalogue": "Run kind aired-catalogue: deterministic measures only, medians per writer in extra (with *_iqr), "
                               "len_ratio = median words/target, gate_pass_rate = TTS-format parse only. Different prompts per model; "
                               "repetition is length-dependent (r = 0.28); era flags, not a ranking. Per-episode rows: results/aired-catalogue.json.",
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if results/leaderboard.json is stale")
    args = ap.parse_args()
    data = build()
    old = json.loads(OUT.read_text()) if OUT.exists() else None
    if old is not None:
        data["generated"] = old.get("generated")
    if old == data:
        print(f"{OUT.relative_to(ROOT)} is up to date ({len(data['runs'])} runs)")
        return
    if args.check:
        print(f"{OUT.relative_to(ROOT)} is stale: run scripts/build_leaderboard.py", file=sys.stderr)
        sys.exit(1)
    data["generated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # keep `generated` first, as in the contract
    data = {"generated": data.pop("generated"), **data}
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(data['runs'])} runs, "
          f"{sum(len(r['rows']) for r in data['runs'])} rows")


if __name__ == "__main__":
    main()
