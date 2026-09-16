#!/usr/bin/env python3
"""
Strip the "Hitag2 BF" (Fiat-BCM Hell brute force) scene from the SubGHz app
to recover flash space. Every piece of it is tagged [HITAG2_BF] in ARF's
source, cleanly separate from the unrelated [HITAG2_SEED] (Renault V1
classic-Hitag2 seed brute force) feature, which this script leaves intact —
seed_bf.c doesn't include or call any of the hitag2_bf/core/hell helpers.

Exact-text surgery, same defensive style as this project's other
patch_*.py scripts: fails loudly if upstream source has changed shape.

Usage:
    strip_hitag2_bf.py <flipper-fw-dir>
"""

import sys
from pathlib import Path


def replace_once(content, old, new, label, path):
    count = content.count(old)
    if count != 1:
        raise SystemExit(
            f"ERROR: expected exactly 1 occurrence of {label!r} in {path}, found {count} "
            "— upstream changed shape, patch needs updating"
        )
    return content.replace(old, new)


def patch_file(path, edits):
    content = path.read_text(encoding="utf-8")
    for old, new, label in edits:
        content = replace_once(content, old, new, label, path)
    path.write_text(content, encoding="utf-8")
    print(f"Patched {path}")


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} <flipper-fw-dir>")

    root = Path(sys.argv[1])
    subghz = root / "applications" / "main" / "subghz"

    # ── Delete Hitag2-BF-only source files ──
    for rel in [
        "helpers/subghz_hitag2_bf.c",
        "helpers/subghz_hitag2_bf.h",
        "helpers/subghz_hitag2_bf_dict.c",
        "helpers/subghz_hitag2_core.c",
        "helpers/subghz_hitag2_core.h",
        "helpers/subghz_hitag2_hell.c",
        "helpers/subghz_hitag2_hell.h",
        "views/subghz_hitag2_bf.c",
        "views/subghz_hitag2_bf.h",
        "scenes/subghz_scene_hitag2_bf.c",
        "resources/subghz/assets/hitag2",
    ]:
        f = subghz / rel
        if f.exists():
            f.unlink()
            print(f"Removed {f}")
        else:
            print(f"WARNING: {f} not found — already removed?", file=sys.stderr)

    # ── scenes/subghz_scene_config.h: drop the scene registration ──
    patch_file(
        subghz / "scenes" / "subghz_scene_config.h",
        [
            (
                "ADD_SCENE(subghz, hitag2_bf, Hitag2Bf) // [HITAG2_BF]\n",
                "",
                "hitag2_bf scene registration",
            ),
        ],
    )

    # ── helpers/subghz_types.h: drop the view id enum value ──
    patch_file(
        subghz / "helpers" / "subghz_types.h",
        [
            (
                "    SubGhzViewIdHitag2Bf, // [HITAG2_BF]\n",
                "",
                "SubGhzViewIdHitag2Bf enum value",
            ),
        ],
    )

    # ── subghz_i.h: drop the view include + struct field ──
    patch_file(
        subghz / "subghz_i.h",
        [
            (
                '#include "views/subghz_hitag2_bf.h" // [HITAG2_BF]\n',
                "",
                "hitag2_bf view include",
            ),
            (
                "    SubGhzViewHitag2Bf* subghz_hitag2_bf; // [HITAG2_BF]\n",
                "",
                "subghz_hitag2_bf struct field",
            ),
        ],
    )

    # ── subghz.c: drop view alloc/add and remove/free ──
    patch_file(
        subghz / "subghz.c",
        [
            (
                '''    // [HITAG2_BF] Hitag2 Bruteforce view
    subghz->subghz_hitag2_bf = subghz_view_hitag2_bf_alloc();
    view_dispatcher_add_view(
        subghz->view_dispatcher,
        SubGhzViewIdHitag2Bf,
        subghz_view_hitag2_bf_get_view(subghz->subghz_hitag2_bf));

''',
                "",
                "hitag2_bf view alloc+add",
            ),
            (
                '''    // [HITAG2_BF] Hitag2 Bruteforce view
    view_dispatcher_remove_view(subghz->view_dispatcher, SubGhzViewIdHitag2Bf);
    subghz_view_hitag2_bf_free(subghz->subghz_hitag2_bf);

''',
                "",
                "hitag2_bf view remove+free",
            ),
        ],
    )

    # ── scenes/subghz_scene_saved_menu.c: drop menu entry + handler ──
    patch_file(
        subghz / "scenes" / "subghz_scene_saved_menu.c",
        [
            (
                "    SubmenuIndexHitag2Bf, // [HITAG2_BF]\n",
                "",
                "SubmenuIndexHitag2Bf enum value",
            ),
            (
                "    bool is_fiat_bf_candidate = false; // [HITAG2_BF] Fiat V1 or V2 without a key\n",
                "",
                "is_fiat_bf_candidate declaration",
            ),
            (
                # Removing the whole Fiat if-block would leave the Renault
                # branch's "else if" dangling with no preceding "if" — so this
                # also turns that "else if" into a plain "if".
                '''            // [HITAG2_BF] Show "Hitag2 BF" (Fiat-BCM Hell BF) for Fiat V1/V2 that
            // are not cracked yet (no "Hitag2 Key" field).
            if(furi_string_equal_str(proto, "Fiat V1") ||
               furi_string_equal_str(proto, "Fiat V2")) {
                uint8_t key_buf[6];
                flipper_format_rewind(fff);
                if(!flipper_format_read_hex(fff, "Hitag2 Key", key_buf, 6)) {
                    is_fiat_bf_candidate = true;
                }
            }
            // [HITAG2_SEED] Renault V1 uses the classic-Hitag2 SEED brute force
            // (the correct model for Renault), exposed as a SEPARATE manual "Seed
            // BF" action. Show it when the SEED has not been recovered yet (no
            // "Recovered: 1" marker in the .sub). The heavy brute force runs ONLY
            // when the user taps this button, never during capture/load.
            else if(furi_string_equal_str(proto, "Renault V1")) {''',
                '''            // [HITAG2_SEED] Renault V1 uses the classic-Hitag2 SEED brute force
            // (the correct model for Renault), exposed as a SEPARATE manual "Seed
            // BF" action. Show it when the SEED has not been recovered yet (no
            // "Recovered: 1" marker in the .sub). The heavy brute force runs ONLY
            // when the user taps this button, never during capture/load.
            if(furi_string_equal_str(proto, "Renault V1")) {''',
                "is_fiat_bf_candidate detection block + dangling else-if fix",
            ),
            (
                '''
    // [HITAG2_BF] Show Hitag2 BF button for uncracked Fiat V1/V2 signals
    if(is_fiat_bf_candidate) {
        submenu_add_item(
            subghz->submenu,
            "Hitag2 BF",
            SubmenuIndexHitag2Bf,
            subghz_scene_saved_menu_submenu_callback,
            subghz);
    }
''',
                "",
                "Hitag2 BF submenu item",
            ),
            (
                '''        } else if(event.event == SubmenuIndexHitag2Bf) {
            // [HITAG2_BF]
            scene_manager_set_scene_state(
                subghz->scene_manager, SubGhzSceneSavedMenu, SubmenuIndexHitag2Bf);
            scene_manager_next_scene(subghz->scene_manager, SubGhzSceneHitag2Bf);
            return true;
''',
                "",
                "Hitag2 BF event handler",
            ),
        ],
    )


if __name__ == "__main__":
    main()
