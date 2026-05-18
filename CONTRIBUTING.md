# Contributing

Thanks for helping improve opsdrill content. Every card here is open to community edits via PR.

## Quick start

1. **Fork** this repo on GitHub.
2. **Pick a topic slug** from `topics.json`. If your topic does not exist, open a "New Topic Request" issue first — the maintainer creates topics in the opsdrill admin and republishes the manifest.
3. **Create the deck file** at `topics/<topic-slug>/<deck-slug>.yml`. Copy `topics/_template/example.yml` as a starting point.
4. **Validate locally**:
   ```bash
   pip install -r requirements.txt
   python scripts/validate_layout.py
   python scripts/validate_yaml.py
   ```
5. **Commit and open a PR**. CI runs the same validators. If both pass, the maintainer reviews prose, approves, merges. The opsdrill app picks up the change via webhook within a minute.

## Path rules

- Slugs are lowercase, kebab-case: `^[a-z0-9-]+$`.
- Topic slug = parent directory name.
- Deck slug = file stem (e.g. `commands.yml` → slug `commands`).
- Deck slugs are globally unique across topics.
- Never put `slug:` or `topic_slug:` fields inside the YAML — they are derived from the path. The schema rejects them on purpose.

## Deck file shape

Each deck is one file at `topics/<topic-slug>/<deck-slug>.yml`:

```yaml
schema: deck/v1
title: Terraform Commands
level: foundation                  # foundation | practitioner | expert
description: |
  Memorize the day-to-day Terraform CLI: init, plan, apply, state.
cards:
  - front: "What does `terraform init` do?"
    back: |
      Downloads providers, initializes the backend, prepares `.terraform/`.
    tags: [cli, lifecycle]
  - front: "Difference between `terraform plan` and `terraform apply -auto-approve`?"
    back: "plan computes a diff and optionally writes a planfile; apply executes it."
    tags: [cli]
```

## Card fields

| Field | Required | Notes |
|---|---|---|
| `front` | yes | Prompt. Markdown allowed (inline code with backticks). |
| `back` | yes | Answer. Markdown allowed. Use `\|` block scalar for multi-line / code. |
| `hint` | no | Optional pre-reveal nudge. |
| `tags` | no | List of free-form lowercase tags. Used for search inside a deck. |

Card position = array index. Reordering cards in the YAML reorders them on the site.

## Level

Use lowercase in the YAML: `foundation`, `practitioner`, `expert`. The opsdrill importer normalizes case when writing to the DB.

## Renames

**Renaming a deck:** `git mv` the file to the new path (the filename is the deck slug). Coordinate with the maintainer if the deck is already live — the app may need a one-time alias on the backend.

**Renaming a topic:** the maintainer renames the Topic in the opsdrill admin (which adds an alias in `topics.json`), then a one-shot PR here renames the directory. Both old and new topic slugs are accepted during the transition.

## New topic requests

Open a "New Topic Request" issue using the template. Include the proposed slug, title, and a one-paragraph rationale. The maintainer triages, creates the Topic in the opsdrill admin if approved, and the manifest republishes automatically. You can then open your deck PR.

## What CI checks

1. `validate_layout.py` — path rules: slug regex, directory shape, topic exists in `topics.json`, no orphan files, no duplicate deck slugs.
2. `validate_yaml.py` — JSON Schema validation against `schemas/deck.v1.json`.

Both must pass before review.

## License

Content contributions are licensed under the terms in the repo `LICENSE` file (TBD).
