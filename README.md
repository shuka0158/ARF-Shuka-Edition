# ARF Shuka Edition

Custom Flipper Zero firmware by **shuka0158** based on **Flipper-ARF**.

## 🎯 v2 (recommended, working) — `v2_arf_base/`

Base = **Flipper-ARF** firmware (already has all 31 automotive protocols + AUT64 cipher + Pandora keeloq stuff + everything).
On top: custom boot text scene replacing the firstboot dolphin animation with:

> **ARF Custom edition.**
> *GitHub: shuka0158*

Shown for 2.5 seconds on every boot, then transitions to normal desktop.

**Firmware size:** 854 KB (26 KB headroom under the BLE_Stack_light radio at 0x080D7000).
**Status:** ✅ Clean build, no `--I-understand-what-I-am-doing` flag, no C2-overlap warning. qFlipper-flashable.

### v2 contents
- `ARF-Shuka-Edition-v2.dfu` — 854 KB flashable .dfu (drag into qFlipper, "Install from file")
- `ARF-Shuka-Edition-v2-update.tgz` — 1.9 MB full update bundle (firmware + radio + resources)
- `0001-ARF-Shuka-Edition-boot-text-scene-disable-firstboot-.patch` — the diff against `D4C1-Labs/Flipper-ARF@main`, applies with `git am`
- `desktop_scene_boot_text.c` — standalone new file (copy into `applications/services/desktop/scenes/`)

### How to reproduce v2

```bash
git clone https://github.com/D4C1-Labs/Flipper-ARF.git
cd Flipper-ARF
git am /path/to/v2_arf_base/0001-*.patch
./fbt COMPACT=1 DEBUG=0 updater_package
# Output: dist/f7-C/flipper-z-f7-full-local.dfu
```

No special flags needed. Builds clean on first try.

## 📝 v1 (historical, bricked attempt) — root of this repo

Original attempt: Momentum-Firmware base + 31 ARF protocols ported on top.
Result: 947 KB firmware (67 KB over the 880 KB radio limit), build required `--I-understand-what-I-am-doing=yes` to bypass the safety check, qFlipper refused the `.dfu`, and the device went into BMS lockout. Recovered via *hold BACK 30s without USB → reconnect → qFlipper recovery* (thanks d4rk$1d3 / z4men in the Flipper-ARF Discord).

The v1 source-level changes are preserved in `patches/`, `new_files/`, `modified_files/` for archaeological interest. See [`SITUATION_REPORT.md`](SITUATION_REPORT.md) for the full story + lesson learned.

**Lesson:** Don't combine the full Momentum kitchen-sink build with the full ARF protocol set — they don't fit together under the radio. Pick one base. For automotive research, ARF is the right base.

## What this is

Base = [Momentum-Firmware](https://github.com/Next-Flip/Momentum-Firmware) (kept all UI, desktop, dolphin animations, asset packs intact).

On top, ported from [Flipper-ARF](https://github.com/D4C1-Labs/Flipper-ARF):

- **29 automotive Sub-GHz protocols:** VAG, PSA, PSA2, Ford v0/v1/v2/v3, Kia v0/v1/v2/v3_v4/v5/v6/v7, BMW CAS4, Subaru, Mazda Siemens, Mazda v0, Mitsubishi v0, Chrysler, Suzuki, Porsche Cayenne, Land Rover v0, Honda Static, Scher-Khan, Sheriff CFM, Star Line
- **2 cipher/helper modules:** AUT64 block cipher, auto_rke_protocols shared raw-buffer helpers, landrover_rke helper
- **Keeloq shifted-button-mapping** (Pandora_SUZUKI / DEA / GIBIDI / MCODE / Unknown_1 / Unknown_2, DoorHan, Alligator_S-275, Pantera_XS/Jaguar, APS-1100_APS-2550, Nissan, Suzuki) — auto-translates protocol button codes to physical button positions for these brands
- **SUBGHZ_CUSTOM_BTN_DEFINE_MAP** macro + long-press/multi-page button state helpers (used by StarLine, Scher-Khan, and the ported Ford protocols)
- **Raw AES-128 ECB primitives** in `furi_hal_crypto` (needed by Kia v6)

Plus a custom boot text scene replacing the dolphin firstboot animation with: *"ARF Custom edition. / GitHub: shuka0158"* shown for 2.5 seconds on every boot.

## What's in this repo

This repo contains only the diff against upstream Momentum — not the full Momentum source.

```
patches/         Two .patch files (apply with git am) reproducing the entire fork
                 against Momentum's mntm-dev branch at commit d3ba597
new_files/       66 source files that ARE NOT in Momentum upstream — copy these
                 directly into a Momentum checkout under the same paths (see below)
modified_files/  12 source files that ARE in Momentum upstream but were edited.
                 Compare against upstream to see exactly what changed.
firmware/        Compiled .dfu (948 KB) ready to flash (warning: see report)
SITUATION_REPORT.md   Full technical write-up + current device state + help request
```

## How to reproduce the build

```bash
git clone https://github.com/Next-Flip/Momentum-Firmware.git
cd Momentum-Firmware
git checkout d3ba597    # the mntm-dev commit this was built from
git am /path/to/this/repo/patches/*.patch
./fbt COMPACT=1 DEBUG=0 COPRO_DISCLAIMER=--I-understand-what-I-am-doing=yes updater_package
```

## File paths for `new_files/`

All 66 files in `new_files/` go into Momentum at these paths:

| File | Path in Momentum |
|------|------------------|
| `desktop_scene_boot_text.c` | `applications/services/desktop/scenes/desktop_scene_boot_text.c` |
| All `*.c` / `*.h` protocol files | `lib/subghz/protocols/` |

## File paths for `modified_files/`

| File | Path in Momentum |
|------|------------------|
| `keeloq.c` | `lib/subghz/protocols/keeloq.c` |
| `protocol_items.c` | `lib/subghz/protocols/protocol_items.c` |
| `protocol_items.h` | `lib/subghz/protocols/protocol_items.h` |
| `custom_btn.c` | `lib/subghz/blocks/custom_btn.c` |
| `custom_btn.h` | `lib/subghz/blocks/custom_btn.h` |
| `custom_btn_i.h` | `lib/subghz/blocks/custom_btn_i.h` |
| `furi_hal_crypto.c` | `targets/f7/furi_hal/furi_hal_crypto.c` |
| `furi_hal_crypto.h` | `targets/furi_hal_include/furi_hal_crypto.h` |
| `desktop.c` | `applications/services/desktop/desktop.c` |
| `desktop_events.h` | `applications/services/desktop/views/desktop_events.h` |
| `desktop_scene_config.h` | `applications/services/desktop/scenes/desktop_scene_config.h` |
| `main_application.fam` | `applications/main/application.fam` |

## Known issue: firmware size overlap

The combined firmware is **947 KB**, which extends to flash address **0x080EC800**.
The default radio binary `stm32wb5x_BLE_Stack_light_fw.bin` loads at **0x080D7000** — so the app firmware overlaps the radio firmware region by ~87 KB.

`scons` emits during build:
```
WARNING: Firmware image overlaps C2 region and is not programmable!
WARNING: Memory layout looks suspicious
```

qFlipper refuses to install the `.dfu` because of this overlap. See `SITUATION_REPORT.md`.

To fix this properly: ~70 KB of firmware needs to be removed (suggestions welcome — `bad_kb`? unused debug apps? smaller asset packs?), OR a smaller radio binary must be used (but none fit cleanly with this firmware size).

## License

GPL-3.0 (inherited from both Flipper-ARF and Momentum-Firmware).

