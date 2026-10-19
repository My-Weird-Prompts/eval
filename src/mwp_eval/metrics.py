"""Copied unchanged from My-Weird-Prompts/mwp-script-eval @ e9d9411;
relative paths in this docstring refer to that repository.

Deterministic script metrics.

Ported, not imported, from the monorepo's corpus build
(My-Weird-Prompts @ f22a010, `pipeline/scripts/build_transcript_corpus.py`) and
the September analysis (MWP-Script-Analysis-0926 @ 3185b9b,
`scripts/03_repetition.py`). The point of porting exactly is comparability: a
candidate's `rep_4` here is on the same footing as the published `rep_*` columns
and the 5,332-episode baseline in `data/tic-targets.json`. Change the normaliser
or the tokeniser and that comparison silently breaks.

Limits, stated next to the code because they bite:

* `rep_4`, `rep_8` and `compression_ratio` are length-dependent (r=0.28 and
  r=-0.60 with word count across the corpus). Compare candidates on the same
  fixtures, never against a corpus median from scripts of a different length.
* `adjacent_turn_similarity_mean` is the one repetition measure that is
  effectively length-independent (r=-0.05).
* Tic rates are lexical. They say nothing about whether a phrase is audible in
  proportion to its rate.
"""

from __future__ import annotations

import gzip
import json
import math
import re
from collections import Counter
from functools import lru_cache
from importlib import resources

UNATTRIBUTED = "UNATTRIBUTED"
LABEL_RE = re.compile(r"^([^\n:]{1,40}):[ \t]*(.*)$", re.DOTALL)
WORD_RE = re.compile(r"[A-Za-z0-9'’]+")
REPEAT_SPAN = 25  # tokens; a repeated run this long is a duplicated passage
ECHO_N = 5
DECILES = 10

_NORMALISE = {
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "—": "-", "–": "-", "…": "...",
}


def normalise(text: str) -> str:
    """Casefold, fold smart punctuation, collapse whitespace."""
    for src, dst in _NORMALISE.items():
        text = text.replace(src, dst)
    return " ".join(text.casefold().split())


def tokens(text: str) -> list[str]:
    return WORD_RE.findall(normalise(text))


def parse_turns(script: str, speakers: set[str]) -> list[tuple[str, str]]:
    """Segment a `Speaker: text` script into turns.

    Same line-wise rule as the corpus build: a line opens a turn only when its
    label is a known speaker; anything else attaches to the turn in progress.
    Text before the first known label is UNATTRIBUTED, not dropped — a script
    that opens with a preamble ("Here is the script:") should cost the model.
    """
    index = {s.casefold(): s for s in speakers}
    turns: list[tuple[str, list[str]]] = []
    for raw in script.split("\n"):
        line = raw.strip()
        if not line:
            if turns:
                turns[-1][1].append("")
            continue
        m = LABEL_RE.match(line)
        label = m.group(1).strip().strip("*").strip().casefold() if m else None
        speaker = index.get(label) if label else None
        if speaker:
            body = m.group(2).strip()
            turns.append((speaker, [body] if body else []))
        elif turns:
            turns[-1][1].append(line)
        else:
            turns.append((UNATTRIBUTED, [line]))
    out = []
    for speaker, parts in turns:
        text = re.sub(r"\n{3,}", "\n\n", "\n".join(parts)).strip()
        if text:
            out.append((speaker, text))
    return out


def rep_n(toks: list[str], n: int) -> float | None:
    if len(toks) < n + 1:
        return None
    grams = [tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)]
    return 1.0 - (len(set(grams)) / len(grams))


def compression_ratio(text: str) -> float | None:
    if not text:
        return None
    raw = text.encode("utf-8")
    return len(gzip.compress(raw, 6)) / len(raw)


def repeated_span_ratio(toks: list[str]) -> float | None:
    if len(toks) < REPEAT_SPAN * 2:
        return None
    first_seen: dict[tuple, int] = {}
    covered = bytearray(len(toks))
    for i in range(len(toks) - REPEAT_SPAN + 1):
        key = tuple(toks[i:i + REPEAT_SPAN])
        start = first_seen.get(key)
        if start is None:
            first_seen[key] = i
            continue
        for j in range(start, start + REPEAT_SPAN):
            covered[j] = 1
        for j in range(i, i + REPEAT_SPAN):
            covered[j] = 1
    return sum(covered) / len(toks)


def thirds(toks: list[str]) -> tuple[float | None, float | None, float | None]:
    if len(toks) < 3 * (4 + 1):
        return None, None, None
    cut = len(toks) // 3
    return rep_n(toks[:cut], 4), rep_n(toks[cut:2 * cut], 4), rep_n(toks[2 * cut:], 4)


