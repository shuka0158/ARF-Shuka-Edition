#!/usr/bin/env python3
"""
Generate 3 custom passport character sets (46x49 1-bit PNGs) for ARF-Shuka-Edition.
Each set has 3 mood variants: happy, okay, bad.

Characters:
  skull  - a skull with moods (grin / neutral / sad)
  hacker - hooded figure with moods
  robot  - robot face with moods

Usage: python3 generate_passport_chars.py <output_dir>
Output files follow Flipper naming: passport_<mood><N>_46x49.png
but prefixed with char name: skull_happy1_46x49.png etc.
"""

import sys, os
from PIL import Image, ImageDraw

W, H = 46, 49
OUT = sys.argv[1] if len(sys.argv) > 1 else "."

os.makedirs(OUT, exist_ok=True)

def new():
    img = Image.new("1", (W, H), 1)
    return img, ImageDraw.Draw(img)

def blk(d, x0,y0,x1,y1):  d.rectangle([x0,y0,x1,y1], fill=0)
def wht(d, x0,y0,x1,y1):  d.rectangle([x0,y0,x1,y1], fill=1)
def oval(d, x0,y0,x1,y1, f=0): d.ellipse([x0,y0,x1,y1], fill=f)
def tri(d, pts, f=0):      d.polygon(pts, fill=f)
def line(d, x0,y0,x1,y1): d.line([x0,y0,x1,y1], fill=0, width=1)

# ─────────────────────────────────────────────────────────────────────────────
# SKULL  (3 variants)
# ─────────────────────────────────────────────────────────────────────────────
def draw_skull_base(d, eye_l, eye_r, nose_open=True):
    # Cranium
    oval(d, 5, 0, 40, 30)
    # Jaw
    blk(d, 10, 25, 35, 38)
    wht(d, 11, 26, 34, 34)   # jaw white interior
    # Cheekbones
    oval(d, 5, 20, 18, 35)
    oval(d, 27, 20, 40, 35)
    wht(d, 6, 21, 17, 30)
    wht(d, 28, 21, 39, 30)
    # Eyes (black sockets)
    oval(d, 10, 7, 21, 18)
    oval(d, 24, 7, 35, 18)
    # Pupils (white dots in sockets)
    oval(d, *eye_l, f=1)
    oval(d, *eye_r, f=1)
    # Nose cavity
    if nose_open:
        blk(d, 19, 20, 26, 26)
        wht(d, 20, 21, 25, 25)
    else:
        oval(d, 19, 20, 26, 26)
        wht(d, 20, 21, 25, 25)

def draw_skull_teeth(d, teeth):
    # teeth = list of (x, w) for each tooth
    for x, w in teeth:
        blk(d, x, 34, x+w, 40)
        wht(d, x+1, 35, x+w-1, 39)

def skull_happy():
    img, d = new()
    draw_skull_base(d, (12,9,19,16), (25,9,33,16))
    draw_skull_teeth(d, [(11,5),(17,5),(23,5),(29,5)])
    # Grin arc
    blk(d, 10, 30, 35, 34)
    wht(d, 11, 28, 34, 33)
    d.arc([10,28,35,36], start=0, end=180, fill=0)
    return img

def skull_okay():
    img, d = new()
    draw_skull_base(d, (12,10,19,16), (25,10,33,16))
    draw_skull_teeth(d, [(13,4),(19,4),(25,4),(31,4)])
    # Straight mouth
    blk(d, 11, 31, 34, 33)
    return img

def skull_bad():
    img, d = new()
    draw_skull_base(d, (12,12,19,17), (25,12,33,17))
    draw_skull_teeth(d, [(13,4),(19,4),(25,4),(31,4)])
    # Frown arc
    d.arc([10,30,35,40], start=180, end=360, fill=0)
    # X eyes overlay
    line(d, 11,8,20,17)
    line(d, 20,8,11,17)
    line(d, 25,8,34,17)
    line(d, 34,8,25,17)
    return img

# ─────────────────────────────────────────────────────────────────────────────
# HACKER  (hooded figure with terminal screen)
# ─────────────────────────────────────────────────────────────────────────────
def hacker_happy():
    img, d = new()
    # Hood
    tri(d, [(5,20),(22,2),(40,20),(38,48),(7,48)])
    wht(d, 9,22,37,46)
    # Face oval
    oval(d, 11,18,34,38)
    wht(d, 12,19,33,37)
    # Mask/visor (dark horizontal band)
    blk(d, 11,22,34,30)
    # Terminal lines inside visor
    wht(d, 13,24,20,25)
    wht(d, 22,24,32,25)
    wht(d, 13,27,28,28)
    # Smile below mask
    d.arc([16,31,30,39], start=0, end=180, fill=0)
    # Glowing eyes in visor
    oval(d, 14,23,19,28, f=1)
    oval(d, 26,23,31,28, f=1)
    # Shoulders
    blk(d, 0,42,45,48)
    wht(d, 1,43,44,47)
    blk(d, 0,44,10,48)
    blk(d, 35,44,45,48)
    return img

def hacker_okay():
    img, d = new()
    tri(d, [(5,20),(22,2),(40,20),(38,48),(7,48)])
    wht(d, 9,22,37,46)
    oval(d, 11,18,34,38)
    wht(d, 12,19,33,37)
    blk(d, 11,22,34,30)
    wht(d, 13,24,20,25)
    wht(d, 22,24,32,25)
    wht(d, 13,27,28,28)
    # Neutral mouth
    blk(d, 16,33,30,34)
    oval(d, 14,23,19,28, f=1)
    oval(d, 26,23,31,28, f=1)
    blk(d, 0,42,45,48)
    wht(d, 1,43,44,47)
    blk(d, 0,44,10,48)
    blk(d, 35,44,45,48)
    return img

