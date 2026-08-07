#!/usr/bin/env python3
"""
Remove one or more App(...) blocks from a Flipper .fam manifest by appid.

.fam files are plain Python, so App() blocks aren't always single-line and
can't be safely stripped with a line-oriented sed pattern. This scans for
top-level (0-indented) `App(` ... `)` blocks and drops any whose body
contains `appid="<name>"` for one of the given names.

Usage:
    remove_fam_apps.py <file.fam> <appid1> [appid2 ...]
"""

import sys


def main():
    if len(sys.argv) < 3:
        raise SystemExit(f"usage: {sys.argv[0]} <file.fam> <appid1> [appid2 ...]")

    path = sys.argv[1]
    targets = set(sys.argv[2:])

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    out = []
    i = 0
    removed = set()
    while i < len(lines):
        line = lines[i]
        if line.startswith("App("):
            block = [line]
            j = i + 1
            while j < len(lines) and lines[j].rstrip("\n") != ")":
                block.append(lines[j])
                j += 1
            if j < len(lines):
                block.append(lines[j])  # closing ")"
                j += 1
            block_text = "".join(block)
            matched = next((t for t in targets if f'appid="{t}"' in block_text), None)
            if matched:
                removed.add(matched)
                # also drop one trailing blank separator line, if present
                if j < len(lines) and lines[j].strip() == "":
                    j += 1
                i = j
                continue
            else:
                out.extend(block)
                i = j
                continue
        out.append(line)
        i += 1

    missing = targets - removed
    if missing:
        raise SystemExit(f"ERROR: appid(s) not found in {path}: {sorted(missing)}")

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(out)

    print(f"Removed {len(removed)} App block(s) from {path}: {sorted(removed)}")


if __name__ == "__main__":
    main()
