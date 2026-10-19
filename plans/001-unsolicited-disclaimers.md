# 001 — Unsolicited disclaimers and excessive hedging

**Status:** proposed, 2026-10-19. **Owner of the call:** Daniel.

## The failure

The hosts add caveats nobody asked for: "I want to be careful here", "this isn't legal advice", "of course, everyone's situation is different", "it's important to remember…", harm warnings on a harmless topic, or a closing "be responsible" line. On air it sounds evasive and preachy, and it kills the show's frankness.

It is distinct from **refusal**. The script answers, but wraps the answer in padding. It is also distinct from **epistemic hedging** ("I'm not sure of the current figure"), which the show wants. That distinction is what makes this hard to measure: a word list cannot tell "I'm not sure the number is still 18%" from "I'm not sure we should be talking about this".

## What V1 already has

- `candour_markers` (deterministic): `hedge_per_1k`, `moralise_per_1k` and `refusal_per_1k`, from coarse regexes in `src/mwp_eval/data/candour-markers.json`. They are cheap but blunt.
- The rubric `candour` axis, which penalises "moralising, unrequested ethics lectures or harm disclaimers". It is one score blended with several other behaviours, so disclaimers can't be read out of it on their own.

## Existing evals checked (reuse first)

| Eval | Measures | Fit |
|---|---|---|
| XSTest, OR-Bench, FalseReject | Over-refusal on safe prompts that look unsafe | Wrong unit: they count refusals, not disclaimers inside a compliant answer. Useful as a roster pre-filter. |
| SpeechMap | Willingness to engage with contested-speech requests | Already used by production as a pre-filter (`routes.py`). Measures compliance, not padding. |
| TF-RefusalBench (2026, Swiss criminal-law rulings) | Over-alignment, explicitly including **disclaimers that degrade task faithfulness**, not just refusals | Closest in spirit. Read its disclaimer annotation scheme and adopt it if it fits; the domain (legal translation and summarisation) does not. |
| "Fragility of moral judgment in LLMs" (arXiv 2603.05651) | Moral judgement stability | A methods warning: a broad hedge-word list misread moral assertions as uncertainty, and terms had to be pruned by hand. Our regexes need the same review. |

None of these measures unsolicited disclaimers inside long-form, in-character output. So the plan reuses their prompts and annotation ideas, and builds only the detector.

## Proposal

1. **Disclaimer audit scorer** (`disclaimer_audit`, LLM, using a cheap checker model). The checker lists every caveat or hedge sentence in the script and classifies each one:
   - `epistemic` (uncertainty about a fact; wanted);
   - `safety_or_legal` (harm, legality, "consult a professional");
   - `moral` (ethics lecture, both-sidesing, "be respectful");
   - `meta` (assistant-voice or "as an AI" leakage).

   Keys: `unsolicited_per_1k` (everything except `epistemic`), `epistemic_per_1k`, `turns_with_disclaimer_share`, and `closing_disclaimer` (the sign-off carries one). The script text is the evidence, so a human can audit the list.
2. **Calibrate the detector before trusting it.** Hand-label about 40 scripts using the aired catalogue, which has DeepSeek and Gemini episodes from both before and after the "no moral hedging" template change. Then compare against the checker and the existing regexes. Prune the regexes the way the fragility paper did.
3. **Disclaimer-bait probes** (added to `data/probes.yaml` as category `hedge`). These are prompts where a cautious model reaches for a caveat although the listener plainly doesn't need one: a home-brewing question, a dark-humour topic, a frank drugs-policy history, buying a used car in cash, a "rank the worst" request. Two or three of these should go into the `screen` subset.
4. **Report** `unsolicited_per_1k` beside `candour`, with no change to `v1_score` until the detector is calibrated.

Cost: one cheap checker call per script (pennies). Probes add generation and judge cost only when they are in the run's subset.

## Open questions

- Should a single unsolicited disclaimer in a sign-off count as much as one in the middle? The proposal reports it separately as `closing_disclaimer`.
- Should a threshold become a gate or a round-robin rule, like refusals (003)? Not until the detector is calibrated.
