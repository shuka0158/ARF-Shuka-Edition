# ARF-Shuka-Edition — Protocol Reference

All protocols operate on Sub-GHz frequencies via AM (OOK) modulation unless noted.
Timings are in microseconds (µs). "te_short/te_long" refer to the PWM pulse widths used to encode 0/1 bits.

---

## Automotive Protocols

### BMW CAS4
| Field | Value |
|---|---|
| File | `bmw_cas4.c` |
| Protocol name | `BMW CAS4` |
| Frequency | 433.92 MHz |
| Modulation | AM (Manchester) |
| Frame size | 64 bit |
| te_short | 500 µs |
| te_long | 1000 µs |
| te_delta | 150 µs |
| Preamble | ≥10 pulses × 500 µs |
| Frame markers | Byte 0 = `0x30`, Byte 6 = `0xC5` |
| Encryption | CAS4 proprietary (hardware-bound, not reversible) |
| Notes | Decoder captures raw 64-bit frame; encryption key is fused to the vehicle ECU. Encode not supported. |

---

### Chrysler
| Field | Value |
|---|---|
| File | `chrysler.c` |
| Frequency | 315 / 433.92 MHz |
| Modulation | AM (PWM) |
| Frame size | 64 bit |
| Notes | Covers Chrysler/Dodge/Jeep/Ram rolling-code remotes. |

---

### Fiat Marelli
| Field | Value |
|---|---|
| File | `fiat_marelli.c` |
| Frequency | 433.92 MHz |
| Modulation | AM |
| Frame size | 64 bit |
| Notes | Marelli-sourced BCM remotes (Fiat, Alfa Romeo, Lancia). |

---

### Fiat SPA
| Field | Value |
|---|---|
| File | `fiat_spa.c` |
| Frequency | 433.92 MHz |
| Modulation | AM |
| Notes | SPA platform (Fiat 500, Bravo, Punto). Different frame from Marelli. |

---

### Ford V0
| Field | Value |
|---|---|
| File | `ford_v0.c` |
| Protocol name | `Ford V0` |
| Frequency | 315 / 433.92 MHz |
| Modulation | AM (Manchester) |
| Frame size | 80 bit (key1=64, key2=16) |
| te_short | 250 µs |
| te_long | 500 µs |
| te_delta | 100 µs |
| Buttons | Lock `0x01`, Unlock `0x02`, Trunk `0x04` |
| Rolling counter | 20 bit |
| CRC | 8-bit polynomial matrix + XOR obfuscation |
| Notes | Ford, Lincoln, Mercury (pre-2010). V1–V3 cover later generations. |

### Ford V1, V2, V3
| Field | Value |
|---|---|
| Files | `ford_v1.c`, `ford_v2.c`, `ford_v3.c` |
| Frequency | 315 / 433.92 MHz |
| Notes | Progressive generations with wider counter and additional buttons. V3 covers 2015+ models with Remote Start. |

---

### GM Rolling
| Field | Value |
|---|---|
| File | `gm_rolling.c` *(new)* |
| Protocol name | `GM Rolling` |
| Frequency | 315 MHz |
| Modulation | AM (Manchester) |
| Frame size | 64 bit |
| te_short | 500 µs |
| te_long | 1000 µs |
| te_delta | 150 µs |
| Buttons | Lock `0x01`, Unlock `0x02`, Trunk `0x04`, Panic `0x08`, Remote Start `0x10` |
| Rolling counter | 16 bit |
| Checksum | XOR of serial + counter + button |
| Notes | Covers Chevrolet, GMC, Buick, Cadillac (2000–2015). |

---

### Honda Static
| Field | Value |
|---|---|
| File | `honda_static.c` |
| Protocol name | `Honda Static` |
| Frequency | 315 / 433.92 MHz |
| Frame type | Fixed code (no rolling counter) |
| Notes | Older Honda/Acura remotes. Static = same code every press; not replay-resistant. |

---

