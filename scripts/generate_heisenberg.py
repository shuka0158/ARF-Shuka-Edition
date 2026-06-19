#!/usr/bin/env python3
"""
Generate a 64x64 pixel-art Heisenberg (Walter White) for the
Flipper Zero SubGHz reading screen.

Output: 1-bit PNG ready for Flipper's fbt asset compiler.
Usage: python3 generate_heisenberg.py <output.png>
"""

import sys
from PIL import Image, ImageDraw

W, H = 64, 64
OUT = sys.argv[1] if len(sys.argv) > 1 else "Heisenberg_64x64.png"

# 1-bit image: 0 = black (ink), 1 = white (background)
img = Image.new("1", (W, H), 1)
d   = ImageDraw.Draw(img)

def blk(x0, y0, x1, y1):          d.rectangle([x0, y0, x1, y1], fill=0)
def wht(x0, y0, x1, y1):          d.rectangle([x0, y0, x1, y1], fill=1)
def oval(x0, y0, x1, y1, f=0):    d.ellipse([x0, y0, x1, y1], fill=f)
def tri(pts, f=0):                 d.polygon(pts, fill=f)
def dot(x, y):                     d.point((x, y), fill=0)
def wdot(x, y):                    d.point((x, y), fill=1)

# ─────────────────────────────────────────────────────────────
# HAT  (porkpie: flat crown, wide snap brim)
# ─────────────────────────────────────────────────────────────
# Crown body
blk(13, 3, 50, 18)
# Round crown top corners
for i in range(4):
    wht(13, 3+i, 13+4-i, 3+i)
    wht(50-3+i, 3, 50, 3+3-i)
# Flat crown top (re-draw after rounding)
blk(17, 3, 46, 4)
# Hat band (lighter stripe)
blk(13, 14, 50, 18)
wht(14, 15, 49, 16)          # band highlight (2 white lines)
# Brim (wide, extends past crown)
blk(4, 18, 59, 23)
# Brim shadow under  (subtle)
for x in range(5, 59):
    dot(x, 23)

# ─────────────────────────────────────────────────────────────
# HEAD / FACE
# ─────────────────────────────────────────────────────────────
oval(11, 20, 52, 55)        # head outline
oval(12, 21, 51, 54, f=1)   # face fill (white)

# Ears (small bumps on sides of head)
oval(9,  30, 13, 38)
oval(51, 30, 55, 38)
oval(10, 31, 12, 37, f=1)   # inner ear
oval(52, 31, 54, 37, f=1)

# ─────────────────────────────────────────────────────────────
# EYEBROWS  (thick, slightly furrowed)
# ─────────────────────────────────────────────────────────────
blk(16, 25, 27, 27)
blk(36, 25, 47, 27)
# Inner frown crease
dot(27, 26); dot(28, 27); dot(35, 27); dot(36, 26)

# ─────────────────────────────────────────────────────────────
# SUNGLASSES  (thick square frames, classic Breaking Bad look)
# ─────────────────────────────────────────────────────────────
# Left lens frame + fill
blk(15, 28, 28, 37)
wht(17, 30, 26, 35)         # lens interior (white = see-through effect)
# Lens reflection (white dot on black frame = shine)
dot(18, 30); dot(19, 30); dot(18, 31)   # re-draw dark corner
# Right lens
blk(35, 28, 48, 37)
wht(37, 30, 46, 35)
dot(38, 30); dot(39, 30); dot(38, 31)
# Bridge between lenses
blk(28, 31, 35, 34)
# Temples (arms going to ears)
d.line([15, 33, 10, 33], fill=0, width=2)
d.line([48, 33, 53, 33], fill=0, width=2)

# ─────────────────────────────────────────────────────────────
# NOSE  (angular, prominent)
# ─────────────────────────────────────────────────────────────
d.line([28, 37, 26, 42], fill=0, width=1)   # left nostril wing
d.line([35, 37, 37, 42], fill=0, width=1)   # right nostril wing
blk(27, 42, 36, 43)                          # nose base
wht(29, 42, 34, 43)                          # philtrum gap

# ─────────────────────────────────────────────────────────────
# MOUTH + GOATEE  (thin upper lip, full chin beard)
# ─────────────────────────────────────────────────────────────
# Upper lip / serious thin line
blk(25, 44, 38, 45)
wht(27, 44, 36, 44)                          # cupid's bow gap
dot(25, 45); dot(38, 45)                     # lip corners

# Goatee (full chin beard – oval with solid fill)
oval(20, 46, 43, 59)
# Chin point (triangle below oval)
tri([(27, 58), (36, 58), (31, 63)], f=0)
# Soul patch (small dark patch above lip)
blk(28, 46, 35, 48)

# ─────────────────────────────────────────────────────────────
# NECK
# ─────────────────────────────────────────────────────────────
blk(27, 53, 36, 58)

# ─────────────────────────────────────────────────────────────
# JACKET / COAT  (dark, authoritative)
# ─────────────────────────────────────────────────────────────
# Full jacket body at bottom
blk(0, 57, 63, 63)
# Broad shoulders
blk(0,  55, 24, 63)
blk(39, 55, 63, 63)

# Left lapel
tri([(0,55),(21,55),(27,61),(0,63)], f=0)
# Right lapel
tri([(63,55),(42,55),(36,61),(63,63)], f=0)

# White shirt (between lapels)
wht(27, 56, 36, 63)
# Tie (narrow, dark)
blk(30, 56, 33, 63)
# Tie knot (slightly wider at top)
blk(29, 56, 34, 59)

# Collar points (shirt)
tri([(21,55),(27,55),(27,60)], f=1)
tri([(42,55),(36,55),(36,60)], f=1)

# ─────────────────────────────────────────────────────────────
# FINISHING TOUCHES
# ─────────────────────────────────────────────────────────────
# Stubble / texture on lower face (below sunglasses, above goatee)
for x in range(24, 40, 2):
    dot(x, 43)

# Lens glare dots (small white reflections inside dark lenses)
wdot(20, 31); wdot(21, 31)    # left lens glare
wdot(40, 31); wdot(41, 31)    # right lens glare

# Jacket button (center chest)
dot(31, 61)

img.save(OUT)
print(f"Heisenberg saved → {OUT}  ({W}×{H} 1-bit)")
