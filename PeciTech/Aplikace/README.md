# 🎛️ PeciTech Studio – Ovládací aplikace pro Peci Deck MK.1

Desktopová aplikace vytvořená v **CustomTkinter (Python)** přesně podle vize PeciTech Studio.

---

## ✨ Klíčové funkce

1. **Auto-detekce Peci Deck MK.1:**
   * Aplikace automaticky prochází COM porty a identifikuje tvůj Peci Deck přes handshake dotaz.
   * Stavový indikátor v záhlaví:
     * 🔴 **Odpojeno** (zařízení není připojeno)
     * 🟢 **Připojeno (COMx)** (zařízení nalezeno a plně aktivní)
2. **Živá synchronizace s displejem ST7789:**
   * Kdykoliv v aplikaci změníš ikonu nebo popisek tlačítka, změna se okamžitě přenese na hardware displej Peci Decku.
   * Možnost regulace jasu podsvícení (PWM) přímo z aplikace nebo enkodérem.
3. **Plné ovládání Windows a médií:**
   * **Enkodéry:** Otáčení zvyšuje/snižuje hlasitost Windows, stisk funguje jako Mute (nebo přepínání skladeb a play/pause).
   * **Tlačítka SW1–SW8:** Play/Pause, Mute, Next, Prev, spouštění libovolných klávesových zkratek (hotkeys), otevírání programů, souborů či URL.
4. **OBS Studio Integrace:**
   * Přímé propojení přes OBS WebSocket (port 4455).
   * Možnost spouštět/zastavovat stream a nahrávání jediným tlačítkem.
5. **Profily & Běh na pozadí:**
   * Ukládání nastavení do JSON profilů (s možností exportu a importu).
   * Minimalizace do systémové lišty (System Tray) pro minimální zatížení CPU a RAM během hraní či streamování.

---

## 🚀 Jak aplikaci spustit

Jednoduše dvakrát klikni na soubor:
```text
C:\PeciTech\PeciTech\Aplikace\Spustit_Aplikaci.bat
```
Nebo v příkazové řádce:
```bash
cd C:\PeciTech\PeciTech\Aplikace
python main.py
```
