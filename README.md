# 🎛️ PeciTech Studio

Kompletní open-source ekosystém pro makroklávesnici **PeciDeck MK.1** s barevným displejem ST7789, 8 mechanickými klávesami a 3 rotačními enkodéry.

Projekt zahrnuje jak moderní desktopovou aplikaci pro Windows v **CustomTkinter**, tak optimalizovaný firmware pro mikrokontrolér **ESP32** (Arduino framework).

---

## 📁 Struktura projektu

- **`PeciTech/Aplikace/`** – Desktopová ovládací aplikace v Pythonu (CustomTkinter)
  - Živá synchronizace s hardwarem přes sériový port (USB COM)
  - Konfigurace tlačítek, ikon, barev a popisků
  - Integrace pro OBS Studio (WebSocket v5), Discord a Twitch
  - Podpora řetězců akcí (Multi-Action), klávesových zkratek, otevírání programů a složek
  - Podpora profilů a minimalizace do systémové lišty (System Tray)
- **`PeciTech/Finware/`** – Firmware pro desku ESP32
  - Ovladače pro TFT displej ST7789 přes SPI
  - Rychlé čtení 8 tlačítek s hardwarovým debouncingem
  - Podpora 3 rotačních enkodérů se stiskem
  - Obousměrný sériový protokol pro live streaming ikon a konfigurace

---

## 🚀 Rychlý start

### 1. Spuštění aplikace (Windows)
1. Ujistěte se, že máte nainstalovaný **Python 3.10+**.
2. Otevřete složku `PeciTech/Aplikace` a spusťte:
   ```bash
   pip install customtkinter pillow pyserial pywin32 websocket-client pystray requests
   python main.py
   ```
   Nebo jednoduše poklepejte na `PeciTech/Aplikace/Spustit_Aplikaci.bat`.

### 2. Nahrání firmwaru do ESP32
1. Otevřete soubor `PeciTech/Finware/PeciDeck_Firmware/PeciDeck_Firmware.ino` v prostředí **Arduino IDE**.
2. Nastavte desku na **ESP32 Dev Module** a správný COM port.
3. Postupujte podle pokynů v `PeciTech/Finware/NAVOD_K_NAHRANI.md`.

---

## 📄 Licence & Autoři
Vyvinuto s láskou pro komunitu PeciTech.
