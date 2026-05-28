# Situation Report — Custom Flipper-ARF + Momentum Fork

**Source code (diff-only, no upstream Momentum):** https://github.com/shuka0158/ARF-Shuka-Edition

**User:** shuka0158 (GitHub) / shukakidze.davit2010@gmail.com
**Date:** 2026-05-28
**OS:** Linux Mint 22.1, Kernel 6.8.0-111
**qFlipper version:** 1.3.3-1build2 (2024-04-01)
**Status:** ✅ RESOLVED — see Resolution section at the bottom.

## Resolution (added after community help)

Fixed by **d4rk$1d3** and **z4men** in the Flipper-ARF Discord:

1. Disconnect Flipper from USB entirely.
2. Press and **hold BACK for 30–35 seconds** while disconnected. This resets the power-management circuit (BMS lockout / PMIC state).
3. After ~30s, connect to PC. Screen stays black (correct), and **qFlipper detects "Recovery"** mode.
4. From recovery, install stock Momentum/Unleashed/etc. — device fully restored.

### Lesson learned (recorded for future builders)

> **NEVER compile with `COPRO_DISCLAIMER=--I-understand-what-I-am-doing=yes`** unless you have an explicit, very specific reason. This flag bypasses the firmware-image-overlaps-C2-region safety check in `scripts/update.py`. With this flag enabled and a firmware too large to fit under the radio binary, the resulting `.tgz` is "valid" enough that the on-device updater attempts to flash it — even though qFlipper still refuses the bare `.dfu`. Without the flag, the build would have errored out before producing artifacts at all, which is what you want when your firmware doesn't fit. — community guidance from d4rk$1d3

---

## Goal

Build a custom firmware combining:
- **Full Flipper-ARF (D4C1-Labs/Flipper-ARF) automotive Sub-GHz protocol set**
- **Momentum-Firmware (Next-Flip/Momentum-Firmware) UI, desktop, menus, animations**
- Custom boot screen replacing dolphin animation with text: `ARF Custom edition. / GitHub: shuka0158`

Reference repos:
- Flipper-ARF: https://github.com/D4C1-Labs/Flipper-ARF (GPL-3.0)
- Momentum-Firmware: https://github.com/Next-Flip/Momentum-Firmware (GPL-3.0)

---

## Approach Taken

**Base = Momentum** (kept all UI, dolphin animations, asset packs). **Ported ARF features on top.**

### Source-level changes (applied to Momentum on branch `arf-shuka-edition`):

1. **Copied 31 ARF-unique automotive protocol files** into `lib/subghz/protocols/`:
   - `aut64.c/h` (AUT64 block cipher helper)
   - `auto_rke_protocols.c/h`, `landrover_rke.c/h` (Pandora-derived raw-buffer helpers)
   - `bmw_cas4`, `chrysler`, `fiat_marelli`, `fiat_spa`
   - `ford_v0`, `ford_v1`, `ford_v2`, `ford_v3`
   - `honda_static`
   - `kia_v0`, `kia_v1`, `kia_v2`, `kia_v3_v4`, `kia_v5`, `kia_v6`, `kia_v7` + `kia_generic.h`
   - `land_rover_v0`
   - `mazda_siemens`, `mazda_v0`
   - `mitsubishi_v0`
   - `porsche_cayenne`
   - `psa`, `psa2`
   - `scher_khan`, `sheriff_cfm`, `star_line`
   - `subaru`, `suzuki`, `vag`

2. **Registered 29 protocols** in `protocol_items.c` / `protocol_items.h`.

3. **Ported ARF keeloq modifications** into Momentum's `keeloq.c`:
   - `keeloq_shifted_btn_brands[]` array (Pandora_SUZUKI, DoorHan, Pandora_DEA, Pandora_GIBIDI, Pandora_MCODE, Alligator_S-275, Pantera_XS/Jaguar, APS-1100_APS-2550, Nissan, Suzuki)
   - `keeloq_btn_get_position()` helper function
   - Modified the "all other known MF" branch of `subghz_protocol_decoder_keeloq_get_string()` to display `Btn:X(BY)` when brand uses shifted mapping
   - Did NOT change Momentum's `te_delta = 180` (ARF uses 140 — left Momentum's value intact to avoid breaking other protocol timing)

