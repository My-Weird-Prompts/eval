"""Create or update the PUBLIC leaderboard Space.

    python scripts/deploy_leaderboard_space.py            # deploy
    python scripts/deploy_leaderboard_space.py --check    # only fetch the live page

Idempotent. The Space `My-Weird-Prompts/script-leaderboard` is `sdk: static`
(index.html + app.js + style.css from spaces/leaderboard/, no build step). It
must be static: HF returns 402 for an ORGANISATION's Gradio/Docker Space
without a paid plan (checked 2026-10-19), while static org Spaces are free.

The page reads results/leaderboard.json and results/informal-evaluations.json
from raw.githubusercontent.com at load, so new results need a git push, not a
redeploy. Redeploy only when spaces/leaderboard/ changes.

Auth: the local Hugging Face token (`hf auth login`, as for
deploy_preference_space.py), with write access to the My-Weird-Prompts org.
After uploading, the script fetches the served page and fails if it doesn't
contain the app, so a 200 from the upload alone isn't taken as success.
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.request
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[1]
REPO = "My-Weird-Prompts/script-leaderboard"
SRC = ROOT / "spaces" / "leaderboard"
SERVED = "https://my-weird-prompts-script-leaderboard.static.hf.space/"
MARKER = 'src="app.js"'


def fetch(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "mwp-deploy"}), timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        return getattr(exc, "code", 0) or 0, str(exc)


def check(tries: int = 12) -> bool:
    for i in range(tries):
        status, body = fetch(SERVED)
        if status == 200 and MARKER in body:
            print(f"serving: {SERVED} (200, app found)")
            return True
        print(f"not serving yet ({status}); retry {i + 1}/{tries}", file=sys.stderr)
        time.sleep(10)
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="only verify the live page")
    args = ap.parse_args()
    if not args.check:
        api = HfApi()
        api.create_repo(REPO, repo_type="space", space_sdk="static", private=False, exist_ok=True)
        api.upload_folder(repo_id=REPO, repo_type="space", folder_path=str(SRC),
                          allow_patterns=["index.html", "app.js", "style.css", "README.md"],
                          commit_message="Deploy leaderboard page")
        print(f"uploaded: https://huggingface.co/spaces/{REPO}")
    if not check():
        sys.exit(f"{SERVED} did not serve the app")


if __name__ == "__main__":
    main()
