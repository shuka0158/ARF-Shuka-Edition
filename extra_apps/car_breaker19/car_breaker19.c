#include <furi.h>
#include <furi_hal.h>
#include <furi/core/kernel.h>
#include <furi/core/timer.h>
#include <gui/gui.h>
#include <gui/view.h>
#include <gui/view_dispatcher.h>
#include <gui/elements.h>
#include <gui/modules/submenu.h>
#include <gui/modules/variable_item_list.h>
#include <gui/modules/dialog_ex.h>
#include <input/input.h>
#include <lib/subghz/subghz_worker.h>
#include <toolbox/crc32_calc.h>
#include <notification/notification_messages.h>

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#include "scenes/car_breaker19_scene_about.h"

#define TAG "CarBreaker19"

#define CAR_BREAKER_MAX_PULSES 512
#define CAR_BREAKER_MAX_FRAMES 512
#define CAR_BREAKER_MIN_PULSES 32
#define CAR_BREAKER_PACKET_GAP_US 4000
#define CAR_BREAKER_MAX_PULSE_US 30000
#define CAR_BREAKER_ROLLING_WINDOW_MS 2500
#define CAR_BREAKER_ROLLBACK_GAP_MS 8000
#define CAR_BREAKER_STATUS_MSG_LEN 64
#define KEY_DEBOUNCE_MS 300
#define CAR_BREAKER_HOP_INTERVAL_MS 500
#define CAR_BREAKER_PRESET_HOPPING 0
#define CAR_BREAKER_ROLLING_SEQUENCE_LEN 5
#define CAR_BREAKER_MIN_FRAME_BITS 40
#define CAR_BREAKER_MAX_FRAME_BITS 160
#define CAR_BREAKER_MIN_FRAME_DURATION_US 3000
#define CAR_BREAKER_MAX_FRAME_DURATION_US 14000
#define CAR_BREAKER_CONSISTENCY_TOLERANCE_PERCENT 18

typedef struct CarBreakerApp CarBreakerApp;

typedef struct {
    uint32_t duration;
    uint8_t level;
} CarBreakerPulse;

typedef struct {
    uint32_t timestamp_ms;
    uint32_t hash;
    uint16_t pulse_count;
    uint16_t approx_bits;
    uint32_t duration_us;
    uint8_t preset_index;
} CarBreakerFrame;

typedef struct {
    CarBreakerFrame frames[CAR_BREAKER_MAX_FRAMES];
    size_t count;
} CarBreakerSession;

typedef struct {
    bool static_code_detected;
    uint32_t static_hash;
    uint32_t static_first_ms;
    uint32_t static_second_ms;
    bool rollback_detected;
    uint32_t rollback_hash;
    uint32_t rollback_gap_ms;
    bool rolling_pwn_detected;
    uint32_t rolling_window_ms;
} CarBreakerAnalysis;

typedef struct {
    const char* name;
    uint32_t frequency;
    const uint8_t* regs;
    size_t regs_size;
    const char* description;
} CarBreakerPreset;

static void car_breaker_stop_capture(CarBreakerApp* app);

static const uint8_t car_breaker_preset_hnd1[] = {
    0x02, 0x0D, 0x0B, 0x06, 0x08, 0x32, 0x07, 0x04, 0x14, 0x00, 0x13, 0x02,
    0x12, 0x04, 0x11, 0x36, 0x10, 0x69, 0x15, 0x32, 0x18, 0x18, 0x19, 0x16,
    0x1D, 0x91, 0x1C, 0x00, 0x1B, 0x07, 0x20, 0xFB, 0x22, 0x10, 0x21, 0x56,
    0x00, 0x00, 0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
};

static const uint8_t car_breaker_preset_hnd2[] = {
    0x02, 0x0D, 0x0B, 0x06, 0x08, 0x32, 0x07, 0x04, 0x14, 0x00, 0x13, 0x02,
    0x12, 0x07, 0x11, 0x36, 0x10, 0xE9, 0x15, 0x32, 0x18, 0x18, 0x19, 0x16,
    0x1D, 0x92, 0x1C, 0x40, 0x1B, 0x03, 0x20, 0xFB, 0x22, 0x10, 0x21, 0x56,
    0x00, 0x00, 0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
};

