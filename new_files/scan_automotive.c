#include "scan_automotive.h"

#include <furi.h>
#include <furi_hal.h>
#include <lib/subghz/subghz_worker.h>
#include <lib/subghz/subghz_protocol_registry.h>
#include <lib/subghz/protocols/base.h>
#include <string.h>

#define TAG "AutoScanner"

/* Frequencies to sweep, in Hz */
static const uint32_t auto_scan_frequencies[] = {
    315000000,
    433920000,
};
#define AUTO_SCAN_FREQ_COUNT (sizeof(auto_scan_frequencies) / sizeof(auto_scan_frequencies[0]))

/* Time to listen on each frequency before switching (ms) */
#define AUTO_SCAN_DWELL_MS 400u

struct AutoScanner {
    FuriThread* thread;
    volatile bool running;
    AutoScanCallback callback;
    void* callback_context;
};

// ─── Worker thread ───────────────────────────────────────────────────────────

typedef struct {
    AutoScanner* scanner;
    SubGhzEnvironment* environment;
    const SubGhzProtocolRegistry* registry;
} ScanThreadCtx;

/*
 * Thin shim: for each protocol decoder, alloc → feed pulses → check result.
 * We do a simplified version here: record the raw captured signal and attempt
 * to deserialize through each registered decoder.
 *
 * A full integration would hook into SubGhzWorker callbacks; this demonstrates
 * the architecture and can be wired into the SubGhz app's scene system.
 */
static void auto_scan_try_protocol(
    const SubGhzProtocol* proto,
    SubGhzEnvironment* env,
    const uint8_t* raw_bits,
    size_t bit_count,
    float freq_mhz,
    AutoScanCallback cb,
    void* ctx) {
    if(!proto->decoder || !proto->decoder->alloc || !proto->decoder->get_string) return;

    void* decoder = proto->decoder->alloc(env);
    if(!decoder) return;

    /* Feed raw bits as synthetic pulses (te_short for 0, te_long for 1).
     * Real integration would use the SubGhzWorker feed path. */
    for(size_t i = 0; i < bit_count; i++) {
        bool bit = (raw_bits[i / 8] >> (7 - (i % 8))) & 1;
        uint32_t dur = bit ? 500u : 250u;
        proto->decoder->feed(decoder, true, dur);
        proto->decoder->feed(decoder, false, dur);
    }

    FuriString* result_str = furi_string_alloc();
    proto->decoder->get_string(decoder, result_str);

    /* A match is indicated by the string containing a serial-like token */
    const char* s = furi_string_get_cstr(result_str);
    if(s && strstr(s, "Sn:") && cb) {
        AutoScanResult result = {0};
        result.found = true;
        result.frequency_mhz = freq_mhz;
        strncpy(result.protocol_name, proto->name, sizeof(result.protocol_name) - 1);
        cb(&result, ctx);
    }

    furi_string_free(result_str);
    proto->decoder->free(decoder);
}

static int32_t auto_scanner_thread(void* arg) {
    ScanThreadCtx* tctx = (ScanThreadCtx*)arg;
    AutoScanner* scanner = tctx->scanner;

    FURI_LOG_I(TAG, "Automotive scanner started");

    size_t freq_idx = 0;
    while(scanner->running) {
        uint32_t freq_hz = auto_scan_frequencies[freq_idx % AUTO_SCAN_FREQ_COUNT];
        float freq_mhz = (float)freq_hz / 1000000.0f;

        FURI_LOG_D(TAG, "Scanning %.2f MHz", (double)freq_mhz);

        furi_hal_subghz_reset();
        furi_hal_subghz_load_custom_preset(NULL);
        furi_hal_subghz_set_frequency_and_path(freq_hz);
        furi_hal_subghz_rx();

        /* Listen for AUTO_SCAN_DWELL_MS, collect raw signal samples */
        furi_delay_ms(AUTO_SCAN_DWELL_MS);

        furi_hal_subghz_reset();

        freq_idx++;
    }

    FURI_LOG_I(TAG, "Automotive scanner stopped");
    return 0;
}

// ─── Public API ─────────────────────────────────────────────────────────────

AutoScanner* auto_scanner_alloc(void) {
    AutoScanner* scanner = malloc(sizeof(AutoScanner));
    scanner->running = false;
    scanner->callback = NULL;
    scanner->callback_context = NULL;
    scanner->thread = furi_thread_alloc_ex("AutoScanner", 2048, auto_scanner_thread, NULL);
    return scanner;
}

void auto_scanner_free(AutoScanner* scanner) {
    furi_assert(scanner);
    auto_scanner_stop(scanner);
    furi_thread_free(scanner->thread);
    free(scanner);
}

void auto_scanner_set_callback(AutoScanner* scanner, AutoScanCallback cb, void* context) {
    furi_assert(scanner);
    scanner->callback = cb;
    scanner->callback_context = context;
}

void auto_scanner_start(AutoScanner* scanner) {
    furi_assert(scanner);
    if(scanner->running) return;

    ScanThreadCtx* ctx = malloc(sizeof(ScanThreadCtx));
    ctx->scanner = scanner;
    ctx->environment = subghz_environment_alloc();
    ctx->registry = subghz_protocol_registry_get_base_protocol_registry();

    scanner->running = true;
    furi_thread_set_context(scanner->thread, ctx);
    furi_thread_start(scanner->thread);
    FURI_LOG_I(TAG, "Scanner started: sweeping %u frequencies", (unsigned)AUTO_SCAN_FREQ_COUNT);
}

void auto_scanner_stop(AutoScanner* scanner) {
    furi_assert(scanner);
    if(!scanner->running) return;

    scanner->running = false;
    furi_thread_join(scanner->thread);

    void* ctx = furi_thread_get_context(scanner->thread);
    if(ctx) {
        ScanThreadCtx* tctx = (ScanThreadCtx*)ctx;
        if(tctx->environment) subghz_environment_free(tctx->environment);
        free(tctx);
        furi_thread_set_context(scanner->thread, NULL);
    }
}

bool auto_scanner_is_running(const AutoScanner* scanner) {
    furi_assert(scanner);
    return scanner->running;
}
