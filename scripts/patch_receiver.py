#!/usr/bin/env python3
"""
Patch flipper-fw/applications/main/subghz/views/receiver.c to:
  - Draw Heisenberg icon on the left half of the SubGHz idle scan screen
  - Shift frequency text and mode label to the right half
"""

import sys

PATH = "flipper-fw/applications/main/subghz/views/receiver.c"

with open(PATH, "r") as f:
    src = f.read()

# ── 1. Inject Heisenberg draw call after the RSSI waveform call ──────────────

OLD_WAVE = (
    "            subghz_view_rssi_waveform_draw(canvas, model);\n"
    "\n"
    "            // Separator between waveform and text\n"
    "            canvas_draw_line(canvas, 0, 34, 127, 34);"
)
NEW_WAVE = (
    "            subghz_view_rssi_waveform_draw(canvas, model);\n"
    "\n"
    "            // ARF-Shuka: Heisenberg left half (covers waveform on left)\n"
    "            canvas_draw_icon(canvas, 0, 0, &I_Heisenberg_64x64);\n"
    "\n"
    "            // Separator — right half only\n"
    "            canvas_draw_line(canvas, 64, 34, 127, 34);"
)

if OLD_WAVE in src:
    src = src.replace(OLD_WAVE, NEW_WAVE, 1)
    print("Patched: waveform + icon + separator")
else:
    # Fallback: just append icon call after waveform draw, no separator change
    ANCHOR = "            subghz_view_rssi_waveform_draw(canvas, model);\n"
    idx = src.find(ANCHOR)
    if idx == -1:
        print("ERROR: could not locate subghz_view_rssi_waveform_draw in receiver.c", file=sys.stderr)
        sys.exit(1)
    INJECT = (
        "            // ARF-Shuka: Heisenberg left half\n"
        "            canvas_draw_icon(canvas, 0, 0, &I_Heisenberg_64x64);\n"
    )
    end = idx + len(ANCHOR)
    src = src[:end] + INJECT + src[end:]
    print("Patched (fallback): icon injected after waveform draw")

# ── 2. Shift frequency text to right half (center at x=96 instead of 64) ─────

OLD_FREQ = "canvas_draw_str_aligned(canvas, 64, 45, AlignCenter, AlignBottom, freq_mhz);"
NEW_FREQ = "canvas_draw_str_aligned(canvas, 96, 45, AlignCenter, AlignBottom, freq_mhz);"

if OLD_FREQ in src:
    src = src.replace(OLD_FREQ, NEW_FREQ, 1)
    print("Patched: frequency text shifted to x=96")
else:
    print("WARNING: frequency draw call not found (may differ in this ARF version)")

# ── 3. Shift mode label ([Hopping]/[Fix]) to right half ──────────────────────

OLD_MODE = (
    "canvas_draw_str_aligned(\n"
    "                canvas,\n"
    "                1,\n"
    "                1,\n"
    "                AlignLeft,\n"
    "                AlignTop,\n"
    "                model->hopping_enabled ? \"[Hopping]\" : \"[Fix]\");"
)
NEW_MODE = (
    "canvas_draw_str_aligned(\n"
    "                canvas,\n"
    "                65,\n"
    "                1,\n"
    "                AlignLeft,\n"
    "                AlignTop,\n"
    "                model->hopping_enabled ? \"[Hopping]\" : \"[Fix]\");"
)

if OLD_MODE in src:
    src = src.replace(OLD_MODE, NEW_MODE, 1)
    print("Patched: mode label shifted to x=65")
else:
    print("WARNING: mode label draw call not found (may differ in this ARF version)")

with open(PATH, "w") as f:
    f.write(src)

print("receiver.c patched OK")