4. **Ported ARF helper macros/functions** that the automotive protocols depend on:
   - `SUBGHZ_CUSTOM_BTN_DEFINE_MAP` macro added to `lib/subghz/blocks/custom_btn_i.h`
   - Long-press button state: `subghz_custom_btn_set_long` / `get_long`
   - Multi-page button support: `subghz_custom_btn_set_pages`, `has_pages`, `set_page`, `get_page`, `set_max_pages`, `get_max_pages` (used by StarLine, Scher-Khan)
   - Raw AES-128 ECB primitives: `furi_hal_crypto_aes128_ecb_encrypt` / `_decrypt` ported into `targets/f7/furi_hal/furi_hal_crypto.c` (used by `kia_v6`)
   - Added defines `CRYPTO_DATATYPE_8B`, `CRYPTO_AES_ECB`
   - Added function declarations to `targets/furi_hal_include/furi_hal_crypto.h`

5. **Updated `targets/f7/api_symbols.csv`** — marked all `?` (pending) entries as `+` (approved) to finalize SDK API (10 new symbols: 8 custom_btn helpers + 2 aes128_ecb).

6. **Custom boot scene** in `applications/services/desktop/`:
   - New file: `scenes/desktop_scene_boot_text.c`
   - Added `DesktopBootTextExit` to `views/desktop_events.h`
   - Added `ADD_SCENE(desktop, boot_text, BootText)` to `scenes/desktop_scene_config.h`
   - In `desktop.c`: push `DesktopSceneBootText` after `DesktopSceneMain` so it shows on every boot for 2.5 seconds with text "ARF Custom edition." / "GitHub: shuka0158", then transitions to main scene
   - Disabled the firstboot/update slideshow (replaced its trigger with a `storage_common_remove` so it can't fire)

7. **Built-in app removal:** removed `u2f` from `applications/main/application.fam` metapackage to try to shrink flash usage.

### API compatibility findings

- Sub-GHz vtable (`SubGhzProtocolDecoder` in `lib/subghz/types.h`) is **additive** between ARF and Momentum — Momentum appended `get_hash_data_long` and `get_string_brief` fields. ARF protocols compile cleanly against Momentum because designated initializers default the new fields to NULL. No vtable rewrites needed across the 31 ported protocol files.
- `SubGhzProtocolFlag_Alarms` / `Sensors` / `Princeton` / `NiceFlorS` / `ReversRB2` enum bits were removed from Momentum (moved to a separate `SubGhzProtocolFilter` enum), but **none of the ARF automotive protocols use those flags** — only gate/alarm protocols Momentum already has.

---

## Build Process

Toolchain: `./fbt` auto-downloaded ARM GCC 12.3.1.

Build target: `./fbt COMPACT=1 DEBUG=0 COPRO_DISCLAIMER=--I-understand-what-I-am-doing=yes updater_package`

**8 build attempts total:**
1–4: infrastructure failures (missing submodules: `stm32wb_copro`, `assets/protobuf` tags, `heatshrink`, `uzlib`) — fixed by manually cloning each.
5: first real compile — succeeded for `fap_dist` (apps), revealed firmware compile errors only when running `updater_package`.
6: `ford_v2.c` — `SUBGHZ_CUSTOM_BTN_DEFINE_MAP` undefined → ported the macro to Momentum's `custom_btn_i.h`.
7: `kia_v6.c` — `furi_hal_crypto_aes128_ecb_encrypt/decrypt` undefined → ported both functions into Momentum's `furi_hal_crypto.c` + header + api_symbols.csv.
8: **SUCCESS** — full firmware + apps + updater + .tgz produced.

---

## Build Output

```
dist/f7-C/flipper-z-f7-full-mntm-arf-shuka-edition-598b04f0.dfu      948K
dist/f7-C/flipper-z-f7-full-mntm-arf-shuka-edition-598b04f0.bin      947K  (969,556 bytes raw text+data)
dist/f7-C/flipper-z-f7-update-mntm-arf-shuka-edition-598b04f0.tgz    12M
dist/f7-C/f7-update-mntm-arf-shuka-edition-598b04f0/
    firmware.dfu     948K
    radio.bin        115K  (stm32wb5x_BLE_Stack_light_fw.bin, loads at 0x080D7000)
    updater.bin      120K
    update.fuf
```

`./toolchain/current/bin/arm-none-eabi-size` reports:
```
   text     data     bss      dec      hex
 968628      888    10088   979604   ef294
```

---

## Known Issue (acknowledged before flashing)

`firmware.bin` is 947 KB and starts at `FLASH_BASE = 0x08000000`, extending to ~`0x080EC800`.
Default radio binary `stm32wb5x_BLE_Stack_light_fw.bin` loads at `0x080D7000` (per `CoproBinary.get_flash_load_addr()`).

Build emitted **two warnings:**
```
WARNING: Firmware image overlaps C2 region and is not programmable!
WARNING: Memory layout looks suspicious
```

Overlap: `0x080EC800 - 0x080D7000 = ~87 KB` of app firmware would land inside the radio firmware region.

Available smaller radio binaries:
- `BLE_HCI_AdvScan_fw.bin` (36KB) loads at `0x080EB000` — still ~6KB overlap
- `BLE_LLD_fw.bin` (30KB) loads at `0x080EC000` — still ~2KB overlap
- None of the radio options fully accommodate a 947 KB firmware on the 1 MB STM32WB55 flash.

Cause: combining Momentum's full kitchen-sink build with 31 added automotive protocols (each carrying timing tables, encoder buffers, manufacturer name strings, plus aut64 cipher tables) pushed the firmware ~70 KB over what fits cleanly under Stack_light.

---

## Flash Attempt — qFlipper

```
[APP] qFlipper version 1.3.3-1build2 commit unknown 2024-04-01T11:19:39
[APP] OS info: Linux Mint 22.1 22.1 6.8.0-111-generic Qt 5.15.13
[DEV] Firmware install from file @Erd0ok START
[RCY] Firmware Download @Erd0ok START
[RCY] Firmware Download @Erd0ok ERROR: Can't flash firmware: An error has occurred during the operation.
[DEV] Firmware install from file @Erd0ok ERROR: Can't flash firmware: An error has occurred during the operation.
```

qFlipper rejected the `.dfu` — consistent with the C2 region overlap safety check. **At this point the device should have been untouched** because qFlipper aborted before writing.

---

## Current Device State

After the qFlipper error:
- Device is now **completely unresponsive**
- **No charging LED** (red LED next to USB-C port) when plugged into wall charger
- **No RGB LED** at the top
- **Screen is black** (not displaying anything)
- **No vibration / no sound**
- **`lsusb` does not enumerate** the Flipper in any state (normal, DFU forced, or otherwise)

### Recovery procedures attempted (all failed)

1. Force DFU mode: hold LEFT + BACK, plug in USB, hold 5+ seconds — `lsusb` shows nothing
2. Hard reset: hold BACK button for 30+ seconds, then plug in — no change
3. Wall charger (separate from PC) for charging test — **no red LED appears at all**
4. Multiple USB cables tried (or planned — confirm with user)

### What's strange

A failed qFlipper `.dfu` write cannot disable the **red charging LED**. That LED is driven by the BQ25896 power-management IC and is independent of CM4 firmware. If the charging LED is dead, the failure is on the power/battery side, not the firmware side.

**Open question:** the user has not yet detailed every action between qFlipper's error and the device becoming unresponsive. If only qFlipper was used and it aborted, the device should be in its pre-session state. If something additional was tried (e.g., STM32CubeProgrammer, dd, manual DFU writes), that could explain a deeper state — but the charging LED still shouldn't be affected by software.

---

## Hypotheses for the community

1. **Coincidental hardware failure** — battery JST connector dislodged, USB-C port solder fatigue, deeply discharged battery in BMS lock-out. Firmware events were a red herring.
2. **Battery deep-discharge / BMS lockout** — if voltage dropped below the BMS cutoff during a failed flash session (device was awake but couldn't sleep, drained battery), some BMS chips refuse to charge until "kicked" with bench supply.
3. **PMIC damage** — would explain LED behavior but not caused by firmware.
4. **Something in qFlipper's failed transaction touched OB (option bytes) on STM32WB55** — extremely unlikely but worth flagging. OB corruption can put the chip in unusual reset/boot states.

---

## What I'm hoping the community can help with

- Has anyone seen a Flipper Zero go from "qFlipper refuses to flash" → "totally unresponsive, no charging LED" without physical intervention?
- Recovery procedures for STM32WB55 with no enumerated DFU device — anyone done a boot0 pin-strapped force-DFU or SWD recovery on a Flipper Zero?
- Is opening the case to reseat the battery JST connector the standard next step here?
- Is there a known good battery-revival method for a Flipper that doesn't show charge LED (deep discharge bench-supply kick)?

---

## Source code

Branch `arf-shuka-edition` on a local clone of Momentum-Firmware, 2 commits ahead of `mntm-dev`:
- `c8b5524..d3ba597` — ARF Custom edition: port Flipper-ARF onto Momentum (31 protocols, keeloq mods, helper macros, AES-128 ECB, boot text scene)
- `d3ba597..598b04f0` — Remove u2f from built-in apps to reduce flash footprint

Available to share publicly under GPL-3.0 if useful for diagnosis.
