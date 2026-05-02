#!/usr/bin/env python3
"""
Scans root-level subdirectories that contain an index.html and regenerates
the <main class="projects"> section of the root index.html.

Each subfolder's index.html should include:
  <meta name="description" content="Card description shown on the home page.">

The card title is derived from the <title> tag (stripping the
" · NUST MISIS" suffix if present), or from an optional
  <meta name="card-title" content="Override title">
tag when the browser tab title and the card title should differ.
"""

import re
import html
from pathlib import Path

# Navigate from .github/scripts/ → .github/ → repo root
REPO_ROOT = Path(__file__).parent.parent.parent
ROOT_INDEX = REPO_ROOT / "index.html"
SKIP_DIRS = {".git", ".github"}


def _attr(pattern, content):
    m = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else None


def extract_meta(html_path):
    content = Path(html_path).read_text(encoding="utf-8")

    # Card title: prefer explicit meta, fall back to <title>
    card_title = _attr(
        r'<meta\s+name=["\']card-title["\']\s+content=["\'](.*?)["\']', content
    ) or _attr(
        r'<meta\s+content=["\'](.*?)["\']\s+name=["\']card-title["\']', content
    )
    if not card_title:
        raw_title = _attr(r"<title>(.*?)</title>", content) or ""
        card_title = re.sub(
            r"\s*[·—]\s*NUST MISIS\s*$", "", raw_title, flags=re.IGNORECASE
        ).strip()
    if not card_title:
        # Fallback: derive from folder name. For best results, add a <title>
        # or <meta name="card-title"> to the subpage's index.html instead.
        card_title = Path(html_path).parent.name.replace("-", " ").title()

    # Description
    description = _attr(
        r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content
    ) or _attr(
        r'<meta\s+content=["\'](.*?)["\']\s+name=["\']description["\']', content
    ) or ""

    # Unescape HTML entities so values round-trip cleanly through html.escape()
    card_title = html.unescape(card_title)
    description = html.unescape(description)
    return card_title, description


def build_cards_html(projects):
    lines = ['    <main class="projects">']
    for folder, title, description in projects:
        safe_title = html.escape(title)
        safe_desc = html.escape(description)
        lines.append(f'        <a href="{folder}/" class="project-card">')
        lines.append(f"            <h2>{safe_title}</h2>")
        if safe_desc:
            lines.append(f"            <p>{safe_desc}</p>")
        lines.append("        </a>")
    lines.append("    </main>")
    return "\n".join(lines)


def main():
    # Collect subfolders that have an index.html
    projects = []
    for entry in sorted(p.name for p in REPO_ROOT.iterdir() if p.is_dir() and p.name not in SKIP_DIRS):
        index_path = REPO_ROOT / entry / "index.html"
        if not index_path.exists():
            continue
        title, description = extract_meta(index_path)
        projects.append((entry, title, description))

    if not projects:
        print("No subpage folders found – root index.html left unchanged.")
        return

    new_main = build_cards_html(projects)

    original = ROOT_INDEX.read_text(encoding="utf-8")

    updated = re.sub(
        r'    <main class="projects">.*?</main>',
        new_main,
        original,
        flags=re.DOTALL,
    )

    if updated == original:
        print("Root index.html is already up to date.")
        return

    ROOT_INDEX.write_text(updated, encoding="utf-8")
    print("Root index.html updated successfully.")


if __name__ == "__main__":
    main()
