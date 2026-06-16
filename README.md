# ARF Shuka Edition

Custom Flipper Zero firmware by **shuka0158**, based on **Flipper-ARF**.
Focused on automotive Sub-GHz research: rolling-code capture, replay, and analysis for RKE remotes.

[![Build](https://github.com/shuka0158/ARF-Shuka-Edition/actions/workflows/build.yml/badge.svg)](https://github.com/shuka0158/ARF-Shuka-Edition/actions/workflows/build.yml)

---

## Quick start — flash pre-built firmware

1. Download the latest `.dfu` from [Releases](../../releases)
2. Open **qFlipper → Install from file** → select the `.dfu`
3. Wait for the flash to complete — you'll see the ARF car boot screen

> **Required:** the `.dfu` is built with `UPDATE_VERSION_STRING=ARF-Shuka-Edition`.
> qFlipper silently rejects `.dfu` files without a recognised version string.
> If you build from source, make sure to pass this to `ufbt`.

---

## What's in this firmware

### 33 automotive Sub-GHz protocols

| Brand | Protocols |
|---|---|
| BMW | CAS4 |
| Chrysler / Dodge / Jeep | Chrysler |
| Fiat / Alfa / Lancia | Fiat Marelli, Fiat SPA |
| Ford / Lincoln | Ford V0, V1, V2, V3 |
| GM / Chevrolet / Buick / Cadillac | GM Rolling *(new)* |
| Honda / Acura | Honda Static |
| Kia / Hyundai | KIA V0–V7 |
| Land Rover | Land Rover V0, RKE |
| Mazda | Mazda V0, Mazda Siemens |
| Mitsubishi | Mitsubishi V0 |
| Nissan / Infiniti | Nissan *(new)* |
| Porsche | Porsche Cayenne |
| PSA / Peugeot / Citroën | PSA V1, PSA V2 |
| Renault / Dacia | Renault *(new)* |
| Subaru | Subaru |
| Suzuki | Suzuki |
| Toyota / Lexus | Toyota *(new)* |
| VAG / VW / Audi / Seat / Skoda | VAG GROUP |
| Russian aftermarket | Scher-Khan, Sheriff CFM, Star Line |

### Crypto / cipher modules
- **AUT64** — 12-round block cipher (VAG types 1/3)
- **TEA** — Tiny Encryption Algorithm (VAG types 2/4)
- **AES-128 ECB** — hardware-accelerated via STM32WB CRYP (Kia v6)
- **Keeloq extended** — long-press, multi-page buttons, programming mode, 8 counter modes

### Tools
- **Automotive passive scanner** — sweeps 315/433 MHz, reports first matching protocol
- **Custom button support** — change button via d-pad in the SubGHz app (all 4 buttons cycle-able)
- **Signal log** — captured protocol + counter saved to SD card

### UI
- Custom boot screen with pixel-art car icon + "ARF Custom edition" text
- Protocol display improvements:
  - **KIA V0/V1**: frequency band shown, button on its own line, bit count inline
  - **BMW CAS4**: frame markers validated, encrypted payload ID shown, no redundant raw hex dump
  - **VAG**: vehicle sub-brand on header, key index inline, decrypt-failure path shows what was received
  - **Ford V0**: counter shown as decimal, CRC + checksum on one line
  - **Toyota / Nissan / Renault / GM**: all show frequency, serial, counter, named button, integrity result

---

## Build from source

### v2 (stable, recommended)

```bash
git clone https://github.com/D4C1-Labs/Flipper-ARF.git
cd Flipper-ARF
git am /path/to/ARF-Shuka-Edition/v2_arf_base/0001-*.patch

# Copy protocol files
cp /path/to/ARF-Shuka-Edition/new_files/*.{c,h} lib/subghz/protocols/
cp /path/to/ARF-Shuka-Edition/modified_files/protocol_items.{c,h} lib/subghz/protocols/
cp /path/to/ARF-Shuka-Edition/modified_files/custom_btn.{c,h} lib/subghz/blocks/
cp /path/to/ARF-Shuka-Edition/modified_files/custom_btn_i.h lib/subghz/blocks/
cp /path/to/ARF-Shuka-Edition/modified_files/keeloq.c lib/subghz/protocols/
cp /path/to/ARF-Shuka-Edition/modified_files/furi_hal_crypto.{c,h} targets/f7/furi_hal/
cp /path/to/ARF-Shuka-Edition/modified_files/desktop.c applications/services/desktop/
cp /path/to/ARF-Shuka-Edition/modified_files/desktop_events.h applications/services/desktop/views/
cp /path/to/ARF-Shuka-Edition/modified_files/desktop_scene_config.h applications/services/desktop/scenes/
cp /path/to/ARF-Shuka-Edition/modified_files/main_application.fam applications/main/application.fam
cp /path/to/ARF-Shuka-Edition/new_files/desktop_scene_boot_text.c applications/services/desktop/scenes/

# Build
ufbt UPDATE_VERSION_STRING="ARF-Shuka-Edition" firmware

# Check size (must stay under 880 KB)
bash /path/to/ARF-Shuka-Edition/scripts/check_size.sh build/f7-firmware/firmware.dfu
```

**Expected output:** ~860 KB with ~20 KB headroom.

> CI does this automatically on every push via `.github/workflows/build.yml`.
> Check the [Actions tab](../../actions) for the latest build status and artifact download.

### File placement reference

| File(s) | Destination in Flipper-ARF |
|---|---|
| `new_files/*.c` / `*.h` | `lib/subghz/protocols/` |
| `new_files/desktop_scene_boot_text.c` | `applications/services/desktop/scenes/` |
| `modified_files/keeloq.c`, `protocol_items.*`, `custom_btn*` | `lib/subghz/protocols/` or `lib/subghz/blocks/` (see above) |
| `modified_files/furi_hal_crypto.*` | `targets/f7/furi_hal/` |
| `modified_files/desktop.c`, `desktop_events.h` | `applications/services/desktop/` |
| `modified_files/desktop_scene_config.h` | `applications/services/desktop/scenes/` |
| `modified_files/main_application.fam` | `applications/main/application.fam` |

---

## Repository structure

```
.github/workflows/build.yml   CI: auto-build + release on push/tag
docs/protocol_reference.md    Frequency, encoding, frame layout for all 33 protocols
new_files/                    All new .c/.h files (protocols + scanner + boot screen)
modified_files/               12 files edited from upstream Flipper-ARF
patches/                      git-am patches (v1 historical, v2 working)
scripts/check_size.sh         Asserts .dfu stays under the 880 KB radio limit
tests/test_aut64.c            AUT64 cipher test vectors (build with gcc, standalone)
tests/test_keeloq.c           Keeloq rolling-code test vectors
v2_arf_base/                  v2 patch + pre-built firmware
firmware/                     v1 firmware (historical — DO NOT FLASH, 947 KB)
CHANGELOG.md                  Version history
SITUATION_REPORT.md           v1 post-mortem + device lockout recovery steps
```

---

## v1 warning

The `firmware/` directory contains the v1 `.dfu` (947 KB). **Do not flash it.**
It exceeds the 880 KB radio flash limit by 67 KB and will put the device into BMS lockout.
Recovery: hold BACK 30 s without USB → reconnect → qFlipper recovery mode.

Full story in [SITUATION_REPORT.md](SITUATION_REPORT.md).

---

## Protocol documentation

See [docs/protocol_reference.md](docs/protocol_reference.md) for:
- Frequency, modulation, frame size for every protocol
- Bit-level frame layout (preamble, serial, counter, button, CRC fields)
- CRC polynomial and algorithm for each brand
- Notable quirks (Nissan inverted button map, VAG multi-key rotation, BMW hardware-bound crypto)

---

## License

GPL-3.0 — inherited from [Flipper-ARF](https://github.com/D4C1-Labs/Flipper-ARF) and [Flipper Zero Firmware](https://github.com/flipperdevices/flipperzero-firmware).
