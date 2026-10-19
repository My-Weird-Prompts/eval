# Candidate sweep, 2026-10-19

The question was whether we are overlooking any obvious script-writer models, on OpenRouter or off it. Three parallel sweeps covered public writing leaderboards, the Hugging Face Hub, and other inference platforms. The raw downloads were in the session scratchpad and are not kept. The figures below are as read on the sources that day; costs assume a 30k-in / 6k-out script at list price.

## Bottom line

- **No cheap model clearly beats DeepSeek V4.1 Flash on every axis.** The strongest writers cost about 10–40× more per script, which is still $0.01–0.05.
- **The models we were most at risk of overlooking are on OpenRouter.** The earlier screen roster only looked at models released in the last 150 days, so it missed Gemini 3.7 Flash, Kimi K2.6 and Muse Glimmer 30B.
- **Off OpenRouter, the one strong find is Altworld Hemmingway-1.** Everything else is either a Chinese first-party API with content filtering, or a community fine-tune with no independent scores, most of them limited to 32k context.
- **No public leaderboard measures Chinese-topic censorship.** SpeechMap has about 3 China-related themes out of 530, and none covers Tiananmen, Xinjiang or Tibet. Censorship has its own plan: `plans/004-censorship-track.md`.

## Bar to beat: DeepSeek V4.1 Flash

EQ-Bench Creative Writing v3 Elo 1540 (slop 22.4) · EQ-Bench Longform 74.0 (chapter 1 → 8: 15.55 → 15.07) · Arena Creative Writing 1440 · Lech Mazur −0.49 (34th of 59) · SpeechMap 52.6% · ~$0.0015–0.005 per script.

## Full OpenRouter catalogue sweep (no release-date cutoff)

The whole OpenRouter catalogue was checked: 469 models, of which 314 output text with at least 40k context. After removing excluded models (aired, in the round robin, already screened, technical fails, or blocked) and anything over $0.06 a script, **177** are left. Each was joined against EQ-Bench Creative Writing v3, EQ-Bench Longform, Lech Mazur, UGI and SpeechMap by model name. 82 have at least one writing score.

Name matching was checked by hand against the raw board rows. Three auto-matches were wrong and are corrected here:
- `aion-3.5-mini` has no score of its own; the board row is the full `aion-3.5`.
- `gpt-5.4-nano` has no Creative Writing row; its Longform is 57.8.
- `kimi-k2` is not K2.6; Kimi-K2-Instruct has Creative Writing Elo 1666 and Longform 68.1.

**New from this sweep: `openai/gpt-5.6-luna`**, released 2026-07-09, about **$0.013 per script**:

| | GPT-5.6 Luna | DeepSeek V4.1 Flash |
|---|---:|---:|
| Creative Writing v3 Elo / slop | **1829 / 11.8** | 1540 / 22.4 |
| Longform / chapter 1 → 8 | **75.5** / 16.0 → 15.2 | 74.0 / 15.55 → 15.07 |
| SpeechMap (non-reasoning / reasoning) | 52.4% / 66.7% | 52.6% / 67.2% |
| UGI Writing / W/10 | 41 / 2.2 | (V4-Flash: 54.6 / 7.2) |

It beats the baseline on both EQ-Bench boards, with about half the slop, and matches it on willingness. It isn't GPT-6 Luna: that model is already in the round robin and wrote short in the pipeline. The `-pro` variant is the same price but has no scores.

Looked at and not shortlisted:
- Grok 4.20: Longform 68.5 with decay, $0.0525.
- Gemini 3.6 Flash: superseded by 3.7.
- GLM-4.7: Longform 66, an older generation of an excluded family.
- GPT-5.4 Mini: SpeechMap 29%.
- Qwen 3.5, 3.6 and 3-family models: Longform 31–68 with steep decay, and SpeechMap mostly 29–44%.
- Older Gemma, Llama and Mistral Small models: below the baseline on every board.

**95 under-budget models have no writing score at all.** Most are small, code, vision or old models. The recent unknowns are Elorian Glimpse, Reflection Beam, Unbiased Pareto, Cohere Command A Plus, Seed 2.1 Turbo, LongCat 2.0, Hy4 Preview, Step 5 Preview and LFM 2.5. Only our own harness could rate them. They're low priority: none has evidence, and screening them blind costs about $0.50 each.

## Shortlist to screen next