typedef enum {
    CarBreakerModeHopping = 0,
    CarBreakerMode433,
    CarBreakerMode315,
} CarBreakerMode;

typedef enum {
    CarBreakerFilterWide = 0,
    CarBreakerFilterNarrow,
} CarBreakerFilter;

static const char* car_breaker_mode_names[] = {"Hopping", "433.92 MHz", "315 MHz"};
static const char* car_breaker_filter_names[] = {"Wide", "Narrow"};

static const CarBreakerPreset car_breaker_presets[] = {
    {
        .name = "433 Wide",
        .frequency = 433920000,
        .regs = car_breaker_preset_hnd1,
        .regs_size = sizeof(car_breaker_preset_hnd1),
        .description = "433.92 MHz wide filter",
    },
    {
        .name = "433 Narrow",
        .frequency = 433920000,
        .regs = car_breaker_preset_hnd2,
        .regs_size = sizeof(car_breaker_preset_hnd2),
        .description = "433.92 MHz narrow filter",
    },
    {
        .name = "315 Wide",
        .frequency = 315000000,
        .regs = car_breaker_preset_hnd1,
        .regs_size = sizeof(car_breaker_preset_hnd1),
        .description = "315 MHz wide filter",
    },
    {
        .name = "315 Narrow",
        .frequency = 315000000,
        .regs = car_breaker_preset_hnd2,
        .regs_size = sizeof(car_breaker_preset_hnd2),
        .description = "315 MHz narrow filter",
    },
};

#define CAR_BREAKER_PRESETS_COUNT (COUNT_OF(car_breaker_presets))

typedef enum {
    CarBreakerViewSplash,
    CarBreakerViewMenu,
    CarBreakerViewConfig,
    CarBreakerViewCapture,
    CarBreakerViewAbout,
} CarBreakerView;

typedef enum {
    CarBreakerMenuStart,
    CarBreakerMenuConfig,
    CarBreakerMenuAbout,
} CarBreakerMenuIndex;

struct CarBreakerApp {
    Gui* gui;
    ViewDispatcher* view_dispatcher;
    Submenu* submenu;
    VariableItemList* config_list;
    DialogEx* splash_dialog;
    DialogEx* capture_dialog;
    View* about_view;
    NotificationApp* notifications;
    char capture_header[40];
    char capture_text[128];

    FuriMutex* lock;
    SubGhzWorker* worker;
    FuriTimer* ui_timer;
    FuriTimer* hop_timer;

    CarBreakerSession session;
    CarBreakerAnalysis analysis;
    CarBreakerPulse pulses[CAR_BREAKER_MAX_PULSES];
    uint16_t pulse_count;

    CarBreakerMode mode;
    CarBreakerFilter filter;
    uint8_t current_preset_index;
    bool capturing;
    bool capture_dirty;
    bool overrun;
    bool is_view_transitioning;
    uint32_t last_key_event_time;
    char status_message[CAR_BREAKER_STATUS_MSG_LEN];
    CarBreakerView active_view;
};

static uint8_t car_breaker_get_preset_index(CarBreakerMode mode, CarBreakerFilter filter) {
    if(mode == CarBreakerMode433) {
        return (filter == CarBreakerFilterWide) ? 0 : 1;
    } else {
        return (filter == CarBreakerFilterWide) ? 2 : 3;
    }
}

static bool car_breaker_is_key_debounced(CarBreakerApp* app) {
    if(!app) return false;
    uint32_t current_time = furi_get_tick();
    if(current_time - app->last_key_event_time < KEY_DEBOUNCE_MS) {
        return false;
    }
    app->last_key_event_time = current_time;
    return true;
}

static void car_breaker_safe_switch_view(CarBreakerApp* app, CarBreakerView view) {
    if(!app || !app->view_dispatcher) return;
    if(app->is_view_transitioning) return;

    app->is_view_transitioning = true;
    app->active_view = view;
    view_dispatcher_switch_to_view(app->view_dispatcher, view);
    app->is_view_transitioning = false;
}

