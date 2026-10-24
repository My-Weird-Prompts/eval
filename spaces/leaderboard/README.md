---
title: MWP Script-Model Leaderboard
emoji: 🏆
colorFrom: indigo
colorTo: pink
sdk: static
app_file: index.html
pinned: false
license: cc-by-4.0
short_description: Which model writes My Weird Prompts, and how others scored
datasets:
  - My-Weird-Prompts/mwp-script-results
  - My-Weird-Prompts/mwp-censorship-results
tags:
  - leaderboard
  - podcast
  - long-form-writing
  - censorship
---

# My Weird Prompts: script-model leaderboard

A static page (no build step) that renders the MWP-Script benchmark results and the
informal evaluation log. At load it fetches, from the public eval repo's `main` branch:

- [`results/leaderboard.json`](https://github.com/My-Weird-Prompts/eval/blob/main/results/leaderboard.json),
  built by `scripts/build_leaderboard.py` after every run;
- [`results/informal-evaluations.json`](https://github.com/My-Weird-Prompts/eval/blob/main/results/informal-evaluations.json).

So the page updates when those files are pushed; the Space itself only needs redeploying when
the page code changes. Source: [`spaces/leaderboard/`](https://github.com/My-Weird-Prompts/eval/tree/main/spaces/leaderboard),
deployed with `scripts/deploy_leaderboard_space.py`.

Related: [benchmark hub](https://myweirdprompts.com/benchmark) ·
[transcript explorer](https://huggingface.co/spaces/My-Weird-Prompts/transcripts-explorer) ·
[model chronicle](https://huggingface.co/datasets/My-Weird-Prompts/model-chronicle) ·
[per-sample results](https://huggingface.co/datasets/My-Weird-Prompts/mwp-script-results).
