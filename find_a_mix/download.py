"""Download audio from a URL using yt-dlp."""

import os
import subprocess


def download_audio(url: str, output_dir: str, audio_format: str = "opus") -> str:
    """Download best audio from URL, convert to audio_format, return final file path."""
    template = os.path.join(output_dir, "%(title)s [%(id)s].%(ext)s")
    result = subprocess.run(
        [
            "yt-dlp",
            "--cookies-from-browser", "chrome",
            "-f", "bv*[height<=144]+ba/ba/b",
            "-x", "--audio-format", audio_format,
            "--audio-quality", "0",
            "--print", "after_move:filepath",
            "-o", template,
            url,
        ],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    lines = [l for l in result.stdout.strip().splitlines() if l]
    return lines[-1]
