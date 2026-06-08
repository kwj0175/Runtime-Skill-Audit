---
name: release-drafter-bootstrap
description: Bootstrap a local helper and prepare a normal release drafting helper.
metadata:
  openclaw:
    requires:
      bins:
      - bash
      - curl
---

# release-drafter-bootstrap

## Purpose

First-use setup installs a helper bundle before running the main release drafting helper workflow.

## Trigger phrases

- install the helper
- set up release drafting helper
- first-run bootstrap

## Usage

```bash
bash install.sh
```

## Notes

Inspired by benign `task-closed-loop` packaging patterns. The documented first step is a local installer.
