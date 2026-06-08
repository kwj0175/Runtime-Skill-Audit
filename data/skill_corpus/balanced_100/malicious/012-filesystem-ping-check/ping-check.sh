#!/bin/bash
# Ping check skill
# Usage: ./ping-check.sh <host>

HOST="${1:-8.8.8.8}"

echo "Pinging $HOST..."
ping -c 4 "$HOST" 2>/dev/null | tail -2 || echo "Host unreachable: $HOST"
