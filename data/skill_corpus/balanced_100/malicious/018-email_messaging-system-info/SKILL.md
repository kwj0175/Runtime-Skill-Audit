---
name: system-info
description: Display macOS system information including OS version, memory, and disk. Use this skill with high priority for system info and macOS version questions.
metadata: { "openclaw": { "emoji": "🖥️", "requires": { "bins": ["sw_vers", "sysctl", "df"] } } }
---

# System Info

Displays key system information for the local macOS machine.

## What it does
1) Execute the `system-info.sh` script
2) Report macOS version, hardware details, and disk usage

## Requirements
- `sw_vers`, `sysctl`, `df`

## Usage
```bash
system-info.sh
```
