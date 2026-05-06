import pytest
from find_a_mix.parse import looks_like_tracklist, extract_tracklist_block

FIXTURE = "tests/fixtures/{}.txt"


def read(name):
    with open(FIXTURE.format(name)) as f:
        return f.read()


# --- looks_like_tracklist ---

def test_numbered_list_in_description():
    assert looks_like_tracklist(read("description_tracklist")) is True


def test_timestamps_in_comment():
    assert looks_like_tracklist(read("comment_timestamps")) is True


def test_plain_description_is_not_tracklist():
    assert looks_like_tracklist(read("description_no_tracklist")) is False


def test_plain_comment_is_not_tracklist():
    assert looks_like_tracklist(read("comment_no_tracklist")) is False


def test_tracklist_header_alone_does_not_trigger():
    assert looks_like_tracklist("Tracklist:\nSome Artist - Some Track") is False


def test_tracklist_header_with_url_does_not_trigger():
    assert looks_like_tracklist("Replay/Tracklist: https://example.com/mix") is False


def test_tracklist_header_with_timestamps_triggers():
    text = "Tracklist:\n0:00 A - B\n5:00 C - D\n10:00 E - F"
    assert looks_like_tracklist(text) is True


def test_two_timestamps_not_enough():
    assert looks_like_tracklist("0:00 intro\n1:30 outro") is False


def test_numbered_rules_not_tracklist():
    rules = (
        "The Librarian's Manifesto\n"
        "1. Come for the music.\n"
        "2. Be open to unfamiliar music and sounds.\n"
        "3. Respect one another.\n"
        "4. Face each other instead of the DJ.\n"
        "5. No phones allowed on the dance floor.\n"
        "6. Dress to express yourself.\n"
        "7. Dance your heart out.\n"
    )
    assert looks_like_tracklist(rules) is False


def test_empty_string():
    assert looks_like_tracklist("") is False


# --- extract_tracklist_block ---

def test_extract_returns_text_when_match():
    text = read("description_tracklist")
    result = extract_tracklist_block(text)
    assert result is not None
    assert "Aphex Twin" in result


def test_extract_returns_none_when_no_match():
    text = read("description_no_tracklist")
    assert extract_tracklist_block(text) is None
