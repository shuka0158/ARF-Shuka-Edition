#!/usr/bin/env bash
# check_size.sh — abort if the built DFU exceeds the STM32WB C2 boundary.
# Usage: check_size.sh <path/to/firmware.dfu>
#
# fbt's own updater_package step (scripts/update.py: layout_check()) is the
# authoritative check — it compares the firmware size against the *actual*
# load address baked into the currently-bundled radio (BLE coprocessor)
# binary's signed metadata, and refuses to package (Error 2, "Firmware image
# overlaps C2 region and is not programmable!") if firmware runs into it.
#
# This script is a cheap, early proxy for that check so a bloated build fails
# fast instead of burning a full ~8-minute build. It previously hardcoded
# 860 KB, which was wrong: as of the radio stack currently pinned by this
# project's fbt config, the real boundary (from the build log's "Using
# guessed radio address 0x080CE000") is 0x080CE000 - 0x08000000 = 824 KB
# exactly, with zero required margin (fbt's own MIN_GAP_PAGES is 0). That
# 36 KB miscalibration meant this script was reporting "OK"/"WARN" on builds
# that fbt was silently failing to package on every single release.
#
# This is a proxy, not a substitute: the real gate is the "Build firmware"
# step now checking fbt's actual exit status. If the bundled radio stack ever
# changes, this number can drift again — watch for "Using guessed radio
# address 0x...." in the build log and recompute (address - 0x08000000).

set -euo pipefail

WARN_LIMIT=$((810 * 1024))   # 829 440 — leave real headroom, not just scrape by
HARD_LIMIT=$((824 * 1024))   # 843 776 — actual radio load address (0x080CE000) minus flash base

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
echo "Limit : 824 KB  (${HARD_LIMIT} bytes) — real radio load address minus flash base, not a round-number guess"
echo "Margin: ${HEADROOM_KB} KB"

if [[ $SIZE -gt $HARD_LIMIT ]]; then
    echo ""
    echo "FAIL: firmware exceeds the 824 KB C2 boundary by $(( SIZE - HARD_LIMIT )) bytes."
    echo "fbt will refuse to package OTA — reduce protocol count or strip unused apps."
    exit 1
elif [[ $SIZE -gt $WARN_LIMIT ]]; then
    echo ""
    echo "WARN: only ${HEADROOM_KB} KB of margin before the 824 KB C2 boundary. Consider trimming."
else
    echo ""
    echo "OK: firmware size is within limits."
fi
