"""Detect and extract tracklist patterns from raw text."""

import re

TIMESTAMP_RE = re.compile(r"\b[tT]?\d{1,2}:\d{2}(?::\d{2})?\b")
TRACKLIST_HEADER_RE = re.compile(r"tracklist|track\s*list|track\s*listing", re.IGNORECASE)
NUMBERED_LINE_RE = re.compile(r"^\s*\d+[\.\)]\s+.+", re.MULTILINE)
# Separator lines like "---", "===", or repeated dashes/underscores
SEPARATOR_RE = re.compile(r"^[-=_—]{3,}\s*$", re.MULTILINE)
# Lines anchored by a leading [MM:SS] or [tMM:SS] timestamp vs. a leading NN. number
_TS_ANCHOR_RE = re.compile(r"^\s*\[[tT]?\d{1,2}:\d{2}(?::\d{2})?\]", re.MULTILINE)
_NUM_ANCHOR_RE = re.compile(r"^\s*\d+[\.\)]\s+", re.MULTILINE)
# Blank / unknown track markers: ???, ID, or timestamp-only lines with no track info
_BLANK_MARKER_RE = re.compile(
    r"^\s*(?:\[[tT]?\d{1,2}:\d{2}(?::\d{2})?\]\s*)?(?:\?{2,}|\bID\b)\s*$",
    re.MULTILINE | re.IGNORECASE,
)
# Reply lines that look like a track identification: starts with a timestamp then content
_REPLY_TRACK_RE = re.compile(r"^\s*\[?[tT]?\d{1,2}:\d{2}(?::\d{2})?\]?\s*[-–]?\s*\S")


def looks_like_tracklist(text: str) -> bool:
    has_timestamps = len(TIMESTAMP_RE.findall(text)) >= 3
    has_numbered = len(NUMBERED_LINE_RE.findall(text)) >= 3
    # Header alone isn't sufficient — a description can mention "tracklist" without containing one
    has_header = bool(TRACKLIST_HEADER_RE.search(text)) and (has_timestamps or has_numbered)
    return has_timestamps or has_numbered or has_header


def _is_mixed_anchor_format(text: str) -> bool:
    """True if lines alternate between [MM:SS]-anchored and NN.-anchored — a partial copy-paste."""
    return bool(_TS_ANCHOR_RE.search(text)) and bool(_NUM_ANCHOR_RE.search(text))


def extract_tracklist_block(text: str) -> str | None:
    """Return just the tracklist portion of text, trimming surrounding boilerplate."""
    if not looks_like_tracklist(text):
        return None
    if _is_mixed_anchor_format(text):
        return None

    lines = text.splitlines()

    # Find where the tracklist starts.
    # Priority: tracklist header > first timestamp line > first numbered line.
    # Timestamps beat numbered lines so that numbered boilerplate (rules, steps)
    # before the actual timestamp-based tracklist doesn't become the anchor.
    start = 0
    header_match = TRACKLIST_HEADER_RE.search(text)
    if header_match:
        start = text[:header_match.start()].count("\n")
    elif len(TIMESTAMP_RE.findall(text)) >= 3:
        for i, line in enumerate(lines):
            if TIMESTAMP_RE.search(line):
                start = i
                break
    else:
        for i, line in enumerate(lines):
            if NUMBERED_LINE_RE.match(line):
                start = i
                break

    # Find where the tracklist ends: a separator line after the start, or end of text
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if SEPARATOR_RE.match(lines[i]) and i > start + 2:
            end = i
            break

    block = lines[start:end]

    # Strip trailing blank lines and hashtag-only lines
    while block and (not block[-1].strip() or block[-1].strip().startswith("#")):
        block.pop()

    return "\n".join(block).strip()


def extract_reply_tracks(replies: list[str]) -> list[str]:
    """Pull lines from reply comments that look like track identifications (timestamp - artist/title)."""
    tracks = []
    for reply in replies:
        for line in reply.splitlines():
            if _REPLY_TRACK_RE.match(line):
                tracks.append(line.strip())
    return tracks
