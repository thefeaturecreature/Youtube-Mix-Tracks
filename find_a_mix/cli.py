"""CLI entry point for unmix."""

import argparse
import os
import re
import sys
from dotenv import load_dotenv

from .pipeline import run
from .output import format_markdown, generate_cue
from .download import download_audio, CookieError

load_dotenv()

_UNSAFE_FILENAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _safe_filename(title: str) -> str:
    return _UNSAFE_FILENAME_RE.sub("_", title).strip(" .")


def main():
    parser = argparse.ArgumentParser(
        prog="unmix",
        description="Identify the tracklist for a DJ mix from a YouTube URL.",
    )
    parser.add_argument("url", help="YouTube URL of the mix")
    parser.add_argument("-o", "--output", metavar="FILE", help="Save tracklist to a markdown file")
    parser.add_argument("-t", "--timestamps", action="store_true", help="Link timestamps to YouTube playback position")
    parser.add_argument("-c", "--cue", action="store_true", help="Download audio and generate a CUE sheet")
    parser.add_argument("-cn", "--cue-no-download", action="store_true", help="Generate a CUE sheet without downloading audio")
    parser.add_argument("--type", default="opus", metavar="FORMAT", help="Audio format for download (default: opus)")
    parser.add_argument("--cookies", metavar="FILE", help="Netscape-format cookies file for yt-dlp (bypasses --cookies-from-browser chrome)")
    parser.add_argument("-ny", "--no-youtube", action="store_true", help="Skip YouTube description and comment checks, go straight to MixesDB and 1001Tracklists")
    parser.add_argument("-nd", "--no-description", action="store_true", help="Skip YouTube description, go straight to comments")
    args = parser.parse_args()

    result = run(args.url, no_youtube=args.no_youtube, skip_description=args.no_description)
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
        base = _safe_filename(result.get("video_title") or "mix")
        package_dir = os.path.join(download_path, base)
        os.makedirs(package_dir, exist_ok=True)
        try:
            audio_path = download_audio(args.url, package_dir, args.type, cookies_file=args.cookies)
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
        cue_path = os.path.join(package_dir, base + ".cue")
        cue_text = generate_cue(result, audio_filename, ext)
        with open(cue_path, "w", encoding="utf-8") as f:
            f.write(cue_text)
        print(f"Downloaded → {audio_path}")
        print(f"CUE sheet  → {cue_path}")

    if args.cue_no_download:
        download_path = os.path.expanduser(os.environ.get("DOWNLOAD_PATH", "~/Downloads"))
        fmt = args.type
        base = _safe_filename(result.get("video_title") or "mix")
        audio_filename = f"{base}.{fmt}"
        cue_path = os.path.join(download_path, base + ".cue")
        cue_text = generate_cue(result, audio_filename, fmt)
        with open(cue_path, "w", encoding="utf-8") as f:
            f.write(cue_text)
        print(f"CUE sheet  → {cue_path}")
