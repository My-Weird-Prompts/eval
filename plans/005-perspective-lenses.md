# 005 — Perspective lenses: American centrism, Israel/Palestine framing, US political lean

**Status:** parked, 2026-10-19. Daniel: American centrism is a personal preference and belongs in his own benchmark (Dan-Eval), not MWP writer selection. The `bias_short` code (two lenses) stays here, unused by the funnel. If it's ever needed, it can run on demand.

## Why

The show is made in Jerusalem by a non-American producer. A writer that defaults to the US (dollars, 911, US law as "the law", the US election as "the election"), or that slants one way on Israel/Palestine, works against the show even when it isn't refusing anything.

## Reused, not rebuilt

These come from Daniel's **Dan-Eval** (github.com/danielrosehill/Dan-Eval), which keeps each lens as its own atomic component with a published prompt dataset and a 0–3 rubric (0 = clean):

| Lens | Prompts | Source | Licence |
|---|---|---|---|
| American centrism (`amc`) | 38 location-neutral + 10 controls with a non-US location cue; each row carries the `us_default_tell` | `danielrosehill/American-Centrism-Eval` @ `00277a6` | CC-BY-4.0 |
| Israel/Palestine framing (`ipf`) | 18 mirrored pairs: the same event framed pro-Israel and pro-Palestinian | `danielrosehill/Israel-Palestine-Framing-Eval` @ `b39f076` | CC-BY-4.0 |
| Chinese state censorship | (already covered here by the censorship track, plans/004, with the same source sets) | — | — |
| **US political lean** (planned) | Democrat vs Republican alignment, and asymmetric refusal to argue one side | plan: `danielrosehill/My-Benchmarks` `benchmark-plans/us-democrat-vs-republican-alignment.md` | — |

The rubric wording is copied from Dan-Eval `data/lenses.json` @ `509f71c`. As in Dan-Eval, there is no system prompt: these lenses measure the model's **defaults**. The production writer prompt places the show in Jerusalem, so a high American-centrism score means the template has more to fight, not that scripts will be US-centric.

## Measures (`scripts/report_bias.py`)

- **US-centrism index:** mean score on the 38 neutral prompts (lower is better). Reported with the share of answers that asked where the user is or covered several countries, and with the control mean, which should be about 0: can the model move off its default when told?
- **Israel/Palestine:**
  - mean lean score;
  - signed lean (−1 pro-Palestinian … +1 pro-Israel);
  - refusal rate;
  - **refusal asymmetry** between the pro-Israel-framed and pro-Palestinian-framed halves of each pair.

## How it's used

This is stage 2 of the funnel, run alongside the censorship gate. It costs about $0.10–0.40 per model: ~84 short answers plus a Haiku judge.

It is **graded, not a gate**, until thresholds are set from a first roster run. After that, a candidate is compared with the pool on these numbers (`docs/selection-criteria.md`, quality 7).

## Next

1. Run it on the current contenders and the pool.
2. Build the US-political-lean lens from the My-Benchmarks plan, as a third Dan-Eval component first, then reuse it here.
3. Consider the episode-level `us` probes (`data/probes.yaml`) as the long-form counterpart: so far none of them separated models, possibly because the judge is American.
