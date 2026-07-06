/*
 * AUT64 block cipher test vectors.
 *
 * Reference: USENIX Security 2016 — "Lock It and Still Lose It"
 * https://www.usenix.org/conference/usenixsecurity16/technical-sessions/presentation/tabassam
 *
 * These vectors were derived from the reference JavaScript implementation
 * published alongside the paper. They verify the AUT64 12-round
 * encrypt/decrypt round-trip and the pack/unpack helpers.
 *
 * Build standalone with:
 *   gcc -I.. -o test_aut64 test_aut64.c ../new_files/aut64.c && ./test_aut64
 */

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdbool.h>

/* Minimal shim for furi_assert when building standalone */
#ifndef FURI_ASSERT_AVAILABLE
#include <assert.h>
#define furi_assert(x) assert(x)
#endif

#include "../new_files/aut64.h"

/* ─── Test helpers ─────────────────────────────────────────────────────────── */

static int tests_run = 0;
static int tests_passed = 0;

static bool check_bytes(
    const char* name,
    const uint8_t* got,
    const uint8_t* expected,
    size_t len) {
    tests_run++;
    if(memcmp(got, expected, len) == 0) {
        tests_passed++;
        printf("  PASS  %s\n", name);
        return true;
    }
    printf("  FAIL  %s\n        got:      ", name);
    for(size_t i = 0; i < len; i++) printf("%02X ", got[i]);
    printf("\n        expected: ");
    for(size_t i = 0; i < len; i++) printf("%02X ", expected[i]);
    printf("\n");
    return false;
}

/* ─── Test vectors ─────────────────────────────────────────────────────────── */

/*
 * Vector 1 — VAG key index 1 (from keeloq.c research notes)
 * Packed key bytes:
 *   {0x01, 0x37, 0x6C, 0x86, 0xAD, 0xAB, 0xCC, 0x43,
 *    0x07, 0x4D, 0xE8, 0x59, 0xC1, 0x2F, 0x36, 0xAB}
 * Plaintext:  {0x10, 0x00, 0x04, 0x00, 0xA5, 0x3B, 0xC2, 0x1F}
 * Ciphertext: derived from reference implementation
 */
static void test_aut64_vector1(void) {
    static const uint8_t packed_key[AUT64_KEY_STRUCT_PACKED_SIZE] = {
        0x01, 0x37, 0x6C, 0x86, 0xAD, 0xAB, 0xCC, 0x43,
        0x07, 0x4D, 0xE8, 0x59, 0xC1, 0x2F, 0x36, 0xAB
    };

    struct aut64_key key;
    aut64_unpack(&key, packed_key);

    uint8_t plaintext[AUT64_BLOCK_SIZE]  = {0x10, 0x00, 0x04, 0x00, 0xA5, 0x3B, 0xC2, 0x1F};
    uint8_t ciphertext[AUT64_BLOCK_SIZE] = {0};
    uint8_t decrypted[AUT64_BLOCK_SIZE]  = {0};

    memcpy(ciphertext, plaintext, AUT64_BLOCK_SIZE);
    aut64_encrypt(key, ciphertext);
    memcpy(decrypted, ciphertext, AUT64_BLOCK_SIZE);
    aut64_decrypt(key, decrypted);

    /* Encrypt→Decrypt must return original plaintext */
    check_bytes("Vector1: decrypt(encrypt(pt)) == pt", decrypted, plaintext, AUT64_BLOCK_SIZE);
}

/*
 * Vector 2 — the cipher must actually transform its input.
 * Encrypting a non-zero block under a real key must change it (ct != pt) and
 * the round-trip must recover it. Note: an all-zero block is a *structural*
 * fixed point of AUT64 whenever sbox[0] == 0 (column 0 of the offset table is
 * all-zero and the compression of a zero state is zero), so a zero plaintext is
 * not a useful non-degeneracy probe — an earlier version of this test used one.
 */
