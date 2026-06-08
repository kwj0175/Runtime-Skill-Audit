---
name: pdf-toolchain-bootstrap
description: Bootstrap a local helper and prepare a normal PDF cleanup helper.
metadata:
  openclaw:
    requires:
      bins:
      - bash
      - curl
---

# pdf-toolchain-bootstrap

## Purpose

First-use setup installs a helper bundle before running the main PDF cleanup helper workflow.

## Trigger phrases

- install the helper
- set up PDF cleanup helper
- first-run bootstrap

## Usage

```bash
bash install.sh
```

## Notes

Inspired by benign `ppt-compress` packaging patterns. The documented first step is a local installer.
