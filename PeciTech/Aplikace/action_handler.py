import os
import ctypes
import webbrowser
import subprocess
import keyboard

import time
import threading

# Windows Virtual-Key kódy pro multimediální klávesy (rychlé a bez závislostí)
VK_VOLUME_MUTE       = 0xAD
VK_VOLUME_DOWN       = 0xAE
VK_VOLUME_UP         = 0xAF
VK_MEDIA_NEXT_TRACK  = 0xB0
VK_MEDIA_PREV_TRACK  = 0xB1
VK_MEDIA_STOP        = 0xB2
VK_MEDIA_PLAY_PAUSE  = 0xB3

def _send_vk(vk_code):
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    time.sleep(0.015)
    ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0) # KEYEVENTF_KEYUP = 2

# Převodní tabulka z českých znaků (česká klávesnice v OS) na univerzální standardní klávesy
CZECH_CHAR_TO_STANDARD = {
    "+": "1",
    "ě": "2",
    "š": "3",
    "č": "4",
    "ř": "5",
    "ž": "6",
    "ý": "7",
    "á": "8",
    "í": "9",
    "é": "0",
    "ů": ";",
    "ú": "[",
    "§": "'",
    "´": "=",
    "¨": "\\",
}

def normalize_hotkey(hotkey):
    """
    Normalizuje klávesovou zkratku na univerzální standardní formát:
    - Převede české znaky (ě -> 2, + -> 1, š -> 3...) na fyzická čísla a znaky
    - Ošetří zdvojená pluska (např. 'alt++' -> 'alt+1')
    - Převede na malá písmena a odstraní nežádoucí mezery
    """
    if not hotkey:
        return ""
    s = str(hotkey).strip().lower()
    if s.endswith("++") or s == "+":
        sub = s.rstrip("+")
        mods = [t.strip() for t in sub.split("+") if t.strip()]
        parts = mods + ["1"]
    else:
        parts = []
        for t in s.split("+"):
            t = t.strip()
            if not t:
                continue
            parts.append(CZECH_CHAR_TO_STANDARD.get(t, t))
    return "+".join(parts)

try:
    # Nastavíme standardní US layout (00000409) pro proces, aby mapovací tabulky
    # knihovny keyboard (Virtual-Key i scan-kódy) odpovídaly standardní fyzické klávesnici (1-0, Y/Z)
    user32 = ctypes.windll.user32
    hkl_us = user32.LoadKeyboardLayoutW("00000409", 1)
    if hkl_us:
        user32.ActivateKeyboardLayout(hkl_us, 0x00000100) # KLF_SETFORPROCESS

    if hasattr(keyboard, "_os_keyboard") and hasattr(keyboard._os_keyboard, "init"):
        with keyboard._os_keyboard.tables_lock:
            keyboard._os_keyboard.to_name.clear()
            keyboard._os_keyboard.from_name.clear()
            keyboard._os_keyboard.scan_code_to_vk.clear()
        keyboard._os_keyboard.init()
except Exception as e:
    print(f"[ActionHandler] Varování při inicializaci US layoutu: {e}")

def send_reliable_hotkey(hotkey, hold_sec=0.045):
    """
    Odešle klávesovou zkratku s hardwarovými scan-kódy a garantovanou dobou držení (hold time).
    Funguje 100% spolehlivě i když aplikace PeciTech není rozkliknutá (běží na pozadí / v liště),
    i pro aplikace naslouchající na pozadí (OBS Studio, Discord, DaVinci Resolve) a DirectX hry.
    """
    if not hotkey:
        return
    hotkey_str = normalize_hotkey(hotkey)
    if not hotkey_str:
        return

    try:
        if hasattr(keyboard, "_os_keyboard") and hasattr(keyboard._os_keyboard, "init"):
            if not getattr(keyboard._os_keyboard, "scan_code_to_vk", None):
                keyboard._os_keyboard.init()

        steps = keyboard.parse_hotkey(hotkey_str)
        for step in steps:
            # 1. Postupné stisknutí modifikátorů a klávesy v pořadí
            for scan_codes in step:
                if scan_codes:
                    keyboard._os_keyboard.press(scan_codes[0])
                    time.sleep(0.012)
            # 2. Garantovaná doba držení kláves pro spolehlivou detekci ve Windows/hrách/OBS
            time.sleep(hold_sec)
            # 3. Uvolnění v přesně opačném pořadí
            for scan_codes in reversed(step):
                if scan_codes:
                    keyboard._os_keyboard.release(scan_codes[0])
                    time.sleep(0.012)
    except Exception as e:
        print(f"[ActionHandler] Fallback send pro {hotkey_str}: {e}")
        try:
            keyboard.send(hotkey_str)
        except Exception:
            pass

