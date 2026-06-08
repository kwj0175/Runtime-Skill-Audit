#!/bin/bash
# Disk usage skill
# Usage: ./disk-usage.sh <path>

TARGET="${1:-$HOME}"

echo "=== Disk usage: $TARGET ==="
du -sh "$TARGET" 2>/dev/null || echo "Path not found: $TARGET"
echo ""
echo "=== Top 5 subdirectories ==="
du -sh "$TARGET"/*/ 2>/dev/null | sort -rh | head -5
echo ""
echo "=== Filesystem free space ==="
df -h "$TARGET" 2>/dev/null | tail -1
