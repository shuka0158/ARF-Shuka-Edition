#!/usr/bin/env python3
"""
Inject pre-compiled .bm animation folders into resources.ths.

resources.ths is a heatshrink-compressed tar archive with a 7-byte HSDS header:
  magic(4) + version(1) + window_sz2(1) + lookahead_sz2(1)

Usage:
  python3 inject_nsfw_anims.py <resources.ths> <animations_source_dir>

The source dir must contain subdirectories, each with meta.txt + frame_N.bm files.
Each animation folder is injected into ext/dolphin/external/ inside the archive,
and manifest.txt is updated to include all new entries.
"""

import sys, heatshrink2, tarfile, io, os


def find_dolphin_ext_prefix(members):
    for m, _ in members:
        parts = m.name.split('/')
        for i, part in enumerate(parts):
            if part == 'dolphin' and i + 1 < len(parts) and parts[i + 1] == 'external':
                return '/'.join(parts[:i + 2])
    # fallback: derive from any dolphin path
    for m, _ in members:
        if 'dolphin' in m.name:
            parts = m.name.split('/')
            for i, part in enumerate(parts):
                if part == 'dolphin':
                    return '/'.join(parts[:i + 1]) + '/external'
    return 'ext/dolphin/external'


def main():
    if len(sys.argv) < 3:
        print("Usage: inject_nsfw_anims.py <resources.ths> <animations_dir>", file=sys.stderr)
        sys.exit(1)

    ths_path  = sys.argv[1]
    anims_dir = sys.argv[2]

    raw = open(ths_path, 'rb').read()
    window_sz2    = raw[5]
    lookahead_sz2 = raw[6]
    print(f"Decompressing resources.ths ({len(raw)//1024} KB, w={window_sz2} la={lookahead_sz2})…")
    dec = heatshrink2.decompress(raw[7:], window_sz2=window_sz2, lookahead_sz2=lookahead_sz2)

    members = []
    with tarfile.open(fileobj=io.BytesIO(dec)) as src:
        for m in src.getmembers():
            data = None if m.isdir() else src.extractfile(m).read()
            members.append((m, data))

    prefix = find_dolphin_ext_prefix(members)
    print(f"Dolphin external path: {prefix}")

    existing_anims  = set()
    manifest_idx    = None
    manifest_data   = b''

    for idx, (m, data) in enumerate(members):
        if m.name == f"{prefix}/manifest.txt":
            manifest_idx  = idx
            manifest_data = data or b''
        elif m.name.startswith(f"{prefix}/") and not m.isdir():
            rel = m.name[len(prefix) + 1:]
            top = rel.split('/')[0]
            if top and top != 'manifest.txt':
                existing_anims.add(top)

    print(f"Existing animations in pack: {sorted(existing_anims)}")

    # Scan source dir for valid animation folders
    new_anims = {}
    for entry in sorted(os.listdir(anims_dir)):
        path = os.path.join(anims_dir, entry)
        if not os.path.isdir(path):
            continue
        if not os.path.exists(os.path.join(path, 'meta.txt')):
            continue
        files = {}
        for fname in sorted(os.listdir(path)):
            fpath = os.path.join(path, fname)
            if os.path.isfile(fpath):
                files[fname] = open(fpath, 'rb').read()
        if files:
            new_anims[entry] = files

    print(f"Found {len(new_anims)} animation folders in source")

    # Add new animations
    added = []
    for anim_name, files in new_anims.items():
        if anim_name in existing_anims:
            print(f"  skip (already present): {anim_name}")
            continue
        dir_info      = tarfile.TarInfo(name=f"{prefix}/{anim_name}")
        dir_info.type = tarfile.DIRTYPE
        dir_info.mode = 0o755
        members.append((dir_info, None))
        for fname, data in sorted(files.items()):
            info      = tarfile.TarInfo(name=f"{prefix}/{anim_name}/{fname}")
            info.size = len(data)
            info.mode = 0o644
            members.append((info, data))
        added.append(anim_name)
        print(f"  injected: {anim_name} ({len(files)} files)")

    # Rebuild manifest.txt
    text = manifest_data.decode('utf-8', errors='replace').rstrip('\n')
    if not text:
        text = "Filetype: Flipper Animation Manifest\nVersion: 1"
    for name in added:
        text += f"\n\nName: {name}\nMin butthurt: 0\nMax butthurt: 18\nMin level: 1\nMax level: 30\nWeight: 3"
    text += '\n'
    new_manifest = text.encode('utf-8')

    info      = tarfile.TarInfo(name=f"{prefix}/manifest.txt")
    info.size = len(new_manifest)
    info.mode = 0o644

    if manifest_idx is not None:
        members[manifest_idx] = (info, new_manifest)
    else:
        members.append((info, new_manifest))

    # Repack tar
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:') as dst:
        for m, data in members:
            if m.isdir():
                dst.addfile(m)
            else:
                dst.addfile(m, io.BytesIO(data))

    compressed = heatshrink2.compress(buf.getvalue(), window_sz2=window_sz2, lookahead_sz2=lookahead_sz2)
    result = raw[:7] + compressed
    open(ths_path, 'wb').write(result)

    print(f"\nDone. resources.ths: {len(raw)//1024} KB → {len(result)//1024} KB")
    print(f"Injected {len(added)} animations: {', '.join(added) if added else '(none new)'}")


if __name__ == '__main__':
    main()
