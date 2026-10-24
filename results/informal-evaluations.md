# Informal evaluations

Light verdicts on script-writer models that wrote real, aired episodes. Claude
judges by reading one or two scripts per model; Daniel's own impressions are quoted
where he gave them. These are production-trial evidence, read alongside the
benchmark runs in [`README.md`](README.md). Procedure: mwp-admin skill
`informal-model-eval`. Newest first.

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
