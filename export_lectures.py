"""
CS 631 Lecture Exporter
Scrapes lecture pages from cs631-s26.cs.usfca.edu and exports them as Markdown.
Skips slides (href ending in -slides.html or title starting with "Slides -").
"""

import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter


BASE_URL = "https://cs631-s26.cs.usfca.edu"
OUTPUT_DIR = Path("output/lectures")


class LectureConverter(MarkdownConverter):
    """Custom converter that handles MkDocs Material-specific elements."""

    def convert_a(self, el, text, parent_tags):
        # Strip permalink anchors (¶ symbols added by MkDocs to headings)
        if el.get_text(strip=True) in ("¶", "#", ""):
            return ""
        return super().convert_a(el, text, parent_tags)

    def convert_details(self, el, text, parent_tags):
        # Convert <details>/<summary> (collapsible "Show Solution" blocks)
        summary = el.find("summary")
        summary_text = summary.get_text(strip=True) if summary else "Details"
        inner = text.strip()
        return f"\n\n> **{summary_text}**\n>\n> {inner.replace(chr(10), chr(10) + '> ')}\n\n"

    def convert_summary(self, el, text, parent_tags):
        # Handled inside convert_details; skip standalone rendering
        return ""


def to_markdown(html: str) -> str:
    return LectureConverter(
        heading_style="ATX",
        bullets="-",
        code_language_callback=lambda el: el.get("class", [""])[0].replace(
            "language-", ""
        )
        if el.get("class")
        else "",
    ).convert(html)


def get_lecture_links(session: requests.Session) -> list[dict]:
    """Fetch the base page and return non-slide lecture links from the nav."""
    resp = session.get(BASE_URL + "/")
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # MkDocs Material nav is inside <nav class="md-nav md-nav--primary">
    # Find the "Lectures" section nav label, then collect links beneath it
    links = []
    nav = soup.find("nav", {"aria-label": "Navigation"}) or soup.find("nav")

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        title = a.get_text(strip=True)

        # Only process lecture links
        if not href.startswith("lectures/"):
            continue

        # Skip slides
        if href.endswith("-slides.html"):
            continue
        if title.startswith("Slides -"):
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
    """Turn 'lectures/01-cs631-2026-01-27-intro-dev-env/' into '01-cs631-2026-01-27-intro-dev-env'."""
    return href.strip("/").removeprefix("lectures/")


def fetch_lecture(session: requests.Session, href: str) -> str:
    """Fetch a lecture page and return its main content as Markdown."""
    url = f"{BASE_URL}/{href}"
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # MkDocs Material content lives in <article class="md-content__inner md-typeset">
    # or <div class="md-typeset">
    content = (
        soup.find("article", class_="md-content__inner")
        or soup.find("div", class_="md-typeset")
        or soup.find("main")
        or soup.find("article")
    )

    if content is None:
        print(f"  WARNING: could not find main content element for {url}", file=sys.stderr)
        content = soup.body

    # Remove nav/header/footer noise that may be inside the content block
    for tag in content.find_all(["nav", "header", "footer", ".md-source"]):
        tag.decompose()

    # Remove "edit this page" and "last update" metadata divs
    for tag in content.find_all("div", class_=re.compile(r"md-(source|footer|meta)")):
        tag.decompose()

    md = to_markdown(str(content))

    # Clean up excessive blank lines left by markdownify
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = "CS633-Exporter/1.0 (educational project)"

    print("Fetching lecture list from nav...")
    lectures = get_lecture_links(session)
    print(f"Found {len(lectures)} lecture(s) to export (slides excluded).\n")

    for i, lecture in enumerate(lectures, 1):
        slug = slug_from_href(lecture["href"])
        out_path = OUTPUT_DIR / f"{slug}.md"
        print(f"[{i}/{len(lectures)}] {lecture['title']}")
        print(f"        -> {out_path}")

        try:
            md = fetch_lecture(session, lecture["href"])
            out_path.write_text(md, encoding="utf-8")
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)

    print("\nDone.")


if __name__ == "__main__":
    main()
