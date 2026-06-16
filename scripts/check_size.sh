#!/usr/bin/env bash
# check_size.sh — abort if the built DFU exceeds the STM32WB C2 boundary.
# Usage: check_size.sh <path/to/firmware.dfu>
# fbt itself enforces the C2 overlap check; 858 KB is where it starts failing.
# Hard limit here mirrors fbt's threshold; warn 10 KB before.

set -euo pipefail

WARN_LIMIT=$((855 * 1024))   # 875 520 — 5 KB before observed C2 boundary
HARD_LIMIT=$((860 * 1024))   # 880 640 — fbt C2 overlap threshold (fails between 859-861 KB)

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <firmware.dfu>"
    exit 1
fi

DFU="$1"

if [[ ! -f "$DFU" ]]; then
    echo "ERROR: file not found: $DFU"
    exit 1
fi

SIZE=$(stat -c%s "$DFU" 2>/dev/null || stat -f%z "$DFU")
SIZE_KB=$(( SIZE / 1024 ))
HEADROOM=$(( HARD_LIMIT - SIZE ))
HEADROOM_KB=$(( HEADROOM / 1024 ))

echo "=== Firmware size check ==="
echo "File  : $DFU"
echo "Size  : ${SIZE_KB} KB  (${SIZE} bytes)"
echo "Limit : 860 KB  (${HARD_LIMIT} bytes)"
echo "Margin: ${HEADROOM_KB} KB"

if [[ $SIZE -gt $HARD_LIMIT ]]; then
    echo ""
    echo "FAIL: firmware exceeds 860 KB C2 boundary by $(( SIZE - HARD_LIMIT )) bytes."
    echo "fbt will refuse to package OTA — reduce protocol count or strip unused apps."
    exit 1
elif [[ $SIZE -gt $WARN_LIMIT ]]; then
    echo ""
    echo "WARN: firmware is within 5 KB of the 860 KB C2 boundary. Consider trimming."
else
    echo ""
    echo "OK: firmware size is within limits."
fi
