#!/usr/bin/env python3
"""
Validate every deck YAML against schemas/deck.v1.json.

Each file under topics/<topic-slug>/<deck-slug>.yml must declare
`schema: deck/v1` and include an inline `cards:` list.

Exits 0 on success, 1 on any violation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parent.parent
TOPICS_DIR = REPO_ROOT / "topics"
SCHEMAS_DIR = REPO_ROOT / "schemas"
TEMPLATE_DIR_NAME = "_template"
DECK_SCHEMA = SCHEMAS_DIR / "deck.v1.json"
EXPECTED_SCHEMA = "deck/v1"


def load_validator() -> Draft202012Validator:
    with DECK_SCHEMA.open(encoding="utf-8") as fh:
        schema = json.load(fh)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def discover_yaml_files() -> list[Path]:
    if not TOPICS_DIR.exists():
        return []
    out: list[Path] = []
    for path in sorted(TOPICS_DIR.rglob("*.yml")):
        rel = path.relative_to(TOPICS_DIR)
        if TEMPLATE_DIR_NAME in rel.parts:
            continue
        if len(rel.parts) != 2:
            continue
        out.append(path)
    return out


def validate_file(path: Path, validator: Draft202012Validator) -> list[str]:
    rel = path.relative_to(REPO_ROOT)
    errors: list[str] = []

    try:
        with path.open(encoding="utf-8") as fh:
            doc: Any = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        return [f"{rel}: yaml-parse-error — {exc}"]

    if not isinstance(doc, dict):
        return [f"{rel}: bad-root — top-level YAML must be a mapping"]

    declared = doc.get("schema")
    if declared != EXPECTED_SCHEMA:
        errors.append(
            f"{rel}: bad-schema-field — expected `schema: {EXPECTED_SCHEMA}`, "
            f"got {declared!r}"
        )
        return errors

    schema_errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))
    for err in schema_errors:
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"{rel}: schema-violation at {loc} — {err.message}")

    if "cards" not in doc:
        errors.append(f"{rel}: missing-cards — deck must include `cards:`")

    return errors


def main() -> int:
    validator = load_validator()
    yaml_files = discover_yaml_files()
    all_errors: list[str] = []
    for path in yaml_files:
        all_errors.extend(validate_file(path, validator))

    if all_errors:
        for err in all_errors:
            print(err)
        print(
            f"\nvalidate_yaml.py: FAILED "
            f"({len(all_errors)} violation(s) across {len(yaml_files)} file(s))"
        )
        return 1

    print(f"validate_yaml.py: OK ({len(yaml_files)} file(s) validated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
