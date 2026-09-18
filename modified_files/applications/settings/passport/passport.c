#include <furi.h>
#include <gui/gui.h>
#include <input/input.h>
#include <stdlib.h>
#include <string.h>

#include <assets_icons.h>
#include <dolphin/dolphin.h>
#include <dolphin/helpers/dolphin_state.h>
#include <furi_hal_version.h>
#include <desktop/desktop_settings.h>

// Mood buckets, mirroring how the rest of the firmware reads butthurt
// (0..BUTTHURT_MAX==14): low butthurt = happy, high = bad.
#define MOOD_HAPPY_MAX 4
#define MOOD_OKAY_MAX  9

typedef struct {
    uint8_t level; // 1..3, matches dolphin_get_level() / passport_*N_46x49 variants
    uint8_t mood; // 0=happy, 1=okay, 2=bad
    uint8_t passport_char; // 0=dolphin, 1=skull, 2=neuromancer, 3=robot
    const char* name; // furi_hal_version_get_name_ptr() — static buffer, lives for app lifetime
    uint32_t xp_above; // XP earned since the last level-up
    uint32_t xp_span; // xp_above + xp still needed for this level; 0 at max level
} PassportModel;

static const char* mood_text(uint8_t mood) {
    switch(mood) {
    case 0:
        return "Happy";
    case 1:
        return "Okay";
    default:
        return "Grumpy";
    }
}

static const Icon* passport_icon(const PassportModel* m) {
    // Built-in dolphin art scales with level (1/2/3); the custom characters
    // only ship one style per mood (real art, see assets/passport_chars/),
    // so they don't vary with level.
    switch(m->passport_char) {
    case 1: // skull
        switch(m->mood) {
        case 0:
            return &I_skull_happy1_46x49;
        case 1:
            return &I_skull_okay1_46x49;
        default:
            return &I_skull_bad1_46x49;
        }
    case 2: // neuromancer (internal symbols kept as I_hacker_* — cosmetic label only)
        switch(m->mood) {
        case 0:
            return &I_hacker_happy1_46x49;
        case 1:
            return &I_hacker_okay1_46x49;
        default:
            return &I_hacker_bad1_46x49;
        }
    case 3: // robot
        switch(m->mood) {
        case 0:
            return &I_robot_happy1_46x49;
        case 1:
            return &I_robot_okay1_46x49;
        default:
            return &I_robot_bad1_46x49;
        }
    default: // dolphin
        switch(m->mood) {
        case 0:
            switch(m->level) {
            case 2:
                return &I_passport_happy2_46x49;
            case 3:
                return &I_passport_happy3_46x49;
            default:
                return &I_passport_happy1_46x49;
            }
        case 1:
            switch(m->level) {
            case 2:
                return &I_passport_okay2_46x49;
            case 3:
                return &I_passport_okay3_46x49;
            default:
                return &I_passport_okay1_46x49;
            }
        default:
            switch(m->level) {
            case 2:
                return &I_passport_bad2_46x49;
            case 3:
                return &I_passport_bad3_46x49;
            default:
                return &I_passport_bad1_46x49;
            }
        }
    }
}

