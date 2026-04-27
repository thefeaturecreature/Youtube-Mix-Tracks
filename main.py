#!/usr/bin/env python3
"""find-a-mix: identify the tracklist for a DJ mix from a YouTube URL."""

import argparse
import sys
from dotenv import load_dotenv

from find_a_mix.pipeline import run
from find_a_mix.output import format_markdown

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        prog="find-a-mix",
        description="Identify the tracklist for a DJ mix from a YouTube URL.",
    )
    parser.add_argument("url", help="YouTube URL of the mix")
    parser.add_argument("-o", "--output", metavar="FILE", help="Save tracklist to a markdown file")
    parser.add_argument("-t", "--timestamps", action="store_true", help="Link timestamps to YouTube playback position")
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


if __name__ == "__main__":
    main()
