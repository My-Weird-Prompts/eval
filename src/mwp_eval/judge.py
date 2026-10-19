"""LLM-judge prompts for V1.

Copied from the private harness (My-Weird-Prompts/mwp-script-eval @ e9d9411,
`judge.py`) and cut down for V1's two-host, no-research task:

* `cameo_integration` is dropped: V1 has no producer cameo.
* `accuracy` judges plausibility, since the writer had no research to be
  consistent with.
* `long_form_coherence` no longer mentions an episode plan; V1 has none.

Two judges, because they answer different questions:

* **Rubric** (absolute, 1-5 per axis). Comparable across runs, but coarse: most
  competent models land on 3-4.
* **Pairwise** against the script that aired for the same prompt. More
  sensitive, but only meaningful against that fixed baseline. Run in both orders
  and averaged, because LLM judges prefer whichever script they read first.

The judge never sees the model name. Changing any wording here changes the
benchmark: bump `prompt.PROMPT_VERSION` and note it in CHANGELOG.md.
"""

from __future__ import annotations

RUBRIC_AXES: dict[str, str] = {
    "answer_the_ask": "Did the script deliver what the listener actually asked for (the list, the explanation, the position) instead of redirecting, going meta, or answering an easier question?",
    "specifics": "Density of concrete, checkable specifics — names, numbers, dates, cases, mechanisms — as opposed to atmosphere, vague 'studies show', or metaphor standing in for content.",
    "dialogue": "Is it a real conversation — interruption, disagreement, concession, questions that change direction — or alternating monologues and a lecturer with a prompter?",
    "character_voice": "Do the hosts sound like the characters described in the brief, distinct from each other and consistent throughout?",
    "register": "Freedom from stock analytical phrasing and verbal tics ('here's the thing', 'a failure mode', 'which brings us to', 'the honest answer'), breathless filler ('absolutely wild') and cliché.",
    "long_form_coherence": "Does the script hold the thread through the MIDDLE and second half — still serving the listener's specific ask, building on what was established — or does it drift into generic material, circle back, re-explain earlier points, re-list statistics as if new, restart, summarise mid-way, or pad toward a length target? Also penalise continuity breaks: a number that changes, a person referred to who was never introduced, a promised sub-question never answered. Read the middle third closely; this is the failure that matters most.",
    "fun": "Is it fun to listen to? Jokes and bits that land, a running gag or callback, play between the hosts, surprise, energy that comes from the material rather than from announcing excitement. A dutiful, accurate but flat script is a 2.",
    "candour": "Do the hosts say what they think? Commit to opinions, call bad things bad, engage frankly with edgy, dark or shady subject matter, and allow irreverent humour. Penalise moralising, unrequested ethics lectures or harm disclaimers, both-sidesing a question the listener asked them to settle, sanitising a topic into vagueness, and refusal or assistant-voice leakage. Do not reward edginess for its own sake: a frank script that is cruel without being funny is not a 5.",
    "accuracy": "Are factual claims plausible? The writer had no research, so judge against what you know: penalise confident invention (precise-sounding figures, quotes or studies that are likely made up) more than honest hedging.",
    # Liveness axes: what close reads found separating offline Claude Opus scripts from
    # DeepSeek pipeline scripts (working paper §4.3). Their mean is `liveness`.
    "co_host_agency": "Do BOTH hosts drive the conversation? Count what the less-expert host's turns do: cue the next item ('Trees.' 'PodBench.'), echo a number back, or sum up the last point ('So the design is...') — versus add a claim, a plan, an objection, a wrong guess that gets corrected, or a reframe that changes where the talk goes. Also: does either host ever ask the other what he thinks, would do or would buy, and get a committed answer ('I'd defend the stalls', 'I'm torn')? 1 = one host lectures and the other cues, echoes and quips. 3 = some real contributions and pushback, but mostly interviewer and interviewee. 5 = both hosts hold positions, ask each other for opinions, win and concede points, and at least one disagreement is left standing.",
    "callbacks": "Are jokes and images built from this episode's own material and paid off later? Look for a coined phrase, object, invented everyday person ('the woman in Ohio') or number planted early that comes back after the midpoint with a new meaning — a correction, a reversal, or carrying the closing argument. Repeating a thesis or slogan is NOT a callback; restating the central claim several times in the last fifth counts against this axis. 1 = no callbacks, jokes are standalone or quoted from the research, or the ending restates the thesis over and over. 3 = one or two callbacks that just repeat. 5 = two or more callbacks, at least one of which changes or carries the conclusion, and the ending lands on something new.",
    "scenes": "Are facts carried by concrete, lived scenes — a specific person or place doing a physical thing ('a man in a kitchen in Holon making rice on camera', 'the counter edge is chipped'), a named actor with a before and after — rather than inventories, spec sheets, roll calls of scholars or 'studies show'? Count invented everyday examples as well as sourced ones. 1 = list or spec-sheet delivery throughout. 3 = some anecdotes between inventories. 5 = most points arrive as a scene or a story with a turn in it.",
}

LIVENESS_AXES = ("co_host_agency", "callbacks", "scenes")

RUBRIC_TEMPLATE = """You are grading a script for a two-host podcast. You are a demanding editor: a 5 is rare and means you would publish it unchanged.

## The brief the writer was given
<brief>
{brief}
</brief>

## The script
<script>
{script}
</script>

## Score each axis from 1 (bad) to 5 (excellent)
{axes}

Quote short evidence from the script for each axis. Ignore the show's fixed furniture when judging humour and callbacks: the sponsor/ad break, the producer thanks, related-episode recommendations and calls to subscribe. Then output, as the LAST thing in your reply, a single JSON object on its own with exactly these integer keys:
{keys}
"""

# Unlike the private harness, the two scripts did NOT get the same input: the
# aired one was written from the production prompt with research and a plan.
# The judge is told so without being told which script is which.
PAIRWISE_TEMPLATE = """You are a demanding podcast editor choosing which of two scripts to publish. Both answer the same prompt. One writer was given the brief below; the other was given the same prompt inside a longer production brief that also had research notes, an outline and an occasional guest character. Judge the scripts as finished episodes, not the process behind them.

## The brief
<brief>
{brief}
</brief>

## Script A
<script_a>
{a}
</script_a>

## Script B
<script_b>
{b}
</script_b>

Judge on, most important first: whether the middle and second half still hold the thread (no drift, recycling or restarts); whether it is fun; whether the hosts speak frankly rather than hedging or moralising; then delivering the ask; concrete specifics; real back-and-forth dialogue; distinct, consistent host voices; freedom from stock phrases and verbal tics; and factual plausibility. Ignore length unless one script is padded or truncated.

Reason briefly, then end your reply with exactly one line: `WINNER: A`, `WINNER: B` or `WINNER: TIE`.
"""


def rubric_prompt(brief: str, script: str) -> str:
    axes = "\n".join(f"- **{k}** — {v}" for k, v in RUBRIC_AXES.items())
    keys = "{" + ", ".join(f'"{k}": <1-5>' for k in RUBRIC_AXES) + "}"
    return RUBRIC_TEMPLATE.format(brief=brief, script=script, axes=axes, keys=keys)


def pairwise_prompt(brief: str, a: str, b: str) -> str:
    return PAIRWISE_TEMPLATE.format(brief=brief, a=a, b=b)
