#!/usr/bin/env python3
"""
Generate 64x64 1-bit pixel-art icons for the SubGHz reading screen.

When called with a single .png path, generates only Heisenberg (backward compat).
When called with a directory path, generates all three band icons:
  - Heisenberg_64x64.png     (433 MHz — Breaking Bad icon)
  - SubGhz315_64x64.png      (315 MHz — car key fob)
  - SubGhz868_64x64.png      (868 MHz — signal tower)

Usage:
  python3 generate_heisenberg.py <output.png>
  python3 generate_heisenberg.py <icons_dir/>
"""

import sys, os
from PIL import Image, ImageDraw

W, H = 64, 64


def blk(d, x0, y0, x1, y1): d.rectangle([x0, y0, x1, y1], fill=0)
def wht(d, x0, y0, x1, y1): d.rectangle([x0, y0, x1, y1], fill=1)
def oval(d, x0, y0, x1, y1, f=0): d.ellipse([x0, y0, x1, y1], fill=f)
def tri(d, pts, f=0): d.polygon(pts, fill=f)
def dot(d, x, y): d.point((x, y), fill=0)
def wdot(d, x, y): d.point((x, y), fill=1)
def arc(d, x0, y0, x1, y1, s, e): d.arc([x0, y0, x1, y1], start=s, end=e, fill=0, width=2)


def make_heisenberg():
    """Walter White — Heisenberg. 433 MHz."""
    img = Image.new("1", (W, H), 1)
    d = ImageDraw.Draw(img)

    # HAT
    blk(d, 13, 3, 50, 18)
    for i in range(4):
        wht(d, 13, 3+i, 13+4-i, 3+i)
        wht(d, 50-3+i, 3, 50, 3+3-i)
    blk(d, 17, 3, 46, 4)
    blk(d, 13, 14, 50, 18)
    wht(d, 14, 15, 49, 16)
    blk(d, 4, 18, 59, 23)
    for x in range(5, 59):
        dot(d, x, 23)

    # HEAD / FACE
    oval(d, 11, 20, 52, 55)
    oval(d, 12, 21, 51, 54, f=1)
    oval(d, 9, 30, 13, 38)
    oval(d, 51, 30, 55, 38)
    oval(d, 10, 31, 12, 37, f=1)
    oval(d, 52, 31, 54, 37, f=1)

    # EYEBROWS
    blk(d, 16, 25, 27, 27)
    blk(d, 36, 25, 47, 27)
    dot(d, 27, 26); dot(d, 28, 27); dot(d, 35, 27); dot(d, 36, 26)

    # SUNGLASSES
    blk(d, 15, 28, 28, 37)
    wht(d, 17, 30, 26, 35)
    dot(d, 18, 30); dot(d, 19, 30); dot(d, 18, 31)
    blk(d, 35, 28, 48, 37)
    wht(d, 37, 30, 46, 35)
    dot(d, 38, 30); dot(d, 39, 30); dot(d, 38, 31)
    blk(d, 28, 31, 35, 34)
    d.line([15, 33, 10, 33], fill=0, width=2)
    d.line([48, 33, 53, 33], fill=0, width=2)

    # NOSE
    d.line([28, 37, 26, 42], fill=0, width=1)
    d.line([35, 37, 37, 42], fill=0, width=1)
    blk(d, 27, 42, 36, 43)
    wht(d, 29, 42, 34, 43)

    # MOUTH + GOATEE
    blk(d, 25, 44, 38, 45)
    wht(d, 27, 44, 36, 44)
    dot(d, 25, 45); dot(d, 38, 45)
    oval(d, 20, 46, 43, 59)
    tri(d, [(27, 58), (36, 58), (31, 63)], f=0)
    blk(d, 28, 46, 35, 48)

    # NECK
    blk(d, 27, 53, 36, 58)

    # JACKET
    blk(d, 0, 57, 63, 63)
    blk(d, 0,  55, 24, 63)
    blk(d, 39, 55, 63, 63)
    tri(d, [(0,55),(21,55),(27,61),(0,63)], f=0)
    tri(d, [(63,55),(42,55),(36,61),(63,63)], f=0)
    wht(d, 27, 56, 36, 63)
    blk(d, 30, 56, 33, 63)
    blk(d, 29, 56, 34, 59)
    tri(d, [(21,55),(27,55),(27,60)], f=1)
    tri(d, [(42,55),(36,55),(36,60)], f=1)

    for x in range(24, 40, 2):
        dot(d, x, 43)
    wdot(d, 20, 31); wdot(d, 21, 31)
    wdot(d, 40, 31); wdot(d, 41, 31)
    dot(d, 31, 61)

    return img


