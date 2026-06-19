#!/usr/bin/env python3
"""
Generate custom Flipper Zero SD-card dolphin animations for ARF-Shuka-Edition.
Output: animations/ directory with subdirectories per animation + manifest.txt

Usage: python3 generate_animations.py [output_dir]
Requires: Pillow  (pip install Pillow)
"""

import os, sys, math
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1] if len(sys.argv) > 1 else "animations"
W, H = 128, 64  # Flipper Zero screen


def save_frame(img, path):
    """Save a Pillow image as 1-bit PNG."""
    img.convert("1").save(path)


def write_meta(anim_dir, passive_frames, active_frames=0, frame_rate=4,
               duration=3600, active_cooldown=7, frames_order=None, bubbles=None):
    if frames_order is None:
        frames_order = list(range(passive_frames + active_frames))
    order_str = " ".join(str(x) for x in frames_order)
    lines = [
        "Filetype: Flipper Animation",
        "Version: 1",
        "",
        f"Width: {W}",
        f"Height: {H}",
        f"Passive frames: {passive_frames}",
        f"Active frames: {active_frames}",
        f"Frames order: {order_str}",
        f"Active cycles: {1 if active_frames else 0}",
        f"Frame rate: {frame_rate}",
        f"Duration: {duration}",
        f"Active cooldown: {active_cooldown}",
        "",
        f"Bubble slots: {len(bubbles) if bubbles else 0}",
    ]
    if bubbles:
        for b in bubbles:
            lines += [
                "",
                f"Slot: {b['slot']}",
                f"X: {b['x']}",
                f"Y: {b['y']}",
                f"Text: {b['text']}",
                f"Align H: {b.get('align_h', 'Left')}",
                f"Align V: {b.get('align_v', 'Bottom')}",
                f"StartFrame: {b['start']}",
                f"EndFrame: {b['end']}",
            ]
    with open(os.path.join(anim_dir, "meta.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Animation 1: RF Signal Sweep
# A radio tower on the left emitting expanding arcs across the screen.
# ─────────────────────────────────────────────────────────────────────────────

def make_rf_sweep():
    name = "L1_RF_Sweep"
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    FRAMES = 8
    TOWER_X, TOWER_Y = 12, 54   # base of tower
    ARC_STEP = 16               # pixels each arc expands per frame

    for f in range(FRAMES):
        img = Image.new("1", (W, H), 1)  # white background
        draw = ImageDraw.Draw(img)

        # Draw antenna tower (simple lines)
        draw.line([(TOWER_X, TOWER_Y), (TOWER_X, TOWER_Y - 20)], fill=0, width=1)
        draw.line([(TOWER_X - 5, TOWER_Y), (TOWER_X + 5, TOWER_Y)], fill=0)
        draw.line([(TOWER_X - 3, TOWER_Y - 7), (TOWER_X + 3, TOWER_Y - 7)], fill=0)
        # Tip blink
        if f % 2 == 0:
            draw.ellipse([(TOWER_X - 1, TOWER_Y - 22), (TOWER_X + 1, TOWER_Y - 20)], fill=0)

        # Draw 3 expanding arcs, each offset by frame index
        for arc_idx in range(3):
            radius = ((f + arc_idx * 3) % FRAMES) * ARC_STEP // 2 + 5
            alpha = 1 - (radius / (W * 0.9))   # fade out as arc expands
            if alpha < 0.15:
                continue
            # Draw arc as a partial ellipse from tower tip
            cx, cy = TOWER_X, TOWER_Y - 20
            bbox = [cx - radius, cy - radius // 2,
                    cx + radius, cy + radius // 2]
            # Draw right-facing arc (angles -60 to +60 degrees)
            try:
                draw.arc(bbox, start=-70, end=70, fill=0, width=1)
            except Exception:
                pass

        # Signal dots drifting right
        for dot_i in range(5):
            dx = TOWER_X + 20 + dot_i * 22 + (f * 3) % 22
            dy = TOWER_Y - 20 + int(math.sin((f + dot_i) * 0.8) * 6)
            if dx < W - 2:
                draw.rectangle([(dx, dy), (dx + 1, dy + 1)], fill=0)

        # Corner text
        for xi, ch in enumerate("ARF"):
            draw.rectangle([(W - 22 + xi * 7, 2), (W - 17 + xi * 7, 8)], fill=0)

        save_frame(img, os.path.join(d, f"frame_{f}.png"))

    write_meta(d, passive_frames=FRAMES, frame_rate=6, duration=3600,
               bubbles=[{"slot": 0, "x": 40, "y": 10, "text": "Scanning...",
                         "start": 0, "end": FRAMES - 1}])
    return name


# ─────────────────────────────────────────────────────────────────────────────
# Animation 2: Car Key Capture
# A car on left, signal bursts, lock icon appears on right.
# ─────────────────────────────────────────────────────────────────────────────

def draw_car(draw, x, y):
    """Draw a simple top-down car icon at (x,y)."""
    # Body
    draw.rectangle([(x, y + 4), (x + 22, y + 14)], fill=0)
    # Roof
    draw.rectangle([(x + 4, y), (x + 18, y + 5)], fill=0)
    # Windows (white cutouts)
    draw.rectangle([(x + 5, y + 1), (x + 10, y + 4)], fill=1)
    draw.rectangle([(x + 12, y + 1), (x + 17, y + 4)], fill=1)
    # Wheels
    draw.ellipse([(x, y + 12), (x + 4, y + 16)], fill=0)
    draw.ellipse([(x + 18, y + 12), (x + 22, y + 16)], fill=0)
    draw.ellipse([(x, y + 3), (x + 4, y + 7)], fill=0)
    draw.ellipse([(x + 18, y + 3), (x + 22, y + 7)], fill=0)


def draw_lock(draw, x, y, open_lock=False):
    """Draw a padlock at (x,y)."""
    # Body
    draw.rectangle([(x, y + 6), (x + 12, y + 16)], fill=0)
    draw.rectangle([(x + 1, y + 7), (x + 11, y + 15)], fill=1)
    # Center dot
    draw.rectangle([(x + 5, y + 10), (x + 7, y + 13)], fill=0)
    # Shackle
    if open_lock:
        draw.arc([(x + 2, y), (x + 10, y + 8)], start=180, end=360, fill=0, width=2)
        draw.line([(x + 10, y + 4), (x + 10, y + 7)], fill=0, width=2)
    else:
        draw.arc([(x + 2, y), (x + 10, y + 8)], start=180, end=360, fill=0, width=2)
        draw.line([(x + 2, y + 4), (x + 2, y + 7)], fill=0, width=2)
        draw.line([(x + 10, y + 4), (x + 10, y + 7)], fill=0, width=2)


def make_car_key():
    name = "L1_Car_Key"
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    FRAMES = 10

    for f in range(FRAMES):
        img = Image.new("1", (W, H), 1)
        draw = ImageDraw.Draw(img)

        # Car on left side
        draw_car(draw, 4, 24)

        # Signal bursts from car
        for wave in range(3):
            radius = (f * 5 + wave * 15) % 60
            if radius < 4:
                continue
            cx, cy = 26, 32
            # Right-facing arcs
            try:
                draw.arc([cx - radius, cy - radius // 2,
                          cx + radius, cy + radius // 2],
                         start=-60, end=60, fill=0, width=1)
            except Exception:
                pass

        # Lock icon on right — open if first half, closing then locked
        lock_x = W - 20
        if f < FRAMES // 3:
            draw_lock(draw, lock_x, 24, open_lock=True)
        elif f < 2 * FRAMES // 3:
            draw_lock(draw, lock_x, 24, open_lock=True)
        else:
            draw_lock(draw, lock_x, 24, open_lock=False)
            # "Captured" check mark
            if f >= FRAMES - 2:
                draw.line([(lock_x - 8, 44), (lock_x - 5, 48)], fill=0, width=2)
                draw.line([(lock_x - 5, 48), (lock_x - 1, 40)], fill=0, width=2)

        # Bottom label dots (progress)
        for pi in range(f + 1):
            px = W // 2 - (FRAMES // 2) * 5 + pi * 5 + 2
            draw.rectangle([(px, H - 5), (px + 2, H - 3)], fill=0)

        save_frame(img, os.path.join(d, f"frame_{f}.png"))

    write_meta(d, passive_frames=FRAMES, frame_rate=5, duration=3600,
               bubbles=[{"slot": 0, "x": 42, "y": 8, "text": "RKE Capture",
                         "start": 0, "end": FRAMES - 1}])
    return name


# ─────────────────────────────────────────────────────────────────────────────
# Animation 3: Binary Rain (Matrix-style)
# Columns of falling 0/1 characters, different scroll speeds per column.
# ─────────────────────────────────────────────────────────────────────────────

def make_binary_rain():
    name = "L1_Binary_Rain"
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    FRAMES = 8
    COLS = 16       # number of character columns
    COL_W = W // COLS   # 8 px per column
    CHAR_H = 8
    ROWS = H // CHAR_H  # 8 rows

    # Each column has a speed (frames per step) and phase offset
    col_speeds = [1 + (c % 3) for c in range(COLS)]
    col_phases = [(c * 3) % FRAMES for c in range(COLS)]

    for f in range(FRAMES):
        img = Image.new("1", (W, H), 1)
        draw = ImageDraw.Draw(img)

        for col in range(COLS):
            speed = col_speeds[col]
            phase = col_phases[col]
            row_offset = ((f + phase) // speed) % ROWS

            for row in range(ROWS):
                # Checkerboard of 0/1 that scrolls
                bit = (col + row + row_offset) % 2
                x = col * COL_W
                y = row * CHAR_H
                # Draw a simple 0 or 1 as a tiny pixel pattern (4x6 within the 8x8 cell)
                px, py = x + 2, y + 1
                if bit == 0:
                    # Draw "0": rectangle with hollow center
                    draw.rectangle([(px, py), (px + 3, py + 5)], fill=0)
                    draw.rectangle([(px + 1, py + 1), (px + 2, py + 4)], fill=1)
                else:
                    # Draw "1": just a vertical line
                    draw.rectangle([(px + 1, py), (px + 2, py + 5)], fill=0)
                    draw.rectangle([(px, py + 1), (px + 1, py + 2)], fill=0)

        # Bright "head" of each column (inverted cell = black box, white char)
        for col in range(COLS):
            speed = col_speeds[col]
            phase = col_phases[col]
            head_row = ((f + phase) // speed) % ROWS
            x = col * COL_W
            y = head_row * CHAR_H
            draw.rectangle([(x, y), (x + COL_W - 1, y + CHAR_H - 1)], fill=0)

        save_frame(img, os.path.join(d, f"frame_{f}.png"))

    write_meta(d, passive_frames=FRAMES, frame_rate=8, duration=3600)
    return name


# ─────────────────────────────────────────────────────────────────────────────
# Animation 4: Idle — simple pulsing signal bars (like phone signal strength)
# ─────────────────────────────────────────────────────────────────────────────

def make_signal_idle():
    name = "L1_Signal_Idle"
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    FRAMES = 12

    for f in range(FRAMES):
        img = Image.new("1", (W, H), 1)
        draw = ImageDraw.Draw(img)

        # Draw signal bars like a phone — 5 bars, animated fill
        cx = W // 2
        NUM_BARS = 7
        bar_w = 10
        gap = 4
        total_w = NUM_BARS * (bar_w + gap) - gap
        start_x = cx - total_w // 2

        for b in range(NUM_BARS):
            bar_h = 8 + b * 6
            bx = start_x + b * (bar_w + gap)
            by = H // 2 + 10
            # Outline always
            draw.rectangle([(bx, by - bar_h), (bx + bar_w, by)], outline=0, fill=1)
            # Fill with animated wave
            fill_level = abs(math.sin((f / FRAMES * math.pi * 2) + b * 0.6))
            fill_h = int(bar_h * fill_level)
            if fill_h > 0:
                draw.rectangle([(bx, by - fill_h), (bx + bar_w, by)], fill=0)

        # Title text as pixel art
        label = "ARF-SHUKA"
        char_w = 5
        lx = cx - len(label) * (char_w + 1) // 2
        for ci, ch in enumerate(label):
            tx = lx + ci * (char_w + 1)
            # Simple blocky render: draw a solid rect per char, then "draw" inside
            if ch != " ":
                draw.rectangle([(tx, 4), (tx + char_w - 1, 12)], fill=0)

        save_frame(img, os.path.join(d, f"frame_{f}.png"))

    write_meta(d, passive_frames=FRAMES, frame_rate=6, duration=3600,
               bubbles=[{"slot": 0, "x": 10, "y": 54,
                         "text": "ARF Shuka Edition", "start": 0, "end": FRAMES - 1}])
    return name


# ─────────────────────────────────────────────────────────────────────────────
# Manifest
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

print(f"\nDone. Animations written to: {OUT}/")
print("Copy the contents of this folder to /ext/dolphin/ on your Flipper SD card.")
print(f"  {n1}  — RF antenna sweeping signal arcs")
print(f"  {n2}  — Car emitting RKE, lock captured")
print(f"  {n3}  — Matrix-style binary rain")
print(f"  {n4}  — Pulsing signal bars")
