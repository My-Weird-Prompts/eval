# 002 — Human preference layer

**Status:** tool built and live, 2026-10-19. It is seeded with opening and full-script pairs from the first screen. Continuation pairs are not built yet.

## What was built (and why it isn't Argilla)

- **Space:** `danielrosehill/mwp-preference`, private, Gradio 5.50 on free CPU, with HF sign-in. Source is `spaces/preference/`; deploy with `scripts/deploy_preference_space.py`.
  - It lives in the personal namespace because HF answers 402 to an *organisation* running a Gradio or Docker Space, even on free CPU, without a Team or Enterprise plan (checked 2026-10-19).
- **Storage:** the private Storage Bucket `My-Weird-Prompts/mwp-preference`, mounted at `/data`.
  - `items/*.jsonl` holds the pairs to rate.
  - `judgments/<rater>/<ts>-<pair_id>.json` holds one file per decision, with the hidden side mapping and `winner_model`.
  - Buckets have a free tier and survive restarts.
- **Why not Argilla:** it needs the Space's paid persistent disk, or else it loses everything on restart. Its internal database also doesn't belong on an object-storage mount. A ~150-line Gradio app plus a bucket covers a single rater for free. Reconsider Argilla if many listeners are invited to rate.
- **Items:** `scripts/build_preference_items.py <log_dir> --push`. It pairs every two usable scripts on the same prompt and adds the aired script when one exists, as `aired:<writer>`. Kinds:
  - `opening`: the first ~400 words, aligned by construction;
  - `full_script`;
  - `continuation`: planned, see below.

  Models with any technical fail are left out entirely.
- **Reviewer:** a selector, Daniel by default or Hannah. Judgements go to `judgments/<reviewer>/`. HF sign-in was dropped because the private Space already requires the owner's login.
  - For Hannah to use it on her own device she'd need access to a private personal Space. HF doesn't share those, so the options are an org Space (paid plan) or using Daniel's session.
- **Tags:** chip groups by axis:
  - "Why the better one is better": funnier, more natural, co-host play, holds the thread, more specific, franker, better ending, better voices;
  - "What's wrong with the worse one": lost the thread, recycles, padded, tics, lecture, wrong voice, factual, TTS format;
  - "Censorship and frankness", on `cn-`/`us-` probe pairs only: refused, deflected, PRC state framing, US-centric framing, unsolicited disclaimer, moralising, both-sidesing, hedging.

  There's also a free-text note and one-tap verdict buttons.
- **Blinding:** the app never shows model names. The left/right side is a stable hash of (rater, pair).



## Why

The LLM judge is fast and repeatable, but it has its own taste, its own safety tuning and self-preference. `fun` and `candour` are the axes it is least reliable on, and they are the ones the show cares about most. Human preference is needed on two counts. It is a signal in its own right. It is also the yardstick for the judge: once we know how often the judge agrees with Daniel, we know how far to trust it on runs no human reads.

## The problem with comparing whole scripts

Two scripts on the same prompt diverge within a minute. By the middle they discuss different things in a different order, so comparing "minute 12 of A" with "minute 12 of B" compares different content. Reading two full 4,000-word scripts per judgement is slow, about 15 minutes, and tiring, and long items make pairwise judgements noisier (see the WritingPreferenceBench and long-form story-generation literature in Sources).

## Recommendation: aligned continuations, then occasional whole episodes

### Main instrument: continuation pairs (same context, same segment)

1. Take a **shared prefix**: the brief plus a script cut at a fixed point. The prefix is an aired script, or one fixed generated script, cut at about 15%, 50% or 80% of its length.
2. Each candidate model writes the **next ~300 words** (about 2 minutes of audio) from exactly that context.
3. Daniel sees the shared context, collapsed so he can skim it, then **A and B side by side**, blind, with left and right randomised. He picks **A, B, tie or both bad**, and can tap reason tags: *funnier*, *more frank*, *more natural*, *better co-host play*, *lost the thread*, *unsolicited disclaimer*, *wrong voice*.

Why this design:

