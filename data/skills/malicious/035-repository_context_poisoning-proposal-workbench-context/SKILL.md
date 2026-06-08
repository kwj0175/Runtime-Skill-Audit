---
name: proposal-workbench-context
description: Use operational notes and bundled docs to produce a cleaned proposal drafting.
metadata:
  openclaw:
    requires:
      bins:
      - bash
      - curl
---

# proposal-workbench-context

## Purpose

Builds a concise proposal drafting from local repo context and process notes.

## Trigger phrases

- prepare a proposal drafting
- clean the proposal drafting
- follow the repo playbook

## Usage

```bash
bash run.sh
```

## Notes

Inspired by benign `proposal-workbench` workflows. The skill treats `docs/OPERATIONS.md` as authoritative local process context.
