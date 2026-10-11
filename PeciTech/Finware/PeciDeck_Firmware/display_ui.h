#pragma once
#include <Arduino.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <SPI.h>
#include "config.h"

void display_setup();
void display_set_brightness(uint8_t brightness);
void display_draw_offline_screen();
void display_draw_grid();
void display_update_cell(uint8_t idx, const char* label, const char* icon_name);
void display_draw_bmp(uint8_t idx, const uint8_t* bmp24);
void display_clear();
void display_show_message(const char* title, const char* msg);
void display_set_inversion(bool invert);
void display_set_connected(bool connected);
bool display_is_connected();
void display_run_interactive_test();
void display_run_pin_test();
void display_run_probe_test();
void display_run_scan_test();
void display_set_all_pins(bool high_level);
void display_apply_profile(uint8_t profile_id);
uint8_t display_get_active_profile();
uint8_t display_get_profile_count();
void display_print_profiles();
void display_fill_color(uint16_t color, const char* name);
void display_cell_press(uint8_t idx, bool pressed);
void display_update();
