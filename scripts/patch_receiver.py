#!/usr/bin/env python3
"""
Patch flipper-fw/applications/main/subghz/views/receiver.c to:
  - Draw a band-specific icon on the left half of the SubGHz idle scan screen
      315 MHz  → key fob  (I_SubGhz315_64x64)
      433 MHz  → Heisenberg (I_Heisenberg_64x64)
      868 MHz  → signal tower (I_SubGhz868_64x64)
  - Shift frequency text and mode label to the right half

Band detection uses the first character of the local freq string variable
(e.g. freq_mhz) that already exists in the draw function — '3'=315, '8'/'9'=800+.
"""

import sys, re

PATH = "flipper-fw/applications/main/subghz/views/receiver.c"

with open(PATH, "r") as f:
    src = f.read()

# ── 0. Find the local frequency-string variable used in the draw function ─────
# We look for the canvas_draw_str call that renders the frequency text and
# extract the variable name from the last argument.  That variable holds a
# string like "433.92 MHz" and is guaranteed to be in scope at the waveform draw.
freq_var = "freq_mhz"   # safe default
m = re.search(
    r'canvas_draw_str_aligned\s*\(\s*canvas\s*,\s*\d+\s*,\s*\d+\s*,\s*\w+\s*,\s*\w+\s*,\s*(\w+)\s*\)',
    src
)
if m:
    freq_var = m.group(1)
print(f"Frequency string variable detected: '{freq_var}'")

# ── 1. Build the band-conditional icon block ───────────────────────────────────
#
# First character of freq_var:
#   '3' → 315 MHz (North American car remotes)
#   '4' → 433 MHz (EU car remotes / standard)
#   '8' or '9' → 868 / 915 MHz (EU IoT / LoRa)
#
ICON_BLOCK = (
    "            // ARF-Shuka: erase left-half waveform then draw band icon\n"
    "            canvas_set_color(canvas, ColorWhite);\n"
    "            canvas_draw_box(canvas, 0, 0, 64, 34);\n"
    "            canvas_set_color(canvas, ColorBlack);\n"
    "            {\n"
    f"                const char* _bfreq = {freq_var};\n"
    "                if(_bfreq && _bfreq[0] == '3') {\n"
    "                    canvas_draw_icon(canvas, 0, 0, &I_SubGhz315_64x64);\n"
    "                } else if(_bfreq && (_bfreq[0] == '8' || _bfreq[0] == '9')) {\n"
    "                    canvas_draw_icon(canvas, 0, 0, &I_SubGhz868_64x64);\n"
    "                } else {\n"
    "                    canvas_draw_icon(canvas, 0, 0, &I_Heisenberg_64x64);\n"
    "                }\n"
    "            }\n"
)

# ── 2. Inject after the RSSI waveform call ────────────────────────────────────

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

# ── 3. Shift frequency text to right half (center at x=96 instead of 64) ──────

OLD_FREQ = "canvas_draw_str_aligned(canvas, 64, 45, AlignCenter, AlignBottom, freq_mhz);"
NEW_FREQ = "canvas_draw_str_aligned(canvas, 96, 45, AlignCenter, AlignBottom, freq_mhz);"

if OLD_FREQ in src:
    src = src.replace(OLD_FREQ, NEW_FREQ, 1)
    print("Patched: frequency text shifted to x=96")
else:
    # Try with the detected variable name
    OLD_FREQ2 = f"canvas_draw_str_aligned(canvas, 64, 45, AlignCenter, AlignBottom, {freq_var});"
    NEW_FREQ2 = f"canvas_draw_str_aligned(canvas, 96, 45, AlignCenter, AlignBottom, {freq_var});"
    if OLD_FREQ2 in src:
        src = src.replace(OLD_FREQ2, NEW_FREQ2, 1)
        print(f"Patched: frequency text shifted to x=96 (var={freq_var})")
    else:
        print("WARNING: frequency draw call not found (may differ in this ARF version)")

# ── 4. Shift mode label ([Hopping]/[Fix]) to right half ───────────────────────

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
