import time
import threading
import serial
import serial.tools.list_ports

class HardwareSerial:
    def __init__(self, on_event_cb=None, on_status_change_cb=None):
        self.on_event_cb = on_event_cb
        self.on_status_change_cb = on_status_change_cb

        self.ser = None
        self.is_connected = False
        self.port_name = None
        self.device_info = {}

        self._running = False
        self._thread = None
        self._write_lock = threading.Lock()

    @property
    def port(self):
        return self.port_name

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self.is_connected:
            self.send_command("DISP:OFFLINE")
            time.sleep(0.08)
        self.disconnect()

    def disconnect(self):
        with self._write_lock:
            if self.ser and self.ser.is_open:
                try:
                    self.ser.close()
                except Exception:
                    pass
            self.ser = None
            if self.is_connected:
                self.is_connected = False
                if self.on_status_change_cb:
                    self.on_status_change_cb(False, None)

    def send_command(self, cmd):
        if not self.is_connected or not self.ser or not self.ser.is_open:
            return False
        with self._write_lock:
            try:
                line = (cmd.strip() + "\n").encode("utf-8")
                self.ser.write(line)
                self.ser.flush()
                return True
            except Exception as e:
                print(f"[Serial] Chyba zápisu: {e}")
                self.disconnect()
                return False

    def update_button(self, btn_idx, icon="", label=""):
        """Okamžitá aktualizace jedné buňky bez probliknutí celého displeje."""
        if not self.is_connected:
            return False
        return self.send_command(f"DISP:SET,{btn_idx},{icon},{label}")

    def update_brightness(self, brightness):
        """Okamžitá změna jasu podsvícení."""
        if not self.is_connected:
            return False
        return self.send_command(f"DISP:BL,{brightness}")

    def press_button(self, btn_idx, pressed=True):
        """Vizuální animace stisku tlačítka na displeji PeciDeck."""
        if not self.is_connected:
            return False
        return self.send_command(f"DISP:PRESS,{btn_idx},{1 if pressed else 0}")

    def sync_profile(self, profile):
        if not self.is_connected:
            return
        # Přepnutí displeje do online režimu (zobrazení mřížky)
        self.send_command("DISP:START")
        time.sleep(0.03)

        buttons = profile.get("buttons", [])
        for b in buttons:
            idx = b.get("id", 0)
            icon = b.get("icon", "")
            label = b.get("label", "")
            self.send_command(f"DISP:SET,{idx},{icon},{label}")

        brightness = profile.get("brightness", 255)
        self.send_command(f"DISP:BL,{brightness}")

    def set_inversion(self, invert):
        val = 1 if invert else 0
        self.send_command(f"DISP:INV,{val}")

    def _worker_loop(self):
        last_heartbeat = 0
        while self._running:
            if not self.is_connected:
                self._try_auto_connect()
                time.sleep(1.5)
            else:
                now = time.time()
                if now - last_heartbeat >= 1.5:
                    self.send_command("PING")
                    last_heartbeat = now
                try:
                    if self.ser and self.ser.in_waiting:
                        line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                        if line:
                            self._process_line(line)
                    else:
                        time.sleep(0.01)
                except Exception as e:
                    print(f"[Serial] Zařízení odpojeno: {e}")
                    self.disconnect()
                    time.sleep(1.0)

    def _try_auto_connect(self):
        ports = list(serial.tools.list_ports.comports())
        # Ignorovat interní ACPI/motherboard sériové porty (např. COM1)
        ports = [p for p in ports if "acpi" not in (p.hwid or "").lower()]
        # Seřadit tak, aby USB/CH34/ESP/UART převodníky byly testovány jako první
        ports.sort(
            key=lambda p: (
                0 if any(k in (p.description or "").lower() or k in (p.hwid or "").lower()
                         for k in ["usb", "ch34", "cp210", "esp", "ftdi", "silicon labs", "uart"])
                else 1
            )
        )

        for port_info in ports:
            pname = port_info.device
            test_ser = None
            try:
                test_ser = serial.Serial()
                test_ser.port = pname
                test_ser.baudrate = 115200
                test_ser.timeout = 0.2
                test_ser.dtr = False
                test_ser.rts = False
                test_ser.open()

                accum = ""
                t0 = time.time()
                info_sent = False

                # Dát zařízení dostatek času na boot po resetu (cca 2s) nebo okamžitou odpověď
                while time.time() - t0 < 3.2:
                    if test_ser.in_waiting:
                        chunk = test_ser.read(test_ser.in_waiting).decode("utf-8", errors="ignore")
                        accum += chunk
                        if "DEVICE=PeciDeck_MK1" in accum or ("PeciDeck_MK1" in accum and "FW=" in accum):
                            break

                    elapsed = time.time() - t0
                    # Pokud zařízení neresetovalo, poslat dotaz INFO po krátké pauze
                    if not info_sent and elapsed > 0.35:
                        test_ser.write(b"INFO\n")
                        test_ser.flush()
                        info_sent = True
                    elif info_sent and elapsed > 1.8 and "DEVICE=" not in accum:
                        test_ser.write(b"INFO\n")
                        test_ser.flush()

                    time.sleep(0.05)

                if "pecideck" in accum.lower():
                    # Pokud byl zachycen boot banner, ale ne celý řádek s DEVICE, počkat na dokončení
                    t1 = time.time()
                    while time.time() - t1 < 1.5 and "device=" not in accum.lower():
                        if test_ser.in_waiting:
                            accum += test_ser.read(test_ser.in_waiting).decode("utf-8", errors="ignore")
                        time.sleep(0.05)

                    print(f"[Serial] Nalezen PeciDeck MK.1 na portu {pname}!")
                    self.ser = test_ser
                    self.port_name = pname
                    self.is_connected = True
                    self._parse_info(accum)
                    if self.on_status_change_cb:
                        self.on_status_change_cb(True, pname)
                    return
                else:
                    test_ser.close()
            except Exception:
                if test_ser and test_ser.is_open:
                    try:
                        test_ser.close()
                    except Exception:
                        pass

    def _parse_info(self, text):
        for line in text.splitlines():
            if "PeciDeck_MK1" in line or "DEVICE=" in line:
                parts = line.strip().split(";")
                for p in parts:
                    if "=" in p:
                        k, v = p.split("=", 1)
                        if k.startswith("INFO:"):
                            k = k[5:]
                        self.device_info[k] = v

    def _process_line(self, line):
        if not line or line == "PONG":
            return
        if line.startswith("INFO:") or line.startswith("DEVICE:"):
            self._parse_info(line)
            return

        parts = line.split(",")
        event_type = parts[0]

        if event_type == "B" and len(parts) >= 3:
            try:
                btn_idx = int(parts[1])
                pressed = (parts[2] == "1")
                if self.on_event_cb:
                    self.on_event_cb("button", btn_idx, pressed)
            except ValueError:
                pass

        elif event_type == "E" and len(parts) >= 3:
            try:
                enc_idx = int(parts[1])
                direction = int(parts[2])
                if self.on_event_cb:
                    self.on_event_cb("encoder_rotate", enc_idx, direction)
            except ValueError:
                pass

        elif event_type == "EB" and len(parts) >= 3:
            try:
                enc_idx = int(parts[1])
                pressed = (parts[2] == "1")
                if self.on_event_cb:
                    self.on_event_cb("encoder_btn", enc_idx, pressed)
            except ValueError:
                pass