static void car_breaker_update_status(CarBreakerApp* app, const char* text) {
    furi_check(app);
    if(!text) return;
    furi_mutex_acquire(app->lock, FuriWaitForever);
    snprintf(app->status_message, CAR_BREAKER_STATUS_MSG_LEN, "%s", text);
    app->capture_dirty = true;
    furi_mutex_release(app->lock);
}

static uint32_t car_breaker_hash_pulses(const CarBreakerPulse* pulses, size_t count) {
    uint32_t crc = 0;
    for(size_t i = 0; i < count; i++) {
        crc = crc32_calc_buffer(crc, &pulses[i].duration, sizeof(pulses[i].duration));
        crc = crc32_calc_buffer(crc, &pulses[i].level, sizeof(pulses[i].level));
    }
    return crc;
}

static void car_breaker_reset_session_locked(CarBreakerApp* app) {
    app->session.count = 0;
    memset(&app->analysis, 0, sizeof(app->analysis));
    app->pulse_count = 0;
    app->capture_dirty = true;
}

static bool car_breaker_frame_is_valid(const CarBreakerFrame* frame) {
    if(!frame) return false;
    if(frame->approx_bits < CAR_BREAKER_MIN_FRAME_BITS ||
       frame->approx_bits > CAR_BREAKER_MAX_FRAME_BITS) {
        return false;
    }
    if(frame->duration_us < CAR_BREAKER_MIN_FRAME_DURATION_US ||
       frame->duration_us > CAR_BREAKER_MAX_FRAME_DURATION_US) {
        return false;
    }
    return true;
}

static uint32_t car_breaker_percent_delta(uint32_t baseline, uint32_t value) {
    if(baseline == 0) return UINT32_MAX;
    uint32_t diff = (baseline > value) ? (baseline - value) : (value - baseline);
    return (diff * 100u) / baseline;
}

static bool car_breaker_frames_consistent(
    const CarBreakerFrame* reference,
    const CarBreakerFrame* candidate) {
    if(!reference || !candidate) return false;
    if(!car_breaker_frame_is_valid(reference) || !car_breaker_frame_is_valid(candidate)) {
        return false;
    }
    if(reference->preset_index != candidate->preset_index) {
        return false;
    }

    uint32_t duration_delta =
        car_breaker_percent_delta(reference->duration_us, candidate->duration_us);
    uint32_t bit_delta = car_breaker_percent_delta(reference->approx_bits, candidate->approx_bits);

    if(duration_delta > CAR_BREAKER_CONSISTENCY_TOLERANCE_PERCENT) return false;
    if(bit_delta > CAR_BREAKER_CONSISTENCY_TOLERANCE_PERCENT) return false;
    return true;
}

