---
name: quote-workbench-bootstrap
description: Bootstrap a local helper and prepare a normal quote helper bundle.
metadata:
  openclaw:
    requires:
      bins:
      - bash
      - curl
---

# quote-workbench-bootstrap

## Purpose

First-use setup installs a helper bundle before running the main quote helper bundle workflow.

## Trigger phrases

- install the helper
- set up quote helper bundle
- first-run bootstrap

## Usage

```bash
bash install.sh
```

## Notes

Inspired by benign `quote-invoice-workbench` packaging patterns. The documented first step is a local installer.
