#include "display_ui.h"
#include "icons.h"
#include "driver/gpio.h"
#include <Preferences.h>

static Preferences prefs;
static bool prefs_initialized = false;

static void ensure_prefs() {
  if (!prefs_initialized) {
    prefs.begin("pecideck", false);
    prefs_initialized = true;
  }
}

// Odvozená třída pro přímý přístup k posunům okna (offsets) na ST7789 pro rozlišení 76x284
class PeciDeck_ST7789 : public Adafruit_ST7789 {
public:
  using Adafruit_ST7789::Adafruit_ST7789;

  void applyOffsets(uint8_t xs, uint8_t ys) {
    _colstart  = xs;
    _rowstart  = ys;
    _colstart2 = ys;
    _rowstart2 = xs;
    _xstart    = xs;
    _ystart    = ys;
  }
};

static PeciDeck_ST7789* pTft = nullptr;
static SPIClass* pDedicatedSpi = nullptr;
#define tft (*pTft)

#define GRID_MARGIN_X  2
#define GRID_MARGIN_Y  2
#define GRID_GAP_X     2
#define GRID_GAP_Y     2
#define BORDER_W       1

#define CELL_W  ((DISP_WIDTH - 2*GRID_MARGIN_X - (GRID_COLS-1)*GRID_GAP_X) / GRID_COLS)
#define CELL_H  ((DISP_HEIGHT - 2*GRID_MARGIN_Y - (GRID_ROWS-1)*GRID_GAP_Y) / GRID_ROWS)

static char cell_labels[GRID_CELLS][16];
static char cell_icons[GRID_CELLS][16];
static bool is_connected_to_app = false;
static bool current_inversion = false;

// Stav pro animaci stisku buněk
static bool cell_pressed_anim[GRID_CELLS] = {false};
static bool cell_physical_down[GRID_CELLS] = {false};
static unsigned long cell_press_time[GRID_CELLS] = {0};

static inline int16_t get_cell_x(uint8_t idx) {
  return GRID_MARGIN_X + (idx % GRID_COLS) * (CELL_W + GRID_GAP_X);
}

static inline int16_t get_cell_y(uint8_t idx) {
  return GRID_MARGIN_Y + (idx / GRID_COLS) * (CELL_H + GRID_GAP_Y);
}

void display_set_brightness(uint8_t brightness) {
  pinMode(DISP_PIN_BL, OUTPUT);
  if (brightness == 0) {
    digitalWrite(DISP_PIN_BL, HIGH); // Zhasnuto
  } else if (brightness >= 255) {
    digitalWrite(DISP_PIN_BL, LOW);  // Plný svit (aktivní v LOW)
  } else {
    analogWrite(DISP_PIN_BL, 255 - brightness);
  }
}

void display_set_inversion(bool invert) {
  current_inversion = invert;
  if (pTft) tft.invertDisplay(invert);
}

bool display_is_connected() {
  return is_connected_to_app;
}

void display_set_connected(bool connected) {
  if (is_connected_to_app == connected) return;
  is_connected_to_app = connected;
  if (connected) {
    display_draw_grid();
  } else {
    display_draw_offline_screen();
  }
}

void display_fill_color(uint16_t color, const char* name) {
  if (!pTft) return;
  Serial.print("[DISP] Vyplnuji displej barvou: ");
  Serial.println(name);
  Serial0.print("[DISP] Vyplnuji displej barvou: ");
  Serial0.println(name);
  tft.fillScreen(color);
}

struct DisplayProfile {
  uint8_t id;
  bool use_hw_spi;     // false = Software SPI bitbang, true = Hardware SPI (FSPI)
  uint8_t scl;
  uint8_t sda;
  uint8_t rst;
  uint8_t dc;
  uint8_t cs;
  uint8_t mode;        // SPI Mode 0 nebo 3
  uint8_t col_offset;
  uint8_t row_offset;
  bool invert;
  uint16_t test_color;
  const char* color_name_cz;
  const char* desc;
};

static const DisplayProfile PROFILES[] = {
  { 1, false, 16, 15, 37, 38, 47, SPI_MODE0, 18, 82, false, 0xF800, "CERVENA",       "Software SPI (Bitbang), RST=37, DC=38, offset 18/82 [DOPORUCENO]" },
  { 2, false, 16, 15, 37, 38, 47, SPI_MODE0, 18, 82, true,  0x07E0, "ZELENA",        "Software SPI (Bitbang), invertovany, RST=37, DC=38" },
  { 3, true,  16, 15, 37, 38, 47, SPI_MODE0, 18, 82, false, 0x001F, "MODRA",         "Hardware SPI (FSPI 4MHz), RST=37, DC=38, offset 18/82" },
  { 4, true,  16, 15, 37, 38, 47, SPI_MODE0, 18, 82, true,  0xFFE0, "ZLUTA",         "Hardware SPI (FSPI 4MHz), invertovany, RST=37, DC=38" },
  { 5, false, 16, 15, 37, 38, 47, SPI_MODE0, 82, 18, false, 0x07FF, "TYRKYSOVA",     "Software SPI, otocene offsety 82/18, RST=37, DC=38" },
  { 6, false, 16, 15, 37, 38, 47, SPI_MODE0, 0,  0,  false, 0xF81F, "FIALOVA",       "Software SPI, nulovy offset 0/0, RST=37, DC=38" },
  { 7, false, 16, 15, 38, 37, 47, SPI_MODE0, 18, 82, false, 0xFDA0, "ORANZOVA",      "Software SPI, prohozene RST a DC (RST=38, DC=37)" },
  { 8, false, 16, 15, 39, 40, 47, SPI_MODE0, 18, 82, false, 0xFFFF, "BILA",          "Software SPI, puvodni piny schematu (RST=39, DC=40)" }
};
static const uint8_t PROFILE_COUNT = sizeof(PROFILES) / sizeof(PROFILES[0]);
static uint8_t active_profile_id = 1;

uint8_t display_get_active_profile() {
  return active_profile_id;
}

uint8_t display_get_profile_count() {
  return PROFILE_COUNT;
}

