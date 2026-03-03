"""
CS 631 Slides PDF Exporter
Scrapes slide deck links from cs631-s26.cs.usfca.edu and exports each as a PDF
using Playwright's headless Chromium with reveal.js's built-in ?print-pdf layout.
"""

import asyncio
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


BASE_URL = "https://cs631-s26.cs.usfca.edu"
OUTPUT_DIR = Path("output/slides")


def get_slide_links(session: requests.Session) -> list[dict]:
    """Fetch the base page and return slide deck links from the nav."""
    resp = session.get(BASE_URL + "/")
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        title = a.get_text(strip=True)

        # Only process lecture links
        if not href.startswith("lectures/"):
            continue

        # Keep only slides (opposite of export_lectures.py)
        if not (href.endswith("-slides.html") or title.startswith("Slides -")):
            continue

        links.append({"href": href, "title": title})

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for link in links:
        key = link["href"]
        if key not in seen:
            seen.add(key)
            unique.append(link)

    return unique


def slug_from_href(href: str) -> str:
    """Turn 'lectures/02-cs631-2026-02-05-parsing-slides.html' into '02-cs631-2026-02-05-parsing'."""
    return href.removeprefix("lectures/").removesuffix("-slides.html")


async def export_slide_pdf(url: str, out_path: Path) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url + "?print-pdf", wait_until="networkidle")

        # Wait for reveal.js to finish (includes RevealMarkdown processing).
        # isReady() is available in reveal.js 4+; older builds just expose the
        # object, so fall back to "Reveal exists" if the method is absent.
        await page.wait_for_function(
            """() => {
                if (typeof Reveal === 'undefined') return false;
                if (typeof Reveal.isReady === 'function') return Reveal.isReady();
                return true;
            }""",
            timeout=60000,
        )

        # Attempt to render any Mermaid diagrams that haven't processed yet.
        # Some slides load Mermaid source but the library doesn't auto-run in
        # headless mode, so we call the API explicitly when available.
        await page.evaluate("""async () => {
            if (typeof mermaid === 'undefined') return;
            const pending = Array.from(document.querySelectorAll('.mermaid'))
                                 .filter(el => el.querySelector('svg') === null);
            if (pending.length === 0) return;
            try {
                if (typeof mermaid.run === 'function') {
                    await mermaid.run({ nodes: pending });
                } else if (typeof mermaid.init === 'function') {
                    mermaid.init(undefined, pending);
                }
            } catch (e) { /* ignore render errors */ }
        }""")

        # Wait up to 30 s for Mermaid SVGs; proceed anyway if they never appear
        # (the PDF will show the source text fallback instead).
        try:
            await page.wait_for_function(
                """() => {
                    const nodes = document.querySelectorAll('.mermaid');
                    if (nodes.length === 0) return true;
                    return Array.from(nodes).every(el => el.querySelector('svg') !== null);
                }""",
                timeout=30000,
            )
        except Exception:
            pass  # proceed — networkidle + Reveal.isReady() is sufficient

        await page.pdf(path=str(out_path), print_background=True)
        await browser.close()


async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = "CS633-Exporter/1.0 (educational project)"

    print("Fetching slide list from nav...")
    slides = get_slide_links(session)
    print(f"Found {len(slides)} slide deck(s) to export.\n")

    for i, slide in enumerate(slides, 1):
        slug = slug_from_href(slide["href"])
        out_path = OUTPUT_DIR / f"{slug}.pdf"
        url = f"{BASE_URL}/{slide['href']}"
        print(f"[{i}/{len(slides)}] {slide['title']}")
        print(f"        -> {out_path}")

        try:
            await export_slide_pdf(url, out_path)
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
