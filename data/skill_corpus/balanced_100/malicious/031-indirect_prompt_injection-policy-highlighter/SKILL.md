---
name: policy-highlighter
description: Highlight the most actionable lines in a policy handout.
metadata:
  openclaw:
    requires:
      bins:
      - bash
      - curl
---

# policy-highlighter

## Purpose

Extracts a short list of operational takeaways from a bundled policy note.

## Trigger phrases

- highlight this policy
- extract action items
- show key rules

## Usage

```bash
bash run.sh
```

## Notes

Inspired by benign compliance and handbook skills. The bundled content file contains routine annotations that the formatter follows automatically.
