#include "subghz_block_generic_global.h"

SubGhzBlockGenericGlobal subghz_block_generic_global = {
    .endless_tx = false,
    .cnt_need_override = false,
    .btn_need_override = false,
    .btn_is_available = false,
    .current_btn = 0,
    .btn_length_bit = 0,
    .cnt_is_available = false,
    .cnt_length_bit = 0,
    .current_cnt = 0,
};

bool subghz_block_generic_global_button_override_get(uint8_t* btn) {
    if(!subghz_block_generic_global.btn_need_override) return false;
    *btn = subghz_block_generic_global.current_btn;
    return true;
}

bool subghz_block_generic_global_counter_override_get(uint32_t* cnt_p) {
    if(!subghz_block_generic_global.cnt_need_override) return false;
    *cnt_p = subghz_block_generic_global.current_cnt;
    return true;
}

void subghz_block_generic_global_counter_override_set(uint32_t cnt) {
    subghz_block_generic_global.current_cnt = cnt;
    subghz_block_generic_global.cnt_need_override = true;
}

void subghz_block_generic_global_reset(void* context) {
    (void)context;
    subghz_block_generic_global.endless_tx        = false;
    subghz_block_generic_global.cnt_need_override = false;
    subghz_block_generic_global.btn_need_override = false;
    subghz_block_generic_global.btn_is_available  = false;
    subghz_block_generic_global.current_btn       = 0;
    subghz_block_generic_global.btn_length_bit    = 0;
    subghz_block_generic_global.cnt_is_available  = false;
    subghz_block_generic_global.cnt_length_bit    = 0;
    subghz_block_generic_global.current_cnt       = 0;
}

__attribute__((weak)) uint32_t furi_hal_subghz_get_rolling_counter_mult(void) {
    return 1;
}
