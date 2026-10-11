# 🛠️ PeciDeck MK.1 – Návod na nahrání firmwaru do ESP32-S3

Tento návod tě krok za krokem provede nahráním firmwaru do tvého zařízení **Peci Deck MK.1** pomocí programu **Arduino IDE**.

---

## 1. Příprava programovacího prostředí

Pokud ještě nemáš nainstalováno **Arduino IDE**, stáhni si verzi 2.x z [arduino.cc](https://www.arduino.cc/en/software).

### A. Přidání podpory pro ESP32
1. Otevři Arduino IDE.
2. Jdi do **File -> Preferences** (Soubor -> Předvolby).
3. Do pole **Additional boards manager URLs** vlož tento odkaz:
   ```text
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Klikni na **OK**.
5. V levém panelu klikni na ikonu desek (**Boards Manager**), do vyhledávání zadej `esp32` a nainstaluj balíček **esp32 by Espressif Systems**.

---

## 2. Instalace potřebných knihoven

V levém panelu klikni na ikonu knihoven (**Library Manager**) a nainstaluj:
1. **Adafruit GFX Library** (od Adafruit) – pokud se zeptá na instalaci závislostí (*Install all*), potvrď to.
2. **Adafruit ST7735 and ST7789 Library** (od Adafruit).

---

## 3. Nastavení desky v Arduino IDE

V horním menu **Tools (Nástroje)** nastav přesně tyto parametry:

| Položka v menu | Hodnota | Poznámka |
| :--- | :--- | :--- |
| **Board** | **ESP32S3 Dev Module** | Základní modul pro S3 |
| **USB CDC On Boot** | **Enabled** | ⚠️ **KRITICKÉ** – zajišťuje, že sériová linka komunikuje přímo přes nativní USB-C! |
| **CPU Frequency** | **240MHz (WiFi)** | Standard |
| **Flash Mode** | **QIO 80MHz** | Nebo dle tvého modulu |
| **Flash Size** | **8MB (64Mb)** nebo **4MB** | Zvol podle verze tvého ESP32-S3 |
| **Partition Scheme** | **Default 4MB with spiffs** (nebo 8MB) | Standard |
| **Upload Speed** | **921600** (nebo 115200) | Rychlost nahrávání |
| **Port** | Vyber příslušný **COM port** | Objeví se po zapojení USB kabelu |

---

## 4. Otevření a nahrání projektu

1. V Arduino IDE zvol **File -> Open...** (Soubor -> Otevřít).
2. Vyber soubor:
   ```text
   C:\PeciTech\PeciTech\Finware\PeciDeck_Firmware\PeciDeck_Firmware.ino
   ```
3. Zkontroluj, že je deska připojena k PC kabelem USB (datovým, ne pouze nabíjecím).
4. Klikni na kulaté tlačítko **Upload** (šipka doprava ➔).

> **💡 Co dělat, pokud nahrávání hlásí chybu připojení (A fatal error occurred: Failed to connect to ESP32-S3):**
> 1. Drž stisknuté tlačítko **BOOT** (na desce ESP32).
> 2. Krátce stiskni a pusť tlačítko **RESET / EN**.
> 3. Pusť tlačítko **BOOT** (ESP32-S3 se tím přepne do bootloader módu).
> 4. Znovu klikni na **Upload** v Arduino IDE.

---

## 5. Jak ověřit, že vše funguje

1. Po nahrání se na displeji objeví uvítací logo **Peci Deck MK.1** a následně mřížka 8 buněk.
2. Otevři v Arduino IDE **Serial Monitor** (ikona lupy vpravo nahoře).
3. Nastav rychlost na **115200 baud**.
4. Zmáčkni libovolné tlačítko SW1–SW8:
   - Na displeji PeciDecku se dané tlačítko okamžitě rozsvítí (zářivé oranžové vyplnění, dvojitý bílý rámeček a černá ikona) pro jasné potvrzení stisku!
   - V monitoru uvidíš výpis např. `B,0,1` (stisknuto) a `B,0,0` (uvolněno).
5. Pootoč enkodérem:
   - V monitoru uvidíš výpis např. `E,0,1` (otočení doprava) nebo `E,0,-1` (otočení doleva).
6. Zmáčkni osu enkodéru:
   - V monitoru uvidíš výpis např. `EB,0,1`.

---

## 📌 Rekapitulace zapojení dle KiCad schématu

### Tlačítka (Cherry MX)
- **SW1** -> GPIO 1
- **SW2** -> GPIO 2
- **SW3** -> GPIO 41
- **SW4** -> GPIO 4
- **SW5** -> GPIO 5
- **SW6** -> GPIO 6
- **SW7** -> GPIO 7
- **SW8** -> GPIO 8
*(Všechna spínají proti GND)*

### Rotační enkodéry
- **Enkodér 1 (SW9):** A = GPIO 9, B = GPIO 10, Tlačítko = GPIO 11
- **Enkodér 2 (SW10):** A = GPIO 12, B = GPIO 13, Tlačítko = GPIO 14
- **Enkodér 3 (SW11):** A = GPIO 17, B = GPIO 18, Tlačítko = GPIO 21

### Displej (ST7789 – konektor J1)
- **SCL (Hodiny):** GPIO 16
- **SDA (Data/MOSI):** GPIO 15
- **RST (Reset):** GPIO 37 *(Pin 34 ESP32 na DPS)*
- **DC (Data/Command):** GPIO 38 *(Pin 35 ESP32 na DPS)*
- **CS (Chip Select):** GPIO 47
- **BL (Podsvícení):** GPIO 48 (stmívání PWM)
