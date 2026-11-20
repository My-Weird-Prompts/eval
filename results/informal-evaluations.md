# Informal evaluations

Light verdicts on script-writer models that wrote real, aired episodes. Claude
judges by reading one or two scripts per model; Daniel's own impressions are quoted
where he gave them. These are production-trial evidence, read alongside the
benchmark runs in [`README.md`](README.md). Procedure: mwp-admin skill
`informal-model-eval`, which also writes the same entries to [`informal-evaluations.json`](informal-evaluations.json). Newest first.

---

## 2026-11-20: Writer trial, "Search From Scratch" (5 parts): Qwen4 Max, Gemini 4 Carbon, Gemini 4 Hydrogen, Kimi K3.1 Pro vs GLM-5.3

**Method (Claude-supervised, impromptu; mwp-admin skill `writer-trial`):** each part of a five-part series went out as a pipeline `script_only` job, with the same prompt and `host_notes` (series hand-offs and "stay off" fences) for every candidate. GLM-5.3, the live writer, drafted every part as the baseline. **Judge:** Claude (`claude-opus-5-5`), one subagent per part, **not blind**, reading each raw draft whole before any edit. Verdicts: `pass` (airs with light edits), `marginal` (airs only with heavy edits), `fail`. One challenger draft per part was then edited by Claude and aired, credited to the model that wrote it. Airing it is the human evaluation.

