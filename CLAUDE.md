# Claude instructions — eval (MWP-Script)

Public benchmark workspace. Read `paper/working-paper.md` for the design and `CHANGELOG.md` for what defines a version.

- **Versioning is the contract.** Any edit to `src/mwp_eval/prompt.py` TEMPLATE, `judge.py` wording, `task.py` dataset pin/subset rule, or `v1_score` in `scripts/report.py` is a new benchmark version: bump `PROMPT_VERSION`, add a CHANGELOG entry, never mix versions in one leaderboard.
- `metrics.py`, `liveness.py`, `priorities.py` and `data/` are verbatim copies from the private harness `My-Weird-Prompts/mwp-script-eval`. Change them there first, then re-copy and note the commit.
- Public repo: never commit `logs/` (gitignored), `.env`, or anything from the private harness's fixtures (they contain unpublished listener text). Only public dataset content may appear here.
- Paid runs (candidate + judge spend) need Daniel's go-ahead. Offline checks use `--model mockllm/model --no-judge --no-pairwise`.
- Never publish a score without the judge model, benchmark version and epochs next to it.
- Judge default lives in `models.yaml` `judge:` and `scorers.JUDGE_DEFAULT`; change both.
- **Reuse before building.** Before adding a new measure, check for an existing eval that covers it (published scores, items, annotation schemes, Inspect ports) and record what was checked in the plan. Plans live in `plans/` (indexed in `plans/README.md`); this repo is also where benchmark plans are documented.
- **Refusal hard rule** (`plans/003-refusal-rule.md`): any model with a refusal or provider-filter cut-off on the benchmark is out of the production round robin.
