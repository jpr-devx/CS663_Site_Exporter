"""
CS 631 Assignment Exporter
Scrapes assignment pages from cs631-s26.cs.usfca.edu and exports them as Markdown.
"""

import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from export_lectures import BASE_URL, fetch_lecture


OUTPUT_DIR = Path("output/assignments")


def get_assignment_links(session: requests.Session) -> list[dict]:
    """Fetch the base page and return assignment links from the nav."""
    resp = session.get(BASE_URL + "/")
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        title = a.get_text(strip=True)
        if not href.startswith("assignments/"):
            continue
        links.append({"href": href, "title": title})

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for link in links:
        if link["href"] not in seen:
            seen.add(link["href"])
            unique.append(link)

    return unique


def slug_from_href(href: str) -> str:
    """Turn 'assignments/lab01/' into 'lab01'."""
    return href.strip("/").removeprefix("assignments/")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = "CS633-Exporter/1.0 (educational project)"

    print("Fetching assignment list from nav...")
    assignments = get_assignment_links(session)
    print(f"Found {len(assignments)} assignment(s) to export.\n")

    for i, assignment in enumerate(assignments, 1):
        slug = slug_from_href(assignment["href"])
        out_path = OUTPUT_DIR / f"{slug}.md"
        print(f"[{i}/{len(assignments)}] {assignment['title']}")
        print(f"        -> {out_path}")
        try:
            md = fetch_lecture(session, assignment["href"])
            out_path.write_text(md, encoding="utf-8")
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)

    print("\nDone.")


if __name__ == "__main__":
    main()
