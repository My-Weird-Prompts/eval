# 006 — Reasoning mode as a variable: does "thinking" hold the middle?

**Status:** proposed, 2026-10-19. This is the most important lead from the long-context board sweep.

## Evidence

Public long-context boards show that **turning reasoning off wrecks long-context use** (checked 2026-10-19):

| Model | Board (~32k) | Reasoning on | Off / minimal |
|---|---|---:|---:|
| GPT-5.6 Luna | AA-LCR | 83.7 (max) | 42.7 (off) |
| GPT-5.5 | Context Arena MRCR v2, 8 needles | 91.5 (medium) | 35.0 |
| Gemini 3.6 Flash | MRCR v2 | 90.1 (medium) | 26.5 (minimal) |
| DeepSeek V4 Flash 0731 | AA-LCR | 80.3 (max) | 22.1 (off) |

**Production runs the writer with reasoning off**, a decision from when reasoning silently dropped temperature (monorepo `context/architecture/llm-routing.md`). The writer's plan sits at 72–88% of a ~28k prompt. Its top failure is *losing the middle*.

The offline Claude Opus episodes with the "X factor" were written with extended thinking on (`mwp-script-eval` `docs/x-factor.md`). ConStory-Bench (March 2026) finds long-story contradictions set up at 15–30% and broken at 40–60%, with errors growing with length, which is the same shape as ours.

## Proposal

Run the same finalists at **reasoning off vs low vs medium**, holding everything else fixed:
- on the `lite` subset;
- with V1 scores plus the mid-context measures (`long_form_coherence`, `recycle_middle`, `recycle_last`, and plan coverage once V2 has plans);
- recording thinking tokens, because they bill as output and add latency.

Start with GPT-6 Luna, Gemini 3.8 Flash and Haiku 5.5, which pass censorship and are in the pool, plus the best new contender.

If reasoning at low or medium clearly improves holding the middle at an acceptable cost, it becomes a pipeline setting change, which is Daniel's call. That's potentially a bigger win than any model swap.

## Methodology change

The selection criteria now treat the reasoning setting as **part of the candidate**: a model is evaluated *with* a stated reasoning setting. H3 asks for reasoning that is **controllable**, not necessarily off.
