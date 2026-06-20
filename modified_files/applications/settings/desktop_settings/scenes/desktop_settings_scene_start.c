#include <applications.h>
#include <lib/toolbox/value_index.h>

#include "../desktop_settings_app.h"
#include "desktop_settings_scene.h"
#include "desktop_settings_scene_i.h"
#include <power/power_service/power.h>

typedef enum {
    DesktopSettingsPinSetup = 0,
    DesktopSettingsAutoLockDelay,
    DesktopSettingsAutoPowerOff,
    DesktopSettingsBatteryDisplay,
    DesktopSettingsClockDisplay,
    DesktopSettingsChangeName,
    DesktopSettingsHappyMode,
    DesktopSettingsMenuScrollLoop,
    DesktopSettingsMenuScrollAnim,
    DesktopSettingsMenuLayout,
    DesktopSettingsPassportChar,
    DesktopSettingsFavoriteLeftShort,
    DesktopSettingsFavoriteLeftLong,
    DesktopSettingsFavoriteRightShort,
    DesktopSettingsFavoriteRightLong,
    DesktopSettingsFavoriteOkLong,
} DesktopSettingsEntry;

#define AUTO_LOCK_DELAY_COUNT 9
const char* const auto_lock_delay_text[AUTO_LOCK_DELAY_COUNT] = {
    "OFF", "10s", "15s", "30s", "60s", "90s", "2min", "5min", "10min",
};
const uint32_t auto_lock_delay_value[AUTO_LOCK_DELAY_COUNT] =
    {0, 10000, 15000, 30000, 60000, 90000, 120000, 300000, 600000};

#define USB_INHIBIT_AUTO_LOCK_DELAY_COUNT 2
const char* const usb_inhibit_auto_lock_delay_text[USB_INHIBIT_AUTO_LOCK_DELAY_COUNT] = {
    "OFF", "ON",
};
const uint32_t usb_inhibit_auto_lock_delay_value[USB_INHIBIT_AUTO_LOCK_DELAY_COUNT] = {0, 1};

#define CLOCK_ENABLE_COUNT 2
const char* const clock_enable_text[CLOCK_ENABLE_COUNT] = {"OFF", "ON"};
const uint32_t clock_enable_value[CLOCK_ENABLE_COUNT] = {0, 1};

#define BATTERY_VIEW_COUNT 6
const char* const battery_view_count_text[BATTERY_VIEW_COUNT] =
    {"Bar", "%", "Inv. %", "Retro 3", "Retro 5", "Bar %"};
const uint32_t displayBatteryPercentage_value[BATTERY_VIEW_COUNT] = {
    DISPLAY_BATTERY_BAR,
    DISPLAY_BATTERY_PERCENT,
    DISPLAY_BATTERY_INVERTED_PERCENT,
    DISPLAY_BATTERY_RETRO_3,
    DISPLAY_BATTERY_RETRO_5,
    DISPLAY_BATTERY_BAR_PERCENT};

// ── Passport character ────────────────────────────────────────────────────

#define PASSPORT_CHAR_COUNT 4
const char* const passport_char_text[PASSPORT_CHAR_COUNT] = {
    "Dolphin", "Skull", "Hacker", "Robot",
};
const uint32_t passport_char_value[PASSPORT_CHAR_COUNT] = {0, 1, 2, 3};

static void desktop_settings_scene_start_passport_char_changed(VariableItem* item) {
    DesktopSettingsApp* app = variable_item_get_context(item);
    uint8_t index = variable_item_get_current_value_index(item);
    variable_item_set_current_value_text(item, passport_char_text[index]);
    app->settings.passport_char = passport_char_value[index];
}

// ── Menu appearance ────────────────────────────────────────────────────────

#define MENU_SCROLL_LOOP_COUNT 2
const char* const menu_scroll_loop_text[MENU_SCROLL_LOOP_COUNT] = {"Linear", "Warp"};
const uint32_t menu_scroll_loop_value[MENU_SCROLL_LOOP_COUNT] = {0, 1};

