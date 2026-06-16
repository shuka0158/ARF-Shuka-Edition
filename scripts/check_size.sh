#!/usr/bin/env bash
# check_size.sh — abort if the built DFU exceeds the Flipper Zero radio flash limit.
# Usage: check_size.sh <path/to/firmware.dfu>
# The DFU payload must stay under 880 KB; we warn at 860 KB and fail at 880 KB.

set -euo pipefail

WARN_LIMIT=$((860 * 1024))   # 880 540
HARD_LIMIT=$((880 * 1024))   # 901 120

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
echo "Limit : 880 KB  (${HARD_LIMIT} bytes)"
echo "Margin: ${HEADROOM_KB} KB"

if [[ $SIZE -gt $HARD_LIMIT ]]; then
    echo ""
    echo "FAIL: firmware exceeds 880 KB hard limit by $(( SIZE - HARD_LIMIT )) bytes."
    echo "This will brick the radio on flash — reduce protocol count or strip unused apps."
    exit 1
elif [[ $SIZE -gt $WARN_LIMIT ]]; then
    echo ""
    echo "WARN: firmware is within 20 KB of the 880 KB limit. Consider trimming."
else
    echo ""
    echo "OK: firmware size is within limits."
fi
