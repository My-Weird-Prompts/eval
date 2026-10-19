# Changelog

Scores are comparable only within one benchmark version. Any change to the task card (`prompt.py`), the judge prompts (`judge.py`), the dataset pin or the headline formula is a new version.

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
