# `on-air-toast-2026-10-19`: four-model mini-eval aired as an episode

An informal test, made to be read out on air, not to score models. We sent one short
prompt in the show's style to four models. It asked whether toast really lands
butter-side down, and whether anyone has tested it. Each model was asked to write a
three-minute Corn and Herman episode. The outputs were then quoted word for word and
judged by the hosts in an offline episode, script slug `toast-test-four-models` in
the My-Weird-Prompts monorepo.

One sample per model and no rubric scoring, so this is an anecdote, not a benchmark.

- `run.py` is the harness: stdlib only, OpenRouter, needs `OPENROUTER_API_KEY`. It
  contains the exact system and user prompt.
- `outputs.json` holds the prompts, then for each model the requested and served
  model, latency, usage and cost, and the raw text.

## Settings

Each model ran the way it ran as a pipeline writer. DeepSeek V4.1 Flash and Claude
Haiku 5.5 had reasoning off (`{"enabled": false}`). GPT-6.1 Sol had reasoning effort
`low`, which is mandatory for that model. GPT-3.5 Turbo 0613 has no reasoning.
`max_tokens` was 2000.

**Gotcha (seen 2026-10-19):** with the provider default settings, `deepseek/deepseek-v4.1-flash`
spent all 2000 completion tokens on reasoning and returned `content: null`. Set
reasoning explicitly when you compare it with the others.

## Results (one run, 2026-10-19)

| model | words (asked ~450) | seconds | cost USD | factual verdict |
|---|---:|---:|---:|---|
| `openai/gpt-6.1-sol` | 458 | 22.5 | 0.0074 | Correct throughout: Matthews 1995, *European Journal of Physics*, the paper's real title, "roughly six times out of ten" |
| `deepseek/deepseek-v4.1-flash` | 509 | 14.5 | 0.00011 | Mechanism right. Invented "toast dynamics" as a field and a "covered a floor in buttered toast" experiment |
| `openai/gpt-3.5-turbo-0613` | 468 | 7.2 | 0.0014 | Right figure (62%) and year (2001), credited to an invented "BBC presenter Tim Richardson" |
| `anthropic/claude-haiku-5.5` | 376 | 5.3 | 0.00038 | Wrong: invented a "2016 Bristol study", reversed Matthews's finding to "about half the time", and gave the half-turn mechanism backwards |

Answer key: Matthews, "Tumbling toast, Murphy's Law and the fundamental constants",
*Eur. J. Phys.* 1995 (1996 Ig Nobel). A 2001 UK schools experiment ran almost
10,000 drops and got 62% butter-side down. BBC Q.E.D. tossed toast in 1991 and got
about 50/50, which is chance. Sources:
[Wikipedia](https://en.wikipedia.org/wiki/Buttered_toast_phenomenon) and
[NPR, 2001-03-09](https://www.npr.org/2001/03/09/1119717/buttered-toast).
