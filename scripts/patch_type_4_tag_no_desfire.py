#!/usr/bin/env python3
"""
Strip Mifare DESFire support out of type_4_tag_poller_i.c (issue #9 flash-
budget trim). DESFire is Type 4 Tag's other platform besides NTAG4xx, and
its code is woven into shared functions rather than living in an isolated
file, so this does exact-text surgery instead of a blanket file/line removal.

Three of type_4_tag_poller_i.c's functions (create_app/create_cc/create_ndef)
are *entirely* DESFire-only — NTAG4xx tags ship pre-formatted and never call
them — so removing the `if(platform == Type4TagPlatformMfDesfire)` body just
leaves them as clean no-ops returning Type4TagErrorNotSupported, which is
already their behavior for any non-DESFire platform today.

Each replacement is matched on exact current text and fails loudly (like this
project's other patch_*.py scripts) if upstream has changed shape, rather
than silently doing the wrong thing.

Usage:
    patch_type_4_tag_no_desfire.py <path/to/type_4_tag_poller_i.c>
"""

import sys


def replace_once(content, old, new, label):
    count = content.count(old)
    if count != 1:
        raise SystemExit(
            f"ERROR: expected exactly 1 occurrence of {label!r} block, found {count} "
            "— upstream type_4_tag_poller_i.c changed shape, patch needs updating"
        )
    return content.replace(old, new)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} <type_4_tag_poller_i.c>")

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Drop the two DESFire includes.
    content = replace_once(
        content,
        '#include <nfc/protocols/mf_desfire/mf_desfire_poller.h>\n'
        '#include <nfc/protocols/mf_desfire/mf_desfire_poller_defs.h>\n',
        "",
        "desfire includes",
    )

    # 2. Drop the DESFire-only static consts/defines (T4T app id, key
    #    settings, CC/NDEF file templates) — only used by the three gutted
    #    functions below.
    content = replace_once(
        content,
        '''static const MfDesfireApplicationId mf_des_picc_app_id = {.data = {0x00, 0x00, 0x00}};
static const MfDesfireApplicationId mf_des_t4t_app_id = {.data = {0x10, 0xEE, 0xEE}};
static const MfDesfireKeySettings mf_des_t4t_app_key_settings = {
    .is_master_key_changeable = true,
    .is_free_directory_list = true,
    .is_free_create_delete = true,
    .is_config_changeable = true,
    .change_key_id = 0,
    .max_keys = 1,
    .flags = 0,
};
#define MF_DES_T4T_CC_FILE_ID (0x01)
static const MfDesfireFileSettings mf_des_t4t_cc_file = {
    .type = MfDesfireFileTypeStandard,
    .comm = MfDesfireFileCommunicationSettingsPlaintext,
    .access_rights[0] = 0xEEEE,
    .access_rights_len = 1,
    .data.size = TYPE_4_TAG_T4T_CC_MIN_SIZE,
};
#define MF_DES_T4T_NDEF_FILE_ID (0x02)
static const MfDesfireFileSettings mf_des_t4t_ndef_file_default = {
    .type = MfDesfireFileTypeStandard,
    .comm = MfDesfireFileCommunicationSettingsPlaintext,
    .access_rights[0] = 0xEEE0,
    .access_rights_len = 1,
};

''',
        "",
        "desfire static consts",
    )

    # 3. In detect_platform(): drop the "try DESFire after NTAG4xx" branch.
    content = replace_once(
        content,
        '''        ntag4xx_poller.free(ntag4xx);
        if(platform != Type4TagPlatformUnknown) break;

        FURI_LOG_D(TAG, "Detect DESFire");
        MfDesfirePoller* mf_desfire = mf_desfire_poller.alloc(instance->iso14443_4a_poller);
        mf_desfire_poller_set_command_mode(mf_desfire, NxpNativeCommandModeIsoWrapped);
        if(mf_desfire_poller.detect(event, mf_desfire)) {
            platform = Type4TagPlatformMfDesfire;
            nfc_device_set_data(
                device, NfcProtocolMfDesfire, mf_desfire_poller.get_data(mf_desfire));
        }
        mf_desfire_poller.free(mf_desfire);
        if(platform != Type4TagPlatformUnknown) break;
    } while(false);''',
        '''        ntag4xx_poller.free(ntag4xx);
        if(platform != Type4TagPlatformUnknown) break;
    } while(false);''',
        "detect_platform DESFire branch",
    )

    # 4. Gut create_app/create_cc/create_ndef: each function's entire body is
    #    `if(platform == Type4TagPlatformMfDesfire) { ... }` around a
    #    NotSupported default — with DESFire gone, that's just NotSupported.
    for fn_name, old_if_open in [
        ("type_4_tag_poller_create_app", "Type4TagError type_4_tag_poller_create_app(Type4TagPoller* instance) {\n    Type4TagError error = Type4TagErrorNotSupported;\n\n    if(instance->data->platform == Type4TagPlatformMfDesfire) {"),
        ("type_4_tag_poller_create_cc", "Type4TagError type_4_tag_poller_create_cc(Type4TagPoller* instance) {\n    Type4TagError error = Type4TagErrorNotSupported;\n\n    if(instance->data->platform == Type4TagPlatformMfDesfire) {"),
        ("type_4_tag_poller_create_ndef", "Type4TagError type_4_tag_poller_create_ndef(Type4TagPoller* instance) {\n    Type4TagError error = Type4TagErrorNotSupported;\n\n    if(instance->data->platform == Type4TagPlatformMfDesfire) {"),
    ]:
        start = content.find(old_if_open)
        if start == -1:
            raise SystemExit(f"ERROR: could not find start of {fn_name} — upstream changed shape")
        # Find the matching closing brace of the `if` block: it's the line
        # "    }\n\n    return error;\n}" immediately following (checked by
        # locating the next occurrence of that exact closer after `start`).
        closer = "    }\n\n    return error;\n}"
        closer_pos = content.find(closer, start)
        if closer_pos == -1:
            raise SystemExit(f"ERROR: could not find end of {fn_name} — upstream changed shape")
        end = closer_pos + len(closer)
        new_fn = (
            f"Type4TagError {fn_name}(Type4TagPoller* instance) {{\n"
            f"    UNUSED(instance);\n"
            f"    return Type4TagErrorNotSupported;\n"
            f"}}"
        )
        content = content[:start] + new_fn + content[end:]
        print(f"  gutted {fn_name}")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Patched {path}: DESFire support removed from Type 4 Tag poller.")


if __name__ == "__main__":
    main()
