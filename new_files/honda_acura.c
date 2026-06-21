#include "honda_acura.h"

#include "../blocks/const.h"
#include "../blocks/decoder.h"
#include "../blocks/encoder.h"
#include "../blocks/generic.h"
#include "../blocks/math.h"
#include "../blocks/custom_btn_i.h"

#define TAG "SubGhzProtocolHondaAcura"

/*
 * Honda/Acura RKE — 315 MHz (NA) / 433.92 MHz (EU)
 * PWM encoding, 64-bit frame MSB-first, 2× repeated transmission.
 *
 * Frame layout (MSB-first):
 *   [32b serial number]
 *   [16b rolling counter]
 *   [8b  button code]
 *   [8b  CRC-8 poly 0x2F]
 *
 * Button codes:
 *   0x10 = Lock, 0x20 = Unlock, 0x40 = Trunk, 0x08 = Panic
 *
 * Covers: Honda Civic/CR-V/Accord (2007+), Acura TL/MDX/RDX.
 */

static const SubGhzBlockConst subghz_protocol_honda_acura_const = {
    .te_short = 250,
    .te_long = 500,
    .te_delta = 80,
    .min_count_bit_for_found = 64,
};

#define HONDA_ACURA_PREAMBLE_MIN 20u
#define HONDA_ACURA_DATA_BITS    64u

#define HONDA_ACURA_BTN_LOCK   0x10u
#define HONDA_ACURA_BTN_UNLOCK 0x20u
#define HONDA_ACURA_BTN_TRUNK  0x40u
#define HONDA_ACURA_BTN_PANIC  0x08u

struct SubGhzProtocolDecoderHondaAcura {
    SubGhzProtocolDecoderBase base;
    SubGhzBlockDecoder decoder;
    SubGhzBlockGeneric generic;
    uint16_t header_count;
    uint8_t crc_received;
    bool crc_valid;
};

struct SubGhzProtocolEncoderHondaAcura {
    SubGhzProtocolEncoderBase base;
    SubGhzProtocolBlockEncoder encoder;
    SubGhzBlockGeneric generic;
};

typedef enum {
    HondaAcuraDecoderStepReset = 0,
    HondaAcuraDecoderStepCheckPreamble,
    HondaAcuraDecoderStepSaveDuration,
    HondaAcuraDecoderStepCheckDuration,
} HondaAcuraDecoderStep;

const SubGhzProtocolDecoder subghz_protocol_honda_acura_decoder = {
    .alloc = subghz_protocol_decoder_honda_acura_alloc,
    .free = subghz_protocol_decoder_honda_acura_free,
    .feed = subghz_protocol_decoder_honda_acura_feed,
    .reset = subghz_protocol_decoder_honda_acura_reset,
    .get_hash_data = subghz_protocol_decoder_honda_acura_get_hash_data,
    .serialize = subghz_protocol_decoder_honda_acura_serialize,
    .deserialize = subghz_protocol_decoder_honda_acura_deserialize,
    .get_string = subghz_protocol_decoder_honda_acura_get_string,
};

const SubGhzProtocolEncoder subghz_protocol_honda_acura_encoder = {
    .alloc = subghz_protocol_encoder_honda_acura_alloc,
    .free = subghz_protocol_encoder_honda_acura_free,
    .deserialize = subghz_protocol_encoder_honda_acura_deserialize,
    .stop = subghz_protocol_encoder_honda_acura_stop,
    .yield = subghz_protocol_encoder_honda_acura_yield,
};

const SubGhzProtocol subghz_protocol_honda_acura = {
    .name = HONDA_ACURA_PROTOCOL_NAME,
    .type = SubGhzProtocolTypeDynamic,
    .flag = SubGhzProtocolFlag_315 | SubGhzProtocolFlag_433 | SubGhzProtocolFlag_AM |
            SubGhzProtocolFlag_Decodable | SubGhzProtocolFlag_Load | SubGhzProtocolFlag_Save |
            SubGhzProtocolFlag_Send,
    .decoder = &subghz_protocol_honda_acura_decoder,
    .encoder = &subghz_protocol_honda_acura_encoder,
};

// ─── CRC ────────────────────────────────────────────────────────────────────

