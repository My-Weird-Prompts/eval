"""Inspect scorers for V1.

Copied from My-Weird-Prompts/mwp-script-eval @ e9d9411 (`scorers.py`). V1
changes: no `plan_coverage` (V1 has no plan), no cameo axis, and the speaker set
is fixed to Corn and Herman.

Each scorer returns a dict-valued Score so one log column carries every sub-
measure, and `report.py` can flatten them without re-running anything.
"""

from __future__ import annotations

import json
import re

from inspect_ai.model import GenerateConfig, get_model
from inspect_ai.scorer import Score, Target, mean, scorer, stderr
from inspect_ai.solver import TaskState

from . import judge
from .prompt import SPEAKERS
from .liveness import liveness_markers as _liveness
from .metrics import script_metrics
from .priorities import candour_markers as _candour, recycling

NAN = float("nan")


def _fixed(keys, **values) -> dict:
    """A score dict with exactly `keys`, NaN where a value is missing or None.

    Inspect reduces dict scores across epochs and samples only when every one has
    the same keys, and a mismatch aborts the whole task (first shortlist run,
    2026-10-17). NaN marks "not applicable" and the reducers skip it.
    """
    return {k: (NAN if values.get(k) is None else float(values[k])) for k in keys}


JUDGE_ROLE = "grader"
# Default also in models.yaml `judge:`; change both.
JUDGE_DEFAULT = "openrouter/anthropic/claude-opus-5.5"
# The show's top three, in order (working paper §2). Their mean is `priority`.
PRIORITY_AXES = ("long_form_coherence", "fun", "candour")


def _script(state: TaskState) -> str:
    return state.output.completion or ""


def _speakers(state: TaskState) -> set[str]:
    """Required speakers. In V1 they are also the only labels that open a turn."""
    return set(SPEAKERS)


_allowed = _speakers


@scorer(metrics={"*": [mean(), stderr()]})
def format_and_length():
    """Hard format checks plus length adherence.

    `parse_ok` is 1 only when every expected speaker has a turn and less than
    2% of the words sit outside a recognised `Speaker:` turn — which is what the
    TTS parser needs. `length_ratio` is words / target; the pipeline asks for a
    target, so both overshoot and undershoot matter.
    """

    async def score(state: TaskState, target: Target) -> Score:
        speakers = _speakers(state)
        m = script_metrics(_script(state), _allowed(state))
        words = m["word_count"] + m["unattributed_words"]
        stray = (m["unattributed_words"] / words) if words else 1.0
        target_words = state.metadata.get("target_words")
        ratio = (m["word_count"] / target_words) if target_words else None
        value = _fixed(
            ("parse_ok", "stray_word_share", "word_count", "length_ratio", "length_within_20pct"),
            parse_ok=set(m["speakers_present"]) >= speakers and stray < 0.02,
            stray_word_share=stray,
            word_count=m["word_count"],
            length_ratio=ratio,
            length_within_20pct=None if ratio is None else 0.8 <= ratio <= 1.2,
        )
        return Score(value=value, metadata={"metrics": m})

    return score


@scorer(metrics={"*": [mean(), stderr()]})
def repetition_and_tics():
    """Corpus-comparable repetition and tic measures (see `metrics.py` limits).

    Lower is better for every key here.
    """

    async def score(state: TaskState, target: Target) -> Score:
        m = script_metrics(_script(state), _allowed(state))
        keys = ["rep_4", "rep_4_last_third", "repeated_span_ratio",
                "adjacent_turn_similarity_mean", "echo_last_decile", "tic_per_1k_named"]
        return Score(value=_fixed(keys, **{k: m[k] for k in keys}), metadata={"tic_hits": m["tic_hits"]})

    return score


def _last_json(text: str) -> dict | None:
    for match in reversed(list(re.finditer(r"\{[^{}]*\}", text, re.DOTALL))):
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            continue
    return None


