#pragma once
#include <Arduino.h>
#include "config.h"

typedef void (*ButtonEventCallback)(uint8_t btn_index, bool pressed);

void buttons_setup(ButtonEventCallback callback);
void buttons_update();
void buttons_print_diag();
