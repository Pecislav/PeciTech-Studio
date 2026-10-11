"""
PeciDeck - Automatický převodník PNG/JPG ikon do C kódu (icons.h) pro displej.

Použití:
1. Nahrajte své obrázky (PNG, JPG) do složky 'custom_icons' (např. twitch.png, steam.png, mic.png).
   Doporučená velikost obrázků: 16x16 až 24x24 px (pokud jsou větší, skript je automaticky zmenší).
2. Spusťte tento skript:
   python convert_icons.py
3. Skript automaticky vygeneruje plnobarevná RGB565 C-pole a uloží je přímo do 'icons.h'.
4. Nahrajte firmware v Arduino IDE do PeciDecku!
"""

import os
import re
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(SCRIPT_DIR, "custom_icons")
HEADER_FILE = os.path.join(SCRIPT_DIR, "icons.h")
TARGET_SIZE = 20  # Max šířka a výška pro buňku displeje (cca 20x20 px)

def sanitize_name(filename):
    name = os.path.splitext(filename)[0].lower()
    return re.sub(r'[^a-z0-9_]', '_', name)

def to_rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def process_image(filepath):
    img = Image.open(filepath).convert("RGBA")
    # Zmenšit proporčně, aby se vešel do TARGET_SIZE x TARGET_SIZE
    img.thumbnail((TARGET_SIZE, TARGET_SIZE), Image.Resampling.LANCZOS)
    w, h = img.size
    
    pixels = []
    for y in range(h):
        for x in range(w):
            r, g, b, a = img.getpixel((x, y))
            if a < 64:
                # Průhledné pozadí -> černá (0x0000)
                pixels.append(0x0000)
            else:
                pixels.append(to_rgb565(r, g, b))
    return w, h, pixels

def main():
    if not os.path.exists(ICONS_DIR):
        os.makedirs(ICONS_DIR, exist_ok=True)
        print(f"Vytvořena složka: {ICONS_DIR}")

    files = [f for f in os.listdir(ICONS_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
    
    if not files:
        print(f"Ve složce '{ICONS_DIR}' nebyly nalezeny žádné obrázky.")
        print("Vložte tam PNG soubory a spusťte skript znovu.")
        return

    print(f"Nalezeno {len(files)} obrázků ke konverzi...")

    arrays_code = []
    checks_code = []

    for filename in sorted(files):
        var_name = sanitize_name(filename)
        filepath = os.path.join(ICONS_DIR, filename)
        try:
            w, h, pixels = process_image(filepath)
            
            # Generování pole
            hex_values = [f"0x{val:04X}" for val in pixels]
            lines = []
            for i in range(0, len(hex_values), 12):
                lines.append("  " + ", ".join(hex_values[i:i+12]))
            array_body = ",\n".join(lines)
            
            arrays_code.append(
                f"// Ikona: {filename} ({w}x{h} px RGB565)\n"
                f"static const uint16_t PROGMEM icon_{var_name}[] = {{\n"
                f"{array_body}\n"
                f"}};\n"
            )

            checks_code.append(
                f'  if (strcmp(name, "{var_name}") == 0) {{\n'
                f'    tft.drawRGBBitmap(cx - {w // 2}, cy - {h // 2}, icon_{var_name}, {w}, {h});\n'
                f'    return true;\n'
                f'  }}\n'
            )
            print(f"  [OK] {filename} -> icon_{var_name} ({w}x{h} px)")
        except Exception as e:
            print(f"  [CHYBA] {filename}: {e}")

    # Sestavení celého icons.h
    content = f"""#pragma once
#include <Arduino.h>
#include <Adafruit_GFX.h>

// =========================================================================
//  PeciDeck Vlastní ikony (Automaticky generováno přes convert_icons.py)
// =========================================================================
//  Pro přidání dalších ikon vložte PNG soubory do složky 'custom_icons'
//  a spusťte: python convert_icons.py
// =========================================================================

{"".join(arrays_code)}
inline bool draw_custom_icon(Adafruit_GFX& tft, int16_t cx, int16_t cy, const char* name) {{
{"".join(checks_code)}
  return false; // Pokud není nalezena, použije se výchozí vektorová ikona
}}
"""

    with open(HEADER_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\nÚspěšně aktualizován soubor: {HEADER_FILE}")
    print("Nyní stačí otevřít Arduino IDE a nahrát firmware do PeciDecku!")

if __name__ == "__main__":
    main()
