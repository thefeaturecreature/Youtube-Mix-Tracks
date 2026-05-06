"""Orchestrates the source cascade for a given YouTube mix URL."""

import asyncio
import os
import re

from googleapiclient.discovery import build

from . import parse, mixesdb, youtube as yt
from .parse import extract_reply_tracks
from . import tracklists_1001
from .infer import parse_tracks


YT_ID_RE = re.compile(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})")
BARE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_1001TL_URL_RE = re.compile(r"https?://(?:www\.)?1001tracklists\.com/tracklist/[^\s]+")


def video_id_from_url(url: str) -> str:
    if BARE_ID_RE.match(url):
        return url
    m = YT_ID_RE.search(url)
    if not m:
        raise ValueError(f"Could not extract video ID from: {url}")
    return m.group(1)


def run(url: str, no_youtube: bool = False, skip_description: bool = False) -> dict:
    video_id = video_id_from_url(url)
    youtube = build("youtube", "v3", developerKey=os.environ["YOUTUBE_API_KEY"])

    info = yt.fetch_video_info(youtube, video_id)
    video_title = info["title"]
    channel = info["channel"]
    base = {"video_title": video_title, "url": url, "source_url": None, "text": None, "tracks": None}

    if not no_youtube and not skip_description:
        # Step 1: YouTube description
        block = parse.extract_tracklist_block(info["description"])
        if block:
            return {**base, "source": "youtube_description", "tracks": parse_tracks(block)}

    # Step 2: YouTube comments
    threads = yt.fetch_comment_threads(youtube, video_id) if not no_youtube else []

    # 2a: if any comment cites a 1001tracklists URL, use it directly (has full timestamps)
    for thread in threads:
        m = _1001TL_URL_RE.search(thread["text"])
        if m:
            tl_url = m.group(0).rstrip(".,)")
            raw_tracks = tracklists_1001.fetch_tracklist(tl_url)
            if raw_tracks:
                text = "\n".join(f"{t['num']}. {t['title']}  {t['time']}".strip() for t in raw_tracks)
                return {**base, "source": "1001tracklists", "source_url": tl_url, "tracks": parse_tracks(text)}

    # 2b: parse comment text as a tracklist, merging replies when blanks are present
    for thread in threads:
        block = parse.extract_tracklist_block(thread["text"])
        if not block:
            continue
        if parse._BLANK_MARKER_RE.search(block) and thread["reply_count"] > 0:
            replies = yt.fetch_replies(youtube, thread["id"])
            reply_tracks = extract_reply_tracks(replies)
            if reply_tracks:
                reply_addendum = "\n".join(reply_tracks)
                block = (
                    f"{block}\n\n"
                    f"NOTE: The following community-identified tracks fill in unknown entries above — "
                    f"use them to replace ??? or ID placeholders at matching timestamps:\n"
                    f"{reply_addendum}"
                )
        return {**base, "source": "youtube_comment", "tracks": parse_tracks(block)}

    # Step 3: MixesDB
    page_url = mixesdb.search(channel, video_title)
    if page_url:
        raw_tracks = mixesdb.fetch_tracklist(page_url)
        if raw_tracks:
            text = "\n".join(raw_tracks)
            return {**base, "source": "mixesdb", "source_url": page_url, "tracks": parse_tracks(text)}

    # Step 4: 1001Tracklists
    tl_url, raw_tracks = asyncio.run(tracklists_1001.search_and_fetch(channel, video_title))
    if raw_tracks:
        text = "\n".join(f"{t['num']}. {t['title']}  {t['time']}".strip() for t in raw_tracks)
        return {**base, "source": "1001tracklists", "source_url": tl_url, "tracks": parse_tracks(text)}

    return {**base, "source": None, "source_url": None}