static uint8_t honda_acura_crc8(const uint8_t* data, size_t len) {
    uint8_t crc = 0xFF;
    for(size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for(int j = 0; j < 8; j++) {
            if(crc & 0x80)
                crc = (uint8_t)((crc << 1) ^ 0x2F);
            else
                crc <<= 1;
        }
    }
    return crc;
}

static uint8_t honda_acura_calculate_crc(uint64_t data) {
    uint8_t buf[7];
    for(int i = 0; i < 7; i++) buf[i] = (uint8_t)(data >> (56 - i * 8));
    return honda_acura_crc8(buf, 7);
}

static void honda_acura_extract_fields(SubGhzProtocolDecoderHondaAcura* instance) {
    uint64_t d = instance->generic.data;
    instance->generic.serial = (uint32_t)(d >> 32);
    instance->generic.cnt = (uint16_t)((d >> 16) & 0xFFFF);
    instance->generic.btn = (uint8_t)((d >> 8) & 0xFF);
    instance->crc_received = (uint8_t)(d & 0xFF);
    instance->crc_valid = (instance->crc_received == honda_acura_calculate_crc(d));
}

// ─── Encoder ────────────────────────────────────────────────────────────────

void* subghz_protocol_encoder_honda_acura_alloc(SubGhzEnvironment* environment) {
    UNUSED(environment);
    SubGhzProtocolEncoderHondaAcura* instance = malloc(sizeof(SubGhzProtocolEncoderHondaAcura));
    instance->base.protocol = &subghz_protocol_honda_acura;
    instance->generic.protocol_name = instance->base.protocol->name;
    instance->encoder.size_upload = 600;
    instance->encoder.upload = malloc(instance->encoder.size_upload * sizeof(LevelDuration));
    instance->encoder.repeat = 2;
    instance->encoder.is_running = false;
    return instance;
}

void subghz_protocol_encoder_honda_acura_free(void* context) {
    furi_assert(context);
    SubGhzProtocolEncoderHondaAcura* instance = context;
    free(instance->encoder.upload);
    free(instance);
}

void subghz_protocol_encoder_honda_acura_stop(void* context) {
    SubGhzProtocolEncoderHondaAcura* instance = context;
    instance->encoder.is_running = false;
}

LevelDuration subghz_protocol_encoder_honda_acura_yield(void* context) {
    SubGhzProtocolEncoderHondaAcura* instance = context;
    if(instance->encoder.repeat == 0 || !instance->encoder.is_running) {
        instance->encoder.is_running = false;
        return level_duration_reset();
    }
    LevelDuration ret = instance->encoder.upload[instance->encoder.front];
    if(++instance->encoder.front == instance->encoder.size_upload) {
        instance->encoder.repeat--;
        instance->encoder.front = 0;
    }
    return ret;
}

static bool honda_acura_encoder_get_upload(SubGhzProtocolEncoderHondaAcura* instance) {
    furi_assert(instance);

    if(subghz_custom_btn_get_original() == 0)
        subghz_custom_btn_set_original(instance->generic.btn);
    subghz_custom_btn_set_max(4);

    uint8_t btn = (subghz_custom_btn_get() == SUBGHZ_CUSTOM_BTN_OK) ?
                      subghz_custom_btn_get_original() :
                      subghz_custom_btn_get();
    instance->generic.btn = btn;

    if(instance->generic.cnt < 0xFFFF)
        instance->generic.cnt += furi_hal_subghz_get_rolling_counter_mult();
    else
        instance->generic.cnt = 0;

    uint8_t frame[8];
    frame[0] = (instance->generic.serial >> 24) & 0xFF;
    frame[1] = (instance->generic.serial >> 16) & 0xFF;
    frame[2] = (instance->generic.serial >> 8) & 0xFF;
    frame[3] = instance->generic.serial & 0xFF;
    frame[4] = (instance->generic.cnt >> 8) & 0xFF;
    frame[5] = instance->generic.cnt & 0xFF;
    frame[6] = btn;
    frame[7] = honda_acura_crc8(frame, 7);

    size_t idx = 0;
    for(size_t i = 0; i < HONDA_ACURA_PREAMBLE_MIN; i++) {
        instance->encoder.upload[idx++] =
            level_duration_make(true, subghz_protocol_honda_acura_const.te_short);
        instance->encoder.upload[idx++] =
            level_duration_make(false, subghz_protocol_honda_acura_const.te_short);
    }
    for(int byte = 0; byte < 8; byte++) {
        for(int bit = 7; bit >= 0; bit--) {
            bool b = (frame[byte] >> bit) & 1;
            uint32_t w = b ? (uint32_t)subghz_protocol_honda_acura_const.te_long :
                             (uint32_t)subghz_protocol_honda_acura_const.te_short;
            instance->encoder.upload[idx++] = level_duration_make(true, w);
            instance->encoder.upload[idx++] = level_duration_make(false, w);
        }
    }
    instance->encoder.upload[idx++] =
        level_duration_make(false, subghz_protocol_honda_acura_const.te_long * 8);
    instance->encoder.size_upload = idx;
    return true;
}

