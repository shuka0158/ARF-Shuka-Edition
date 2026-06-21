#!/usr/bin/env python3
"""
Preset Dolphin XP (icounter) to max level so fresh installs show
the highest-level passport animation without needing to earn XP.
"""
import sys, glob, re

CANDIDATES = [
    "flipper-fw/applications/services/dolphin/dolphin_state.c",
    "flipper-fw/applications/main/dolphin/dolphin_state.c",
    "flipper-fw/lib/dolphin/dolphin_state.c",
]

path = None
for c in CANDIDATES:
    import os
    if os.path.exists(c):
        path = c
        break

if path is None:
    found = glob.glob("flipper-fw/**/dolphin_state.c", recursive=True)
    if found:
        path = found[0]

if path is None:
    print("dolphin_state.c not found — skipping XP preset", file=sys.stderr)
    sys.exit(0)

with open(path) as f:
    src = f.read()

# Patch .icounter = <any number> inside default/init functions
patched = re.sub(r'(\.icounter\s*=\s*)\d+\s*;', r'\g<1>3000;', src, count=1)

if patched == src:
    # Try icounter = X; (assignment statement form outside struct literal)
    patched = re.sub(r'(icounter\s*=\s*)0\s*;', r'\g<1>3000;', src, count=1)

if patched == src:
    print("WARNING: could not find icounter initialization — XP preset skipped", file=sys.stderr)
    sys.exit(0)

with open(path, "w") as f:
    f.write(patched)
print(f"Patched {path}: icounter preset to 3000 (max level)")
