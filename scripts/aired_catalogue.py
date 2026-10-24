"""ScriptBench objective track on the aired catalogue, by writer model. Free: no model calls.

    python scripts/aired_catalogue.py                              # markdown headline table to stdout
    python scripts/aired_catalogue.py --json results/aired-catalogue.json

For every canonical writer model in the show's history, the deterministic,
non-subjective ScriptBench measures on a sample of its aired scripts: length
against target, repetition (`rep_4`, `repeated_span_ratio`, `rep_4_last_third`),
losing the middle (`recycle_middle`, `recycle_last`, `rep_4_middle_third`), echo
(`echo_last_decile`, `adjacent_turn_similarity_mean`), catalogued tics per 1k
words, and the TTS-format gate (parseability only). No judge.

It extends `scripts/aired_baseline.py` (V1 prompts only) to the whole public
`My-Weird-Prompts/transcripts` dataset and reuses its measurement path
(`aired_baseline.measure`, `AIRED_SPEAKERS`).

Rules (also in results/README.md, "aired-catalogue"):

* Writer = `llm_model_canonical`. Skipped: `manual-script`, `manual-generation`,
  `unknown`, `none`, `mixed`, empty.
* Pipeline-written = `episode_type` not `manual-script` (the offline Claude Code
  marker, monorepo `context/operations/hf-datasets.md` *Model provenance*), and
  a dialogue format: formats that are not one writer's two-host script
  (NON_DIALOGUE_TYPES) are left out.
* Offline (`manual-script`) episodes are excluded, except for a model that has
  no pipeline episode at all: it gets its own `written: "offline"` row.
* Sample: up to SAMPLE_SIZE per model, stratified across the model's date range
  (equal-width time bins, one seeded draw per non-empty bin, then a seeded
  top-up from the rest). Deterministic for a given dataset revision.
* Length target: the planner's midpoint for the episode's recorded
  `target_length` (minutes), using the word tiers in force on its date
  (PLANNER_TIERS, from monorepo `pipeline/core/episode_planning.py` history);
  where no target is recorded, the task card's 3,800 words (`prompt.TARGET_WORDS`).
  On length = ratio 0.8-1.2, the V1 gate window.
* Gate: `scorers.format_and_length` `parse_ok` rule: under 2% of the words sit
  outside a recognised `Speaker:` turn. Adapted to aired formats: the show's
  other voices open turns (CATALOGUE_SPEAKERS) and the required cast is Corn
  plus one other voice, not Corn and Herman (see `gate`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from aired_baseline import AIRED_SPEAKERS, measure  # noqa: E402
from mwp_eval.metrics import script_metrics  # noqa: E402
from mwp_eval.prompt import TARGET_WORDS  # noqa: E402

DATASET = "My-Weird-Prompts/transcripts"
# 2026-10-24 (latest episode #6234). Moving the pin changes the sample.
DATASET_REVISION = "8705df4670f1413f2f6680c882326b966be3b022"
PARQUET = "episodes/train-00000-of-00001.parquet"
COLUMNS = ["episode_number", "slug", "title", "pub_date", "episode_type", "llm_model", "llm_model_canonical",
           "target_length", "transcript"]

SAMPLE_SIZE = 20
SEED = "scriptbench-aired-catalogue-v1"
SKIP_MODELS = {"manual-script", "manual-generation", "unknown", "none", "mixed", ""}
OFFLINE_TYPE = "manual-script"
# Not a single writer's two-host script: evaluation/meta episodes written offline
# (audio_eval), multi-voice formats (panel, conference), non-English or non-script
# output (translation, audiobook, music_hour), and hand-assembled updates.
NON_DIALOGUE_TYPES = {"audio_eval", "panel", "conference", "translation", "audiobook", "music_hour",
                      "project_update", "host_update"}

# Planner word ranges by target minutes, as (in force from, ranges). History of
# `EpisodePlan.get_word_count_range` in the monorepo: 286d7cf (2026-04-02),
# f869907 (2026-04-12 00:00 +0300, +~10%), 161dfa6 (2026-10-17 18:23 +0300,
# decision 135, 20/25/30 cut by ~600). Commit time stands in for deploy time.
_LONG = {10: (1_300, 1_900), 15: (2_000, 2_600), 35: (5_300, 6_200), 40: (6_200, 7_000),
         45: (7_200, 8_600), 60: (9_900, 11_900), 90: (14_500, 17_800)}
PLANNER_TIERS = [
    ("2026-10-17T15:23:49+00:00", {**_LONG, 20: (2_100, 2_700), 25: (3_100, 3_700), 30: (4_000, 4_700)}),
    ("2026-04-11T21:00:15+00:00", {**_LONG, 20: (2_600, 3_300), 25: (3_700, 4_300), 30: (4_600, 5_300)}),
    ("2000-01-01T00:00:00+00:00", {**_LONG, 20: (2_400, 3_000), 25: (3_400, 3_900), 30: (4_200, 4_800)}),
]

MEASURES = ["word_count", "length_ratio", "rep_4", "repeated_span_ratio", "rep_4_last_third",
            "recycle_middle", "recycle_last", "rep_4_middle_third", "echo_last_decile",
            "adjacent_turn_similarity_mean", "tic_per_1k_named", "stray_word_share"]
RATES = ["on_length", "parse_ok"]

# Every voice that has a turn label in the sampled formats opens a turn: the
# V1 aired set plus the early-era Narrator intro (Nov-Dec 2025) and the voices of
# the March 2026 "Weird AI Experiments" format (Corn with Bernard and Dorothy)
# and the SITREP guest (Raz, Jacob).
CATALOGUE_SPEAKERS = frozenset(AIRED_SPEAKERS | {"Narrator", "Bernard", "Dorothy", "Raz", "Jacob"})


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def target_words(target_length: int | None, pub_date: str) -> tuple[int, str]:
    if target_length:
        for since, ranges in PLANNER_TIERS:
            if _ts(pub_date) >= _ts(since):
                lo, hi = ranges.get(target_length, ranges[25])
                return (lo + hi) // 2, f"planner {target_length} min"
    return TARGET_WORDS, "task card default"


def gate(script: str) -> tuple[bool, float]:
    """`parse_ok` and `stray_word_share` as `scorers.format_and_length` computes them (stray words
    under 2%), adapted to aired formats: every show voice in CATALOGUE_SPEAKERS opens a turn, and
    the required cast is Corn plus at least one other voice rather than Corn and Herman, because
    the "Weird AI Experiments" format has no Herman."""
    m = script_metrics(script, CATALOGUE_SPEAKERS)
    words = m["word_count"] + m["unattributed_words"]
    stray = (m["unattributed_words"] / words) if words else 1.0
    present = set(m["speakers_present"])
    return "Corn" in present and len(present) >= 2 and stray < 0.02, stray


def episode_row(r: dict, written: str) -> dict:
    script = r["transcript"] or ""
    m = measure(script, CATALOGUE_SPEAKERS)
    tw, src = target_words(r["target_length"], r["pub_date"])
    ok, stray = gate(script)
    ratio = m["word_count"] / tw if tw else None
    row = {"slug": r["slug"], "episode_number": r["episode_number"], "date": r["pub_date"][:10],
           "model": r["llm_model_canonical"], "llm_model": r["llm_model"], "episode_type": r["episode_type"],
           "written": written, "target_length_min": r["target_length"], "target_words": tw, "target_source": src}
    for k in MEASURES:
        v = {"length_ratio": ratio, "stray_word_share": stray}.get(k, m.get(k))
        row[k] = round(v, 4) if isinstance(v, float) else v
    row["on_length"] = ratio is not None and 0.8 <= ratio <= 1.2
    row["parse_ok"] = ok
    return row


def sample(rows: list[dict], model: str, k: int = SAMPLE_SIZE) -> list[dict]:
    """Up to k rows spread across the model's date range: k equal-width time bins,
    one seeded pick per non-empty bin, then a seeded top-up from the rest."""
    rows = sorted(rows, key=lambda r: (r["pub_date"], r["episode_number"]))
    if len(rows) <= k:
        return rows
    rng = random.Random(int(hashlib.sha256(f"{SEED}:{model}".encode()).hexdigest(), 16))
    t0, t1 = _ts(rows[0]["pub_date"]).timestamp(), _ts(rows[-1]["pub_date"]).timestamp()
    width = (t1 - t0) / k or 1.0
    bins: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        bins[min(int((_ts(r["pub_date"]).timestamp() - t0) / width), k - 1)].append(r)
    picked = [rng.choice(bins[b]) for b in sorted(bins)]
    chosen = {r["slug"] for r in picked}
    rest = [r for r in rows if r["slug"] not in chosen]
    picked += rng.sample(rest, k - len(picked))
    return sorted(picked, key=lambda r: (r["pub_date"], r["episode_number"]))


def summarise(eps: list[dict]) -> dict:
    out = {}
    for k in MEASURES:
        vals = sorted(e[k] for e in eps if e[k] is not None)
        if not vals:
            out[k] = {"median": None, "q1": None, "q3": None}
            continue
        q = statistics.quantiles(vals, n=4, method="inclusive") if len(vals) > 1 else [vals[0]] * 3
        rnd = (lambda x: int(round(x))) if k == "word_count" else (lambda x: round(x, 4))
        out[k] = {"median": rnd(statistics.median(vals)), "q1": rnd(q[0]), "q3": rnd(q[2])}
    for k in RATES:
        out[f"{k}_rate"] = round(sum(e[k] for e in eps) / len(eps), 4)
    return out


def load_rows() -> list[dict]:
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download

    path = hf_hub_download(DATASET, PARQUET, repo_type="dataset", revision=DATASET_REVISION)
    return pq.read_table(path, columns=COLUMNS).to_pylist()


def build() -> dict:
    rows = [r for r in load_rows() if (r["llm_model_canonical"] or "") not in SKIP_MODELS]
    pipeline, offline = defaultdict(list), defaultdict(list)
    excluded_types: dict[str, int] = defaultdict(int)
    for r in rows:
        m = r["llm_model_canonical"]
        if r["episode_type"] == OFFLINE_TYPE:
            offline[m].append(r)
        elif r["episode_type"] in NON_DIALOGUE_TYPES:
            excluded_types[r["episode_type"]] += 1
        else:
            pipeline[m].append(r)
    groups = [(m, "pipeline", rs) for m, rs in pipeline.items()]
    groups += [(m, "offline", rs) for m, rs in offline.items() if m not in pipeline]
    models, episodes = [], []
    for model, written, rs in groups:
        eps = [episode_row(r, written) for r in sample(rs, model)]
        episodes += eps
        models.append({"model": model, "written": written, "n": len(eps), "available": len(rs),
                       "first": min(r["pub_date"] for r in rs)[:10], "last": max(r["pub_date"] for r in rs)[:10],
                       "offline_episodes_excluded": len(offline.get(model, [])) if written == "pipeline" else 0,
                       **summarise(eps)})
    models.sort(key=lambda m: (m["written"] == "offline", m["first"], m["model"]))
    episodes.sort(key=lambda e: (e["date"], e["episode_number"]))
    return {
        "dataset": DATASET, "dataset_revision": DATASET_REVISION,
        "built_by": "scripts/aired_catalogue.py", "sample_size": SAMPLE_SIZE, "seed": SEED,
        "rules": {
            "writer": "llm_model_canonical; skipped: " + ", ".join(sorted(s for s in SKIP_MODELS if s)),
            "offline": f"episode_type == {OFFLINE_TYPE!r}; excluded unless the model has no pipeline episode, then a written=offline row",
            "non_dialogue_types_excluded": dict(sorted(excluded_types.items())),
            "sample": "up to 20 per model: equal-width time bins over the model's date range, one seeded pick per non-empty bin, seeded top-up",
            "length_target": "planner midpoint for the recorded target_length at the episode's date; else the task card's 3,800 words",
            "on_length": "length_ratio within 0.8-1.2 (V1 gate window)",
            "parse_ok": "scorers.format_and_length rule (stray words < 2% of all words), with Corn plus at least one "
                        "other voice required; turn-opening labels: " + ", ".join(sorted(CATALOGUE_SPEAKERS)),
        },
        "caveat": "Different prompts per model; repetition is length-dependent (r = 0.28); era flags, not a ranking.",
        "models": models,
        "episodes": episodes,
    }


def fmt(v, k):
    if v is None:
        return "—"
    return f"{v:.0f}" if k == "word_count" else f"{v:.2f}" if k in ("length_ratio", "tic_per_1k_named") else f"{v:.4f}"


def table(data: dict) -> str:
    cols = ["word_count", "length_ratio", "rep_4", "recycle_middle", "recycle_last", "echo_last_decile",
            "tic_per_1k_named"]
    head = ["model", "era", "n", "words", "len ratio", "rep_4", "recycle_middle", "recycle_last",
            "echo_last_decile", "tics/1k", "on length", "gate pass"]
    lines = ["| " + " | ".join(head) + " |", "|---|---|---:|" + "---:|" * (len(head) - 3)]
    for m in data["models"]:
        name = f"`{m['model']}`" + (" (offline)" if m["written"] == "offline" else "")
        era = m["first"] if m["first"] == m["last"] else f"{m['first']} – {m['last']}"
        cells = [fmt(m[k]["median"], k) for k in cols]
        lines.append(f"| {name} | {era} | {m['n']} | " + " | ".join(cells)
                     + f" | {m['on_length_rate']:.2f} | {m['parse_ok_rate']:.2f} |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", help="write the full result (per-model summaries and per-episode rows) here")
    args = ap.parse_args()
    data = build()
    print(f"Aired catalogue, {DATASET} @ {DATASET_REVISION[:7]}. Medians.\n")
    print(table(data))
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