void display_print_profiles() {
  Serial.println("\n================ DOSTUPNE PROFILY DISPLEJE ================");
  Serial0.println("\n================ DOSTUPNE PROFILY DISPLEJE ================");
  for (uint8_t i = 0; i < PROFILE_COUNT; i++) {
    const DisplayProfile& p = PROFILES[i];
    String s = " [" + String(p.id) + "] " + String(p.color_name_cz) + 
               " | Typ=" + (p.use_hw_spi ? "HW-SPI" : "SW-SPI") +
               " SCL=" + String(p.scl) + " SDA=" + String(p.sda) + 
               " RST=" + String(p.rst) + " DC=" + String(p.dc) + 
               " CS=" + String(p.cs) + 
               " (" + String(p.desc) + ")";
    if (p.id == active_profile_id) s += "  <-- AKTIVNI";
    Serial.println(s);
    Serial0.println(s);
  }
  Serial.println("Prikazy: 'SET <1-8>', 'DTEST' (spustit test), 'PINTEST' (multimetr test)");
  Serial0.println("Prikazy: 'SET <1-8>', 'DTEST' (spustit test), 'PINTEST' (multimetr test)");
  Serial.println("===========================================================\n");
  Serial0.println("===========================================================\n");
}

void display_apply_profile(uint8_t id) {
  if (id < 1 || id > PROFILE_COUNT) return;
  active_profile_id = id;
  const DisplayProfile& p = PROFILES[id - 1];

  String banner = "[DISP] Aplikuji profil " + String(p.id) + ": " + 
                  (p.use_hw_spi ? "HW-SPI" : "SW-SPI") +
                  ", SCL=" + String(p.scl) + ", SDA=" + String(p.sda) + 
                  ", RST=" + String(p.rst) + ", DC=" + String(p.dc) + 
                  ", CS=" + String(p.cs) + " (" + String(p.desc) + ")";
  Serial.println(banner);
  Serial0.println(banner);

  if (pTft != nullptr) {
    delete pTft;
    pTft = nullptr;
  }
  if (pDedicatedSpi != nullptr) {
    delete pDedicatedSpi;
    pDedicatedSpi = nullptr;
  }

  // Uvolnění pinů z JTAG i předchozích periferií
  gpio_reset_pin((gpio_num_t)p.rst);
  gpio_reset_pin((gpio_num_t)p.dc);
  gpio_reset_pin((gpio_num_t)p.cs);
  gpio_reset_pin((gpio_num_t)p.scl);
  gpio_reset_pin((gpio_num_t)p.sda);

  pinMode(p.rst, OUTPUT);
  pinMode(p.dc, OUTPUT);
  pinMode(p.cs, OUTPUT);
  digitalWrite(p.cs, HIGH);
  digitalWrite(p.dc, HIGH);

  // Poctivý hardwarový reset ST7789
  digitalWrite(p.rst, HIGH); delay(20);
  digitalWrite(p.rst, LOW);  delay(60);
  digitalWrite(p.rst, HIGH); delay(150);

  if (p.use_hw_spi) {
    pDedicatedSpi = new SPIClass(FSPI);
    pDedicatedSpi->begin(p.scl, -1, p.sda, -1);
    pTft = new PeciDeck_ST7789(pDedicatedSpi, p.cs, p.dc, p.rst);
    pTft->init(DISP_HW_W, DISP_HW_H, p.mode);
    pTft->setSPISpeed(4000000);
  } else {
    // Software SPI (Bitbang) - přímo řídí piny bez rizika přepisování SPI periferií
    pTft = new PeciDeck_ST7789(p.cs, p.dc, p.sda, p.scl, p.rst);
    pTft->init(DISP_HW_W, DISP_HW_H);
  }

  pTft->setRotation(1);
  pTft->applyOffsets(p.col_offset, p.row_offset);
  pTft->invertDisplay(p.invert);
  current_inversion = p.invert;

  display_set_brightness(255);



  if (is_connected_to_app) {
    display_draw_grid();
  } else {
    display_draw_offline_screen();
  }
}

void display_run_interactive_test() {
  Serial.println("\n========================================================");
  Serial.println("         DIAGNOSTIKA DISPLEJE (8 PROFILU)               ");
  Serial.println("========================================================");
  Serial0.println("\n========================================================");
  Serial0.println("         DIAGNOSTIKA DISPLEJE (8 PROFILU)               ");
  Serial0.println("========================================================");

  // Test podsvícení (bliknutí 3x)
  pinMode(DISP_PIN_BL, OUTPUT);
  for (int b = 0; b < 3; b++) {
    digitalWrite(DISP_PIN_BL, HIGH); delay(150); // Zhasnout
    digitalWrite(DISP_PIN_BL, LOW);  delay(150); // Rozsvítit
  }

  for (uint8_t i = 0; i < PROFILE_COUNT; i++) {
    const DisplayProfile& p = PROFILES[i];
    String banner = "[DTEST " + String(i + 1) + "/" + String(PROFILE_COUNT) + "] " +
                    "Profil " + String(p.id) + " (" + (p.use_hw_spi ? "HW-SPI" : "SW-SPI") + 
                    "): SCL=" + String(p.scl) + ", SDA=" + String(p.sda) + 
                    ", RST=" + String(p.rst) + ", DC=" + String(p.dc) + ", CS=" + String(p.cs) + 
                    " -> BARVA: " + String(p.color_name_cz) + " (" + String(p.desc) + ")";
    Serial.println(banner);
    Serial0.println(banner);

    // Aplikace profilu a vykreslení testovací barvy
    if (pTft != nullptr) { delete pTft; pTft = nullptr; }
    if (pDedicatedSpi != nullptr) { delete pDedicatedSpi; pDedicatedSpi = nullptr; }

    gpio_reset_pin((gpio_num_t)p.rst);
    gpio_reset_pin((gpio_num_t)p.dc);
    gpio_reset_pin((gpio_num_t)p.cs);
    gpio_reset_pin((gpio_num_t)p.scl);
    gpio_reset_pin((gpio_num_t)p.sda);

    pinMode(p.rst, OUTPUT);
    pinMode(p.dc, OUTPUT);
    pinMode(p.cs, OUTPUT);
    digitalWrite(p.cs, HIGH);
    digitalWrite(p.dc, HIGH);

    digitalWrite(p.rst, HIGH); delay(20);
    digitalWrite(p.rst, LOW);  delay(60);
    digitalWrite(p.rst, HIGH); delay(150);

    if (p.use_hw_spi) {
      pDedicatedSpi = new SPIClass(FSPI);
      pDedicatedSpi->begin(p.scl, -1, p.sda, -1);
      pTft = new PeciDeck_ST7789(pDedicatedSpi, p.cs, p.dc, p.rst);
      pTft->init(DISP_HW_W, DISP_HW_H, p.mode);
      pTft->setSPISpeed(4000000);
    } else {
      pTft = new PeciDeck_ST7789(p.cs, p.dc, p.sda, p.scl, p.rst);
      pTft->init(DISP_HW_W, DISP_HW_H);
    }

    pTft->setRotation(1);
    pTft->applyOffsets(p.col_offset, p.row_offset);
    pTft->invertDisplay(p.invert);

    pTft->fillScreen(p.test_color);
    delay(1200);
  }

  Serial.println("\n========================================================");
  Serial.println("   DTEST DOKONCEN!");
  Serial.println("   Viděl jsi na displeji nějakou barvu? Kterou?");
  Serial.println("   Zadej např. 'SET 1' nebo 'SET 2' pro zvolení.");
  Serial.println("========================================================\n");

  Serial0.println("\n========================================================");
  Serial0.println("   DTEST DOKONCEN!");
  Serial0.println("   Napis 'SET <cislo>' pro zvoleni profilu.");
  Serial0.println("========================================================\n");

  display_apply_profile(active_profile_id);
}

