#!/usr/bin/env python3
"""
Fail the build if the external apps we ship (the .fap files packed into
resources.ths) were built for a different firmware API *major* version than the
firmware itself.

Why this matters
----------------
Flipper's app loader gates every external .fap on the API version baked into the
firmware. The check (lib/flipper_application/application_manifest.c) compares the
*major* only:

    app.api_version.major < firmware.api_version.major  -> "App Too Old"
    app.api_version.major > firmware.api_version.major   -> "App Too New"

If a bundle ever ships FAPs whose major differs from the firmware's, then *every*
external app (NFC, Infrared, RFID, GPIO, and the whole catalog) breaks at launch
with "App Too Old"/"App Too New" and the built-ins (Sub-GHz, Settings) are the
only things that still work. This is exactly the failure reported in issue #8 —
there it was caused by a firmware flash that didn't fully land on the user's
device, but the same skew could also be introduced on *our* side (e.g. stale /
prebuilt FAPs of a different generation sneaking into resources.ths). This guard
makes that impossible to ship silently.

The firmware's exported API version is read from targets/f7/api_symbols.csv
(the `Version,+,<major>.<minor>` line) — the single source fbt uses to both
stamp the firmware's API table and to build the FAPs. Each FAP's own API version
is read from its `.fapmeta` ELF section.

Usage:
    check_api_consistency.py <api_symbols.csv> <resources.ths>
"""

import struct
import sys
import tarfile
import io

FAP_MANIFEST_MAGIC = 0x52474448  # "HDGR" little-endian


def firmware_api_version(csv_path):
    """Return (major, minor) from the `Version,+,M.m` line of api_symbols.csv."""
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 3 and parts[0] == "Version":
                major, minor = parts[2].split(".")
                return int(major), int(minor)
    raise SystemExit(f"ERROR: no `Version` row found in {csv_path}")


def decompress_ths(path):
    """Decompress a Flipper heatshrink 'HSDS' resources.ths into raw tar bytes."""
    import heatshrink2  # provided in the CI toolchain (pip install heatshrink2)

    data = open(path, "rb").read()
    if data[:4] != b"HSDS":
        raise SystemExit(f"ERROR: {path} is not a HSDS heatshrink stream")
    window, lookahead = data[5], data[6]
    # 4-byte magic + version + window + lookahead = 7-byte header
    return heatshrink2.decompress(data[7:], window_sz2=window, lookahead_sz2=lookahead)


def fap_api_version(blob):
    """Read (major, minor) from a .fap ELF's .fapmeta section, or None if absent."""
    if blob[:4] != b"\x7fELF":
        return None
    e_shoff = struct.unpack_from("<I", blob, 0x20)[0]
    e_shentsize = struct.unpack_from("<H", blob, 0x2E)[0]
    e_shnum = struct.unpack_from("<H", blob, 0x30)[0]
    e_shstrndx = struct.unpack_from("<H", blob, 0x32)[0]
    if not e_shoff or not e_shnum:
        return None

    def sh(i):
        return blob[e_shoff + i * e_shentsize : e_shoff + (i + 1) * e_shentsize]

    shstr_off = struct.unpack_from("<I", sh(e_shstrndx), 0x10)[0]

    def secname(i):
        name_off = struct.unpack_from("<I", sh(i), 0)[0]
        end = blob.index(b"\x00", shstr_off + name_off)
        return blob[shstr_off + name_off : end].decode(errors="replace")

    for i in range(e_shnum):
        if secname(i) == ".fapmeta":
            off = struct.unpack_from("<I", sh(i), 0x10)[0]
            meta = blob[off : off + 12]
            if struct.unpack_from("<I", meta, 0)[0] != FAP_MANIFEST_MAGIC:
                return None
            # uint32 magic, uint32 manifest_version, uint32 api_version=(major<<16)|minor
            api = struct.unpack_from("<I", meta, 8)[0]
            return (api >> 16) & 0xFFFF, api & 0xFFFF
    return None


def main():
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {sys.argv[0]} <api_symbols.csv> <resources.ths>")
    csv_path, ths_path = sys.argv[1], sys.argv[2]

    fw_major, fw_minor = firmware_api_version(csv_path)
    print(f"Firmware API version (from api_symbols.csv): {fw_major}.{fw_minor}")

    tar_bytes = decompress_ths(ths_path)
    tf = tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:")

    checked = 0
    no_meta = []
    mismatches = []
    for member in tf.getmembers():
        if not member.isfile() or not member.name.endswith(".fap"):
            continue
        blob = tf.extractfile(member).read()
        ver = fap_api_version(blob)
        if ver is None:
            no_meta.append(member.name)
            continue
        checked += 1
        maj, minr = ver
        if maj != fw_major:
            mismatches.append((member.name, maj, minr))

    print(f"Checked {checked} FAP(s) against firmware API major {fw_major}")
    if no_meta:
        print(f"note: {len(no_meta)} .fap file(s) had no readable .fapmeta (skipped)")

    if mismatches:
        print("")
        print("ERROR: API major mismatch — these apps would show 'App Too Old' / "
              "'App Too New' and freeze on launch:")
        for name, maj, minr in mismatches[:20]:
            direction = "too old" if maj < fw_major else "too new"
            print(f"  {name}: app API {maj}.{minr} vs firmware {fw_major}.{fw_minor} ({direction})")
        if len(mismatches) > 20:
            print(f"  ... and {len(mismatches) - 20} more")
        raise SystemExit(1)

    if checked == 0:
        raise SystemExit("ERROR: no FAPs found in resources.ths — bundle looks broken")

    print("OK — every shipped app matches the firmware API major version.")


if __name__ == "__main__":
    main()
