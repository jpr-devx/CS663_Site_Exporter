# CS 631 Site Exporter

Automatically exports content from the [CS 631 Systems Foundations](https://cs631-s26.cs.usfca.edu/) course site (USF, Spring 2026) into an Obsidian vault. Lecture notes and assignments are exported as Markdown; slide decks are exported as PDFs. The export runs automatically whenever the vault is opened in Obsidian.

---

## What It Does

When the CS 631 Obsidian vault is opened, the exporter:

1. Scrapes the course site navigation to find all lectures, slide decks, and assignments
2. Skips anything already exported (incremental — only fetches new content)
3. Writes the results directly into the vault's `output/` directory

```
output/
  lectures/     ← Markdown files, one per lecture page
  slides/       ← PDF files, one per slide deck
  assignments/  ← Markdown files, one per assignment
```

Filenames are derived from the URL slug (e.g. `05-cs631-2026-02-24-debugging.md`), so they are stable across runs and Obsidian wikilinks never break.

---

## Project Structure

```
CS633_Site_Exporter/
  export_lectures.py      Scrapes lecture pages → Markdown
  export_slides.py        Scrapes slide decks → PDF via Playwright
  export_assignments.py   Scrapes assignment pages → Markdown
  update.py               Incremental runner; ties the three exporters together
  run.sh                  Bootstraps the Python venv and invokes update.py
  launcher.c              C source for the named launcher binary
  CS631-Site-Exporter     Compiled binary (gitignored); called by launchd
  CS631-Site-Exporter.plist  launchd agent template; populated by install.sh
  install.sh              One-time setup script
  requirements.txt        Python dependencies
  .env.example            Config template; copy to .env and fill in your path
```

---

## Setup (Fresh Machine)

```bash
# 1. Clone the repo
git clone <repo-url> CS633_Site_Exporter
cd CS633_Site_Exporter

# 2. Run the installer
./install.sh
```

`install.sh` will prompt for your Obsidian vault directory:

```
Enter the path to your Obsidian vault directory:
> /path/to/your/CS631_vault
```

It then:
- Writes your config to `.env` (gitignored)
- Compiles the launcher binary from `launcher.c`
- Populates and registers the launchd agent

The next time you open the CS 631 vault in Obsidian, the export runs automatically.

**To check logs:**
```bash
cat ~/Library/Logs/cs631-exporter.log
```

**To uninstall:**
```bash
launchctl bootout "gui/$(id -u)" ~/Library/LaunchAgents/CS631-Site-Exporter.plist
rm ~/Library/LaunchAgents/CS631-Site-Exporter.plist
```

---

## How It Was Built

### 1. Scraping the Course Site

The site is built with the **MkDocs Material** theme. Content lives inside `<article class="md-content__inner">`. Navigation links are scraped from the `<nav>` element on the home page.

**Lectures (`export_lectures.py`):**
- Walks the nav and collects all `href` values starting with `lectures/`, excluding anything ending in `-slides.html` or titled `Slides -`.
- Fetches each page, strips MkDocs chrome (permalink anchors, edit/footer metadata), and converts the HTML to Markdown using [markdownify](https://github.com/matthewwithanm/python-markdownify) with a custom `LectureConverter` subclass.
- `convert_details` turns `<details>`/`<summary>` blocks (collapsible "Show Solution" sections) into Obsidian-friendly blockquotes.

**Slides (`export_slides.py`):**
- Collects the inverse set of nav links (those ending in `-slides.html`).
- Each slide deck uses **reveal.js**. Loading the URL with `?print-pdf` switches it into a printable layout.
- [Playwright](https://playwright.dev/) drives a headless Chromium instance, waits for `Reveal.isReady()`, explicitly calls `mermaid.run()` to force-render any Mermaid diagrams that don't auto-render in headless mode, then exports the page to PDF.

**Assignments (`export_assignments.py`):**
- Collects nav links starting with `assignments/`.
- Reuses `fetch_lecture()` from `export_lectures.py` since the page structure is identical.

**Incremental updates (`update.py`):**
- Accepts an optional output directory as a positional argument (defaults to `./output`).
- Before exporting each item, checks whether the output file already exists and skips it if so.
- This makes repeated runs cheap — on a fully up-to-date vault the whole script completes in a few seconds.

---

### 2. Python Environment

Rather than Docker or conda, the project uses a plain **Python venv** managed by `run.sh`. This keeps the setup portable and lightweight.

`run.sh` handles the full bootstrap on first run:
1. Sources `.env` to get `OUTPUT_DIR` (derived from your vault path by `install.sh`).
2. Creates `.venv/` via `python3 -m venv` if it does not exist.
3. Runs `pip install -r requirements.txt` (fast no-op when already satisfied).
4. Runs `playwright install chromium` once, guarded by a `.playwright_installed` marker file.
5. Calls `update.py` with the vault's `output/` directory as the target.

---

### 3. Automatic Trigger via launchd

The goal was for the export to run automatically when the CS 631 vault is opened in Obsidian — and **only** that vault, not any other.

**Why this works:** Obsidian writes to `.obsidian/workspace.json` inside the active vault whenever the vault is opened. Each vault has its own `workspace.json`, so watching the CS 631 vault's file only triggers for that vault.

**`CS631-Site-Exporter.plist`** is a macOS `launchd` user agent template (installed in `~/Library/LaunchAgents/`) that uses `WatchPaths` to monitor the vault's `workspace.json`. The actual path is substituted by `install.sh` at install time.

When that file changes, launchd runs the `CS631-Site-Exporter` binary, which in turn runs `run.sh`.

Logs are written to `~/Library/Logs/cs631-exporter.log`.

---

### 4. Named Launcher Binary

Initially the plist called `/bin/bash run.sh` directly, which caused macOS Background Activities to display the process as **"bash"** — unhelpful for identifying it in the future.

The fix is a small C binary (`launcher.c`) that:
1. Resolves its own path using `_NSGetExecutablePath` (macOS-specific).
2. Constructs the path to `run.sh` relative to itself.
3. `fork()`s a child process that `execv()`s `/bin/bash run.sh`.
4. The parent waits for the child and propagates its exit code.

Using `fork()` rather than a direct `execv()` is critical: a plain `execv()` replaces the process entirely with bash, so Background Activities would still show "bash". With `fork()`, the parent (`CS631-Site-Exporter`) stays alive and remains the visible process.

The binary is compiled by `install.sh` on first run:
```bash
clang -o CS631-Site-Exporter launcher.c
```

The compiled binary is gitignored; only the source (`launcher.c`) is tracked.

---

## Dependencies

| Dependency | Purpose |
|---|---|
| Python 3.11+ | Runtime for all exporter scripts |
| requests | HTTP client for scraping |
| beautifulsoup4 | HTML parsing |
| markdownify 1.2.2 | HTML → Markdown conversion |
| playwright + Chromium | Headless browser for slide PDF export |
| clang | Compiles `launcher.c` (Xcode Command Line Tools) |
