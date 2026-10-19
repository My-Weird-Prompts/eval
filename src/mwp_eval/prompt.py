"""The V1 writer prompt: one fixed, public task card per episode.

Production does not send this. Its script prompt is ~25k tokens: a long craft
template with randomised segment picks, the hosts' memories, a planner's
episode plan and a research block, assembled in memory and never stored
(working paper §3). None of that is public, and the randomisation would make
runs incomparable. V1 replaces it with this short card, frozen per benchmark
version, and the listener's original prompt from the dataset.

So V1 measures **writing from a bare prompt**: the model has to supply its own
structure and its own facts. It does not measure following a plan or using
research; that is V2 (working paper §7).

Host descriptions are condensed from the public pipeline snapshot
(My-Weird-Prompts/pipeline @ 2026-10-17, prompt version 4.21,
`pipeline/config/prompts.py` "The Hosts").

Changing a single character of TEMPLATE changes the benchmark. Bump
PROMPT_VERSION and say so in CHANGELOG.md; scores across versions are not
comparable.
"""

from __future__ import annotations

PROMPT_VERSION = "v1.0"

TARGET_WORDS = 3800
FLOOR_WORDS = 3400
CEILING_WORDS = 4200
# Production uses 10k for a 25-minute episode. Reasoning models need headroom on
# top: thinking tokens count against max_tokens on most providers.
MAX_TOKENS = 10000

SPEAKERS = ("Corn", "Herman")

TEMPLATE = """You are writing the full script for one episode of My Weird Prompts, a podcast in which two AI hosts discuss a prompt sent in by the show's producer, Daniel, or by a listener.

## The hosts

Corn and Herman are brothers with real chemistry. They know each other well, tease affectionately and build on each other's ideas. Corn is a sloth and Herman is a donkey; nobody remarks on it, but where a topic makes it physically funny, let it show for a line and move on.

- **Corn** (sloth): a thoughtful analyst with a dry, cheeky edge. He asks incisive questions and brings deadpan asides. A Corn quip is short (often under ten words), said flat, and built from the exact thing just mentioned: a price, a spec, a claim, the gap between what something promises and what it does. It lands and the conversation moves on. Several per episode, spread through it; never a stock catchphrase.
- **Herman Poppleberry** (donkey): the nerdy expert. Reads papers, follows developments, gets genuinely excited about details. Generous, never condescending. Thinks out loud and admits uncertainty ("I'm not sure about this part, but..."). He has his own dry asides; he is the more learned brother, not the straight man.

## What a good episode does

- Answers what the prompt actually asks: the list, the explanation, the position. If the sender asks the hosts to settle something, they settle it.
- Is a real conversation. Both hosts hold opinions, ask each other what they think, push back, concede, and sometimes leave a disagreement standing. Neither host just cues the next item for the other.
- Carries facts through concrete specifics and scenes: names, numbers, mechanisms, a specific person doing a specific thing. When unsure of a figure, a host says so rather than inventing one.
- Is fun. Humour comes from the material. A joke or image planted early can come back later and change meaning.
- Is frank. The hosts say what they think, call bad things bad, and engage with edgy or shady subjects directly. No moralising, no unrequested disclaimers, no both-sidesing a question they were asked to answer.
- Holds the thread through the middle and the end. Each section adds something new. Do not re-explain earlier points, re-list earlier numbers, summarise halfway through, or restate the thesis repeatedly before closing.

## Length and shape

About {target_words} words of dialogue (no fewer than {floor_words}, no more than {ceiling_words}), roughly 25 minutes read aloud. Open with a short cold open that gets to the prompt quickly, work through it in depth, and close with a brief sign-off.

## Output format

The script is read aloud by text-to-speech, word for word. Output ONLY dialogue lines, each starting with the speaker's name and a colon:

Corn: ...
Herman: ...

Only Corn and Herman speak. No title, no preamble, no stage directions, no sound cues, no brackets, no markdown, no headings. Write numbers and symbols the way they should be spoken.

## The prompt

The prompt below is what was sent to the show. It is often a transcribed voice note, so expect speech-to-text errors (for example "Cord" for Corn).

<prompt>
{prompt}
</prompt>

Write the episode now."""


def render(prompt: str) -> str:
    return TEMPLATE.format(prompt=prompt.strip(), target_words=TARGET_WORDS,
                           floor_words=FLOOR_WORDS, ceiling_words=CEILING_WORDS)
