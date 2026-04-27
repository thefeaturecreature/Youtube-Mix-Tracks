# unmix

Finds the tracklist for a DJ mix on YouTube. Searches the video description, comments, MixesDB, and 1001Tracklists in order, then uses an LLM to parse whatever it finds into a clean, consistent format.

## Pipeline

```
YouTube URL / Video ID
        │
        ▼
1. YouTube Description  ──found──▶ parse_tracks()
        │ not found
        ▼
2. YouTube Comments     ──found──▶ parse_tracks()
        │ not found
        ▼
3. MixesDB              ──found──▶ parse_tracks()
        │ not found
        ▼
4. 1001Tracklists       ──found──▶ parse_tracks()
        │ not found
        ▼
   (no tracklist found)
```

`parse_tracks()` calls an LLM via OpenAI-compatible API and returns a consistent list of tracks with fields: `num, timestamp, artist, title, label, date, apple_music_id, spotify_id`.

## Setup

### Install

```bash
pip install -e .
```

### API Keys

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

| Variable | Where to get it |
|---|---|
| `YOUTUBE_API_KEY` | [Google Cloud Console](https://console.cloud.google.com) — enable YouTube Data API v3 |
| `LLM_API_KEY` | Your LLM provider (default: [Mistral](https://console.mistral.ai)) |
| `LLM_MODEL` | Model name, e.g. `devstral-small-2507` |
| `LLM_BASE_URL` | Provider base URL, e.g. `https://api.mistral.ai/v1` |
| `ACRCLOUD_HOST` | [ACRCloud](https://console.acrcloud.com) — audio fingerprinting (optional, not yet wired) |
| `ACRCLOUD_ACCESS_KEY` | ACRCloud |
| `ACRCLOUD_ACCESS_SECRET` | ACRCloud |

### 1001Tracklists

The 1001Tracklists scraper uses Playwright and requires a visible browser window to bypass the site's JS gate. Install the browser once:

```bash
playwright install chromium
```

## Usage

```bash
# By video ID (no quoting needed)
unmix W21yvhnjrOw

# By full URL (quote to escape shell special chars)
unmix 'https://www.youtube.com/watch?v=W21yvhnjrOw'

# Save to a file
unmix W21yvhnjrOw -o tracklist.md

# Link timestamps to YouTube playback position
unmix W21yvhnjrOw -t
```

## Output

```
# Groovy Disco Mix // Happy Uplifting Music
[Listen](https://www.youtube.com/watch?v=W21yvhnjrOw)

01 [00:00] Spooky (Quinten 909 Extended Remix) - Dusty Springfield
02 [04:30] Got 2 Be Loved - Soul Reductions
03 [10:15] She Can't Love You (Purple Disco Machine Edit) - Purple Disco Machine, Chemise
...

_Source: YouTube description_
```

With `-t`, timestamps become clickable links to that position in the video.

## Eval

The LLM parser is evaluated against a set of JSON fixtures in `tests/eval/`. Each fixture contains `raw_text` (the input) and `tracks` (expected structured output).

```bash
# Run all fixtures
python tests/eval_runner.py

# Run a single fixture
python tests/eval_runner.py tests/eval/yt_desc_timestamped.json

# Slower rate-limited models
EVAL_DELAY=3 python tests/eval_runner.py
```

Prompt versions are stored in `tests/eval/prompts/vN.txt`. Bump `PROMPT_VERSION` in `find_a_mix/infer.py` when changing the prompt — scores are logged to `tests/eval/scores.jsonl` after each full suite run.

Current baseline: **v3 prompt, devstral-small-2507, 99.9% across 6 fixtures**.