static void car_breaker_recompute_analysis_locked(CarBreakerApp* app) {
    CarBreakerAnalysis updated = {0};
    const CarBreakerSession* session = &app->session;

    for(size_t idx = 0; idx < session->count; idx++) {
        const CarBreakerFrame* frame = &session->frames[idx];
        const bool frame_valid = car_breaker_frame_is_valid(frame);

        if(!updated.rolling_pwn_detected &&
           (idx + 1u) >= CAR_BREAKER_ROLLING_SEQUENCE_LEN &&
           frame_valid) {
            size_t start_idx = idx + 1 - CAR_BREAKER_ROLLING_SEQUENCE_LEN;
            const CarBreakerFrame* start_frame = &session->frames[start_idx];
            if(car_breaker_frame_is_valid(start_frame)) {
                uint32_t window = frame->timestamp_ms - start_frame->timestamp_ms;
                if(window <= CAR_BREAKER_ROLLING_WINDOW_MS) {
                    bool consistent = true;
                    bool unique_hashes = true;

                    for(size_t i = start_idx; i <= idx && consistent; i++) {
                        const CarBreakerFrame* candidate = &session->frames[i];
                        if(!car_breaker_frames_consistent(start_frame, candidate)) {
                            consistent = false;
                        }
                    }

                    if(consistent) {
                        for(size_t i = start_idx; i < idx && unique_hashes; i++) {
                            for(size_t j = i + 1; j <= idx && unique_hashes; j++) {
                                if(session->frames[i].hash == session->frames[j].hash) {
                                    unique_hashes = false;
                                }
                            }
                        }
                    }

                    if(consistent && unique_hashes) {
                        updated.rolling_pwn_detected = true;
                        updated.rolling_window_ms = window;
                    }
                }
            }
        }

        if(!frame_valid) continue;

        for(size_t older_idx = 0; older_idx < idx; older_idx++) {
            const CarBreakerFrame* older = &session->frames[older_idx];
            if(older->hash != frame->hash) continue;
            if(!car_breaker_frames_consistent(frame, older)) continue;

            uint32_t gap = frame->timestamp_ms - older->timestamp_ms;
            if(!updated.static_code_detected) {
                updated.static_code_detected = true;
                updated.static_hash = frame->hash;
                updated.static_first_ms = older->timestamp_ms;
                updated.static_second_ms = frame->timestamp_ms;
            }
            if(!updated.rollback_detected && gap >= CAR_BREAKER_ROLLBACK_GAP_MS) {
                updated.rollback_detected = true;
                updated.rollback_hash = frame->hash;
                updated.rollback_gap_ms = gap;
            }
        }
    }

    app->analysis = updated;
}

static void car_breaker_finalize_frame_locked(CarBreakerApp* app) {
    if(app->pulse_count < CAR_BREAKER_MIN_PULSES) {
        app->pulse_count = 0;
        return;
    }

    CarBreakerSession* session = &app->session;
    if(session->count >= CAR_BREAKER_MAX_FRAMES) {
        memmove(
            &session->frames[0],
            &session->frames[1],
            (CAR_BREAKER_MAX_FRAMES - 1) * sizeof(CarBreakerFrame));
        session->count = CAR_BREAKER_MAX_FRAMES - 1;
    }

    CarBreakerFrame* frame = &session->frames[session->count++];
    frame->timestamp_ms = furi_get_tick();
    frame->pulse_count = app->pulse_count;
    frame->hash = car_breaker_hash_pulses(app->pulses, app->pulse_count);
    frame->preset_index = app->current_preset_index;

    uint64_t duration_sum = 0;
    for(size_t i = 0; i < app->pulse_count; i++) {
        duration_sum += app->pulses[i].duration;
    }
    if(duration_sum > UINT32_MAX) duration_sum = UINT32_MAX;
    frame->duration_us = (uint32_t)duration_sum;
    frame->approx_bits = (uint16_t)(duration_sum / 65);
    if(frame->approx_bits == 0) {
        frame->approx_bits = 1;
    }

    app->pulse_count = 0;
    app->capture_dirty = true;
    car_breaker_recompute_analysis_locked(app);
}

static void car_breaker_worker_overrun_callback(void* context) {
    CarBreakerApp* app = context;
    app->overrun = true;
}

static void car_breaker_worker_pair_callback(void* context, bool level, uint32_t duration) {
    CarBreakerApp* app = context;
    if(!app->capturing) return;

    if(duration > CAR_BREAKER_MAX_PULSE_US) duration = CAR_BREAKER_MAX_PULSE_US;

    furi_mutex_acquire(app->lock, FuriWaitForever);

    if(app->pulse_count >= CAR_BREAKER_MAX_PULSES) {
        car_breaker_finalize_frame_locked(app);
    }

    if(app->pulse_count < CAR_BREAKER_MAX_PULSES) {
        CarBreakerPulse* pulse = &app->pulses[app->pulse_count++];
        pulse->duration = duration;
        pulse->level = level ? 1 : 0;
    }

    if(!level && duration >= CAR_BREAKER_PACKET_GAP_US) {
        car_breaker_finalize_frame_locked(app);
    }

    furi_mutex_release(app->lock);
}

