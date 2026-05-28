#pragma once

#include "custom_btn.h"

#define PROG_MODE_OFF              (0U)
#define PROG_MODE_KEELOQ_BFT       (1U)
#define PROG_MODE_KEELOQ_APRIMATIC (2U)
#define PROG_MODE_KEELOQ_DEA_MIO   (3U)

typedef uint8_t ProgMode;

void subghz_custom_btn_set_original(uint8_t btn_code);

void subghz_custom_btn_set_max(uint8_t b);

void subghz_custom_btn_set_prog_mode(ProgMode prog_mode);

ProgMode subghz_custom_btn_get_prog_mode(void);

/* ARF Custom edition: helper macro from Flipper-ARF.
 * Declares a static button-map and conversion helpers for protocols
 * that support remappable custom buttons.
 */

typedef struct {
    uint8_t custom_btn_id;
    uint8_t protocol_code;
} SubGhzCustomBtnEntry;

#define SUBGHZ_CUSTOM_BTN_DEFINE_MAP(prefix_, ...)                              \
    static const SubGhzCustomBtnEntry prefix_##_btn_map[] = {__VA_ARGS__};      \
    static const uint8_t prefix_##_custom_btn_max =                             \
        (sizeof(prefix_##_btn_map) / sizeof(SubGhzCustomBtnEntry)) - 1U;        \
                                                                                \
    static uint8_t prefix_##_custom_btn_to_code(uint8_t custom_btn) {           \
        for(size_t i = 0; i < sizeof(prefix_##_btn_map) /                       \
                              sizeof(SubGhzCustomBtnEntry); i++) {              \
            if(prefix_##_btn_map[i].custom_btn_id == custom_btn)                \
                return prefix_##_btn_map[i].protocol_code;                      \
        }                                                                       \
        return prefix_##_btn_map[0].protocol_code;                              \
    }                                                                           \
                                                                                \
    static uint8_t prefix_##_code_to_custom_btn(uint8_t code) {                 \
        for(size_t i = 0; i < sizeof(prefix_##_btn_map) /                       \
                              sizeof(SubGhzCustomBtnEntry); i++) {              \
            if(prefix_##_btn_map[i].protocol_code == code)                      \
                return prefix_##_btn_map[i].custom_btn_id;                      \
        }                                                                       \
        return SUBGHZ_CUSTOM_BTN_OK;                                            \
    }                                                                           \
                                                                                \
    static void prefix_##_custom_btn_init(uint8_t current_code) {               \
        uint8_t original = prefix_##_code_to_custom_btn(current_code);          \
        if(subghz_custom_btn_get_original() == 0)                               \
            subghz_custom_btn_set_original(original);                           \
        subghz_custom_btn_set_max(prefix_##_custom_btn_max);                    \
    }
