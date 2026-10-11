#pragma once
#include <Arduino.h>
#include <Adafruit_GFX.h>

// =========================================================================
//  PeciDeck Vlastní ikony (Bitmapy / C-Arrays)
// =========================================================================
//  Zde můžete přidávat vlastní C pole obrázků (vygenerovaná přes image2cpp
//  nebo automaticky ze složky 'custom_icons' pomocí convert_icons.py).
//
//  Typy podporovaných formátů:
//  1) 1-bit monochromatická bitmapa (PROGMEM const unsigned char):
//     tft.drawBitmap(cx - w/2, cy - h/2, data, w, h, barva);
//
//  2) 16-bit RGB565 plnobarevná bitmapa (PROGMEM const uint16_t):
//     tft.drawRGBBitmap(cx - w/2, cy - h/2, data, w, h);
// =========================================================================

// Sem vkládejte svá C pole ikon:

// [PŘÍKLAD] Monochromatická ikona 16x16 px:
// static const unsigned char PROGMEM icon_priklad_16x16[] = {
//   0x00, 0x00, 0x07, 0xe0, 0x0f, 0xf0, 0x1f, 0xf8,
//   0x3f, 0xfc, 0x7f, 0xfe, 0x7f, 0xfe, 0xff, 0xff,
//   0xff, 0xff, 0x7f, 0xfe, 0x7f, 0xfe, 0x3f, 0xfc,
//   0x1f, 0xf8, 0x0f, 0xf0, 0x07, 0xe0, 0x00, 0x00
// };

// Funkce, která se volá před vykreslením výchozí vektorové grafiky.
// Vrátí true, pokud byla vlastní ikona nalezena a vykreslena.
inline bool draw_custom_icon(Adafruit_GFX& tft, int16_t cx, int16_t cy, const char* name) {
  // Příklad použití:
  // if (strcmp(name, "priklad") == 0) {
  //   tft.drawBitmap(cx - 8, cy - 8, icon_priklad_16x16, 16, 16, 0xFBE0); // Oranžová
  //   return true;
  // }

  return false; // Není vlastní ikona -> pokračuje se na výchozí vektorové ikony
}
