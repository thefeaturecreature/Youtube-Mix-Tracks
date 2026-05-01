"""Download audio from a URL using yt-dlp."""

import os
import subprocess


class CookieError(Exception):
    pass


def download_audio(url: str, output_dir: str, audio_format: str = "opus", cookies_file: str | None = None) -> str:
    """Download best audio from URL, convert to audio_format, return final file path."""
    template = os.path.join(output_dir, "%(title)s [%(id)s].%(ext)s")
    cookie_args = ["--cookies", cookies_file] if cookies_file else ["--cookies-from-browser", "chrome"]
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                *cookie_args,
                "-f", "bv*[height<=144]+ba/ba/b",
                "-x", "--audio-format", audio_format,
                "--audio-quality", "0",
                "--print", "after_move:filepath",
                "-o", template,
                url,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").lower()
        if any(kw in stderr for kw in ("cookie", "sign in", "bot", "login")):
            raise CookieError(e.stderr) from None
        raise
    lines = [l for l in result.stdout.strip().splitlines() if l]
    return lines[-1]