def adjacent_turn_similarity(turns: list[tuple[str, str]]) -> tuple[float | None, float | None]:
    """Mean and max TF-IDF cosine between consecutive turns, IDF within the script."""
    docs = [Counter(tokens(text)) for _, text in turns]
    docs = [d for d in docs if d]
    if len(docs) < 2:
        return None, None
    df: Counter = Counter()
    for d in docs:
        df.update(d.keys())
    idf = {w: math.log(len(docs) / (1 + c)) + 1.0 for w, c in df.items()}
    vectors = []
    for d in docs:
        vec = {w: c * idf[w] for w, c in d.items()}
        vectors.append((vec, math.sqrt(sum(v * v for v in vec.values()))))
    sims = []
    for (a, na), (b, nb) in zip(vectors, vectors[1:]):
        if not na or not nb:
            continue
        if len(a) > len(b):
            a, b = b, a
        sims.append(sum(v * b.get(w, 0.0) for w, v in a.items()) / (na * nb))
    if not sims:
        return None, None
    return sum(sims) / len(sims), max(sims)


def echo_by_decile(turns: list[tuple[str, str]]) -> list[float | None]:
    """Mean share of a turn's 5-grams already said earlier in the script, by decile.

    The long-form "losing the middle" signal: the corpus runs ~0.002 in the
    first decile and ~0.04 in the last under the current writer.
    """
    seen: set[tuple] = set()
    sums = [0.0] * DECILES
    counts = [0] * DECILES
    n_turns = len(turns)
    for i, (_, text) in enumerate(turns):
        toks = tokens(text)
        grams = [tuple(toks[j:j + ECHO_N]) for j in range(len(toks) - ECHO_N + 1)]
        if grams:
            bucket = min(int(i / n_turns * DECILES), DECILES - 1)
            sums[bucket] += sum(1 for g in grams if g in seen) / len(grams)
            counts[bucket] += 1
            seen.update(grams)
    return [s / c if c else None for s, c in zip(sums, counts)]


@lru_cache(maxsize=1)
def tic_patterns() -> dict[str, re.Pattern]:
    """Named tic phrases from the September analysis, plus its unnamed high-rate
    candidates. Matched against normalised text, as measured there."""
    raw = json.loads(resources.files(__package__).joinpath("data/tic-targets.json").read_text())
    pats = {t["phrase"]: re.compile(t["pattern"]) for t in raw["phrase_targets"]}
    for c in raw.get("unnamed_candidates", []):
        pats.setdefault(c["phrase"], re.compile(r"\b" + re.escape(c["phrase"]) + r"\b"))
    return pats


@lru_cache(maxsize=1)
def named_tics() -> frozenset[str]:
    raw = json.loads(resources.files(__package__).joinpath("data/tic-targets.json").read_text())
    return frozenset(t["phrase"] for t in raw["phrase_targets"])


def tic_counts(text: str) -> dict[str, int]:
    norm = normalise(text)
    return {phrase: len(p.findall(norm)) for phrase, p in tic_patterns().items()}


def script_metrics(script: str, speakers: set[str]) -> dict:
    """Every deterministic measure for one script, as a flat JSON-able dict."""
    turns = parse_turns(script, speakers)
    spoken = "\n".join(text for s, text in turns if s != UNATTRIBUTED)
    toks = tokens(spoken)
    words = len(toks)
    first, middle, last = thirds(toks)
    sim_mean, sim_max = adjacent_turn_similarity([t for t in turns if t[0] != UNATTRIBUTED])
    echo = echo_by_decile([t for t in turns if t[0] != UNATTRIBUTED])
    tics = tic_counts(spoken)
    named = named_tics()
    named_hits = sum(n for p, n in tics.items() if p in named)
    by_speaker = Counter(s for s, _ in turns)
    words_by_speaker = Counter()
    for s, text in turns:
        words_by_speaker[s] += len(tokens(text))
    return {
        "word_count": words,
        "turns": len(turns),
        "unattributed_words": words_by_speaker.get(UNATTRIBUTED, 0),
        "speakers_present": sorted(s for s in by_speaker if s != UNATTRIBUTED),
        "turns_by_speaker": dict(by_speaker),
        "words_by_speaker": dict(words_by_speaker),
        "mean_turn_words": (words / len(turns)) if turns else None,
        "rep_4": rep_n(toks, 4),
        "rep_8": rep_n(toks, 8),
        "rep_4_first_third": first,
        "rep_4_middle_third": middle,
        "rep_4_last_third": last,
        "compression_ratio": compression_ratio(spoken),
        "repeated_span_ratio": repeated_span_ratio(toks),
        "adjacent_turn_similarity_mean": sim_mean,
        "adjacent_turn_similarity_max": sim_max,
        "echo_first_decile": echo[0],
        "echo_last_decile": echo[-1],
        "tic_hits_named": named_hits,
        "tic_per_1k_named": (named_hits / words * 1000) if words else None,
        "tic_hits": {p: n for p, n in tics.items() if n},
    }
