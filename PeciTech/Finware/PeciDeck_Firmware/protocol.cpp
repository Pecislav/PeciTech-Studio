#include "protocol.h"
#include "config.h"
#include "display_ui.h"

static String rx_buffer_cdc = "";
static String rx_buffer_uart = "";

void protocol_setup() {
  Serial.begin(SERIAL_BAUD);   // USB CDC / Native USB
  Serial0.begin(SERIAL_BAUD);  // CH343 / UART port (COM3)
  rx_buffer_cdc.reserve(256);
  rx_buffer_uart.reserve(256);
}

static void send_both(const String& s) {
  Serial.print(s);
  Serial0.print(s);
}

static void send_both_ln(const String& s) {
  Serial.println(s);
  Serial0.println(s);
}

void protocol_send_hello() {
  String msg = "INFO:DEVICE=";
  msg += DEVICE_NAME;
  msg += ";FW=";
  msg += FW_VERSION;
  msg += ";BTNS=";
  msg += String(NUM_BUTTONS);
  msg += ";ENCS=";
  msg += String(NUM_ENCODERS);
  msg += ";DISP=284x76;STATUS=READY";
  send_both_ln(msg);
}

#include "buttons.h"

void protocol_send_button(uint8_t btn_idx, bool pressed) {
  // Protokol pro PC aplikaci:
  String msg = "B," + String(btn_idx) + "," + String(pressed ? 1 : 0);
  send_both_ln(msg);

  // Prehledny informativni vypis pro Serial Monitor pouze kdyz neni pripojena PC aplikace:
  if (!display_is_connected() && btn_idx < NUM_BUTTONS) {
    if (pressed) {
      String banner = ">>> [STISKNUTO] Klavesa " + String(btn_idx + 1) + 
                      " (" + BTN_CONFIG[btn_idx].kicad_name + " | GPIO " + String(BTN_CONFIG[btn_idx].gpio) + 
                      " | " + BTN_CONFIG[btn_idx].position_cz + ")";
      send_both_ln(banner);
    } else {
      String banner = "<<< [UVOLNENO]  Klavesa " + String(btn_idx + 1) + 
                      " (" + BTN_CONFIG[btn_idx].kicad_name + " | GPIO " + String(BTN_CONFIG[btn_idx].gpio) + ")";
      send_both_ln(banner);
    }
  }
}

void protocol_send_encoder(uint8_t enc_idx, int8_t direction) {
  String msg = "E," + String(enc_idx) + "," + String(direction);
  send_both_ln(msg);

  if (!display_is_connected()) {
    String name = (enc_idx == 0 ? "Vlevo" : (enc_idx == 1 ? "Uprostred" : "Vpravo"));
    String dbg = ">>> [ENKODER " + String(enc_idx + 1) + " - " + name + "] " +
                 (direction > 0 ? "DOPRAVA (+1)" : "DOLEVA (-1)");
    send_both_ln(dbg);
  }
}

void protocol_send_encoder_btn(uint8_t enc_idx, bool pressed) {
  String msg = "EB," + String(enc_idx) + "," + String(pressed ? 1 : 0);
  send_both_ln(msg);

  if (!display_is_connected()) {
    String name = (enc_idx == 0 ? "Vlevo" : (enc_idx == 1 ? "Uprostred" : "Vpravo"));
    String banner = (pressed ? ">>> [STISKNUTO] Tlacitko enkoderu " : "<<< [UVOLNENO]  Tlacitko enkoderu ") +
                    String(enc_idx + 1) + " (" + name + ")";
    send_both_ln(banner);
  }
}

static inline uint8_t hex_to_byte(char hi, char lo) {
  auto char_val = [](char c) -> uint8_t {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    return 0;
  };
  return (char_val(hi) << 4) | char_val(lo);
}

static unsigned long last_app_comm_time = 0;

