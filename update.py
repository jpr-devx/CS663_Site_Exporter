"""
CS 631 Site Exporter — Incremental Update
Exports only lectures and slides not already present in the output directory.

Usage:
    python3 update.py [output_root]   (default: output)
"""

import asyncio
import sys
from pathlib import Path

import requests

from export_lectures import (
    BASE_URL,
    fetch_lecture,
    get_lecture_links,
    slug_from_href as lecture_slug,
)
from export_slides import export_slide_pdf, get_slide_links
from export_slides import slug_from_href as slide_slug


def main():
    output_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output")
    lectures_dir = output_root / "lectures"
    slides_dir = output_root / "slides"

    lectures_dir.mkdir(parents=True, exist_ok=True)
    slides_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = "CS633-Exporter/1.0 (educational project)"

    # ── Lectures ──────────────────────────────────────────────────────────────
    print("Fetching lecture list from nav...")
    lectures = get_lecture_links(session)
    print(f"Found {len(lectures)} lecture(s).\n")

    n = len(lectures)
    for i, lecture in enumerate(lectures, 1):
        slug = lecture_slug(lecture["href"])
        out_path = lectures_dir / f"{slug}.md"
        print(f"[{i}/{n}] {lecture['title']}")
        if out_path.exists():
            print("        SKIP  (already exported)")
            continue
        print(f"        -> {out_path}")
        try:
            md = fetch_lecture(session, lecture["href"])
            out_path.write_text(md, encoding="utf-8")
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)

    # ── Slides ────────────────────────────────────────────────────────────────
    print("\nFetching slide list from nav...")
    slides = get_slide_links(session)
    print(f"Found {len(slides)} slide deck(s).\n")

    n = len(slides)
    for i, slide in enumerate(slides, 1):
        slug = slide_slug(slide["href"])
        out_path = slides_dir / f"{slug}.pdf"
        url = f"{BASE_URL}/{slide['href']}"
        print(f"[{i}/{n}] {slide['title']}")
        if out_path.exists():
            print("        SKIP  (already exported)")
            continue
        print(f"        -> {out_path}")
        try:
            asyncio.run(export_slide_pdf(url, out_path))
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)

    print("\nDone.")


if __name__ == "__main__":
    main()
