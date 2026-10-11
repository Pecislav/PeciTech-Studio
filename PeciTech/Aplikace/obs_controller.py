import os
import json
import time
import threading
import subprocess
import obsws_python as obs

class OBSController:
    """
    Pokročilý správce komunikace s OBS Studio přes OBS WebSocket v5:
    - Automatická detekce portu a hesla přímo z konfigurace OBS Studio
    - Automatické povolení WebSocket serveru v OBS, pokud je vypnutý
    - Asynchronní připojení a bezpečný auto-reconnect na pozadí (žádné zamrzání UI)
    - Kompletní podpora: Stream, Záznam, Pauza záznamu, Scény (další/předchozí/výběr),
      Ztlumení zvuku, Regulace hlasitosti (pro enkodéry), Virtuální kamera, Replay buffer.
    """
    def __init__(self, host="localhost", port=4455, password="", auto_connect=True, on_status_change_cb=None):
        self.host = host
        self.port = int(port)
        self.password = password
        self.auto_connect = auto_connect
        self.on_status_change_cb = on_status_change_cb

        self.client = None
        self.is_connected = False
        self._lock = threading.Lock()

        # Poslední známý stav
        self.last_scenes = []
        self.last_audio_inputs = []

        # Správa auto-reconnect smyčky
        self._reconnect_running = False
        self._reconnect_thread = None

        # Omezení frekvence pokusů o připojení (pro plynulost bez zamrzání při vypnutém OBS)
        self._last_connect_attempt = 0.0
        self._connect_cooldown = 4.0

        # Pokud není zadáno heslo nebo port, zkusíme automaticky načíst z OBS
        if not self.password or self.port == 4455:
            self._try_load_local_obs_config()

    # =========================================================================
    #  AUTODETEKCE A SYSTÉMOVÁ KONFIGURACE OBS
    # =========================================================================
    @staticmethod
    def get_obs_config_path():
        """Vrátí absolutní cestu k souboru config.json pluginu obs-websocket."""
        appdata = os.environ.get("APPDATA", "")
        if not appdata:
            return None
        cfg_path = os.path.join(appdata, "obs-studio", "plugin_config", "obs-websocket", "config.json")
        return cfg_path if os.path.exists(cfg_path) else None

    @classmethod
    def detect_obs_config(cls):
        """
        Přečte nastavení WebSocketu přímo z OBS konfigurace v %APPDATA%.
        Vrací slovník s informacemi nebo None.
        """
        cfg_path = cls.get_obs_config_path()
        if not cfg_path:
            # Zkusíme také vytvořit výchozí cestu pro případ, že složka existuje
            appdata = os.environ.get("APPDATA", "")
            cfg_path = os.path.join(appdata, "obs-studio", "plugin_config", "obs-websocket", "config.json")
            if not os.path.exists(cfg_path):
                return None

        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            server_enabled = data.get("server_enabled", False)
            auth_required = data.get("auth_required", True)
            pwd = data.get("server_password", "") if auth_required else ""
            port = data.get("server_port", 4455)

            return {
                "found": True,
                "host": "localhost",
                "port": int(port),
                "password": pwd,
                "auth_required": auth_required,
                "server_enabled": server_enabled,
                "path": cfg_path
            }
        except Exception as e:
            print(f"[OBS] Nelze načíst konfiguraci OBS: {e}")
            return None

    @classmethod
    def ensure_obs_websocket_enabled(cls):
        """
        Zajistí, že server_enabled v konfiguraci OBS je nastaven na True.
        """
        cfg_path = cls.get_obs_config_path()
        if not cfg_path:
            return False
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not data.get("server_enabled", False):
                data["server_enabled"] = True
                with open(cfg_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print("[OBS] WebSocket server byl v konfiguraci OBS automaticky povolen.")
            return True
        except Exception as e:
            print(f"[OBS] Chyba při úpravě konfigurace OBS: {e}")
            return False

    def _try_load_local_obs_config(self):
        detected = self.detect_obs_config()
        if detected:
            if not self.password and detected.get("password"):
                self.password = detected["password"]
            if detected.get("port"):
                self.port = detected["port"]
            # Zkontrolujeme a povolíme WebSocket server
            self.ensure_obs_websocket_enabled()

    @staticmethod
    def is_obs_running():
        """Zkontroluje, zda běží proces OBS Studio."""
        try:
            import psutil
            for p in psutil.process_iter(['name']):
                if "obs64.exe" in (p.info.get("name") or "").lower() or "obs32.exe" in (p.info.get("name") or "").lower():
                    return True
        except Exception:
            pass
        return False

    @staticmethod
    def launch_obs():
        """Pokusí se spustit OBS Studio z obvyklých umístění."""
        paths = [
            r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
            r"C:\Program Files (x86)\obs-studio\bin\32bit\obs32.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\obs-studio\bin\64bit\obs64.exe")
        ]
        for p in paths:
            if os.path.exists(p):
                workdir = os.path.dirname(p)
                try:
                    subprocess.Popen([p], cwd=workdir, shell=False)
                    return True
                except Exception as e:
                    print(f"[OBS] Nelze spustit OBS ze souboru {p}: {e}")
        return False

    # =========================================================================
    #  PŘIPOJENÍ A AUTO-RECONNECT
    # =========================================================================
    def connect(self, silent=False, force=False):
        """
        Pokusí se synchronně připojit k OBS WebSocket serveru.
        """
        now = time.time()
        if not force and not self.is_connected and (now - self._last_connect_attempt < self._connect_cooldown):
            return False

        with self._lock:
            if not force and not self.is_connected and (time.time() - self._last_connect_attempt < self._connect_cooldown):
                return False
            self._last_connect_attempt = time.time()

            # Ujistíme se, že WebSocket server je v OBS configu aktivní
            self.ensure_obs_websocket_enabled()

            try:
                self.client = obs.ReqClient(
                    host=self.host,
                    port=self.port,
                    password=self.password,
                    timeout=1.5
                )
                self.is_connected = True
                if not silent:
                    print(f"[OBS] Úspěšně připojeno k OBS ({self.host}:{self.port})")
                self._notify_status(True)
                # Načteme scény a zdroje do mezipaměti
                self._refresh_cache_safe()
                return True
            except Exception as e:
                self.client = None
                self.is_connected = False
                if not silent:
                    print(f"[OBS] Nelze se připojit k OBS: {e}")
                self._notify_status(False)
                return False

    def connect_async(self, on_done_cb=None):
        """Asynchronní připojení ve vedlejším vlákně (nezablokuje GUI)."""
        def _worker():
            ok = self.connect(silent=False)
            if on_done_cb:
                on_done_cb(ok)
        threading.Thread(target=_worker, daemon=True).start()

    def disconnect(self):
        """Čisté odpojení od OBS."""
        with self._lock:
            if self.client:
                try:
                    self.client.disconnect()
                except Exception:
                    pass
            self.client = None
            was_connected = self.is_connected
            self.is_connected = False
            if was_connected:
                print("[OBS] Spojení s OBS ukončeno.")
                self._notify_status(False)

    def _notify_status(self, connected):
        if self.on_status_change_cb:
            try:
                self.on_status_change_cb(connected)
            except Exception as e:
                print(f"[OBS] Chyba v status callbacku: {e}")

    def start_auto_reconnect(self):
        """Spustí vlákno, které na pozadí automaticky obnovuje spojení s OBS."""
        if self._reconnect_running:
            return
        self._reconnect_running = True
        self._reconnect_thread = threading.Thread(target=self._auto_reconnect_loop, daemon=True)
        self._reconnect_thread.start()

    def stop_auto_reconnect(self):
        """Zastaví vlákno automatického obnovení spojení."""
        self._reconnect_running = False

    def _auto_reconnect_loop(self):
        while self._reconnect_running:
            if not self.is_connected:
                # Pokud je povoleno auto_connect, zkusíme se tiše připojit
                if self.auto_connect:
                    self.connect(silent=True)
                time.sleep(3.0)
            else:
                # Jsme připojeni - ověřujeme spojení lehkým dotazem
                time.sleep(3.0)
                try:
                    with self._lock:
                        if self.client:
                            self.client.get_version()
                except Exception:
                    print("[OBS] Detekována ztráta spojení s OBS.")
                    self.disconnect()

    def _refresh_cache_safe(self):
        try:
            self.get_scenes()
            self.get_audio_inputs()
        except Exception:
            pass

    # =========================================================================
    #  STREAM & ZÁZNAM & VIRTUÁLNÍ KAMERA & REPLAY
    # =========================================================================
    def toggle_stream(self):
        """Spustí nebo zastaví stream."""
        if not self._check_connection():
            return False
        try:
            res = self.client.toggle_stream()
            return getattr(res, "output_active", True)
        except Exception as e:
            print(f"[OBS] Chyba toggle_stream: {e}")
            return False

    def start_stream(self):
        if not self._check_connection(): return False
        try:
            self.client.start_stream()
            return True
        except Exception as e:
            print(f"[OBS] Chyba start_stream: {e}")
            return False

    def stop_stream(self):
        if not self._check_connection(): return False
        try:
            self.client.stop_stream()
            return True
        except Exception as e:
            print(f"[OBS] Chyba stop_stream: {e}")
            return False

    def get_stream_status(self):
        if not self._check_connection(): return False
        try:
            res = self.client.get_stream_status()
            return getattr(res, "output_active", False)
        except Exception:
            return False

    def toggle_record(self):
        """Spustí nebo zastaví nahrávání."""
        if not self._check_connection():
            return False
        try:
            res = self.client.toggle_record()
            return getattr(res, "output_active", True)
        except Exception as e:
            print(f"[OBS] Chyba toggle_record: {e}")
            return False

    def start_record(self):
        if not self._check_connection(): return False
        try:
            self.client.start_record()
            return True
        except Exception as e:
            print(f"[OBS] Chyba start_record: {e}")
            return False

    def stop_record(self):
        if not self._check_connection(): return False
        try:
            self.client.stop_record()
            return True
        except Exception as e:
            print(f"[OBS] Chyba stop_record: {e}")
            return False

    def toggle_record_pause(self):
        """Pozastaví nebo obnoví nahrávání."""
        if not self._check_connection():
            return False
        try:
            res = self.client.toggle_record_pause()
            return getattr(res, "output_paused", False)
        except Exception as e:
            print(f"[OBS] Chyba toggle_record_pause: {e}")
            return False

    def get_record_status(self):
        if not self._check_connection(): return False
        try:
            res = self.client.get_record_status()
            return {
                "active": getattr(res, "output_active", False),
                "paused": getattr(res, "output_paused", False)
            }
        except Exception:
            return {"active": False, "paused": False}

    def toggle_virtual_cam(self):
        """Zapne nebo vypne virtuální kameru."""
        if not self._check_connection():
            return False
        try:
            res = self.client.toggle_virtual_cam()
            return getattr(res, "output_active", False)
        except Exception as e:
            print(f"[OBS] Chyba toggle_virtual_cam: {e}")
            return False

    def save_replay_buffer(self):
        """Uloží záznam z Replay bufferu (klip)."""
        if not self._check_connection():
            return False
        try:
            self.client.save_replay_buffer()
            return True
        except Exception as e:
            print(f"[OBS] Chyba save_replay_buffer: {e}")
            return False

    def toggle_replay_buffer(self):
        if not self._check_connection(): return False
        try:
            res = self.client.toggle_replay_buffer()
            return getattr(res, "output_active", False)
        except Exception as e:
            print(f"[OBS] Chyba toggle_replay_buffer: {e}")
            return False

    def toggle_studio_mode(self):
        """Přepne režim Studio v OBS."""
        if not self._check_connection():
            return False
        try:
            cur = self.client.get_studio_mode_enabled()
            is_enabled = getattr(cur, "studio_mode_enabled", False)
            self.client.set_studio_mode_enabled(not is_enabled)
            return not is_enabled
        except Exception as e:
            print(f"[OBS] Chyba toggle_studio_mode: {e}")
            return False

    # =========================================================================
    #  SPRÁVA SCÉN
    # =========================================================================
    def get_scenes(self):
        """Vrátí seznam názvů všech scén v OBS jako list[str]."""
        if not self._check_connection():
            return self.last_scenes
        try:
            res = self.client.get_scene_list()
            scenes = []
            for s in getattr(res, "scenes", []):
                if isinstance(s, dict):
                    name = s.get("sceneName") or s.get("scene_name")
                else:
                    name = getattr(s, "scene_name", None) or getattr(s, "sceneName", None) or str(s)
                if name:
                    scenes.append(name)
            if scenes:
                self.last_scenes = scenes
            return scenes
        except Exception as e:
            print(f"[OBS] Chyba get_scenes: {e}")
            return self.last_scenes

    def get_current_scene(self):
        """Vrátí název aktuální programové scény."""
        if not self._check_connection():
            return ""
        try:
            res = self.client.get_current_program_scene()
            name = getattr(res, "current_program_scene_name", None) or getattr(res, "scene_name", None)
            return name or ""
        except Exception:
            return ""

    def set_current_program_scene(self, scene_name):
        """Přepne OBS na konkrétní scénu."""
        if not self._check_connection() or not scene_name:
            return False
        try:
            self.client.set_current_program_scene(scene_name)
            return True
        except Exception as e:
            print(f"[OBS] Chyba přepnutí scény na '{scene_name}': {e}")
            return False

    def next_scene(self):
        """Cyklicky přepne na další scénu v pořadí."""
        if not self._check_connection():
            return False
        try:
            scenes = self.get_scenes()
            if not scenes:
                return False
            curr = self.get_current_scene()
            if curr in scenes:
                idx = (scenes.index(curr) + 1) % len(scenes)
            else:
                idx = 0
            target = scenes[idx]
            self.client.set_current_program_scene(target)
            return target
        except Exception as e:
            print(f"[OBS] Chyba next_scene: {e}")
            return False

    def prev_scene(self):
        """Cyklicky přepne na předchozí scénu v pořadí."""
        if not self._check_connection():
            return False
        try:
            scenes = self.get_scenes()
            if not scenes:
                return False
            curr = self.get_current_scene()
            if curr in scenes:
                idx = (scenes.index(curr) - 1) % len(scenes)
            else:
                idx = len(scenes) - 1
            target = scenes[idx]
            self.client.set_current_program_scene(target)
            return target
        except Exception as e:
            print(f"[OBS] Chyba prev_scene: {e}")
            return False

    # =========================================================================
    #  SPRÁVA ZVUKU & HLASITOSTI
    # =========================================================================
    def get_audio_inputs(self):
        """Vrátí seznam názvů všech audio vstupů/stop v OBS."""
        if not self._check_connection():
            return self.last_audio_inputs
        try:
            inputs = []
            res = self.client.get_input_list()
            for inp in getattr(res, "inputs", []):
                if isinstance(inp, dict):
                    name = inp.get("inputName") or inp.get("input_name")
                else:
                    name = getattr(inp, "input_name", None) or getattr(inp, "inputName", None) or str(inp)
                if name:
                    inputs.append(name)

            # Přidáme i speciální systémové vstupy (Desktop Audio, Mic)
            try:
                spec = self.client.get_special_inputs()
                for attr in ("desktop1", "desktop2", "mic1", "mic2", "mic3", "mic4"):
                    val = getattr(spec, attr, None)
                    if val and val not in inputs:
                        inputs.append(val)
            except Exception:
                pass

            if inputs:
                self.last_audio_inputs = inputs
            return inputs
        except Exception as e:
            print(f"[OBS] Chyba get_audio_inputs: {e}")
            return self.last_audio_inputs

    def toggle_input_mute(self, input_name):
        """Přepne stav ztlumení (Mute) daného vstupu."""
        if not self._check_connection() or not input_name:
            return False
        try:
            res = self.client.toggle_input_mute(input_name)
            return getattr(res, "input_muted", False)
        except Exception as e:
            print(f"[OBS] Chyba toggle_input_mute ({input_name}): {e}")
            return False

    def get_input_mute(self, input_name):
        """Vrátí True pokud je vstup ztlumen, jinak False."""
        if not self._check_connection() or not input_name:
            return False
        try:
            res = self.client.get_input_mute(input_name)
            return getattr(res, "input_muted", False)
        except Exception:
            return False

    def set_input_mute(self, input_name, muted):
        if not self._check_connection() or not input_name:
            return False
        try:
            self.client.set_input_mute(input_name, muted)
            return True
        except Exception as e:
            print(f"[OBS] Chyba set_input_mute ({input_name}): {e}")
            return False

    def change_input_volume(self, input_name, db_delta=2.0):
        """Změní hlasitost vstupu o db_delta dB (pro rotační enkodéry)."""
        if not self._check_connection() or not input_name:
            return False
        try:
            res = self.client.get_input_volume(input_name)
            curr_db = getattr(res, "input_volume_db", 0.0)
            new_db = max(-100.0, min(0.0, curr_db + db_delta))
            self.client.set_input_volume(input_name, vol_db=new_db)
            return True
        except Exception as e:
            print(f"[OBS] Chyba change_input_volume ({input_name}): {e}")
            return False

    def get_input_volume(self, input_name):
        if not self._check_connection() or not input_name:
            return None
        try:
            res = self.client.get_input_volume(input_name)
            return {
                "db": getattr(res, "input_volume_db", 0.0),
                "mul": getattr(res, "input_volume_mul", 1.0)
            }
        except Exception:
            return None

    # =========================================================================
    #  POMOCNÉ
    # =========================================================================
    def _check_connection(self):
        if not self.is_connected or not self.client:
            # Rychlý pokus o připojení pokud není aktivní
            if self.auto_connect:
                return self.connect(silent=True)
            return False
        return True