### Kia V0–V7
| Field | Value |
|---|---|
| Files | `kia_v0.c` … `kia_v7.c` |
| Protocol name | `KIA/HYU V0` … `KIA V7` |
| Frequency | 315 / 433.92 MHz |
| Modulation | AM (PWM) |
| Frame size | 64 bit |
| te_short | 250 µs |
| te_long | 500 µs |
| te_delta | 100 µs |
| Frame layout | [4b preamble 0x0F][16b counter][28b serial][4b button][8b CRC] |
| Buttons | Unknown `0x0`, Lock `0x1`, Unlock `0x2`, Trunk `0x3`, Horn `0x4` |
| CRC | CRC-8, polynomial `0x7F`, MSB-first over bytes 1–6 |
| Notes | V0 = Kia/Hyundai pre-2010. V1–V7 cover successive platform changes; button codes and bit ordering vary. Hyundai Santa Fe 2013–2016 uses a Hitag2-derived rolling code (in `auto_rke_protocols.c`). |

---

### Land Rover V0 / RKE
| Field | Value |
|---|---|
| Files | `land_rover_v0.c`, `landrover_rke.c` |
| Frequency | 433.92 MHz |
| Notes | Covers Freelander 2, Discovery 3/4, Range Rover (2004–2012). |

---

### Mazda V0 / Siemens
| Field | Value |
|---|---|
| Files | `mazda_v0.c`, `mazda_siemens.c` |
| Frequency | 315 / 433.92 MHz |
| Notes | Mazda V0 = standard PWM frame. Siemens = OEM supplier variant with proprietary block cipher. |

---

### Mitsubishi V0
| Field | Value |
|---|---|
| File | `mitsubishi_v0.c` |
| Frequency | 315 / 433.92 MHz |
| Frame size | 64 bit |

---

### Nissan
| Field | Value |
|---|---|
| File | `nissan.c` *(new)* |
| Protocol name | `Nissan` |
| Frequency | 315 / 433.92 MHz |
| Modulation | AM (PWM) |
| Frame size | 64 bit |
| te_short | 300 µs |
| te_long | 600 µs |
| te_delta | 100 µs |
| Rolling counter | 16 bit |
| Buttons | Lock `0x2`, Unlock `0x1`, Trunk `0x4`, Panic `0x8` (physical→code mapping documented in keeloq.c comment) |
| CRC | CRC-8 `0x97` polynomial |
| Notes | Covers Nissan, Infiniti (2003–2018). Button code mapping is inverted vs. most brands — see `keeloq.c` comment referencing Pandora firmware analysis. |

---

### Porsche Cayenne
| Field | Value |
|---|---|
| File | `porsche_cayenne.c` |
| Frequency | 433.92 MHz |
| Notes | First-generation Cayenne (2002–2010) shared with VAG platform. |

---

### PSA V1 / V2
| Field | Value |
|---|---|
| Files | `psa.c`, `psa2.c` |
| Protocol name | `PSA V1`, `PSA V2` |
| Frequency | 433.92 MHz |
| Notes | Peugeot, Citroën, DS. V1 = pre-2008, V2 = 2008+ with wider counter. |

---

### Renault / Dacia
| Field | Value |
|---|---|
| File | `renault.c` *(new)* |
| Protocol name | `Renault` |
| Frequency | 433.92 MHz |
| Modulation | AM (PCM) |
| Frame size | 64 bit |
| te_short | 400 µs |
| te_long | 800 µs |
| te_delta | 120 µs |
| Rolling counter | 16 bit |
| Buttons | Lock `0x01`, Unlock `0x02`, Trunk `0x04` |
| CRC | 8-bit XOR checksum over payload bytes |
| Notes | Covers Renault Clio III/IV, Megane III, Dacia Duster/Sandero (2005–2020). |

---

### Scher-Khan
| Field | Value |
|---|---|
| File | `scher_khan.c` |
| Notes | Russian aftermarket alarm system. Widely used across CIS countries. |

---

### Sheriff CFM
| Field | Value |
|---|---|
| File | `sheriff_cfm.c` |
| Notes | Sheriff brand alarm/immobilizer remote. CIS market. |

---

### Star Line
| Field | Value |
|---|---|
| File | `star_line.c` |
| Notes | StarLine alarm system. Most common car alarm brand in Russia/CIS. |

