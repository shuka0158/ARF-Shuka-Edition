#!/usr/bin/env python3
"""
Generate custom Flipper Zero dolphin-format animations for ARF-Shuka-Edition.

In CI this is called with output pointing to flipper-fw/assets/dolphin/external/
so fbt compiles them directly into the resources pack (resources.ths in the .tgz).

Usage: python3 generate_animations.py <output_dir>
Requires: Pillow  (pip install Pillow)

Frame naming: frame_0.png, frame_1.png ... (no zero-padding — fbt requirement)
Directory naming: L{level}_{Name}_{W}x{H}  (e.g. L1_RF_Sweep_128x64)
"""

import os, sys, math
from PIL import Image, ImageDraw

OUT = sys.argv[1] if len(sys.argv) > 1 else "external"
W, H = 128, 64


def save_frame(img, directory, index):
    img.convert("1").save(os.path.join(directory, f"frame_{index}.png"))


def write_meta(anim_dir, passive_frames, active_frames=0, frame_rate=4,
               duration=3600, active_cooldown=0, bubbles=None):
    total = passive_frames + active_frames
    order = " ".join(str(i) for i in range(total))
    lines = [
        "Filetype: Flipper Animation",
        "Version: 1",
        "",
        f"Width: {W}",
        f"Height: {H}",
        f"Passive frames: {passive_frames}",
        f"Active frames: {active_frames}",
        f"Frames order: {order}",
        f"Active cycles: {1 if active_frames else 0}",
        f"Frame rate: {frame_rate}",
        f"Duration: {duration}",
        f"Active cooldown: {active_cooldown}",
        "",
        f"Bubble slots: {len(bubbles) if bubbles else 0}",
    ]
    if bubbles:
        for i, b in enumerate(bubbles):
            lines += [
                "",
                f"Slot: {i}",
                f"X: {b['x']}",
                f"Y: {b['y']}",
                f"Text: {b['text']}",
                f"AlignH: {b.get('align_h', 'Left')}",
                f"AlignV: {b.get('align_v', 'Bottom')}",
                f"StartFrame: {b['start']}",
                f"EndFrame: {b['end']}",
            ]
    with open(os.path.join(anim_dir, "meta.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Animation 1: RF Signal Sweep — radio tower emitting expanding arcs
# ─────────────────────────────────────────────────────────────────────────────

def make_rf_sweep():
    name = "L1_RF_Sweep_128x64"
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    FRAMES = 8
    TX, TY = 14, 54      # tower base

    for f in range(FRAMES):
        img = Image.new("1", (W, H), 1)
        draw = ImageDraw.Draw(img)

        # Tower mast
        draw.line([(TX, TY), (TX, TY - 22)], fill=0, width=1)
        # Cross-arms
        draw.line([(TX - 6, TY - 5), (TX + 6, TY - 5)], fill=0)
        draw.line([(TX - 4, TY - 13), (TX + 4, TY - 13)], fill=0)
        draw.line([(TX - 8, TY), (TX + 8, TY)], fill=0)
        # Blinking tip
        if f % 2 == 0:
            draw.ellipse([(TX - 2, TY - 25), (TX + 2, TY - 21)], fill=0)

        # 3 expanding arcs offset by phase
        for arc in range(3):
            phase = (f + arc * 3) % FRAMES
            radius = phase * 9 + 6
            if radius > W - TX - 4:
                continue
            cx, cy = TX, TY - 20
            bbox = [cx - radius, cy - radius * 3 // 5,
                    cx + radius, cy + radius * 3 // 5]
            try:
                draw.arc(bbox, start=-65, end=65, fill=0, width=1)
            except Exception:
                pass

        # Ground line
        draw.line([(0, TY + 1), (W, TY + 1)], fill=0)

        # Right side: signal strength bars (animated)
        bx = W - 36
        by = TY
        for b in range(5):
            bh = 6 + b * 6
            fill_bars = ((f + 1) % (FRAMES + 1))
            filled = b < (fill_bars * 5 // FRAMES)
            draw.rectangle([(bx + b * 7, by - bh), (bx + b * 7 + 4, by)],
                           fill=(0 if filled else 1), outline=0)

        save_frame(img, d, f)

    write_meta(d, passive_frames=FRAMES, frame_rate=5, duration=3600)
    return name


# ─────────────────────────────────────────────────────────────────────────────
# Animation 2: Car Key Capture — car, rolling RKE burst, lock snaps shut
# ─────────────────────────────────────────────────────────────────────────────

def draw_car(draw, x, y):
    draw.rectangle([(x, y + 5), (x + 28, y + 16)], fill=0)
    draw.rectangle([(x + 5, y), (x + 23, y + 7)], fill=0)
    draw.rectangle([(x + 6, y + 1), (x + 12, y + 6)], fill=1)
    draw.rectangle([(x + 14, y + 1), (x + 22, y + 6)], fill=1)
    for wx in [x + 1, x + 23]:
        draw.ellipse([(wx, y + 14), (wx + 5, y + 19)], fill=0)
    for wx in [x + 1, x + 23]:
        draw.ellipse([(wx, y + 2), (wx + 5, y + 7)], fill=0)


def draw_lock(draw, x, y, closed=True):
    draw.rectangle([(x, y + 7), (x + 14, y + 18)], fill=0)
    draw.rectangle([(x + 1, y + 8), (x + 13, y + 17)], fill=1)
    draw.rectangle([(x + 5, y + 11), (x + 9, y + 15)], fill=0)
    # Shackle
    if closed:
        draw.arc([(x + 2, y), (x + 12, y + 9)], start=180, end=360, fill=0, width=2)
        draw.line([(x + 2, y + 4), (x + 2, y + 8)], fill=0, width=2)
        draw.line([(x + 12, y + 4), (x + 12, y + 8)], fill=0, width=2)
    else:
        draw.arc([(x + 2, y - 4), (x + 12, y + 5)], start=180, end=360, fill=0, width=2)
        draw.line([(x + 12, y + 0), (x + 12, y + 8)], fill=0, width=2)


def make_car_key():
    name = "L1_Car_Key_128x64"
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    FRAMES = 12

    for f in range(FRAMES):
        img = Image.new("1", (W, H), 1)
        draw = ImageDraw.Draw(img)

        # Ground
        draw.line([(0, 55), (W, 55)], fill=0)

        # Car on left
        draw_car(draw, 2, 34)

        # Signal waves
        for wave in range(4):
            radius = ((f * 6 + wave * 14) % 70)
            if radius < 8:
                continue
            cx, cy = 30, 43
            try:
                draw.arc([cx - radius, cy - radius // 3,
                          cx + radius, cy + radius // 3],
                         start=-55, end=55, fill=0, width=1)
            except Exception:
                pass

        # Lock on right — open until frame 8, then snapping shut
        closed = f >= 8
        draw_lock(draw, W - 22, 30, closed=closed)

        # Captured checkmark
        if f >= 10:
            cx = W - 35
            draw.line([(cx, 50), (cx + 4, 54)], fill=0, width=2)
            draw.line([(cx + 4, 54), (cx + 10, 44)], fill=0, width=2)

        save_frame(img, d, f)

    write_meta(d, passive_frames=FRAMES, frame_rate=6, duration=3600)
    return name


# ─────────────────────────────────────────────────────────────────────────────
# Animation 3: Binary Rain — matrix-style scrolling 0/1 columns
# ─────────────────────────────────────────────────────────────────────────────

def make_binary_rain():
    name = "L1_Binary_Rain_128x64"
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    FRAMES = 8
    COLS = 16
    COL_W = W // COLS   # 8 px
    CHAR_H = 8
    ROWS = H // CHAR_H  # 8 rows

    col_speeds = [1 + (c % 3) for c in range(COLS)]
    col_phases = [(c * 3) % FRAMES for c in range(COLS)]

    def draw_bit(draw, x, y, bit):
        # Tiny 3x5 "0" or "1" glyph inside 8x8 cell
        px, py = x + 2, y + 1
        if bit == 0:
            draw.rectangle([(px, py), (px + 3, py + 5)], fill=0)
            draw.rectangle([(px + 1, py + 1), (px + 2, py + 4)], fill=1)
        else:
            draw.rectangle([(px + 1, py), (px + 2, py + 5)], fill=0)
            draw.rectangle([(px, py + 1), (px + 1, py + 2)], fill=0)

    for f in range(FRAMES):
        img = Image.new("1", (W, H), 1)
        draw = ImageDraw.Draw(img)

        for col in range(COLS):
            speed = col_speeds[col]
            phase = col_phases[col]
            offset = ((f + phase) // speed) % ROWS
            head = offset

            for row in range(ROWS):
                bit = (col + row + offset) % 2
                x = col * COL_W
                y = row * CHAR_H
                if row == head:
                    # Bright head: inverted cell
                    draw.rectangle([(x, y), (x + COL_W - 1, y + CHAR_H - 1)], fill=0)
                    draw_bit(draw, x, y, 1 - bit)  # inverted glyph
                elif (row - head) % ROWS < ROWS // 2:
                    # Active trail
                    draw_bit(draw, x, y, bit)

        save_frame(img, d, f)

    write_meta(d, passive_frames=FRAMES, frame_rate=8, duration=3600)
    return name


# ─────────────────────────────────────────────────────────────────────────────
# Animation 4: Signal Idle — pulsing signal bars, "ARF-SHUKA" label
# ─────────────────────────────────────────────────────────────────────────────

def make_signal_idle():
    name = "L1_Signal_Idle_128x64"
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    FRAMES = 12

    for f in range(FRAMES):
        img = Image.new("1", (W, H), 1)
        draw = ImageDraw.Draw(img)

        # Ground
        draw.line([(0, H - 1), (W, H - 1)], fill=0)

        # Pulsing signal bars
        NUM_BARS = 7
        bw, gap = 11, 5
        total_w = NUM_BARS * (bw + gap) - gap
        sx = (W - total_w) // 2
        base_y = H - 4

        for b in range(NUM_BARS):
            bar_h = 8 + b * 7
            bx = sx + b * (bw + gap)
            draw.rectangle([(bx, base_y - bar_h), (bx + bw, base_y)], outline=0, fill=1)
            fill_frac = abs(math.sin((f / FRAMES * math.pi * 2) + b * 0.5))
            fill_h = int(bar_h * fill_frac)
            if fill_h > 1:
                draw.rectangle([(bx + 1, base_y - fill_h), (bx + bw - 1, base_y - 1)], fill=0)

        # Simple "A R F" pixel logo at top
        # Each letter is a 5×7 block
        letters = {
            'A': [(0,6),(1,5),(1,4),(1,3),(1,2),(1,1),(2,0),(3,0),(3,1),(3,2),(3,3),(3,4),(3,5),(3,6),(4,6),(2,3),(1,3)],
            'R': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,0),(2,0),(3,0),(3,1),(3,2),(2,3),(1,3),(2,4),(3,5),(3,6)],
            'F': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(1,0),(2,0),(3,0),(1,3),(2,3)],
            '-': [(1,3),(2,3),(3,3)],
            'S': [(3,0),(2,0),(1,0),(0,1),(0,2),(1,3),(2,3),(3,4),(3,5),(2,6),(1,6),(0,6)],
            'H': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(4,0),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6),(1,3),(2,3),(3,3)],
            'U': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(1,6),(2,6),(3,6),(4,5),(4,4),(4,3),(4,2),(4,1),(4,0)],
            'K': [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(3,0),(2,1),(1,2),(1,3),(2,4),(3,5),(4,6)],
        }
        label = "ARF-SHUKA"
        lx = (W - len(label) * 7) // 2
        ly = 2
        for ci, ch in enumerate(label):
            tx = lx + ci * 7
            if ch in letters:
                for px, py in letters[ch]:
                    draw.point((tx + px, ly + py), fill=0)

        save_frame(img, d, f)

    write_meta(d, passive_frames=FRAMES, frame_rate=5, duration=3600)
    return name


