import os
import sys
import socket
import threading

# Optimalizace GIL switch intervalu: z výchozích 5ms na 20ms.
# Zajišťuje, že hlavní GUI vlákno Tkinteru dostane dostatečně dlouhý nepřerušovaný
# čas pro zpracování událostí myši (včetně 1000Hz gaming myší) a nedochází k trhání kurzoru.
sys.setswitchinterval(0.02)

from PIL import Image
import customtkinter as ctk
import pystray
from pystray import MenuItem as TrayItem, Menu as TrayMenu

from config_manager import ConfigManager
from hardware_serial import HardwareSerial
from obs_controller import OBSController
from discord_controller import DiscordController
from twitch_controller import TwitchController
from action_handler import ActionHandler
from ui.dashboard_view import DashboardView
from ui.deck_view import DeckView
from ui.settings_view import SettingsModal

_app_assets_logo = os.path.join(os.path.dirname(__file__), "assets", "PeciTech_logo_aplikace.png")
LOGO_PATH = _app_assets_logo if os.path.exists(_app_assets_logo) else os.path.join(os.path.dirname(__file__), "..", "..", "Logo", "PeciTech_logo_aplikace.png")
import ctypes
kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32
ERROR_ALREADY_EXISTS = 183
SINGLE_INSTANCE_PORT = 49258

try:
    # Nastavíme standardní US layout (00000409) pro celý proces aplikace,
    # aby klávesové zkratky a nízkoúrovňové odposlechy fungovaly 100% spolehlivě
    # a nezávisle na zvoleném jazyce (např. čeština vs angličtina) v OS.
    hkl_us = user32.LoadKeyboardLayoutW("00000409", 1)
    if hkl_us:
        user32.ActivateKeyboardLayout(hkl_us, 0x00000100) # KLF_SETFORPROCESS
except Exception:
    pass

def ensure_single_instance(port=SINGLE_INSTANCE_PORT):
    """
    Zajišťuje běh pouze jediné instance aplikace pomocí systémového Win32 Mutexu a TCP soketu.
    Pokud již aplikace běží:
    1. Pošle běžící instanci signál RESTORE pro okamžité obnovení z oznamovací lišty do popředí.
    2. Pomocí Win32 API přenese existující okno přímo do popředí.
    3. Druhý proces čistě ukončí (žádné duplicitní ikony v liště ani konflikty s COM portem).
    """
    # 1. Globální Win32 Mutex - 100% spolehlivý na Windows (nezávislý na síti)
    mutex = kernel32.CreateMutexW(None, False, "Local\\PeciDeckStudio_SingleInstance_Mutex")
    last_err = kernel32.GetLastError()

    if last_err == ERROR_ALREADY_EXISTS:
        # Aplikace již běží! Pošleme signál RESTORE
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(1.2)
            client.connect(("127.0.0.1", port))
            client.sendall(b"RESTORE\n")
            client.close()
        except Exception:
            # Fallback - přeneseme okno do popředí přímo přes Win32
            try:
                hwnd = user32.FindWindowW(None, "PeciTech Studio – Peci Deck MK.1")
                if hwnd:
                    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                    user32.SetForegroundWindow(hwnd)
            except Exception:
                pass
        sys.exit(0)

    # 2. Jsme první instance: otevřeme TCP soket pro příjem RESTORE příkazů (BEZ SO_REUSEADDR!)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        sock.listen(5)
    except Exception as e:
        print(f"[SingleInstance] Soket bind info: {e}")
        sock = None

    return (sock, mutex)

