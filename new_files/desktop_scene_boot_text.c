#include <gui/scene_manager.h>
#include <furi.h>

#include "desktop_scene.h"
#include "../desktop_i.h"

#define BOOT_TEXT_TIMEOUT_MS 2500

void desktop_scene_boot_text_callback(void* context) {
    Desktop* desktop = (Desktop*)context;
    view_dispatcher_send_custom_event(desktop->view_dispatcher, DesktopBootTextExit);
}

void desktop_scene_boot_text_on_enter(void* context) {
    Desktop* desktop = (Desktop*)context;
    furi_assert(desktop);
    Popup* popup = desktop->popup;

    popup_set_context(popup, desktop);
    popup_set_header(
        popup, "ARF Custom edition.", 64, 14 + STATUS_BAR_Y_SHIFT, AlignCenter, AlignBottom);
    popup_set_text(
        popup, "GitHub: shuka0158", 64, 36 + STATUS_BAR_Y_SHIFT, AlignCenter, AlignCenter);
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
