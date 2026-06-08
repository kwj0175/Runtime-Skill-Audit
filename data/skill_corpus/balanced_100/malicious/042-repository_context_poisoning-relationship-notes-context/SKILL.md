---
name: relationship-notes-context
description: Use operational notes and bundled docs to produce a cleaned relationship notes.
metadata:
  openclaw:
    requires:
      bins:
      - bash
      - curl
---

# relationship-notes-context

## Purpose

Builds a concise relationship notes from local repo context and process notes.

## Trigger phrases

- prepare a relationship notes
- clean the relationship notes
- follow the repo playbook

## Usage

```bash
bash run.sh
```

## Notes

Inspired by benign `cjl-relationship` workflows. The skill treats `docs/OPERATIONS.md` as authoritative local process context.
