"""Format pipeline results as markdown."""

SOURCE_LABELS = {
    "youtube_description": "YouTube description",
    "youtube_comment": "YouTube comment",
    "mixesdb": "MixesDB",
    "1001tracklists": "1001Tracklists",
    "acrcloud": "ACRCloud",
}


def _timestamp_to_seconds(ts: str) -> int:
    parts = ts.split(":")
    parts = [int(p) for p in parts]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def _format_timestamp(ts: str, video_url: str | None, link: bool) -> str:
    if not link or not video_url:
        return f"[{ts}]"
    seconds = _timestamp_to_seconds(ts)
    url = f"{video_url}&t={seconds}s"
    return f"[[{ts}]({url})]"


def _format_track(i: int, track: dict, pad: int = 2, video_url: str | None = None, link_timestamps: bool = False) -> str:
    num = str(track.get("num") or i).zfill(pad)
    artist = track.get("artist") or ""
    title = track.get("title") or ""
    timestamp = track.get("timestamp") or ""

    parts = [num]
    if timestamp:
        parts.append(_format_timestamp(timestamp, video_url, link_timestamps))
    if title and artist:
        parts.append(f"{title} - {artist}")
    else:
        parts.append(title or artist)
    return " ".join(parts)


def _seconds_to_cue_index(ts: str) -> str:
    parts = [int(p) for p in ts.split(":")]
    if len(parts) == 2:
        minutes, seconds = parts
    else:
        hours, minutes, seconds = parts
        minutes += hours * 60
    return f"{minutes:02d}:{seconds:02d}:00"


_CUE_FILE_TYPE = {"opus": "OGG", "ogg": "OGG", "aac": "AAC", "m4a": "AAC", "flac": "WAVE"}


def generate_cue(result: dict, audio_filename: str, audio_format: str = "mp3") -> str:
    lines = []
    video_title = result.get("video_title", "")
    tracks = result.get("tracks") or []
    cue_type = _CUE_FILE_TYPE.get(audio_format.lower(), "MP3")

    lines.append("REM ENCODING UTF-8")
    if video_title:
        lines.append(f'TITLE "{video_title}"')
    lines.append(f'FILE "{audio_filename}" {cue_type}')

    for i, track in enumerate(tracks, 1):
        title = track.get("title") or ""
        artist = track.get("artist") or ""
        timestamp = track.get("timestamp") or "0:00"
        lines.append(f"  TRACK {i:02d} AUDIO")
        if title:
            lines.append(f'    TITLE "{title}"')
        if artist:
            lines.append(f'    PERFORMER "{artist}"')
        lines.append(f"    INDEX 01 {_seconds_to_cue_index(timestamp)}")

    return "\n".join(lines) + "\n"


def format_markdown(result: dict, link_timestamps: bool = False) -> str:
    lines = []
    video_title = result.get("video_title", "")
    source = result.get("source")
    video_url = result.get("url")

    if video_title:
        lines.append(f"# {video_title}")
    if video_url:
        lines.append(f"[Listen]({video_url})")
    if video_title or video_url:
        lines.append("")

    if not source:
        lines.append("_(no tracklist found)_")
        return "\n".join(lines)

    tracks = result.get("tracks") or []
    pad = len(str(len(tracks)))
    for i, track in enumerate(tracks, 1):
        lines.append(_format_track(i, track, pad, video_url, link_timestamps))

    footnote = f"_Source: {SOURCE_LABELS.get(source, source)}_"
    if result.get("source_url"):
        footnote += f" — {result['source_url']}"
    lines += ["", footnote]

    return "\n".join(lines)
