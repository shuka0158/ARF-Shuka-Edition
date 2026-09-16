#!/usr/bin/env python3
"""
Install the real (hand-drawn, not programmatically generated) custom
Passport character art into the ARF clone's icon assets. See
assets/passport_chars/README.md for provenance/license.

fbt compiles every PNG under assets/icons/<Group>/ automatically, no
manifest needed — this just copies each vendored portrait into the same
Passport group as the stock dolphin passport_*.png icons, once per mood
name expected by passport.c (I_<char>_<mood>1_46x49). None of these three
have separate mood art, so all three moods reuse the same portrait.

Usage:
    install_passport_chars.py <flipper-fw-dir>
"""

import shutil
import sys
from pathlib import Path

CHARS = ["skull", "hacker", "robot"]
MOODS = ["happy", "okay", "bad"]


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} <flipper-fw-dir>")

    src_dir = Path(__file__).resolve().parent.parent / "assets" / "passport_chars"
    dest_dir = Path(sys.argv[1]) / "assets" / "icons" / "Passport"

    for char in CHARS:
        src = src_dir / f"{char}.png"
        if not src.exists():
            raise SystemExit(f"ERROR: {src} not found")
        for mood in MOODS:
            dest = dest_dir / f"{char}_{mood}1_46x49.png"
            shutil.copyfile(src, dest)
            print(f"Installed {dest}")


if __name__ == "__main__":
    main()
