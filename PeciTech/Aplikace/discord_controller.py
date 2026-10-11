import os
import subprocess
import threading
import time
import ctypes
from ctypes import wintypes
import keyboard

# Rychlá Win32 detekce běžícího procesu Discord.exe bez spouštění subprocess
kernel32 = ctypes.windll.kernel32
TH32CS_SNAPPROCESS = 0x00000002

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ('dwSize', wintypes.DWORD),
        ('cntUsage', wintypes.DWORD),
        ('th32ProcessID', wintypes.DWORD),
        ('th32DefaultHeapID', ctypes.c_size_t),
        ('th32ModuleID', wintypes.DWORD),
        ('cntThreads', wintypes.DWORD),
        ('th32ParentProcessID', wintypes.DWORD),
        ('pcPriClassBase', wintypes.LONG),
        ('dwFlags', wintypes.DWORD),
        ('szExeFile', ctypes.c_char * 260)
    ]

def check_process_running(exe_name="discord.exe"):
    """Bleskově zjistí, zda proces běží na Windows bez zatížení CPU."""
    try:
        hSnapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if hSnapshot == -1:
            return False
        entry = PROCESSENTRY32()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
        found = False
        target = exe_name.lower()
        if kernel32.Process32First(hSnapshot, ctypes.byref(entry)):
            while True:
                name = entry.szExeFile.decode('utf-8', errors='ignore').lower()
                if name == target:
                    found = True
                    break
                if not kernel32.Process32Next(hSnapshot, ctypes.byref(entry)):
                    break
        kernel32.CloseHandle(hSnapshot)
        return found
    except Exception:
        return False


# =============================================================================
#  WIN32 HARDWARE KEYBD_EVENT PRO LOW-LEVEL SPOLEHLIVÉ ZACHYCENÍ DISCORDEM NA POZADÍ
# =============================================================================
user32 = ctypes.windll.user32
KEYEVENTF_KEYUP = 0x0002

VK_MAP = {
    'ctrl': (0x11, 0x1D),
    'control': (0x11, 0x1D),
    'shift': (0x10, 0x2A),
    'alt': (0x12, 0x38),
    'm': (0x4D, 0x32),
    'd': (0x44, 0x20),
    'p': (0x50, 0x19),
    'h': (0x48, 0x23),
}
# Přidání funkčních kláves F1-F24 pro případ vlastních globálních Discord zkratek
for i in range(1, 13):
    VK_MAP[f'f{i}'] = (0x6F + i, 0x3A + i)
for i in range(13, 25):
    VK_MAP[f'f{i}'] = (0x7B + (i - 12), 0)

def get_key_vk_sc(k_name):
    k = k_name.lower().strip()
    if k in VK_MAP:
        return VK_MAP[k]
    if len(k) == 1:
        try:
            vk = user32.VkKeyScanW(ord(k)) & 0xFF
            sc = user32.MapVirtualKeyW(vk, 0)
            return (vk, sc)
        except Exception:
            pass
    return (0, 0)

def send_hardware_combo(combo_str):
    """Odešle hardware-level stisk a uvolnění kláves se scan-kódy pro spolehlivé zachycení globálním hookem Discordu i v hrách."""
    parts = [p.strip().lower() for p in str(combo_str).split('+') if p.strip()]
    keys_info = []
    for p in parts:
        vk, sc = get_key_vk_sc(p)
        if vk or sc:
            keys_info.append((vk, sc))
    if not keys_info:
        return False

    # Stisknout klávesy v pořadí (down)
    for vk, sc in keys_info:
        user32.keybd_event(vk, sc, 0, 0)
        time.sleep(0.01)

    time.sleep(0.05)

    # Uvolnit klávesy v obráceném pořadí (up)
    for vk, sc in reversed(keys_info):
        user32.keybd_event(vk, sc, KEYEVENTF_KEYUP, 0)
        time.sleep(0.01)

    return True


def find_discord_hwnd():
    """Najde okno Discordu (Chrome_WidgetWin_1 s názvem obsahujícím Discord) pro spolehlivé směrování zkratek na pozadí."""
    try:
        hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
        dhwnd = None
        def enum_wnd(hwnd, lp):
            nonlocal dhwnd
            cls_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buf, 256)
            if 'Chrome_WidgetWin_1' in cls_buf.value:
                length = user32.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                if 'discord' in buf.value.lower():
                    dhwnd = hwnd
                    return False
            return True
        WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        if hdesk:
            user32.EnumDesktopWindows(hdesk, WNDPROC(enum_wnd), 0)
        return dhwnd
    except Exception:
        return None