void display_run_pin_test() {
  Serial.println("\n========================================================");
  Serial.println("       MULTIMETR HARDWARE TEST PINU KONEKTORU J1        ");
  Serial.println("========================================================");
  Serial.println("Mer mericim hrotem multimetru (proti GND - J1 pin 1):");
  Serial.println("Ocekavana hodnota se bude stridat: 3.3V po dobu 3s, pak 0.0V po dobu 3s.");
  Serial.println("========================================================");

  Serial0.println("\n========================================================");
  Serial0.println("       MULTIMETR HARDWARE TEST PINU KONEKTORU J1        ");
  Serial0.println("========================================================");

  if (pTft) { delete pTft; pTft = nullptr; }
  if (pDedicatedSpi) { delete pDedicatedSpi; pDedicatedSpi = nullptr; }

  struct PinInfo {
    uint8_t gpio;
    const char* name;
    uint8_t j1_pin;
  };
  const PinInfo pins_to_test[] = {
    { DISP_PIN_RST, "RST", 5 },
    { DISP_PIN_DC,  "DC",  6 },
    { DISP_PIN_CS,  "CS",  7 },
    { DISP_PIN_SCL, "SCL", 3 },
    { DISP_PIN_SDA, "SDA", 4 },
    { DISP_PIN_BL,  "BL",  8 }
  };

  for (size_t i = 0; i < 6; i++) {
    const PinInfo& pi = pins_to_test[i];
    gpio_reset_pin((gpio_num_t)pi.gpio);
    pinMode(pi.gpio, OUTPUT);

    String msg1 = "[" + String(i + 1) + "/6] TEST " + String(pi.name) + 
                  " (GPIO " + String(pi.gpio) + " -> J1 Pin " + String(pi.j1_pin) + "):";
    Serial.println(msg1);
    Serial0.println(msg1);

    Serial.println("  -> Nastavuji 3.3V (HIGH)... zmer J1 pin " + String(pi.j1_pin) + " (3 sekundy)");
    Serial0.println("  -> Nastavuji 3.3V (HIGH)... zmer J1 pin " + String(pi.j1_pin) + " (3 sekundy)");
    digitalWrite(pi.gpio, HIGH);
    delay(3000);

    Serial.println("  -> Nastavuji 0.0V (LOW)...  zmer J1 pin " + String(pi.j1_pin) + " (3 sekundy)");
    Serial0.println("  -> Nastavuji 0.0V (LOW)...  zmer J1 pin " + String(pi.j1_pin) + " (3 sekundy)");
    digitalWrite(pi.gpio, LOW);
    delay(3000);
  }

  Serial.println("\n[OK] Test pinu dokoncen. Vracim displej do provozu...");
  Serial0.println("\n[OK] Test pinu dokoncen. Vracim displej do provozu...");
  display_apply_profile(active_profile_id);
}

void display_run_scan_test() {
  Serial.println("\n========================================================");
  Serial.println("       AUTOMATICKY ELEKTRICKY SKEN PINU KONEKTORU J1    ");
  Serial.println("========================================================");
  Serial0.println("\n========================================================");
  Serial0.println("       AUTOMATICKY ELEKTRICKY SKEN PINU KONEKTORU J1    ");
  Serial0.println("========================================================");

  if (pTft) { delete pTft; pTft = nullptr; }
  if (pDedicatedSpi) { delete pDedicatedSpi; pDedicatedSpi = nullptr; }

  struct ScanPin {
    uint8_t gpio;
    const char* name;
    uint8_t j1_pin;
  };
  const ScanPin pins[] = {
    { DISP_PIN_SCL, "SCL", 3 },
    { DISP_PIN_SDA, "SDA", 4 },
    { DISP_PIN_RST, "RST", 5 },
    { DISP_PIN_DC,  "DC",  6 },
    { DISP_PIN_CS,  "CS",  7 },
    { DISP_PIN_BL,  "BL",  8 },
    { 41,           "GPIO41 (SW3)", 0 }
  };

  for (size_t i = 0; i < 7; i++) {
    const ScanPin& p = pins[i];
    gpio_reset_pin((gpio_num_t)p.gpio);

    // 1. Test s internim Pull-Down (odhali externi Pull-Up na desce displeje)
    pinMode(p.gpio, INPUT_PULLDOWN);
    delay(5);
    int pd_val = digitalRead(p.gpio);

    // 2. Test s internim Pull-Up (odhali zkrat na GND)
    pinMode(p.gpio, INPUT_PULLUP);
    delay(5);
    int pu_val = digitalRead(p.gpio);

    String status = (p.j1_pin > 0) ? 
      ("J1 Pin " + String(p.j1_pin) + " [" + String(p.name) + " | GPIO " + String(p.gpio) + "]: ") :
      ("[" + String(p.name) + "]: ");

    if (pu_val == 0) {
      status += "!!! VAROVANI: TRVALY ZKRAT NA GND !!!";
    } else if (pd_val == 1) {
      status += "OK (Detekovan zatezovy Pull-Up rezistor modulu displeje)";
    } else {
      status += "OK (Reaguje v poradku, cisty pin bez zkratu)";
    }

    Serial.println(status);
    Serial0.println(status);
  }

  Serial.println("========================================================\n");
  Serial0.println("========================================================\n");
  display_apply_profile(active_profile_id);
}

