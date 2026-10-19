"""Copied unchanged from My-Weird-Prompts/mwp-script-eval @ e9d9411;
relative paths in this docstring refer to that repository.

Deterministic proxies for the "X factor": dialogue that feels alive.

Derived 2026-10-18 by comparing 24 offline Claude Opus 5.5 scripts with 22
DeepSeek V4.1 Flash pipeline scripts aired between #6038 and #6097
(docs/x-factor.md). Each key is a turn-level habit that a close read found on
the flat side and a whole-corpus count confirmed. AUC is P(Opus value > DeepSeek
value) on that corpus, so values far from 0.5 separate the two:

* `so_open_share`: host turns opening "So ..." (summarise-then-cue). AUC 0.10.
* `agree_open_share`: host turns opening with agreement ("Exactly", "Right",
  "That's a great point"). AUC 0.17.
* `cue_turn_share`: host turns of four words or fewer with no question mark,
  e.g. "Trees." / "PodBench." / "Thirty-three." (the co-host announcing the
  next item or echoing a number). AUC 0.25.
* `opinion_q_per_1k`: one host asking the other what he thinks, would do or
  would buy, per 1k host words. AUC 0.77.
* `question_per_turn`: question marks per host turn. AUC 0.74.

These are weak, gameable proxies. None separates the two models on its own, and
together they explain far less than the judge's liveness axes. Use them to spot
regressions cheaply, not to rank models. Signpost-phrase and "That's not X.
That's Y" counts were tried and did not separate the corpus (AUC 0.37 and 0.47),
so they were left out.
"""

from __future__ import annotations

import re

from .metrics import parse_turns

HOSTS = ("Corn", "Herman")

AGREE_OPEN = re.compile(
    r"^(right|exactly|yeah|yes|absolutely|totally|precisely|indeed|true|"
    r"that's (right|exactly|true|it|a (great|good|fair) (point|question))|"
    r"good point|great point|fair point|oh,? (absolutely|totally))\b",
    re.I,
)
OPINION_Q = re.compile(
    r"\b(would you|what would you|do you (buy|think|believe|trust|reckon)|would you rather|you think|"
    r"what do you (actually )?think|where would you|which would you|are you (convinced|sold))\b",
    re.I,
)


def liveness_markers(script: str, speakers: set[str]) -> dict:
    turns = [(s, t) for s, t in parse_turns(script, speakers) if s in HOSTS]
    if len(turns) < 10:
        return {}
    words = sum(len(t.split()) for _, t in turns)
    text = " ".join(t for _, t in turns)
    n = len(turns)
    return {
        "so_open_share": sum(t.startswith("So ") for _, t in turns) / n,
        "agree_open_share": sum(bool(AGREE_OPEN.match(t.strip())) for _, t in turns) / n,
        "cue_turn_share": sum(len(t.split()) <= 4 and "?" not in t for _, t in turns) / n,
        "opinion_q_per_1k": 1000 * len(OPINION_Q.findall(text)) / words,
        "question_per_turn": text.count("?") / n,
    }
