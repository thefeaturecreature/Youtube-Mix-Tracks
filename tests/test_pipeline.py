"""
Pipeline integration tests.
Each test asserts that the correct source is returned for a given mix.
Requires cassettes — see tests/cassettes/README.md for recording instructions.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from find_a_mix.pipeline import video_id_from_url, run


# --- video_id_from_url ---

def test_extract_id_from_watch_url():
    assert video_id_from_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_id_from_short_url():
    assert video_id_from_url("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_id_raises_on_bad_url():
    with pytest.raises(ValueError):
        video_id_from_url("https://example.com/not-a-video")


# --- source cascade (mocked) ---

def _make_pipeline_mock(description="", comments=None, title="Test Mix", channel="Test DJ"):
    yt_mock = MagicMock()
    yt_mock.videos().list().execute.return_value = {
        "items": [{"snippet": {
            "title": title,
            "channelTitle": channel,
            "description": description,
        }}]
    }
    yt_mock.commentThreads().list().execute.return_value = {
        "items": [
            {"snippet": {"topLevelComment": {"snippet": {"textDisplay": c}}}}
            for c in (comments or [])
        ]
    }
    return yt_mock


def test_pipeline_returns_description_source(monkeypatch):
    yt = _make_pipeline_mock(description="Tracklist:\n1. Artist - Track\n2. Artist2 - Track2\n3. A - B")
    monkeypatch.setenv("YOUTUBE_API_KEY", "fake")
    with patch("find_a_mix.pipeline.build", return_value=yt), \
         patch("find_a_mix.pipeline.mixesdb.search", return_value=None), \
         patch("find_a_mix.pipeline.asyncio.run", return_value=(None, [])):
        result = run("https://www.youtube.com/watch?v=fake_id_001")
    assert result["source"] == "youtube_description"


def test_pipeline_falls_through_to_comment(monkeypatch):
    comment = "0:00 A - B\n5:00 C - D\n10:00 E - F\n15:00 G - H"
    yt = _make_pipeline_mock(description="Recorded live. Follow on Instagram.", comments=[comment])
    monkeypatch.setenv("YOUTUBE_API_KEY", "fake")
    with patch("find_a_mix.pipeline.build", return_value=yt), \
         patch("find_a_mix.pipeline.mixesdb.search", return_value=None), \
         patch("find_a_mix.pipeline.asyncio.run", return_value=(None, [])):
        result = run("https://www.youtube.com/watch?v=fake_id_002")
    assert result["source"] == "youtube_comment"


def test_pipeline_returns_none_when_no_source(monkeypatch):
    yt = _make_pipeline_mock(description="Just vibes.", comments=["great set!"])
    monkeypatch.setenv("YOUTUBE_API_KEY", "fake")
    with patch("find_a_mix.pipeline.build", return_value=yt), \
         patch("find_a_mix.pipeline.mixesdb.search", return_value=None), \
         patch("find_a_mix.pipeline.asyncio.run", return_value=(None, [])):
        result = run("https://www.youtube.com/watch?v=fake_id_003")
    assert result["source"] is None