static void execute_command(const String& cmd) {
  last_app_comm_time = millis();

  if (cmd == "PING") {
    send_both_ln("PONG");
    return;
  }

  if (cmd == "INFO" || cmd == "ID" || cmd == "DISCOVER") {
    protocol_send_hello();
    return;
  }

  // Interaktivní diagnostické příkazy pro uživatele
  if (cmd == "TEST" || cmd == "STATUS") {
    buttons_print_diag();
    return;
  }

  // Zkratka '1' nebo 'PROBE' - dotykový drátkový test
  if (cmd == "1" || cmd == "PROBE" || cmd == "DOTYK" || cmd == "WIRETEST" || cmd == "TEST:WIRE") {
    display_run_probe_test();
    return;
  }

  // Zkratka '2' nebo 'SCAN' - rychlý automatický elektrický test
  if (cmd == "2" || cmd == "SCAN" || cmd == "PINSCAN" || cmd == "TEST:SCAN") {
    display_run_scan_test();
    return;
  }

  // Zkratka '3' nebo 'PINTEST' / 'VOLTTEST' - střídavý test pro multimetr (3s cykly)
  if (cmd == "3" || cmd == "PINTEST" || cmd == "VOLTTEST" || cmd == "TEST:PINS" || cmd == "PINS") {
    display_run_pin_test();
    return;
  }

  // Trvalý multimetr režim: ALL 1 (vše na 3.3V) a ALL 0 (vše na 0.0V)
  if (cmd == "ALL 1" || cmd == "ALL1" || cmd == "HIGH") {
    display_set_all_pins(true);
    return;
  }
  if (cmd == "ALL 0" || cmd == "ALL0" || cmd == "LOW") {
    display_set_all_pins(false);
    return;
  }

  if (cmd == "RUN" || cmd == "START" || cmd == "DISP") {
    display_apply_profile(display_get_active_profile());
    send_both_ln("[OK] Displej obnoven.");
    return;
  }

  if (cmd == "DTEST" || cmd == "TEST:DISP" || cmd == "TEST DISP") {
    display_run_interactive_test();
    return;
  }

  if (cmd == "PROFILES" || cmd == "PROFILE") {
    display_print_profiles();
    return;
  }

  // Přímé příkazy pro barevnou výplň displeje
  if (cmd == "RED" || cmd == "CERVENA") {
    display_fill_color(COL_RED, "CERVENA");
    return;
  }
  if (cmd == "GREEN" || cmd == "ZELENA") {
    display_fill_color(COL_GREEN, "ZELENA");
    return;
  }
  if (cmd == "BLUE" || cmd == "MODRA") {
    display_fill_color(COL_BLUE, "MODRA");
    return;
  }
  if (cmd == "BLACK" || cmd == "CERNA") {
    display_fill_color(COL_BLACK, "CERNA");
    return;
  }
  if (cmd == "WHITE" || cmd == "BILA") {
    display_fill_color(COL_WHITE, "BILA");
    return;
  }
  if (cmd == "ORANGE" || cmd == "ORANZOVA") {
    display_fill_color(COL_ORANGE, "ORANZOVA");
    return;
  }

  if (cmd.startsWith("SET ") || cmd.startsWith("SET,") || cmd.startsWith("PROFILE ") || cmd.startsWith("PROFILE,")) {
    int space = cmd.indexOf(' ');
    int comma = cmd.indexOf(',');
    int idx = (comma >= 0 ? comma : space);
    int p_id = cmd.substring(idx + 1).toInt();
    if (p_id >= 1 && p_id <= display_get_profile_count()) {
      display_apply_profile((uint8_t)p_id);
      send_both_ln("[OK] Aktivovan displej profil " + String(p_id));
    } else {
      send_both_ln("[CHYBA] Neplatny profil. Zadej 1 az " + String(display_get_profile_count()));
    }
    return;
  }

  if (cmd == "HELP" || cmd == "?") {
    send_both_ln("\n=================== PECI DECK MK.1 - PRIKAZY ===================");
    send_both_ln("PROBE (nebo DOTYK)   - INTERAKTIVNI TEST VODIVOSTI DRATKEM: dotykas se pinu a vidis reakci!");
    send_both_ln("SCAN (nebo PINSCAN)  - RYCHLY ELEKTRICKY TEST PINU J1: overi zkraty na GND a externi pull-upy");
    send_both_ln("VOLTTEST (PINTEST)   - MULTIMETR TEST: strida 3.3V a 0V na kazdem pinu J1 (pro mereni)");
    send_both_ln("DTEST                - Spusti test 8 profilu displeje (vyzkousi barvy na displeji)");
    send_both_ln("TEST                 - Vypise aktualni stav vsech 8 tlacitek a 3 enkoderu");
    send_both_ln("PROFILES             - Zobrazi seznam 8 profilu (SW-SPI vs HW-SPI, offsety)");
    send_both_ln("SET <1-8>            - Aktivuje profil (napr. 'SET 1' nebo 'SET 2')");
    send_both_ln("RED / GREEN / BLUE   - Vyplni displej danou barvou");
    send_both_ln("BLACK / WHITE / ORANGE - Vyplni displej danou barvou");
    send_both_ln("INV 1 / INV 0        - Zapne/vypne inverzi barev");
    send_both_ln("BL <0-255>           - Nastavi jas podsviceni");
    send_both_ln("STANDBY / OFFLINE    - Vykresli standby obrazovku PeciDeck MK.1");
    send_both_ln("ONLINE / GRID        - Prepne do herni mrizky (8 bunek)");
    send_both_ln("================================================================\n");
    return;
  }

  // Příkaz pro přechod do online módu (zobrazení mřížky)
  if (cmd == "DISP:START" || cmd == "DISP:ONLINE") {
    display_set_connected(true);
    return;
  }

  // Příkaz pro přechod do offline standby obrazovky ("PeciDeck MK.1")
  if (cmd == "DISP:OFFLINE" || cmd == "DISP:STANDBY") {
    display_set_connected(false);
    last_app_comm_time = 0;
    return;
  }

  // Test inverze barev: INV 0 / INV 1 nebo DISP:INV,1 / DISP:INV,0
  if (cmd.startsWith("INV ") || cmd.startsWith("INV,") || cmd.startsWith("DISP:INV,") || cmd.startsWith("DISP:INV ")) {
    int comma = cmd.indexOf(',');
    int space = cmd.indexOf(' ');
    int idx = (comma >= 0 ? comma : space);
    int inv = cmd.substring(idx + 1).toInt();
    display_set_inversion(inv != 0);
    send_both_ln("[OK] Inverze barev nastavena na: " + String(inv));
    return;
  }

  if (cmd == "DISP:GRID") {
    display_set_connected(true);
    display_draw_grid();
    return;
  }

  if (cmd == "DISP:CLEAR") {
    display_clear();
    return;
  }

  // DISP:BL,<0-255>  (nastavení jasu)
  if (cmd.startsWith("DISP:BL,")) {
    int val = cmd.substring(8).toInt();
    if (val < 0) val = 0;
    if (val > 255) val = 255;
    display_set_brightness((uint8_t)val);
    return;
  }

  // DISP:PRESS,<idx>,<1|0>
  if (cmd.startsWith("DISP:PRESS,")) {
    int p1 = cmd.indexOf(',', 11);
    if (p1 > 0) {
      uint8_t idx = cmd.substring(11, p1).toInt();
      bool pressed = (cmd.substring(p1 + 1).toInt() != 0);
      display_cell_press(idx, pressed);
    }
    return;
  }

  // DISP:CELL,<idx>,<text>
  if (cmd.startsWith("DISP:CELL,")) {
    display_set_connected(true);
    int p1 = cmd.indexOf(',', 10);
    if (p1 > 0) {
      uint8_t idx = cmd.substring(10, p1).toInt();
      String label = cmd.substring(p1 + 1);
      label.trim();
      display_update_cell(idx, label.c_str(), "");
    }
    return;
  }

  // DISP:ICON,<idx>,<icon_name>
  if (cmd.startsWith("DISP:ICON,")) {
    int p1 = cmd.indexOf(',', 10);
    if (p1 > 0) {
      uint8_t idx = cmd.substring(10, p1).toInt();
      String icon = cmd.substring(p1 + 1);
      icon.trim();
      display_update_cell(idx, nullptr, icon.c_str());
    }
    return;
  }

  // DISP:SET,<idx>,<icon_name>,<label>
  if (cmd.startsWith("DISP:SET,")) {
    int p1 = cmd.indexOf(',', 9);
    int p2 = cmd.indexOf(',', p1 + 1);
    if (p1 > 0 && p2 > 0) {
      uint8_t idx = cmd.substring(9, p1).toInt();
      String icon = cmd.substring(p1 + 1, p2);
      String label = cmd.substring(p2 + 1);
      icon.trim();
      label.trim();
      display_update_cell(idx, label.c_str(), icon.c_str());
    }
    return;
  }

  // DISP:PAGE,<c0>,<c1>,<c2>,<c3>,<c4>,<c5>,<c6>,<c7>
  if (cmd.startsWith("DISP:PAGE,")) {
    display_set_connected(true);
    String rest = cmd.substring(10);
    for (uint8_t i = 0; i < GRID_CELLS; i++) {
      int comma = rest.indexOf(',');
      String val;
      if (comma >= 0) {
        val = rest.substring(0, comma);
        rest = rest.substring(comma + 1);
      } else {
        val = rest;
        rest = "";
      }
      val.trim();
      display_update_cell(i, val.c_str(), "");
    }
    return;
  }

  // DISP:MSG,<title>,<msg>
  if (cmd.startsWith("DISP:MSG,")) {
    int comma = cmd.indexOf(',', 9);
    if (comma > 0) {
      String title = cmd.substring(9, comma);
      String text = cmd.substring(comma + 1);
      title.trim();
      text.trim();
      display_show_message(title.c_str(), text.c_str());
    }
    return;
  }

  // DISP:BMP,<idx>,<hex144>
  if (cmd.startsWith("DISP:BMP,")) {
    display_set_connected(true);
    int p1 = cmd.indexOf(',', 9);
    if (p1 > 0) {
      uint8_t idx = cmd.substring(9, p1).toInt();
      String hex = cmd.substring(p1 + 1);
      hex.trim();
      if (hex.length() >= 144) {
        uint8_t bmp[72];
        for (int i = 0; i < 72; i++) {
          bmp[i] = hex_to_byte(hex.charAt(i * 2), hex.charAt(i * 2 + 1));
        }
        display_draw_bmp(idx, bmp);
      }
    }
    return;
  }
}

static void process_stream(Stream& s, String& buf) {
  while (s.available() > 0) {
    char c = (char)s.read();
    if (c == '\n') {
      buf.trim();
      if (buf.length() > 0) {
        execute_command(buf);
      }
      buf = "";
    } else if (c != '\r') {
      buf += c;
      if (buf.length() > 240) {
        buf = "";
      }
    }
  }
}

void protocol_process_incoming() {
  process_stream(Serial, rx_buffer_cdc);
  process_stream(Serial0, rx_buffer_uart);
}