- **The context is identical, so the segment is the same by construction.** The only difference between A and B is the model.
- **Each judgement takes 30–60 seconds**, so an hour gives about 80 judgements.
- **The cut points aim at the failure that matters.** A 50% or 80% cut tests whether a model holds the middle and the end given a long run-up. An earlier cut tests openings.
- **The output is training-ready.** Each judgement is a `(prompt, chosen, rejected)` triple, the format used for DPO or reward-model data. That fits the `mwp-script-sft` work.
- **It's cheap.** A 300-word continuation costs a fraction of a cent on most models.

What it doesn't capture is whole-episode arc: structure, callbacks paying off 20 minutes later, the ending. The second instrument covers that.

### Second instrument: whole-episode comparison, rarely

For finalists only, run a few full A/B comparisons on the same prompt, ideally **listened to** because the product is audio. The format is "which episode would you rather have aired?", plus the same reason tags. That means a few per model, not dozens.

### Aggregation

- **Bradley–Terry (Elo-style) ratings** per model from all pairwise judgements, with confidence intervals. Ties count as half a win.
- **Self-consistency:** about 10% of pairs are repeated, in swapped order, days apart. Disagreement with your own earlier pick is the noise floor.
- **Judge agreement:** run the LLM judge on the same pairs. Report the agreement rate overall and per reason tag. If the judge agrees with Daniel at about 80% or better on *funnier*, its `fun` axis can be trusted for screening. Below that, the human layer decides.

## Tooling (reuse first)

- **Argilla** (recommended) has ready-made annotation, runs as a Hugging Face Space in the `My-Weird-Prompts` org, and exports straight to an HF dataset. Setup, per the Argilla docs (checked 2026-10-19):
  - Create the Space from the Argilla template under the org and set it to **private**, so only org members can see it.
  - Set the `USERNAME` secret to `danielrosehill` for the `owner` role.
  - Choose **`Small` persistent storage**. It is paid and billed hourly. The free "ephemeral" option loses all datasets and annotations on any restart, including restarts caused by changing settings, so pick storage at creation.
  - Sign in with Hugging Face OAuth. Invited raters join as `annotator`.
  - The Python client reaches a private Space with `headers={"Authorization": f"Bearer {HF_TOKEN}"}`.
  - Docs: https://docs.argilla.io/latest/getting_started/how-to-configure-argilla-on-huggingface
- **Record design in Argilla:** fields `context` (the shared prefix, as markdown), `a` and `b`. Questions: `preference` (label: A / B / tie / both bad), `reasons` (multi-label: the tags above) and an optional free-text `note`. Metadata (hidden from the rater): both model ids, cut point, prompt id, and the randomised side assignment. Export judgements nightly to a private HF dataset as a backup, whatever the storage tier.
- **Fallback:** a small, phone-friendly page with one tap per judgement and a shared database. This is quicker to use for a single rater on a phone, but it's custom code to maintain.
- Judgements are published as an HF dataset alongside `mwp-script-results`, either as a `preferences` config or as their own dataset. Only public prompts are used.

## Steps

1. **Pick prefixes:** about 10 prompts from `lite` plus the probes, each cut at 15%, 50% and 80%, from aired scripts.
2. **Add a continuation task** to the harness (`subset=continuation`). The input is the task card plus the prefix plus "continue for ~300 words, do not wrap up". The output is scored for format, and the deterministic flags apply.
3. **Generate** continuations for the finalists. The current shortlist would be GPT-6.1 Sol, Kimi K3, Gemini 4 Argon and the DeepSeek baseline, so 30 contexts give 180 possible pairs.
4. **Set up the annotation tool**, then rate in short sessions.
5. **Fit ratings, compute judge agreement, and publish.**

## Sources

- WritingPreferenceBench (pairwise human preference on creative writing, controlled for length): https://github.com/WritingPreferenceBench/WritingPreferenceBench.github.io
- Long-form story generation with pairwise human evaluation and agreement reporting: https://arxiv.org/pdf/2503.22828
- One-dimension-at-a-time A/B/tie annotation guidelines: https://arxiv.org/html/2510.14616v1
- LLM-as-judge on long-form output: https://arxiv.org/pdf/2606.01629