---

### Subaru
| Field | Value |
|---|---|
| File | `subaru.c` |
| Frequency | 433.92 MHz |
| Frame size | 48 bit, LSB-first |
| Notes | Subaru/Fuji Heavy Industries legacy remote (pre-Denso era). |

---

### Suzuki
| Field | Value |
|---|---|
| File | `suzuki.c` |
| Frequency | 315 / 433.92 MHz |

---

### Toyota / Lexus
| Field | Value |
|---|---|
| File | `toyota_lexus.c` *(new)* |
| Protocol name | `Toyota` |
| Frequency | 315 MHz (NAM) / 433.92 MHz (EU/JPN) |
| Modulation | AM (PWM) |
| Frame size | 72 bit |
| te_short | 430 µs |
| te_long | 1290 µs |
| te_delta | 150 µs |
| Frame layout | [8b preamble][16b counter][32b serial][8b button][8b CRC] |
| Buttons | Lock `0x01`, Unlock `0x02`, Trunk `0x04`, Panic `0x08`, Remote Start `0x10` |
| CRC | CRC-8 `0xEA` polynomial over bytes 1–7 |
| Notes | Covers Toyota (Corolla, Camry, RAV4, Hilux) and Lexus (IS, RX, GS) 2003–2020. Encoding uses 3× repetition. |

---

### VAG GROUP
| Field | Value |
|---|---|
| File | `vag.c` |
| Protocol name | `VAG GROUP` |
| Frequency | 433.92 MHz |
| Modulation | AM (Manchester) |
| Frame size | 80 bit (prefix=15, key1=64, key2=16) |
| te_short (T1/T2) | 300 µs |
| te_long (T1/T2) | 600 µs |
| te_short (T3/T4) | 500 µs |
| te_long (T3/T4) | 1000 µs |
| Frame prefix | `0x2F3F` (Type 1/3) or `0x2F1C` (Type 2/4) |
| Encryption (T1/T3) | AUT64 block cipher (8-byte key, 12 rounds) |
| Encryption (T2/T4) | TEA (Tiny Encryption Algorithm, 32 rounds, δ=`0x9E3779B9`) |
| Brands | VW (`0xC0`), Audi (`0xC1`), Seat (`0xC2`), Skoda (`0xC3`) |
| Buttons | Unlock `0x10`, Lock `0x20`, Trunk `0x40`, Panic `0x80` |
| Keys | 3 hardcoded keys (index 1–3) tried in sequence on decode |
| Notes | Covers VAG Group vehicles 2000–2015. Pre-2004 "simple" variant is in `auto_rke_protocols.c`. |

---

## Security System Protocols (aftermarket)

### Keeloq (base)
| Field | Value |
|---|---|
| File | `modified_files/keeloq.c` |
| Notes | Extended Keeloq with long-press, multi-page buttons, and programming mode. Supports: Simple, Normal, Secure, Magic XOR T1, Magic Serial T1–T3 learning methods. Counter modes 0–7. |

---

## Cipher / Crypto Modules

### AUT64
| Field | Value |
|---|---|
| File | `aut64.c` |
| Block size | 8 bytes |
| Key size | 8 bytes + P-box (8 bytes) + S-box (16 bytes) = 32 bytes packed |
| Rounds | 12 |
| Operations | Permutation, substitution, bit-level compression, key-dependent round keys |
| Reference | USENIX Security 2016 — "Lock It and Still Lose It" |

### AES-128 ECB
| Field | Value |
|---|---|
| File | `modified_files/furi_hal_crypto.c` |
| Notes | Hardware AES via STM32WB CRYP peripheral. Used by some VAG/BMW protocols internally. |

---

## Passive Scanner
| Field | Value |
|---|---|
| File | `scan_automotive.c` *(new)* |
| Function | Sweeps 315 MHz and 433.92 MHz, feeds received pulses through all registered automotive decoders |
| Output | First matching protocol name + key fields displayed on screen |
| Notes | Useful when manufacturer is unknown. Not a replay tool — read-only observation mode. |
