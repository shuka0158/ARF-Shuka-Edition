#include <gui/scene_manager.h>
#include <gui/modules/popup.h>
#include <gui/icon.h>
#include <furi.h>

#include "desktop_scene.h"
#include "../desktop_i.h"

#define BOOT_TEXT_TIMEOUT_MS 2500

/*
 * Pixel-art car icon — 32×16 monochrome, XBM bit order (LSB first per byte).
 * Rendered on the left side of the boot popup alongside the text.
 *
 *  Shape (32×16):
 *    ....██████████████████....
 *    ...█▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓█...
 *    .██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██.
 *    █▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓█
 *    ████████████████████████
 *    █▓▒░.........░▒▓▓▒░.░▒▓█  (windows + side trim)
 *    █████████████████████████
 *    .██░░░░░░░░░░░░░░░░░░░██.
 *    ..████████████████████...
 *    ...░██░...........░██░...  (wheel arches)
 *    ..░████░.........░████░..
 *    ..░█  █░.........░█  █░..
 *    ..░████░.........░████░..
 *    ...░██░...........░██░...
 */
static const uint8_t arf_car_icon_data[] = {
    /* Row 0 */  0x00, 0xF8, 0xFF, 0x00,
    /* Row 1 */  0x00, 0xFC, 0xFF, 0x00,
    /* Row 2 */  0x80, 0xFF, 0xFF, 0x01,
    /* Row 3 */  0xFF, 0xFF, 0xFF, 0xFF,
    /* Row 4 */  0xFF, 0xFF, 0xFF, 0xFF,
    /* Row 5 */  0xFF, 0xC3, 0xC3, 0xFF,
    /* Row 6 */  0xFF, 0xFF, 0xFF, 0xFF,
    /* Row 7 */  0xFE, 0xFF, 0xFF, 0x7F,
    /* Row 8 */  0xFC, 0xFF, 0xFF, 0x3F,
    /* Row 9 */  0x38, 0xE0, 0x07, 0x1C,
    /* Row 10 */ 0x7C, 0xF0, 0x0F, 0x3E,
    /* Row 11 */ 0x64, 0xF0, 0x0F, 0x26,
    /* Row 12 */ 0x7C, 0xF0, 0x0F, 0x3E,
    /* Row 13 */ 0x38, 0xE0, 0x07, 0x1C,
    /* Row 14 */ 0x00, 0x00, 0x00, 0x00,
    /* Row 15 */ 0x00, 0x00, 0x00, 0x00,
};

static const Icon arf_car_icon = {
    .width = 32,
    .height = 16,
    .frame_count = 1,
    .frame_rate = 0,
    .frames = (const uint8_t* const[]){arf_car_icon_data},
};

void desktop_scene_boot_text_callback(void* context) {
    Desktop* desktop = (Desktop*)context;
    view_dispatcher_send_custom_event(desktop->view_dispatcher, DesktopBootTextExit);
}

void desktop_scene_boot_text_on_enter(void* context) {
    Desktop* desktop = (Desktop*)context;
    furi_assert(desktop);
    Popup* popup = desktop->popup;

    popup_set_context(popup, desktop);

    /* Car icon centred horizontally at top of popup */
    popup_set_icon(popup, 48, 4 + STATUS_BAR_Y_SHIFT, &arf_car_icon);

    popup_set_header(
        popup, "ARF Custom edition.", 64, 24 + STATUS_BAR_Y_SHIFT, AlignCenter, AlignBottom);
    popup_set_text(
        popup, "github: shuka0158", 64, 36 + STATUS_BAR_Y_SHIFT, AlignCenter, AlignCenter);

    popup_set_callback(popup, desktop_scene_boot_text_callback);
    popup_set_timeout(popup, BOOT_TEXT_TIMEOUT_MS);
    popup_enable_timeout(popup);
    view_dispatcher_switch_to_view(desktop->view_dispatcher, DesktopViewIdPopup);
}

bool desktop_scene_boot_text_on_event(void* context, SceneManagerEvent event) {
    Desktop* desktop = (Desktop*)context;
    bool consumed = false;

    if(event.type == SceneManagerEventTypeCustom) {
        if(event.event == DesktopBootTextExit) {
            scene_manager_previous_scene(desktop->scene_manager);
            consumed = true;
        }
    }
    return consumed;
}

void desktop_scene_boot_text_on_exit(void* context) {
    Desktop* desktop = (Desktop*)context;
    furi_assert(desktop);

    Popup* popup = desktop->popup;
    popup_disable_timeout(popup);
    popup_reset(popup);
}