def hacker_bad():
    img, d = new()
    tri(d, [(5,20),(22,2),(40,20),(38,48),(7,48)])
    wht(d, 9,22,37,46)
    oval(d, 11,18,34,38)
    wht(d, 12,19,33,37)
    blk(d, 11,22,34,30)
    # Error lines in visor
    wht(d, 13,24,20,25)
    wht(d, 13,27,20,28)
    blk(d, 22,25,32,27)  # "ERR" block
    wht(d, 23,26,31,26)
    # Frown
    d.arc([16,32,30,40], start=180, end=360, fill=0)
    # Red-X eyes
    line(d, 14,23,19,28)
    line(d, 19,23,14,28)
    line(d, 26,23,31,28)
    line(d, 31,23,26,28)
    blk(d, 0,42,45,48)
    wht(d, 1,43,44,47)
    blk(d, 0,44,10,48)
    blk(d, 35,44,45,48)
    return img

# ─────────────────────────────────────────────────────────────────────────────
# ROBOT  (retro robot head)
# ─────────────────────────────────────────────────────────────────────────────
def robot_happy():
    img, d = new()
    # Antenna
    blk(d, 21,0,24,5)
    oval(d, 19,3,26,9)
    wht(d, 20,4,25,8)
    blk(d, 22,4,23,7)
    # Head box
    blk(d, 5,8,40,40)
    wht(d, 6,9,39,39)
    # Eyes (square LCD style)
    blk(d, 9,14,17,22)
    blk(d, 28,14,36,22)
    wht(d, 10,15,16,21)
    wht(d, 29,15,35,21)
    # Pupils
    blk(d, 12,17,14,19)
    blk(d, 31,17,33,19)
    # Mouth (happy display)
    blk(d, 9,28,36,36)
    wht(d, 10,29,35,35)
    # Happy pixelated smile
    for x in range(11,35,2): blk(d, x,33,x+1,34)
    for x,y in [(11,32),(12,31),(19,30),(20,30),(21,30),(22,30),(23,31),(24,32)]:
        blk(d, x,y,x+1,y+1)
    # Ear bolts
    blk(d, 2,20,6,26)
    blk(d, 39,20,43,26)
    wht(d, 3,21,5,25)
    wht(d, 40,21,42,25)
    # Neck
    blk(d, 16,39,29,44)
    # Body hint
    blk(d, 8,43,37,48)
    wht(d, 9,44,36,47)
    return img

def robot_okay():
    img, d = new()
    blk(d, 21,0,24,5)
    oval(d, 19,3,26,9)
    wht(d, 20,4,25,8)
    blk(d, 22,4,23,7)
    blk(d, 5,8,40,40)
    wht(d, 6,9,39,39)
    blk(d, 9,14,17,22)
    blk(d, 28,14,36,22)
    wht(d, 10,15,16,21)
    wht(d, 29,15,35,21)
    blk(d, 12,17,14,19)
    blk(d, 31,17,33,19)
    # Neutral mouth display
    blk(d, 9,28,36,36)
    wht(d, 10,29,35,35)
    blk(d, 11,31,34,33)
    blk(d, 2,20,6,26)
    blk(d, 39,20,43,26)
    wht(d, 3,21,5,25)
    wht(d, 40,21,42,25)
    blk(d, 16,39,29,44)
    blk(d, 8,43,37,48)
    wht(d, 9,44,36,47)
    return img

def robot_bad():
    img, d = new()
    blk(d, 21,0,24,5)
    oval(d, 19,3,26,9)
    wht(d, 20,4,25,8)
    blk(d, 22,4,23,7)
    blk(d, 5,8,40,40)
    wht(d, 6,9,39,39)
    # X eyes
    blk(d, 9,14,17,22)
    blk(d, 28,14,36,22)
    wht(d, 10,15,16,21)
    wht(d, 29,15,35,21)
    line(d, 10,15,16,21)
    line(d, 16,15,10,21)
    line(d, 29,15,35,21)
    line(d, 35,15,29,21)
    # Sad mouth display
    blk(d, 9,28,36,36)
    wht(d, 10,29,35,35)
    blk(d, 11,33,34,35)   # frown line at bottom
    for x in range(12,35,3): blk(d, x,31,x+1,32)  # dotted sad
    blk(d, 2,20,6,26)
    blk(d, 39,20,43,26)
    wht(d, 3,21,5,25)
    wht(d, 40,21,42,25)
    blk(d, 16,39,29,44)
    blk(d, 8,43,37,48)
    wht(d, 9,44,36,47)
    return img

# ─────────────────────────────────────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────────────────────────────────────
sets = {
    "skull":  [("happy", skull_happy), ("okay", skull_okay), ("bad", skull_bad)],
    "hacker": [("happy", hacker_happy), ("okay", hacker_okay), ("bad", hacker_bad)],
    "robot":  [("happy", robot_happy), ("okay", robot_okay), ("bad", robot_bad)],
}

for char, variants in sets.items():
    for mood, fn in variants:
        img = fn()
        fname = f"{char}_{mood}1_46x49.png"
        img.save(os.path.join(OUT, fname))
        print(f"Saved {fname}")

print(f"\nAll passport characters saved to {OUT}/")
