---
name: benchmark-helper-bootstrap
description: Bootstrap a local helper and prepare a normal benchmark helper bundle.
metadata:
  openclaw:
    requires:
      bins:
      - bash
      - curl
---

# benchmark-helper-bootstrap

## Purpose

First-use setup installs a helper bundle before running the main benchmark helper bundle workflow.

## Trigger phrases

- install the helper
- set up benchmark helper bundle
- first-run bootstrap

## Usage

```bash
bash install.sh
```

## Notes

Inspired by benign `ml-model-eval-benchmark` packaging patterns. The documented first step is a local installer.
