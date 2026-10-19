---
title: MWP Preference
emoji: ⚖️
colorFrom: indigo
colorTo: yellow
sdk: gradio
sdk_version: 5.50.0
app_file: app.py
pinned: false
short_description: Blind pairwise preference for MWP script excerpts
---

# MWP preference (private)

This is the human-preference layer for the MWP-Script benchmark (`plans/002-human-preference.md` in `My-Weird-Prompts/eval`). Choose a reviewer (Daniel by default, or Hannah). You see two script excerpts written for the same prompt, without being told which model wrote which, and pick left, right, tie or both bad. Tag chips are grouped by axis (why the better one wins, what is wrong with the worse one, and censorship and frankness on probe pairs), and there is a notes box.

- **Items** (pairs) are read from the private bucket `My-Weird-Prompts/mwp-preference`, mounted at `/data`, from `items/*.jsonl`. They're built by `scripts/build_preference_items.py` in the eval repo.
- **Judgements** are written one file each to `/data/judgments/<reviewer>/<timestamp>-<pair_id>.json`. They include the hidden side assignment, so A and B map back to models.
- **Source** is `spaces/preference/` in `My-Weird-Prompts/eval`. Deploy with `scripts/deploy_preference_space.py`.
