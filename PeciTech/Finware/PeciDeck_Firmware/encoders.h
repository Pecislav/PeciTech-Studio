#pragma once
#include <Arduino.h>
#include "config.h"

typedef void (*EncoderRotateCallback)(uint8_t enc_index, int8_t direction);
typedef void (*EncoderButtonCallback)(uint8_t enc_index, bool pressed);

void encoders_setup(EncoderRotateCallback rotate_cb, EncoderButtonCallback btn_cb);
void encoders_update();
