---
license: cc-by-4.0
language:
- en
pretty_name: My Weird Prompts — Eval Prompts
size_categories:
- n<1K
task_categories:
- text-generation
tags:
- podcast
- dialogue
- script-writing
- evaluation
configs:
- config_name: default
  data_files:
  - split: test
    path: eval-prompts.jsonl
---

# My Weird Prompts — Eval Prompts

A fixed set of 10 real prompts from the [My Weird Prompts](https://myweirdprompts.com) podcast, used to compare script-writer models on identical input. Each prompt is **verbatim** as Daniel Rosehill sent it to the production pipeline, dictation slips included, along with any `context` and `host_notes` it was sent with. Every one aired as an episode, so a model's script can be read next to the aired version.

Daniel chose to publish these (2026-11-02). They are an exception to the rule that the `episodes` and `transcripts` datasets publish no prompt text.

## Fields

| Field | Meaning |
|---|---|
| `id` | Stable id, `ep-NN-<slug>`. Never reused or renumbered. |
| `prompt` | The prompt, verbatim. |
| `context` | Background sent with the prompt ("Daniel briefed you beforehand"), or null. |
| `host_notes` | Private production direction for the writer (never read aloud), or null. |
| `category` | Rough topic: how-to, history, culture, urbanism, society, tech, diy. |
| `sender` | Always `daniel`. |
| `source_job` | The production job id. |
| `dispatched` | Date the prompt was sent (UTC). |
| `source_episode_number`, `source_episode_url` | The aired episode. |
| `aired_writer` | The model that wrote the aired script (`episodes.llm_model`). |

## Using it

```python
from datasets import load_dataset
ds = load_dataset("My-Weird-Prompts/Eval-Prompts", split="test")
```

To run a prompt through the real pipeline with a chosen writer, send it as a `script_only` job with `script_model` set. Pass `context`, `host_notes` and `sender="daniel"` exactly as given. Results and Daniel's ratings are published with the ScriptBench results: [github.com/My-Weird-Prompts/eval](https://github.com/My-Weird-Prompts/eval).

## Versioning

The set is append-only. Prompts are added under new ids and never edited, so an id always means the same input. Built by `eval-prompts/` in the eval repo.
