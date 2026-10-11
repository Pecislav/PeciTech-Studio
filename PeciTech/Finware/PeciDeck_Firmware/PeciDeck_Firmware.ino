/*
 * =============================================================================
 *   PECI DECK MK.1 - OFFICIAL FIRMWARE
 *   Vytvořeno pro PeciTech Studio
 *   Mikrokontrolér: ESP32-S3 DevKitC
 * =============================================================================
 */

#include "config.h"
#include "display_ui.h"
#include "buttons.h"
#include "encoders.h"
#include "protocol.h"

// Callback při stisku či uvolnění tlačítek (SW1..SW8)
void onButtonEvent(uint8_t btn_index, bool pressed) {
  protocol_send_button(btn_index, pressed);
  // Okamžitá vizuální animace stisknutí tlačítka přímo na displeji PeciDecku (0 ms latence!)
  display_cell_press(btn_index, pressed);
}

// Callback při pootočení enkodérů (+1 doprava / -1 doleva)
void onEncoderRotate(uint8_t enc_index, int8_t direction) {
  protocol_send_encoder(enc_index, direction);
}

// Callback při stisku integrovaného tlačítka enkodéru
void onEncoderButton(uint8_t enc_index, bool pressed) {
  protocol_send_encoder_btn(enc_index, pressed);
}

void setup() {
  // 1. Inicializace sériové linky
  protocol_setup();
  delay(300);
  Serial.println("\n\n========================================");
  Serial.println("       PECI DECK MK.1 STARTUJE          ");
  Serial.println("========================================");
  Serial0.println("\n\n========================================");
  Serial0.println("       PECI DECK MK.1 STARTUJE          ");
  Serial0.println("========================================");

  // 2. Inicializace tlačítek a enkodérů
  buttons_setup(onButtonEvent);
  encoders_setup(onEncoderRotate, onEncoderButton);
  Serial.println("[BOOT] Tlacitka a enkodery OK");
  Serial0.println("[BOOT] Tlacitka a enkodery OK");

  // Vypis diagnostiky pinu tlacitek do Serial Monitoru
  buttons_print_diag();

  // 3. Inicializace displeje – nastartuje v Standby/Offline režimu
  display_setup();

  // 4. Odeslání identifikační zprávy a nápovědy
  protocol_send_hello();
  Serial.println("\n[TIP] Do radku nahore v Serial Monitoru muzes napsat:");
  Serial.println("      'PROFILES' -> zobrazi vsech 11 hardwarovych profilu displeje");
  Serial.println("      'SET <N>'  -> prepne displej na profil N (napr. 'SET 2' pro zelenou)");
  Serial.println("      'DTEST'    -> znovu spusti test barev vsech profilu");
  Serial.println("      'TEST'     -> overi stav pinu tlacitek a enkoderu");
  Serial.println("      'BL 0' / 'BL 255' -> test podsviceni displeje");
  Serial.println("      'HELP'     -> zobrazi vsechny prikazy\n");
  Serial0.println("\n[TIP] Muzes poslat prikazy 'PROFILES', 'SET <1-11>', 'DTEST', 'TEST', 'HELP'.\n");
}

void loop() {
  buttons_update();
  encoders_update();
  protocol_process_incoming();
  display_update();
}
