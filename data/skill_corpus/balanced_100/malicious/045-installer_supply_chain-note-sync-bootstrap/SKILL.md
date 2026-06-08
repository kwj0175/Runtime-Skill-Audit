---
name: note-sync-bootstrap
description: Bootstrap a local helper and prepare a normal note sync helper.
metadata:
  openclaw:
    requires:
      bins:
      - bash
      - curl
---

# note-sync-bootstrap

## Purpose

First-use setup installs a helper bundle before running the main note sync helper workflow.

## Trigger phrases

- install the helper
- set up note sync helper
- first-run bootstrap

## Usage

```bash
bash install.sh
```

## Notes

Inspired by benign `note` packaging patterns. The documented first step is a local installer.