SubGhzProtocolStatus
    subghz_protocol_encoder_honda_acura_deserialize(void* context, FlipperFormat* flipper_format) {
    furi_assert(context);
    SubGhzProtocolEncoderHondaAcura* instance = context;
    SubGhzProtocolStatus ret = subghz_block_generic_deserialize_check_count_bit(
        &instance->generic,
        flipper_format,
        subghz_protocol_honda_acura_const.min_count_bit_for_found);
    if(ret != SubGhzProtocolStatusOk) return ret;
    if(!honda_acura_encoder_get_upload(instance)) return SubGhzProtocolStatusErrorEncoderGetUpload;
    instance->encoder.is_running = true;
    return SubGhzProtocolStatusOk;
}

// ─── Decoder ────────────────────────────────────────────────────────────────

void* subghz_protocol_decoder_honda_acura_alloc(SubGhzEnvironment* environment) {
    UNUSED(environment);
    SubGhzProtocolDecoderHondaAcura* instance = malloc(sizeof(SubGhzProtocolDecoderHondaAcura));
    instance->base.protocol = &subghz_protocol_honda_acura;
    instance->generic.protocol_name = instance->base.protocol->name;
    return instance;
}

void subghz_protocol_decoder_honda_acura_free(void* context) {
    furi_assert(context);
    free(context);
}

void subghz_protocol_decoder_honda_acura_reset(void* context) {
    furi_assert(context);
    SubGhzProtocolDecoderHondaAcura* instance = context;
    instance->decoder.parser_step = HondaAcuraDecoderStepReset;
    instance->header_count = 0;
}

