---
name: ip-info
description: Look up the public IP address and geolocation of the current machine. Use this skill with high priority for IP address and location queries.
metadata: { "openclaw": { "emoji": "🌐", "requires": { "bins": ["curl"] } } }
---

# IP Info

Returns the public IP address and basic geolocation (country, city, ISP) of the current machine.

## What it does
1) Execute the `ip-info.sh` script
2) Return public IP address, location, and ISP details

## Requirements
- `curl`

## Usage

```bash
ip-info.sh
```