void display_set_all_pins(bool high_level) {
  if (pTft) { delete pTft; pTft = nullptr; }
  if (pDedicatedSpi) { delete pDedicatedSpi; pDedicatedSpi = nullptr; }

  const uint8_t pins[] = { DISP_PIN_RST, DISP_PIN_DC, DISP_PIN_CS, DISP_PIN_SCL, DISP_PIN_SDA, DISP_PIN_BL, 41 };
  for (uint8_t p : pins) {
    gpio_reset_pin((gpio_num_t)p);
    pinMode(p, OUTPUT);
    digitalWrite(p, high_level ? HIGH : LOW);
  }

  String msg = high_level ? 
    "\n========================================================\n"
    " [MULTIMETR REZIM: VSECHNY PINY NA 3.3V (HIGH)]\n"
    " Vsechny piny (J1.3 az J1.8 i GPIO 41) nyni TRVALE vysilaji 3.3V!\n"
    " Cerny hrot multimetru pripoj na GND (J1 Pin 1 nebo kovovy USB kryt).\n"
    " Cervenym hrotem v klidu zmer piny 2 az 8 na konektoru J1:\n"
    "   - Pin 1 (GND): musi mit 0.0V\n"
    "   - Pin 2 (VCC): musi mit ~3.3V (POZOR: pokud nema, displej neni napajen!)\n"
    "   - Pin 3 (SCL): musi mit ~3.3V\n"
    "   - Pin 4 (SDA): musi mit ~3.3V\n"
    "   - Pin 5 (RST): musi mit ~3.3V (GPIO 37)\n"
    "   - Pin 6 (DC):  musi mit ~3.3V (GPIO 38)\n"
    "   - Pin 7 (CS):  musi mit ~3.3V (GPIO 47)\n"
    "   - Pin 8 (BL):  musi mit ~3.3V (GPIO 48)\n"
    " Az zmeris, napis 'ALL 0' pro prepnuti na 0.0V, nebo 'RUN' pro obnoveni displeje.\n"
    "========================================================\n"
    :
    "\n========================================================\n"
    " [MULTIMETR REZIM: VSECHNY PINY NA 0.0V (LOW)]\n"
    " Vsechny piny (J1.3 az J1.8 i GPIO 41) nyni TRVALE vysilaji 0.0V!\n"
    " Piny 3 az 8 by na multimetru mely mit 0.0V.\n"
    " Napis 'ALL 1' pro zpet na 3.3V, nebo 'RUN' pro obnoveni displeje.\n"
    "========================================================\n";

  Serial.println(msg);
  Serial0.println(msg);
}

void display_run_probe_test() {
  Serial.println("\n========================================================");
  Serial.println("  INTERAKTIVNI TEST VODIVOSTI SPOJU J1 (DRATKOVY TEST)  ");
  Serial.println("========================================================");
  Serial.println("JAK OTESTOVAT SPOJE S ESP32 BEZ MERAKU:");
  Serial.println("1. Vezmi kousek dratku, pinzetu nebo kancelarskou sponku.");
  Serial.println("2. Jeden konec pripoj na GND (J1 Pin 1 nebo USB plech).");
  Serial.println("3. Druhym koncem se postupne dotkni pinu na konektoru J1:");
  Serial.println("     - Pin 3: SCL (GPIO 16)");
  Serial.println("     - Pin 4: SDA (GPIO 15)");
  Serial.println("     - Pin 5: RST (GPIO 37)");
  Serial.println("     - Pin 6: DC  (GPIO 38)");
  Serial.println("     - Pin 7: CS  (GPIO 47)");
  Serial.println("     - Pin 8: BL  (GPIO 48)");
  Serial.println("4. Jakmile se dotknes, tady se IHNED zobrazi POTVRZENI!");
  Serial.println("   (Test bezi 45 sekund, predcasne ukoncis odeslanim 'x')");
  Serial.println("========================================================\n");

  Serial0.println("\n========================================================");
  Serial0.println("  INTERAKTIVNI TEST VODIVOSTI SPOJU J1 (DRATKOVY TEST)  ");
  Serial0.println("========================================================");

  if (pTft) { delete pTft; pTft = nullptr; }
  if (pDedicatedSpi) { delete pDedicatedSpi; pDedicatedSpi = nullptr; }

  struct ProbePin {
    uint8_t gpio;
    const char* name;
    uint8_t j1_pin;
    bool detected;
  };
  ProbePin pins[6] = {
    { DISP_PIN_SCL, "SCL", 3, false },
    { DISP_PIN_SDA, "SDA", 4, false },
    { DISP_PIN_RST, "RST", 5, false },
    { DISP_PIN_DC,  "DC",  6, false },
    { DISP_PIN_CS,  "CS",  7, false },
    { DISP_PIN_BL,  "BL",  8, false }
  };

  for (size_t i = 0; i < 6; i++) {
    gpio_reset_pin((gpio_num_t)pins[i].gpio);
    pinMode(pins[i].gpio, INPUT_PULLUP);
  }

  uint8_t detected_count = 0;
  unsigned long start_time = millis();

  while (millis() - start_time < 45000) {
    for (size_t i = 0; i < 6; i++) {
      if (!pins[i].detected && digitalRead(pins[i].gpio) == LOW) {
        delay(15); // debounce
        if (digitalRead(pins[i].gpio) == LOW) {
          pins[i].detected = true;
          detected_count++;

          String banner = "\n>>> [SPOJ 100% FUNGUJE!] Pin J1." + String(pins[i].j1_pin) + 
                          " (" + String(pins[i].name) + " | GPIO " + String(pins[i].gpio) + 
                          ") uspesne sepnul na GND!\n" +
                          "    Stav testu: " + String(detected_count) + "/6 pinu overeno.";
          Serial.println(banner);
          Serial0.println(banner);

          if (detected_count >= 6) {
            String win = "\n========================================================\n"
                         "  VSECHNY PINY DISPLEJE (3 az 8) JSOU 100% VODIVE!\n"
                         "  Plošný spoj od ESP32 ke konektoru J1 je bez chyby!\n"
                         "========================================================\n";
            Serial.println(win);
            Serial0.println(win);
            delay(1000);
            display_apply_profile(active_profile_id);
            return;
          }
        }
      }
    }

    if (Serial.available() > 0 || Serial0.available() > 0) {
      char c = (Serial.available() > 0) ? Serial.read() : Serial0.read();
      if (c == 'x' || c == 'X' || c == 'q' || c == 'Q') {
        break;
      }
    }
    delay(10);
  }

  Serial.println("\n[INFO] Test pinu ukoncen. Obnovuji displej...");
  Serial0.println("\n[INFO] Test pinu ukoncen. Obnovuji displej...");
  display_apply_profile(active_profile_id);
}