def make_keyfob():
    """Car key fob silhouette. 315 MHz — North American RKE band."""
    img = Image.new("1", (W, H), 1)
    d = ImageDraw.Draw(img)

    # Signal arcs above fob (3 arcs, small to large)
    arc(d, 26, 2, 38, 14,  210, 330)
    arc(d, 22, 0, 42, 20,  210, 330)
    arc(d, 18, -4, 46, 24, 210, 330)

    # Fob body — rounded rectangle
    blk(d, 20, 18, 44, 54)
    # Round the corners
    wht(d, 20, 18, 22, 20)
    wht(d, 42, 18, 44, 20)
    wht(d, 20, 52, 22, 54)
    wht(d, 42, 52, 44, 54)
    oval(d, 20, 18, 24, 22, f=0)
    oval(d, 40, 18, 44, 22, f=0)
    oval(d, 20, 50, 24, 54, f=0)
    oval(d, 40, 50, 44, 54, f=0)
    # Fob body interior (white fill inside rounded rect)
    wht(d, 21, 19, 43, 53)
    blk(d, 22, 20, 42, 52)
    wht(d, 23, 21, 41, 51)

    # Lock button (padlock icon-ish, top button)
    blk(d, 26, 23, 38, 29)
    wht(d, 27, 24, 37, 28)
    dot(d, 32, 26)  # lock keyhole
    oval(d, 29, 22, 35, 26, f=0)  # shackle arc
    wht(d, 30, 24, 34, 26)        # shackle fill

    # Unlock button (open lock, middle)
    blk(d, 26, 31, 38, 37)
    wht(d, 27, 32, 37, 36)
    # Open shackle (angled to right)
    d.line([29, 32, 29, 29], fill=0, width=1)
    d.line([29, 29, 33, 29], fill=0, width=1)
    dot(d, 32, 33)

    # Trunk button (hatch, bottom)
    blk(d, 26, 39, 38, 45)
    wht(d, 27, 40, 37, 44)
    # Simple car top silhouette (hatch shape)
    tri(d, [(29, 43), (35, 43), (35, 41), (32, 40), (29, 41)], f=0)

    # Key blade at bottom
    blk(d, 30, 55, 34, 62)
    # Key teeth (extending left from blade)
    blk(d, 26, 57, 30, 58)
    blk(d, 25, 59, 30, 60)
    blk(d, 27, 61, 30, 62)
    # Key bow (ring)
    oval(d, 27, 51, 37, 57)
    wht(d, 29, 53, 35, 56)
    dot(d, 32, 54)

    return img


def make_tower():
    """Signal tower / LoRa icon. 868 MHz — EU IoT band."""
    img = Image.new("1", (W, H), 1)
    d = ImageDraw.Draw(img)

    # Signal arcs emanating from tower top (3 pairs, left+right)
    # Small
    arc(d, 27, 4, 37, 14, 200, 340)
    # Medium
    arc(d, 22, 1, 42, 21, 200, 340)
    # Large
    arc(d, 17, -2, 47, 28, 200, 340)

    # Tower shaft (narrow, centered)
    blk(d, 30, 14, 34, 52)

    # Cross arm / beam at top of shaft
    blk(d, 24, 22, 40, 24)
    # Cross arm lower
    blk(d, 26, 30, 38, 32)

    # Diagonal legs spreading to base
    d.line([30, 52, 14, 63], fill=0, width=2)
    d.line([34, 52, 50, 63], fill=0, width=2)

    # Diagonal braces (X pattern)
    d.line([24, 22, 14, 63], fill=0, width=1)
    d.line([40, 22, 50, 63], fill=0, width=1)

    # Base platform
    blk(d, 10, 61, 54, 63)
    # Base feet
    blk(d, 10, 59, 16, 61)
    blk(d, 48, 59, 54, 61)

    # Antenna tip above arcs
    blk(d, 31, 0, 33, 5)
    # Antenna ball
    oval(d, 29, 1, 35, 7)
    wht(d, 30, 2, 34, 6)
    dot(d, 32, 4)

    # Guy wires (thin lines from cross arm to ground)
    d.line([24, 24, 18, 52], fill=0, width=1)
    d.line([40, 24, 46, 52], fill=0, width=1)

    return img


def save(img, path):
    img.save(path)
    print(f"Written → {path}  ({W}×{H} 1-bit)")


arg = sys.argv[1] if len(sys.argv) > 1 else "Heisenberg_64x64.png"

if os.path.isdir(arg) or (not arg.endswith(".png")):
    # Directory mode: generate all 3 band icons
    out_dir = arg
    save(make_heisenberg(), os.path.join(out_dir, "Heisenberg_64x64.png"))
    save(make_keyfob(),     os.path.join(out_dir, "SubGhz315_64x64.png"))
    save(make_tower(),      os.path.join(out_dir, "SubGhz868_64x64.png"))
else:
    # Single-file mode (backward compat): generate only Heisenberg
    save(make_heisenberg(), arg)
