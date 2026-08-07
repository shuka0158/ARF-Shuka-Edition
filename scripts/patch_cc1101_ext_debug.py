#!/usr/bin/env python3
"""
Temporary diagnostic patch (issue: external CC1101 not detected on
Shuka-Edition but works on stock Unleashed with identical wiring — every
layer of source between the two firmwares checked byte-identical, so the
next step is finding out precisely which step of the device's own
self-test actually fails, straight from the device's own debug log,
instead of reconstructing the SPI transaction externally and guessing).

subghz_device_cc1101_ext_check_init() (applications/drivers/subghz/
cc1101_ext/cc1101_ext.c) has several distinct failure points that all
currently collapse into the same generic "Init failed" log line. This adds
a distinct FURI_LOG_E at each one, so `log` over the CLI will show exactly
where it stops: chip reset (CHIP_RDYn timeout), the first IOCFG0 write,
the GD0-low wait, the GD0-high wait, or one of the two later writes.

Exact-text surgery, same defensive style as this project's other
patch_*.py scripts: fails loudly if upstream source has changed shape.
Meant to be reverted once the real cause is found — not a permanent change.

Usage:
    patch_cc1101_ext_debug.py <flipper-fw-dir>
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


def main():
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} <flipper-fw-dir>")

    root = Path(sys.argv[1])
    path = (
        root
        / "applications"
        / "drivers"
        / "subghz"
        / "cc1101_ext"
        / "cc1101_ext.c"
    )
    content = path.read_text(encoding="utf-8")

    edits = [
        (
            '''        cc1101_status = cc1101_reset(subghz_device_cc1101_ext->spi_bus_handle);
        if(cc1101_status.CHIP_RDYn != 0) {
            //timeout or error
            break;
        }
        cc1101_status = cc1101_write_reg(
            subghz_device_cc1101_ext->spi_bus_handle, CC1101_IOCFG0, CC1101IocfgHighImpedance);
        if(cc1101_status.CHIP_RDYn != 0) {
            //timeout or error
            break;
        }''',
            '''        cc1101_status = cc1101_reset(subghz_device_cc1101_ext->spi_bus_handle);
        if(cc1101_status.CHIP_RDYn != 0) {
            FURI_LOG_E(TAG, "[shuka-debug] FAIL at cc1101_reset, CHIP_RDYn=%d", cc1101_status.CHIP_RDYn);
            break;
        }
        cc1101_status = cc1101_write_reg(
            subghz_device_cc1101_ext->spi_bus_handle, CC1101_IOCFG0, CC1101IocfgHighImpedance);
        if(cc1101_status.CHIP_RDYn != 0) {
            FURI_LOG_E(TAG, "[shuka-debug] FAIL at first IOCFG0 write (HighImpedance), CHIP_RDYn=%d", cc1101_status.CHIP_RDYn);
            break;
        }''',
            "reset + first IOCFG0 write checks",
        ),
        (
            '''        while(furi_hal_gpio_read(subghz_device_cc1101_ext->g0_pin) != false) {
            if(furi_hal_cortex_timer_is_expired(timer)) {
                //timeout
                break;
            }
        }
        if(furi_hal_cortex_timer_is_expired(timer)) {
            //timeout
            break;
        }''',
            '''        while(furi_hal_gpio_read(subghz_device_cc1101_ext->g0_pin) != false) {
            if(furi_hal_cortex_timer_is_expired(timer)) {
                //timeout
                break;
            }
        }
        if(furi_hal_cortex_timer_is_expired(timer)) {
            FURI_LOG_E(TAG, "[shuka-debug] FAIL waiting for GD0 LOW (100ms timeout) — GD0 stuck at %d", furi_hal_gpio_read(subghz_device_cc1101_ext->g0_pin));
            break;
        }''',
            "GD0-low wait timeout",
        ),
        (
            '''        while(furi_hal_gpio_read(subghz_device_cc1101_ext->g0_pin) != true) {
            if(furi_hal_cortex_timer_is_expired(timer)) {
                //timeout
                break;
            }
        }
        if(furi_hal_cortex_timer_is_expired(timer)) {
            //timeout
            break;
        }''',
            '''        while(furi_hal_gpio_read(subghz_device_cc1101_ext->g0_pin) != true) {
            if(furi_hal_cortex_timer_is_expired(timer)) {
                //timeout
                break;
            }
        }
        if(furi_hal_cortex_timer_is_expired(timer)) {
            FURI_LOG_E(TAG, "[shuka-debug] FAIL waiting for GD0 HIGH (100ms timeout) — GD0 stuck at %d", furi_hal_gpio_read(subghz_device_cc1101_ext->g0_pin));
            break;
        }''',
            "GD0-high wait timeout",
        ),
        (
            '''        // Reset GDO2 (!TX/RX) to floating state
        cc1101_status = cc1101_write_reg(
            subghz_device_cc1101_ext->spi_bus_handle, CC1101_IOCFG2, CC1101IocfgHighImpedance);
        if(cc1101_status.CHIP_RDYn != 0) {
            //timeout or error
            break;
        }

        // Go to sleep
        cc1101_status = cc1101_shutdown(subghz_device_cc1101_ext->spi_bus_handle);
        if(cc1101_status.CHIP_RDYn != 0) {
            //timeout or error
            break;
        }''',
            '''        // Reset GDO2 (!TX/RX) to floating state
        cc1101_status = cc1101_write_reg(
            subghz_device_cc1101_ext->spi_bus_handle, CC1101_IOCFG2, CC1101IocfgHighImpedance);
        if(cc1101_status.CHIP_RDYn != 0) {
            FURI_LOG_E(TAG, "[shuka-debug] FAIL at IOCFG2 write, CHIP_RDYn=%d", cc1101_status.CHIP_RDYn);
            break;
        }

        // Go to sleep
        cc1101_status = cc1101_shutdown(subghz_device_cc1101_ext->spi_bus_handle);
        if(cc1101_status.CHIP_RDYn != 0) {
            FURI_LOG_E(TAG, "[shuka-debug] FAIL at cc1101_shutdown, CHIP_RDYn=%d", cc1101_status.CHIP_RDYn);
            break;
        }''',
            "IOCFG2 write + shutdown checks",
        ),
    ]

    for old, new, label in edits:
        content = replace_once(content, old, new, label, path)

    path.write_text(content, encoding="utf-8")
    print(f"Patched {path}")


if __name__ == "__main__":
    main()
