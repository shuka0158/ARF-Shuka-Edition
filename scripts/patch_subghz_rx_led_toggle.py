#!/usr/bin/env python3
"""
Add a "RX LED" ON/OFF toggle to SubGHz Settings, letting the user disable the
LED indicator while in Read (Receiver) mode — useful for covert reads or
battery saving. Only the LED is affected: vibration, beep, and backlight
feedback on a captured signal are untouched, since that's what was asked
for. Defaults to ON (existing behavior unchanged for anyone who never
touches the new setting) and persists like every other SubGHz setting.

Exact-text surgery, same defensive style as this project's other
patch_*.py scripts: fails loudly if upstream source has changed shape.

Usage:
    patch_subghz_rx_led_toggle.py <flipper-fw-dir>
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

    # ── subghz_last_settings.h: new field ──
    patch_file(
        subghz / "subghz_last_settings.h",
        [
            (
                "    bool protocol_file_names;\n",
                "    bool protocol_file_names;\n    bool rx_led_indicator;\n",
                "settings struct field",
            ),
        ],
    )

    # ── subghz_last_settings.c: define, default, load, save ──
    patch_file(
        subghz / "subghz_last_settings.c",
        [
            (
                '#define SUBGHZ_LAST_SETTING_FIELD_PROTOCOL_FILE_NAMES               "ProtocolNames"\n',
                '#define SUBGHZ_LAST_SETTING_FIELD_PROTOCOL_FILE_NAMES               "ProtocolNames"\n'
                '#define SUBGHZ_LAST_SETTING_FIELD_RX_LED_INDICATOR                  "RxLedIndicator"\n',
                "field name define",
            ),
            (
                "    instance->leds_and_amp = true;\n",
                "    instance->leds_and_amp = true;\n    instance->rx_led_indicator = true;\n",
                "load default value",
            ),
            (
                '''             if(!flipper_format_read_bool(
                    fff_data_file,
                    SUBGHZ_LAST_SETTING_FIELD_CUSTOM_CAR_EMULATE,
                    &instance->custom_car_emulate,
                    1)) {
                instance->custom_car_emulate = false;
                flipper_format_rewind(fff_data_file);
            }
            FuriString* filter_str = furi_string_alloc();''',
                '''             if(!flipper_format_read_bool(
                    fff_data_file,
                    SUBGHZ_LAST_SETTING_FIELD_CUSTOM_CAR_EMULATE,
                    &instance->custom_car_emulate,
                    1)) {
                instance->custom_car_emulate = false;
                flipper_format_rewind(fff_data_file);
            }
            if(!flipper_format_read_bool(
                    fff_data_file,
                    SUBGHZ_LAST_SETTING_FIELD_RX_LED_INDICATOR,
                    &instance->rx_led_indicator,
                    1)) {
                instance->rx_led_indicator = true;
                flipper_format_rewind(fff_data_file);
            }
            FuriString* filter_str = furi_string_alloc();''',
                "load field read",
            ),
            (
                '''        if(!flipper_format_write_bool(
               file,
               SUBGHZ_LAST_SETTING_FIELD_CUSTOM_CAR_EMULATE,
               &instance->custom_car_emulate,
               1)) {
            break;
        }
        if(!flipper_format_write_string_cstr(''',
                '''        if(!flipper_format_write_bool(
               file,
               SUBGHZ_LAST_SETTING_FIELD_CUSTOM_CAR_EMULATE,
               &instance->custom_car_emulate,
               1)) {
            break;
        }
        if(!flipper_format_write_bool(
               file,
               SUBGHZ_LAST_SETTING_FIELD_RX_LED_INDICATOR,
               &instance->rx_led_indicator,
               1)) {
            break;
        }
        if(!flipper_format_write_string_cstr(''',
                "save field write",
            ),
        ],
    )

    # ── subghz_scene_radio_settings.c: menu toggle ──
    patch_file(
        subghz / "scenes" / "subghz_scene_radio_settings.c",
        [
            (
                '''static void subghz_scene_receiver_config_set_timestamp_file_names(VariableItem* item) {
    SubGhz* subghz = variable_item_get_context(item);
    uint8_t index = variable_item_get_current_value_index(item);

    variable_item_set_current_value_text(item, on_off_text[index]);

    subghz->last_settings->protocol_file_names = (index == 1);
    subghz_last_settings_save(subghz->last_settings);
}''',
                '''static void subghz_scene_receiver_config_set_timestamp_file_names(VariableItem* item) {
    SubGhz* subghz = variable_item_get_context(item);
    uint8_t index = variable_item_get_current_value_index(item);

    variable_item_set_current_value_text(item, on_off_text[index]);

    subghz->last_settings->protocol_file_names = (index == 1);
    subghz_last_settings_save(subghz->last_settings);
}

static void subghz_scene_radio_settings_set_rx_led_indicator(VariableItem* item) {
    SubGhz* subghz = variable_item_get_context(item);
    uint8_t index = variable_item_get_current_value_index(item);

    variable_item_set_current_value_text(item, on_off_text[index]);

    // Only the LED is affected — vibro/beep/backlight on a captured signal
    // stay on regardless, this is purely a stealth/battery-save option for
    // the blink while listening and the LED flash on capture.
    subghz->last_settings->rx_led_indicator = (index == 1);
    subghz_last_settings_save(subghz->last_settings);
}''',
                "radio settings setter function",
            ),
            (
                '''    item = variable_item_list_add(
        variable_item_list,
        "Protocol Names",
        ON_OFF_COUNT,
        subghz_scene_receiver_config_set_timestamp_file_names,
        subghz);
    value_index = subghz->last_settings->protocol_file_names;
    variable_item_set_current_value_index(item, value_index);
    variable_item_set_current_value_text(item, on_off_text[value_index]);''',
                '''    item = variable_item_list_add(
        variable_item_list,
        "Protocol Names",
        ON_OFF_COUNT,
        subghz_scene_receiver_config_set_timestamp_file_names,
        subghz);
    value_index = subghz->last_settings->protocol_file_names;
    variable_item_set_current_value_index(item, value_index);
    variable_item_set_current_value_text(item, on_off_text[value_index]);

    item = variable_item_list_add(
        variable_item_list,
        "RX LED",
        ON_OFF_COUNT,
        subghz_scene_radio_settings_set_rx_led_indicator,
        subghz);
    value_index = subghz->last_settings->rx_led_indicator;
    variable_item_set_current_value_index(item, value_index);
    variable_item_set_current_value_text(item, on_off_text[value_index]);''',
                "radio settings menu item",
            ),
        ],
    )

    # ── subghz_scene_receiver.c: LED-only variants of the capture sequences,
    #    and gate all three LED trigger points on the new setting ──
    patch_file(
        subghz / "scenes" / "subghz_scene_receiver.c",
        [
            (
                '''const NotificationSequence subghz_sequence_rx_locked = {
    &message_green_255,

    &message_display_backlight_on,

    &message_vibro_on,
    &message_note_c6,
    &message_delay_50,
    &message_sound_off,
    &message_vibro_off,

    &message_delay_500,

    &message_display_backlight_off,
    NULL,
};''',
                '''const NotificationSequence subghz_sequence_rx_locked = {
    &message_green_255,

    &message_display_backlight_on,

    &message_vibro_on,
    &message_note_c6,
    &message_delay_50,
    &message_sound_off,
    &message_vibro_off,

    &message_delay_500,

    &message_display_backlight_off,
    NULL,
};

// LED-off counterparts (issue: RX LED toggle) — same vibro/beep/backlight
// feedback on a captured signal, just without the green LED flash.
const NotificationSequence subghz_sequence_rx_no_led = {
    &message_display_backlight_on,

    &message_vibro_on,
    &message_note_c6,
    &message_delay_50,
    &message_sound_off,
    &message_vibro_off,

    &message_delay_50,
    NULL,
};

const NotificationSequence subghz_sequence_rx_locked_no_led = {
    &message_display_backlight_on,

    &message_vibro_on,
    &message_note_c6,
    &message_delay_50,
    &message_sound_off,
    &message_vibro_off,

    &message_delay_500,

    &message_display_backlight_off,
    NULL,
};''',
                "no-led sequence variants",
            ),
            (
                '''        switch(subghz->state_notifications) {
        case SubGhzNotificationStateRx:
            notification_message(subghz->notifications, &sequence_blink_cyan_10);
            break;
        case SubGhzNotificationStateRxDone:
            if(!subghz_is_locked(subghz)) {
                notification_message(subghz->notifications, &subghz_sequence_rx);
            } else {
                notification_message(subghz->notifications, &subghz_sequence_rx_locked);
            }
            subghz->state_notifications = SubGhzNotificationStateRx;
            break;
        default:
            break;
        }''',
                '''        switch(subghz->state_notifications) {
        case SubGhzNotificationStateRx:
            if(subghz->last_settings->rx_led_indicator) {
                notification_message(subghz->notifications, &sequence_blink_cyan_10);
            }
            break;
        case SubGhzNotificationStateRxDone:
            if(!subghz_is_locked(subghz)) {
                notification_message(
                    subghz->notifications,
                    subghz->last_settings->rx_led_indicator ? &subghz_sequence_rx :
                                                                &subghz_sequence_rx_no_led);
            } else {
                notification_message(
                    subghz->notifications,
                    subghz->last_settings->rx_led_indicator ?
                        &subghz_sequence_rx_locked :
                        &subghz_sequence_rx_locked_no_led);
            }
            subghz->state_notifications = SubGhzNotificationStateRx;
            break;
        default:
            break;
        }''',
                "tick handler LED gating",
            ),
        ],
    )


if __name__ == "__main__":
    main()
