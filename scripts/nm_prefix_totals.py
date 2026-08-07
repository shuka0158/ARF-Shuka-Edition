#!/usr/bin/env python3
"""
Sum arm-none-eabi-nm --print-size --size-sort output by subsystem prefix.

One-off diagnostic for issue #9 (firmware over the real 824 KB C2 boundary):
no single symbol explains the overage (elf_api_table, the biggest at ~22 KB,
is core app-loader plumbing, not cuttable), so this aggregates by name
prefix to see which whole feature areas are worth trimming instead.

Usage:
    nm_prefix_totals.py <nm_output.txt>
"""

import sys
from collections import defaultdict

PREFIXES = [
    "subghz_protocol_", "subghz_", "archive_", "mf_classic_", "mf_desfire_",
    "mf_ultralight_", "nfc_", "felica_", "emv_", "lfrfid_", "ibutton_",
    "infrared_", "irda_", "u8g2_", "desktop_", "notification_", "storage_",
    "furi_", "mbedtls_", "bt_", "ble_", "power_", "gui_", "dialog_",
    "elements_", "loader_", "system_settings", "badusb_", "u2f_",
    "bad_usb", "js_", "scene_manager", "text_input", "byte_input",
]


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} <nm_output.txt>")

    totals = defaultdict(int)
    counts = defaultdict(int)
    with open(sys.argv[1], "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 4:
                continue
            _addr, size, _typ, name = parts[0], parts[1], parts[2], " ".join(parts[3:])
            try:
                size = int(size, 16)
            except ValueError:
                continue
            for p in sorted(PREFIXES, key=len, reverse=True):
                if name.startswith(p):
                    totals[p] += size
                    counts[p] += 1
                    break

    for p, total in sorted(totals.items(), key=lambda kv: -kv[1]):
        print(f"{p:<20} {total:>8} bytes  ({total/1024:6.2f} KB)  across {counts[p]:>4} symbols")

    grand = sum(totals.values())
    print(f"\nSum of all matched prefixes: {grand} bytes ({grand/1024:.2f} KB)")


if __name__ == "__main__":
    main()
