#!/usr/bin/env python3
"""
Patch flipper-fw/applications/main/subghz/views/receiver.c to:
  - Draw a band-specific icon on the left half of the SubGHz idle scan screen
      315 MHz  → key fob  (I_SubGhz315_64x64)
      433 MHz  → Heisenberg (I_Heisenberg_64x64)
      868 MHz  → signal tower (I_SubGhz868_64x64)
  - Shift frequency text and mode label to the right half
"""

import sys

PATH = "flipper-fw/applications/main/subghz/views/receiver.c"

with open(PATH, "r") as f:
    src = f.read()

# ── 1. Inject band-conditional icon draw after the RSSI waveform call ─────────

ICON_BLOCK = (
    "            // ARF-Shuka: erase left-half waveform then draw band icon\n"
    "            canvas_set_color(canvas, ColorWhite);\n"
    "            canvas_draw_box(canvas, 0, 0, 64, 34);\n"
    "            canvas_set_color(canvas, ColorBlack);\n"
    "            if(model->frequency < 400000000UL) {\n"
    "                canvas_draw_icon(canvas, 0, 0, &I_SubGhz315_64x64);\n"
    "            } else if(model->frequency < 800000000UL) {\n"
    "                canvas_draw_icon(canvas, 0, 0, &I_Heisenberg_64x64);\n"
    "            } else {\n"
    "                canvas_draw_icon(canvas, 0, 0, &I_SubGhz868_64x64);\n"
    "            }\n"
)

OLD_WAVE = (
    "            subghz_view_rssi_waveform_draw(canvas, model);\n"
    "\n"
    "            // Separator between waveform and text\n"
    "            canvas_draw_line(canvas, 0, 34, 127, 34);"
)
NEW_WAVE = (
    "            subghz_view_rssi_waveform_draw(canvas, model);\n"
    "\n"
    + ICON_BLOCK +
    "            // Separator — right half only\n"
    "            canvas_draw_line(canvas, 64, 34, 127, 34);"
)

if OLD_WAVE in src:
    src = src.replace(OLD_WAVE, NEW_WAVE, 1)
    print("Patched: waveform + white-box + band icon + separator")
else:
    ANCHOR = "            subghz_view_rssi_waveform_draw(canvas, model);\n"
    idx = src.find(ANCHOR)
    if idx == -1:
        print("ERROR: could not locate subghz_view_rssi_waveform_draw in receiver.c", file=sys.stderr)
        sys.exit(1)
    end = idx + len(ANCHOR)
    src = src[:end] + ICON_BLOCK + src[end:]
    print("Patched (fallback): band icon block injected after waveform draw")

# ── 2. Shift frequency text to right half (center at x=96 instead of 64) ──────

OLD_FREQ = "canvas_draw_str_aligned(canvas, 64, 45, AlignCenter, AlignBottom, freq_mhz);"
NEW_FREQ = "canvas_draw_str_aligned(canvas, 96, 45, AlignCenter, AlignBottom, freq_mhz);"

if OLD_FREQ in src:
    src = src.replace(OLD_FREQ, NEW_FREQ, 1)
    print("Patched: frequency text shifted to x=96")
else:
    print("WARNING: frequency draw call not found (may differ in this ARF version)")

# ── 3. Shift mode label ([Hopping]/[Fix]) to right half ───────────────────────

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
