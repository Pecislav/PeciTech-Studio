#include "buttons.h"

static ButtonEventCallback btn_callback = nullptr;
static bool btn_last_state[NUM_BUTTONS];
static unsigned long btn_last_debounce[NUM_BUTTONS];

void buttons_setup(ButtonEventCallback callback) {
  btn_callback = callback;
  for (uint8_t i = 0; i < NUM_BUTTONS; i++) {
    // Reset pinu (klíčové pro GPIO 41, aby se uvolnil z JTAG rozhraní)
    gpio_reset_pin((gpio_num_t)BTN_CONFIG[i].gpio);
    pinMode(BTN_CONFIG[i].gpio, INPUT_PULLUP);
    btn_last_state[i] = digitalRead(BTN_CONFIG[i].gpio);
    btn_last_debounce[i] = 0;
  }
}

void buttons_print_diag() {
  Serial.println("\n========================================================");
  Serial.println("   PECI DECK MK.1 - AKTUALNI STAV VSECH TLACITEK A PINU   ");
  Serial.println("========================================================");
  for (uint8_t i = 0; i < NUM_BUTTONS; i++) {
    int val = digitalRead(BTN_CONFIG[i].gpio);
    String status = (val == HIGH) ? "1 (HIGH) -> [OK: Ceka na stisk]" : "0 (LOW)  -> !!! SEPNUTO NA GND (Stisknuto/Zkrat) !!!";
    
    Serial.print("Klavesa ");
    Serial.print(i + 1);
    Serial.print(" [");
    Serial.print(BTN_CONFIG[i].kicad_name);
    Serial.print(" | GPIO ");
    if (BTN_CONFIG[i].gpio < 10) Serial.print(" ");
    Serial.print(BTN_CONFIG[i].gpio);
    Serial.print("] (");
    Serial.print(BTN_CONFIG[i].position_cz);
    Serial.print("): ");
    Serial.println(status);

    Serial0.print("Klavesa ");
    Serial0.print(i + 1);
    Serial0.print(" [");
    Serial0.print(BTN_CONFIG[i].kicad_name);
    Serial0.print(" | GPIO ");
    if (BTN_CONFIG[i].gpio < 10) Serial0.print(" ");
    Serial0.print(BTN_CONFIG[i].gpio);
    Serial0.print("] (");
    Serial0.print(BTN_CONFIG[i].position_cz);
    Serial0.print("): ");
    Serial0.println(status);
  }

  // Detailní elektrická analýza pinu GPIO 2 (Klávesa 5):
  pinMode(2, INPUT_PULLUP);
  delay(1);
  int pu2 = digitalRead(2);
  pinMode(2, INPUT_PULLDOWN);
  delay(1);
  int pd2 = digitalRead(2);
  pinMode(2, INPUT_PULLUP); // Zpět na pull-up

  String diag2 = "\n[KONTROLA KLAVESY 5 (GPIO 2)]:\n";
  diag2 += "  - S internim Pull-Up:   " + String(pu2) + "\n";
  diag2 += "  - S internim Pull-Down: " + String(pd2) + "\n";
  if (pu2 == 0 && pd2 == 0) {
    diag2 += "  -> ZAVADA: Pin GPIO 2 je trvale zkratovan na GND (pajeci mustek na spinaci SW2 nebo pinu 40)!\n";
  } else if (pu2 == 1 && pd2 == 0) {
    diag2 += "  -> VYSLEDEK: ESP32 cte pin GPIO 2 spravne (HIGH). Pokud se po stisku nic nedeje, spinac SW2 nesepne na GND (zkontroluj pajeni pinu SW2 nebo vymen spinac)!\n";
  } else {
    diag2 += "  -> Stav pinu: " + String(pu2) + "\n";
  }
  Serial.println(diag2);
  Serial0.println(diag2);

  Serial.println("--------------------------------------------------------");
  Serial0.println("--------------------------------------------------------");
  for (uint8_t i = 0; i < NUM_ENCODERS; i++) {
    int val_btn = digitalRead(ENC_PINS[i].pin_btn);
    int val_a = digitalRead(ENC_PINS[i].pin_a);
    int val_b = digitalRead(ENC_PINS[i].pin_b);

    String enc_str = "Enkoder " + String(i + 1) + " (SW" + String(i + 9) + "): " +
                     "A=GPIO" + String(ENC_PINS[i].pin_a) + " [" + String(val_a) + "], " +
                     "B=GPIO" + String(ENC_PINS[i].pin_b) + " [" + String(val_b) + "], " +
                     "Tlacitko=GPIO" + String(ENC_PINS[i].pin_btn) + " [" + String(val_btn) + "]" +
                     (val_btn == LOW ? " -> !!! TLACITKO SEPNUTO !!!" : " -> [OK]");
    Serial.println(enc_str);
    Serial0.println(enc_str);
  }
  Serial.println("========================================================\n");
  Serial0.println("========================================================\n");
}

void buttons_update() {
  unsigned long now = millis();

  for (uint8_t i = 0; i < NUM_BUTTONS; i++) {
    bool raw_state = digitalRead(BTN_CONFIG[i].gpio);

    if (raw_state != btn_last_state[i]) {
      if ((now - btn_last_debounce[i]) > BTN_DEBOUNCE_MS) {
        btn_last_state[i] = raw_state;
        btn_last_debounce[i] = now;

        if (btn_callback != nullptr) {
          // raw_state == LOW znamená stisknuto (sepnuto na GND)
          btn_callback(i, raw_state == LOW);
        }
      }
    }
  }
}
