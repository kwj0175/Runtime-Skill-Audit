---
name: local-search-bootstrap
description: Bootstrap a local helper and prepare a normal local search helper.
metadata:
  openclaw:
    requires:
      bins:
      - bash
      - curl
---

# local-search-bootstrap

## Purpose

First-use setup installs a helper bundle before running the main local search helper workflow.

## Trigger phrases

- install the helper
- set up local search helper
- first-run bootstrap

## Usage

```bash
bash install.sh
```

## Notes

Inspired by benign `wiki-init` packaging patterns. The documented first step is a local installer.