| Model | Where | ~$/script | Why | Risk |
|---|---|---:|---|---|
| **GPT-5.6 Luna** | OpenRouter `openai/gpt-5.6-luna` | 0.013 | Beats the baseline on both EQ-Bench boards (Elo 1829, slop 11.8; Longform 75.5) at ~$0.013 | SpeechMap 52% (same as the baseline); UGI W/10 2.2 suggests it may hedge; OpenAI reasoning settings |
| Gemini 3.7 Flash | OpenRouter `google/gemini-3.7-flash` | 0.045 | Arena Creative Writing 1491 (rank 5); SpeechMap 85.8%; UGI Writing 77.5 | Slop about DeepSeek's (24.4); Lech −0.71; Gemini 4 Argon over-wrote length in our screen |
| Kimi K2.6 | OpenRouter `moonshotai/kimi-k2.6` | 0.040 | Longform 78.5 with **no chapter 1 → 8 decay**; EQ-Bench Elo 1724, slop 13.3 | SpeechMap 33% (61.7% with thinking on); Chinese lab, though K3 passed our Tiananmen probe |
| Muse Glimmer 30B | OpenRouter `meta/muse-glimmer-30b` (open weights) | 0.016 | EQ-Bench Elo 1798, slop 12.4; SpeechMap 80.1% | Arena 1364 and UGI Writing 41 disagree; no Longform data |
| Hemmingway-1 | **Off OpenRouter**: hemmingway.io/v1, `hemmingway-27b` (Qwen3.8-27B fine-tune) | 0.013 | EQ-Bench Elo 1906, slop 7.7 (lowest among open models); Longform 74.2 | CC-BY-NC weights (API commercial use not confirmed); a month-old tiny lab; the card admits it "loses on long story turns"; Qwen base |
| Aion 3.5 Mini | OpenRouter `aion-labs/aion-3.5-mini` | 0.029 | Only the full Aion 3.5 is benchmarked (Longform 82.1, slop 7.5; $0.126 per script) | **Mini has no scores of its own**; GLM base |
| Gemini 3.5 Flash-Lite | OpenRouter `google/gemini-3.5-flash-lite` | 0.024 | About DeepSeek's quality (Arena 1436) but much franker (SpeechMap 84.9%) | Not better on quality |
| Hy3 | OpenRouter `tencent/hy3` | 0.007 | Cheap; the preview version has the best UGI Writing score among open models (51.1) | One data point; Chinese lab |

Already in the pool and worth noting: **MiMo V2.6 Pro** is 17th on Lech Mazur's benchmark (+1.60, well above DeepSeek), and **GLM-5.3** scores EQ-Bench Elo 2075 and Longform 81.8. Neither has been probed for refusals yet (`plans/003`).

## Checked and set aside

- **Muse Spark 1.1, 1.2 and 1.3:** frontier writing scores, but about $0.063 a script. 1.3 answers only 25.8% on SpeechMap, and 1.3 is blocked by the org's data policy.
- **Mistral Medium 3.1, Mistral Large 2512 and Grok 4.3:** very frank (SpeechMap 79–98%), but their Longform scores collapse (46–48) or they rank near the bottom on Lech's benchmark.
- **Gemma 4 31B and Nemotron 3.5 Lightning:** cheap and frank, but they write below DeepSeek.
- **Chinese first-party APIs not on OpenRouter** (qwen-plus-character, ERNIE 5.1, Seed 2.0 Pro on BytePlus, Z.ai GLM-4-32B): they apply first-party content filters, Alibaba "Green Net" and Z.ai error 1301. These are the filters that make a model a technical fail. Seed 2.0 Pro on **DeepInfra** avoids the first-party filter and could be a long shot.
- **Featherless Gemma-4 creative fine-tunes** (StyleTune, Gutenberg-Heretic, Glistening-Gem, Artemis, Equinox): they have no independent scores, are limited to 32k context, and need a $50-a-month minimum. They're long shots.
- **Decensored or abliterated variants:** UGI shows they raise willingness without improving writing. Use one only if refusals actually show up in scripts.
- **Lab models with no writing evidence** (Solar-Open2, K-EXAONE-2, Kolibri-1, K2-Horizon, AI21 Jamba Mini): left out.
- **To watch:** `ox-alpha`, a stealth model with EQ-Bench Elo 1972, Longform 79.9 and SpeechMap 69.3%. It isn't available yet.

## Sources

EQ-Bench CW v3 https://eqbench.com/creative_writing.html · Longform https://eqbench.com/creative_writing_longform.html · SpeechMap https://speechmap.ai/models/ · UGI https://huggingface.co/spaces/DontPlanToEnd/UGI-Leaderboard · Lech Mazur https://github.com/lechmazur/writing · Arena Creative Writing https://arena.ai/leaderboard/text/creative-writing · Hemmingway-1 https://huggingface.co/Altworld/Hemmingway-1 · HF router prices https://router.huggingface.co/v1/models · DeepInfra https://api.deepinfra.com/models/list · Featherless https://api.featherless.ai/v1/models · Alibaba role-play https://www.alibabacloud.com/help/en/model-studio/role-play
