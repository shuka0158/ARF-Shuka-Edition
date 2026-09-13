#!/usr/bin/env python3
"""
Strip FeliCa/Suica support out of Metroflip (issue #9 flash-budget trim,
paired with the core lib/nfc/protocols/felica removal and the standalone
suica_plugin App() block deletion, handled separately). Metroflip loses
live Suica detection and the ability to re-open previously saved Suica
dumps from disk — the dedicated suica_plugin (scenes/plugins/suica.c) is
removed by the caller of this script, same as Opal/Myki/Clipper/Nol/ITSO
were for the DESFire strip; this script only handles the shared scene
files that reference FeliCa alongside other, kept protocols.

Runs in both build variants now (FeliCa was never part of the "nfc variant
keeps the full DESFire/EMV stack" promise — it's just unrelated size that
happened to also need cutting once nfc's own budget ran out). That matters
for one edit specifically: metroflip_scene_auto.c's menu dispatch has the
FeliCa branch immediately followed by the Mifare DESFire branch in
upstream ARF. In the "protocols" variant, patch_metroflip_no_desfire.py
already ran and collapsed that DESFire branch away, so FeliCa's block is
followed by NfcProtocolIso14443_4a instead. In the "nfc" variant, DESFire
is never stripped, so the original NfcProtocolMfDesfire trailing context
is still there. `replace_variant` below tries both known-valid trailing
contexts and uses whichever one actually matches — still fails loudly if
neither does (upstream changed shape), same as every other patch here.

Exact-text surgery, same defensive style as this project's other
patch_*.py scripts: fails loudly if upstream Metroflip source has changed
shape, rather than silently doing the wrong thing.

Usage:
    patch_metroflip_no_felica.py <metroflip_dir>
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


def replace_variant(content, pairs, label, path):
    """Like replace_once, but tries several possible (old, new) pairs (for
    text whose exact shape depends on which other strip steps already ran)
    and applies whichever `old` is present exactly once. Fails loudly only
    if none of the candidates match — same guarantee as replace_once."""
    matches = [(old, new) for old, new in pairs if content.count(old) == 1]
    if len(matches) != 1:
        raise SystemExit(
            f"ERROR: expected exactly 1 of {len(pairs)} candidate texts for {label!r} "
            f"to match exactly once in {path}, found {len(matches)} — upstream changed shape, "
            "patch needs updating"
        )
    old, new = matches[0]
    return content.replace(old, new)


def patch_file(path, edits):
    content = path.read_text(encoding="utf-8")
    for edit in edits:
        if len(edit) == 3:
            old, new, label = edit
            content = replace_once(content, old, new, label, path)
        else:
            pairs, label = edit
            content = replace_variant(content, pairs, label, path)
    path.write_text(content, encoding="utf-8")
    print(f"Patched {path}")


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} <metroflip_dir>")

    root = Path(sys.argv[1])

    # ── metroflip_scene_auto.c: two self-contained else-if branches ──
    patch_file(
        root / "scenes" / "metroflip_scene_auto.c",
        [
            (
                '''        } else if(event.data.protocols && *event.data.protocols == NfcProtocolFelica) {
            nfc_detected_protocols_set(
                app->detected_protocols, event.data.protocols, event.data.protocol_num);
            view_dispatcher_send_custom_event(
                app->view_dispatcher, MetroflipCustomEventPollerDetect);
        } else if(event.data.protocols && *event.data.protocols == NfcProtocolIso14443_4b) {''',
                '''        } else if(event.data.protocols && *event.data.protocols == NfcProtocolIso14443_4b) {''',
                "metroflip_scene_auto.c scan-detect felica branch",
            ),
            (
                [
                    # nfc variant: DESFire not stripped, original trailing context.
                    (
                        '''            } else if(proto == NfcProtocolFelica) {
                popup_set_header(
                    popup, "FeliCa card\\ndetected!\\nReading...", 68, 30, AlignLeft, AlignTop);
                app->card_type = "suica";
                app->is_desfire = false;
                scene_manager_next_scene(app->scene_manager, MetroflipSceneParse);
                consumed = true;
            } else if(proto == NfcProtocolMfDesfire) {''',
                        '''            } else if(proto == NfcProtocolMfDesfire) {''',
                    ),
                    # protocols variant: patch_metroflip_no_desfire.py already
                    # collapsed the DESFire branch away.
                    (
                        '''            } else if(proto == NfcProtocolFelica) {
                popup_set_header(
                    popup, "FeliCa card\\ndetected!\\nReading...", 68, 30, AlignLeft, AlignTop);
                app->card_type = "suica";
                app->is_desfire = false;
                scene_manager_next_scene(app->scene_manager, MetroflipSceneParse);
                consumed = true;
            } else if(proto == NfcProtocolIso14443_4a) {''',
                        '''            } else if(proto == NfcProtocolIso14443_4a) {''',
                    ),
                ],
                "metroflip_scene_auto.c menu felica branch",
            ),
        ],
    )

    # ── metroflip_scene_load.c: drop the suica_loading.h include and both
    #    load_suica_data() call sites (live-scan format + legacy on-disk
    #    format); mark either as an unrecognized card instead of crashing on
    #    missing Suica data downstream ──
    patch_file(
        root / "scenes" / "metroflip_scene_load.c",
        [
            (
                '#include "../api/metroflip/metroflip_api.h"\n'
                '#include "../api/suica/suica_loading.h"\n',
                '#include "../api/metroflip/metroflip_api.h"\n',
                "metroflip_scene_load.c suica_loading include",
            ),
            (
                '''                } else if(strcmp(protocol_name, "FeliCa") == 0) {
                    do {
                        uint32_t data_format_version = 0;
                        bool read_success = flipper_format_read_uint32(
                            format, "Data format version", &data_format_version, 1);
                        if(!read_success || data_format_version != 2) break;
                        // data format version 2 => post API 87.0 i.e. OFW #4254
                        // If we didn't find a format version, it should be saved by previous Metroflip version
                        // So we let it fall through to the Japan Transit IC logic below
                        app->card_type = "suica";
                        app->is_desfire = false;
                        app->data_loaded = true;
                        load_suica_data(app, format, false);
                        FURI_LOG_I(TAG, "Detected: FeliCa (API 87.0+)");
                    } while(false);
                } else if(strcmp(protocol_name, "ST25TB") == 0) {''',
                '''                } else if(strcmp(protocol_name, "FeliCa") == 0) {
                    // FeliCa/Suica support stripped from this build (issue #9
                    // flash budget) — saved FeliCa dumps can no longer be parsed.
                    FURI_LOG_I(TAG, "Detected: FeliCa (unsupported, FeliCa stripped)");
                    app->card_type = "unknown";
                } else if(strcmp(protocol_name, "ST25TB") == 0) {''',
                "metroflip_scene_load.c FeliCa protocol_name branch",
            ),
            (
                '''                if(strcmp(card_str, "Japan Transit IC") == 0) {
                    FURI_LOG_I(TAG, "Detected: Japan Transit IC");
                    app->card_type = "suica";
                    app->is_desfire = false;
                    app->data_loaded = true;
                    load_suica_data(app, format, true);
                    // This format is deprecated after OFW #4254 but kept for backward compatibility
                } else if(strcmp(card_str, "calypso") == 0) {''',
                '''                if(strcmp(card_str, "Japan Transit IC") == 0) {
                    // FeliCa/Suica support stripped from this build (issue #9
                    // flash budget) — this legacy on-disk format can no longer
                    // be parsed.
                    FURI_LOG_I(TAG, "Detected: Japan Transit IC (unsupported, FeliCa stripped)");
                    app->card_type = "unknown";
                } else if(strcmp(card_str, "calypso") == 0) {''',
                "metroflip_scene_load.c Japan Transit IC branch",
            ),
        ],
    )


if __name__ == "__main__":
    main()
