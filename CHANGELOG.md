# Changelog

Scores are comparable only within one benchmark version. Any change to the task card (`prompt.py`), the judge prompts (`judge.py`), the dataset pin or the headline formula is a new version.

## v1.0 — 2026-10-19

- Task card `PROMPT_VERSION = "v1.0"`; target 3,800 words (3,400–4,200), `max_tokens` 10,000, temperature 1.0.
- Dataset `My-Weird-Prompts/episodes-eval` @ `73bf1020144f3fd5bb78c7bc30e78b07e2f9238c`, rows with `has_prompt` (189); `lite` = first 40 by SHA-1 of slug.
- Rubric: 12 axes (private harness axes minus `cameo_integration`; `accuracy` as plausibility). Default judge `openrouter/anthropic/claude-opus-5.5`.
- Headline `v1_score` = 25 × (priority − 1), gated on `parse_ok` and length ratio 0.8–1.2.
