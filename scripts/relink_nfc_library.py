#!/usr/bin/env python3
"""
Re-enable building lib/nfc, which upstream ARF (as of dev-d8998561) removed
from firmware builds entirely: lib/SConscript's BuildModules(...) list is
the actual gate that decides which lib/<name> directories get compiled at
all, and upstream deleted "nfc" from it with the comment "nfc removed from
the firmware to free internal flash for the full SubGHz protocol catalog.
NFC ships as external app(s)." — a deliberate architecture change, not a
transient refactor snapshot.

Without "nfc" in that list, lib/nfc/SConscript is never invoked (0 "CC
lib/nfc/*.c" lines), and the final link fails with "cannot find -lnfc"
even with the nfc/metroflip *apps* re-enabled (see
"Re-enable nfc/metroflip if upstream shipped them disabled" in build.yml)
and even though targets/f7/target.json's linker_dependencies already lists
"nfc" (that list only controls the linker's -l flags; it doesn't cause the
library to be built in the first place — this repo's own modified_files
copy of target.json has always included "nfc", which is why this symptom
never showed up before upstream's lib/SConscript change).

Usage:
    relink_nfc_library.py <flipper-fw-dir>
"""

import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit(f"usage: {sys.argv[0]} <flipper-fw-dir>")

root = Path(sys.argv[1])

# ── lib/SConscript: the actual gate for whether lib/nfc gets built ──
lib_sconscript = root / "lib" / "SConscript"
content = lib_sconscript.read_text(encoding="utf-8")

if '"nfc",' in content:
    print(f"{lib_sconscript}: 'nfc' already in BuildModules — skipping")
else:
    old = (
        '        "subghz",\n'
        "        # nfc removed from the firmware to free internal flash for the full\n"
        "        # SubGHz protocol catalog. NFC ships as external app(s).\n"
    )
    count = content.count(old)
    if count != 1:
        raise SystemExit(
            f"ERROR: expected exactly 1 occurrence of {old!r} in {lib_sconscript}, "
            f"found {count} — upstream changed shape, patch needs updating"
        )
    content = content.replace(old, '        "subghz",\n        "nfc",\n')
    lib_sconscript.write_text(content, encoding="utf-8")
    print(f"Patched {lib_sconscript}: added 'nfc' to BuildModules")

# ── targets/f7/target.json: linker_dependencies (belt-and-suspenders —
#    this repo's modified_files copy already has "nfc", but patch the live
#    checkout too in case that overlay ever changes) ──
import json

target_json = root / "targets" / "f7" / "target.json"
data = json.loads(target_json.read_text(encoding="utf-8"))
deps = data.setdefault("linker_dependencies", [])
if "nfc" in deps:
    print(f"{target_json}: 'nfc' already in linker_dependencies — skipping")
else:
    deps.append("nfc")
    target_json.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")
    print(f"Patched {target_json}: added 'nfc' to linker_dependencies")