static void car_breaker_update_capture_display(CarBreakerApp* app) {
    size_t frame_count = 0;
    CarBreakerAnalysis analysis = {0};
    bool capturing = false;

    furi_mutex_acquire(app->lock, FuriWaitForever);
    frame_count = app->session.count;
    analysis = app->analysis;
    capturing = app->capturing;
    furi_mutex_release(app->lock);

    bool any_detected = analysis.static_code_detected ||
                        analysis.rollback_detected ||
                        analysis.rolling_pwn_detected;

    if(capturing && any_detected) {
        car_breaker_stop_capture(app);
        capturing = false;
    }

    // Header is just "Scanning"
    dialog_ex_set_header(app->capture_dialog, "Scanning", 64, 2, AlignCenter, AlignTop);

    char* ptr = app->capture_text;
    size_t remaining = sizeof(app->capture_text);
    int written = 0;

    // First line: Mode
    written = snprintf(ptr, remaining, "Mode: %s\n", car_breaker_presets[app->current_preset_index].name);
    ptr += written;
    remaining -= written;

    if(any_detected) {
        if(analysis.rolling_pwn_detected && remaining > 0) {
            written = snprintf(ptr, remaining, "Rolling-Pwn DETECTED!\n");
            ptr += written;
            remaining -= written;
            if(analysis.rolling_window_ms && remaining > 0) {
                written = snprintf(
                    ptr,
                    remaining,
                    "Window: %lums\n",
                    (unsigned long)analysis.rolling_window_ms);
                ptr += written;
                remaining -= written;
            }
        }
        if(analysis.rollback_detected && remaining > 0) {
            written = snprintf(ptr, remaining, "RollBack SUSPECT!\n");
            ptr += written;
            remaining -= written;
        }
        if(analysis.static_code_detected && remaining > 0) {
            snprintf(ptr, remaining, "Static Code DETECTED!");
        }
    } else {
        if(remaining > 0) {
            written = snprintf(
                ptr,
                remaining,
                "Frame Buffer %u/%u\n",
                (unsigned)frame_count,
                (unsigned)CAR_BREAKER_MAX_FRAMES);
            ptr += written;
            remaining -= written;
        }
        if(frame_count == 0) {
            snprintf(ptr, remaining, "Waiting for signal...");
        } else {
            snprintf(ptr, remaining, "Analyzing...");
        }
    }

    dialog_ex_set_text(app->capture_dialog, app->capture_text, 64, 32, AlignCenter, AlignCenter);
}

static void car_breaker_ui_timer_callback(void* context) {
    CarBreakerApp* app = context;
    bool dirty = false;

    furi_mutex_acquire(app->lock, FuriWaitForever);
    dirty = app->capture_dirty;
    app->capture_dirty = false;
    furi_mutex_release(app->lock);

    if(dirty && app->active_view == CarBreakerViewCapture) {
        car_breaker_update_capture_display(app);
    }
}

static void car_breaker_apply_preset(CarBreakerApp* app, uint8_t preset_idx) {
    if(preset_idx >= CAR_BREAKER_PRESETS_COUNT) {
        return;
    }

    if(subghz_worker_is_running(app->worker)) {
        subghz_worker_stop(app->worker);
        furi_hal_subghz_stop_async_rx();
    }
    furi_hal_subghz_idle();

    const CarBreakerPreset* preset = &car_breaker_presets[preset_idx];
    furi_hal_subghz_load_custom_preset(preset->regs);
    furi_hal_subghz_set_frequency_and_path(preset->frequency);
    furi_hal_subghz_flush_rx();
    furi_hal_subghz_rx();

    furi_hal_subghz_start_async_rx(subghz_worker_rx_callback, app->worker);
    subghz_worker_start(app->worker);

    app->current_preset_index = preset_idx;
    app->capture_dirty = true;
}

static void car_breaker_hop_timer_callback(void* context) {
    CarBreakerApp* app = context;
    if(!app->capturing) return;

    uint8_t next_idx = app->current_preset_index + 1;
    if(next_idx >= CAR_BREAKER_PRESETS_COUNT) {
        next_idx = 0;
    }

    car_breaker_apply_preset(app, next_idx);
}

