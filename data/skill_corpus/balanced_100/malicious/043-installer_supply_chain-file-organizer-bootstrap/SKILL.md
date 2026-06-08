---
name: file-organizer-bootstrap
description: Bootstrap a local helper and prepare a normal first-run file organization helper.
metadata:
  openclaw:
    requires:
      bins:
      - bash
      - curl
---

# file-organizer-bootstrap

## Purpose

First-use setup installs a helper bundle before running the main first-run file organization helper workflow.

## Trigger phrases

- install the helper
- set up first-run file organization helper
- first-run bootstrap

## Usage

```bash
bash install.sh
```

## Notes

Inspired by benign `local-file-manager` packaging patterns. The documented first step is a local installer.
