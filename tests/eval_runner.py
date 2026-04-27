#!/usr/bin/env python3
"""Eval runner for parse_tracks().

Usage:
  python tests/eval_runner.py                    # run all fixtures in tests/eval/
  python tests/eval_runner.py tests/eval/foo.json  # run a specific fixture
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from rapidfuzz import fuzz
from dotenv import load_dotenv

load_dotenv()

FIELDS = ["num", "timestamp", "artist", "title", "label", "date", "apple_music_id", "spotify_id"]
FUZZY_FIELDS = {"artist", "title", "label", "date"}
FUZZY_THRESHOLD = 85
SCORES_LOG = Path("tests/eval/scores.jsonl")


def _parse_tracks(raw_text: str) -> list[dict]:
    try:
        from find_a_mix.infer import parse_tracks
        return parse_tracks(raw_text)
    except ImportError:
        print("  [find_a_mix.infer not yet implemented — no LLM output to compare]\n")
        return []


def _prompt_version() -> int:
    try:
        from find_a_mix.infer import PROMPT_VERSION
        return PROMPT_VERSION
    except (ImportError, AttributeError):
        return 0


def _norm(val) -> str | None:
    return str(val).strip() if val is not None else None


def _match(field: str, expected, actual) -> bool:
    e, a = _norm(expected), _norm(actual)
    if e is None and a is None:
        return True
    if e is None or a is None:
        return False
    if field == "num":
        try:
            return int(e) == int(a)
        except ValueError:
            return e == a
    if field in FUZZY_FIELDS:
        return fuzz.ratio(e.lower(), a.lower()) >= FUZZY_THRESHOLD
    return e.lower() == a.lower()


def _display(val) -> str:
    return str(val) if val is not None else "—"


def _track_header(track: dict) -> str:
    parts = []
    if track.get("timestamp"):
        parts.append(track["timestamp"])
    if track.get("artist"):
        parts.append(track["artist"])
    if track.get("title"):
        parts.append(f"- {track['title']}")
    return " ".join(parts) if parts else "(unknown)"


def run_fixture(path: Path) -> tuple[int, int]:
    with open(path) as f:
        fixture = json.load(f)

    raw_text = fixture.get("raw_text", "")
    expected_tracks = fixture["tracks"]
    actual_tracks = _parse_tracks(raw_text)

    total = matched = 0

    print(f"\n{'═' * 70}")
    print(f"  {path.name}  —  {fixture['url']}")
    print(f"{'═' * 70}")

    n = max(len(expected_tracks), len(actual_tracks))
    for i in range(n):
        exp = expected_tracks[i] if i < len(expected_tracks) else {}
        act = actual_tracks[i] if i < len(actual_tracks) else {}

        header = _track_header(exp) if exp else _track_header(act)
        print(f"\n[{header}]")

        for field in FIELDS:
            e_val = exp.get(field)
            a_val = act.get(field)
            if field == "num" and a_val is None:
                a_val = str(i + 1)
            ok = _match(field, e_val, a_val)
            mark = "✓" if ok else "✗"
            total += 1
            if ok:
                matched += 1
            print(f"  [{field:<16}] {_display(e_val):<30} : {_display(a_val):<30} {mark}")

    pct = 100 * matched / total if total else 0
    print(f"\n{'─' * 70}")
    print(f"  {matched}/{total} fields matched ({pct:.1f}%)")

    return matched, total


def _log_results(fixture_scores: dict[str, tuple[int, int]], grand_matched: int, grand_total: int) -> None:
    pct = 100 * grand_matched / grand_total if grand_total else 0
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "prompt_version": _prompt_version(),
        "total": {"matched": grand_matched, "total": grand_total, "pct": round(pct, 1)},
        "fixtures": {
            name: {"matched": m, "total": t, "pct": round(100 * m / t, 1) if t else 0}
            for name, (m, t) in fixture_scores.items()
        },
    }
    with open(SCORES_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    paths = [Path(p) for p in sys.argv[1:]] if len(sys.argv) > 1 else sorted(Path("tests/eval").glob("*.json"))
    paths = [p for p in paths if p.name != "scores.jsonl"]

    if not paths:
        print("No fixture files found in tests/eval/")
        sys.exit(1)

    delay = float(os.environ.get("EVAL_DELAY", 1))

    grand_matched = grand_total = 0
    fixture_scores: dict[str, tuple[int, int]] = {}
    for i, path in enumerate(paths):
        if i > 0:
            time.sleep(delay)
        m, t = run_fixture(path)
        grand_matched += m
        grand_total += t
        fixture_scores[path.name] = (m, t)

    if len(paths) > 1:
        pct = 100 * grand_matched / grand_total if grand_total else 0
        print(f"\n{'═' * 70}")
        print(f"  TOTAL  {grand_matched}/{grand_total} fields matched ({pct:.1f}%)")
        print(f"{'═' * 70}")
        _log_results(fixture_scores, grand_matched, grand_total)


if __name__ == "__main__":
    main()
