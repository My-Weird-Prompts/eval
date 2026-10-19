"""Blind pairwise preference app for MWP script excerpts (plans/002).

Items: JSONL files under DATA_DIR/items/, one pair per line:
  {"pair_id", "kind", "prompt", "context", "a": {"model", "text"}, "b": {"model", "text"}, "meta": {...}}
Model names are never shown. Which side appears on the left is a stable hash of
(reviewer, pair_id), so it survives reloads and balances across pairs; the
judgment records the mapping.

Judgments: one JSON file per decision under DATA_DIR/judgments/<reviewer>/ on
the Storage Bucket mounted at DATA_DIR (default /data). One file per write
avoids concurrent-append problems on an object-storage mount.

Tags are grouped by axis. Each tag is recorded against the side it describes:
"Winner" tags say why the chosen side is better, "Loser" tags name what is
wrong with the other side. The censorship group appears only on probe pairs
(meta.prompt_id starting "cn-" or "us-").
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
REVIEWERS = ["Daniel", "Hannah"]
SETS = {"Openings (quick)": "opening", "Continuations": "continuation", "Full scripts": "full_script", "Everything": "all"}

WIN_TAGS = ["Funnier", "More natural", "Better co-host play", "Holds the thread", "More specific",
            "Franker / commits to a view", "Better ending", "Better voices"]
LOSE_TAGS = ["Lost the thread", "Repetitive / recycles", "Padded / too long", "Stock phrases / tics",
             "Lecture, not a conversation", "Wrong character voice", "Factual problem", "Format / TTS problem"]
CENSOR_TAGS = ["Refused", "Deflected / vague", "PRC state framing", "US-centric framing",
               "Unsolicited disclaimer", "Moralising", "Both-sidesing", "Hedging"]

CSS = """
.gradio-container {max-width: 1280px !important}
.script-card {border: 1px solid var(--border-color-primary); border-radius: 12px; padding: 14px 18px;
  max-height: 62vh; overflow-y: auto; background: var(--background-fill-secondary)}
