"""Create or update the PRIVATE preference Space and its private Storage Bucket.

    python scripts/deploy_preference_space.py

Idempotent. The Space `danielrosehill/mwp-preference` (Gradio, free CPU,
private, HF OAuth) runs spaces/preference/app.py. The bucket
`My-Weird-Prompts/mwp-preference` (private) is mounted read-write at /data:
items/ (pairs to rate, from build_preference_items.py --push) and judgments/
(one JSON per decision). Private personal Space = only Daniel (and anyone he adds) can open it.
"""

from __future__ import annotations

from pathlib import Path

from huggingface_hub import HfApi, Volume, create_bucket

ROOT = Path(__file__).resolve().parents[1]
# Personal namespace, not the org: HF requires a Team/Enterprise plan for an
# ORGANISATION to run Gradio/Docker Spaces even on free cpu-basic (402,
# 2026-10-19). A personal private Space on cpu-basic is free. The bucket stays
# in the org; the Space mounts it with the owner's org membership.
REPO = "danielrosehill/mwp-preference"
BUCKET = "My-Weird-Prompts/mwp-preference"


def main() -> None:
    api = HfApi()
    create_bucket(BUCKET, private=True, exist_ok=True)
    api.create_repo(REPO, repo_type="space", space_sdk="gradio", private=True, exist_ok=True)
    api.upload_folder(repo_id=REPO, repo_type="space", folder_path=str(ROOT / "spaces" / "preference"),
                      commit_message="Deploy preference app")
    api.set_space_volumes(REPO, volumes=[Volume(type="bucket", source=BUCKET, mount_path="/data")])
    api.add_space_variable(REPO, "DATA_DIR", "/data")
    print(f"https://huggingface.co/spaces/{REPO}")


if __name__ == "__main__":
    main()