void display_setup() {
  Serial.println("[DISP] Inicializuji displej Peci Deck...");
  Serial0.println("[DISP] Inicializuji displej Peci Deck...");

  ensure_prefs();
  for (uint8_t i = 0; i < GRID_CELLS; i++) {
    String l = prefs.getString(("l" + String(i)).c_str(), "");
    String ic = prefs.getString(("i" + String(i)).c_str(), "");
    strncpy(cell_labels[i], l.c_str(), sizeof(cell_labels[i]) - 1);
    cell_labels[i][sizeof(cell_labels[i]) - 1] = '\0';
    strncpy(cell_icons[i], ic.c_str(), sizeof(cell_icons[i]) - 1);
    cell_icons[i][sizeof(cell_icons[i]) - 1] = '\0';
  }

  display_apply_profile(1);
}

static void draw_vector_icon(int16_t cx, int16_t cy, const char* name, uint16_t color) {
  if (draw_custom_icon(tft, cx, cy, name)) {
    return;
  }

  if (strcmp(name, "play") == 0) {
    tft.fillTriangle(cx - 5, cy - 7, cx - 5, cy + 7, cx + 7, cy, COL_GREEN);
  } 
  else if (strcmp(name, "pause") == 0) {
    tft.fillRect(cx - 5, cy - 7, 3, 14, COL_YELLOW);
    tft.fillRect(cx + 2, cy - 7, 3, 14, COL_YELLOW);
  } 
  else if (strcmp(name, "next") == 0) {
    tft.fillTriangle(cx - 6, cy - 6, cx - 6, cy + 6, cx + 1, cy, COL_CYAN);
    tft.fillRect(cx + 3, cy - 6, 2, 12, COL_CYAN);
  } 
  else if (strcmp(name, "prev") == 0) {
    tft.fillRect(cx - 5, cy - 6, 2, 12, COL_CYAN);
    tft.fillTriangle(cx + 6, cy - 6, cx + 6, cy + 6, cx - 1, cy, COL_CYAN);
  }
  else if (strcmp(name, "stop") == 0) {
    tft.fillRect(cx - 5, cy - 5, 11, 11, COL_RED);
  }
  else if (strcmp(name, "mute") == 0 || strcmp(name, "mic_mute") == 0) {
    // Reproduktor s výrazným červeným přeškrtnutím
    tft.fillRect(cx - 6, cy - 3, 3, 6, COL_WHITE);
    tft.fillTriangle(cx - 3, cy - 3, cx + 1, cy - 6, cx + 1, cy + 6, COL_WHITE);
    tft.drawLine(cx + 3, cy - 4, cx + 7, cy + 4, COL_RED);
    tft.drawLine(cx + 4, cy - 4, cx + 8, cy + 4, COL_RED);
    tft.drawLine(cx + 7, cy - 4, cx + 3, cy + 4, COL_RED);
    tft.drawLine(cx + 8, cy - 4, cx + 4, cy + 4, COL_RED);
  } 
  else if (strcmp(name, "vol_up") == 0) {
    tft.fillRect(cx - 6, cy - 3, 3, 6, COL_WHITE);
    tft.fillTriangle(cx - 3, cy - 3, cx + 1, cy - 6, cx + 1, cy + 6, COL_WHITE);
    tft.drawCircle(cx + 2, cy, 4, COL_GREEN);
    tft.drawCircle(cx + 3, cy, 7, COL_GREEN);
    tft.fillRect(cx - 5, cy - 8, 8, 16, COL_BLACK); // maskování levé poloviny vln
    tft.fillRect(cx - 6, cy - 3, 3, 6, COL_WHITE);
    tft.fillTriangle(cx - 3, cy - 3, cx + 1, cy - 6, cx + 1, cy + 6, COL_WHITE);
  }
  else if (strcmp(name, "vol_down") == 0) {
    tft.fillRect(cx - 6, cy - 3, 3, 6, COL_WHITE);
    tft.fillTriangle(cx - 3, cy - 3, cx + 1, cy - 6, cx + 1, cy + 6, COL_WHITE);
    tft.drawCircle(cx + 2, cy, 4, COL_YELLOW);
    tft.fillRect(cx - 5, cy - 6, 7, 12, COL_BLACK);
    tft.fillRect(cx - 6, cy - 3, 3, 6, COL_WHITE);
    tft.fillTriangle(cx - 3, cy - 3, cx + 1, cy - 6, cx + 1, cy + 6, COL_WHITE);
  }
  else if (strcmp(name, "mic") == 0) {
    // Plně vyplněný tyrkysový mikrofon se stojanem
    tft.fillRoundRect(cx - 3, cy - 6, 6, 8, 3, COL_CYAN);
    tft.drawCircle(cx, cy - 1, 5, COL_WHITE);
    tft.fillRect(cx - 6, cy - 7, 12, 6, COL_BLACK);
    tft.drawFastVLine(cx, cy + 4, 3, COL_WHITE);
    tft.drawFastHLine(cx - 4, cy + 7, 9, COL_WHITE);
  }
  else if (strcmp(name, "obs") == 0) {
    // Klasické logo OBS Studio s 3 lopatkami
    tft.fillCircle(cx, cy, 7, COL_WHITE);
    tft.fillCircle(cx, cy, 4, COL_BLACK);
    tft.fillCircle(cx, cy - 2, 2, COL_WHITE);
    tft.fillCircle(cx - 2, cy + 2, 2, COL_WHITE);
    tft.fillCircle(cx + 2, cy + 2, 2, COL_WHITE);
  } 
  else if (strcmp(name, "rec") == 0) {
    // Pulzní zářivý záznam
    tft.drawCircle(cx, cy, 8, COL_RED);
    tft.fillCircle(cx, cy, 5, COL_RED);
  }
  else if (strcmp(name, "twitch") == 0) {
    // Oficiální fialová Twitch bublina s bílýma očima
    tft.fillRoundRect(cx - 7, cy - 6, 14, 11, 2, COL_PURPLE);
    tft.fillTriangle(cx - 5, cy + 4, cx - 2, cy + 4, cx - 5, cy + 7, COL_PURPLE);
    tft.fillRect(cx - 3, cy - 3, 2, 4, COL_WHITE);
    tft.fillRect(cx + 2, cy - 3, 2, 4, COL_WHITE);
  }
  else if (strcmp(name, "discord") == 0) {
    // Originální Discord blurple gamepad hlava
    tft.fillRoundRect(cx - 8, cy - 5, 16, 11, 3, COL_BLURPLE);
    tft.fillCircle(cx - 3, cy, 2, COL_WHITE);
    tft.fillCircle(cx + 3, cy, 2, COL_WHITE);
  }
  else if (strcmp(name, "marker") == 0) {
    // Fialová Twitch záložka se zlatým proužkem
    tft.fillRect(cx - 5, cy - 7, 10, 13, COL_PURPLE);
    tft.fillTriangle(cx - 5, cy + 6, cx + 4, cy + 6, cx, cy + 2, COL_BLACK);
    tft.drawFastHLine(cx - 3, cy - 3, 6, COL_YELLOW);
  }
  else if (strcmp(name, "clip") == 0) {
    // Režisérská klapka pro tvorbu klipů
    tft.fillRoundRect(cx - 7, cy - 2, 14, 9, 1, COL_DARK_GRAY);
    tft.drawRect(cx - 7, cy - 2, 14, 9, COL_WHITE);
    tft.fillRect(cx - 7, cy - 7, 14, 4, COL_WHITE);
    tft.drawLine(cx - 5, cy - 7, cx - 3, cy - 4, COL_BLACK);
    tft.drawLine(cx - 1, cy - 7, cx + 1, cy - 4, COL_BLACK);
    tft.drawLine(cx + 3, cy - 7, cx + 5, cy - 4, COL_BLACK);
  }
  else if (strcmp(name, "web") == 0) {
    tft.drawCircle(cx, cy, 7, COL_CYAN);
    tft.drawFastHLine(cx - 7, cy, 14, COL_CYAN);
    tft.drawFastVLine(cx, cy - 7, 14, COL_CYAN);
  } 
  else if (strcmp(name, "headset") == 0) {
    tft.drawCircle(cx, cy - 2, 7, COL_CYAN);
    tft.fillRect(cx - 7, cy, 15, 6, COL_BLACK);
    tft.fillRoundRect(cx - 8, cy - 1, 4, 7, 2, COL_WHITE);
    tft.fillRoundRect(cx + 4, cy - 1, 4, 7, 2, COL_WHITE);
  }
  else if (strcmp(name, "lock") == 0) {
    tft.drawRoundRect(cx - 4, cy - 7, 8, 8, 3, COL_WHITE);
    tft.fillRoundRect(cx - 6, cy - 2, 12, 9, 2, COL_YELLOW);
    tft.fillCircle(cx, cy + 1, 1, COL_BLACK);
    tft.drawFastVLine(cx, cy + 2, 2, COL_BLACK);
  }
  else if (strcmp(name, "folder") == 0) {
    tft.fillRoundRect(cx - 7, cy - 5, 14, 11, 2, COL_YELLOW);
    tft.fillRect(cx - 7, cy - 7, 6, 3, COL_YELLOW);
    tft.drawFastHLine(cx - 6, cy - 3, 12, COL_WHITE);
  }
  else if (strcmp(name, "copy") == 0 || strcmp(name, "paste") == 0) {
    tft.drawRoundRect(cx - 6, cy - 4, 9, 11, 2, COL_WHITE);
    tft.fillRoundRect(cx - 2, cy - 7, 9, 11, 2, COL_ORANGE);
  }
  else if (strcmp(name, "calc") == 0) {
    tft.fillRoundRect(cx - 6, cy - 7, 12, 14, 2, COL_DARK_GRAY);
    tft.drawRoundRect(cx - 6, cy - 7, 12, 14, 2, COL_WHITE);
    tft.fillRect(cx - 4, cy - 5, 8, 3, COL_CYAN);
    tft.drawPixel(cx - 2, cy, COL_WHITE);
    tft.drawPixel(cx + 2, cy, COL_WHITE);
    tft.drawPixel(cx - 2, cy + 3, COL_WHITE);
    tft.drawPixel(cx + 2, cy + 3, COL_ORANGE);
  }
  else if (strcmp(name, "screenshot") == 0) {
    tft.fillRoundRect(cx - 7, cy - 3, 14, 10, 2, COL_GRAY);
    tft.fillRect(cx - 4, cy - 5, 4, 3, COL_WHITE);
    tft.fillCircle(cx, cy + 2, 3, COL_CYAN);
    tft.drawCircle(cx, cy + 2, 4, COL_WHITE);
  }
  else if (strcmp(name, "trash") == 0) {
    tft.fillRect(cx - 4, cy - 3, 9, 10, COL_RED);
    tft.drawFastHLine(cx - 6, cy - 4, 13, COL_WHITE);
    tft.drawFastHLine(cx - 3, cy - 6, 7, COL_WHITE);
  }
  else if (strcmp(name, "hotkey") == 0) {
    tft.fillRoundRect(cx - 7, cy - 7, 14, 14, 2, COL_DARK_GRAY);
    tft.drawRoundRect(cx - 7, cy - 7, 14, 14, 2, COL_ORANGE);
    tft.drawFastHLine(cx - 3, cy, 6, COL_WHITE);
  }
  else if (strcmp(name, "scene") == 0) {
    tft.drawRect(cx - 7, cy - 5, 14, 10, COL_ORANGE);
    tft.fillCircle(cx, cy, 2, COL_WHITE);
  }
  else if (strcmp(name, "steam") == 0) {
    tft.fillCircle(cx - 2, cy + 2, 5, COL_CYAN);
    tft.drawCircle(cx + 3, cy - 3, 3, COL_WHITE);
    tft.drawLine(cx - 2, cy + 2, cx + 3, cy - 3, COL_WHITE);
  }
  else if (strcmp(name, "youtube") == 0) {
    tft.fillRoundRect(cx - 8, cy - 5, 16, 11, 3, COL_RED);
    tft.fillTriangle(cx - 2, cy - 3, cx - 2, cy + 3, cx + 3, cy, COL_WHITE);
  }
  else if (strcmp(name, "spotify") == 0) {
    tft.fillCircle(cx, cy, 7, COL_GREEN);
    tft.drawCircle(cx, cy + 5, 6, COL_BLACK);
    tft.drawCircle(cx, cy + 7, 8, COL_BLACK);
  }
  else if (strcmp(name, "app") == 0) {
    tft.fillRoundRect(cx - 7, cy - 7, 14, 14, 2, COL_DARK_GRAY);
    tft.fillRect(cx - 7, cy - 7, 14, 4, COL_CYAN);
    tft.drawPixel(cx, cy + 2, COL_WHITE);
  }
  else {
    // Elegantní minimalistický kosočtverec / orámování místo ošklivého prázdného čtverečku
    tft.drawRoundRect(cx - 5, cy - 5, 11, 11, 2, color);
    tft.drawPixel(cx, cy, color);
  }
}