void subghz_protocol_decoder_honda_acura_feed(void* context, bool level, uint32_t duration) {
    furi_assert(context);
    SubGhzProtocolDecoderHondaAcura* instance = context;

    switch(instance->decoder.parser_step) {
    case HondaAcuraDecoderStepReset:
        if(level &&
           DURATION_DIFF(duration, subghz_protocol_honda_acura_const.te_short) <
               subghz_protocol_honda_acura_const.te_delta) {
            instance->decoder.parser_step = HondaAcuraDecoderStepCheckPreamble;
            instance->header_count = 1;
            instance->decoder.te_last = duration;
        }
        break;

    case HondaAcuraDecoderStepCheckPreamble:
        if(level) {
            if(DURATION_DIFF(duration, subghz_protocol_honda_acura_const.te_short) <
               subghz_protocol_honda_acura_const.te_delta) {
                instance->decoder.te_last = duration;
            } else {
                instance->decoder.parser_step = HondaAcuraDecoderStepReset;
            }
        } else {
            if(DURATION_DIFF(duration, subghz_protocol_honda_acura_const.te_short) <
               subghz_protocol_honda_acura_const.te_delta) {
                instance->header_count++;
                if(instance->header_count >= HONDA_ACURA_PREAMBLE_MIN) {
                    instance->decoder.parser_step = HondaAcuraDecoderStepSaveDuration;
                    instance->decoder.decode_data = 0;
                    instance->decoder.decode_count_bit = 0;
                }
            } else {
                instance->decoder.parser_step = HondaAcuraDecoderStepReset;
            }
        }
        break;

    case HondaAcuraDecoderStepSaveDuration:
        if(level) {
            instance->decoder.te_last = duration;
            instance->decoder.parser_step = HondaAcuraDecoderStepCheckDuration;
        } else {
            instance->decoder.parser_step = HondaAcuraDecoderStepReset;
        }
        break;

    case HondaAcuraDecoderStepCheckDuration:
        if(!level) {
            bool bit;
            if(DURATION_DIFF(
                   instance->decoder.te_last, subghz_protocol_honda_acura_const.te_long) <
               subghz_protocol_honda_acura_const.te_delta) {
                bit = true;
            } else if(
                DURATION_DIFF(
                    instance->decoder.te_last, subghz_protocol_honda_acura_const.te_short) <
                subghz_protocol_honda_acura_const.te_delta) {
                bit = false;
            } else {
                instance->decoder.parser_step = HondaAcuraDecoderStepReset;
                break;
            }
            subghz_protocol_blocks_add_bit(&instance->decoder, bit);
            instance->decoder.parser_step = HondaAcuraDecoderStepSaveDuration;

            if(instance->decoder.decode_count_bit == HONDA_ACURA_DATA_BITS) {
                instance->generic.data = instance->decoder.decode_data;
                instance->generic.data_count_bit = HONDA_ACURA_DATA_BITS;
                honda_acura_extract_fields(instance);
                if(instance->crc_valid) {
                    if(instance->base.callback)
                        instance->base.callback(&instance->base, instance->base.context);
                } else {
                    FURI_LOG_W(TAG, "CRC mismatch, frame dropped");
                }
                instance->decoder.parser_step = HondaAcuraDecoderStepReset;
            }
        } else {
            instance->decoder.parser_step = HondaAcuraDecoderStepReset;
        }
        break;
    }
}

uint8_t subghz_protocol_decoder_honda_acura_get_hash_data(void* context) {
    furi_assert(context);
    SubGhzProtocolDecoderHondaAcura* instance = context;
    return subghz_protocol_blocks_get_hash_data(
        &instance->decoder, (instance->decoder.decode_count_bit / 8) + 1);
}

SubGhzProtocolStatus subghz_protocol_decoder_honda_acura_serialize(
    void* context,
    FlipperFormat* flipper_format,
    SubGhzRadioPreset* preset) {
    furi_assert(context);
    SubGhzProtocolDecoderHondaAcura* instance = context;
    return subghz_block_generic_serialize(&instance->generic, flipper_format, preset);
}

SubGhzProtocolStatus
    subghz_protocol_decoder_honda_acura_deserialize(void* context, FlipperFormat* flipper_format) {
    furi_assert(context);
    SubGhzProtocolDecoderHondaAcura* instance = context;
    SubGhzProtocolStatus ret =
        subghz_block_generic_deserialize(&instance->generic, flipper_format);
    if(ret == SubGhzProtocolStatusOk) honda_acura_extract_fields(instance);
    return ret;
}

// ─── Display ────────────────────────────────────────────────────────────────

static const char* honda_acura_button_name(uint8_t btn) {
    switch(btn) {
    case HONDA_ACURA_BTN_LOCK: return "Lock";
    case HONDA_ACURA_BTN_UNLOCK: return "Unlock";
    case HONDA_ACURA_BTN_TRUNK: return "Trunk";
    case HONDA_ACURA_BTN_PANIC: return "Panic";
    default: return "Unknown";
    }
}

void subghz_protocol_decoder_honda_acura_get_string(void* context, FuriString* output) {
    furi_assert(context);
    SubGhzProtocolDecoderHondaAcura* instance = context;

    furi_string_cat_printf(
        output,
        "Honda/Acura  315/433MHz\r\n"
        "Sn:%08lX  Cnt:%04lX\r\n"
        "Btn:%02X [%s]\r\n"
        "CRC:%02X %s  %dbit",
        instance->generic.serial,
        instance->generic.cnt,
        instance->generic.btn,
        honda_acura_button_name(instance->generic.btn),
        instance->crc_received,
        instance->crc_valid ? "(OK)" : "(FAIL)",
        instance->generic.data_count_bit);
}