static void car_breaker_start_capture(CarBreakerApp* app) {
    if(app->capturing) return;

    car_breaker_update_status(app, "Listening...");
    dialog_ex_set_center_button_text(app->capture_dialog, "Stop");

    furi_hal_subghz_reset();
    furi_hal_subghz_idle();

    subghz_worker_set_context(app->worker, app);
    subghz_worker_set_pair_callback(app->worker, car_breaker_worker_pair_callback);
    subghz_worker_set_overrun_callback(app->worker, car_breaker_worker_overrun_callback);

    if(app->mode == CarBreakerModeHopping) {
        app->current_preset_index = 0;
        car_breaker_apply_preset(app, app->current_preset_index);

        if(!app->hop_timer) {
            app->hop_timer =
                furi_timer_alloc(car_breaker_hop_timer_callback, FuriTimerTypePeriodic, app);
        }
        furi_timer_start(app->hop_timer, furi_ms_to_ticks(CAR_BREAKER_HOP_INTERVAL_MS));
    } else {
        uint8_t preset_idx = car_breaker_get_preset_index(app->mode, app->filter);
        app->current_preset_index = preset_idx;
        const CarBreakerPreset* preset = &car_breaker_presets[preset_idx];
        furi_hal_subghz_load_custom_preset(preset->regs);
        furi_hal_subghz_set_frequency_and_path(preset->frequency);
        furi_hal_subghz_flush_rx();
        furi_hal_subghz_rx();

        furi_hal_subghz_start_async_rx(subghz_worker_rx_callback, app->worker);
        subghz_worker_start(app->worker);
    }

    app->pulse_count = 0;
    app->capturing = true;
    app->overrun = false;

    if(!app->ui_timer) {
        app->ui_timer =
            furi_timer_alloc(car_breaker_ui_timer_callback, FuriTimerTypePeriodic, app);
    }
    furi_timer_start(app->ui_timer, furi_ms_to_ticks(250));
}

static void car_breaker_stop_capture(CarBreakerApp* app) {
    if(!app->capturing) return;

    if(app->hop_timer) {
        furi_timer_stop(app->hop_timer);
    }

    if(subghz_worker_is_running(app->worker)) {
        subghz_worker_stop(app->worker);
        furi_hal_subghz_stop_async_rx();
    }
    furi_hal_subghz_idle();

    app->capturing = false;
    if(app->ui_timer) {
        furi_timer_stop(app->ui_timer);
    }
    car_breaker_update_status(app, "Capture paused");
    dialog_ex_set_center_button_text(app->capture_dialog, "Back");
}


static void car_breaker_capture_callback(DialogExResult result, void* context) {
    CarBreakerApp* app = context;
    if(result == DialogExResultCenter) {
        // Stop button pressed
        car_breaker_stop_capture(app);
        // Reset session for next scan
        furi_mutex_acquire(app->lock, FuriWaitForever);
        car_breaker_reset_session_locked(app);
        furi_mutex_release(app->lock);
        car_breaker_safe_switch_view(app, CarBreakerViewMenu);
    }
}

static uint32_t car_breaker_capture_back_callback(void* context) {
    CarBreakerApp* app = context;
    car_breaker_stop_capture(app);
    // Reset session for next scan
    furi_mutex_acquire(app->lock, FuriWaitForever);
    car_breaker_reset_session_locked(app);
    furi_mutex_release(app->lock);
    return CarBreakerViewMenu;
}


static uint32_t car_breaker_splash_previous_callback(void* context) {
    UNUSED(context);
    return CarBreakerViewSplash;
}

static uint32_t car_breaker_menu_previous_callback(void* context) {
    UNUSED(context);
    return VIEW_NONE;
}

static uint32_t car_breaker_view_previous_callback(void* context) {
    UNUSED(context);
    return CarBreakerViewMenu;
}

static VariableItem* car_breaker_filter_item = NULL;

