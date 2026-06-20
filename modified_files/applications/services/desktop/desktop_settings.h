#pragma once

#include <stdint.h>

#define DISPLAY_BATTERY_BAR              0
#define DISPLAY_BATTERY_PERCENT          1
#define DISPLAY_BATTERY_INVERTED_PERCENT 2
#define DISPLAY_BATTERY_RETRO_3          3
#define DISPLAY_BATTERY_RETRO_5          4
#define DISPLAY_BATTERY_BAR_PERCENT      5

#define MENU_SCROLL_LOOP_DEFAULT 1 // warp (current behaviour)
#define MENU_SCROLL_ANIM_DEFAULT 0 // instant
#define MENU_LAYOUT_DEFAULT      0 // list

// Passport character: 0=dolphin, 1=skull, 2=hacker, 3=robot
#define PASSPORT_CHAR_DEFAULT 0

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    FavoriteAppLeftShort,
    FavoriteAppLeftLong,
    FavoriteAppRightShort,
    FavoriteAppRightLong,
    FavoriteAppOkLong,

    FavoriteAppNumber,
} FavoriteAppShortcut;

typedef struct {
    char name_or_path[128];
} FavoriteApp;

typedef struct {
    uint32_t auto_lock_delay_ms;
    uint8_t usb_inhibit_auto_lock;
    uint8_t displayBatteryPercentage;
    uint8_t display_clock;
    FavoriteApp favorite_apps[FavoriteAppNumber];
    uint8_t menu_scroll_loop; // 0=linear (stop at ends), 1=warp (wrap around)
    uint8_t menu_scroll_anim; // 0=instant, 1=slide
    uint8_t menu_layout;      // 0=list, 1=grid
    uint8_t passport_char;    // 0=dolphin, 1=skull, 2=hacker, 3=robot
} DesktopSettings;

void desktop_settings_load(DesktopSettings* settings);
void desktop_settings_save(const DesktopSettings* settings);

#ifdef __cplusplus
}
#endif