.script-card p {margin: 0 0 .55em 0; line-height: 1.5}
.side-label {font-weight: 700; font-size: 1.05em; margin-bottom: 4px}
.verdict button {font-size: 1.05em !important; min-height: 52px}
.tags .wrap {gap: 6px !important}
.tags label {border-radius: 999px !important; padding: 4px 12px !important}
.progress {opacity: .8}
"""


def load_items() -> list[dict]:
    items = []
    for f in sorted(ITEMS.glob("*.jsonl")):
        for line in f.read_text().splitlines():
            if line.strip():
                items.append(json.loads(line))
    return items


def rated(reviewer: str) -> set[str]:
    d = JUDGMENTS / reviewer.lower()
    out = set()
    for f in d.glob("*.json") if d.exists() else []:
        try:
            out.add(json.loads(f.read_text())["pair_id"])
        except (json.JSONDecodeError, KeyError):
            continue
    return out


def flipped(reviewer: str, pair_id: str) -> bool:
    return int(hashlib.sha1(f"{reviewer.lower()}:{pair_id}".encode()).hexdigest(), 16) % 2 == 1


def as_markdown(text: str) -> str:
    """Bold the speaker labels of a `Speaker: text` script; one paragraph per turn."""
    text = re.sub(r"(?m)^(\w[\w .'-]{0,30}):", r"**\1:**", text.strip())
    return re.sub(r"\n(?=\*\*)", "\n\n", text)


def is_probe(item: dict) -> bool:
    return str(item.get("meta", {}).get("prompt_id", "")).startswith(("cn-", "us-"))


def show(reviewer: str, set_label: str, skipped: list[str] | None):
    kind = SETS[set_label]
    items = [i for i in load_items() if kind == "all" or i.get("kind") == kind]
    done = rated(reviewer)
    todo = [i for i in items if i["pair_id"] not in done and i["pair_id"] not in (skipped or [])]
    n_done = sum(1 for i in items if i["pair_id"] in done)
    progress = f"**{reviewer}** · {n_done} of {len(items)} rated in *{set_label}*"
    blank = gr.update(value=[])
    if not todo:
        return (None, progress + " · nothing left here: try another set", "", "", "",
                blank, blank, gr.update(value=[], visible=False), "")
    item = sorted(todo, key=lambda i: hashlib.sha1(i["pair_id"].encode()).hexdigest())[0]
    left, right = (item["b"], item["a"]) if flipped(reviewer, item["pair_id"]) else (item["a"], item["b"])
    ctx = item.get("context") or ""
    header = f"> {item.get('prompt', '').strip()}" + (f"\n\n**Script so far**\n\n{as_markdown(ctx)}" if ctx else "")
    return (item["pair_id"], progress, header, as_markdown(left["text"]), as_markdown(right["text"]),
            blank, blank, gr.update(value=[], visible=is_probe(item)), "")


def decide(verdict: str):
    def handler(reviewer, set_label, pair_id, win_tags, lose_tags, censor_tags, note, skipped):
        if pair_id:
            item = next(i for i in load_items() if i["pair_id"] == pair_id)
            left, right = ("b", "a") if flipped(reviewer, pair_id) else ("a", "b")
            winner = {"left": left, "right": right, "tie": "tie", "both_bad": "both_bad"}[verdict]
            loser = {"a": "b", "b": "a"}.get(winner)
            record = {
                "pair_id": pair_id, "reviewer": reviewer, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "kind": item.get("kind"), "verdict": verdict, "winner": winner,
                "winner_model": item[winner]["model"] if winner in ("a", "b") else None,
                "loser_model": item[loser]["model"] if loser else None,
                "model_a": item["a"]["model"], "model_b": item["b"]["model"], "left": left,
                "win_tags": win_tags or [], "lose_tags": lose_tags or [], "censorship_tags": censor_tags or [],
                "note": (note or "").strip(), "meta": item.get("meta", {}),
            }
            out = JUDGMENTS / reviewer.lower()
            out.mkdir(parents=True, exist_ok=True)
            (out / f"{record['ts'].replace(':', '')}-{pair_id}.json").write_text(json.dumps(record, indent=1))
        return show(reviewer, set_label, skipped)
    return handler


def skip(reviewer, set_label, pair_id, skipped):
    skipped = (skipped or []) + ([pair_id] if pair_id else [])
    return (*show(reviewer, set_label, skipped), skipped)


with gr.Blocks(title="MWP preference", css=CSS, theme=gr.themes.Soft()) as demo:
    gr.Markdown("## MWP preference\nWhich excerpt would you rather hear on air? Models are hidden and sides are shuffled.")
    with gr.Row():
        reviewer = gr.Radio(REVIEWERS, value="Daniel", label="Reviewer", scale=1)
        set_label = gr.Radio(list(SETS), value="Openings (quick)", label="Set", scale=2)
    progress = gr.Markdown(elem_classes="progress")
    pair_id = gr.State()
    skipped = gr.State([])
    with gr.Accordion("Prompt", open=True):
        header = gr.Markdown()
    with gr.Row(equal_height=False):
        with gr.Column():
            gr.Markdown("Left", elem_classes="side-label")
            left = gr.Markdown(elem_classes="script-card")
        with gr.Column():
            gr.Markdown("Right", elem_classes="side-label")
            right = gr.Markdown(elem_classes="script-card")
    with gr.Group():
        win_tags = gr.CheckboxGroup(WIN_TAGS, label="Why the better one is better", elem_classes="tags")
        lose_tags = gr.CheckboxGroup(LOSE_TAGS, label="What's wrong with the worse one (or both, if both bad)",
                                     elem_classes="tags")
        censor_tags = gr.CheckboxGroup(CENSOR_TAGS, label="Censorship and frankness (worse side)",
                                       elem_classes="tags", visible=False)
        note = gr.Textbox(label="Notes", placeholder="Anything worth remembering about this pair", lines=2)
    with gr.Row(elem_classes="verdict"):
        b_left = gr.Button("◀ Left is better", variant="primary")
        b_tie = gr.Button("Tie")
        b_bad = gr.Button("Both bad", variant="stop")
        b_right = gr.Button("Right is better ▶", variant="primary")
    b_skip = gr.Button("Skip for now", size="sm")

    outs = [pair_id, progress, header, left, right, win_tags, lose_tags, censor_tags, note]
    view_in = [reviewer, set_label, skipped]
    demo.load(show, view_in, outs)
    reviewer.change(show, view_in, outs)
    set_label.change(show, view_in, outs)
    decide_in = [reviewer, set_label, pair_id, win_tags, lose_tags, censor_tags, note, skipped]
    for btn, verdict in ((b_left, "left"), (b_right, "right"), (b_tie, "tie"), (b_bad, "both_bad")):
        btn.click(decide(verdict), decide_in, outs)
    b_skip.click(skip, [reviewer, set_label, pair_id, skipped], [*outs, skipped])

if __name__ == "__main__":
    demo.launch()
