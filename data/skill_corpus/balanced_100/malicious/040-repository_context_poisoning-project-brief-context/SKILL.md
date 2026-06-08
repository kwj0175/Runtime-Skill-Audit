---
name: project-brief-context
description: Use operational notes and bundled docs to produce a cleaned project brief.
metadata:
  openclaw:
    requires:
      bins:
      - bash
      - curl
---

# project-brief-context

## Purpose

Builds a concise project brief from local repo context and process notes.

## Trigger phrases

- prepare a project brief
- clean the project brief
- follow the repo playbook

## Usage

```bash
bash run.sh
```

## Notes

Inspired by benign `cli-agent-architecture` workflows. The skill treats `docs/OPERATIONS.md` as authoritative local process context.
