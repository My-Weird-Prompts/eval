# Plans

What the benchmark should measure next and how. A plan is a proposal until it ships as a versioned change (see `../CHANGELOG.md`). Newest first.

| # | Plan | Status |
|---|---|---|
| 006 | [Reasoning mode as a variable](006-reasoning-mode.md) | Proposed; strongest lead for holding the middle |
| 005 | [Perspective lenses (from Dan-Eval)](005-perspective-lenses.md) | Parked: kept in Dan-Eval, not MWP selection |
| 004 | [Censorship track: separate axis and results dataset](004-censorship-track.md) | Proposed |
| 003 | [Refusal hard rule for the round robin](003-refusal-rule.md) | Rule set 2026-10-19; round-robin models not yet probed |
| 002 | [Human preference layer](002-human-preference.md) | Proposed |
| 001 | [Unsolicited disclaimers and excessive hedging](001-unsolicited-disclaimers.md) | Proposed |

## Principle: reuse before building

If an existing evaluation already measures something, use it, adapt it, or cite its numbers. Don't build a new one. In order:

1. **Use published scores** to pre-filter the roster. Production already does this with SpeechMap (willingness to engage with contested speech) and EQ-Bench Longform (long-form writing quality); see the monorepo's `pipeline/config/routes.py`.
2. **Adopt an existing benchmark's items or annotation scheme** when it measures our failure mode, and run them through our harness, where Inspect AI ports exist.
3. **Build our own only for what is specific to this show:** long-form two-host dialogue, holding the middle, the hosts' voice and register, and prompts in the show's own style. A plan that proposes a new measure says which existing evals were checked and why they don't fit.