class PeciDeckApp(ctk.CTk):
    def __init__(self, instance_socket=None, instance_mutex=None, instance_info=None):
        super().__init__()
        if instance_info:
            self.instance_socket, self.instance_mutex = instance_info
        else:
            self.instance_socket = instance_socket
            self.instance_mutex = instance_mutex
        if self.instance_socket:
            threading.Thread(target=self._listen_single_instance, daemon=True).start()

        # Inicializace správců
        self.config_mgr = ConfigManager()

        obs_cfg = self.config_mgr.settings.get("obs", {})
        self.obs = OBSController(
            host=obs_cfg.get("host", "localhost"),
            port=obs_cfg.get("port", 4455),
            password=obs_cfg.get("password", ""),
            auto_connect=obs_cfg.get("auto_connect", True),
            on_status_change_cb=self._on_obs_status_change
        )

        self.discord = DiscordController(config_manager=self.config_mgr)
        self.twitch = TwitchController(config_manager=self.config_mgr)

        self.serial = HardwareSerial(
            on_event_cb=self._on_hardware_event,
            on_status_change_cb=self._on_hardware_status_change
        )

        self.action_handler = ActionHandler(
            obs_controller=self.obs,
            serial_bridge=self.serial,
            config_manager=self.config_mgr,
            on_page_change_cb=self._on_page_action,
            discord_controller=self.discord,
            twitch_controller=self.twitch
        )

        # Základní nastavení okna (Pevně uzamčená velikost 1160x760 bez nežádoucího roztažení)
        self.title("PeciTech Studio – Peci Deck MK.1")
        self.geometry("1160x780")
        self.minsize(1120, 720)
        self.resizable(True, True)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Nastavení ikony okna
        self._load_icon()

        # Správa zavření okna (Okamžité čisté ukončení a přepnutí displeje do standby režimu)
        self.protocol("WM_DELETE_WINDOW", self._on_close_attempt)

        # Hlavní kontejner
        self.main_container = ctk.CTkFrame(self, fg_color="#0D0E12", corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        # Inicializace obou hlavních obrazovek
        self.dashboard_view = DashboardView(
            self.main_container,
            serial_bridge=self.serial,
            on_configure_cb=self._show_deck,
            on_scan_cb=self._on_scan,
            on_settings_cb=self._open_settings_modal
        )

        self.deck_view = DeckView(
            self.main_container,
            config_mgr=self.config_mgr,
            serial_bridge=self.serial,
            action_handler=self.action_handler,
            on_back_cb=self._show_dashboard,
            on_settings_cb=self._open_settings_modal,
            obs_controller=self.obs,
            discord_controller=self.discord,
            twitch_controller=self.twitch
        )

        # In-app moderní okno nastavení ve stylu Cricut Design Space (Obrázek 4)
        self.settings_modal = SettingsModal(
            self.main_container,
            config_mgr=self.config_mgr,
            serial_bridge=self.serial,
            obs_controller=self.obs,
            on_scan_cb=self._on_scan,
            discord_controller=self.discord,
            twitch_controller=self.twitch
        )

        # VÝCHOZÍ OBRAZOVKA PŘI SPUŠTĚNÍ: Základní menu "Moje Zařízení" (Fotka 1)
        self.dashboard_view.pack(fill="both", expand=True)

        # Spuštění komunikace se sériovou linkou na pozadí
        self.serial.start()

        # Spuštění automatického připojování k OBS na pozadí
        self.obs.start_auto_reconnect()

        # Inicializace systémové lišty (System Tray) pro běh na pozadí
        self._init_tray()

    def _load_icon(self):
        try:
            if os.path.exists(LOGO_PATH):
                self.icon_image = Image.open(LOGO_PATH)
            else:
                self.icon_image = Image.new("RGBA", (64, 64), color=(255, 122, 41, 255))
        except Exception:
            self.icon_image = Image.new("RGBA", (64, 64), color=(255, 122, 41, 255))

    def _show_dashboard(self):
        """Návrat do základního menu Moje Zařízení."""
        self.deck_view.pack_forget()
        self.dashboard_view.pack(fill="both", expand=True)

    def _show_deck(self):
        """Přechod do konfigurace PeciDeck MK.1."""
        self.dashboard_view.pack_forget()
        self.deck_view.pack(fill="both", expand=True)

    def _on_scan(self):
        """Znovu vyhledá COM porty."""
        if not self.serial.is_connected:
            self.serial.disconnect()

    def _open_settings_modal(self):
        """Otevře moderní in-app okno nastavení ve stylu Cricut Design Space."""
        self.settings_modal.show()

    def _on_hardware_status_change(self, is_connected, port):
        """Reakce na připojení/odpojení USB hardware."""
        def _update():
            self.dashboard_view.update_connection_status(is_connected, port)
            if hasattr(self, "settings_modal"):
                self.settings_modal.update_hardware_status(is_connected, port)
            if is_connected:
                # Synchronizujeme profil do displeje při prvním připojení
                self.serial.sync_profile(self.config_mgr.profile)

        self.after(0, _update)

    def _on_hardware_event(self, event_type, index, value):
        """Reakce na fyzické stisknutí tlačítka nebo otočení enkodéru na zařízení."""
        def _animate():
            if event_type == "button":
                self.deck_view.highlight_button(index, value)
            elif event_type == "encoder_btn":
                self.deck_view.highlight_encoder(index, value)
            elif event_type == "encoder_rotate":
                self.deck_view.animate_encoder_rotate(index, value)
        self.after(0, _animate)

        # Spuštění akce
        if event_type == "button" and value is True:
            buttons = self.config_mgr.profile.get("buttons", [])
            if 0 <= index < len(buttons):
                bdata = buttons[index]
                self.action_handler.execute(bdata)
                if hasattr(self, "deck_view"):
                    self.deck_view.toggle_button_runtime_state(index)

        elif event_type == "encoder_rotate":
            encoders = self.config_mgr.profile.get("encoders", [])
            if 0 <= index < len(encoders):
                edata = encoders[index]
                action = edata.get("cw" if value > 0 else "ccw", {})
                self.action_handler.execute(action)

        elif event_type == "encoder_btn" and value is True:
            encoders = self.config_mgr.profile.get("encoders", [])
            if 0 <= index < len(encoders):
                edata = encoders[index]
                action = edata.get("btn", {})
                self.action_handler.execute(action)

    def _on_page_action(self, param):
        """Reakce na hardwarové nebo softwarové přepnutí stránky/složky."""
        def _exec():
            if param == "profile_switch":
                if hasattr(self, "deck_view"):
                    self.deck_view._render_profile_bar()
                    self.deck_view._render_pages_pill()
                    self.deck_view._refresh_all_buttons_ui()
                    self.deck_view._refresh_all_encoders_ui()
                if self.serial and self.serial.is_connected:
                    self.serial.sync_profile(self.config_mgr.profile)
                return

            pages = self.config_mgr.profile.get("pages", [])
            if not pages:
                return
            current = self.config_mgr.profile.get("active_page", 0)
            target = current

            if param == "next":
                target = (current + 1) % len(pages)
            elif param == "prev":
                target = (current - 1) % len(pages)
            elif param.startswith("goto:"):
                try:
                    target = int(param.split(":", 1)[1])
                except Exception:
                    pass
            elif param.startswith("folder:"):
                try:
                    target = int(param.split(":", 1)[1])
                except Exception:
                    pass
            elif param == "back":
                curr_pg = pages[current] if current < len(pages) else {}
                target = curr_pg.get("parent_page", 0)

            if 0 <= target < len(pages):
                self.deck_view.switch_to_page(target)

        try:
            self.after(0, _exec)
        except Exception:
            pass

    def _on_obs_status_change(self, is_connected):
        """Reakce na změnu stavu připojení k OBS WebSocket."""
        def _update():
            try:
                if hasattr(self, "dashboard_view"):
                    self.dashboard_view.update_obs_status(is_connected)
                if hasattr(self, "deck_view"):
                    self.deck_view.update_obs_status(is_connected)
                if hasattr(self, "settings_modal") and hasattr(self.settings_modal, "lbl_obs_tab_status"):
                    self.settings_modal.lbl_obs_tab_status.configure(
                        text="● Připojeno k OBS" if is_connected else "● Odpojeno od OBS",
                        text_color="#2ECC71" if is_connected else "#E74C3C"
                    )
            except Exception:
                pass

        try:
            self.after(0, _update)
        except Exception:
            pass

    def _init_tray(self):
        """Inicializace ikony v systémové liště (System Tray) pro běh na pozadí."""
        try:
            menu = TrayMenu(
                TrayItem("Otevřít PeciDeck Studio", self._show_window_from_tray, default=True),
                TrayItem("Ztlumit mikrofon", lambda: self.discord.toggle_mute()),
                TrayMenu.SEPARATOR,
                TrayItem("Ukončit aplikaci", self._quit_app)
            )
            tray_img = self.icon_image.resize((64, 64)) if hasattr(self, "icon_image") else Image.new("RGBA", (64, 64), color=(255, 122, 41, 255))
            self.tray_icon = pystray.Icon("PeciDeckStudio", tray_img, "PeciDeck Studio", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            print(f"[Tray] Nelze inicializovat systémovou lištu: {e}")
            self.tray_icon = None

    def _listen_single_instance(self):
        """Naslouchá novým pokusům o spuštění aplikace a obnoví okno na popředí."""
        while True:
            try:
                if not getattr(self, "instance_socket", None):
                    break
                conn, _ = self.instance_socket.accept()
                data = conn.recv(1024)
                conn.close()
                if b"RESTORE" in data:
                    self.after(0, self._show_window_from_tray)
            except Exception:
                break

    def _show_window_from_tray(self, icon=None, item=None):
        """Obnoví zobrazení okna aplikace z oznamovací lišty a přenese jej do popředí."""
        def _restore():
            self.deiconify()
            self.state("normal")
            try:
                import ctypes
                hwnd = self.winfo_id()
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass
            self.lift()
            self.attributes("-topmost", True)
            self.after(100, lambda: self.attributes("-topmost", False))
            self.focus_force()
        self.after(0, _restore)

    def _on_close_attempt(self):
        """Při zavření křížkem minimalizuje do systémové lišty pro nepřetržitý běh na pozadí."""
        min_to_tray = self.config_mgr.settings.get("minimize_to_tray", True)
        if min_to_tray and getattr(self, "tray_icon", None):
            self.withdraw()
        else:
            self._quit_app()

    def _quit_app(self, icon=None, item=None):
        """Čisté ukončení celé aplikace včetně systémové lišty, OBS, COM portu a instance socketu."""
        def _cleanup():
            try:
                if getattr(self, "instance_socket", None):
                    self.instance_socket.close()
                    self.instance_socket = None
            except Exception:
                pass
            try:
                if getattr(self, "instance_mutex", None):
                    kernel32.CloseHandle(self.instance_mutex)
                    self.instance_mutex = None
            except Exception:
                pass
            try:
                if getattr(self, "tray_icon", None):
                    self.tray_icon.stop()
            except Exception:
                pass
            try:
                self.obs.stop_auto_reconnect()
                self.obs.disconnect()
            except Exception:
                pass
            try:
                self.serial.stop()
            except Exception:
                pass
            try:
                self.destroy()
            except Exception:
                pass
            sys.exit(0)
        self.after(0, _cleanup)

if __name__ == "__main__":
    lock_sock, lock_mutex = ensure_single_instance()
    app = PeciDeckApp(instance_socket=lock_sock, instance_mutex=lock_mutex)
    app.mainloop()
