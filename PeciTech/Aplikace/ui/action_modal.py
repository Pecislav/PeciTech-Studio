import customtkinter as ctk
from tkinter import filedialog

AVAILABLE_ICONS = [
    "none", "play", "pause", "next", "prev", 
    "mute", "vol_up", "mic", "obs", "rec", 
    "discord", "web", "app"
]

class ActionModal(ctk.CTkToplevel):
    def __init__(self, parent, item_type, item_id, item_data, on_save_cb):
        super().__init__(parent)
        self.item_type = item_type # "button" nebo "encoder"
        self.item_id = item_id
        self.item_data = dict(item_data)
        self.on_save_cb = on_save_cb

        title_str = f"Konfigurace: Klávesa {item_id + 1}" if item_type == "button" else f"Konfigurace: Enkodér {item_id + 1}"
        self.title(title_str)
        self.geometry("520x620")
        self.resizable(False, False)
        self.configure(fg_color="#111218")
        self.grab_set()

        self._init_ui()

    def _init_ui(self):
        # Hlavní nadpis
        header_text = f"Tlačítko SW{self.item_id + 1}" if self.item_type == "button" else f"Enkodér E{self.item_id + 1}"
        lbl_head = ctk.CTkLabel(self, text=header_text, font=ctk.CTkFont(size=20, weight="bold"), text_color="#FF7A29")
        lbl_head.pack(pady=(16, 10))

        if self.item_type == "button":
            self._build_button_ui()
        else:
            self._build_encoder_ui()

        # Spodní tlačítka Uložit / Zrušit
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=20, pady=16)

        btn_cancel = ctk.CTkButton(
            bottom_frame, 
            text="Zrušit", 
            fg_color="#1E202C", 
            hover_color="#282A3A", 
            border_width=1,
            border_color="#2D3042",
            text_color="#CBD5E1", 
            corner_radius=8,
            height=36,
            font=ctk.CTkFont(weight="bold"),
            command=self.destroy
        )
        btn_cancel.pack(side="left", expand=True, padx=5)

        btn_save = ctk.CTkButton(
            bottom_frame, 
            text="Uložit a nahrát do PeciDecku", 
            fg_color="#FF6E14", 
            hover_color="#FF8A35", 
            text_color="#0A0A0E", 
            corner_radius=8,
            height=36,
            font=ctk.CTkFont(weight="bold"), 
            command=self._on_save
        )
        btn_save.pack(side="right", expand=True, padx=5)

    def _build_button_ui(self):
        # 1. Nastavení displeje (Popisek + Ikona)
        disp_frame = ctk.CTkFrame(self, fg_color="#14151E", corner_radius=12, border_width=1, border_color="#242738")
        disp_frame.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(disp_frame, text="Zobrazení na displeji", font=ctk.CTkFont(weight="bold", size=13), text_color="#FF7A29").pack(anchor="w", padx=14, pady=(12, 6))

        f_inputs = ctk.CTkFrame(disp_frame, fg_color="transparent")
        f_inputs.pack(fill="x", padx=14, pady=(0, 12))

        ctk.CTkLabel(f_inputs, text="Popisek (max 10 znaků):", text_color="#CBD5E1").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_label = ctk.CTkEntry(f_inputs, width=180, height=28, fg_color="#0E0F15", border_color="#282B3C", border_width=1, corner_radius=7, text_color="#FFFFFF", placeholder_text="např. Mute")
        self.entry_label.insert(0, self.item_data.get("label", ""))
        self.entry_label.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(f_inputs, text="Ikona:", text_color="#CBD5E1").grid(row=1, column=0, sticky="w", pady=5)
        self.combo_icon = ctk.CTkComboBox(f_inputs, values=AVAILABLE_ICONS, width=180, height=28, fg_color="#0E0F15", border_color="#282B3C", border_width=1, corner_radius=7)
        curr_icon = self.item_data.get("icon", "none")
        self.combo_icon.set(curr_icon if curr_icon in AVAILABLE_ICONS else "none")
        self.combo_icon.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        # 2. Nastavení Akce
        act_frame = ctk.CTkFrame(self, fg_color="#14151E", corner_radius=12, border_width=1, border_color="#242738")
        act_frame.pack(fill="both", expand=True, padx=20, pady=8)

        ctk.CTkLabel(act_frame, text="Přiřazená akce po stisknutí", font=ctk.CTkFont(weight="bold", size=13), text_color="#FF7A29").pack(anchor="w", padx=14, pady=(12, 6))

        self.action_type_var = ctk.StringVar(value=self.item_data.get("action_type", "none"))

        types = [
            ("Žádná akce", "none"),
            ("Média / Ovládání zvuku", "media"),
            ("Klávesová zkratka (Hotkey)", "hotkey"),
            ("Spustit aplikaci / program", "app"),
            ("Otevřít webovou URL", "url"),
            ("OBS Studio", "obs")
        ]

        self.combo_type = ctk.CTkComboBox(act_frame, values=[t[0] for t in types], command=self._on_type_changed, width=320, height=30, fg_color="#0E0F15", border_color="#282B3C", border_width=1, corner_radius=7)
        type_to_title = {t[1]: t[0] for t in types}
        self.combo_type.set(type_to_title.get(self.action_type_var.get(), "Žádná akce"))
        self.combo_type.pack(padx=14, pady=5)

        # Dynamický detail akce
        self.detail_frame = ctk.CTkFrame(act_frame, fg_color="transparent")
        self.detail_frame.pack(fill="both", expand=True, padx=14, pady=10)

        self._render_action_detail()

    def _on_type_changed(self, choice):
        mapping = {
            "Žádná akce": "none",
            "Média / Ovládání zvuku": "media",
            "Klávesová zkratka (Hotkey)": "hotkey",
            "Spustit aplikaci / program": "app",
            "Otevřít webovou URL": "url",
            "OBS Studio": "obs"
        }
        self.action_type_var.set(mapping.get(choice, "none"))
        self._render_action_detail()

    def _render_action_detail(self):
        for widget in self.detail_frame.winfo_children():
            widget.destroy()

        atype = self.action_type_var.get()
        param = self.item_data.get("action_param", "")

        if atype == "media":
            ctk.CTkLabel(self.detail_frame, text="Vyber multimediální příkaz:", text_color="#CBD5E1").pack(anchor="w", pady=4)
            self.media_combo = ctk.CTkComboBox(self.detail_frame, values=[
                "play_pause", "mute", "next", "prev", "stop"
            ], width=260, height=28, fg_color="#0E0F15", border_color="#282B3C", border_width=1, corner_radius=7)
            self.media_combo.set(param if isinstance(param, str) and param in ["play_pause", "mute", "next", "prev", "stop"] else "play_pause")
            self.media_combo.pack(anchor="w", pady=4)

        elif atype == "hotkey":
            ctk.CTkLabel(self.detail_frame, text="Kombinace kláves (např. ctrl+shift+m nebo win+shift+s):", text_color="#CBD5E1").pack(anchor="w", pady=4)
            self.entry_hotkey = ctk.CTkEntry(self.detail_frame, width=320, height=28, fg_color="#0E0F15", border_color="#282B3C", border_width=1, corner_radius=7, placeholder_text="např. ctrl+alt+t")
            self.entry_hotkey.insert(0, param if isinstance(param, str) else "")
            self.entry_hotkey.pack(anchor="w", pady=4)

        elif atype == "app":
            ctk.CTkLabel(self.detail_frame, text="Cesta k aplikaci / souboru:", text_color="#CBD5E1").pack(anchor="w", pady=4)
            f_box = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
            f_box.pack(fill="x", pady=4)
            self.entry_path = ctk.CTkEntry(f_box, width=280, height=28, fg_color="#0E0F15", border_color="#282B3C", border_width=1, corner_radius=7)
            self.entry_path.insert(0, param if isinstance(param, str) else "")
            self.entry_path.pack(side="left")
            btn_browse = ctk.CTkButton(f_box, text="Procházet...", width=90, height=28, fg_color="#1E202C", hover_color="#282A3A", border_width=1, border_color="#2D3042", corner_radius=7, command=self._browse_file)
            btn_browse.pack(side="left", padx=8)

        elif atype == "url":
            ctk.CTkLabel(self.detail_frame, text="Webová adresa URL:", text_color="#CBD5E1").pack(anchor="w", pady=4)
            self.entry_url = ctk.CTkEntry(self.detail_frame, width=360, height=28, fg_color="#0E0F15", border_color="#282B3C", border_width=1, corner_radius=7, placeholder_text="https://...")
            self.entry_url.insert(0, param if isinstance(param, str) else "https://")
            self.entry_url.pack(anchor="w", pady=4)

        elif atype == "obs":
            ctk.CTkLabel(self.detail_frame, text="OBS Akce:", text_color="#CBD5E1").pack(anchor="w", pady=4)
            obs_actions = [
                ("Spustit / Zastavit Stream", "toggle_stream"),
                ("Spustit / Zastavit Záznam", "toggle_record"),
                ("Pozastavit / Obnovit Záznam", "toggle_record_pause"),
                ("Další scéna OBS", "next_scene"),
                ("Předchozí scéna OBS", "prev_scene"),
                ("Přepnout na scénu...", "scene:"),
                ("Ztlumit zvuk (Mute)...", "mute:"),
                ("Virtuální kamera", "toggle_virtual_cam"),
                ("Uložit Replay buffer", "save_replay_buffer")
            ]
            self.obs_action_map = dict(obs_actions)
            self.obs_action_rev = {v: k for k, v in obs_actions}

            current_key = "toggle_stream"
            sub_val = ""
            if isinstance(param, str):
                if param.startswith("scene:"):
                    current_key = "scene:"
                    sub_val = param[6:]
                elif param.startswith("mute:"):
                    current_key = "mute:"
                    sub_val = param[5:]
                elif param in self.obs_action_rev:
                    current_key = param

            self.obs_combo = ctk.CTkComboBox(
                self.detail_frame,
                values=[k for k, _ in obs_actions],
                command=self._on_obs_action_changed,
                width=320,
                height=28,
                fg_color="#0E0F15",
                border_color="#282B3C",
                border_width=1,
                corner_radius=7
            )
            self.obs_combo.set(self.obs_action_rev.get(current_key, "Spustit / Zastavit Stream"))
            self.obs_combo.pack(anchor="w", pady=4)

            self.f_obs_sub = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
            self.f_obs_sub.pack(fill="x", pady=4)

            self.lbl_obs_sub = ctk.CTkLabel(self.f_obs_sub, text="Název:", text_color="#CBD5E1")
            self.lbl_obs_sub.pack(side="left", padx=(0, 8))

            self.entry_obs_sub = ctk.CTkEntry(
                self.f_obs_sub,
                width=240,
                height=28,
                fg_color="#0E0F15",
                border_color="#282B3C",
                border_width=1,
                corner_radius=7,
                placeholder_text="Název scény nebo audio stopy..."
            )
            self.entry_obs_sub.insert(0, sub_val)
            self.entry_obs_sub.pack(side="left")

            if current_key not in ("scene:", "mute:"):
                self.f_obs_sub.pack_forget()

    def _on_obs_action_changed(self, choice):
        act_id = self.obs_action_map.get(choice, "toggle_stream")
        if act_id in ("scene:", "mute:"):
            label_text = "Název scény:" if act_id == "scene:" else "Audio stopa:"
            self.lbl_obs_sub.configure(text=label_text)
            self.f_obs_sub.pack(fill="x", pady=4)
        else:
            self.f_obs_sub.pack_forget()

    def _browse_file(self):
        filename = filedialog.askopenfilename(
            title="Vyber aplikaci nebo soubor",
            filetypes=[("Spustitelné soubory", "*.exe;*.bat;*.cmd"), ("Všechny soubory", "*.*")]
        )
        if filename:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, filename)

    def _build_encoder_ui(self):
        f = ctk.CTkFrame(self, fg_color="#14151E", corner_radius=12, border_width=1, border_color="#242738")
        f.pack(fill="both", expand=True, padx=20, pady=8)

        ctk.CTkLabel(f, text="Nastavení funkcí enkodéru", font=ctk.CTkFont(weight="bold", size=13), text_color="#FF7A29").pack(anchor="w", padx=14, pady=(12, 6))

        ctk.CTkLabel(f, text="Typ ovládání:", text_color="#CBD5E1").pack(anchor="w", padx=14, pady=(10, 2))
        self.enc_mode_combo = ctk.CTkComboBox(f, values=[
            "Hlavní hlasitost Windows (+/- a Mute)",
            "Média (Posun vpřed/vzad a Play/Pause)",
            "Jas displeje PeciDeck (+/- a Vypnout)",
            "OBS: Přepínání scén (CW další, CCW předchozí)",
            "OBS: Hlasitost stopy v OBS (+/- a Mute)"
        ], width=360, height=30, fg_color="#0E0F15", border_color="#282B3C", border_width=1, corner_radius=7)

        cw = self.item_data.get("cw", {}).get("action_type", "")
        cw_p = self.item_data.get("cw", {}).get("action_param", "")
        if cw == "volume":
            self.enc_mode_combo.set("Hlavní hlasitost Windows (+/- a Mute)")
        elif cw == "media":
            self.enc_mode_combo.set("Média (Posun vpřed/vzad a Play/Pause)")
        elif cw == "brightness":
            self.enc_mode_combo.set("Jas displeje PeciDeck (+/- a Vypnout)")
        elif cw == "obs" and ("scene" in cw_p):
            self.enc_mode_combo.set("OBS: Přepínání scén (CW další, CCW předchozí)")
        elif cw == "obs" and ("vol" in cw_p):
            self.enc_mode_combo.set("OBS: Hlasitost stopy v OBS (+/- a Mute)")
        else:
            self.enc_mode_combo.set("Hlavní hlasitost Windows (+/- a Mute)")
        self.enc_mode_combo.pack(padx=14, pady=5)

    def _on_save(self):
        if self.item_type == "button":
            self.item_data["label"] = self.entry_label.get().strip()
            self.item_data["icon"] = self.combo_icon.get()
            atype = self.action_type_var.get()
            self.item_data["action_type"] = atype

            if atype == "media":
                self.item_data["action_param"] = self.media_combo.get()
            elif atype == "hotkey":
                self.item_data["action_param"] = self.entry_hotkey.get().strip()
            elif atype == "app":
                self.item_data["action_param"] = self.entry_path.get().strip()
            elif atype == "url":
                self.item_data["action_param"] = self.entry_url.get().strip()
            elif atype == "obs":
                choice = self.obs_combo.get()
                act_id = getattr(self, "obs_action_map", {}).get(choice, "toggle_stream")
                if act_id in ("scene:", "mute:"):
                    sub_val = self.entry_obs_sub.get().strip() if hasattr(self, "entry_obs_sub") else ""
                    self.item_data["action_param"] = f"{act_id}{sub_val}"
                else:
                    self.item_data["action_param"] = act_id
            else:
                self.item_data["action_param"] = ""

        else: # encoder
            mode = self.enc_mode_combo.get()
            if "hlasitost" in mode and "OBS" not in mode:
                self.item_data["cw"] = {"action_type": "volume", "action_param": "up"}
                self.item_data["ccw"] = {"action_type": "volume", "action_param": "down"}
                self.item_data["btn"] = {"action_type": "volume", "action_param": "mute"}
            elif "Média" in mode:
                self.item_data["cw"] = {"action_type": "media", "action_param": "next"}
                self.item_data["ccw"] = {"action_type": "media", "action_param": "prev"}
                self.item_data["btn"] = {"action_type": "media", "action_param": "play_pause"}
            elif "Jas" in mode:
                self.item_data["cw"] = {"action_type": "brightness", "action_param": "up"}
                self.item_data["ccw"] = {"action_type": "brightness", "action_param": "down"}
                self.item_data["btn"] = {"action_type": "brightness", "action_param": "toggle"}
            elif "scén" in mode:
                self.item_data["cw"] = {"action_type": "obs", "action_param": "next_scene"}
                self.item_data["ccw"] = {"action_type": "obs", "action_param": "prev_scene"}
                self.item_data["btn"] = {"action_type": "obs", "action_param": "toggle_stream"}
            elif "OBS" in mode and "Hlasitost" in mode:
                self.item_data["cw"] = {"action_type": "obs", "action_param": "vol_up:Desktop Audio"}
                self.item_data["ccw"] = {"action_type": "obs", "action_param": "vol_down:Desktop Audio"}
                self.item_data["btn"] = {"action_type": "obs", "action_param": "mute:Desktop Audio"}

        self.on_save_cb(self.item_type, self.item_id, self.item_data)
        self.destroy()
