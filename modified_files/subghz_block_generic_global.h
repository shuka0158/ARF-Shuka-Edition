#pragma once
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    bool endless_tx;
    bool cnt_need_override;
    bool btn_need_override;
    bool btn_is_available;
    uint8_t current_btn;
    uint8_t btn_length_bit;
    bool cnt_is_available;
    uint8_t cnt_length_bit;
    uint32_t current_cnt;
} SubGhzBlockGenericGlobal;

extern SubGhzBlockGenericGlobal subghz_block_generic_global;

bool subghz_block_generic_global_button_override_get(uint8_t* btn);
bool subghz_block_generic_global_counter_override_get(uint32_t* cnt_p);
void subghz_block_generic_global_counter_override_set(uint32_t cnt);
void subghz_block_generic_global_reset(void* context);

/* ARF-specific furi_hal extension: rolling counter advance multiplier.
 * Returns 1 by default; overridden by the UI layer for configurable step. */
uint32_t furi_hal_subghz_get_rolling_counter_mult(void);

#ifdef __cplusplus
}
#endif
