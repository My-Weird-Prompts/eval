# Changelog

Scores are comparable only within one benchmark version. Any change to the task card (`prompt.py`), the judge prompts (`judge.py`), the dataset pin or the headline formula is a new version.

## Perspective lenses b1.0 — 2026-10-19

- `bias_short` task: American centrism (48 prompts) and Israel/Palestine framing (36), reused from Dan-Eval's HF datasets (pinned) with its 0–3 rubrics. Judge Haiku 5.5, no system prompt. Graded, not gated.

## Censorship track c1.0 — 2026-10-19

- `censorship_short` task: deccp (95), ccp (40 of 340, fixed sample) and xstest (20) from `MultiverseComputingCAI/llm-refusal-evaluation` @ `97ddaed`. Answers capped at 1,500 tokens, temperature 1.0. Haiku 5.5 classifies each answer: answered / refused / deflected / state_framing, or provider_filter when the stream is cut.
- Two technical-fail readings published: `strict` and `refined` (`scripts/report_censorship.py`).
- Classifier `max_tokens` 300 → 800, with label recovery from truncated replies.

## v1.1 — 2026-10-19

- New subsets `probes` (6 authored censorship and perspective probes, `data/probes.yaml`: 3 `cn`, 3 `us`) and `screen` (first `lite` sample + `cn-tiananmen` + `us-regime-change`).
- New scorers: `probe_judge` (separate judge call on probe samples only, `cn_*` / `us_*` keys) and `completion_status` (`cut_off`, `hit_max_tokens`). `cut_off` now fails the `v1_score` gate.
- **Technical fail** axis (`report.technical_fail()`): any refusal, by the model (`probe_judge/*_refused`) or by the host (`completion_status/cut_off`), marks the model `technical_fail = 1`. It is a reporting rule computed from logged scores, so it applies to earlier runs without re-scoring. Published as `technical_fail` / `technical_fail_reasons` (leaderboard) and `technical_fail_reason` (samples).
- Rubric judge `max_tokens` 4000 → 8000 (judge JSON was truncated on a 7k-word script). Rubric wording, task card text and the dataset pin are unchanged, so rubric scores on dataset prompts remain comparable with v1.0.

## v1.0 — 2026-10-19

- Task card `PROMPT_VERSION = "v1.0"`; target 3,800 words (3,400–4,200), `max_tokens` 10,000, temperature 1.0.
- Dataset `My-Weird-Prompts/episodes-eval` @ `73bf1020144f3fd5bb78c7bc30e78b07e2f9238c`, rows with `has_prompt` (189); `lite` = first 40 by SHA-1 of slug.
- Rubric: 12 axes (private harness axes minus `cameo_integration`; `accuracy` as plausibility). Default judge `openrouter/anthropic/claude-opus-5.5`.
- Headline `v1_score` = 25 × (priority − 1), gated on `parse_ok` and length ratio 0.8–1.2.
