#include "encoders.h"

static EncoderRotateCallback enc_rotate_cb = nullptr;
static EncoderButtonCallback enc_button_cb = nullptr;

struct EncoderDriver {
  uint8_t pin_a;
  uint8_t pin_b;
  uint8_t pin_btn;
  uint8_t last_ab;
  volatile int accumulator;
  bool btn_state;
  unsigned long btn_debounce_time;
};

static EncoderDriver encoders[NUM_ENCODERS];

// Gray kód lookup table pro přesné dekódování bez falešných zákmitů
static const int8_t ENC_TABLE[4][4] = {
  {  0, -1,  1,  0 },
  {  1,  0,  0, -1 },
  { -1,  0,  0,  1 },
  {  0,  1, -1,  0 },
};

static void IRAM_ATTR isr_encoder_common(uint8_t idx) {
  uint8_t a = digitalRead(encoders[idx].pin_a);
  uint8_t b = digitalRead(encoders[idx].pin_b);
  uint8_t curr_ab = (b << 1) | a;

  int8_t step = ENC_TABLE[encoders[idx].last_ab][curr_ab];
  encoders[idx].accumulator += step;
  encoders[idx].last_ab = curr_ab;
}

static void IRAM_ATTR isr_enc0() { isr_encoder_common(0); }
static void IRAM_ATTR isr_enc1() { isr_encoder_common(1); }
static void IRAM_ATTR isr_enc2() { isr_encoder_common(2); }

void encoders_setup(EncoderRotateCallback rotate_cb, EncoderButtonCallback btn_cb) {
  enc_rotate_cb = rotate_cb;
  enc_button_cb = btn_cb;

  for (uint8_t i = 0; i < NUM_ENCODERS; i++) {
    encoders[i].pin_a = ENC_PINS[i].pin_a;
    encoders[i].pin_b = ENC_PINS[i].pin_b;
    encoders[i].pin_btn = ENC_PINS[i].pin_btn;
    encoders[i].accumulator = 0;
    encoders[i].btn_state = HIGH;
    encoders[i].btn_debounce_time = 0;

    gpio_reset_pin((gpio_num_t)encoders[i].pin_a);
    gpio_reset_pin((gpio_num_t)encoders[i].pin_b);
    gpio_reset_pin((gpio_num_t)encoders[i].pin_btn);

    pinMode(encoders[i].pin_a, INPUT_PULLUP);
    pinMode(encoders[i].pin_b, INPUT_PULLUP);
    pinMode(encoders[i].pin_btn, INPUT_PULLUP);

    uint8_t a = digitalRead(encoders[i].pin_a);
    uint8_t b = digitalRead(encoders[i].pin_b);
    encoders[i].last_ab = (b << 1) | a;
  }

  // Připojení přerušení pro každý kanál (CHANGE reaguje na náběžnou i sestupnou hranu)
  attachInterrupt(digitalPinToInterrupt(encoders[0].pin_a), isr_enc0, CHANGE);
  attachInterrupt(digitalPinToInterrupt(encoders[0].pin_b), isr_enc0, CHANGE);

  attachInterrupt(digitalPinToInterrupt(encoders[1].pin_a), isr_enc1, CHANGE);
  attachInterrupt(digitalPinToInterrupt(encoders[1].pin_b), isr_enc1, CHANGE);

  attachInterrupt(digitalPinToInterrupt(encoders[2].pin_a), isr_enc2, CHANGE);
  attachInterrupt(digitalPinToInterrupt(encoders[2].pin_b), isr_enc2, CHANGE);
}

void encoders_update() {
  unsigned long now = millis();

  for (uint8_t i = 0; i < NUM_ENCODERS; i++) {
    // 1. Čtení otočení z akumulátoru (většina enkodérů má 4 přechody na 1 mechanický zub/klik)
    noInterrupts();
    int acc = encoders[i].accumulator;
    if (acc >= 4) {
      encoders[i].accumulator -= 4;
      interrupts();
      if (enc_rotate_cb != nullptr) enc_rotate_cb(i, 1); // Rotace po směru (CW)
    } else if (acc <= -4) {
      encoders[i].accumulator += 4;
      interrupts();
      if (enc_rotate_cb != nullptr) enc_rotate_cb(i, -1); // Rotace proti směru (CCW)
    } else {
      interrupts();
    }

    // 2. Čtení stisku integrovaného tlačítka s debouncem
    bool btn_raw = digitalRead(encoders[i].pin_btn);
    if (btn_raw != encoders[i].btn_state) {
      if ((now - encoders[i].btn_debounce_time) > ENC_DEBOUNCE_MS) {
        encoders[i].btn_state = btn_raw;
        encoders[i].btn_debounce_time = now;
        if (enc_button_cb != nullptr) {
          enc_button_cb(i, btn_raw == LOW);
        }
      }
    }
  }
}