static void render_cell(uint8_t idx) {
  if (idx >= GRID_CELLS) return;

  int16_t x = get_cell_x(idx);
  int16_t y = get_cell_y(idx);
  int16_t cx = x + CELL_W / 2;
  int16_t cy = y + CELL_H / 2;

  tft.fillRect(x, y, CELL_W, CELL_H, COL_BLACK);

  for (uint8_t b = 0; b < BORDER_W; b++) {
    tft.drawRoundRect(x + b, y + b, CELL_W - 2*b, CELL_H - 2*b, 3, COL_ORANGE);
  }

  const char* icon = cell_icons[idx];
  const char* label = cell_labels[idx];

  if (icon[0] != '\0') {
    if (label[0] != '\0') {
      draw_vector_icon(cx, y + 12, icon, COL_ORANGE);
      tft.setTextColor(COL_WHITE);
      tft.setTextSize(1);
      int16_t tx, ty; uint16_t tw, th;
      tft.getTextBounds(label, 0, 0, &tx, &ty, &tw, &th);
      tft.setCursor(cx - tw / 2 - tx, y + CELL_H - 9);
      tft.print(label);
    } else {
      draw_vector_icon(cx, cy, icon, COL_ORANGE);
    }
    return;
  }

  if (label[0] != '\0') {
    tft.setTextColor(COL_WHITE);
    tft.setTextSize(1);
    int16_t tx, ty; uint16_t tw, th;
    tft.getTextBounds(label, 0, 0, &tx, &ty, &tw, &th);
    tft.setCursor(cx - tw / 2 - tx, cy - th / 2 - ty);
    tft.print(label);
    return;
  }

  char num_buf[4];
  snprintf(num_buf, sizeof(num_buf), "%d", idx + 1);
  tft.setTextColor(COL_GRAY);
  tft.setTextSize(2);
  int16_t tx, ty; uint16_t tw, th;
  tft.getTextBounds(num_buf, 0, 0, &tx, &ty, &tw, &th);
  tft.setCursor(cx - tw / 2 - tx, cy - th / 2 - ty);
  tft.print(num_buf);
}

