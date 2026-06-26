#!/usr/bin/env python3
"""Repack resources.ths keeping only core FAPs so qFlipper's MD5 check doesn't time out."""
import sys, heatshrink2, tarfile, io, os

CORE_FAPS = {'infrared.fap', 'nfc.fap', 'lfrfid.fap', 'gpio.fap'}

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
        if m.isfile() and os.path.basename(m.name) in CORE_FAPS:
            print(f'  keeping: {m.name}')
            dst_tar.addfile(m, src_tar.extractfile(m))
        elif m.isdir():
            dst_tar.addfile(m)

slim_tar = slim_buf.getvalue()
recompressed = heatshrink2.compress(slim_tar, window_sz2=window_sz2, lookahead_sz2=lookahead_sz2)
result = raw[:7] + recompressed
open(src_path, 'wb').write(result)
print(f'  resources.ths: {len(raw)//1024}KB -> {len(result)//1024}KB')
