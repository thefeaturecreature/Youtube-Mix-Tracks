"""1001Tracklists scraping via Playwright.

Requires headless=False + TrustedDOMTypes disabled to bypass the site's JS gate
and allow dynamic content to render.
"""

import asyncio
from playwright.async_api import async_playwright, BrowserContext


LAUNCH_ARGS = [
    "--disable-web-security",
    "--disable-features=TrustedDOMTypes",
]

SEARCH_URL = "https://www.1001tracklists.com/search/index.html"


async def _wait_past_gate(page, timeout_s: int = 30) -> bool:
    for _ in range(timeout_s):
        text = await page.inner_text("body")
        if "forwarded" not in text.lower() and len(text) > 500:
            return True
        await page.wait_for_timeout(1000)
    return False


async def _fetch_tracklist_page(ctx: BrowserContext, url: str) -> list[dict]:
    page = await ctx.new_page()
    await page.goto(url, wait_until="domcontentloaded", timeout=20000)
    await _wait_past_gate(page)
    tracks = await page.evaluate("""() => {
        const items = document.querySelectorAll(".tlpItem");
        return Array.from(items).map(el => {
            const num = el.querySelector(".fontXL")?.innerText.trim() || "";
            const title = el.querySelector(".notranslate")?.innerText.trim() || "";
            const time = el.querySelector(".cueValueField")?.value || "";
            return { num, title, time };
        });
    }""")
    await page.close()
    return [t for t in tracks if t["title"]]


async def _search_page(ctx: BrowserContext, query: str) -> str | None:
    page = await ctx.new_page()
    await page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=20000)
    await _wait_past_gate(page)
    await page.fill("#sBoxInput", query)
    await page.press("#sBoxInput", "Enter")
    await page.wait_for_timeout(3000)
    link = await page.query_selector("a[href*='/tracklist/']")
    href = await link.get_attribute("href") if link else None
    await page.close()
    if href:
        return f"https://www.1001tracklists.com{href}" if href.startswith("/") else href
    return None


async def search_and_fetch(artist: str, title: str) -> tuple[str | None, list[dict]]:
    """Return (source_url, tracks). source_url is None if no result was found."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=LAUNCH_ARGS)
        ctx = await browser.new_context()
        url = await _search_page(ctx, f"{artist} {title}")
        tracks = await _fetch_tracklist_page(ctx, url) if url else []
        await browser.close()
    return url, tracks


def fetch_tracklist(page_url: str) -> list[dict]:
    async def _run():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, args=LAUNCH_ARGS)
            ctx = await browser.new_context()
            tracks = await _fetch_tracklist_page(ctx, page_url)
            await browser.close()
            return tracks
    return asyncio.run(_run())
