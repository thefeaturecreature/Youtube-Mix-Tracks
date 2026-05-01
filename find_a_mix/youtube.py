"""YouTube description and comment tracklist extraction."""

import html
import re
from googleapiclient.discovery import build

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    """Strip HTML tags and unescape entities from YouTube comment textDisplay."""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    return html.unescape(_HTML_TAG_RE.sub("", text))


def fetch_video_info(youtube, video_id: str) -> dict:
    """Return title, channel, and description for a video in one API call."""
    response = youtube.videos().list(part="snippet", id=video_id).execute()
    items = response.get("items", [])
    if not items:
        return {"title": "", "channel": "", "description": ""}
    snippet = items[0]["snippet"]
    return {
        "title": snippet.get("title", ""),
        "channel": snippet.get("channelTitle", ""),
        "description": snippet.get("description", ""),
    }


def fetch_comment_threads(youtube, video_id: str, max_results: int = 100) -> list[dict]:
    """Return top-level comments with thread id and reply count."""
    response = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        order="relevance",
        maxResults=max_results,
    ).execute()
    return [
        {
            "id": item["id"],
            "text": _strip_html(item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]),
            "reply_count": item["snippet"]["totalReplyCount"],
        }
        for item in response.get("items", [])
    ]


def fetch_top_comments(youtube, video_id: str, max_results: int = 100) -> list[str]:
    return [t["text"] for t in fetch_comment_threads(youtube, video_id, max_results)]


def fetch_replies(youtube, thread_id: str) -> list[str]:
    """Return reply texts for a comment thread, oldest first."""
    response = youtube.comments().list(
        part="snippet",
        parentId=thread_id,
        maxResults=100,
    ).execute()
    return [
        _strip_html(item["snippet"]["textDisplay"])
        for item in response.get("items", [])
    ]
