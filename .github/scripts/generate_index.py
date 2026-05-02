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

import os
import re
import sys
import html

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT_INDEX = os.path.join(REPO_ROOT, "index.html")
SKIP_DIRS = {".git", ".github"}


def _attr(pattern, content):
    m = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else None


def extract_meta(html_path):
    with open(html_path, encoding="utf-8") as f:
        content = f.read()

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
        card_title = os.path.basename(os.path.dirname(html_path)).replace("-", " ").title()

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
    for entry in sorted(os.listdir(REPO_ROOT)):
        if entry in SKIP_DIRS:
            continue
        folder_path = os.path.join(REPO_ROOT, entry)
        if not os.path.isdir(folder_path):
            continue
        index_path = os.path.join(folder_path, "index.html")
        if not os.path.exists(index_path):
            continue
        title, description = extract_meta(index_path)
        projects.append((entry, title, description))

    if not projects:
        print("No subpage folders found – root index.html left unchanged.")
        return

    new_main = build_cards_html(projects)

    with open(ROOT_INDEX, encoding="utf-8") as f:
        original = f.read()

    updated = re.sub(
        r'    <main class="projects">.*?</main>',
        new_main,
        original,
        flags=re.DOTALL,
    )

    if updated == original:
        print("Root index.html is already up to date.")
        return

    with open(ROOT_INDEX, "w", encoding="utf-8") as f:
        f.write(updated)
    print("Root index.html updated successfully.")


if __name__ == "__main__":
    main()
