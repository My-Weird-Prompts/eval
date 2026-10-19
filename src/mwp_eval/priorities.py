"""Copied unchanged from My-Weird-Prompts/mwp-script-eval @ e9d9411 (relative
paths below refer to that repository). V1 uses
`recycling`, `script_thirds` and `candour_markers`; the plan helpers are kept so
the file stays a verbatim copy for V2, which restores plan coverage.

Measures for the writer failure modes Daniel ranks highest (2026-10-17).

In order: losing context in the middle, not being fun, being over-sanitised.
`docs/task-spec.md` defines them. This module holds the deterministic parts.
The judged parts are the `fun` and `candour` rubric axes and the
`plan_coverage` scorer.

These measures are additive and kept out of `metrics.py` on purpose:
`metrics.py` has to stay byte-compatible with the monorepo corpus build. This
module reuses its tokeniser and adds no new normalisation.
"""

from __future__ import annotations

import json
import re
from importlib import resources

from .metrics import UNATTRIBUTED, parse_turns, tokens

# 6-grams, not the corpus's 4-grams: at 4 tokens ordinary phrases ("one of the
# things") collide across thirds and swamp the signal. A 6-gram shared between
# the first and middle third is almost always a re-explained point or a reused
# bit.
RECYCLE_N = 6

_PLAN_HEAD = re.compile(r"^## EPISODE PLAN\b.*$", re.M)
_NEXT_H2 = re.compile(r"^## ", re.M)
_SEGMENT = re.compile(r"^\*\*(.+?)\*\*(?:\s*\(.*\))?\s*$")
_TARGET = re.compile(r"\*\*Target Length\*\*:\s*(\d+)\s*minutes\s*\(~\s*([\d,]+)\s*words\)")


def plan_block(brief: str) -> str | None:
    """The `## EPISODE PLAN` section of an assembled script prompt, if any.

    Format comes from `EpisodePlan.to_prompt_string()` (monorepo
    `pipeline/core/episode_planning.py`).
    """
    m = _PLAN_HEAD.search(brief)
    if not m:
        return None
    rest = brief[m.end():]
    nxt = _NEXT_H2.search(rest)
    return rest[: nxt.start()] if nxt else rest


def plan_target_words(brief: str) -> int | None:
    """The word target the planner gave the writer, which is what it was told to hit."""
    block = plan_block(brief) or ""
    m = _TARGET.search(block)
    return int(m.group(2).replace(",", "")) if m else None


def plan_points(brief: str) -> list[dict]:
    """Every planned point and question, tagged with its segment's index, plus
    the plan's "Key Facts to Include" (`kind="fact"`).

    Segment headers are bold all-caps lines (`**OPENING** (~400 words, ...)`).
    Bullets under them are the points. The labels **Topic**, **Target Length**,
    **HARD CEILING** and **Floor** are bold too, but they contain a colon inside
    the bold, so `_SEGMENT` skips them.
    """
    block = plan_block(brief)
    if not block:
        return []
    out, seg_idx, seg_name, section = [], -1, None, None
    for line in block.splitlines():
        s = line.strip()
        if s.startswith("### "):
            # "Segment Outline" holds the segments; "Key Facts to Include" holds
            # research facts the planner wants on air (kind="fact", no segment).
            # Misconceptions, transitions and tone are guidance, not checkable points.
            title = s[4:].casefold()
            section = "segments" if "segment" in title else "facts" if "key facts" in title else None
            continue
        m = _SEGMENT.match(s)
        if section == "segments" and m and ":" not in m.group(1):
            seg_idx += 1
            seg_name = m.group(1).strip()
            continue
        if not s.startswith("- "):
            continue
        if section == "segments" and seg_idx >= 0:
            out.append({"kind": "point", "segment": seg_idx, "segment_name": seg_name, "point": s[2:].strip()})
        elif section == "facts":
            out.append({"kind": "fact", "segment": None, "segment_name": None, "point": s[2:].strip()})
    n_seg = seg_idx + 1
    for p in out:
        if p["kind"] == "fact":
            p["middle"] = False
            continue
        # The middle is every segment but the first and last. With fewer than three
        # segments there is no middle segment, so none are marked.
        p["middle"] = n_seg >= 3 and 0 < p["segment"] < n_seg - 1
    return out


def _grams(toks: list[str], n: int) -> set[tuple]:
    return {tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def _share_seen(part: list[str], seen: set[tuple], n: int) -> float | None:
    grams = [tuple(part[i:i + n]) for i in range(len(part) - n + 1)]
    if not grams:
        return None
    return sum(g in seen for g in grams) / len(grams)


def recycling(script: str, speakers: set[str]) -> dict:
    """How much of each later third re-says the earlier ones.

    `recycle_middle`: share of the middle third's 6-grams that already appeared
    in the first third. `recycle_last`: the same for the last third against
    the first two. Lower is better. A script that loses the thread and
    re-explains its opening scores high, because restatement reuses wording.
    """
    turns = parse_turns(script, speakers)
    toks = tokens("\n".join(t for s, t in turns if s != UNATTRIBUTED))
    if len(toks) < 3 * (RECYCLE_N + 1):
        return {}
    cut = len(toks) // 3
    first, middle, last = toks[:cut], toks[cut:2 * cut], toks[2 * cut:]
    return {
        "recycle_middle": _share_seen(middle, _grams(first, RECYCLE_N), RECYCLE_N),
        "recycle_last": _share_seen(last, _grams(first + middle, RECYCLE_N), RECYCLE_N),
    }


def script_thirds(script: str) -> tuple[str, str, str]:
    """Split the raw script into thirds by line, at turn boundaries, for the judge."""
    lines = script.splitlines()
    total = sum(len(l.split()) for l in lines) or 1
    parts, acc, cur = [[], [], []], 0, 0
    for line in lines:
        # Advance to the next part only at a line that opens a turn, so the
        # judge never sees a turn cut in half.
        if cur < 2 and acc >= total * (cur + 1) / 3 and re.match(r"^\s*\**[A-Za-z][\w .'-]{0,40}\**\s*:", line):
            cur += 1
        parts[cur].append(line)
        acc += len(line.split())
    return tuple("\n".join(p).strip() for p in parts)  # type: ignore[return-value]


def _candour_patterns() -> dict[str, dict[str, re.Pattern]]:
    raw = json.loads(resources.files(__package__).joinpath("data/candour-markers.json").read_text())
    return {group: {p: re.compile(p) for p in pats} for group, pats in raw["patterns"].items()}


def candour_markers(script: str, speakers: set[str]) -> dict:
    """Rates of sanitising language: hedges, moralising, refusal or AI-voice leakage.

    A coarse signal. Some hedging is natural speech, so compare models with
    each other and don't read a rate as good or bad on its own. The judge's
    `candour` axis is the measure to trust. Matching runs on the normalised
    spoken text (lower-cased, smart quotes folded).
    """
    from .metrics import normalise

    turns = parse_turns(script, speakers)
    spoken = normalise("\n".join(t for s, t in turns if s != UNATTRIBUTED))
    words = len(tokens(spoken)) or 1
    out: dict = {"hits": {}}
    for group, pats in _candour_patterns().items():
        n = 0
        for src, pat in pats.items():
            k = len(pat.findall(spoken))
            if k:
                out["hits"][src] = k
                n += k
        out[f"{group}_per_1k"] = n / words * 1000
    return out