static void car_breaker_config_mode_changed(VariableItem* item) {
    CarBreakerApp* app = variable_item_get_context(item);
    uint8_t index = variable_item_get_current_value_index(item);
    if(index > CarBreakerMode315) index = CarBreakerModeHopping;
    app->mode = index;
    variable_item_set_current_value_text(item, car_breaker_mode_names[index]);

    if(car_breaker_filter_item) {
        if(index == CarBreakerModeHopping) {
            variable_item_set_current_value_text(car_breaker_filter_item, "N/A");
        } else {
            variable_item_set_current_value_text(car_breaker_filter_item, car_breaker_filter_names[app->filter]);
        }
    }
}

static void car_breaker_config_filter_changed(VariableItem* item) {
    CarBreakerApp* app = variable_item_get_context(item);
    if(app->mode == CarBreakerModeHopping) {
        variable_item_set_current_value_text(item, "N/A");
        return;
    }
    uint8_t index = variable_item_get_current_value_index(item);
    if(index > CarBreakerFilterNarrow) index = CarBreakerFilterWide;
    app->filter = index;
    variable_item_set_current_value_text(item, car_breaker_filter_names[index]);
}


static void car_breaker_splash_callback(DialogExResult result, void* context) {
    CarBreakerApp* app = context;
    UNUSED(result);
    car_breaker_safe_switch_view(app, CarBreakerViewMenu);
}

static void car_breaker_submenu_callback(void* context, uint32_t index) {
    CarBreakerApp* app = context;

    if(!car_breaker_is_key_debounced(app)) return;

    switch(index) {
    case CarBreakerMenuStart:
        car_breaker_start_capture(app);
        car_breaker_safe_switch_view(app, CarBreakerViewCapture);
        break;
    case CarBreakerMenuConfig:
        car_breaker_safe_switch_view(app, CarBreakerViewConfig);
        break;
    case CarBreakerMenuAbout:
        car_breaker_safe_switch_view(app, CarBreakerViewAbout);
        break;
    default:
        break;
    }
}