#define MENU_SCROLL_ANIM_COUNT 2
const char* const menu_scroll_anim_text[MENU_SCROLL_ANIM_COUNT] = {"Instant", "Slide"};
const uint32_t menu_scroll_anim_value[MENU_SCROLL_ANIM_COUNT] = {0, 1};

#define MENU_LAYOUT_COUNT 2
const char* const menu_layout_text[MENU_LAYOUT_COUNT] = {"List", "Grid"};
const uint32_t menu_layout_value[MENU_LAYOUT_COUNT] = {0, 1};

// ── Callbacks ──────────────────────────────────────────────────────────────

static void desktop_settings_scene_start_var_list_enter_callback(void* context, uint32_t index) {
    DesktopSettingsApp* app = context;
    view_dispatcher_send_custom_event(app->view_dispatcher, index);
}

static void desktop_settings_scene_start_battery_view_changed(VariableItem* item) {
    DesktopSettingsApp* app = variable_item_get_context(item);
    uint8_t index = variable_item_get_current_value_index(item);
    variable_item_set_current_value_text(item, battery_view_count_text[index]);
    app->settings.displayBatteryPercentage = index;
}

static void desktop_settings_scene_start_clock_enable_changed(VariableItem* item) {
    DesktopSettingsApp* app = variable_item_get_context(item);
    uint8_t index = variable_item_get_current_value_index(item);
    variable_item_set_current_value_text(item, clock_enable_text[index]);
    app->settings.display_clock = index;
}

static void desktop_settings_scene_start_auto_lock_delay_changed(VariableItem* item) {
    DesktopSettingsApp* app = variable_item_get_context(item);
    uint8_t index = variable_item_get_current_value_index(item);
    variable_item_set_current_value_text(item, auto_lock_delay_text[index]);
    app->settings.auto_lock_delay_ms = auto_lock_delay_value[index];
}

static void desktop_settings_scene_start_usb_inhibit_auto_lock_delay_changed(VariableItem* item) {
    DesktopSettingsApp* app = variable_item_get_context(item);
    uint8_t index = variable_item_get_current_value_index(item);
    variable_item_set_current_value_text(item, usb_inhibit_auto_lock_delay_text[index]);
    app->settings.usb_inhibit_auto_lock = usb_inhibit_auto_lock_delay_value[index];
}

static void desktop_settings_scene_start_menu_scroll_loop_changed(VariableItem* item) {
    DesktopSettingsApp* app = variable_item_get_context(item);
    uint8_t index = variable_item_get_current_value_index(item);
    variable_item_set_current_value_text(item, menu_scroll_loop_text[index]);
    app->settings.menu_scroll_loop = menu_scroll_loop_value[index];
}

static void desktop_settings_scene_start_menu_scroll_anim_changed(VariableItem* item) {
    DesktopSettingsApp* app = variable_item_get_context(item);
    uint8_t index = variable_item_get_current_value_index(item);
    variable_item_set_current_value_text(item, menu_scroll_anim_text[index]);
    app->settings.menu_scroll_anim = menu_scroll_anim_value[index];
}

static void desktop_settings_scene_start_menu_layout_changed(VariableItem* item) {
    DesktopSettingsApp* app = variable_item_get_context(item);
    uint8_t index = variable_item_get_current_value_index(item);
    variable_item_set_current_value_text(item, menu_layout_text[index]);
    app->settings.menu_layout = menu_layout_value[index];
}

// ── Scene enter ────────────────────────────────────────────────────────────

