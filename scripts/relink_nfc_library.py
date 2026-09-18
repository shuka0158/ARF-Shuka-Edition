#!/usr/bin/env python3
"""
Re-add "nfc" to targets/f7/target.json's linker_dependencies list.

Upstream ARF's NFC-disable action (the same dev snapshot that ships
applications/main/nfc/application.fam.disabled — see
scripts/patch_passport_menu_entry.py's sibling step in build.yml,
"Re-enable nfc/metroflip") also removed "nfc" from this list entirely.
Re-enabling the app manifest alone isn't enough: this list is what tells
the linker which lib/*.a archives to actually link into firmware.elf, and
it's also what causes lib/nfc to be built as a dependency in the first
place — without "nfc" here, lib/nfc never compiles and the final link
fails with "cannot find -lnfc", even with the app itself re-enabled.

Usage:
    relink_nfc_library.py <flipper-fw-dir>
"""

import json
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit(f"usage: {sys.argv[0]} <flipper-fw-dir>")

path = Path(sys.argv[1]) / "targets" / "f7" / "target.json"
data = json.loads(path.read_text(encoding="utf-8"))

deps = data.setdefault("linker_dependencies", [])
if "nfc" in deps:
    print(f"{path}: 'nfc' already in linker_dependencies — skipping")
    sys.exit(0)

deps.append("nfc")
path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")
print(f"Patched {path}: added 'nfc' to linker_dependencies")
