import json
import urllib.request
import urllib.error
import urllib.parse
import webbrowser
import threading
import subprocess

class TwitchController:
    """
    Správce integrace platformy Twitch přes oficiální Twitch Helix API.
    Umožňuje:
    - Vytvoření značky ve streamu (Stream Marker) s popisem
    - Okamžité vytvoření klipu (Create Clip) s automatickým zkopírováním odkazu
    - Spuštění reklamy (Commercial: 30s, 60s, 90s, 180s)
    - Vymazání chatu (Clear Chat)
    - Zapnutí/vypnutí režimu štítu (Shield Mode)
    - Přepínání režimů chatu (Pouze emote, Pouze subs, Pomalý režim)
    - Odesílání zpráv a příkazů do chatu
    - Otevření Panelu vysílání (Twitch Creator Dashboard)
    """
    def __init__(self, config_manager=None):
        self.config_mgr = config_manager
        self.shield_active = False
        self.emote_mode_active = False
        self.sub_mode_active = False
        self.slow_mode_active = False
        self._load_config()

    def _load_config(self):
        cfg = self.config_mgr.settings.get("twitch", {}) if self.config_mgr else {}
        self.channel = cfg.get("channel", "").strip()
        self.oauth_token = self.clean_token(cfg.get("oauth_token", ""))
        self.client_id = cfg.get("client_id", "").strip()
        self.user_id = str(cfg.get("user_id", "")).strip()

    @staticmethod
    def clean_token(token):
        if not token:
            return ""
        t = str(token).strip()
        if t.lower().startswith("oauth:"):
            t = t[6:].strip()
        return t

    def is_configured(self):
        return bool(self.oauth_token and self.user_id)

    def validate_token(self, token_to_test=None):
        """
        Ověří OAuth token proti Twitch autorizačnímu serveru.
        Při úspěchu automaticky získá a uloží login kanálu, user_id i client_id.
        """
        token = self.clean_token(token_to_test if token_to_test is not None else self.oauth_token)
        if not token:
            return False, "Nebyl zadán žádný OAuth token."

        url = "https://id.twitch.tv/oauth2/validate"
        headers = {
            "Authorization": f"OAuth {token}",
            "User-Agent": "PeciDeckStudio/1.1"
        }

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                user_id = str(data.get("user_id", ""))
                login = data.get("login", "")
                client_id = data.get("client_id", "")

                self.oauth_token = token
                self.user_id = user_id
                self.channel = login
                self.client_id = client_id

                if self.config_mgr:
                    tw_cfg = self.config_mgr.settings.setdefault("twitch", {})
                    tw_cfg["oauth_token"] = token
                    tw_cfg["user_id"] = user_id
                    tw_cfg["channel"] = login
                    tw_cfg["client_id"] = client_id
                    self.config_mgr.save_settings()

                return True, f"Spojení úspěšné! Kanál: {login} (ID: {user_id})"
        except urllib.error.HTTPError as e:
            try:
                err_data = json.loads(e.read().decode("utf-8"))
                msg = err_data.get("message", f"HTTP {e.code}")
            except Exception:
                msg = f"HTTP {e.code}"
            return False, f"Chyba autorizace ({msg})"
        except Exception as e:
            return False, f"Chyba připojení: {e}"

    def _helix_request(self, endpoint, method="GET", json_body=None, params=None):
        """Pomocná metoda pro autorizované volání Twitch Helix API."""
        if not self.is_configured():
            return False, 0, {"error": "Twitch není nakonfigurován. Zadejte token v Nastavení."}

        url = f"https://api.twitch.tv/helix/{endpoint}"
        if params:
            url += "?" + urllib.parse.urlencode(params)

        headers = {
            "Authorization": f"Bearer {self.oauth_token}",
            "Client-Id": self.client_id,
            "User-Agent": "PeciDeckStudio/1.1"
        }

        data_bytes = None
        if json_body is not None:
            headers["Content-Type"] = "application/json"
            data_bytes = json.dumps(json_body).encode("utf-8")

        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=7.0) as resp:
                status_code = resp.status
                raw = resp.read()
                data = json.loads(raw.decode("utf-8")) if raw else {}
                return True, status_code, data
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                data = json.loads(raw.decode("utf-8")) if raw else {}
            except Exception:
                data = {"message": raw.decode("utf-8", errors="ignore")}
            return False, e.code, data
        except Exception as e:
            return False, 0, {"error": str(e)}

    # =========================================================================
    #  JEDNOTLIVÉ TWITCH AKCE
    # =========================================================================
    def create_marker(self, description="PeciDeck Marker"):
        """Vytvoří značku ve streamu (Stream Marker) pro snadné pozdější vyhledání momentu při střihu."""
        if not self.is_configured():
            print("[Twitch] Token není nastaven. Otevírám Twitch Creator Dashboard...")
            self.open_stream_manager()
            return False, "Twitch token není nastaven."

        body = {
            "user_id": self.user_id,
            "description": description[:140] if description else "PeciDeck Marker"
        }
        ok, code, data = self._helix_request("streams/markers", method="POST", json_body=body)
        if ok:
            sec = data.get("data", [{}])[0].get("position_seconds", 0)
            mins = sec // 60
            secs = sec % 60
            msg = f"✓ Značka ve streamu vytvořena v čase {mins:02d}:{secs:02d}!"
            print(f"[Twitch] {msg}")
            return True, msg
        elif code == 404:
            msg = "Stream není online (značku lze vytvořit pouze během živého vysílání)."
            print(f"[Twitch] {msg}")
            return False, msg
        else:
            err = data.get("message", "Neznámá chyba")
            msg = f"Chyba při tvorbě značky: {err}"
            print(f"[Twitch] {msg}")
            return False, msg

    def create_clip(self):
        """Vytvoří klip z posledních sekund streamu a zkopíruje odkaz na editaci do schránky."""
        if not self.is_configured():
            if self.channel:
                webbrowser.open(f"https://twitch.tv/{self.channel}/clip")
            else:
                webbrowser.open("https://clips.twitch.tv/create")
            return False, "Twitch token není nastaven. Otevřen prohlížeč pro klip."

        ok, code, data = self._helix_request(
            "clips",
            method="POST",
            params={"broadcaster_id": self.user_id, "has_delay": "false"}
        )
        if ok:
            clip_info = data.get("data", [{}])[0]
            edit_url = clip_info.get("edit_url", "")
            clip_id = clip_info.get("id", "")
            if edit_url:
                self._copy_to_clipboard(edit_url)
            msg = f"✓ Klip vytvořen (ID: {clip_id})! Odkaz zkopírován do schránky."
            print(f"[Twitch] {msg}")
            return True, msg
        elif code == 404:
            msg = "Klip nelze vytvořit: Kanál právě nevysílá živě."
            print(f"[Twitch] {msg}")
            return False, msg
        else:
            err = data.get("message", "Neznámá chyba")
            msg = f"Chyba při tvorbě klipu: {err}"
            print(f"[Twitch] {msg}")
            return False, msg

    def start_commercial(self, length=30):
        """Spustí reklamu dané délky (30, 60, 90, 120, 180 sekund)."""
        if not self.is_configured():
            return False, "Twitch token není nastaven."

        try:
            sec = int(length)
        except Exception:
            sec = 30

        body = {
            "broadcaster_id": self.user_id,
            "length": sec
        }
        ok, code, data = self._helix_request("channels/commercial", method="POST", json_body=body)
        if ok:
            msg = f"✓ Spuštěna reklama na {sec} sekund."
            print(f"[Twitch] {msg}")
            return True, msg
        else:
            err = data.get("message", "Neznámá chyba")
            msg = f"Chyba při spuštění reklamy: {err}"
            print(f"[Twitch] {msg}")
            return False, msg

    def clear_chat(self):
        """Smaže historii zpráv v chatu."""
        if not self.is_configured():
            return False, "Twitch token není nastaven."

        ok, code, data = self._helix_request(
            "chat/messages",
            method="DELETE",
            params={"broadcaster_id": self.user_id, "moderator_id": self.user_id}
        )
        if ok:
            msg = "✓ Chat Twitch byl vymazán."
            print(f"[Twitch] {msg}")
            return True, msg
        else:
            err = data.get("message", "Neznámá chyba")
            msg = f"Chyba při mazání chatu: {err}"
            print(f"[Twitch] {msg}")
            return False, msg

    def toggle_shield_mode(self, active=None):
        """Zapne nebo vypne Režim štítu (Shield Mode)."""
        if not self.is_configured():
            return False, "Twitch token není nastaven."

        if active is None:
            self.shield_active = not self.shield_active
        else:
            self.shield_active = bool(active)

        body = {"is_active": self.shield_active}
        ok, code, data = self._helix_request(
            "moderation/shield_mode",
            method="PUT",
            json_body=body,
            params={"broadcaster_id": self.user_id, "moderator_id": self.user_id}
        )
        if ok:
            st = "ZAPNUT" if self.shield_active else "VYPNUT"
            msg = f"✓ Režim štítu byl {st}."
            print(f"[Twitch] {msg}")
            return True, msg
        else:
            err = data.get("message", "Neznámá chyba")
            msg = f"Chyba při změně Režimu štítu: {err}"
            print(f"[Twitch] {msg}")
            return False, msg

    def toggle_chat_mode(self, mode="emote"):
        """Přepne režim chatu: 'emote', 'sub' nebo 'slow'."""
        if not self.is_configured():
            return False, "Twitch token není nastaven."

        body = {}
        st_name = ""
        if mode == "emote":
            self.emote_mode_active = not self.emote_mode_active
            body["emote_mode"] = self.emote_mode_active
            st_name = f"Pouze emotikony ({'ZAP' if self.emote_mode_active else 'VYP'})"
        elif mode == "sub":
            self.sub_mode_active = not self.sub_mode_active
            body["subscriber_mode"] = self.sub_mode_active
            st_name = f"Pouze předplatitelé ({'ZAP' if self.sub_mode_active else 'VYP'})"
        elif mode == "slow":
            self.slow_mode_active = not self.slow_mode_active
            body["slow_mode"] = self.slow_mode_active
            if self.slow_mode_active:
                body["slow_mode_wait_time"] = 30
            st_name = f"Pomalý režim ({'ZAP' if self.slow_mode_active else 'VYP'})"

        ok, code, data = self._helix_request(
            "chat/settings",
            method="PATCH",
            json_body=body,
            params={"broadcaster_id": self.user_id, "moderator_id": self.user_id}
        )
        if ok:
            msg = f"✓ Režim chatu upraven: {st_name}."
            print(f"[Twitch] {msg}")
            return True, msg
        else:
            err = data.get("message", "Neznámá chyba")
            msg = f"Chyba nastavení chatu: {err}"
            print(f"[Twitch] {msg}")
            return False, msg

    def send_chat_message(self, message):
        """Odešle zprávu nebo příkaz do chatu streamu."""
        if not message:
            return False, "Prázdná zpráva."
        if not self.is_configured():
            return False, "Twitch token není nastaven."

        body = {
            "broadcaster_id": self.user_id,
            "sender_id": self.user_id,
            "message": str(message)[:500]
        }
        ok, code, data = self._helix_request("chat/messages", method="POST", json_body=body)
        if ok:
            msg = f"✓ Zpráva odeslána do chatu: '{message}'"
            print(f"[Twitch] {msg}")
            return True, msg
        else:
            err = data.get("message", "Neznámá chyba")
            msg = f"Chyba při odeslání zprávy: {err}"
            print(f"[Twitch] {msg}")
            return False, msg

    def open_stream_manager(self):
        """Otevře Twitch Creator Dashboard (Správce vysílání)."""
        chan = self.channel or ""
        url = f"https://dashboard.twitch.tv/u/{chan}/stream-manager" if chan else "https://dashboard.twitch.tv/stream-manager"
        webbrowser.open(url)

    def open_channel(self):
        """Otevře domovskou stránku Twitch kanálu."""
        chan = self.channel or ""
        url = f"https://twitch.tv/{chan}" if chan else "https://twitch.tv"
        webbrowser.open(url)

    def _copy_to_clipboard(self, text):
        try:
            import subprocess
            subprocess.run(["clip"], input=text.strip().encode("utf-16"), check=True)
        except Exception:
            pass

    # =========================================================================
    #  DISPEČER AKCÍ Z PECIDECK HARDWARE (ASYNC V VLÁKNĚ)
    # =========================================================================
    def execute_action(self, param):
        """Vykoná požadovanou Twitch akci v samostatném vlákně bez blokování hardware."""
        p = str(param or "").strip()

        def _worker():
            if p == "marker" or p.startswith("marker:"):
                desc = p[7:].strip() if p.startswith("marker:") else "PeciDeck Marker"
                self.create_marker(desc)
            elif p in ("clip", "create_clip"):
                self.create_clip()
            elif p.startswith("commercial:"):
                try:
                    sec = int(p.split(":", 1)[1])
                except Exception:
                    sec = 30
                self.start_commercial(sec)
            elif p == "commercial":
                self.start_commercial(30)
            elif p in ("clear_chat", "clear"):
                self.clear_chat()
            elif p in ("toggle_shield", "shield"):
                self.toggle_shield_mode()
            elif p in ("toggle_emote_only", "emote_only"):
                self.toggle_chat_mode("emote")
            elif p in ("toggle_sub_only", "sub_only"):
                self.toggle_chat_mode("sub")
            elif p in ("toggle_slow_mode", "slow_mode"):
                self.toggle_chat_mode("slow")
            elif p.startswith("chat:"):
                msg = p[5:].strip()
                self.send_chat_message(msg)
            elif p in ("open_dashboard", "dashboard"):
                self.open_stream_manager()
            elif p in ("open_channel", "channel", "open"):
                self.open_channel()
            else:
                print(f"[Twitch] Neznámý parametr akce: {p}")

        threading.Thread(target=_worker, daemon=True).start()