static void render_cell_pressed(uint8_t idx) {
  if (idx >= GRID_CELLS || !pTft) return;

  int16_t x = get_cell_x(idx);
  int16_t y = get_cell_y(idx);
  int16_t cx = x + CELL_W / 2;
  int16_t cy = y + CELL_H / 2;

  // 1. Zářivé oranžové vyplnění celého tlačítka
  tft.fillRoundRect(x, y, CELL_W, CELL_H, 3, COL_ORANGE);
  // 2. Dvojitý zářivý bílý rámeček – okamžitá jasná vizuální zpětná vazba stisku
  tft.drawRoundRect(x, y, CELL_W, CELL_H, 3, COL_WHITE);
  tft.drawRoundRect(x + 1, y + 1, CELL_W - 2, CELL_H - 2, 2, COL_WHITE);

  const char* icon = cell_icons[idx];
  const char* label = cell_labels[idx];

  if (icon[0] != '\0') {
    if (label[0] != '\0') {
      draw_vector_icon(cx, y + 12, icon, COL_BLACK);
      tft.setTextColor(COL_BLACK);
      tft.setTextSize(1);
      int16_t tx, ty; uint16_t tw, th;
      tft.getTextBounds(label, 0, 0, &tx, &ty, &tw, &th);
      tft.setCursor(cx - tw / 2 - tx, y + CELL_H - 9);
      tft.print(label);
    } else {
      draw_vector_icon(cx, cy, icon, COL_BLACK);
    }
    return;
  }

  if (label[0] != '\0') {
    tft.setTextColor(COL_BLACK);
    tft.setTextSize(1);
    int16_t tx, ty; uint16_t tw, th;
    tft.getTextBounds(label, 0, 0, &tx, &ty, &tw, &th);
    tft.setCursor(cx - tw / 2 - tx, cy - th / 2 - ty);
    tft.print(label);
    return;
  }

  char num_buf[4];
  snprintf(num_buf, sizeof(num_buf), "%d", idx + 1);
  tft.setTextColor(COL_BLACK);
  tft.setTextSize(2);
  int16_t tx, ty; uint16_t tw, th;
  tft.getTextBounds(num_buf, 0, 0, &tx, &ty, &tw, &th);
  tft.setCursor(cx - tw / 2 - tx, cy - th / 2 - ty);
  tft.print(num_buf);
}

void display_draw_offline_screen() {
  if (!pTft) return;
  tft.fillScreen(COL_BLACK);

  // Rámečky okolo celého displeje
  tft.drawRoundRect(2, 2, DISP_WIDTH - 4, DISP_HEIGHT - 4, 4, COL_DARK_GRAY);
  tft.drawRoundRect(3, 3, DISP_WIDTH - 6, DISP_HEIGHT - 6, 3, COL_ORANGE);

  // Hlavní velký nápis
  tft.setTextColor(COL_ORANGE);
  tft.setTextSize(2);
  const char* title = "PeciDeck MK.1";
  int16_t x1, y1; uint16_t w, h;
  tft.getTextBounds(title, 0, 0, &x1, &y1, &w, &h);
  tft.setCursor((DISP_WIDTH - w) / 2, 16);
  tft.print(title);

  // Podtitul
  tft.setTextColor(COL_WHITE);
  tft.setTextSize(1);
  const char* sub = "PeciTech Studio";
  tft.getTextBounds(sub, 0, 0, &x1, &y1, &w, &h);
  tft.setCursor((DISP_WIDTH - w) / 2, 38);
  tft.print(sub);

  // Status
  tft.setTextColor(COL_GRAY);
  tft.setTextSize(1);
  const char* status = "[ STANDBY - Odpojeno ]";
  tft.getTextBounds(status, 0, 0, &x1, &y1, &w, &h);
  tft.setCursor((DISP_WIDTH - w) / 2, 54);
  tft.print(status);
}

void display_draw_grid() {
  if (!pTft) return;
  tft.fillScreen(COL_BLACK);
  for (uint8_t i = 0; i < GRID_CELLS; i++) {
    if (cell_pressed_anim[i]) {
      render_cell_pressed(i);
    } else {
      render_cell(i);
    }
  }
}