# ─────────────────────────────────────────────────────────────────────────────
# Manifest (ARF external format — replaces assets/dolphin/external/manifest.txt)
# ─────────────────────────────────────────────────────────────────────────────

def write_manifest(names):
    lines = [
        "Filetype: Flipper Animation Manifest",
        "Version: 1",
        "",
    ]
    for name in names:
        lines += [
            f"Name: {name}",
            "Min butthurt: 0",
            "Max butthurt: 18",
            "Min level: 1",
            "Max level: 30",
            "Weight: 3",
            "",
        ]
    with open(os.path.join(OUT, "manifest.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")


# ─────────────────────────────────────────────────────────────────────────────

os.makedirs(OUT, exist_ok=True)

print("Generating RF Sweep...")
n1 = make_rf_sweep()
print("Generating Car Key Capture...")
n2 = make_car_key()
print("Generating Binary Rain...")
n3 = make_binary_rain()
print("Generating Signal Idle...")
n4 = make_signal_idle()

write_manifest([n1, n2, n3, n4])

total = sum(
    len([f for f in os.listdir(os.path.join(OUT, n)) if f.endswith('.png')])
    for n in [n1, n2, n3, n4]
)
print(f"\nDone. {total} frames across 4 animations → {OUT}/")
print("manifest.txt will replace ARF's external dolphin manifest in the firmware.")
