#!/usr/bin/env python3
"""
Strip Mifare DESFire support out of Metroflip (issue #9 flash-budget trim,
paired with the core lib/nfc/protocols/mf_desfire removal). Metroflip loses
its own DESFire-only scene glue and the transit-card plugins that can't
function without it (Opal/Myki/Clipper/Nol/ITSO are handled separately by
deleting their App() blocks and source files — this script only handles the
shared scene files that reference DESFire alongside other, kept protocols).

Exact-text surgery, same defensive style as this project's other
patch_*.py scripts: fails loudly if upstream Metroflip source has changed
shape, rather than silently doing the wrong thing.

Usage:
    patch_metroflip_no_desfire.py <metroflip_dir>
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
        raise SystemExit(f"usage: {sys.argv[0]} <metroflip_dir>")

    root = Path(sys.argv[1])

    # ── metroflip_i.h: drop the desfire.h include and the mfdes_data field ──
    patch_file(
        root / "metroflip_i.h",
        [
            (
                '#include "scenes/desfire.h"\n#include "scenes/nfc_detected_protocols.h"',
                '#include "scenes/nfc_detected_protocols.h"',
                "metroflip_i.h desfire include",
            ),
            (
                "    NfcDetectedProtocols* detected_protocols;\n    MfDesfireData* mfdes_data;\n    MfClassicData* mfc_data;",
                "    NfcDetectedProtocols* detected_protocols;\n    MfClassicData* mfc_data;",
                "metroflip_i.h mfdes_data field",
            ),
        ],
    )

    # ── metroflip_scene_auto.c ──
    patch_file(
        root / "scenes" / "metroflip_scene_auto.c",
        [
            (
                '#include "keys.h"\n#include "desfire.h"\n#include <nfc/protocols/mf_desfire/mf_desfire_poller.h>\n#include <lib/nfc/protocols/mf_desfire/mf_desfire.h>\n#include <lib/nfc/protocols/iso14443_4a/iso14443_4a.h>',
                '#include "keys.h"\n#include <lib/nfc/protocols/iso14443_4a/iso14443_4a.h>',
                "metroflip_scene_auto.c desfire includes",
            ),
            (
                '''static NfcCommand
    metroflip_scene_detect_desfire_poller_callback(NfcGenericEvent event, void* context) {
    furi_assert(event.protocol == NfcProtocolMfDesfire);

    Metroflip* app = context;
    NfcCommand command = NfcCommandContinue;

    const MfDesfirePollerEvent* mf_desfire_event = event.event_data;
    if(mf_desfire_event->type == MfDesfirePollerEventTypeReadSuccess) {
        nfc_device_set_data(
            app->nfc_device, NfcProtocolMfDesfire, nfc_poller_get_data(app->poller));
        const MfDesfireData* data = nfc_device_get_data(app->nfc_device, NfcProtocolMfDesfire);
        furi_string_reset(app->text_box_store);
        app->card_type = desfire_type(data);

        // For T-Mobilitat Desfire cards, extract card number from ISO14443_4a historical bytes
        if(app->card_type && strstr(app->card_type, "T-mobilitat") != NULL) {
            const Iso14443_4aData* iso_data =
                nfc_device_get_data(app->nfc_device, NfcProtocolIso14443_4a);
            if(iso_data) {
                memset(app->hist_bytes, 0, sizeof(app->hist_bytes));
                app->hist_bytes_count = 0;

                uint32_t hb_count;
                const uint8_t* hb = iso14443_4a_get_historical_bytes(iso_data, &hb_count);
                if(hb && hb_count > 0) {
                    memcpy(app->hist_bytes, hb, MIN(hb_count, sizeof(app->hist_bytes)));
                    app->hist_bytes_count = MIN(hb_count, sizeof(app->hist_bytes));
                    app->card_type = "tmobilitat";
                    app->is_desfire = false;
                }
            }
        }

        view_dispatcher_send_custom_event(app->view_dispatcher, MetroflipCustomEventPollerSuccess);

        command = NfcCommandStop;
    } else if(mf_desfire_event->type == MfDesfirePollerEventTypeReadFailed) {
        view_dispatcher_send_custom_event(app->view_dispatcher, MetroflipCustomEventPollerSuccess);
        command = NfcCommandContinue;
    }

    return command;
}

static NfcCommand
    metroflip_scene_detect_iso14443_4a_poller_callback(NfcGenericEvent event, void* context) {''',
                '''static NfcCommand
    metroflip_scene_detect_iso14443_4a_poller_callback(NfcGenericEvent event, void* context) {''',
                "metroflip_scene_auto.c desfire callback function",
            ),
            (
                '''        } else if(event.data.protocols && *event.data.protocols == NfcProtocolMfDesfire) {
            nfc_detected_protocols_set(
                app->detected_protocols, event.data.protocols, event.data.protocol_num);
            view_dispatcher_send_custom_event(
                app->view_dispatcher, MetroflipCustomEventPollerDetect);
        } else if(event.data.protocols && *event.data.protocols == NfcProtocolFelica) {''',
                '''        } else if(event.data.protocols && *event.data.protocols == NfcProtocolFelica) {''',
                "metroflip_scene_auto.c scan-detect desfire branch",
            ),
            (
                '''            } else if(proto == NfcProtocolMfDesfire) {
                popup_set_header(
                    popup, "DESFire card\\ndetected!\\nReading AIDs...", 68, 30, AlignLeft, AlignTop);
                app->is_desfire = true;
                app->poller = nfc_poller_alloc(app->nfc, NfcProtocolMfDesfire);
                nfc_poller_start(app->poller, metroflip_scene_detect_desfire_poller_callback, app);
                consumed = true;
            } else if(proto == NfcProtocolIso14443_4a) {''',
                '''            } else if(proto == NfcProtocolIso14443_4a) {''',
                "metroflip_scene_auto.c menu desfire branch",
            ),
        ],
    )

    # ── metroflip_scene_load.c ──
    patch_file(
        root / "scenes" / "metroflip_scene_load.c",
        [
            (
                '''                } else if(strcmp(protocol_name, "Mifare DESFire") == 0) {
                    MfDesfireData* data = mf_desfire_alloc();
                    if(!mf_desfire_load(data, format, 2)) {
                        mf_desfire_free(data);
                        break;
                    }

                    app->is_desfire = true;
                    app->data_loaded = true;
                    app->card_type =
                        desfire_type(data); // This must return a static literal string

                    mf_desfire_free(data);
                } else if(strcmp(protocol_name, "FeliCa") == 0) {''',
                '''                } else if(strcmp(protocol_name, "FeliCa") == 0) {''',
                "metroflip_scene_load.c desfire load branch",
            ),
        ],
    )


if __name__ == "__main__":
    main()
