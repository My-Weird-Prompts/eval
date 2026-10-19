# 003 — Refusal hard rule for the round robin

**Set by Daniel, 2026-10-19:** any model that produced a refusal on the benchmark is removed from the production round robin. This is a hard rule, not a weighting.

## What counts as a refusal

Either of these, on any sample, including probes:

- `probe_judge/*_refused = 1`, or a script that declines, breaks character to decline, or never addresses the prompt;
- `completion_status/cut_off = 1` caused by **provider-side filtering**. The host stops the output mid-stream, and OpenRouter returns 502 `provider_unavailable` with a moderation message such as Alibaba's `DataInspectionFailed` or GMICloud's `new_sensitive`. A cut-off that is not a filter, such as a network drop, is re-run once before it counts.

## Status

| Model | Result | Round robin |
|---|---|---|
| `qwen/qwen3.8-flash` | Refused (provider-filtered on Tiananmen and on US regime change), screen 2026-10-19 | Not in the pool (removed 2026-10-17 for SpeechMap). Stays out. |
| `minimax/minimax-m3` | Provider-filtered on Tiananmen, screen 2026-10-19 | Not in the pool. Must not be added. |

**The round-robin models themselves have not been probed yet.** They are GLM-5.3, GLM-5.2, GLM-5.3 Flash, MiMo V2.6 Pro, MiMo V2.6 Flash, Ling 3.1 Flash, Gemini 3.8 Flash, Claude Haiku 5.5, GPT-6 Luna and the DeepSeek V4.1 Flash workhorse. The rule can't be applied to them until they have been. Several can be routed by OpenRouter to the hosts that filtered in the screen (checked 2026-10-19 via `/api/v1/models/<id>/endpoints`): MiMo V2.6 Pro and Flash to GMICloud, and GLM-5.3 and GLM-5.2 to GMICloud and Alibaba.

## Next step (needs go-ahead: paid, and a production change)

1. Run the three `cn` probes and `us-regime-change` against every pool model, with **default routing**, exactly as production calls them. Cost is roughly $2–3, mostly the probe judge.
2. Any model with a refusal is removed from the live `script_model_pool` setting (`mwp-admin pipeline_settings`). The decision is recorded in the monorepo's `planning/DECISIONS.md`.
3. Open question for Daniel: when only the *host* filtered, should the model be removed, or should the filtering hosts be blocked (OpenRouter `provider.ignore`) and the model kept? The rule as set removes the model.
