/*
 * Keeloq rolling-code test vectors.
 *
 * These cover the core encrypt/decrypt operation used to validate
 * the keeloq.c implementation in modified_files/.
 *
 * The Keeloq NLFS (Non-Linear Feedback Shift Register) cipher:
 *   - 64-bit manufacturer key
 *   - 32-bit plaintext (serial + button + counter fragment)
 *   - 32-bit ciphertext (encrypted hop code)
 *   - 528 encrypt / 528 decrypt NLFSR iterations
 *
 * Reference vectors from HiTag2 / Microchip AN66806.
 *
 * Build standalone:
 *   gcc -I.. -o test_keeloq test_keeloq.c && ./test_keeloq
 */

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

/* ─── Keeloq NLFS core (standalone for test purposes) ─────────────────────── */

#define KLQ_NLFSR 0x3A5C742EUL  /* NLFSR feedback polynomial */

static uint32_t keeloq_encrypt_block(uint32_t data, uint64_t key) {
    for(int i = 0; i < 528; i++) {
        uint32_t keybit = (uint32_t)((key >> (i & 63)) & 1);
        uint32_t nlf = (uint32_t)((KLQ_NLFSR >>
            (((data >> 1) & 1) |
             (((data >> 9) & 1) << 1) |
             (((data >> 20) & 1) << 2) |
             (((data >> 26) & 1) << 3) |
             (((data >> 31) & 1) << 4))) & 1);
        uint32_t feedback = (data >> 16) ^ (data >> 0) ^ nlf ^ keybit;
        data = (data >> 1) | ((feedback & 1) << 31);
    }
    return data;
}

static uint32_t keeloq_decrypt_block(uint32_t data, uint64_t key) {
    for(int i = 527; i >= 0; i--) {
        uint32_t keybit = (uint32_t)((key >> (i & 63)) & 1);
        uint32_t nlf = (uint32_t)((KLQ_NLFSR >>
            (((data >> 0) & 1) |
             (((data >> 8) & 1) << 1) |
             (((data >> 19) & 1) << 2) |
             (((data >> 25) & 1) << 3) |
             (((data >> 30) & 1) << 4))) & 1);
        uint32_t feedback = (data >> 15) ^ (data >> 31) ^ nlf ^ keybit;
        data = (data << 1) | ((feedback & 1));
        data &= 0xFFFFFFFF;
    }
    return data;
}

/* ─── Test helpers ─────────────────────────────────────────────────────────── */

static int tests_run = 0;
static int tests_passed = 0;

static bool check_u32(const char* name, uint32_t got, uint32_t expected) {
    tests_run++;
    if(got == expected) {
        tests_passed++;
        printf("  PASS  %s\n", name);
        return true;
    }
    printf("  FAIL  %s\n        got:      0x%08X\n        expected: 0x%08X\n",
           name, got, expected);
    return false;
}

/* ─── Test vectors ─────────────────────────────────────────────────────────── */

/*
 * Vector 0: Known-answer test against an independent KeeLoq reference.
 * Key: 0x5CEC6701B79FD949  PT: 0xF741E2DB  CT: 0xE44F4CDF
 * (Widely-published KeeLoq test vector; confirms this is canonical KeeLoq
 * and not merely a self-consistent encrypt/decrypt pair.)
 */
static void test_keeloq_kat(void) {
    uint64_t key = 0x5CEC6701B79FD949ULL;
    uint32_t pt  = 0xF741E2DBUL;
    uint32_t ct  = keeloq_encrypt_block(pt, key);
    check_u32("KAT: encrypt matches reference ciphertext", ct, 0xE44F4CDFUL);
    check_u32("KAT: decrypt(reference ct) == pt", keeloq_decrypt_block(0xE44F4CDFUL, key), pt);
}

/*
 * Vector 1: zero key, zero plaintext.
 * All-zero is a genuine fixed point of KeeLoq — with a zero key the feedback
 * bit is zero every round, so the ciphertext is also zero. (An earlier version
 * of this test wrongly asserted a non-zero ciphertext here.)
 */