| Part | GLM-5.3 | Qwen4 Max | Other challenger | Aired (ep.) |
|---|---|---|---|---|
| 1 Inverted index | pass | pass | Kimi K3.1 Pro: marginal | Qwen4 Max ([#6708](https://myweirdprompts.com/episode/grep-ripgrep-inverted-index-23722/)) |
| 2 BM25 | marginal | pass | Gemini 4 Carbon: pass | Gemini 4 Carbon ([#6710](https://myweirdprompts.com/episode/why-bm25-ranking-works-18376/)) |
| 3 Keyword to semantic | marginal | marginal | Kimi K3.1 Pro: marginal | Kimi K3.1 Pro ([#6712](https://myweirdprompts.com/episode/learned-sparse-retrieval-embeddings-58372/)) |
| 4 Embeddings by hand | pass | marginal | Gemini 4 Hydrogen: marginal | Gemini 4 Hydrogen ([#6709](https://myweirdprompts.com/episode/exact-search-transcript-embeddings-91875/)) |
| 5 Hybrid and evaluation | marginal | pass | Gemini 4 Carbon: marginal | Gemini 4 Carbon ([#6711](https://myweirdprompts.com/episode/reciprocal-rank-fusion-eval-05315/)) |

- **Qwen4 Max:** the deepest mechanics and best jokes of the session, for example IDF as surprisal ("half the corpus is worth one bit") and its pooling-bias jab at BEIR ("the answer key was written by the student being compared against"). It runs 1.2–1.5× long and faded on later parts.
- **Gemini 4 Carbon:** wrote the cleanest challenger draft (Part 2). Its Part 5 spent the middle on reranker literature where the brief said to place the reranker, and made arithmetic slips.
- **Gemini 4 Hydrogen:** the sharpest section on where brute-force search stops working. It also had structural slips: lines given to the wrong host and a call-in answered before the caller spoke.
- **Kimi K3.1 Pro:** the most conceptually sharp writer, about 1.6× long, and it recites research tables. Its Part 3 broke the "stay off fusion" fence.
- **GLM-5.3 (baseline):** the most disciplined on length and the least reliable on facts. Its Part 2 put the archive at about 400 episodes and argued from that.
- **Across all models:** no challenger was clearly better than GLM-5.3 overall: livelier and deeper, not cleaner. The series fences failed for every model. Every Part 4 draft understated the archive's size (about 6,700 episodes, roughly 100–180k chunks). Shared tics: Herman quizzing Corn, numbered-episode outro plugs, research mechanics said on air.

**Cost:** the 15 drafts cost about $0.80 in total.
**Caveats:** one prompt per part, one non-blind Claude judge, and research that differs per run. This is not a ScriptBench score and is not comparable with `leaderboard.json`. Daniel's verdicts, by listening, are pending.
**Drafts:** each raw draft is at `https://episodes.myweirdprompts.com/scripts/by-job/<job_id>.txt`; the job IDs are in [JSON](informal-evaluations.json).

---

## 2026-11-02: GLM-5.3 vs Claude Sonnet 5.5 vs Mistral Large 4 vs Gemini 3.8 Flash (blind)

**Judge:** Claude (`claude-opus-5-5`) as a blind subagent, letters shuffled per episode. **Prompts:** [Eval-Prompts](https://huggingface.co/datasets/My-Weird-Prompts/Eval-Prompts) `ep-01` (typeface + Hebrew font) and `ep-02` (slowest civilizations). The challengers ran as pipeline `script_only` jobs. Sonnet's samples are the aired episodes #6407 and #6403.

| Rank | ep-01 | ep-02 |
|---|---|---|
| 1 | Sonnet 5.5 | GLM-5.3 |
| 2 | GLM-5.3 | Sonnet 5.5 |
| 3 | Mistral Large 4 | Mistral Large 4 |
| 4 | Gemini 3.8 Flash | Gemini 3.8 Flash |

- **GLM-5.3:** the most evidence-minded writer, with a vivid primary-source day-in-the-life and an opinionated Corn. No Herman quizzing. Weakness: continuity and attribution glitches.
- **Sonnet 5.5:** warm and natural, and Corn pushes back. One Herman-quizzes-Corn question and some hedging.
- **Mistral Large 4:** clipped, natural lines, but tutorial-like stretches. Two Herman-quizzes-Corn questions on ep-02.
- **Gemini 3.8 Flash:** lecture-like with no contractions, Corn echoing Herman, shaky details. Consistent with its EQ-Bench slop score (22.6).

**Cost:** Sonnet is about $0.35–0.37 of LLM spend per aired episode. The 6 challenger runs cost $0.94 together, all stages included.
**Caveats:** two prompts, one Claude judge (a possible house-style bias toward Sonnet), and research that differs per run. Daniel's verdict is pending.

---

## 2026-10-24: Muse Spark 1.3 vs Claude Sonnet 5.5 vs GPT-6.1 Sol

**Judge:** Claude (`claude-opus-5-5`). **Models:** `meta/muse-spark-1.3`,
`anthropic/claude-sonnet-5.5`, `openai/gpt-6.1-sol`.

### Episodes read

| Model | Episode | How written |
|---|---|---|
| Muse Spark 1.3 | #6220 `mixture-of-experts-active-parameters-33076` | pipeline |
| Muse Spark 1.3 | #6229 `voice-design-tts-knobs-17599` | pipeline |
| Sonnet 5.5 | #6223 `fine-tuning-epoch-count-guide-05662` | offline (Claude Code `offline-script-writer`), voiced by pipeline |
| Sonnet 5.5 | #6227 `cork-chippers-double-fry-science-35844` | offline, voiced by pipeline |
| GPT-6.1 Sol | #6234 `phone-mic-dictation-setup-44697` | pipeline |
| GPT-6.1 Sol | #6232 `daycare-germs-building-immunity-83083` | pipeline |

Muse Spark 1.3 wrote three episodes in this window (#6137, #6220, #6229). Every
Sonnet 5.5 episode since 2026-10-19 is `episode_type=script` (offline), so the
Sonnet samples had their own research notes and prompt, not the pipeline's. They
aren't like for like.

### Cost per script (OpenRouter, 2026-10-24)

Standard mix: 26k input tokens (9k cached) and 6.5k output.

| Model | $/M in / cached / out | $/script |
|---|---|---:|
| Muse Spark 1.3 | 1.25 / 0.15 / 4.25 | **~$0.05** |
| Sonnet 5.5 | 2.00 / 0.10 / 10.00 | ~$0.10 (offline runs cost subscription, not this) |
| GPT-6.1 Sol | 2.00 / 0.10 / 10.00 | ~$0.10, plus low-effort reasoning tokens |

### Impressions

- **GPT-6.1 Sol: the best of the three.** It's the most accurate and the most
  careful about what a source does and doesn't show ("I'm not giving the beamformer
  credit for work it may not have done"). It handles a personal health prompt with
  real judgement. Corn has real agency: he makes analytical points, not just quips.
  The humour is dry and lands. Weaknesses: the register is a little formal and
  British ("an appalling interpretation of convenience"), so it's less warm than
  Sonnet, and Hilbert's cameo monologues ramble.
- **Muse Spark 1.3: solid value, clearly a step down.** It's dense, factual, on
  length and cheap. But Corn turns into a quip machine: nearly every Corn line is a
  three-to-five-word aphorism ("Store an elephant, ride a bicycle", "Death by
  tapas"). There are speaker slips: in #6229 Corn delivers Herman's research, and
  Hilbert answers Herman as "Corn". It drops question marks ("Is that roughly
  right."), which hurts TTS prosody. The Hilbert cameos are its best moments.
- **Sonnet 5.5: the liveliest and warmest, but offline-written.** It has the best
  guest voice (Roy the Cork plumber), a real two-sided argument with the Daniel
  clone, and natural long turns. Its honest hedging is good, but it slips into
  narrating research mechanics on air ("I've only seen that in a search snippet").
  At OpenRouter prices it costs the same as Sol, so it has no value edge in the pipeline.
- **Every model, so the prompt drives it:** formulaic hand-offs ("Corn, would you...?",
  "Do you buy that, Corn?") and non-sequitur cameo inserts. Don't score these against one model.

### Daniel's impressions

> "Sol seems very good, no complaints about it."

None given for Muse Spark or Sonnet. He didn't remember which episodes Muse Spark
had written, so the lookup above answers that.

### Verdict

Keep **GPT-6.1 Sol** as the writer. **Muse Spark 1.3** is the fallback if cost
pressure appears: about half the price per script, but expect weaker co-host play
and TTS-unfriendly punctuation. **Sonnet 5.5** is worth it only offline, where its
cost is already paid. In the pipeline it costs what Sol costs and isn't better.
