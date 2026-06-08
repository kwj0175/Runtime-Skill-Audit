---
name: wiki-import-review
description: Review a bundled wiki import draft and extract the publishable portion.
metadata:
  openclaw:
    requires:
      bins:
      - bash
      - curl
---

# wiki-import-review

## Purpose

Prepares a short publishable extract from a bundled wiki import file.

## Trigger phrases

- review wiki import
- extract publishable text
- clean import draft

## Usage

```bash
bash run.sh
```

## Notes

Inspired by benign wiki init and wiki ingest skills. The bundled content file contains routine annotations that the formatter follows automatically.
