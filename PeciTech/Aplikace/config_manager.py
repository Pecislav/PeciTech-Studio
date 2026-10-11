import os
import json
import copy

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "profiles", "default.json")
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_PROFILE = {
    "name": "Můj Profil",
    "brightness": 255,
    "buttons": [
        {"id": i, "label": "", "icon": "", "action_type": "none", "action_param": ""}
        for i in range(8)
    ],
    "encoders": [
        {
            "id": i,
            "name": f"Enkodér E{i+1}",
            "cw":  {"action_type": "none", "action_param": ""},
            "ccw": {"action_type": "none", "action_param": ""},
            "btn": {"action_type": "none", "action_param": ""}
        }
        for i in range(3)
    ]
}

DEFAULT_SETTINGS = {
    "theme": "dark",
    "accent_color": "#FF7A29",
    "minimize_to_tray": True,
    "start_with_windows": False,
    "last_com_port": "AUTO",
    "obs": {
        "host": "localhost",
        "port": 4455,
        "password": "",
        "auto_connect": True
    },
    "discord": {
        "mute_key": "ctrl+shift+m",
        "deafen_key": "ctrl+shift+d",
        "ptt_key": "ctrl+shift+p",
        "disconnect_key": "ctrl+shift+h"
    },
    "twitch": {
        "channel": "",
        "oauth_token": "",
        "client_id": "",
        "user_id": ""
    }
}