@scorer(metrics={"*": [mean(), stderr()]})
def rubric_judge(judge_model: str | None = None):
    """Absolute 1-5 rubric from `judge.RUBRIC_AXES`, plus their mean as `overall`."""

    async def score(state: TaskState, target: Target) -> Score:
        grader = get_model(judge_model, role=JUDGE_ROLE, default=JUDGE_DEFAULT)
        script = _script(state)
        keys = (*judge.RUBRIC_AXES, "overall", "priority", "liveness", "judge_parse_failed")
        if not script.strip():
            return Score(value={**{k: 1.0 for k in keys}, "judge_parse_failed": 0.0}, explanation="empty script")
        out = await grader.generate(judge.rubric_prompt(state.metadata["brief"], script),
                                    config=GenerateConfig(temperature=0.0, max_tokens=4000))
        parsed = _last_json(out.completion) or {}
        value = {k: float(parsed[k]) for k in judge.RUBRIC_AXES if isinstance(parsed.get(k), (int, float))}
        if len(value) != len(judge.RUBRIC_AXES):
            return Score(value=_fixed(keys, judge_parse_failed=1.0), explanation=out.completion)
        value["overall"] = sum(value.values()) / len(value)
        value["priority"] = sum(value[k] for k in PRIORITY_AXES) / len(PRIORITY_AXES)
        value["liveness"] = sum(value[k] for k in judge.LIVENESS_AXES) / len(judge.LIVENESS_AXES)
        return Score(value=_fixed(keys, **value, judge_parse_failed=0.0), explanation=out.completion)

    return score


@scorer(metrics={"*": [mean(), stderr()]})
def pairwise_vs_reference(judge_model: str | None = None):
    """Win rate against the script that aired for this prompt.

    Judged twice with the order swapped; `win` is 1 / 0.5 / 0 from the
    candidate's side, averaged over both orders. `order_disagreement` is 1 when
    the two orders gave different verdicts — a high rate means the judge is
    reading position, not quality, and the win rate is noise.
    Every V1 sample has one (the dataset's `transcript`).
    """

    def verdict(text: str) -> str | None:
        m = re.findall(r"WINNER:\s*(A|B|TIE)", text.upper())
        return m[-1] if m else None

    async def score(state: TaskState, target: Target) -> Score:
        keys = ("win", "order_disagreement", "judge_parse_failed")
        reference = state.metadata.get("reference_script")
        if not reference:
            return Score(value=_fixed(keys), explanation="no reference script")
        grader = get_model(judge_model, role=JUDGE_ROLE, default=JUDGE_DEFAULT)
        cand, brief = _script(state), state.metadata["brief"]
        cfg = GenerateConfig(temperature=0.0, max_tokens=2000)
        first = await grader.generate(judge.pairwise_prompt(brief, cand, reference), config=cfg)
        second = await grader.generate(judge.pairwise_prompt(brief, reference, cand), config=cfg)
        v1, v2 = verdict(first.completion), verdict(second.completion)
        points = {"A": 1.0, "TIE": 0.5, "B": 0.0}
        if v1 is None or v2 is None:
            return Score(value=_fixed(keys, judge_parse_failed=1.0),
                         explanation=f"{first.completion}\n---\n{second.completion}")
        win = (points[v1] + (1.0 - points[v2])) / 2
        return Score(
            value=_fixed(keys, win=win, order_disagreement=points[v1] != 1.0 - points[v2],
                         judge_parse_failed=0.0),
            explanation=f"candidate-first: {v1}; reference-first: {v2}",
        )

    return score


@scorer(metrics={"*": [mean(), stderr()]})
def mid_context_hold():
    """Deterministic signals for losing the middle (lower is better).

    `recycle_middle` / `recycle_last` come from `priorities.recycling`, as 6-gram
    reuse against the earlier thirds. `rep_4_middle_third` is the corpus metric
    restricted to the middle third.
    """

    async def score(state: TaskState, target: Target) -> Score:
        script = _script(state)
        mid = script_metrics(script, _allowed(state))["rep_4_middle_third"]
        return Score(value=_fixed(("recycle_middle", "recycle_last", "rep_4_middle_third"),
                                  **recycling(script, _allowed(state)), rep_4_middle_third=mid))

    return score


@scorer(metrics={"*": [mean(), stderr()]})
def candour_markers():
    """Hedge, moralise and refusal phrase rates per 1k words (lower is better). Coarse."""

    async def score(state: TaskState, target: Target) -> Score:
        m = _candour(_script(state), _allowed(state))
        hits = m.pop("hits")
        return Score(value=_fixed(("hedge_per_1k", "moralise_per_1k", "refusal_per_1k"), **m), metadata={"hits": hits})

    return score


@scorer(metrics={"*": [mean(), stderr()]})
def liveness_markers():
    """Cheap turn-level proxies for lively dialogue (`liveness.py`; weak, see its docstring).

    Lower is better for the three `*_share` keys; higher for the two question keys.
    """

    keys = ("so_open_share", "agree_open_share", "cue_turn_share", "opinion_q_per_1k", "question_per_turn")

    async def score(state: TaskState, target: Target) -> Score:
        return Score(value=_fixed(keys, **_liveness(_script(state), _allowed(state))))

    return score
