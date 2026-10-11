#pragma once
#include <Arduino.h>

void protocol_setup();
void protocol_send_hello();
void protocol_send_button(uint8_t btn_idx, bool pressed);
void protocol_send_encoder(uint8_t enc_idx, int8_t direction);
void protocol_send_encoder_btn(uint8_t enc_idx, bool pressed);
void protocol_process_incoming();
