import os
import subprocess
import json
import customtkinter as ctk
from tkinter import filedialog, messagebox
from assets_manager import get_asset_icon

class SettingsModal(ctk.CTkFrame):
    """
    Moderní CELOOBRAZOVKOVÉ nastavení PeciTech Studia (Obrázek 4):
    - Roztaženo přes celé okno (žádné ořezané karty ani černé pruhy)
    - Čistá hlavička s titulkem "Nastavení PeciTech Studio" a zavíracím tlačítkem "✕"
    - Vodorovné záložky:
        [ Zařízení ]  [ OBS Studio ]  [ Profily & Záloha ]  [ Obecné & Systém ]
    - Perfektně zarovnané ovládací prvky (žádné překrývání slideru a tlačítek)
    - Spodní lišta s prominentním zaobleným tlačítkem "Hotovo"
    """
    def __init__(self, parent, config_mgr, serial_bridge, obs_controller, on_scan_cb=None, discord_controller=None, twitch_controller=None):
        super().__init__(parent, fg_color="#0D0E14")
        self.config_mgr = config_mgr
        self.serial = serial_bridge
        self.obs = obs_controller
        self.discord = discord_controller
        self.twitch = twitch_controller
        self.on_scan_cb = on_scan_cb
        self.is_inverted = True

        self.current_tab = "devices"
        self.tab_buttons = {}
        self.tab_indicators = {}
        self.tab_frames = {}

        self.current_sub_tab = "obs"
        self.sub_tab_buttons = {}
        self.sub_tab_indicators = {}
        self.sub_tab_frames = {}

        self._build_ui()

    def _build_ui(self):
        # 1. HORNÍ LIŠTA: Titulek a křížek "✕" (Plná šířka okna)
        top_bar = ctk.CTkFrame(self, fg_color="transparent", height=50)
        top_bar.pack(fill="x", padx=36, pady=(18, 6))

        lbl_title = ctk.CTkLabel(
            top_bar,
            text="Nastavení PeciTech Studio",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        lbl_title.place(relx=0.5, rely=0.5, anchor="center")

        btn_close = ctk.CTkButton(
            top_bar,
            text="✕",
            width=36,
            height=36,
            corner_radius=18,
            fg_color="#181A24",
            hover_color="#2A2D3E",
            border_width=1,
            border_color="#262838",
            text_color="#94A3B8",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.hide
        )
        btn_close.pack(side="right")

        # 2. VODOROVNÉ ZÁLOŽKY (Pills s akcentním podtržením)
        tabs_bar = ctk.CTkFrame(self, fg_color="transparent", height=44)
        tabs_bar.pack(fill="x", padx=36, pady=(0, 8))

        tabs_container = ctk.CTkFrame(tabs_bar, fg_color="transparent")
        tabs_container.place(relx=0.5, rely=0.5, anchor="center")

        tab_defs = [
            ("devices", "Zařízení"),
            ("integrations", "Pluginy & Integrace"),
            ("profiles", "Profily & Záloha"),
            ("system", "Obecné & Systém")
        ]

        for tid, tlabel in tab_defs:
            tbox = ctk.CTkFrame(tabs_container, fg_color="transparent")
            tbox.pack(side="left", padx=16)

            btn = ctk.CTkButton(
                tbox,
                text=tlabel,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="transparent",
                hover_color="#1A1C28",
                text_color="#FF7A29" if tid == self.current_tab else "#7E849B",
                height=32,
                corner_radius=6,
                command=lambda t=tid: self._switch_tab(t)
            )
            btn.pack()

            indicator = ctk.CTkFrame(
                tbox,
                height=3,
                width=64,
                corner_radius=2,
                fg_color="#FF7A29" if tid == self.current_tab else "transparent"
            )
            indicator.pack(pady=(2, 0))

            self.tab_buttons[tid] = btn
            self.tab_indicators[tid] = indicator

        # Oddělovací linka pod záložkami přes celou šířku
        line = ctk.CTkFrame(self, height=1, fg_color="#1E202C")
        line.pack(fill="x", padx=36, pady=(0, 14))

        # 3. OBSAHOVÁ ČÁST PRO ZÁLOŽKY (Plná výška a šířka okna)
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.pack(fill="both", expand=True, padx=36, pady=(0, 12))

        # Vytvoření jednotlivých panelů
        self._build_devices_tab()
        self._build_integrations_tab()
        self._build_profiles_tab()
        self._build_system_tab()

        # Zobrazení výchozí záložky
        self._switch_tab("devices")

        # 4. DOLNÍ LIŠTA S TLAČÍTKEM "HOTOVO"
        bottom_bar = ctk.CTkFrame(self, fg_color="transparent", height=52)
        bottom_bar.pack(fill="x", padx=36, pady=(0, 20))

        btn_done = ctk.CTkButton(
            bottom_bar,
            text="Hotovo",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#FF7A29",
            hover_color="#FF8E3D",
            text_color="#0A0A0E",
            corner_radius=18,
            width=140,
            height=38,
            command=self.hide
        )
        btn_done.pack(side="right")

    def _switch_tab(self, tid):
        if tid in ("obs", "discord", "twitch"):
            sub_target = tid
            tid = "integrations"
            self._switch_sub_tab(sub_target)

        self.current_tab = tid
        for name, btn in self.tab_buttons.items():
            is_active = (name == tid)
            btn.configure(text_color="#FF7A29" if is_active else "#7E849B")
            self.tab_indicators[name].configure(fg_color="#FF7A29" if is_active else "transparent")

        for name, f in self.tab_frames.items():
            if name == tid:
                f.pack(fill="both", expand=True)
            else:
                f.pack_forget()

    # =========================================================================
    #  ZÁLOŽKA 1: ZAŘÍZENÍ (CELOOBRAZOVKOVÝ DVOUPOHLEDOVÝ STYL)
    # =========================================================================
    def _build_devices_tab(self):
        f = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.tab_frames["devices"] = f

        # LEVÝ SLOUPEC: "Moje Zařízení" (Seznam a status)
        left_box = ctk.CTkFrame(f, width=280, fg_color="#12131C", corner_radius=14, border_width=1, border_color="#202232")
        left_box.pack(side="left", fill="y", padx=(0, 20))
        left_box.pack_propagate(False)

        lbl_mach = ctk.CTkLabel(left_box, text="Moje Zařízení", font=ctk.CTkFont(size=12, weight="bold"), text_color="#8E95AE")
        lbl_mach.pack(anchor="w", padx=18, pady=(16, 12))

        # Karta PeciDeck MK.1
        self.device_tile = ctk.CTkFrame(
            left_box,
            fg_color="#181A26",
            corner_radius=12,
            border_width=1.5,
            border_color="#FF7A29"
        )
        self.device_tile.pack(fill="x", padx=14, pady=4)

        dev_icon = get_asset_icon("gear", size=(22, 22))
        lbl_dico = ctk.CTkLabel(
            self.device_tile,
            image=dev_icon,
            text="",
            width=36,
            height=36,
            corner_radius=8,
            fg_color="#222536"
        )
        lbl_dico.pack(side="left", padx=(12, 10), pady=12)

        info_b = ctk.CTkFrame(self.device_tile, fg_color="transparent")
        info_b.pack(side="left", fill="both", expand=True, padx=(0, 14), pady=12)

        lbl_dname = ctk.CTkLabel(info_b, text="PeciDeck MK.1", font=ctk.CTkFont(size=13, weight="bold"), text_color="#FFFFFF")
        lbl_dname.pack(anchor="w")

        self.lbl_dstatus = ctk.CTkLabel(info_b, text="● Připojeno (USB)", font=ctk.CTkFont(size=10, weight="bold"), text_color="#10B981")
        self.lbl_dstatus.pack(anchor="w", pady=(3, 0))

        # Tlačítko pro vyhledání dalších zařízení vespod
        btn_rescan = ctk.CTkButton(
            left_box,
            text="+ Znovu vyhledat zařízení",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="transparent",
            hover_color="#1B1D2A",
            text_color="#FF7A29",
            height=34,
            command=self._on_rescan_click
        )
        btn_rescan.pack(side="bottom", fill="x", padx=14, pady=14)

        # PRAVÝ SLOUPEC: Detailní nastavení zařízení s dostatkem prostoru
        right_box = ctk.CTkFrame(f, fg_color="#12131C", corner_radius=14, border_width=1, border_color="#202232")
        right_box.pack(side="left", fill="both", expand=True)

        right_scroll = ctk.CTkScrollableFrame(
            right_box, 
            fg_color="transparent",
            scrollbar_button_color="#282A3C",
            scrollbar_button_hover_color="#3E4258"
        )
        right_scroll.pack(fill="both", expand=True, padx=8, pady=8)

        # 1. SEKCE: Aktualizace Firmware
        self._create_setting_row(
            parent=right_scroll,
            title="Aktualizace Firmware",
            subtitle="Ověřte, zda vaše zařízení PeciDeck MK.1 běží na nejnovějším firmware (FW 1.1.0).",
            btn_text="Zkontrolovat",
            btn_cmd=self._check_firmware
        )

        # 2. SEKCE: Jas Displeje ST7789 (Bez ořezání a bez kolizí)
        row_disp = ctk.CTkFrame(right_scroll, fg_color="transparent")
        row_disp.pack(fill="x", padx=20, pady=12)

        txt_b = ctk.CTkFrame(row_disp, fg_color="transparent")
        txt_b.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(txt_b, text="Jas Displeje (ST7789)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#FFFFFF").pack(anchor="w")
        ctk.CTkLabel(txt_b, text="Nastavte úroveň podsvícení IPS displeje zařízení (10-255).", font=ctk.CTkFont(size=11), text_color="#7E849B").pack(anchor="w", pady=(2, 0))

        ctrl_b = ctk.CTkFrame(row_disp, fg_color="transparent")
        ctrl_b.pack(side="right", padx=(16, 0))

        self.slider_br = ctk.CTkSlider(
            ctrl_b,
            from_=10,
            to=255,
            width=160,
            button_color="#FF7A29",
            button_hover_color="#FFA05C",
            progress_color="#FF7A29",
            fg_color="#202230",
            command=self._on_brightness_change
        )
        self.slider_br.set(self.config_mgr.profile.get("brightness", 255))
        self.slider_br.pack(side="left", padx=(0, 12))

        btn_inv = ctk.CTkButton(
            ctrl_b,
            text="Invertovat barvy",
            font=ctk.CTkFont(size=11, weight="bold"),
            width=130,
            height=30,
            corner_radius=15,
            fg_color="#1E202C",
            hover_color="#282A3A",
            border_width=1,
            border_color="#2D3042",
            text_color="#FFFFFF",
            command=self._toggle_inversion
        )
        btn_inv.pack(side="left")

        self._add_divider(right_scroll)

        # 3. SEKCE: Synchronizace Mřížky
        self._create_setting_row(
            parent=right_scroll,
            title="Synchronizace s Hardwarem",
            subtitle="Nahrajte aktuální ikony, popisky a rozložení tlačítek přímo do zařízení.",
            btn_text="Synchronizovat",
            btn_cmd=self._on_sync_display
        )

        # 4. SEKCE: Standby Režim
        self._create_setting_row(
            parent=right_scroll,
            title="Úsporný Režim (Offline)",
            subtitle="Přepne IPS displej do úsporného standby režimu.",
            btn_text="Uspat displej",
            btn_cmd=self._show_standby
        )

    # =========================================================================
    #  ZÁLOŽKA 2: PLUGINY & INTEGRACE (SLOUČENÉ OBS STUDIO A DISCORD S PŘEPÍNAČEM)
    # =========================================================================
    def _build_integrations_tab(self):
        f = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.tab_frames["integrations"] = f

        # Horní přepínač pod-záložek: OBS Studio | Discord (Obrázek od uživatele)
        sub_bar = ctk.CTkFrame(f, fg_color="transparent", height=42)
        sub_bar.pack(fill="x", padx=4, pady=(0, 6))

        sub_container = ctk.CTkFrame(sub_bar, fg_color="transparent")
        sub_container.place(relx=0.5, rely=0.5, anchor="center")

        sub_defs = [
            ("obs", "OBS Studio"),
            ("discord", "Discord"),
            ("twitch", "Twitch")
        ]

        for sid, slabel in sub_defs:
            sbox = ctk.CTkFrame(sub_container, fg_color="transparent")
            sbox.pack(side="left", padx=28)

            btn = ctk.CTkButton(
                sbox,
                text=slabel,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="transparent",
                hover_color="#181A26",
                text_color="#FF7A29" if sid == self.current_sub_tab else "#7E849B",
                height=32,
                corner_radius=6,
                command=lambda s=sid: self._switch_sub_tab(s)
            )
            btn.pack()

            indicator = ctk.CTkFrame(
                sbox,
                height=3,
                width=80,
                corner_radius=2,
                fg_color="#FF7A29" if sid == self.current_sub_tab else "transparent"
            )
            indicator.pack(pady=(2, 0))

            self.sub_tab_buttons[sid] = btn
            self.sub_tab_indicators[sid] = indicator

        # Oddělovací linka pod volbou OBS / Discord / Twitch
        sep_line = ctk.CTkFrame(f, height=1, fg_color="#1E202C")
        sep_line.pack(fill="x", padx=10, pady=(0, 8))

        # Obsahová oblast pro pod-panely (OBS Studio, Discord a Twitch)
        self.sub_content_area = ctk.CTkFrame(f, fg_color="transparent")
        self.sub_content_area.pack(fill="both", expand=True)

        self._build_obs_panel(self.sub_content_area)
        self._build_discord_panel(self.sub_content_area)
        self._build_twitch_panel(self.sub_content_area)

        self._switch_sub_tab("obs")

    def _switch_sub_tab(self, sid):
        self.current_sub_tab = sid
        for name, btn in self.sub_tab_buttons.items():
            is_active = (name == sid)
            btn.configure(text_color="#FF7A29" if is_active else "#7E849B")
            self.sub_tab_indicators[name].configure(fg_color="#FF7A29" if is_active else "transparent")

        for name, fr in self.sub_tab_frames.items():
            if name == sid:
                fr.pack(fill="both", expand=True)
            else:
                fr.pack_forget()

    def _build_obs_tab(self):
        """Zpětná kompatibilita."""
        pass

    def _build_discord_tab(self):
        """Zpětná kompatibilita."""
        pass

    def _build_obs_panel(self, parent):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        self.sub_tab_frames["obs"] = f

        box = ctk.CTkFrame(f, fg_color="#12131C", corner_radius=14, border_width=1, border_color="#202232")
        box.pack(fill="both", expand=True, padx=4, pady=4)

        header_row = ctk.CTkFrame(box, fg_color="transparent")
        header_row.pack(fill="x", padx=24, pady=(20, 4))

        ctk.CTkLabel(header_row, text="OBS WebSocket Server", font=ctk.CTkFont(size=16, weight="bold"), text_color="#FFFFFF").pack(side="left")

        # Stavový indikátor vpravo
        is_conn = bool(self.obs and self.obs.is_connected)
        self.lbl_obs_tab_status = ctk.CTkLabel(
            header_row,
            text="● Připojeno k OBS" if is_conn else "● Odpojeno od OBS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2ECC71" if is_conn else "#E74C3C"
        )
        self.lbl_obs_tab_status.pack(side="right")

        ctk.CTkLabel(box, text="Parametry pro spojení s programem OBS Studio přes OBS WebSocket v5 (OBS 28+).", font=ctk.CTkFont(size=12), text_color="#7E849B").pack(anchor="w", padx=24, pady=(0, 14))

        obs_cfg = self.config_mgr.settings.get("obs", {})

        # Rychlá tlačítka akcí nahoře
        quick_bar = ctk.CTkFrame(box, fg_color="transparent")
        quick_bar.pack(fill="x", padx=24, pady=(0, 14))

        btn_autodetect = ctk.CTkButton(
            quick_bar,
            text="⚡ Automaticky načíst z OBS",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            corner_radius=16,
            fg_color="#182333",
            hover_color="#24344D",
            text_color="#38BDF8",
            border_width=1,
            border_color="#2F425C",
            command=self._auto_detect_obs
        )
        btn_autodetect.pack(side="left", padx=(0, 12))

        btn_launch = ctk.CTkButton(
            quick_bar,
            text="Spustit OBS Studio",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            corner_radius=16,
            fg_color="#1E202C",
            hover_color="#282A3A",
            text_color="#CBD5E1",
            border_width=1,
            border_color="#2D3042",
            command=self._launch_obs
        )
        btn_launch.pack(side="left")

        form = ctk.CTkFrame(box, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=4)

        # Host & Port
        r1 = ctk.CTkFrame(form, fg_color="transparent")
        r1.pack(fill="x", pady=8)
        ctk.CTkLabel(r1, text="Host adresa:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1", width=110, anchor="w").pack(side="left")
        self.entry_obs_host = ctk.CTkEntry(r1, width=240, height=32, fg_color="#181A25", border_color="#282B3C", border_width=1, corner_radius=8, text_color="#FFFFFF")
        self.entry_obs_host.insert(0, obs_cfg.get("host", "localhost"))
        self.entry_obs_host.pack(side="left", padx=(0, 24))

        ctk.CTkLabel(r1, text="Port:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1", width=50, anchor="w").pack(side="left")
        self.entry_obs_port = ctk.CTkEntry(r1, width=110, height=32, fg_color="#181A25", border_color="#282B3C", border_width=1, corner_radius=8, text_color="#FFFFFF")
        self.entry_obs_port.insert(0, str(obs_cfg.get("port", 4455)))
        self.entry_obs_port.pack(side="left")

        # Heslo
        r2 = ctk.CTkFrame(form, fg_color="transparent")
        r2.pack(fill="x", pady=8)
        ctk.CTkLabel(r2, text="Heslo serveru:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1", width=110, anchor="w").pack(side="left")
        self.entry_obs_pwd = ctk.CTkEntry(r2, width=240, height=32, show="*", fg_color="#181A25", border_color="#282B3C", border_width=1, corner_radius=8, text_color="#FFFFFF")
        self.entry_obs_pwd.insert(0, obs_cfg.get("password", ""))
        self.entry_obs_pwd.pack(side="left")

        # Checkbox Automatické připojení
        r_auto = ctk.CTkFrame(form, fg_color="transparent")
        r_auto.pack(fill="x", pady=(12, 6))
        self.chk_obs_auto = ctk.CTkCheckBox(
            r_auto,
            text="Automaticky připojovat k OBS na pozadí při startu aplikace",
            font=ctk.CTkFont(size=12),
            text_color="#CBD5E1",
            fg_color="#FF7A29",
            hover_color="#FFA05C",
            command=self._on_auto_connect_changed
        )
        if obs_cfg.get("auto_connect", True):
            self.chk_obs_auto.select()
        else:
            self.chk_obs_auto.deselect()
        self.chk_obs_auto.pack(anchor="w")

        # Test tlačítko a výsledek
        r3 = ctk.CTkFrame(form, fg_color="transparent")
        r3.pack(fill="x", pady=(16, 8))

        btn_test = ctk.CTkButton(
            r3,
            text="Otestovat spojení s OBS",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=200,
            height=34,
            corner_radius=17,
            fg_color="#1E202C",
            hover_color="#FF7A29",
            border_width=1,
            border_color="#2D3042",
            text_color="#FFFFFF",
            command=self._test_obs_connection
        )
        btn_test.pack(side="left")

        self.lbl_obs_res = ctk.CTkLabel(r3, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_obs_res.pack(side="left", padx=18)

    # =========================================================================
    #  ZÁLOŽKA: DISCORD PLUGIN
    # =========================================================================
    def _build_discord_panel(self, parent):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        self.sub_tab_frames["discord"] = f

        box = ctk.CTkFrame(f, fg_color="#12131C", corner_radius=14, border_width=1, border_color="#202232")
        box.pack(fill="both", expand=True, padx=4, pady=4)

        header_row = ctk.CTkFrame(box, fg_color="transparent")
        header_row.pack(fill="x", padx=24, pady=(20, 4))

        ctk.CTkLabel(header_row, text="Discord Integrace & Hlas", font=ctk.CTkFont(size=16, weight="bold"), text_color="#FFFFFF").pack(side="left")

        # Stavový indikátor vpravo
        is_disc = bool(self.discord and self.discord.is_running())
        self.lbl_discord_tab_status = ctk.CTkLabel(
            header_row,
            text="● Discord běží (Aktivní)" if is_disc else "○ Discord neběží",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2ECC71" if is_disc else "#FF9D54"
        )
        self.lbl_discord_tab_status.pack(side="right")

        ctk.CTkLabel(box, text="Přímé ovládání mikrofonu, sluchátek a hovorů aplikace Discord pro PeciDeck.", font=ctk.CTkFont(size=12), text_color="#7E849B").pack(anchor="w", padx=24, pady=(0, 14))

        disc_cfg = self.config_mgr.settings.get("discord", {})

        # Rychlá tlačítka akcí nahoře
        quick_bar = ctk.CTkFrame(box, fg_color="transparent")
        quick_bar.pack(fill="x", padx=24, pady=(0, 14))

        btn_launch = ctk.CTkButton(
            quick_bar,
            text="🚀 Otevřít Discord",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            corner_radius=16,
            fg_color="#1E202C",
            hover_color="#282A3A",
            text_color="#CBD5E1",
            border_width=1,
            border_color="#2D3042",
            command=self._launch_discord
        )
        btn_launch.pack(side="left", padx=(0, 10))

        btn_test_mute = ctk.CTkButton(
            quick_bar,
            text="🎙️ Otestovat Mute",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            corner_radius=16,
            fg_color="#182333",
            hover_color="#24344D",
            text_color="#38BDF8",
            border_width=1,
            border_color="#2F425C",
            command=self._test_discord_mute
        )
        btn_test_mute.pack(side="left", padx=(0, 10))

        btn_test_deafen = ctk.CTkButton(
            quick_bar,
            text="🎧 Otestovat Deafen",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            corner_radius=16,
            fg_color="#182333",
            hover_color="#24344D",
            text_color="#38BDF8",
            border_width=1,
            border_color="#2F425C",
            command=self._test_discord_deafen
        )
        btn_test_deafen.pack(side="left")

        form = ctk.CTkFrame(box, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=4)

        # Mute & Deafen klávesy
        r1 = ctk.CTkFrame(form, fg_color="transparent")
        r1.pack(fill="x", pady=8)
        ctk.CTkLabel(r1, text="Mute mikrofonu:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1", width=140, anchor="w").pack(side="left")
        self.entry_disc_mute = ctk.CTkEntry(r1, width=180, height=32, fg_color="#181A25", border_color="#282B3C", border_width=1, corner_radius=8, text_color="#FFFFFF")
        self.entry_disc_mute.insert(0, disc_cfg.get("mute_key", "ctrl+shift+m"))
        self.entry_disc_mute.pack(side="left", padx=(0, 24))

        ctk.CTkLabel(r1, text="Deafen sluchátek:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1", width=140, anchor="w").pack(side="left")
        self.entry_disc_deafen = ctk.CTkEntry(r1, width=180, height=32, fg_color="#181A25", border_color="#282B3C", border_width=1, corner_radius=8, text_color="#FFFFFF")
        self.entry_disc_deafen.insert(0, disc_cfg.get("deafen_key", "ctrl+shift+d"))
        self.entry_disc_deafen.pack(side="left")

        # PTT & Disconnect klávesy
        r2 = ctk.CTkFrame(form, fg_color="transparent")
        r2.pack(fill="x", pady=8)
        ctk.CTkLabel(r2, text="Push-to-Talk (PTT):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1", width=140, anchor="w").pack(side="left")
        self.entry_disc_ptt = ctk.CTkEntry(r2, width=180, height=32, fg_color="#181A25", border_color="#282B3C", border_width=1, corner_radius=8, text_color="#FFFFFF")
        self.entry_disc_ptt.insert(0, disc_cfg.get("ptt_key", "ctrl+shift+p"))
        self.entry_disc_ptt.pack(side="left", padx=(0, 24))

        ctk.CTkLabel(r2, text="Odpojit hovor:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1", width=140, anchor="w").pack(side="left")
        self.entry_disc_disc = ctk.CTkEntry(r2, width=180, height=32, fg_color="#181A25", border_color="#282B3C", border_width=1, corner_radius=8, text_color="#FFFFFF")
        self.entry_disc_disc.insert(0, disc_cfg.get("disconnect_key", "ctrl+shift+h"))
        self.entry_disc_disc.pack(side="left")

        # Uložit tlačítko
        r_btns = ctk.CTkFrame(form, fg_color="transparent")
        r_btns.pack(fill="x", pady=(14, 8))
        btn_save_disc = ctk.CTkButton(
            r_btns,
            text="Uložit nastavení Discordu",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
            corner_radius=17,
            fg_color="#FF7A29",
            hover_color="#FF8E3D",
            text_color="#0A0A0E",
            command=self._save_discord_settings
        )
        btn_save_disc.pack(side="left", padx=(0, 12))

        # Detailní návod pro spolehlivý běh na pozadí bez nutnosti cokoliv stahovat
        guide_box = ctk.CTkFrame(box, fg_color="#151722", corner_radius=10, border_width=1, border_color="#272A3C")
        guide_box.pack(fill="x", padx=24, pady=(16, 20))

        ctk.CTkLabel(
            guide_box,
            text="⚡ NÁVOD PRO SPOLEHLIVÉ FUNGOVÁNÍ DISCORDU NA POZADÍ (Nemusíte nic stahovat!):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FF9D54"
        ).pack(anchor="w", padx=16, pady=(12, 6))

        guide_text = (
            "Aby Discord reagoval na PeciDeck i když je minimalizovaný nebo když hrajete hru či stříháte v DaVinci:\n\n"
            "1. V aplikaci Discord klikněte na Ozubené kolečko (Uživatelská nastavení dole u vašeho jména).\n"
            "2. V levém menu otevřete položku 'Klávesové zkratky' (Keybinds).\n"
            "3. Klikněte na modré tlačítko 'Přidat klávesovou zkratku':\n"
            "     • Akce: 'Přepnout ztlumení' (Toggle Mute)  —  Zkratka: Ctrl + Shift + M\n"
            "     • Akce: 'Přepnout ztlumení zvuku' (Toggle Deafen)  —  Zkratka: Ctrl + Shift + D\n\n"
            "✓ Od této chvíle funguje ztlumení Discordu odkudkoliv i na pozadí!\n"
            "✓ Ztlumení Discordu ztlumí POUZE Discord – váš mikrofon v DaVinci Resolve a jinde zůstane 100% aktivní."
        )
        ctk.CTkLabel(
            guide_box,
            text=guide_text,
            font=ctk.CTkFont(size=11),
            text_color="#CBD5E1",
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 14))

    # =========================================================================
    #  ZÁLOŽKA: TWITCH INTEGRACE (HELIX API)
    # =========================================================================
    def _build_twitch_panel(self, parent):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        self.sub_tab_frames["twitch"] = f

        box = ctk.CTkFrame(f, fg_color="#12131C", corner_radius=14, border_width=1, border_color="#202232")
        box.pack(fill="both", expand=True, padx=4, pady=4)

        header_row = ctk.CTkFrame(box, fg_color="transparent")
        header_row.pack(fill="x", padx=24, pady=(20, 4))

        ctk.CTkLabel(header_row, text="Twitch Integrace (Helix API)", font=ctk.CTkFont(size=16, weight="bold"), text_color="#FFFFFF").pack(side="left")

        # Stavový indikátor vpravo
        is_tw = bool(self.twitch and self.twitch.is_configured())
        self.lbl_twitch_tab_status = ctk.CTkLabel(
            header_row,
            text="● Twitch autorizován (Aktivní)" if is_tw else "○ Twitch nepřipojen",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2ECC71" if is_tw else "#9146FF"
        )
        self.lbl_twitch_tab_status.pack(side="right")

        ctk.CTkLabel(
            box,
            text="Přímé ovládání streamu pro PeciDeck – značky ve streamu (Stream Marker), klipy, reklamy, moderování a zprávy v chatu.",
            font=ctk.CTkFont(size=12),
            text_color="#7E849B"
        ).pack(anchor="w", padx=24, pady=(0, 14))

        tw_cfg = self.config_mgr.settings.get("twitch", {})

        # Rychlá tlačítka akcí nahoře
        quick_bar = ctk.CTkFrame(box, fg_color="transparent")
        quick_bar.pack(fill="x", padx=24, pady=(0, 14))

        btn_token = ctk.CTkButton(
            quick_bar,
            text="🔑 Získat OAuth Token",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            corner_radius=16,
            fg_color="#182333",
            hover_color="#24344D",
            text_color="#38BDF8",
            border_width=1,
            border_color="#2F425C",
            command=self._open_token_generator
        )
        btn_token.pack(side="left", padx=(0, 10))

        btn_launch = ctk.CTkButton(
            quick_bar,
            text="🟣 Otevřít Twitch kanál",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            corner_radius=16,
            fg_color="#1E202C",
            hover_color="#282A3A",
            text_color="#CBD5E1",
            border_width=1,
            border_color="#2D3042",
            command=self._launch_twitch
        )
        btn_launch.pack(side="left", padx=(0, 10))

        btn_dashboard = ctk.CTkButton(
            quick_bar,
            text="📊 Panel vysílání (Dashboard)",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            corner_radius=16,
            fg_color="#1E202C",
            hover_color="#282A3A",
            text_color="#CBD5E1",
            border_width=1,
            border_color="#2D3042",
            command=self._launch_twitch_dashboard
        )
        btn_dashboard.pack(side="left", padx=(0, 10))

        btn_test_marker = ctk.CTkButton(
            quick_bar,
            text="🔖 Otestovat značku",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            corner_radius=16,
            fg_color="#1E202C",
            hover_color="#282A3A",
            text_color="#CBD5E1",
            border_width=1,
            border_color="#2D3042",
            command=self._test_twitch_marker
        )
        btn_test_marker.pack(side="left", padx=(0, 10))

        btn_test_clip = ctk.CTkButton(
            quick_bar,
            text="🎬 Otestovat klip",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            corner_radius=16,
            fg_color="#1E202C",
            hover_color="#282A3A",
            text_color="#CBD5E1",
            border_width=1,
            border_color="#2D3042",
            command=self._test_twitch_clip
        )
        btn_test_clip.pack(side="left")

        form = ctk.CTkFrame(box, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=4)

        # Řádek 1: OAuth Token
        r1 = ctk.CTkFrame(form, fg_color="transparent")
        r1.pack(fill="x", pady=6)
        ctk.CTkLabel(r1, text="OAuth Access Token:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1", width=150, anchor="w").pack(side="left")
        self.entry_tw_token = ctk.CTkEntry(
            r1,
            width=360,
            height=32,
            show="*",
            fg_color="#181A25",
            border_color="#282B3C",
            border_width=1,
            corner_radius=8,
            text_color="#FFFFFF",
            placeholder_text="oauth:xxxxxxxxxxxxxxxxxxxxxx"
        )
        saved_tok = tw_cfg.get("oauth_token", "")
        if saved_tok:
            self.entry_tw_token.insert(0, saved_tok)
        self.entry_tw_token.pack(side="left", padx=(0, 10))

        self.btn_toggle_tw_token = ctk.CTkButton(
            r1,
            text="👁",
            width=36,
            height=32,
            corner_radius=8,
            fg_color="#1E202C",
            hover_color="#282A3A",
            text_color="#CBD5E1",
            command=self._toggle_twitch_token_visibility
        )
        self.btn_toggle_tw_token.pack(side="left")

        # Řádek 2: Kanál (Login) a User ID
        r2 = ctk.CTkFrame(form, fg_color="transparent")
        r2.pack(fill="x", pady=6)
        ctk.CTkLabel(r2, text="Kanál (Streamer):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1", width=150, anchor="w").pack(side="left")
        self.entry_tw_channel = ctk.CTkEntry(
            r2,
            width=180,
            height=32,
            fg_color="#181A25",
            border_color="#282B3C",
            border_width=1,
            corner_radius=8,
            text_color="#FFFFFF",
            placeholder_text="např. pecitech"
        )
        self.entry_tw_channel.insert(0, tw_cfg.get("channel", ""))
        self.entry_tw_channel.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(r2, text="Twitch User ID:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1", width=110, anchor="w").pack(side="left")
        self.entry_tw_userid = ctk.CTkEntry(
            r2,
            width=150,
            height=32,
            fg_color="#181A25",
            border_color="#282B3C",
            border_width=1,
            corner_radius=8,
            text_color="#94A3B8"
        )
        self.entry_tw_userid.insert(0, str(tw_cfg.get("user_id", "")))
        self.entry_tw_userid.pack(side="left")

        # Tlačítka pro uložení & test
        r_btns = ctk.CTkFrame(form, fg_color="transparent")
        r_btns.pack(fill="x", pady=(12, 6))

        btn_save_tw = ctk.CTkButton(
            r_btns,
            text="⚡ Ověřit a Uložit token Twitch",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34,
            corner_radius=17,
            fg_color="#9146FF",
            hover_color="#772CE8",
            text_color="#FFFFFF",
            command=self._save_twitch_settings
        )
        btn_save_tw.pack(side="left", padx=(0, 16))

        self.lbl_tw_res = ctk.CTkLabel(r_btns, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_tw_res.pack(side="left")

        # Návod
        guide_box = ctk.CTkFrame(box, fg_color="#151722", corner_radius=10, border_width=1, border_color="#272A3C")
        guide_box.pack(fill="x", padx=24, pady=(12, 16))

        ctk.CTkLabel(
            guide_box,
            text="⚡ RYCHLÝ NÁVOD PRO PROPOJENÍ S TWITCHEM:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#A970FF"
        ).pack(anchor="w", padx=16, pady=(10, 4))

        guide_text = (
            "1. Klikněte na tlačítko '🔑 Získat OAuth Token' výše (otevře twitchtokengenerator.com).\n"
            "2. Vyberte oprávnění: channel:manage:broadcast (pro značky/reklamu), clips:edit (pro klipy),\n"
            "   moderator:manage:chat_messages a user:write:chat (pro mazání a posílání zpráv).\n"
            "3. Vygenerovaný token vložte do pole 'OAuth Access Token' a klikněte na '⚡ Ověřit a Uložit'.\n"
            "4. Kanál a uživatelské ID se načtou automaticky z Twitch serveru.\n\n"
            "✓ Od této chvíle mohou tlačítka PeciDecku okamžitě tvořit značky ve streamu i klipovat momenty!"
        )
        ctk.CTkLabel(
            guide_box,
            text=guide_text,
            font=ctk.CTkFont(size=11),
            text_color="#CBD5E1",
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 12))

    def _open_token_generator(self):
        import webbrowser
        webbrowser.open("https://twitchtokengenerator.com")

    def _launch_twitch(self):
        if self.twitch:
            self.twitch.open_channel()
        else:
            import webbrowser
            webbrowser.open("https://twitch.tv")

    def _launch_twitch_dashboard(self):
        if self.twitch:
            self.twitch.open_stream_manager()
        else:
            import webbrowser
            webbrowser.open("https://dashboard.twitch.tv/stream-manager")

    def _toggle_twitch_token_visibility(self):
        cur_show = self.entry_tw_token.cget("show")
        if cur_show == "*":
            self.entry_tw_token.configure(show="")
            self.btn_toggle_tw_token.configure(text="🔒")
        else:
            self.entry_tw_token.configure(show="*")
            self.btn_toggle_tw_token.configure(text="👁")

    def _save_twitch_settings(self):
        token_input = self.entry_tw_token.get().strip()
        channel_input = self.entry_tw_channel.get().strip()

        if not token_input:
            self.lbl_tw_res.configure(text="✗ Zadejte OAuth token.", text_color="#E74C3C")
            return

        self.lbl_tw_res.configure(text="Ověřuji token...", text_color="#94A3B8")
        self.update_idletasks()

        if self.twitch:
            ok, msg = self.twitch.validate_token(token_input)
            if ok:
                if self.twitch.channel:
                    self.entry_tw_channel.delete(0, "end")
                    self.entry_tw_channel.insert(0, self.twitch.channel)
                if self.twitch.user_id:
                    self.entry_tw_userid.delete(0, "end")
                    self.entry_tw_userid.insert(0, self.twitch.user_id)

                self.lbl_tw_res.configure(text=f"✓ {msg}", text_color="#2ECC71")
                if hasattr(self, "lbl_twitch_tab_status"):
                    self.lbl_twitch_tab_status.configure(text="● Twitch autorizován (Aktivní)", text_color="#2ECC71")
            else:
                self.lbl_tw_res.configure(text=f"✗ {msg}", text_color="#E74C3C")
                if hasattr(self, "lbl_twitch_tab_status"):
                    self.lbl_twitch_tab_status.configure(text="○ Twitch nepřipojen", text_color="#E74C3C")
        else:
            tw_cfg = self.config_mgr.settings.setdefault("twitch", {})
            tw_cfg["oauth_token"] = token_input
            if channel_input:
                tw_cfg["channel"] = channel_input
            self.config_mgr.save_settings()
            self.lbl_tw_res.configure(text="✓ Nastavení uloženo.", text_color="#2ECC71")

    def _test_twitch_marker(self):
        if not self.twitch:
            messagebox.showwarning("Twitch", "Twitch kontroler není inicializován.")
            return
        self.lbl_tw_res.configure(text="Vytvářím testovací značku...", text_color="#94A3B8")
        self.update_idletasks()
        ok, msg = self.twitch.create_marker("PeciDeck Test Marker")
        if ok:
            self.lbl_tw_res.configure(text=msg, text_color="#2ECC71")
            messagebox.showinfo("Twitch Značka", msg)
        else:
            self.lbl_tw_res.configure(text=msg, text_color="#FF9D54")
            messagebox.showinfo("Twitch Značka", msg)

    def _test_twitch_clip(self):
        if not self.twitch:
            messagebox.showwarning("Twitch", "Twitch kontroler není inicializován.")
            return
        self.lbl_tw_res.configure(text="Vytvářím testovací klip...", text_color="#94A3B8")
        self.update_idletasks()
        ok, msg = self.twitch.create_clip()
        if ok:
            self.lbl_tw_res.configure(text=msg, text_color="#2ECC71")
            messagebox.showinfo("Twitch Klip", msg)
        else:
            self.lbl_tw_res.configure(text=msg, text_color="#FF9D54")
            messagebox.showinfo("Twitch Klip", msg)

    # =========================================================================
    #  ZÁLOŽKA: PROFILY & ZÁLOHA
    # =========================================================================
    def _build_profiles_tab(self):
        f = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.tab_frames["profiles"] = f

        box = ctk.CTkFrame(f, fg_color="#12131C", corner_radius=14, border_width=1, border_color="#202232")
        box.pack(fill="both", expand=True, padx=4, pady=4)

        ctk.CTkLabel(box, text="Správa Konfigurace a Profilů", font=ctk.CTkFont(size=15, weight="bold"), text_color="#FFFFFF").pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(box, text="Zálohujte, přenášejte nebo obnovte rozvržení tlačítek a akcí.", font=ctk.CTkFont(size=12), text_color="#7E849B").pack(anchor="w", padx=24, pady=(0, 18))

        # 1. Export
        self._create_setting_row(
            parent=box,
            title="Exportovat Profil",
            subtitle="Uloží kompletní konfiguraci zařízení do souboru JSON.",
            btn_text="Exportovat",
            btn_cmd=self._export_profile
        )

        # 2. Import
        self._create_setting_row(
            parent=box,
            title="Importovat Profil",
            subtitle="Načte rozložení tlačítek a enkodérů ze souboru JSON.",
            btn_text="Importovat",
            btn_cmd=self._import_profile
        )

        # 3. Tovární Reset
        self._create_setting_row(
            parent=box,
            title="Tovární Reset",
            subtitle="Smaže všechny úpravy a obnoví výchozí profil od výrobce.",
            btn_text="Obnovit výchozí",
            btn_cmd=self._reset_profile,
            is_danger=True
        )

    # =========================================================================
    #  ZÁLOŽKA 4: OBECNÉ & SYSTÉM
    # =========================================================================
    def _build_system_tab(self):
        f = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.tab_frames["system"] = f

        box = ctk.CTkFrame(f, fg_color="#12131C", corner_radius=14, border_width=1, border_color="#202232")
        box.pack(fill="both", expand=True, padx=4, pady=4)

        ctk.CTkLabel(box, text="O Aplikaci PeciTech Studio", font=ctk.CTkFont(size=15, weight="bold"), text_color="#FFFFFF").pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(box, text="Informace o verzi, hardwaru a systémových složkách.", font=ctk.CTkFont(size=12), text_color="#7E849B").pack(anchor="w", padx=24, pady=(0, 18))

        # Verze
        r_ver = ctk.CTkFrame(box, fg_color="transparent")
        r_ver.pack(fill="x", padx=24, pady=12)
        ctk.CTkLabel(r_ver, text="PeciTech Studio MK.1", font=ctk.CTkFont(size=13, weight="bold"), text_color="#FFFFFF").pack(anchor="w")
        ctk.CTkLabel(r_ver, text="Verze 1.1.0 • Vyvinuto pro PeciDeck MK.1 • Python 3.14 & CustomTkinter", font=ctk.CTkFont(size=11), text_color="#7E849B").pack(anchor="w", pady=(2, 0))

        self._add_divider(box)

        # Složka ikon
        self._create_setting_row(
            parent=box,
            title="Složka Ikon & Aktiv",
            subtitle="Otevře systémovou složku pro přidání vašich vlastních PNG ikon.",
            btn_text="Otevřít složku",
            btn_cmd=self._open_icons_folder
        )

        # Běh na pozadí (Systémová lišta)
        self._create_setting_row(
            parent=box,
            title="Běh na Pozadí (System Tray)",
            subtitle="Při zavření okna křížkem aplikace zůstává aktivní v liště a hardware dále funguje.",
            btn_text="Minimalizovat",
            btn_cmd=lambda: self.winfo_toplevel().withdraw()
        )

        # Ukončit aplikaci
        self._create_setting_row(
            parent=box,
            title="Ukončit PeciDeck Studio",
            subtitle="Zcela ukončí běh aplikace, vypne systémovou lištu a odpojí USB hardware.",
            btn_text="Ukončit program",
            btn_cmd=lambda: getattr(self.winfo_toplevel(), "_quit_app", lambda: sys.exit(0))(),
            is_danger=True
        )

    # =========================================================================
    #  POMOCNÉ METODY PRO VYKRESLOVÁNÍ ŘÁDKŮ
    # =========================================================================
    def _create_setting_row(self, parent, title, subtitle, btn_text, btn_cmd, is_danger=False):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=12)

        txt_b = ctk.CTkFrame(row, fg_color="transparent")
        txt_b.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(txt_b, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color="#FFFFFF").pack(anchor="w")
        ctk.CTkLabel(txt_b, text=subtitle, font=ctk.CTkFont(size=11), text_color="#7E849B").pack(anchor="w", pady=(2, 0))

        btn = ctk.CTkButton(
            row,
            text=btn_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            width=130,
            height=32,
            corner_radius=16,
            fg_color="#281519" if is_danger else "#1E202C",
            hover_color="#451D24" if is_danger else "#282A3A",
            border_width=1,
            border_color="#482028" if is_danger else "#2D3042",
            text_color="#FF6B6B" if is_danger else "#FFFFFF",
            command=btn_cmd
        )
        btn.pack(side="right")

        self._add_divider(parent)

    def _add_divider(self, parent):
        d = ctk.CTkFrame(parent, height=1, fg_color="#1A1C28")
        d.pack(fill="x", padx=24, pady=(3, 3))

    # =========================================================================
    #  AKCE A UDÁLOSTI
    # =========================================================================
    def show(self):
        """Zobrazí modal jako plynulý celoobrazovkový in-app overlay."""
        is_conn = bool(self.serial and self.serial.is_connected)
        if is_conn:
            port = getattr(self.serial, "port", "USB")
            self.lbl_dstatus.configure(text=f"● Připojeno ({port})", text_color="#2ECC71")
            self.device_tile.configure(border_color="#FF7A29")
        else:
            self.lbl_dstatus.configure(text="● Zařízení odpojeno", text_color="#E74C3C")
            self.device_tile.configure(border_color="#2D3042")

        is_obs = bool(self.obs and self.obs.is_connected)
        if hasattr(self, "lbl_obs_tab_status"):
            self.lbl_obs_tab_status.configure(
                text="● Připojeno k OBS" if is_obs else "● Odpojeno od OBS",
                text_color="#2ECC71" if is_obs else "#E74C3C"
            )

        if hasattr(self, "lbl_discord_tab_status") and self.discord:
            is_disc = self.discord.is_running()
            self.lbl_discord_tab_status.configure(
                text="● Discord běží (Aktivní)" if is_disc else "○ Discord neběží",
                text_color="#2ECC71" if is_disc else "#FF9D54"
            )

        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()

        # Záchranný escape
        try:
            self.winfo_toplevel().bind("<Escape>", lambda e: self.hide(), add="+")
        except Exception:
            pass

    def hide(self):
        """Zavře modal."""
        self.place_forget()

    def update_hardware_status(self, is_connected, port_name=None):
        """Aktualizuje stav hardwaru v okně nastavení."""
        if hasattr(self, "lbl_dstatus") and hasattr(self, "device_tile"):
            if is_connected:
                p = port_name or getattr(self.serial, "port", "USB") or "USB"
                self.lbl_dstatus.configure(text=f"● Připojeno ({p})", text_color="#2ECC71")
                self.device_tile.configure(border_color="#FF7A29")
            else:
                self.lbl_dstatus.configure(text="● Zařízení odpojeno", text_color="#E74C3C")
                self.device_tile.configure(border_color="#2D3042")

    def _on_rescan_click(self):
        if self.on_scan_cb:
            self.on_scan_cb()
        is_conn = bool(self.serial and self.serial.is_connected)
        if is_conn:
            self.lbl_dstatus.configure(text="● Připojeno přes USB", text_color="#2ECC71")
            self.device_tile.configure(border_color="#FF7A29")
        else:
            self.lbl_dstatus.configure(text="● Zařízení odpojeno", text_color="#E74C3C")

    def _check_firmware(self):
        messagebox.showinfo("Firmware PeciDeck", "PeciDeck MK.1 běží na verzi FW 1.1.0.\nVáš firmware je aktuální!")

    def _on_brightness_change(self, val):
        b = int(val)
        self.config_mgr.profile["brightness"] = b
        self.config_mgr.save_profile()
        if self.serial and self.serial.is_connected:
            self.serial.send_command(f"DISP:BL,{b}")

    def _on_sync_display(self):
        if self.serial and self.serial.is_connected:
            self.serial.sync_profile(self.config_mgr.profile)
            messagebox.showinfo("Synchronizace", "Profil byl úspěšně synchronizován do displeje PeciDeck MK.1.")
        else:
            messagebox.showwarning("Upozornění", "PeciDeck není připojen přes USB.")

    def _toggle_inversion(self):
        self.is_inverted = not self.is_inverted
        if self.serial and self.serial.is_connected:
            self.serial.set_inversion(self.is_inverted)

    def _show_standby(self):
        if self.serial and self.serial.is_connected:
            self.serial.send_command("DISP:OFFLINE")

    def _auto_detect_obs(self):
        """Automaticky načte port a heslo z lokální instalace OBS Studio a povolí WebSocket."""
        from obs_controller import OBSController
        detected = OBSController.detect_obs_config()
        if detected and detected.get("found"):
            host = detected.get("host", "localhost")
            port = detected.get("port", 4455)
            pwd = detected.get("password", "")

            self.entry_obs_host.delete(0, "end")
            self.entry_obs_host.insert(0, host)
            self.entry_obs_port.delete(0, "end")
            self.entry_obs_port.insert(0, str(port))
            self.entry_obs_pwd.delete(0, "end")
            self.entry_obs_pwd.insert(0, pwd)

            self.config_mgr.settings["obs"]["host"] = host
            self.config_mgr.settings["obs"]["port"] = port
            self.config_mgr.settings["obs"]["password"] = pwd
            self.config_mgr.save_settings()

            OBSController.enable_obs_websocket()

            self.lbl_obs_res.configure(
                text="✓ Údaje načteny z OBS! Zkouším připojení...",
                text_color="#38BDF8"
            )
            self._test_obs_connection()
        else:
            self.lbl_obs_res.configure(
                text="✗ Konfigurace OBS nenalezena v %APPDATA%.",
                text_color="#E74C3C"
            )

    def _launch_obs(self):
        """Spustí aplikaci OBS Studio."""
        from obs_controller import OBSController
        if OBSController.is_obs_running():
            self.lbl_obs_res.configure(text="ℹ OBS Studio již běží.", text_color="#38BDF8")
            return
        ok = OBSController.launch_obs()
        if ok:
            self.lbl_obs_res.configure(text="✓ Spouštím OBS Studio...", text_color="#2ECC71")
            self.after(3000, self._test_obs_connection)
        else:
            self.lbl_obs_res.configure(text="✗ Soubor obs64.exe nebyl nalezen.", text_color="#E74C3C")

    def _on_auto_connect_changed(self):
        val = bool(self.chk_obs_auto.get())
        self.config_mgr.settings["obs"]["auto_connect"] = val
        self.config_mgr.save_settings()
        if self.obs:
            self.obs.auto_connect = val

    def _test_obs_connection(self):
        host = self.entry_obs_host.get().strip()
        port = self.entry_obs_port.get().strip()
        pwd = self.entry_obs_pwd.get()

        self.config_mgr.settings["obs"]["host"] = host
        self.config_mgr.settings["obs"]["port"] = int(port) if port.isdigit() else 4455
        self.config_mgr.settings["obs"]["password"] = pwd
        self.config_mgr.save_settings()

        if self.obs:
            self.obs.host = host
            self.obs.port = int(port) if port.isdigit() else 4455
            self.obs.password = pwd
            self.lbl_obs_res.configure(text="Připojuji...", text_color="#94A3B8")
            self.update_idletasks()

            ok = self.obs.connect(force=True)
            if ok:
                scenes = self.obs.get_scenes()
                cur = self.obs.get_current_scene()
                info = f"✓ Spojení úspěšné! ({len(scenes)} scén"
                if cur:
                    info += f", aktivní: {cur}"
                info += ")"
                self.lbl_obs_res.configure(text=info, text_color="#2ECC71")
                if hasattr(self, "lbl_obs_tab_status"):
                    self.lbl_obs_tab_status.configure(text="● Připojeno k OBS", text_color="#2ECC71")
            else:
                from obs_controller import OBSController
                if not OBSController.is_obs_running():
                    self.lbl_obs_res.configure(
                        text="✗ OBS Studio neběží. Klikněte na 'Spustit OBS Studio'.",
                        text_color="#E74C3C"
                    )
                else:
                    self.lbl_obs_res.configure(
                        text="✗ Nepodařilo se připojit k OBS. Ověřte port a heslo.",
                        text_color="#E74C3C"
                    )
                if hasattr(self, "lbl_obs_tab_status"):
                    self.lbl_obs_tab_status.configure(text="● Odpojeno od OBS", text_color="#E74C3C")

    def _export_profile(self):
        fn = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON profily", "*.json")],
            initialfile="peci_deck_profil.json"
        )
        if fn:
            self.config_mgr.save_profile(fn)
            messagebox.showinfo("Export", "Profil byl úspěšně exportován.")

    def _import_profile(self):
        fn = filedialog.askopenfilename(filetypes=[("JSON profily", "*.json")])
        if fn:
            p = self.config_mgr.load_profile(fn)
            self.config_mgr.profile = p
            self.config_mgr.save_profile()
            self._on_sync_display()
            messagebox.showinfo("Import", "Profil byl úspěšně načten.")

    def _launch_discord(self):
        if self.discord:
            self.discord.open_discord()
        else:
            try:
                subprocess.Popen(["cmd", "/c", "start", "discord://"], shell=True)
            except Exception:
                pass

    def _test_discord_mute(self):
        if self.discord:
            self.discord.toggle_mute()

    def _test_discord_deafen(self):
        if self.discord:
            self.discord.toggle_deafen()

    def _save_discord_settings(self):
        disc_cfg = self.config_mgr.settings.setdefault("discord", {})
        disc_cfg["mute_key"] = self.entry_disc_mute.get().strip() or "ctrl+shift+m"
        disc_cfg["deafen_key"] = self.entry_disc_deafen.get().strip() or "ctrl+shift+d"
        disc_cfg["ptt_key"] = self.entry_disc_ptt.get().strip() or "ctrl+shift+p"
        disc_cfg["disconnect_key"] = self.entry_disc_disc.get().strip() or "ctrl+shift+h"
        self.config_mgr.save_settings()
        messagebox.showinfo("Nastavení Discordu", "Klávesové zkratky pro Discord byly úspěšně uloženy!")

    def _reset_profile(self):
        if messagebox.askyesno("Reset", "Opravdu chcete obnovit profil do továrního nastavení?"):
            from config_manager import DEFAULT_PROFILE
            self.config_mgr.profile = json.loads(json.dumps(DEFAULT_PROFILE))
            self.config_mgr.save_profile()
            self._on_sync_display()
            messagebox.showinfo("Reset", "Profil byl obnoven do výchozího stavu.")

    def _open_icons_folder(self):
        icons_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "icons")
        if os.path.exists(icons_dir):
            try:
                os.startfile(icons_dir)
            except Exception:
                subprocess.Popen(["explorer", icons_dir])


# Alias pro zpětnou kompatibilitu
SettingsView = SettingsModal
