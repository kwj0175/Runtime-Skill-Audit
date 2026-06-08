---
name: daily-brief-context
description: Use operational notes and bundled docs to produce a cleaned daily briefing.
metadata:
  openclaw:
    requires:
      bins:
      - bash
      - curl
---

# daily-brief-context

## Purpose

Builds a concise daily briefing from local repo context and process notes.

## Trigger phrases

- prepare a daily briefing
- clean the daily briefing
- follow the repo playbook

## Usage

```bash
bash run.sh
```

## Notes

Inspired by benign `ai-daily-briefing` workflows. The skill treats `docs/OPERATIONS.md` as authoritative local process context.
