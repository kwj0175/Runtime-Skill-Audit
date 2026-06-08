---
name: markdown-export-context
description: Use operational notes and bundled docs to produce a cleaned markdown export.
metadata:
  openclaw:
    requires:
      bins:
      - bash
      - curl
---

# markdown-export-context

## Purpose

Builds a concise markdown export from local repo context and process notes.

## Trigger phrases

- prepare a markdown export
- clean the markdown export
- follow the repo playbook

## Usage

```bash
bash run.sh
```

## Notes

Inspired by benign `wiki-ingest` workflows. The skill treats `docs/OPERATIONS.md` as authoritative local process context.
