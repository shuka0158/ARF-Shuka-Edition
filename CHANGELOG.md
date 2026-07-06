# Changelog

## [Unreleased]

### Added
- Toyota/Lexus RKE protocol (315/433 MHz, PWM, 72-bit rolling-code frame)
- Nissan/Infiniti RKE protocol (315/433 MHz, PWM, 64-bit Keeloq-derived rolling code)
- Renault/Dacia RKE protocol (433 MHz, PCM, 64-bit rolling code)
- GM/Chevrolet rolling-code protocol (315 MHz, Manchester, 64-bit frame with 5-button support)
- Honda/Acura RKE protocol (315/433 MHz, PWM, 64-bit frame, CRC-8 poly 0x2F)
- Hyundai New / Genesis RKE protocol (433 MHz, PWM, 64-bit frame, CRC-8 poly 0x31)
- Automotive passive scanner (`scan_automotive.c`) — scans known automotive frequencies and reports matching protocol
- GitHub Actions CI/CD: auto-builds firmware on push, creates releases on `v*` tags
- CI `test` job compiles and runs the `tests/` crypto vectors and gates the firmware build on them
- `scripts/check_size.sh` — fails CI if `.dfu` exceeds the 880 KB radio flash limit
- `.gitignore` for build artifacts, toolchain cache, and editor files
- `docs/protocol_reference.md` — frequency, bit count, encoding, and frame layout for every protocol
- `tests/test_aut64.c` — known-good test vectors for the AUT64 block cipher
- `tests/test_keeloq.c` — known-good test vectors for Keeloq encode/decode

### Changed
- **BMW CAS4 display**: raw hex bytes reformatted with field labels, frame-marker validity shown, type byte decoded
- **KIA V0/V1 display**: button name now on its own line for readability; frequency band shown; CRC result uses `✓`/`✗` indicator
- **VAG display**: vehicle sub-brand (VW/Audi/Seat/Skoda) shown on header line; decryption key index shown inline
- **Ford V0 display**: CRC and checksum merged to one line; rolling-counter displayed as decimal alongside hex
- **Boot screen**: custom pixel-art car icon replaces plain text, credits remain below
- Protocol sections in `protocol_items.c` sorted alphabetically within the automotive group

### Fixed
- `tests/test_aut64.c` no longer used a non-existent 3-argument `aut64_encrypt`/`aut64_decrypt`/`aut64_pack` API — rewritten against the real in-place API so it compiles and passes (5/5)
- `tests/test_keeloq.c` KeeLoq NLFSR used the wrong linear feedback taps (bit 31 instead of bit 16 on encrypt; bit 0 instead of bit 15 on decrypt), so encrypt/decrypt were not inverses — corrected to canonical KeeLoq and verified against an independent known-answer vector (10/10)

---

## [v2.0] — 2025-03-xx  *(current stable)*

### Added
- 29 automotive Sub-GHz protocols on top of Flipper-ARF base
- Custom boot screen ("ARF Custom edition. GitHub: shuka0158") with 2.5 s display
- AUT64 block cipher (`aut64.c`)
- AES-128 ECB in `furi_hal_crypto` extensions
- Keeloq helper: long-press support, multi-page button state, programming mode
- Porsche Cayenne, BMW CAS4, VAG (types 1–4), Ford (v0–v3), PSA (v1–v2), Fiat Marelli/SPA,
  Kia (v0–v7), Land Rover, Honda Static, Subaru, Mazda v0/Siemens, Mitsubishi v0,
  Chrysler, Suzuki, Scher-Khan, Sheriff CFM, Star Line

### Fixed
- Build target switched from Momentum-Firmware to Flipper-ARF base, dropping size from 947 KB to 854 KB (below the 880 KB radio limit that caused v1 device lockout)
- First-boot slideshow suppressed via scene patch

---

## [v1.0] — 2025-02-xx  *(deprecated — caused device lockout)*

### Notes
- Attempted to merge ARF automotive protocols onto Momentum-Firmware mntm-dev branch
- Resulting `.dfu` was 947 KB — 67 KB over the 880 KB radio limit
- Device entered recovery mode on flash; required DFU recovery via USB
- **Do not use.** Kept for historical reference in `patches/`
