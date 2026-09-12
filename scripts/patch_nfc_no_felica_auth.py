#!/usr/bin/env python3
"""
Remove the FeliCa branch from the two "DES auth" scenes shared between FeliCa
and Mifare Ultralight-C manual key entry (issue #9 flash budget, protocols
variant FeliCa strip).

nfc_scene_des_auth_key_input.c and nfc_scene_des_auth_unlock_warn.c aren't
FeliCa-specific despite the "des_auth" name — they're a generic 3DES-key
entry/confirm flow used by both FeliCa (nfc->felica_auth) and Mifare
Ultralight-C (nfc->mf_ul_auth). With felica_auth removed, only the Ultralight
path remains: drop the ternary/branch and the now-dead `protocol` lookup, and
swap the borrowed FELICA_DATA_BLOCK_SIZE constant for the real Ultralight one
(both are 16 bytes — MF_ULTRALIGHT_C_AUTH_DES_KEY_SIZE, from
lib/nfc/protocols/mf_ultralight/mf_ultralight.h, already reachable via
nfc_app_i.h -> helpers/mf_ultralight_auth.h -> that header, so no new
#include is needed).

Two exact-text edits per file, defensive like this project's other patch_*.py
scripts (fails loudly if upstream changed shape).

Usage:
    patch_nfc_no_felica_auth.py <nfc_app_dir>
      (e.g. flipper-fw/applications/main/nfc)
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


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} <nfc_app_dir>")

    nfc = Path(sys.argv[1])

    # ── nfc_scene_des_auth_key_input.c ──
    key_input_c = nfc / "scenes" / "nfc_scene_des_auth_key_input.c"
    content = key_input_c.read_text(encoding="utf-8")

    content = replace_once(
        content,
        "    // Setup view\n"
        "    NfcProtocol protocol = nfc_device_get_protocol(nfc->nfc_device);\n"
        "    uint8_t* key = (protocol == NfcProtocolFelica) ? nfc->felica_auth->card_key.data :\n"
        "                                                     nfc->mf_ul_auth->tdes_key.data;\n",
        "    // Setup view (Mifare Ultralight-C only: the FeliCa branch this scene\n"
        "    // used to also serve was removed with FeliCa support, issue #9)\n"
        "    uint8_t* key = nfc->mf_ul_auth->tdes_key.data;\n",
        "key_input on_enter setup",
        key_input_c,
    )
    content = replace_once(
        content,
        "        key,\n"
        "        FELICA_DATA_BLOCK_SIZE);\n",
        "        key,\n"
        "        MF_ULTRALIGHT_C_AUTH_DES_KEY_SIZE);\n",
        "key_input byte count",
        key_input_c,
    )
    content = replace_once(
        content,
        "        if(event.event == NfcCustomEventByteInputDone) {\n"
        "            NfcProtocol protocol = nfc_device_get_protocol(nfc->nfc_device);\n"
        "\n"
        "            if(protocol == NfcProtocolFelica) {\n"
        "                nfc->felica_auth->skip_auth = false;\n"
        "            } else {\n"
        "                nfc->mf_ul_auth->type = MfUltralightAuthTypeManual;\n"
        "            }\n"
        "\n"
        "            scene_manager_next_scene(nfc->scene_manager, NfcSceneDesAuthUnlockWarn);\n",
        "        if(event.event == NfcCustomEventByteInputDone) {\n"
        "            nfc->mf_ul_auth->type = MfUltralightAuthTypeManual;\n"
        "\n"
        "            scene_manager_next_scene(nfc->scene_manager, NfcSceneDesAuthUnlockWarn);\n",
        "key_input on_event branch",
        key_input_c,
    )
    key_input_c.write_text(content, encoding="utf-8")
    print(f"Patched {key_input_c}: dropped FeliCa branch, Ultralight-only now.")

    # ── nfc_scene_des_auth_unlock_warn.c ──
    unlock_warn_c = nfc / "scenes" / "nfc_scene_des_auth_unlock_warn.c"
    content = unlock_warn_c.read_text(encoding="utf-8")

    content = replace_once(
        content,
        "    NfcProtocol protocol = nfc_device_get_protocol(nfc->nfc_device);\n"
        "    uint8_t* key = (protocol == NfcProtocolFelica) ? nfc->felica_auth->card_key.data :\n"
        "                                                     nfc->mf_ul_auth->tdes_key.data;\n"
        "\n"
        "    for(uint8_t i = 0; i < FELICA_DATA_BLOCK_SIZE; i++)\n",
        "    // Mifare Ultralight-C only: the FeliCa branch this scene used to also\n"
        "    // serve was removed with FeliCa support (issue #9)\n"
        "    uint8_t* key = nfc->mf_ul_auth->tdes_key.data;\n"
        "\n"
        "    for(uint8_t i = 0; i < MF_ULTRALIGHT_C_AUTH_DES_KEY_SIZE; i++)\n",
        "unlock_warn on_enter setup",
        unlock_warn_c,
    )
    content = replace_once(
        content,
        "        if(event.event == DialogExResultRight) {\n"
        "            nfc->felica_auth->skip_auth = false;\n"
        "            scene_manager_next_scene(nfc->scene_manager, NfcSceneRead);\n",
        "        if(event.event == DialogExResultRight) {\n"
        "            scene_manager_next_scene(nfc->scene_manager, NfcSceneRead);\n",
        "unlock_warn on_event right-button",
        unlock_warn_c,
    )
    unlock_warn_c.write_text(content, encoding="utf-8")
    print(f"Patched {unlock_warn_c}: dropped FeliCa branch, Ultralight-only now.")


if __name__ == "__main__":
    main()
