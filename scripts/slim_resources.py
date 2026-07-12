#!/usr/bin/env python3
"""Repack resources.ths keeping core FAPs + all dolphin animations.

Previous version only kept files whose basename was in CORE_FAPS, which
silently stripped all dolphin animation frames (frame_0.bm, meta, etc.)
because those filenames are not FAP names. Now we keep everything that
isn't a non-core .fap file — animations, manifests, and directory
structure are preserved; only non-essential third-party app FAPs are cut.
"""
import sys, heatshrink2, tarfile, io, os

CORE_FAPS = {'infrared.fap', 'ibutton.fap', 'nfc.fap', 'lfrfid.fap', 'gpio.fap', 'bad_usb.fap', 'u2f.fap'}

src_path = sys.argv[1]
raw = open(src_path, 'rb').read()

# HSDS header: magic(4) + version(1) + window_sz2(1) + lookahead_sz2(1)
window_sz2    = raw[5]
lookahead_sz2 = raw[6]
dec = heatshrink2.decompress(raw[7:], window_sz2=window_sz2, lookahead_sz2=lookahead_sz2)

slim_buf = io.BytesIO()
with tarfile.open(fileobj=io.BytesIO(dec)) as src_tar, \
     tarfile.open(fileobj=slim_buf, mode='w:') as dst_tar:
    for m in src_tar.getmembers():
        if m.isdir():
            dst_tar.addfile(m)
        elif m.name.endswith('.fap'):
            # Strip non-core FAPs; keep the 7 core ones
            if os.path.basename(m.name) in CORE_FAPS:
                print(f'  keeping fap: {m.name}')
                dst_tar.addfile(m, src_tar.extractfile(m))
        else:
            # Keep everything else: dolphin animations, manifests, icons, etc.
            dst_tar.addfile(m, src_tar.extractfile(m))

slim_tar = slim_buf.getvalue()
recompressed = heatshrink2.compress(slim_tar, window_sz2=window_sz2, lookahead_sz2=lookahead_sz2)
result = raw[:7] + recompressed
open(src_path, 'wb').write(result)
print(f'  resources.ths: {len(raw)//1024}KB -> {len(result)//1024}KB')
