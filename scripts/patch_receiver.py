#!/usr/bin/env python3
"""
Patch flipper-fw/applications/main/subghz/views/receiver.c to:
  - Draw a band-specific icon on the left half of the SubGHz idle scan screen:
        315 MHz  → key fob  (I_SubGhz315_64x64)
        433 MHz  → Heisenberg (I_Heisenberg_64x64)
        868/915  → signal tower (I_SubGhz868_64x64)
  - Shift frequency text and mode label to the right half

Band detection: model->frequency_str holds a string like "433.92 MHz".
We check its first character at draw time — '3'=315 MHz, '8'/'9'=800+ MHz.
The patch auto-detects whether frequency_str is a FuriString* or char[].
"""

import sys, re

PATH = "flipper-fw/applications/main/subghz/views/receiver.c"

with open(PATH, "r") as f:
    src = f.read()

# ── 0. Detect whether frequency_str is FuriString* or char[] ─────────────────
# Look for furi_string_get_cstr(model->frequency_str) anywhere in the file.
if "furi_string_get_cstr(model->frequency_str)" in src:
    freq_first_char = "furi_string_get_cstr(model->frequency_str)[0]"
    print("Detected: frequency_str is FuriString*")
else:
    freq_first_char = "model->frequency_str[0]"
    print("Detected: frequency_str is char[]")

# ── 1. Build the band-conditional icon block ───────────────────────────────────
ICON_BLOCK = (
    "            // ARF-Shuka: erase left-half waveform then draw band icon\n"
    "            canvas_set_color(canvas, ColorWhite);\n"
    "            canvas_draw_box(canvas, 0, 0, 64, 34);\n"
    "            canvas_set_color(canvas, ColorBlack);\n"
    "            {\n"
    f"                char _bch = {freq_first_char};\n"
    "                if(_bch == '3') {\n"
    "                    canvas_draw_icon(canvas, 0, 0, &I_SubGhz315_64x64);\n"
    "                } else if(_bch == '8' || _bch == '9') {\n"
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

# ── 3. Shift frequency text to right half (x=96 instead of 64) ───────────────
# Match any canvas_draw_str_aligned call at x=64, y=45 with AlignCenter/AlignBottom
freq_shift = re.sub(
    r'(canvas_draw_str_aligned\s*\(\s*canvas\s*,\s*)64(\s*,\s*45\s*,\s*AlignCenter\s*,\s*AlignBottom)',
    r'\g<1>96\2',
    src,
    count=1
)
if freq_shift != src:
    src = freq_shift
    print("Patched: frequency text shifted to x=96")
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
