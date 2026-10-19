"""Blind pairwise preference app for MWP script excerpts (plans/002).

Items: JSONL files under DATA_DIR/items/, one pair per line:
  {"pair_id", "kind", "prompt", "context", "a": {"model", "text"}, "b": {"model", "text"}, "meta": {...}}
The app never shows model names. Which item side appears on the left is
decided per (rater, pair_id) by a hash, so it is stable across reloads and
balanced across pairs; the judgment records the mapping.

Judgments: one JSON file per decision under DATA_DIR/judgments/<rater>/, on the
Storage Bucket mounted at DATA_DIR (default /data). One file per write avoids
concurrent-append problems on an object-storage mount.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

import gradio as gr

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
ITEMS = DATA_DIR / "items"
JUDGMENTS = DATA_DIR / "judgments"
CHOICES = ["Left is better", "Right is better", "Tie", "Both bad"]
REASONS = ["funnier", "more frank", "more natural", "better co-host play", "holds the thread",
           "lost the thread (other side)", "unsolicited disclaimer (other side)", "wrong voice (other side)",
           "too long / padded (other side)"]


def load_items() -> list[dict]:
    items = []
    for f in sorted(ITEMS.glob("*.jsonl")):
        for line in f.read_text().splitlines():
            if line.strip():
                items.append(json.loads(line))
    return items


def rated(rater: str) -> set[str]:
    d = JUDGMENTS / rater
    if not d.exists():
        return set()
    out = set()
    for f in d.glob("*.json"):
        try:
            out.add(json.loads(f.read_text())["pair_id"])
        except (json.JSONDecodeError, KeyError):
            continue
    return out


def flipped(rater: str, pair_id: str) -> bool:
    return int(hashlib.sha1(f"{rater}:{pair_id}".encode()).hexdigest(), 16) % 2 == 1


def as_markdown(text: str) -> str:
    """Bold the speaker labels of a `Speaker: text` script."""
    return re.sub(r"(?m)^(\w[\w .'-]{0,30}):", r"**\1:**", text.strip())


def rater_of(profile: gr.OAuthProfile | None) -> str:
    return profile.username if profile else os.environ.get("DEFAULT_RATER", "anonymous")


def next_item(kind: str, skipped: list[str] | None, profile: gr.OAuthProfile | None):
    rater = rater_of(profile)
    items = [i for i in load_items() if kind == "all" or i.get("kind") == kind]
    done = rated(rater)
    todo = [i for i in items if i["pair_id"] not in done and i["pair_id"] not in (skipped or [])]
    n_done = sum(1 for i in items if i["pair_id"] in done)
    progress = f"**{rater}** · {n_done} of {len(items)} rated ({kind})"
    if not todo:
        return (None, progress + " · nothing left in this set", "", "", "", gr.update(value=None),
                gr.update(value=[]), "")
    # Stable pseudo-random order, so consecutive pairs mix prompts and models.
    item = sorted(todo, key=lambda i: hashlib.sha1(i["pair_id"].encode()).hexdigest())[0]
    left, right = (item["b"], item["a"]) if flipped(rater, item["pair_id"]) else (item["a"], item["b"])
    ctx = item.get("context") or ""
    header = f"### Prompt\n{item.get('prompt', '')}" + (f"\n\n### Script so far\n{as_markdown(ctx)}" if ctx else "")
    return (item["pair_id"], progress, header, as_markdown(left["text"]), as_markdown(right["text"]),
            gr.update(value=None), gr.update(value=[]), "")


def skip_item(pair_id, kind, skipped, profile: gr.OAuthProfile | None):
    skipped = (skipped or []) + ([pair_id] if pair_id else [])
    return (*next_item(kind, skipped, profile), skipped)


def submit(pair_id, choice, reasons, note, kind, skipped, profile: gr.OAuthProfile | None):
    if pair_id and choice:
        rater = rater_of(profile)
        item = next(i for i in load_items() if i["pair_id"] == pair_id)
        flip = flipped(rater, pair_id)
        left, right = ("b", "a") if flip else ("a", "b")
        winner = {"Left is better": left, "Right is better": right, "Tie": "tie", "Both bad": "both_bad"}[choice]
        record = {
            "pair_id": pair_id, "rater": rater, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "kind": item.get("kind"), "winner": winner,
            "winner_model": item[winner]["model"] if winner in ("a", "b") else None,
            "model_a": item["a"]["model"], "model_b": item["b"]["model"],
            "left": left, "reasons": reasons or [], "note": note or "", "meta": item.get("meta", {}),
        }
        out = JUDGMENTS / rater
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{record['ts'].replace(':', '')}-{pair_id}.json").write_text(json.dumps(record, indent=1))
    return next_item(kind, skipped, profile)


with gr.Blocks(title="MWP preference") as demo:
    gr.Markdown("## MWP preference\nPick the excerpt you'd rather hear on air. Models are hidden; sides are shuffled.")
    with gr.Row():
        gr.LoginButton()
        kind = gr.Radio(["opening", "continuation", "full_script", "all"], value="opening", label="Set")
    progress = gr.Markdown()
    pair_id = gr.State()
    skipped = gr.State([])
    header = gr.Markdown()
    with gr.Row(equal_height=False):
        with gr.Column():
            gr.Markdown("#### Left")
            left = gr.Markdown()
        with gr.Column():
            gr.Markdown("#### Right")
            right = gr.Markdown()
    choice = gr.Radio(CHOICES, label="Which would you rather air?")
    reasons = gr.CheckboxGroup(REASONS, label="Why (optional)")
    note = gr.Textbox(label="Note (optional)", lines=2)
    with gr.Row():
        go = gr.Button("Submit and next", variant="primary")
        skip = gr.Button("Skip")
    outs = [pair_id, progress, header, left, right, choice, reasons, note]
    demo.load(next_item, [kind, skipped], outs)
    kind.change(next_item, [kind, skipped], outs)
    go.click(submit, [pair_id, choice, reasons, note, kind, skipped], outs)
    skip.click(skip_item, [pair_id, kind, skipped], [*outs, skipped])

if __name__ == "__main__":
    demo.launch()