void desktop_settings_scene_start_on_enter(void* context) {
    DesktopSettingsApp* app = context;
    VariableItemList* variable_item_list = app->variable_item_list;

    VariableItem* item;
    uint8_t value_index;

    variable_item_list_add(variable_item_list, "PIN Setup", 1, NULL, NULL);

    item = variable_item_list_add(
        variable_item_list,
        "Auto Lock Time",
        AUTO_LOCK_DELAY_COUNT,
        desktop_settings_scene_start_auto_lock_delay_changed,
        app);
    value_index = value_index_uint32(
        app->settings.auto_lock_delay_ms, auto_lock_delay_value, AUTO_LOCK_DELAY_COUNT);
    variable_item_set_current_value_index(item, value_index);
    variable_item_set_current_value_text(item, auto_lock_delay_text[value_index]);

    item = variable_item_list_add(
        variable_item_list,
        "Auto Lock disarm by active USB session",
        USB_INHIBIT_AUTO_LOCK_DELAY_COUNT,
        desktop_settings_scene_start_usb_inhibit_auto_lock_delay_changed,
        app);
    value_index = value_index_uint32(
        app->settings.usb_inhibit_auto_lock,
        usb_inhibit_auto_lock_delay_value,
        USB_INHIBIT_AUTO_LOCK_DELAY_COUNT);
    variable_item_set_current_value_index(item, value_index);
    variable_item_set_current_value_text(item, usb_inhibit_auto_lock_delay_text[value_index]);

    item = variable_item_list_add(
        variable_item_list,
        "Battery View",
        BATTERY_VIEW_COUNT,
        desktop_settings_scene_start_battery_view_changed,
        app);
    value_index = value_index_uint32(
        app->settings.displayBatteryPercentage,
        displayBatteryPercentage_value,
        BATTERY_VIEW_COUNT);
    variable_item_set_current_value_index(item, value_index);
    variable_item_set_current_value_text(item, battery_view_count_text[value_index]);

    item = variable_item_list_add(
        variable_item_list,
        "Show Clock",
        CLOCK_ENABLE_COUNT,
        desktop_settings_scene_start_clock_enable_changed,
        app);
    value_index =
        value_index_uint32(app->settings.display_clock, clock_enable_value, CLOCK_ENABLE_COUNT);
    variable_item_set_current_value_index(item, value_index);
    variable_item_set_current_value_text(item, clock_enable_text[value_index]);

    variable_item_list_add(variable_item_list, "Change Flipper Name", 0, NULL, app);
    variable_item_list_add(variable_item_list, "Happy Mode", 1, NULL, NULL);

    // ── Menu appearance ──────────────────────────────────────────────────

    item = variable_item_list_add(
        variable_item_list,
        "Menu Scroll",
        MENU_SCROLL_LOOP_COUNT,
        desktop_settings_scene_start_menu_scroll_loop_changed,
        app);
    value_index = value_index_uint32(
        app->settings.menu_scroll_loop, menu_scroll_loop_value, MENU_SCROLL_LOOP_COUNT);
    variable_item_set_current_value_index(item, value_index);
    variable_item_set_current_value_text(item, menu_scroll_loop_text[value_index]);

    item = variable_item_list_add(
        variable_item_list,
        "Menu Animation",
        MENU_SCROLL_ANIM_COUNT,
        desktop_settings_scene_start_menu_scroll_anim_changed,
        app);
    value_index = value_index_uint32(
        app->settings.menu_scroll_anim, menu_scroll_anim_value, MENU_SCROLL_ANIM_COUNT);
    variable_item_set_current_value_index(item, value_index);
    variable_item_set_current_value_text(item, menu_scroll_anim_text[value_index]);

    item = variable_item_list_add(
        variable_item_list,
        "Menu Layout",
        MENU_LAYOUT_COUNT,
        desktop_settings_scene_start_menu_layout_changed,
        app);
    value_index =
        value_index_uint32(app->settings.menu_layout, menu_layout_value, MENU_LAYOUT_COUNT);
    variable_item_set_current_value_index(item, value_index);
    variable_item_set_current_value_text(item, menu_layout_text[value_index]);

    item = variable_item_list_add(
        variable_item_list,
        "Passport Char",
        PASSPORT_CHAR_COUNT,
        desktop_settings_scene_start_passport_char_changed,
        app);
    value_index = value_index_uint32(
        app->settings.passport_char, passport_char_value, PASSPORT_CHAR_COUNT);
    variable_item_set_current_value_index(item, value_index);
    variable_item_set_current_value_text(item, passport_char_text[value_index]);

    // ── Favorites ────────────────────────────────────────────────────────

    variable_item_list_add(variable_item_list, "Favorite App - Left Short", 1, NULL, NULL);
    variable_item_list_add(variable_item_list, "Favorite App - Left Long", 1, NULL, NULL);
    variable_item_list_add(variable_item_list, "Favorite App - Right Short", 1, NULL, NULL);
    variable_item_list_add(variable_item_list, "Favorite App - Right Long", 1, NULL, NULL);
    variable_item_list_add(variable_item_list, "Favorite App - Ok Long", 1, NULL, NULL);

    variable_item_list_set_enter_callback(
        variable_item_list, desktop_settings_scene_start_var_list_enter_callback, app);

    view_dispatcher_switch_to_view(app->view_dispatcher, DesktopSettingsAppViewVarItemList);
}

