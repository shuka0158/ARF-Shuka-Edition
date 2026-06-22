#!/usr/bin/env python3
"""
Patch about.c to display Shuka-ARF build attribution.

Injects two extra lines at the end of the info string list:
  "Built by Heisenberg [shuka0158]"
  "github.com/shuka0158/ARF-Shuka-Edition"
"""

import sys, os, glob, re

ATTR_LINE = "Built by Heisenberg [shuka0158]"
URL_LINE  = "github.com/shuka0158/ARF-Shuka-Edition"
GUARD     = "shuka_attribution_patched"

CANDIDATES = [
    "flipper-fw/applications/settings/about/about.c",
    "flipper-fw/applications/about/about.c",
    "flipper-fw/applications/main/about/about.c",
]

path = next((c for c in CANDIDATES if os.path.exists(c)), None)
if not path:
    hits = glob.glob("flipper-fw/**/about.c", recursive=True)
    path = hits[0] if hits else None

if not path:
    print("WARNING: about.c not found — skipping attribution patch", file=sys.stderr)
    sys.exit(0)

print(f"Patching: {path}")

with open(path) as f:
    src = f.read()

if GUARD in src:
    print("Already patched — skipping")
    sys.exit(0)

patched = False

# ── Strategy A: static const char* array of info lines ───────────────────────
# Matches:  static const char* const foo[] = { "line1", "line2", NULL };
#       or: static const char* foo[] = { ... NULL };
array_pat = re.compile(
    r'(static\s+const\s+char\s*\*\s*(?:const\s+)?\w+\[\]\s*=\s*\{)'
    r'((?:[^}]|\n)*?)'
    r'(NULL\s*\}\s*;)',
    re.DOTALL
)
def inject_array(m):
    return (
        m.group(1)
        + m.group(2)
        + f'    "{ATTR_LINE}",\n'
        + f'    "{URL_LINE}",\n'
        + "    "
        + m.group(3)
    )
new_src, n = array_pat.subn(inject_array, src, count=1)
if n:
    src = new_src
    patched = True
    print("Patched via Strategy A: injected into string array")

# ── Strategy B: last canvas_draw_str_aligned or canvas_draw_str call ─────────
if not patched:
    # Find the last occurrence of canvas_draw_str... and insert after its line
    draw_pat = re.compile(
        r'(canvas_draw_str(?:_aligned)?\s*\([^;]+;\s*\n)'
    )
    matches = list(draw_pat.finditer(src))
    if matches:
        last = matches[-1]
        insert_pos = last.end()
        # Derive the x/y from the last call or use safe defaults
        addition = (
            f'    canvas_draw_str(canvas, 0, 60, "{ATTR_LINE}");\n'
            f'    canvas_draw_str(canvas, 0, 70, "{URL_LINE}");\n'
        )
        src = src[:insert_pos] + addition + src[insert_pos:]
        patched = True
        print("Patched via Strategy B: canvas_draw_str appended")

# ── Strategy C: inject before the closing brace of the last render function ──
if not patched:
    # Find last render/draw function closing brace
    fn_pat = re.compile(
        r'(static\s+void\s+\w*(?:render|draw|view)\w*\s*\([^)]*\)\s*\{)'
        r'((?:[^{}]|\{[^{}]*\})*)'
        r'(\})',
        re.DOTALL | re.IGNORECASE
    )
    matches = list(fn_pat.finditer(src))
    if matches:
        last = matches[-1]
        addition = (
            f'\n    canvas_draw_str(canvas, 0, 60, "{ATTR_LINE}");\n'
            f'    canvas_draw_str(canvas, 0, 70, "{URL_LINE}");\n'
        )
        insert_pos = last.start(3)
        src = src[:insert_pos] + addition + src[insert_pos:]
        patched = True
        print("Patched via Strategy C: injected before render function closing brace")

if not patched:
    print("WARNING: no injection point found in about.c — attribution not added", file=sys.stderr)
    print("  File:", path, file=sys.stderr)
    sys.exit(0)

# Prepend guard comment
src = f"// {GUARD}\n" + src

with open(path, "w") as f:
    f.write(src)

print(f"about.c attribution patch applied OK ({path})")