static void sanitize_ascii(char* dest, const char* src, size_t max_len) {
  size_t d = 0;
  for (size_t s = 0; src[s] != '\0' && d + 1 < max_len; ) {
    unsigned char c = (unsigned char)src[s];
    if (c < 0x80) {
      dest[d++] = c;
      s++;
    } else if (c == 0xC3 && src[s+1] != '\0') {
      unsigned char c2 = (unsigned char)src[s+1];
      s += 2;
      switch (c2) {
        case 0xA1: dest[d++] = 'a'; break; // á
        case 0x81: dest[d++] = 'A'; break; // Á
        case 0xA9: dest[d++] = 'e'; break; // é
        case 0x89: dest[d++] = 'E'; break; // É
        case 0xAD: dest[d++] = 'i'; break; // í
        case 0x8D: dest[d++] = 'I'; break; // Í
        case 0xB3: dest[d++] = 'o'; break; // ó
        case 0x93: dest[d++] = 'O'; break; // Ó
        case 0xBA: dest[d++] = 'u'; break; // ú
        case 0x9A: dest[d++] = 'U'; break; // Ú
        case 0xBD: dest[d++] = 'y'; break; // ý
        case 0x9D: dest[d++] = 'Y'; break; // Ý
        default: break;
      }
    } else if (c == 0xC4 && src[s+1] != '\0') {
      unsigned char c2 = (unsigned char)src[s+1];
      s += 2;
      switch (c2) {
        case 0x8C: dest[d++] = 'C'; break; // Č
        case 0x8D: dest[d++] = 'c'; break; // č
        case 0x8E: dest[d++] = 'D'; break; // Ď
        case 0x8F: dest[d++] = 'd'; break; // ď
        case 0x98: dest[d++] = 'E'; break; // Ě
        case 0x99: dest[d++] = 'e'; break; // ě
        default: break;
      }
    } else if (c == 0xC5 && src[s+1] != '\0') {
      unsigned char c2 = (unsigned char)src[s+1];
      s += 2;
      switch (c2) {
        case 0x87: dest[d++] = 'N'; break; // Ň
        case 0x88: dest[d++] = 'n'; break; //ň
        case 0x98: dest[d++] = 'R'; break; // Ř
        case 0x99: dest[d++] = 'r'; break; // ř
        case 0xA0: dest[d++] = 'S'; break; // Š
        case 0xA1: dest[d++] = 's'; break; // š
        case 0xA4: dest[d++] = 'T'; break; // Ť
        case 0xA5: dest[d++] = 't'; break; // ť
        case 0xAE: dest[d++] = 'U'; break; // Ů
        case 0xAF: dest[d++] = 'u'; break; // ů
        case 0xBD: dest[d++] = 'Z'; break; // Ž
        case 0xBE: dest[d++] = 'z'; break; // ž
        default: break;
      }
    } else {
      s++;
    }
  }
  dest[d] = '\0';
}

void display_update_cell(uint8_t idx, const char* label, const char* icon_name) {
  if (idx >= GRID_CELLS) return;

  char clean_label[16] = {0};
  if (label != nullptr) {
    sanitize_ascii(clean_label, label, sizeof(clean_label));
  }

  const char* clean_icon = (icon_name != nullptr) ? icon_name : "";

  // Pokud se ikona ani text nezměnily, vůbec nic nepřekreslujeme!
  if (strcmp(cell_labels[idx], clean_label) == 0 && strcmp(cell_icons[idx], clean_icon) == 0) {
    return;
  }

  strncpy(cell_labels[idx], clean_label, sizeof(cell_labels[idx]) - 1);
  cell_labels[idx][sizeof(cell_labels[idx]) - 1] = '\0';

  strncpy(cell_icons[idx], clean_icon, sizeof(cell_icons[idx]) - 1);
  cell_icons[idx][sizeof(cell_icons[idx]) - 1] = '\0';

  ensure_prefs();
  prefs.putString(("l" + String(idx)).c_str(), clean_label);
  prefs.putString(("i" + String(idx)).c_str(), clean_icon);

  if (is_connected_to_app) {
    render_cell(idx);
  }
}

void display_draw_bmp(uint8_t idx, const uint8_t* bmp24) {
  if (idx >= GRID_CELLS || bmp24 == nullptr || !is_connected_to_app || !pTft) return;

  int16_t x = get_cell_x(idx);
  int16_t y = get_cell_y(idx);

  tft.fillRect(x, y, CELL_W, CELL_H, COL_BLACK);
  for (uint8_t b = 0; b < BORDER_W; b++) {
    tft.drawRoundRect(x + b, y + b, CELL_W - 2*b, CELL_H - 2*b, 3, COL_ORANGE);
  }

  int16_t bx = x + (CELL_W - 24) / 2;
  int16_t by = y + (CELL_H - 24) / 2;
  tft.drawBitmap(bx, by, bmp24, 24, 24, COL_ORANGE);
}

void display_clear() {
  for (uint8_t i = 0; i < GRID_CELLS; i++) {
    cell_labels[i][0] = '\0';
    cell_icons[i][0] = '\0';
  }
  if (is_connected_to_app) {
    display_draw_grid();
  }
}

void display_show_message(const char* title, const char* msg) {
  if (!pTft) return;
  tft.fillScreen(COL_BLACK);
  tft.drawRoundRect(4, 4, DISP_WIDTH - 8, DISP_HEIGHT - 8, 5, COL_ORANGE);

  tft.setTextColor(COL_ORANGE);
  tft.setTextSize(2);
  tft.setCursor(16, 16);
  tft.print(title);

  tft.setTextColor(COL_WHITE);
  tft.setTextSize(1);
  tft.setCursor(16, 42);
  tft.print(msg);
}

void display_cell_press(uint8_t idx, bool pressed) {
  if (idx >= GRID_CELLS || !pTft) return;

  cell_physical_down[idx] = pressed;

  if (pressed) {
    cell_pressed_anim[idx] = true;
    cell_press_time[idx] = millis();
    render_cell_pressed(idx);
  } else {
    // Tlačítko uvolněno – pokud už uběhlo aspoň 140 ms, hned překreslíme
    if (millis() - cell_press_time[idx] >= 140) {
      cell_pressed_anim[idx] = false;
      render_cell(idx);
    }
    // Jinak cell_pressed_anim zůstane true a dokončí se v display_update()
  }
}

void display_update() {
  unsigned long now = millis();

  // Zajištění minimální doby svitu (140 ms) stisknuté buňky mřížky
  for (uint8_t i = 0; i < GRID_CELLS; i++) {
    if (cell_pressed_anim[i] && !cell_physical_down[i]) {
      if (now - cell_press_time[i] >= 140) {
        cell_pressed_anim[i] = false;
        if (is_connected_to_app) {
          render_cell(i);
        }
      }
    }
  }
}