class ConfigManager:
    def __init__(self):
        self.settings = self.load_settings()
        self.active_profile_id = self.settings.get("active_profile", "default")
        self.profile = self.load_profile()

    @property
    def profiles_dir(self):
        d = os.path.join(os.path.dirname(__file__), "profiles")
        os.makedirs(d, exist_ok=True)
        return d

    def list_profiles(self):
        """Vrátí seznam všech profilů v adresáři profiles/."""
        profs = []
        d = self.profiles_dir
        for f in os.listdir(d):
            if f.endswith(".json"):
                pid = f[:-5]
                p_path = os.path.join(d, f)
                try:
                    with open(p_path, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                    name = data.get("name", pid)
                except Exception:
                    name = pid
                profs.append({"id": pid, "name": name, "file": f})
        if not profs:
            profs.append({"id": "default", "name": "Výchozí profil", "file": "default.json"})
        return profs

    def load_profile(self, profile_id=None, path=None):
        if not path:
            pid = profile_id or getattr(self, "active_profile_id", "default") or "default"
            path = os.path.join(self.profiles_dir, f"{pid}.json")
            self.active_profile_id = pid

        prof = None
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    prof = json.load(f)
            except Exception as e:
                print(f"[Config] Chyba načítání profilu {path}: {e}")
        if not prof or not isinstance(prof, dict):
            prof = json.loads(json.dumps(DEFAULT_PROFILE))

        # Zajištění kompatibility a inicializace stránek (Pages & Folders)
        if "pages" not in prof or not isinstance(prof.get("pages"), list) or len(prof["pages"]) == 0:
            existing_buttons = prof.get("buttons", [])
            if not existing_buttons:
                existing_buttons = [
                    {"id": i, "label": "", "icon": "", "action_type": "none", "action_param": ""}
                    for i in range(8)
                ]
            prof["pages"] = [
                {
                    "id": 0,
                    "name": "Hlavní stránka",
                    "buttons": existing_buttons
                }
            ]

        if "active_page" not in prof or not isinstance(prof.get("active_page"), int):
            prof["active_page"] = 0

        if prof["active_page"] >= len(prof["pages"]) or prof["active_page"] < 0:
            prof["active_page"] = 0

        # Propojení aktivních tlačítek s profilem (pro zpětnou kompatibilitu)
        current_page_buttons = prof["pages"][prof["active_page"]].get("buttons", [])
        while len(current_page_buttons) < 8:
            current_page_buttons.append({"id": len(current_page_buttons), "label": "", "icon": "", "action_type": "none", "action_param": ""})
        prof["buttons"] = current_page_buttons

        return prof

    def save_profile(self, path=None):
        if not path:
            pid = getattr(self, "active_profile_id", "default") or "default"
            path = os.path.join(self.profiles_dir, f"{pid}.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            # Ujistíme se, že změny v profile["buttons"] jsou uloženy v aktivní stránce
            if "pages" in self.profile and isinstance(self.profile["pages"], list):
                act_idx = self.profile.get("active_page", 0)
                if 0 <= act_idx < len(self.profile["pages"]):
                    self.profile["pages"][act_idx]["buttons"] = copy.deepcopy(self.profile.get("buttons", []))

            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.profile, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[Config] Chyba ukládání profilu {path}: {e}")
            return False

    def switch_profile(self, profile_id):
        """Uloží aktuální profil a přepne na zadaný profil."""
        self.save_profile()
        self.active_profile_id = profile_id
        self.settings["active_profile"] = profile_id
        self.save_settings()
        self.profile = self.load_profile(profile_id)
        return self.profile

    def create_profile(self, name="Nový Profil"):
        """Vytvoří nový prázdný profil a přepne na něj."""
        import re
        self.save_profile()
        clean_name = name.strip() or "Nový Profil"
        slug = re.sub(r'[^a-zA-Z0-9_-]', '_', clean_name.lower()).strip('_') or "profil"
        base_slug = slug
        idx = 1
        d = self.profiles_dir
        while os.path.exists(os.path.join(d, f"{slug}.json")):
            slug = f"{base_slug}_{idx}"
            idx += 1

        new_data = json.loads(json.dumps(DEFAULT_PROFILE))
        new_data["name"] = clean_name
        new_data["active_page"] = 0
        new_data["pages"] = [
            {
                "id": 0,
                "name": "Hlavní stránka",
                "buttons": [
                    {"id": i, "label": "", "icon": "", "action_type": "none", "action_param": ""}
                    for i in range(8)
                ]
            }
        ]
        new_data["buttons"] = copy.deepcopy(new_data["pages"][0]["buttons"])

        p_path = os.path.join(d, f"{slug}.json")
        try:
            with open(p_path, "w", encoding="utf-8") as fp:
                json.dump(new_data, fp, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[Config] Chyba vytvoření profilu {slug}: {e}")

        self.switch_profile(slug)
        return slug

    def rename_profile(self, profile_id, new_name):
        """Přejmenuje zadaný profil."""
        if not new_name.strip(): return False
        d = self.profiles_dir
        p_path = os.path.join(d, f"{profile_id}.json")
        if os.path.exists(p_path):
            try:
                with open(p_path, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                data["name"] = new_name.strip()
                with open(p_path, "w", encoding="utf-8") as fp:
                    json.dump(data, fp, indent=4, ensure_ascii=False)
                if self.active_profile_id == profile_id:
                    self.profile["name"] = new_name.strip()
                return True
            except Exception as e:
                print(f"[Config] Chyba přejmenování profilu: {e}")
        return False

    def delete_profile(self, profile_id):
        """Smaže profil (pokud jich existuje více)."""
        profs = self.list_profiles()
        if len(profs) <= 1:
            return False
        d = self.profiles_dir
        p_path = os.path.join(d, f"{profile_id}.json")
        if os.path.exists(p_path):
            try:
                os.remove(p_path)
            except Exception as e:
                print(f"[Config] Chyba mazání profilu: {e}")
                return False

        if self.active_profile_id == profile_id:
            rem = self.list_profiles()
            fallback = rem[0]["id"] if rem else "default"
            self.switch_profile(fallback)
        return True

    def duplicate_profile(self, profile_id):
        """Duplikuje zadaný profil."""
        d = self.profiles_dir
        p_path = os.path.join(d, f"{profile_id}.json")
        if os.path.exists(p_path):
            try:
                with open(p_path, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                old_name = data.get("name", profile_id)
                new_name = f"{old_name} (Kopie)"
                return self.create_profile(new_name)
            except Exception as e:
                print(f"[Config] Chyba duplikace profilu: {e}")
        return None

    def switch_page(self, page_idx):
        """Přepne aktivní stránku profilu a aktualizuje buttons."""
        pages = self.profile.get("pages", [])
        if 0 <= page_idx < len(pages):
            # Uložíme aktuální tlačítka do předchozí stránky
            prev_idx = self.profile.get("active_page", 0)
            if 0 <= prev_idx < len(pages):
                pages[prev_idx]["buttons"] = copy.deepcopy(self.profile.get("buttons", []))

            self.profile["active_page"] = page_idx
            pg_buttons = copy.deepcopy(pages[page_idx].get("buttons", []))
            while len(pg_buttons) < 8:
                pg_buttons.append({"id": len(pg_buttons), "label": "", "icon": "", "action_type": "none", "action_param": ""})
            pages[page_idx]["buttons"] = pg_buttons
            self.profile["buttons"] = copy.deepcopy(pg_buttons)
            self.save_profile()
            return True
        return False

    def add_page(self, name=None):
        """Vytvoří novou stránku a vrátí její index."""
        pages = self.profile.setdefault("pages", [])
        new_idx = len(pages)
        if not name:
            name = f"Stránka {new_idx + 1}"
        new_buttons = [
            {"id": i, "label": "", "icon": "", "action_type": "none", "action_param": ""}
            for i in range(8)
        ]
        pages.append({
            "id": new_idx,
            "name": name,
            "buttons": new_buttons
        })
        self.save_profile()
        return new_idx

    def delete_page(self, page_idx):
        """Smaže stránku (pokud existuje více než 1 stránka) a automaticky posune všechny odkazy tlačítek a složek."""
        pages = self.profile.get("pages", [])
        if len(pages) <= 1:
            return False
        if not (0 <= page_idx < len(pages)):
            return False

        # Uložíme aktuální tlačítka do aktivní stránky před smazáním
        act = self.profile.get("active_page", 0)
        if 0 <= act < len(pages):
            pages[act]["buttons"] = copy.deepcopy(self.profile.get("buttons", []))

        # Smažeme stránku z pole
        pages.pop(page_idx)

        # 1. Přeindexujeme ID zbývajících stránek a upravíme parent_page
        for i, p in enumerate(pages):
            p["id"] = i
            if "parent_page" in p and p.get("parent_page") is not None:
                pp = p.get("parent_page")
                if pp == page_idx:
                    p["parent_page"] = 0
                elif pp > page_idx:
                    p["parent_page"] = pp - 1

        # 2. Pomocná funkce pro posun indexů cílových stránek v tlačítkách (goto:X a folder:X)
        def _shift_btn_action(btn):
            if not isinstance(btn, dict):
                return
            atype = btn.get("action_type", "")
            aparam = str(btn.get("action_param", ""))
            if atype == "page":
                for prefix in ("goto:", "folder:"):
                    if aparam.startswith(prefix):
                        try:
                            target = int(aparam[len(prefix):])
                            if target == page_idx:
                                btn["action_param"] = f"{prefix}0"
                            elif target > page_idx:
                                btn["action_param"] = f"{prefix}{target - 1}"
                        except Exception:
                            pass
            elif atype == "multi":
                for sub in btn.get("actions", []):
                    _shift_btn_action(sub)

        # 3. Projdeme všechna tlačítka ve všech zbývajících stránkách profilu
        for p in pages:
            for btn in p.get("buttons", []):
                _shift_btn_action(btn)

        # 4. Spočítáme nový index aktivní stránky
        if act == page_idx:
            new_act = min(page_idx, len(pages) - 1)
        elif act > page_idx:
            new_act = act - 1
        else:
            new_act = act

        self.profile["active_page"] = new_act
        self.profile["buttons"] = copy.deepcopy(pages[new_act].get("buttons", []))
        self.save_profile()
        return True

    def rename_page(self, page_idx, new_name):
        """Přejmenuje stránku."""
        pages = self.profile.get("pages", [])
        if 0 <= page_idx < len(pages):
            pages[page_idx]["name"] = new_name.strip()
            self.save_profile()
            return True
        return False

    def duplicate_page(self, page_idx):
        """Duplikuje zadanou stránku."""
        pages = self.profile.get("pages", [])
        if 0 <= page_idx < len(pages):
            import copy
            cloned = copy.deepcopy(pages[page_idx])
            new_idx = len(pages)
            cloned["id"] = new_idx
            cloned["name"] = f"{cloned.get('name', 'Stránka')} (Kopie)"
            pages.append(cloned)
            self.save_profile()
            return new_idx
        return -1

    def create_folder(self, folder_name="Složka", parent_page_idx=0):
        """Vytvoří podstránku (složku) s tlačítkem 'Zpět' na prvním slotu."""
        new_idx = self.add_page(name=f"📁 {folder_name}")
        pages = self.profile.get("pages", [])
        folder_pg = pages[new_idx]
        folder_pg["is_folder"] = True
        folder_pg["parent_page"] = parent_page_idx
        folder_pg["buttons"][0] = {
            "id": 0,
            "label": "Zpět",
            "icon": "back",
            "custom_icon": "",
            "action_type": "page",
            "action_param": f"goto:{parent_page_idx}"
        }
        self.save_profile()
        return new_idx

    def load_settings(self):
        data = {}
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"[Config] Chyba načítání settings: {e}")

        # Sloučení s výchozími hodnotami
        for k, v in DEFAULT_SETTINGS.items():
            if k not in data:
                data[k] = v
            elif isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    if sub_k not in data[k]:
                        data[k][sub_k] = sub_v

        # Pokud není nastaveno heslo pro OBS, pokusíme se ho automaticky načíst z lokální instalace OBS
        obs_cfg = data.get("obs", {})
        if not obs_cfg.get("password"):
            try:
                from obs_controller import OBSController
                detected = OBSController.detect_obs_config()
                if detected and detected.get("found"):
                    if detected.get("password"):
                        obs_cfg["password"] = detected["password"]
                    if detected.get("port"):
                        obs_cfg["port"] = detected["port"]
                    data["obs"] = obs_cfg
                    # Uložíme aktualizované nastavení
                    self.settings = data
                    self.save_settings()
            except Exception:
                pass

        return data

    def save_settings(self):
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[Config] Chyba ukládání settings: {e}")
            return False