static CarBreakerApp* car_breaker_alloc(void) {
    CarBreakerApp* app = malloc(sizeof(CarBreakerApp));
    memset(app, 0, sizeof(CarBreakerApp));

    app->lock = furi_mutex_alloc(FuriMutexTypeNormal);
    app->worker = subghz_worker_alloc();
    app->mode = CarBreakerModeHopping;
    app->filter = CarBreakerFilterWide;
    snprintf(app->status_message, sizeof(app->status_message), "Ready");

    app->gui = furi_record_open(RECORD_GUI);
    app->notifications = furi_record_open(RECORD_NOTIFICATION);

    app->view_dispatcher = view_dispatcher_alloc();
    view_dispatcher_attach_to_gui(app->view_dispatcher, app->gui, ViewDispatcherTypeFullscreen);

    // Splash dialog
    app->splash_dialog = dialog_ex_alloc();
    dialog_ex_set_header(app->splash_dialog, "Car Breaker 19", 64, 3, AlignCenter, AlignTop);
    dialog_ex_set_text(
        app->splash_dialog,
        "Passive Honda RKE analyzer\nDetect Rolling-Pwn, RollBack,\nand static-code risks.",
        64,
        32,
        AlignCenter,
        AlignCenter);
    dialog_ex_set_center_button_text(app->splash_dialog, "Continue");
    dialog_ex_set_context(app->splash_dialog, app);
    dialog_ex_set_result_callback(app->splash_dialog, car_breaker_splash_callback);
    view_set_previous_callback(dialog_ex_get_view(app->splash_dialog), car_breaker_splash_previous_callback);
    view_dispatcher_add_view(
        app->view_dispatcher, CarBreakerViewSplash, dialog_ex_get_view(app->splash_dialog));

    app->submenu = submenu_alloc();
    submenu_set_header(app->submenu, "Car Breaker 19");
    submenu_add_item(
        app->submenu, "Start Capture", CarBreakerMenuStart, car_breaker_submenu_callback, app);
    submenu_add_item(
        app->submenu, "Config", CarBreakerMenuConfig, car_breaker_submenu_callback, app);
    submenu_add_item(
        app->submenu, "About", CarBreakerMenuAbout, car_breaker_submenu_callback, app);
    view_set_previous_callback(submenu_get_view(app->submenu), car_breaker_menu_previous_callback);
    view_dispatcher_add_view(
        app->view_dispatcher, CarBreakerViewMenu, submenu_get_view(app->submenu));

    app->config_list = variable_item_list_alloc();
    variable_item_list_set_header(app->config_list, "Capture Options");

    VariableItem* mode_item = variable_item_list_add(
        app->config_list,
        "Frequency",
        3,
        car_breaker_config_mode_changed,
        app);
    variable_item_set_current_value_index(mode_item, app->mode);
    variable_item_set_current_value_text(mode_item, car_breaker_mode_names[app->mode]);

    car_breaker_filter_item = variable_item_list_add(
        app->config_list,
        "Filter",
        2,
        car_breaker_config_filter_changed,
        app);
    variable_item_set_current_value_index(car_breaker_filter_item, app->filter);
    if(app->mode == CarBreakerModeHopping) {
        variable_item_set_current_value_text(car_breaker_filter_item, "N/A");
    } else {
        variable_item_set_current_value_text(car_breaker_filter_item, car_breaker_filter_names[app->filter]);
    }

    view_set_previous_callback(
        variable_item_list_get_view(app->config_list), car_breaker_view_previous_callback);
    view_dispatcher_add_view(
        app->view_dispatcher, CarBreakerViewConfig, variable_item_list_get_view(app->config_list));

    // Capture dialog
    app->capture_dialog = dialog_ex_alloc();
    dialog_ex_set_header(app->capture_dialog, "Scanning...", 64, 10, AlignCenter, AlignTop);
    dialog_ex_set_text(app->capture_dialog, "Waiting for signal...", 64, 32, AlignCenter, AlignCenter);
    dialog_ex_set_center_button_text(app->capture_dialog, "Stop");
    dialog_ex_set_context(app->capture_dialog, app);
    dialog_ex_set_result_callback(app->capture_dialog, car_breaker_capture_callback);
    view_set_previous_callback(dialog_ex_get_view(app->capture_dialog), car_breaker_capture_back_callback);
    view_dispatcher_add_view(
        app->view_dispatcher, CarBreakerViewCapture, dialog_ex_get_view(app->capture_dialog));

    app->about_view = car_breaker19_scene_about_alloc();
    view_set_previous_callback(app->about_view, car_breaker_view_previous_callback);
    view_dispatcher_add_view(app->view_dispatcher, CarBreakerViewAbout, app->about_view);

    return app;
}

static void car_breaker_free(CarBreakerApp* app) {
    if(!app) return;

    car_breaker_stop_capture(app);

    if(app->ui_timer) {
        furi_timer_free(app->ui_timer);
    }

    if(app->hop_timer) {
        furi_timer_free(app->hop_timer);
    }

    view_dispatcher_remove_view(app->view_dispatcher, CarBreakerViewAbout);
    car_breaker19_scene_about_free(app->about_view);

    view_dispatcher_remove_view(app->view_dispatcher, CarBreakerViewCapture);
    dialog_ex_free(app->capture_dialog);

    view_dispatcher_remove_view(app->view_dispatcher, CarBreakerViewConfig);
    variable_item_list_free(app->config_list);

    view_dispatcher_remove_view(app->view_dispatcher, CarBreakerViewMenu);
    submenu_free(app->submenu);

    view_dispatcher_remove_view(app->view_dispatcher, CarBreakerViewSplash);
    dialog_ex_free(app->splash_dialog);

    view_dispatcher_free(app->view_dispatcher);
    furi_record_close(RECORD_GUI);
    furi_record_close(RECORD_NOTIFICATION);

    subghz_worker_free(app->worker);
    furi_mutex_free(app->lock);

    free(app);
}

static void car_breaker_run(CarBreakerApp* app) {
    car_breaker_safe_switch_view(app, CarBreakerViewSplash);
    view_dispatcher_run(app->view_dispatcher);
}

int32_t car_breaker19_app(void* arg) {
    UNUSED(arg);
    CarBreakerApp* app = car_breaker_alloc();
    car_breaker_run(app);
    car_breaker_free(app);
    return 0;
}
