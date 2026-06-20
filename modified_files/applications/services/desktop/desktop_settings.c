#include "desktop_settings.h"
#include "desktop_settings_filename.h"

#include <saved_struct.h>
#include <storage/storage.h>

#define TAG "DesktopSettings"

#define DESKTOP_SETTINGS_VER_17 (17)
#define DESKTOP_SETTINGS_VER_18 (18)
#define DESKTOP_SETTINGS_VER_19 (19)
#define DESKTOP_SETTINGS_VER    (20)

#define DESKTOP_SETTINGS_PATH  INT_PATH(DESKTOP_SETTINGS_FILE_NAME)
#define DESKTOP_SETTINGS_MAGIC (0x17)

typedef struct {
    uint32_t auto_lock_delay_ms;
    uint8_t usb_inhibit_auto_lock;
    uint8_t displayBatteryPercentage;
    uint8_t dummy_mode;
    uint8_t display_clock;
    FavoriteApp favorite_apps[FavoriteAppNumber];
    FavoriteApp dummy_apps[9];
} DesktopSettingsV17;

typedef struct {
    uint32_t auto_lock_delay_ms;
    uint8_t usb_inhibit_auto_lock;
    uint8_t displayBatteryPercentage;
    uint8_t display_clock;
    FavoriteApp favorite_apps[FavoriteAppNumber];
} DesktopSettingsV18;

static void desktop_settings_set_defaults(DesktopSettings* settings) {
    settings->menu_scroll_loop = MENU_SCROLL_LOOP_DEFAULT;
    settings->menu_scroll_anim = MENU_SCROLL_ANIM_DEFAULT;
    settings->menu_layout      = MENU_LAYOUT_DEFAULT;
    settings->passport_char    = PASSPORT_CHAR_DEFAULT;
}

void desktop_settings_load(DesktopSettings* settings) {
    furi_assert(settings);

    bool success = false;

    do {
        uint8_t version;
        if(!saved_struct_get_metadata(DESKTOP_SETTINGS_PATH, NULL, &version, NULL)) break;

        if(version == DESKTOP_SETTINGS_VER) {
            success = saved_struct_load(
                DESKTOP_SETTINGS_PATH,
                settings,
                sizeof(DesktopSettings),
                DESKTOP_SETTINGS_MAGIC,
                DESKTOP_SETTINGS_VER);

        } else if(version == DESKTOP_SETTINGS_VER_19) {
            // V19 = same as current minus passport_char — migrate with defaults
            typedef struct {
                uint32_t auto_lock_delay_ms;
                uint8_t usb_inhibit_auto_lock;
                uint8_t displayBatteryPercentage;
                uint8_t display_clock;
                FavoriteApp favorite_apps[FavoriteAppNumber];
                uint8_t menu_scroll_loop;
                uint8_t menu_scroll_anim;
                uint8_t menu_layout;
            } DesktopSettingsV19;
            DesktopSettingsV19* s19 = malloc(sizeof(DesktopSettingsV19));

            success = saved_struct_load(
                DESKTOP_SETTINGS_PATH,
                s19,
                sizeof(DesktopSettingsV19),
                DESKTOP_SETTINGS_MAGIC,
                DESKTOP_SETTINGS_VER_19);

            if(success) {
                settings->auto_lock_delay_ms       = s19->auto_lock_delay_ms;
                settings->usb_inhibit_auto_lock    = s19->usb_inhibit_auto_lock;
                settings->displayBatteryPercentage = s19->displayBatteryPercentage;
                settings->display_clock            = s19->display_clock;
                memcpy(settings->favorite_apps, s19->favorite_apps, sizeof(settings->favorite_apps));
                settings->menu_scroll_loop = s19->menu_scroll_loop;
                settings->menu_scroll_anim = s19->menu_scroll_anim;
                settings->menu_layout      = s19->menu_layout;
                settings->passport_char    = PASSPORT_CHAR_DEFAULT;
            }

            free(s19);

        } else if(version == DESKTOP_SETTINGS_VER_18) {
            DesktopSettingsV18* s18 = malloc(sizeof(DesktopSettingsV18));

            success = saved_struct_load(
                DESKTOP_SETTINGS_PATH,
                s18,
                sizeof(DesktopSettingsV18),
                DESKTOP_SETTINGS_MAGIC,
                DESKTOP_SETTINGS_VER_18);

            if(success) {
                settings->auto_lock_delay_ms     = s18->auto_lock_delay_ms;
                settings->usb_inhibit_auto_lock  = s18->usb_inhibit_auto_lock;
                settings->displayBatteryPercentage = s18->displayBatteryPercentage;
                settings->display_clock          = s18->display_clock;
                memcpy(settings->favorite_apps, s18->favorite_apps, sizeof(settings->favorite_apps));
                desktop_settings_set_defaults(settings);
            }

            free(s18);

        } else if(version > DESKTOP_SETTINGS_VER) {
            // Newer settings file (built by a future version) — use defaults rather than failing
            FURI_LOG_W(TAG, "Settings version %d > code version %d, resetting to defaults", version, DESKTOP_SETTINGS_VER);
            success = true;
            memset(settings, 0, sizeof(DesktopSettings));
            desktop_settings_set_defaults(settings);

        } else if(version == DESKTOP_SETTINGS_VER_17) {
            DesktopSettingsV17* s17 = malloc(sizeof(DesktopSettingsV17));

            success = saved_struct_load(
                DESKTOP_SETTINGS_PATH,
                s17,
                sizeof(DesktopSettingsV17),
                DESKTOP_SETTINGS_MAGIC,
                DESKTOP_SETTINGS_VER_17);

            if(success) {
                settings->auto_lock_delay_ms     = s17->auto_lock_delay_ms;
                settings->usb_inhibit_auto_lock  = s17->usb_inhibit_auto_lock;
                settings->displayBatteryPercentage = s17->displayBatteryPercentage;
                settings->display_clock          = s17->display_clock;
                memcpy(settings->favorite_apps, s17->favorite_apps, sizeof(settings->favorite_apps));
                desktop_settings_set_defaults(settings);
            }

            free(s17);
        }

    } while(false);

    if(!success) {
        FURI_LOG_W(TAG, "Failed to load file, using defaults");
        memset(settings, 0, sizeof(DesktopSettings));
        desktop_settings_set_defaults(settings);
        desktop_settings_save(settings);
    }
}

void desktop_settings_save(const DesktopSettings* settings) {
    furi_assert(settings);

    const bool success = saved_struct_save(
        DESKTOP_SETTINGS_PATH,
        settings,
        sizeof(DesktopSettings),
        DESKTOP_SETTINGS_MAGIC,
        DESKTOP_SETTINGS_VER);

    if(!success) {
        FURI_LOG_E(TAG, "Failed to save file");
    }
}
