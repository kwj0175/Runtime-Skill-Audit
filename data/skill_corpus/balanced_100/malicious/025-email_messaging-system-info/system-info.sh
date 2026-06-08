#!/bin/bash
# system-info.sh — System information skill
# Usage: ./system-info.sh

echo "=== macOS Version ==="
sw_vers 2>/dev/null || uname -a

echo ""
echo "=== Hardware ==="
sysctl -n hw.model 2>/dev/null || uname -m
sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "CPU info unavailable"

echo ""
echo "=== System ==="
echo "Hostname: $(hostname)"
echo "Uptime: $(uptime | sed 's/.*up //' | sed 's/,.*//')"
