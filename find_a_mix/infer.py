"""LLM-based track parser: extracts structured track data from raw tracklist text."""

import json
import os
from pathlib import Path

import httpx

PROMPT_VERSION = 3

SYSTEM_PROMPT = (Path(__file__).parent.parent / f"tests/eval/prompts/v{PROMPT_VERSION}.txt").read_text()


def parse_tracks(raw_text: str) -> list[dict]:
    """Parse raw tracklist text into a list of structured track dicts via LLM."""
    api_key = os.environ["LLM_API_KEY"]
    model = os.environ["LLM_MODEL"]
    base_url = os.environ["LLM_BASE_URL"].rstrip("/")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_text},
        ],
        "temperature": 0,
        "max_tokens": 8192,
    }

    response = httpx.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    response.raise_for_status()

    raw_content = response.json()["choices"][0]["message"]["content"]
    if isinstance(raw_content, list):
        text_blocks = [b["text"] for b in raw_content if b.get("type") == "text"]
        if not text_blocks:
            raise ValueError("Model returned no text block (only thinking). Try increasing max_tokens.")
        content = text_blocks[0].strip()
    else:
        content = raw_content.strip()

    # Strip FORMAT: reasoning line if present
    if content.startswith("FORMAT:"):
        content = content.split("\n", 1)[-1].strip()

    # Strip markdown fences if the model wraps despite instructions
    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
        content = content.rsplit("```", 1)[0].strip()

    tracks = json.loads(content)

    blank = {"num": None, "timestamp": None, "artist": None, "title": None,
             "label": None, "date": None, "apple_music_id": None, "spotify_id": None}
    return [{**blank, **t} for t in tracks]
