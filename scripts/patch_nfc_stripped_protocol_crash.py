#!/usr/bin/env python3
"""
Stop the NULL-pointer reboot when the NFC app reaches a protocol that was
stripped from this build (Mifare DESFire and EMV — issue #9 flash budget).

Both protocols are removed from the poller/device tables and from
`nfc_protocol_support_plugin_names[]`, but they stay defined in the
`NfcProtocol` enum (removing an enumerator would renumber every table). So:

  * `nfc_protocol_support_alloc(protocol)` looks up
    `nfc_protocol_support_plugin_names[protocol]`, which is now NULL for the
    stripped protocols, and passes it straight into
    `furi_string_alloc_printf("plugins/nfc_%s.fal", protocol_name)`.
    A NULL "%s" dereferences a null pointer and hard-faults the firmware
    ("Flipper crashed and was rebooted NULL pointer dereference").

  * "Extra Actions -> Read Specific Card Type" fills the menu with *every*
    enum protocol (`nfc_detected_protocols_fill_all_protocols`), so DESFire
    and EMV still appear and selecting them walks straight into the crash
    above.

Two exact-text edits, defensive like this project's other patch_*.py scripts
(fails loudly if upstream changed shape):

  1. nfc_protocol_support.c: guard the alloc — a NULL plugin name falls back
     to the empty support base (graceful no-op) instead of crashing. This is
     the actual crash fix and covers every code path, present and future.

  2. nfc_scene_select_protocol.c: hide protocols with no plugin from the
     "Read Specific Card Type" list, so stripped protocols aren't offered at
     all instead of being dead "unsupported" entries.

Usage:
    patch_nfc_stripped_protocol_crash.py <nfc_app_dir>
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

    # ── 1. Crash fix: guard nfc_protocol_support_alloc against a NULL name ──
    support_c = nfc / "helpers" / "protocol_support" / "nfc_protocol_support.c"
    content = support_c.read_text(encoding="utf-8")
    content = replace_once(
        content,
        "    const char* protocol_name = nfc_protocol_support_plugin_names[protocol];\n"
        "    FuriString* plugin_path =\n"
        "        furi_string_alloc_printf(APP_ASSETS_PATH(\"plugins/nfc_%s.fal\"), protocol_name);\n",
        "    const char* protocol_name = nfc_protocol_support_plugin_names[protocol];\n"
        "    if(!protocol_name) {\n"
        "        /* Protocol stripped from this build (DESFire/EMV, issue #9 flash\n"
        "         * budget): its plugin-name slot is NULL. Passing NULL to the \"%s\"\n"
        "         * below dereferences a null pointer and hard-faults the firmware.\n"
        "         * Fall back to the empty support base so a stray read of a removed\n"
        "         * protocol is a graceful no-op instead of a reboot. */\n"
        "        protocol_support->plugin_manager = NULL;\n"
        "        protocol_support->base = &nfc_protocol_support_empty;\n"
        "        instance->protocol_support = protocol_support;\n"
        "        return;\n"
        "    }\n"
        "    FuriString* plugin_path =\n"
        "        furi_string_alloc_printf(APP_ASSETS_PATH(\"plugins/nfc_%s.fal\"), protocol_name);\n",
        "nfc_protocol_support_alloc NULL guard",
        support_c,
    )
    support_c.write_text(content, encoding="utf-8")
    print(f"Patched {support_c}: guarded alloc against stripped-protocol NULL name.")

    # ── 2. Hide stripped protocols from "Read Specific Card Type" ──
    select_c = nfc / "scenes" / "nfc_scene_select_protocol.c"
    content = select_c.read_text(encoding="utf-8")

    content = replace_once(
        content,
        "#include \"../nfc_app_i.h\"\n",
        "#include \"../nfc_app_i.h\"\n\n"
        "/* Defined in helpers/protocol_support/nfc_protocol_support.c — non-NULL\n"
        " * only for protocols actually compiled into this build. Used to hide\n"
        " * stripped protocols (DESFire/EMV, issue #9) from the read menu. */\n"
        "extern const char* nfc_protocol_support_plugin_names[];\n",
        "select_protocol extern decl",
        select_c,
    )

    content = replace_once(
        content,
        "    for(uint32_t i = 0; i < nfc_detected_protocols_get_num(instance->detected_protocols); i++) {\n"
        "        furi_string_printf(\n"
        "            temp_str,\n"
        "            \"%s %s\",\n"
        "            prefix,\n"
        "            nfc_device_get_protocol_name(\n"
        "                nfc_detected_protocols_get_protocol(instance->detected_protocols, i)));\n",
        "    for(uint32_t i = 0; i < nfc_detected_protocols_get_num(instance->detected_protocols); i++) {\n"
        "        NfcProtocol proto =\n"
        "            nfc_detected_protocols_get_protocol(instance->detected_protocols, i);\n"
        "        /* Skip protocols stripped from this build (DESFire/EMV, issue #9):\n"
        "         * their plugin-name slot is NULL and reading them would hard-fault. */\n"
        "        if(!nfc_protocol_support_plugin_names[proto]) continue;\n"
        "        furi_string_printf(\n"
        "            temp_str,\n"
        "            \"%s %s\",\n"
        "            prefix,\n"
        "            nfc_device_get_protocol_name(proto));\n",
        "select_protocol read-menu loop",
        select_c,
    )
    select_c.write_text(content, encoding="utf-8")
    print(f"Patched {select_c}: hid stripped protocols from Read Specific Card Type.")


if __name__ == "__main__":
    main()
