#pragma once
#include <Arduino.h>

// =============================================================================
//  PECI DECK MK.1 - KONFIGURACE HARDWARU (Dle KiCad schématu a DPS)
// =============================================================================

#define FW_VERSION       "1.1.0"
#define DEVICE_NAME      "PeciDeck_MK1"
#define SERIAL_BAUD      115200

// ------------------- Tlačítka (Cherry MX - SW1 až SW8) -----------------------
// Rozmístění na desce dle KiCad PCB:
// HORNÍ ŘADA:   SW1 (GPIO 1),  SW3 (GPIO 41), SW5 (GPIO 5), SW7 (GPIO 7)
// DOLNÍ ŘADA:   SW2 (GPIO 2),  SW4 (GPIO 4),  SW6 (GPIO 6), SW8 (GPIO 8)
//
// V kódu a aplikaci jsou tlačítka seřazena přirozeně po řádcích (1-4 nahoře, 5-8 dole):
// Index 0 -> SW1 (GPIO 1)   - Horní řada, 1. zleva
// Index 1 -> SW3 (GPIO 41)  - Horní řada, 2. zleva
// Index 2 -> SW5 (GPIO 5)   - Horní řada, 3. zleva
// Index 3 -> SW7 (GPIO 7)   - Horní řada, 4. zleva (vpravo)
// Index 4 -> SW2 (GPIO 2)   - Dolní řada, 1. zleva
// Index 5 -> SW4 (GPIO 4)   - Dolní řada, 2. zleva
// Index 6 -> SW6 (GPIO 6)   - Dolní řada, 3. zleva
// Index 7 -> SW8 (GPIO 8)   - Dolní řada, 4. zleva (vpravo)

#define NUM_BUTTONS      8

struct ButtonMeta {
  uint8_t gpio;
  const char* kicad_name;
  const char* position_cz;
};

const ButtonMeta BTN_CONFIG[NUM_BUTTONS] = {
  { 1,  "SW1", "Horni rada, 1. zleva" },
  { 41, "SW3", "Horni rada, 2. zleva" },
  { 5,  "SW5", "Horni rada, 3. zleva" },
  { 7,  "SW7", "Horni rada, 4. zleva" },
  { 2,  "SW2", "Dolni rada, 1. zleva" },
  { 4,  "SW4", "Dolni rada, 2. zleva" },
  { 6,  "SW6", "Dolni rada, 3. zleva" },
  { 8,  "SW8", "Dolni rada, 4. zleva" }
};

const uint8_t BTN_PINS[NUM_BUTTONS] = { 1, 41, 5, 7, 2, 4, 6, 8 };

// ------------------- Rotační enkodéry (SW9, SW10, SW11) -----------------------
// Každý enkodér má piny A, B a tlačítko (Switch). C a S2 jsou spojeny s GND.
#define NUM_ENCODERS     3

struct EncoderPinConfig {
  uint8_t pin_a;
  uint8_t pin_b;
  uint8_t pin_btn;
};

const EncoderPinConfig ENC_PINS[NUM_ENCODERS] = {
  { 9,  10, 11 },   // SW9  (Enkodér 1 - vlevo):     A=GPIO9,  B=GPIO10, Tlačítko=GPIO11
  { 12, 13, 14 },   // SW10 (Enkodér 2 - uprostřed): A=GPIO12, B=GPIO13, Tlačítko=GPIO14
  { 17, 18, 21 }    // SW11 (Enkodér 3 - vpravo):    A=GPIO17, B=GPIO18, Tlačítko=GPIO21
};

// ------------------- Displej (ST7789, konektor J1) ---------------------------
// J1 pin 1: GND
// J1 pin 2: +3.3V
// J1 pin 3: SCL (SPI SCK)  -> GPIO 16
// J1 pin 4: SDA (SPI MOSI) -> GPIO 15
// J1 pin 5: RST            -> GPIO 37 (U1 Pin 34 na DPS)
// J1 pin 6: DC             -> GPIO 38 (U1 Pin 35 na DPS)
// J1 pin 7: CS             -> GPIO 47
// J1 pin 8: BL (Podsvícení)-> GPIO 48
#define DISP_PIN_SCL     16
#define DISP_PIN_SDA     15
#define DISP_PIN_RST     37
#define DISP_PIN_DC      38
#define DISP_PIN_CS      47
#define DISP_PIN_BL      48

// Rozlišení úzkého ST7789 displeje
#define DISP_WIDTH       284
#define DISP_HEIGHT      76
#define DISP_HW_W        76
#define DISP_HW_H        284

// PeciTech barvy v 16bit RGB565 formátu
#define COL_BLACK        0x0000
#define COL_ORANGE       0xFBC5   // PeciTech signature oranžová (#FF7A29)
#define COL_WHITE        0xFFFF
#define COL_GRAY         0x39E7
#define COL_DARK_GRAY    0x18C3
#define COL_GREEN        0x2FA8
#define COL_RED          0xF800
#define COL_BLUE         0x001F
#define COL_PURPLE       0x923F   // Twitch fialová (#9146FF)
#define COL_BLURPLE      0x5B5F   // Discord blurple (#5865F2)
#define COL_CYAN         0x07FF   // Tyrkysová / azurová
#define COL_YELLOW       0xFFE0   // Zlatá / žlutá

// Mřížka pro tlačítka (4 sloupce x 2 řádky = 8 buněk)
#define GRID_COLS        4
#define GRID_ROWS        2
#define GRID_CELLS       8

// Časování pro debounce (odrušení zákmitů v ms)
#define BTN_DEBOUNCE_MS  35
#define ENC_DEBOUNCE_MS  40
