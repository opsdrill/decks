#!/usr/bin/env python3
"""
Validate the on-disk layout of topics/.

Rules (path-as-data, see anki-decks-feature.md §3.3):
  - Top-level entries under topics/ are directories named after a topic slug
    that exists in topics.json (or aliases of one).
  - The reserved directory topics/_template/ is allowed and skipped.
  - Each topic directory contains only single-file decks:
      topics/<topic>/<deck>.yml
    (no subdirectories, no orphan files).
  - Slug regex (^[a-z0-9-]+$) applied to topic dir name and deck slug.
  - Deck slugs are globally unique across the whole tree.

Exits 0 on success, 1 on any violation. Prints one line per violation as
  <path>: <rule> — <detail>
so CI logs stay greppable.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOPICS_DIR = REPO_ROOT / "topics"
TOPICS_JSON = REPO_ROOT / "topics.json"
TEMPLATE_DIR_NAME = "_template"

SLUG_RE = re.compile(r"^[a-z0-9-]+$")


def load_known_topic_slugs() -> set[str]:
    if not TOPICS_JSON.exists():
        raise SystemExit(f"{TOPICS_JSON}: missing — cannot validate topic references")
    with TOPICS_JSON.open(encoding="utf-8") as fh:
        manifest = json.load(fh)
    slugs: set[str] = set()
    for topic in manifest.get("topics", []):
        slugs.add(topic["slug"])
        slugs.update(topic.get("aliases", []))
    return slugs


def validate() -> list[str]:
    errors: list[str] = []

    if not TOPICS_DIR.exists():
        return [f"{TOPICS_DIR}: missing — repo bootstrap incomplete"]

    known_topics = load_known_topic_slugs()
    seen_deck_slugs: dict[str, Path] = {}

    for entry in sorted(TOPICS_DIR.iterdir()):
        rel = entry.relative_to(REPO_ROOT)

        if entry.is_file():
            errors.append(f"{rel}: orphan-file — files at topics/ root are not allowed")
            continue

        topic_slug = entry.name
        if topic_slug == TEMPLATE_DIR_NAME:
            continue

        if not SLUG_RE.match(topic_slug):
            errors.append(f"{rel}: bad-slug — topic directory must match ^[a-z0-9-]+$")
            continue

        if topic_slug not in known_topics:
            errors.append(
                f"{rel}: unknown-topic — '{topic_slug}' not in topics.json; "
                f"open a New Topic Request first"
            )
            continue

        _validate_topic_dir(entry, errors, seen_deck_slugs)

    return errors


def _validate_topic_dir(
    topic_dir: Path,
    errors: list[str],
    seen_deck_slugs: dict[str, Path],
) -> None:
    for child in sorted(topic_dir.iterdir()):
        rel = child.relative_to(REPO_ROOT)

        if child.name.startswith("."):
            continue

        if child.is_dir():
            errors.append(
                f"{rel}: nested-dir — topic directories may only contain "
                f"<deck-slug>.yml files"
            )
            continue

        if child.suffix != ".yml":
            errors.append(f"{rel}: bad-extension — expected .yml")
            continue

        deck_slug = child.stem
        if not SLUG_RE.match(deck_slug):
            errors.append(f"{rel}: bad-slug — deck filename must match ^[a-z0-9-]+$")
            continue
        _claim_deck_slug(deck_slug, rel, seen_deck_slugs, errors)


def _claim_deck_slug(
    slug: str,
    path: Path,
    seen: dict[str, Path],
    errors: list[str],
) -> None:
    if slug in seen:
        errors.append(
            f"{path}: duplicate-slug — '{slug}' already used at {seen[slug]}"
        )
        return
    seen[slug] = path


def main() -> int:
    errors = validate()
    if errors:
        for err in errors:
            print(err)
        print(f"\nvalidate_layout.py: FAILED ({len(errors)} violation(s))")
        return 1
    print("validate_layout.py: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