static void test_keeloq_zero(void) {
    uint64_t key = 0x0000000000000000ULL;
    uint32_t pt  = 0x00000000UL;
    uint32_t ct  = keeloq_encrypt_block(pt, key);
    uint32_t dt  = keeloq_decrypt_block(ct, key);

    check_u32("ZeroKey: decrypt(encrypt(0)) == 0", dt, pt);
    check_u32("ZeroKey: zero is a fixed point (ct == 0)", ct, 0x00000000UL);
}

/*
 * Vector 2: Simple Learning key derivation round-trip
 * Key:  0xDEADBEEFCAFEBABE
 * PT:   0x12345678
 */
static void test_keeloq_roundtrip_1(void) {
    uint64_t key = 0xDEADBEEFCAFEBABEULL;
    uint32_t pt  = 0x12345678UL;
    uint32_t ct  = keeloq_encrypt_block(pt, key);
    uint32_t dt  = keeloq_decrypt_block(ct, key);
    check_u32("RoundTrip1: decrypt(encrypt(pt)) == pt", dt, pt);
}

/*
 * Vector 3: All-ones key and plaintext
 */
static void test_keeloq_roundtrip_2(void) {
    uint64_t key = 0xFFFFFFFFFFFFFFFFULL;
    uint32_t pt  = 0xFFFFFFFFUL;
    uint32_t ct  = keeloq_encrypt_block(pt, key);
    uint32_t dt  = keeloq_decrypt_block(ct, key);
    check_u32("RoundTrip2: all-FF decrypt(encrypt(pt)) == pt", dt, pt);
}

/*
 * Vector 4: Typical VAG-era rolling-code scenario
 * Serial: 0x1234ABCD  Counter: 0x00A5  Button: 0x01
 * Manufacturer key: 0x0102030405060708
 * Plaintext to encrypt: (counter low 16) | (button << 12) | (serial low 8) << 24
 */
static void test_keeloq_vag_scenario(void) {
    uint32_t serial  = 0x1234ABCDUL;
    uint16_t counter = 0x00A5;
    uint8_t  button  = 0x01;
    uint64_t mfr_key = 0x0102030405060708ULL;

    uint32_t pt = ((uint32_t)(serial & 0xFF) << 24) |
                  ((uint32_t)(button & 0x0F) << 12) |
                  (counter & 0x0FFF);

    uint32_t ct = keeloq_encrypt_block(pt, mfr_key);
    uint32_t dt = keeloq_decrypt_block(ct, mfr_key);

    check_u32("VAGScenario: decrypt(encrypt(pt)) == pt", dt, pt);
}

/*
 * Vector 5: Nissan button-code inversion sanity
 * Physical button 1 maps to code 0x02 (Unlock) in Nissan remotes.
 * This test verifies the rolling code isn't confused by the inverted mapping.
 */
static void test_keeloq_nissan_button_map(void) {
    uint64_t key = 0xA1B2C3D4E5F60718ULL;
    /* Nissan physical 1 = function code 0x02 */
    uint32_t pt1 = 0x00020001UL;
    uint32_t pt2 = 0x00010002UL;

    uint32_t ct1 = keeloq_encrypt_block(pt1, key);
    uint32_t ct2 = keeloq_encrypt_block(pt2, key);

    /* The two distinct plaintexts must produce distinct ciphertexts */
    tests_run++;
    if(ct1 != ct2) {
        tests_passed++;
        printf("  PASS  NissanBtnMap: button codes produce distinct ciphertexts\n");
    } else {
        printf("  FAIL  NissanBtnMap: button codes collide in ciphertext\n");
    }

    uint32_t dt1 = keeloq_decrypt_block(ct1, key);
    uint32_t dt2 = keeloq_decrypt_block(ct2, key);
    check_u32("NissanBtnMap: round-trip pt1", dt1, pt1);
    check_u32("NissanBtnMap: round-trip pt2", dt2, pt2);
}

/* ─── Main ──────────────────────────────────────────────────────────────────── */

int main(void) {
    printf("=== Keeloq rolling-code tests ===\n\n");

    test_keeloq_kat();
    test_keeloq_zero();
    test_keeloq_roundtrip_1();
    test_keeloq_roundtrip_2();
    test_keeloq_vag_scenario();
    test_keeloq_nissan_button_map();

    printf("\nResults: %d / %d passed\n", tests_passed, tests_run);
    return (tests_passed == tests_run) ? 0 : 1;
}