class DiscordController:
    """
    Správce integrace s Discordem (Discord Plugin pro PeciDeck MK.1).
    Umožňuje:
    - Rychlé ztlumení / odtlumení mikrofonu (Toggle Mute)
    - Ztlumení / odtlumení sluchátek (Toggle Deafen)
    - Push-to-Talk (stisk pro mluvení)
    - Odpojení z probíhajícího hlasového hovoru
    - Přímé spuštění / přepnutí do okna Discordu
    - Detekci stavu aplikace Discord
    """
    def __init__(self, config_manager=None, on_status_change_cb=None):
        self.config_mgr = config_manager
        self.on_status_change_cb = on_status_change_cb

        self.is_muted = False
        self.is_deafened = False
        self._last_process_check = 0
        self._cached_running = False

    def is_running(self):
        """Vrátí True, pokud je proces Discord.exe aktivní (s lehkým 2s cache)."""
        now = time.time()
        if now - self._last_process_check > 2.0:
            self._cached_running = check_process_running("discord.exe")
            self._last_process_check = now
        return self._cached_running

    def _get_key(self, action_key, default_key):
        if self.config_mgr and hasattr(self.config_mgr, "settings"):
            cfg = self.config_mgr.settings.get("discord", {})
            return cfg.get(action_key, default_key)
        return default_key

    def _toggle_system_mic(self):
        """Přepne hardwarové ztlumení výchozího mikrofonu ve Windows (funguje 100% na pozadí ve všech hrách)."""
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            mic = AudioUtilities.GetMicrophone()
            if mic:
                endpoint = mic.Activate(IAudioEndpointVolume._iid_, 7, None)
                vol = endpoint.QueryInterface(IAudioEndpointVolume)
                current = vol.GetMute()
                vol.SetMute(0 if current else 1, None)
                return True
        except Exception as e:
            print(f"[DiscordController] Systémový mic mute chyba: {e}")
        return False

    def toggle_system_mic(self):
        """Přepne hardwarové ztlumení výchozího mikrofonu ve Windows (pro samostatnou systémovou akci)."""
        return self._toggle_system_mic()

    def _send_key_combo(self, key):
        """Spolehlivé odeslání klávesové zkratky pro zachycení Discordem i v prohlížeči a na pozadí."""
        dhwnd = find_discord_hwnd()
        cur_fg = user32.GetForegroundWindow()

        # 1. Pokud je okno Discordu již v popředí, odešleme hardwarové stisky přímo
        if cur_fg and dhwnd and cur_fg == dhwnd:
            send_hardware_combo(key)
            return True

        # 2. Odešleme systémové hardwarové scan-kódy (pro případ, že má uživatel v Discordu přidaný globální keybind)
        send_hardware_combo(key)

        # 3. Asistence pro pozadí (prohlížeč, hra, DaVinci):
        # Pokud uživatel nemá v nastavení Discordu ručně zadanou globální zkratku,
        # Discord na pozadí klávesy ignoruje. Na 20 ms odemkneme a aktivujeme okno Discordu,
        # odešleme zkratku a okamžitě vrátíme zaměření zpět do původní aplikace (prohlížeče).
        if dhwnd:
            try:
                # Odemknutí zámku přepnutí oken ve Windows (Alt tap trik)
                user32.keybd_event(0x12, 0, 0, 0)
                user32.keybd_event(0x12, 0, KEYEVENTF_KEYUP, 0)
                user32.SetForegroundWindow(dhwnd)
                time.sleep(0.015)
                send_hardware_combo(key)
                time.sleep(0.015)
            except Exception as e:
                print(f"[Discord] Asistence na pozadí chyba: {e}")
            finally:
                if cur_fg and cur_fg != dhwnd:
                    try:
                        user32.keybd_event(0x12, 0, 0, 0)
                        user32.keybd_event(0x12, 0, KEYEVENTF_KEYUP, 0)
                        user32.SetForegroundWindow(cur_fg)
                    except Exception:
                        pass
            return True

        # Fallback přes knihovnu keyboard
        try:
            keyboard.press(key)
            time.sleep(0.04)
            keyboard.release(key)
            return True
        except Exception:
            try:
                keyboard.send(key)
                return True
            except Exception as e:
                print(f"[Discord] Chyba při odeslání zkratky {key}: {e}")
                return False

    def toggle_mute(self):
        """
        Přepne stav ztlumení mikrofonu v Discordu odesláním globální zkratky.
        (Nezasahuje do výchozího Windows mikrofonu, takže neovlivní DaVinci Resolve ani jiné aplikace).
        """
        key = self._get_key("mute_key", "ctrl+shift+m")
        self._send_key_combo(key)
        self.is_muted = not self.is_muted
        return True

    def toggle_deafen(self):
        """Přepne stav ztlumení sluchátek / zvuku v Discordu."""
        key = self._get_key("deafen_key", "ctrl+shift+d")
        self._send_key_combo(key)
        self.is_deafened = not self.is_deafened
        return True

    def push_to_talk(self):
        """Aktivuje Push-to-Talk klávesu v Discordu."""
        key = self._get_key("ptt_key", "ctrl+shift+p")
        self._send_key_combo(key)
        return True

    def disconnect_call(self):
        """Odpojí probíhající hovor v Discordu."""
        key = self._get_key("disconnect_key", "ctrl+shift+h")
        self._send_key_combo(key)
        return True

    def open_discord(self):
        """Otevře Discord nebo přenese jeho okno do popředí."""
        try:
            # Protokol discord:// okamžitě probudí klientskou aplikaci
            subprocess.Popen(["cmd", "/c", "start", "discord://"], shell=True)
            return True
        except Exception:
            localapp = os.environ.get("LOCALAPPDATA", "")
            updater = os.path.join(localapp, "Discord", "Update.exe")
            if os.path.exists(updater):
                subprocess.Popen([updater, "--processStart", "Discord.exe"])
                return True
            return False

    def execute_action(self, param):
        """Vykoná požadovanou akci Discordu na základě parametru tlačítka."""
        p = str(param or "").lower().strip()
        if p in ("mute", "toggle_mute"):
            return self.toggle_mute()
        elif p in ("deafen", "toggle_deafen"):
            return self.toggle_deafen()
        elif p in ("ptt", "push_to_talk"):
            return self.push_to_talk()
        elif p in ("disconnect", "leave_call"):
            return self.disconnect_call()
        elif p in ("open", "launch", "focus"):
            return self.open_discord()
        else:
            # Fallback - přímá zkratka nebo otevření
            return self.toggle_mute()
