#!/usr/bin/env python3
"""
Patch flipper-fw/lib/subghz/protocols/psa.c to fix two verified decrypt bugs
in the "PSA GROUP" decoder, found by cross-checking against a Ghidra
decompilation of the real firmware (see new_files/psa2.c for the annotated
reference copy). Both bugs only affect decrypt correctness (button/serial/
counter fields and BF2 brute-force success rate) — they don't touch capture.

Unlike new_files/, this file is NOT copied into the build automatically:
psa.c already exists in upstream ARF, so we patch it in place with exact
string matches (same pattern as patch_receiver.py) instead of overlaying a
stale full-file copy that would silently revert future upstream changes.
"""

import sys

PATH = "flipper-fw/lib/subghz/protocols/psa.c"

with open(PATH, "r") as f:
    src = f.read()

# ── Fix 1: mode23 XOR decrypt was missing a firmware-verified step ───────────
# buffer[8]'s high nibble must be overwritten with the checksum before the
# second-stage XOR, or decoded button/serial/counter fields come out wrong.
OLD_XOR = (
    "    uint8_t validation_result = (checksum ^ key2_high) & 0xF0;\n"
    "    if(validation_result == 0) {\n"
    "        buffer[13] = buffer[9] ^ buffer[8];"
)
NEW_XOR = (
    "    uint8_t validation_result = (checksum ^ key2_high) & 0xF0;\n"
    "    if(validation_result == 0) {\n"
    "        buffer[8] = (buffer[8] & 0x0F) | (checksum & 0xF0);\n"
    "        buffer[13] = buffer[9] ^ buffer[8];"
)

if OLD_XOR not in src:
    print("ERROR: psa_direct_xor_decrypt validation block not found — psa.c changed upstream", file=sys.stderr)
    sys.exit(1)
src = src.replace(OLD_XOR, NEW_XOR, 1)
print("Patched: psa_direct_xor_decrypt buffer[8] checksum nibble fix")

# ── Fix 2: BF2 brute-force CRC-16 input buffer had two bytes swapped ─────────
# This made the checksum essentially never match, silently failing BF2
# decryption on every packet.
OLD_CRC = (
    "            uint8_t crc_buffer[6] = {\n"
    "                (uint8_t)((dec_v0 >> 24) & 0xFF),\n"
    "                (uint8_t)((dec_v0 >> 8) & 0xFF),\n"
    "                (uint8_t)((dec_v0 >> 16) & 0xFF),\n"
    "                (uint8_t)(dec_v0 & 0xFF),"
)
NEW_CRC = (
    "            uint8_t crc_buffer[6] = {\n"
    "                (uint8_t)((dec_v0 >> 24) & 0xFF),\n"
    "                (uint8_t)((dec_v0 >> 16) & 0xFF),\n"
    "                (uint8_t)((dec_v0 >> 8) & 0xFF),\n"
    "                (uint8_t)(dec_v0 & 0xFF),"
)

if OLD_CRC not in src:
    print("ERROR: psa_brute_force_decrypt_bf2 crc_buffer block not found — psa.c changed upstream", file=sys.stderr)
    sys.exit(1)
src = src.replace(OLD_CRC, NEW_CRC, 1)
print("Patched: psa_brute_force_decrypt_bf2 CRC-16 byte order fix")

with open(PATH, "w") as f:
    f.write(src)

print("psa.c patched OK")