bool desktop_settings_scene_start_on_event(void* context, SceneManagerEvent event) {
    DesktopSettingsApp* app = context;
    bool consumed = false;

    if(event.type == SceneManagerEventTypeCustom) {
        switch(event.event) {
        case DesktopSettingsPinSetup:
            scene_manager_next_scene(app->scene_manager, DesktopSettingsAppScenePinMenu);
            break;

        case DesktopSettingsChangeName:
            scene_manager_next_scene(app->scene_manager, DesktopSettingsAppSceneChangeName);
            break;

        case DesktopSettingsFavoriteLeftShort:
            scene_manager_set_scene_state(
                app->scene_manager,
                DesktopSettingsAppSceneFavorite,
                SCENE_STATE_SET_FAVORITE_APP | FavoriteAppLeftShort);
            scene_manager_next_scene(app->scene_manager, DesktopSettingsAppSceneFavorite);
            break;
        case DesktopSettingsFavoriteLeftLong:
            scene_manager_set_scene_state(
                app->scene_manager,
                DesktopSettingsAppSceneFavorite,
                SCENE_STATE_SET_FAVORITE_APP | FavoriteAppLeftLong);
            scene_manager_next_scene(app->scene_manager, DesktopSettingsAppSceneFavorite);
            break;
        case DesktopSettingsFavoriteRightShort:
            scene_manager_set_scene_state(
                app->scene_manager,
                DesktopSettingsAppSceneFavorite,
                SCENE_STATE_SET_FAVORITE_APP | FavoriteAppRightShort);
            scene_manager_next_scene(app->scene_manager, DesktopSettingsAppSceneFavorite);
            break;
        case DesktopSettingsFavoriteRightLong:
            scene_manager_set_scene_state(
                app->scene_manager,
                DesktopSettingsAppSceneFavorite,
                SCENE_STATE_SET_FAVORITE_APP | FavoriteAppRightLong);
            scene_manager_next_scene(app->scene_manager, DesktopSettingsAppSceneFavorite);
            break;
        case DesktopSettingsFavoriteOkLong:
            scene_manager_set_scene_state(
                app->scene_manager,
                DesktopSettingsAppSceneFavorite,
                SCENE_STATE_SET_FAVORITE_APP | FavoriteAppOkLong);
            scene_manager_next_scene(app->scene_manager, DesktopSettingsAppSceneFavorite);
            break;

        case DesktopSettingsHappyMode:
            scene_manager_next_scene(app->scene_manager, DesktopSettingsAppSceneHappyMode);
            break;

        default:
            break;
        }
        consumed = true;
    }
    return consumed;
}

void desktop_settings_scene_start_on_exit(void* context) {
    DesktopSettingsApp* app = context;
    variable_item_list_reset(app->variable_item_list);
    desktop_settings_save(&app->settings);

    Power* power = furi_record_open(RECORD_POWER);
    power_trigger_ui_update(power);
    furi_record_close(RECORD_POWER);
}
