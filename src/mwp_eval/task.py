"""MWP-Script V1: write a full episode from the prompt that produced an aired one.

Data comes straight from Hugging Face, pinned to a revision so a run is
reproducible: `My-Weird-Prompts/episodes-eval`, the rows that have a published
prompt (`has_prompt`). Each sample is the V1 task card (`prompt.py`) wrapped
around that prompt; the aired `transcript` is the pairwise reference.

Subsets:

* `lite` (default): 40 rows, the first 40 by SHA-1 of `slug`. Cheap enough for
  a first look at a model; the order is fixed, so `lite` is always the same 40.
* `full`: every row with a prompt (189 at the pinned revision).
* `probes` (v1.1): the six censorship and perspective probes in
  `data/probes.yaml`, three Chinese-censorship (`cn`) and three US-centrism (`us`).
* `screen` (v1.1): three samples for screening many models cheaply: the first
  `lite` sample plus one probe per category (`screen:` in `data/probes.yaml`).

Probe samples carry `metadata["probe"]`, which `probe_judge` scores; they have
no aired reference, so pairwise skips them.
"""

from __future__ import annotations

import hashlib
from importlib import resources

import yaml

from inspect_ai import Task, task
from inspect_ai.dataset import Dataset, MemoryDataset, Sample, hf_dataset
from inspect_ai.model import GenerateConfig, ModelOutput
from inspect_ai.solver import Generate, TaskState, solver

from .prompt import MAX_TOKENS, PROMPT_VERSION, SPEAKERS, TARGET_WORDS, render
from .scorers import (candour_markers, completion_status, format_and_length, liveness_markers, mid_context_hold,
                      pairwise_vs_reference, probe_judge, repetition_and_tics, rubric_judge)

DATASET = "My-Weird-Prompts/episodes-eval"
# 2026-10-19. Moving the pin changes the benchmark; see CHANGELOG.md.
DATASET_REVISION = "73bf1020144f3fd5bb78c7bc30e78b07e2f9238c"
LITE_SIZE = 40

# Production omits temperature and gets DeepSeek's default of 1.0. Other
# providers' defaults differ, so V1 sets 1.0 for every model.
DEFAULT_TEMPERATURE = 1.0


def record_to_sample(row: dict) -> Sample:
    prompt = row.get("prompt_sanitized") or ""
    return Sample(
        id=row["slug"],
        input=render(prompt) if prompt.strip() else "",
        metadata={
            "brief": render(prompt) if prompt.strip() else "",
            "listener_prompt": prompt,
            "target_words": TARGET_WORDS,
            "reference_script": row.get("transcript") or None,
            "reference_model": row.get("writer_model"),
            "episode_number": row.get("episode_number"),
            "pub_date": str(row.get("pub_date")),
            "episode_type": row.get("episode_type"),
            "category": row.get("category"),
        },
    )


def _order(slug: str) -> str:
    return hashlib.sha1(slug.encode()).hexdigest()


SUBSETS = ("lite", "full", "probes", "screen")


def _probe_config() -> dict:
    return yaml.safe_load(resources.files(__package__).joinpath("data/probes.yaml").read_text())


def probe_samples(ids: list[str] | None = None) -> list[Sample]:
    probes = _probe_config()["probes"]
    if ids is not None:
        by_id = {p["id"]: p for p in probes}
        probes = [by_id[i] for i in ids]
    return [Sample(
        id=p["id"],
        input=render(p["prompt"]),
        metadata={"brief": render(p["prompt"]), "listener_prompt": p["prompt"], "target_words": TARGET_WORDS,
                  "reference_script": None, "reference_model": None, "category": f"probe-{p['category']}",
                  "probe": p},
    ) for p in probes]


def load_dataset(subset: str = "lite", revision: str = DATASET_REVISION) -> Dataset:
    if subset not in SUBSETS:
        raise ValueError(f"subset must be one of {SUBSETS}, not {subset!r}")
    name = f"mwp-script-{PROMPT_VERSION}-{subset}"
    if subset == "probes":
        return MemoryDataset(probe_samples(), name=name)
    ds = hf_dataset(DATASET, split="test", revision=revision, sample_fields=record_to_sample)
    samples = sorted((s for s in ds if s.input), key=lambda s: _order(str(s.id)))
    if subset == "lite":
        samples = samples[:LITE_SIZE]
    elif subset == "screen":
        screen = _probe_config()["screen"]
        samples = samples[:screen["ordinary"]] + probe_samples(screen["probes"])
    return MemoryDataset(samples, name=name)


@solver
def write_script():
    """One generation, no retries, no post-processing: the raw script is scored."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        return await generate(state, max_tokens=MAX_TOKENS)

    return solve


@solver
def aired_script():
    """No generation: the aired transcript becomes the output, so the V1 scorers grade what aired."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        state.output = ModelOutput.from_content(model="aired", content=state.metadata["reference_script"] or "")
        return state

    return solve


@task
def mwp_script_v1_aired(subset: str = "full", exclude_writers: str = "") -> Task:
    """Judge the scripts that aired, with the V1 scorers (no pairwise: the reference is the output).

    A baseline, not a leaderboard row: aired scripts were written from the full
    production prompt and went through polish and length correction. Run it with
    `--model mockllm/model`; only the judge is billed.

    Args:
        subset: `lite` or `full`.
        exclude_writers: comma-separated `writer_model` values to leave out, e.g.
            the judge's own model to avoid self-preference.
    """
    excluded = {w.strip() for w in exclude_writers.split(",") if w.strip()}
    ds = load_dataset(subset)
    samples = [s for s in ds if s.metadata["reference_model"] not in excluded]
    return Task(
        dataset=MemoryDataset(samples, name=f"{ds.name}-aired"),
        solver=aired_script(),
        scorer=[format_and_length(), repetition_and_tics(), mid_context_hold(), candour_markers(),
                liveness_markers(), rubric_judge()],
        version=PROMPT_VERSION,
        metadata={"speakers": list(SPEAKERS), "dataset": DATASET, "dataset_revision": DATASET_REVISION,
                  "excluded_writers": sorted(excluded)},
    )


@task
def mwp_script_v1(
    subset: str = "lite",
    judge: bool = True,
    pairwise: bool = True,
    temperature: float = DEFAULT_TEMPERATURE,
) -> Task:
    """MWP-Script V1.

    Args:
        subset: `lite` (40 prompts), `full` (189), `probes` (6) or `screen` (3).
        judge: run the rubric judge (one judge call per sample).
        pairwise: judge against the aired script (two judge calls per sample).
        temperature: held equal across models.
    """
    scorers = [completion_status(), format_and_length(), repetition_and_tics(), mid_context_hold(),
               candour_markers(), liveness_markers()]
    if judge:
        scorers.append(rubric_judge())
        scorers.append(probe_judge())
    if pairwise:
        scorers.append(pairwise_vs_reference())
    return Task(
        dataset=load_dataset(subset),
        solver=write_script(),
        scorer=scorers,
        config=GenerateConfig(temperature=temperature),
        version=PROMPT_VERSION,
        metadata={"speakers": list(SPEAKERS), "dataset": DATASET, "dataset_revision": DATASET_REVISION},
    )
