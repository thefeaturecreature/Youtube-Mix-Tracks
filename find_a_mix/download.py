"""Download audio from a URL using yt-dlp."""

import os
import subprocess
import sys


class CookieError(Exception):
    pass


def download_audio(url: str, output_dir: str, audio_format: str = "opus", cookies_file: str | None = None) -> str:
    """Download best audio from URL, convert to audio_format, return final file path."""
    template = os.path.join(output_dir, "%(title)s.%(ext)s")
    cookie_args = ["--cookies", cookies_file] if cookies_file else ["--cookies-from-browser", "chrome"]
    proc = subprocess.Popen(
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
    )
    stderr_chunks = []
    for line in proc.stderr:
        sys.stderr.write(line)
        sys.stderr.flush()
        stderr_chunks.append(line)
    proc.wait()
    if proc.returncode != 0:
        stderr = "".join(stderr_chunks)
        if any(kw in stderr.lower() for kw in ("cookie", "sign in", "bot", "login")):
            raise CookieError(stderr) from None
        raise subprocess.CalledProcessError(proc.returncode, proc.args, stderr=stderr)
    lines = [l for l in proc.stdout.read().strip().splitlines() if l]
    return lines[-1]