static void passport_draw_callback(Canvas* canvas, void* ctx) {
    const PassportModel* m = ctx;

    canvas_clear(canvas);
    canvas_set_color(canvas, ColorBlack);

    // Same three-piece layout as stock Flipper passport: character icon,
    // the booklet's perforated divider, and the bottom stamp strip with
    // its "Lvl." badge — using ARF's own (unused until now) passport_left
    // and passport_bottom assets instead of a hand-rolled frame.
    canvas_draw_icon(canvas, 0, 0, passport_icon(m));
    canvas_draw_icon(canvas, 46, 0, &I_passport_left_6x46);
    canvas_draw_icon(canvas, 0, 46, &I_passport_bottom_128x18);

    canvas_set_font(canvas, FontPrimary);
    canvas_draw_str(canvas, 54, 11, m->name ? m->name : "Flipper");

    canvas_set_font(canvas, FontSecondary);
    FuriString* mood = furi_string_alloc_printf("Mood: %s", mood_text(m->mood));
    canvas_draw_str(canvas, 54, 23, furi_string_get_cstr(mood));
    furi_string_free(mood);

    // XP bar toward next level. At max level (dolphin ships preset there,
    // see patch_dolphin_level.py) xp_span is 0 — a "full" bar would render
    // as another solid black rectangle sitting right above the equally
    // solid black Lvl. badge below, reading as a glitchy duplicate rather
    // than two distinct elements, so leave it as an empty outline instead.
    const uint8_t bar_x = 54, bar_y = 30, bar_w = 70, bar_h = 6;
    canvas_draw_frame(canvas, bar_x, bar_y, bar_w, bar_h);
    if(m->xp_span > 0) {
        uint8_t fill = (uint8_t)(((uint64_t)m->xp_above * (bar_w - 2)) / m->xp_span);
        if(fill > 0) {
            canvas_draw_box(canvas, bar_x + 1, bar_y + 1, fill, bar_h - 2);
        }
    }

    canvas_set_color(canvas, ColorWhite);
    FuriString* lvl = furi_string_alloc_printf("Lvl. %u", m->level);
    canvas_draw_str(canvas, 65, 53, furi_string_get_cstr(lvl));
    furi_string_free(lvl);
}

static void passport_input_callback(InputEvent* input_event, void* ctx) {
    FuriMessageQueue* event_queue = ctx;
    furi_message_queue_put(event_queue, input_event, FuriWaitForever);
}

int32_t passport_app(void* p) {
    UNUSED(p);

    PassportModel model = {0};

    Dolphin* dolphin = furi_record_open(RECORD_DOLPHIN);
    DolphinStats stats = dolphin_stats(dolphin);
    furi_record_close(RECORD_DOLPHIN);

    model.level = stats.level;
    model.mood = (stats.butthurt <= MOOD_HAPPY_MAX) ? 0 :
                 (stats.butthurt <= MOOD_OKAY_MAX)   ? 1 :
                                                        2;
    model.name = furi_hal_version_get_name_ptr();
    model.xp_above = dolphin_state_xp_above_last_levelup(stats.icounter);
    uint32_t xp_to_go = dolphin_state_xp_to_levelup(stats.icounter);
    model.xp_span = (model.level >= 3) ? 0 : (model.xp_above + xp_to_go);

    // Heap-allocated: DesktopSettings is ~650 bytes (5x 128-byte favorite-app
    // slots) and this app's stack is small — a stack-local copy here caused
    // an MPU fault (stack overflow) on real hardware.
    DesktopSettings* settings = malloc(sizeof(DesktopSettings));
    memset(settings, 0, sizeof(DesktopSettings));
    desktop_settings_load(settings);
    model.passport_char = settings->passport_char;
    free(settings);

    FuriMessageQueue* event_queue = furi_message_queue_alloc(8, sizeof(InputEvent));

    ViewPort* view_port = view_port_alloc();
    view_port_draw_callback_set(view_port, passport_draw_callback, &model);
    view_port_input_callback_set(view_port, passport_input_callback, event_queue);

    Gui* gui = furi_record_open(RECORD_GUI);
    gui_add_view_port(gui, view_port, GuiLayerFullscreen);

    InputEvent event;
    bool running = true;
    while(running) {
        if(furi_message_queue_get(event_queue, &event, FuriWaitForever) == FuriStatusOk) {
            if(event.type == InputTypePress && event.key == InputKeyBack) {
                running = false;
            }
        }
    }

    gui_remove_view_port(gui, view_port);
    furi_record_close(RECORD_GUI);
    view_port_free(view_port);
    furi_message_queue_free(event_queue);

    return 0;
}
