"""
YouTube source tests — requires cassettes recorded against real API.
Record: change record_mode to "new_episodes" in conftest.py, set YOUTUBE_API_KEY, run once.
"""

import pytest
from unittest.mock import MagicMock
from find_a_mix.youtube import fetch_video_info, fetch_top_comments


def _mock_youtube(description="", comments=None, title="Test Mix", channel="Test DJ"):
    youtube = MagicMock()
    youtube.videos().list().execute.return_value = {
        "items": [{"snippet": {"title": title, "channelTitle": channel, "description": description}}]
    }
    youtube.commentThreads().list().execute.return_value = {
        "items": [
            {"snippet": {"topLevelComment": {"snippet": {"textDisplay": c}}}}
            for c in (comments or [])
        ]
    }
    return youtube


def test_fetch_video_info_returns_fields():
    yt = _mock_youtube(description="Tracklist:\n1. Some Track", title="DJ - Mix", channel="DJ")
    result = fetch_video_info(yt, "fake_id")
    assert "Tracklist" in result["description"]
    assert result["title"] == "DJ - Mix"
    assert result["channel"] == "DJ"


def test_fetch_video_info_empty_when_no_items():
    yt = MagicMock()
    yt.videos().list().execute.return_value = {"items": []}
    result = fetch_video_info(yt, "fake_id")
    assert result == {"title": "", "channel": "", "description": ""}


def test_fetch_top_comments_returns_list():
    yt = _mock_youtube(comments=["0:00 Track A", "great mix!"])
    result = fetch_top_comments(yt, "fake_id")
    assert result == ["0:00 Track A", "great mix!"]


def test_fetch_top_comments_empty_video():
    yt = _mock_youtube(comments=[])
    assert fetch_top_comments(yt, "fake_id") == []