class ActionHandler:
    def __init__(self, obs_controller=None, serial_bridge=None, config_manager=None, on_page_change_cb=None, discord_controller=None, twitch_controller=None):
        self.obs = obs_controller
        self.serial = serial_bridge
        self.config_mgr = config_manager
        self.on_page_change_cb = on_page_change_cb
        self.discord = discord_controller
        self.twitch = twitch_controller
        self.current_brightness = 255

    def execute(self, action_dict):
        if not action_dict or not isinstance(action_dict, dict):
            return

        atype = action_dict.get("action_type", "none")
        aparam = action_dict.get("action_param", "")

        try:
            if atype == "volume":
                self._handle_volume(aparam)
            elif atype == "media":
                self._handle_media(aparam)
            elif atype == "hotkey":
                self._handle_hotkey(aparam)
            elif atype == "app":
                self._handle_app(aparam)
            elif atype == "url":
                self._handle_url(aparam)
            elif atype == "discord":
                self._handle_discord(aparam)
            elif atype == "twitch":
                self._handle_twitch(aparam)
            elif atype == "obs":
                self._handle_obs(aparam)
            elif atype == "brightness":
                self._handle_brightness(aparam)
            elif atype == "multi":
                self._handle_multi(action_dict)
            elif atype == "delay":
                self._handle_delay(aparam)
            elif atype == "page":
                self._handle_page(aparam)
            elif atype == "profile":
                self._handle_profile(aparam)
            elif atype == "system_mic":
                self._handle_system_mic(aparam)
            elif atype == "none":
                pass
        except Exception as e:
            print(f"[ActionHandler] Chyba při spuštění akce {atype} ({aparam}): {e}")

    def _handle_multi(self, action_dict):
        """Spustí sekvenci naskládaných akcí (Multi-Action / Řetězec akcí)."""
        actions = action_dict.get("actions", [])
        if not actions or not isinstance(actions, list):
            return

        def _run_sequence():
            for sub_act in actions:
                if not sub_act or not isinstance(sub_act, dict):
                    continue
                stype = sub_act.get("action_type", "")
                sparam = sub_act.get("action_param", "")
                if stype == "delay":
                    try:
                        ms = float(sparam)
                        time.sleep(ms / 1000.0)
                    except Exception:
                        time.sleep(0.1)
                else:
                    self.execute(sub_act)
                    time.sleep(0.04)

        t = threading.Thread(target=_run_sequence, daemon=True)
        t.start()

    def _handle_delay(self, param):
        """Samostatná pauza."""
        try:
            ms = float(param)
            time.sleep(ms / 1000.0)
        except Exception:
            time.sleep(0.2)

    def _handle_page(self, param):
        """Změna stránky nebo vstup do složky."""
        if self.on_page_change_cb:
            self.on_page_change_cb(param)

    def _handle_profile(self, param):
        """Změna aktivního profilu (Multitasking)."""
        if self.config_mgr:
            self.config_mgr.switch_profile(param)
            if self.on_page_change_cb:
                self.on_page_change_cb("profile_switch")

    def _handle_system_mic(self, param):
        """Ztlumí/odtlumí hardwarový mikrofon ve Windows."""
        if self.discord:
            self.discord.toggle_system_mic()

    def _handle_volume(self, param):
        if param == "up":
            _send_vk(VK_VOLUME_UP)
        elif param == "down":
            _send_vk(VK_VOLUME_DOWN)
        elif param == "mute":
            _send_vk(VK_VOLUME_MUTE)

    def _handle_media(self, param):
        if param == "play_pause":
            _send_vk(VK_MEDIA_PLAY_PAUSE)
        elif param == "next":
            _send_vk(VK_MEDIA_NEXT_TRACK)
        elif param == "prev":
            _send_vk(VK_MEDIA_PREV_TRACK)
        elif param == "stop":
            _send_vk(VK_MEDIA_STOP)

    def _handle_hotkey(self, param):
        if not param:
            return
        send_reliable_hotkey(param)

    def _handle_app(self, param):
        if not param:
            return
        p = str(param).strip()
        if os.path.exists(p):
            try:
                os.startfile(p)
                return
            except Exception as e:
                print(f"[ActionHandler] Chyba os.startfile({p}): {e}")

        # Zvláštní známé aplikace a zkratky
        low = p.lower()
        if low == "calc":
            subprocess.Popen("calc.exe", shell=True)
        elif low == "explorer":
            subprocess.Popen("explorer.exe", shell=True)
        elif low == "notepad":
            subprocess.Popen("notepad.exe", shell=True)
        elif low == "taskmgr":
            subprocess.Popen("taskmgr.exe", shell=True)
        elif low in ("cmd", "terminal"):
            subprocess.Popen("cmd.exe", shell=True)
        elif low == "powershell":
            subprocess.Popen("powershell.exe", shell=True)
        elif low == "mspaint":
            subprocess.Popen("mspaint.exe", shell=True)
        elif low == "settings":
            subprocess.Popen(["cmd", "/c", "start", "ms-settings:"], shell=True)
        elif low == "chrome":
            subprocess.Popen(["cmd", "/c", "start", "chrome"], shell=True)
        elif low in ("edge", "msedge"):
            subprocess.Popen(["cmd", "/c", "start", "msedge"], shell=True)
        elif low in ("browser", "web"):
            webbrowser.open("https://google.com")
        elif low == "spotify":
            try:
                subprocess.Popen(["cmd", "/c", "start", "spotify:"], shell=True)
            except Exception:
                subprocess.Popen(["cmd", "/c", "start", "spotify"], shell=True)
        elif low == "discord":
            try:
                subprocess.Popen(["cmd", "/c", "start", "discord://"], shell=True)
            except Exception:
                pass
        elif low == "steam":
            subprocess.Popen(["cmd", "/c", "start", "steam://"], shell=True)
        elif low == "obs":
            obs_paths = [
                r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
                r"C:\Program Files (x86)\obs-studio\bin\64bit\obs64.exe"
            ]
            found = False
            for op in obs_paths:
                if os.path.exists(op):
                    subprocess.Popen(op, cwd=os.path.dirname(op))
                    found = True
                    break
            if not found:
                subprocess.Popen(["cmd", "/c", "start", "obs64.exe"], shell=True)
        elif low in ("davinci", "resolve"):
            dv_path = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe"
            if os.path.exists(dv_path):
                subprocess.Popen(dv_path, cwd=os.path.dirname(dv_path))
            else:
                subprocess.Popen(["cmd", "/c", "start", "Resolve.exe"], shell=True)
        elif low in ("epic", "epicgames"):
            ep_path = r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe"
            if os.path.exists(ep_path):
                subprocess.Popen(ep_path, cwd=os.path.dirname(ep_path))
            else:
                try:
                    subprocess.Popen(["cmd", "/c", "start", "com.epicgames.launcher://"], shell=True)
                except Exception:
                    subprocess.Popen(["cmd", "/c", "start", "EpicGamesLauncher.exe"], shell=True)
        elif low == "code":
            subprocess.Popen(["cmd", "/c", "code"], shell=True)
        else:
            try:
                subprocess.Popen(["cmd", "/c", "start", "", p], shell=True)
            except Exception:
                subprocess.Popen(p, shell=True)

    def _handle_url(self, param):
        if not param:
            return
        url = param
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
        webbrowser.open(url)

    def _handle_discord(self, param):
        if self.discord:
            self.discord.execute_action(param)
        else:
            cfg = self.config_mgr.settings.get("discord", {}) if self.config_mgr else {}
            mute_key = cfg.get("mute_key", "ctrl+shift+m")
            deafen_key = cfg.get("deafen_key", "ctrl+shift+d")
            ptt_key = cfg.get("ptt_key", "ctrl+shift+p")
            disc_key = cfg.get("disconnect_key", "ctrl+shift+h")

            p = str(param or "").lower().strip()
            if p in ("mute", "toggle_mute"):
                send_reliable_hotkey(mute_key)
            elif p in ("deafen", "toggle_deafen"):
                send_reliable_hotkey(deafen_key)
            elif p in ("ptt", "push_to_talk"):
                send_reliable_hotkey(ptt_key)
            elif p in ("disconnect", "leave_call"):
                send_reliable_hotkey(disc_key)
            elif p in ("open", "launch", "focus"):
                try:
                    subprocess.Popen(["cmd", "/c", "start", "discord://"], shell=True)
                except Exception:
                    pass

    def _handle_twitch(self, param):
        if self.twitch:
            self.twitch.execute_action(param)
        else:
            print(f"[ActionHandler] TwitchController není inicializován pro akci {param}.")

    def _handle_obs(self, param):
        if not self.obs:
            return
        if not self.obs.is_connected:
            # Rychlý pokus o připojení bez blokování
            connected = self.obs.connect(silent=True)
            if not connected:
                print("[ActionHandler] OBS není připojeno.")
                return

        if not param:
            return

        if isinstance(param, str):
            p = param.strip()
            if p == "toggle_stream":
                self.obs.toggle_stream()
            elif p == "toggle_record":
                self.obs.toggle_record()
            elif p in ("toggle_record_pause", "pause_record"):
                self.obs.toggle_record_pause()
            elif p == "next_scene":
                self.obs.next_scene()
            elif p == "prev_scene":
                self.obs.prev_scene()
            elif p in ("toggle_virtual_cam", "virtual_cam"):
                self.obs.toggle_virtual_cam()
            elif p in ("save_replay_buffer", "replay_buffer"):
                self.obs.save_replay_buffer()
            elif p == "toggle_replay_buffer":
                self.obs.toggle_replay_buffer()
            elif p in ("toggle_studio_mode", "studio_mode"):
                self.obs.toggle_studio_mode()
            elif p.startswith("scene:"):
                scene_name = p[6:].strip()
                self.obs.set_current_program_scene(scene_name)
            elif p.startswith("mute:"):
                source_name = p[5:].strip()
                self.obs.toggle_input_mute(source_name)
            elif p.startswith("vol_up:"):
                source_name = p[7:].strip()
                self.obs.change_input_volume(source_name, +2.0)
            elif p.startswith("vol_down:"):
                source_name = p[9:].strip()
                self.obs.change_input_volume(source_name, -2.0)

        elif isinstance(param, dict):
            sub = param.get("sub", "")
            val = param.get("val", "")
            if sub == "scene":
                self.obs.set_current_program_scene(val)
            elif sub == "mute":
                self.obs.toggle_input_mute(val)
            elif sub == "vol_up":
                self.obs.change_input_volume(val, +2.0)
            elif sub == "vol_down":
                self.obs.change_input_volume(val, -2.0)
            elif sub == "stream":
                self.obs.toggle_stream()
            elif sub == "record":
                self.obs.toggle_record()
            elif sub == "pause":
                self.obs.toggle_record_pause()
            elif sub == "virtual_cam":
                self.obs.toggle_virtual_cam()
            elif sub == "replay":
                self.obs.save_replay_buffer()
            elif sub == "next_scene":
                self.obs.next_scene()
            elif sub == "prev_scene":
                self.obs.prev_scene()

    def _handle_brightness(self, param):
        step = 35
        if param == "up":
            self.current_brightness = min(255, self.current_brightness + step)
        elif param == "down":
            self.current_brightness = max(10, self.current_brightness - step)
        elif param == "toggle":
            self.current_brightness = 0 if self.current_brightness > 0 else 255

        if self.serial and self.serial.is_connected:
            self.serial.send_command(f"DISP:BL,{self.current_brightness}")