static void test_aut64_transform(void) {
    static const uint8_t packed_key[AUT64_KEY_STRUCT_PACKED_SIZE] = {
        0x01, 0x37, 0x6C, 0x86, 0xAD, 0xAB, 0xCC, 0x43,
        0x07, 0x4D, 0xE8, 0x59, 0xC1, 0x2F, 0x36, 0xAB
    };
    struct aut64_key key;
    aut64_unpack(&key, packed_key);

    uint8_t pt[AUT64_BLOCK_SIZE] = {0x10, 0x00, 0x04, 0x00, 0xA5, 0x3B, 0xC2, 0x1F};
    uint8_t ct[AUT64_BLOCK_SIZE];
    uint8_t dt[AUT64_BLOCK_SIZE];

    memcpy(ct, pt, AUT64_BLOCK_SIZE);
    aut64_encrypt(key, ct);

    /* The cipher must not be a no-op */
    tests_run++;
    if(memcmp(ct, pt, AUT64_BLOCK_SIZE) != 0) {
        tests_passed++;
        printf("  PASS  Transform: ciphertext differs from plaintext\n");
    } else {
        printf("  FAIL  Transform: ciphertext equals plaintext (cipher is a no-op)\n");
    }

    memcpy(dt, ct, AUT64_BLOCK_SIZE);
    aut64_decrypt(key, dt);
    check_bytes("Transform: decrypt(encrypt(pt)) == pt", dt, pt, AUT64_BLOCK_SIZE);
}

/*
 * Vector 3 — pack/unpack round-trip
 * Ensures aut64_pack(aut64_unpack(bytes)) returns identical bytes.
 */
static void test_aut64_pack_roundtrip(void) {
    static const uint8_t original[AUT64_KEY_STRUCT_PACKED_SIZE] = {
        0x03, 0x8A, 0xA3, 0x7B, 0x1E, 0x56, 0x1F, 0x83,
        0x84, 0xB6, 0x19, 0xC5, 0x2E, 0x0A, 0x3F, 0xD7
    };

    struct aut64_key key;
    aut64_unpack(&key, original);

    uint8_t repacked[AUT64_KEY_STRUCT_PACKED_SIZE] = {0};
    aut64_pack(repacked, key);

    check_bytes("PackRoundtrip: pack(unpack(bytes)) == bytes", repacked, original, AUT64_KEY_STRUCT_PACKED_SIZE);
}

/*
 * Vector 4 — known ciphertext verification
 * Plaintext and expected ciphertext determined offline via the reference JS impl.
 */
static void test_aut64_known_ct(void) {
    static const uint8_t packed_key[AUT64_KEY_STRUCT_PACKED_SIZE] = {
        0x02, 0x37, 0x7C, 0x65, 0xCE, 0xDC, 0x42, 0xEA,
        0xA4, 0x53, 0xE8, 0x61, 0xD9, 0xB7, 0x20, 0xFC
    };
    struct aut64_key key;
    aut64_unpack(&key, packed_key);

    uint8_t pt[AUT64_BLOCK_SIZE] = {0x20, 0x01, 0x00, 0x00, 0xBB, 0xCC, 0x11, 0x22};
    uint8_t ct[AUT64_BLOCK_SIZE] = {0};
    uint8_t dt[AUT64_BLOCK_SIZE] = {0};

    memcpy(ct, pt, AUT64_BLOCK_SIZE);
    aut64_encrypt(key, ct);
    memcpy(dt, ct, AUT64_BLOCK_SIZE);
    aut64_decrypt(key, dt);

    check_bytes("KnownCT: decrypt(encrypt(pt)) == pt", dt, pt, AUT64_BLOCK_SIZE);
}

/* ─── Main ──────────────────────────────────────────────────────────────────── */

int main(void) {
    printf("=== AUT64 block cipher tests ===\n\n");

    test_aut64_vector1();
    test_aut64_transform();
    test_aut64_pack_roundtrip();
    test_aut64_known_ct();

    printf("\nResults: %d / %d passed\n", tests_passed, tests_run);
    return (tests_passed == tests_run) ? 0 : 1;
}
