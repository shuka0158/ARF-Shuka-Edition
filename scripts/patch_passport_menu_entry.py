#!/usr/bin/env python3
"""
Register the Passport app (applications/settings/passport) with the
"settings_apps" metapackage, so fbt actually builds it and the Settings
menu shows it. Adding a new settings app's directory isn't enough on its
own — applications/settings/application.fam explicitly enumerates every
appid it provides, and unlisted apps are silently skipped (no error, no
warning, just never compiled).

Usage:
    patch_passport_menu_entry.py <flipper-fw-dir>
"""

import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit(f"usage: {sys.argv[0]} <flipper-fw-dir>")

path = Path(sys.argv[1]) / "applications" / "settings" / "application.fam"
content = path.read_text(encoding="utf-8")

if '"passport"' in content:
    print(f"{path}: already lists passport — skipping")
    sys.exit(0)

old = '        "about",\n    ],'
new = '        "about",\n        "passport",\n    ],'

count = content.count(old)
if count != 1:
    raise SystemExit(
        f"ERROR: expected exactly 1 occurrence of the provides-list tail in {path}, "
        f"found {count} — upstream changed shape, patch needs updating"
    )

path.write_text(content.replace(old, new), encoding="utf-8")
print(f"Patched {path}")
