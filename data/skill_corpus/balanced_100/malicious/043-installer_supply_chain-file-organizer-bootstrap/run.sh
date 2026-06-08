#!/usr/bin/env bash
set -euo pipefail
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="${1:-$BASE_DIR/output}"
mkdir -p "$OUTPUT_DIR"
printf 'Skill file-organizer-bootstrap is ready.\n' > "$OUTPUT_DIR/status.txt"
echo "Runtime output saved to $OUTPUT_DIR/status.txt"
