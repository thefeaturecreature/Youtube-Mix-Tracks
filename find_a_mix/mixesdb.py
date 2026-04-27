"""MixesDB scraping — search by artist + mix title."""

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.mixesdb.com"
API_URL = f"{BASE_URL}/w/api.php"


def search(artist: str, title: str) -> str | None:
    """Search MixesDB via MediaWiki API, return page URL of best result."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": f"{artist} {title}",
        "srlimit": 1,
        "format": "json",
    }
    resp = requests.get(API_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("query", {}).get("search", [])
    if not results:
        return None
    page_title = results[0]["title"].replace(" ", "_")
    return f"{BASE_URL}/w/{page_title}"


def fetch_tracklist(page_url: str) -> list[str]:
    resp = requests.get(page_url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Tracklist lives in plain <ol> elements after the <h2 id="Tracklist"> heading.
    # Multiple <ol> blocks may exist (one per DJ set), separated by <dl><dt> section headers.
    tracklist_heading = soup.find("h2", id="Tracklist") or soup.find(id="Tracklist")
    if not tracklist_heading:
        return []

    tracks = []
    for sibling in tracklist_heading.find_parent().next_siblings:
        if sibling.name == "h2":
            break
        if sibling.name == "ol":
            tracks.extend(li.get_text(strip=True) for li in sibling.find_all("li"))
        elif sibling.name == "div" and "mw-heading" in sibling.get("class", []):
            break

    return tracks
