"""CLI entry point for unmix."""

import argparse
import os
import sys
from dotenv import load_dotenv

from .pipeline import run
from .output import format_markdown, generate_cue
from .download import download_audio, CookieError

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        prog="unmix",
        description="Identify the tracklist for a DJ mix from a YouTube URL.",
    )
    parser.add_argument("url", help="YouTube URL of the mix")
    parser.add_argument("-o", "--output", metavar="FILE", help="Save tracklist to a markdown file")
    parser.add_argument("-t", "--timestamps", action="store_true", help="Link timestamps to YouTube playback position")
    parser.add_argument("-c", "--cue", action="store_true", help="Download audio and generate a CUE sheet")
    parser.add_argument("--type", default="opus", metavar="FORMAT", help="Audio format for download (default: opus)")
    parser.add_argument("--cookies", metavar="FILE", help="Netscape-format cookies file for yt-dlp (bypasses --cookies-from-browser chrome)")
    args = parser.parse_args()

    result = run(args.url)
    formatted = format_markdown(result, link_timestamps=args.timestamps)

    if args.output:
        with open(args.output, "w") as f:
            f.write(formatted)
        source = result.get("source") or "no source"
        print(f"Saved ({source}) → {args.output}")
    else:
        print(formatted)

    if args.cue:
        download_path = os.path.expanduser(os.environ.get("DOWNLOAD_PATH", "~/Downloads"))
        try:
            audio_path = download_audio(args.url, download_path, args.type, cookies_file=args.cookies)
        except CookieError:
            print(
                "\nError: YouTube requires authentication to download this video.\n"
                "\n"
                "To fix:\n"
                "  1. Open Chrome with YouTube loaded and signed in, then retry.\n"
                "  2. Or export a cookies file and pass it with --cookies:\n"
                "       unmix -c --cookies ~/cookies.txt <url>\n"
                "     (use the 'Get cookies.txt LOCALLY' browser extension to export)\n",
                file=sys.stderr,
            )
            raise SystemExit(1)
        audio_filename = os.path.basename(audio_path)
        ext = os.path.splitext(audio_filename)[1].lstrip(".")
        base = os.path.splitext(audio_filename)[0]
        cue_path = os.path.join(download_path, base + ".cue")
        cue_text = generate_cue(result, audio_filename, ext)
        with open(cue_path, "w", encoding="utf-8") as f:
            f.write(cue_text)
        print(f"Downloaded → {audio_path}")
        print(f"CUE sheet  → {cue_path}")
