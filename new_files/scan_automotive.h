#pragma once

#include <furi.h>
#include <furi_hal.h>

/*
 * Automotive passive scanner — sweeps 315 MHz and 433.92 MHz and feeds
 * received pulses through all registered automotive protocol decoders.
 * First matching protocol + key fields are displayed.
 *
 * This is a read-only observation tool. It does NOT transmit.
 */

typedef struct AutoScanResult {
    char protocol_name[32];
    uint32_t serial;
    uint16_t counter;
    uint8_t button;
    float frequency_mhz;
    bool found;
} AutoScanResult;

typedef void (*AutoScanCallback)(const AutoScanResult* result, void* context);

typedef struct AutoScanner AutoScanner;

AutoScanner* auto_scanner_alloc(void);
void auto_scanner_free(AutoScanner* scanner);

void auto_scanner_set_callback(AutoScanner* scanner, AutoScanCallback cb, void* context);

/* Start scanning. Alternates between 315 and 433.92 MHz every ~250 ms. */
void auto_scanner_start(AutoScanner* scanner);
void auto_scanner_stop(AutoScanner* scanner);
bool auto_scanner_is_running(const AutoScanner* scanner);
