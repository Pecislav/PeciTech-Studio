import os
import customtkinter as ctk
from PIL import Image
from assets_manager import get_asset_icon

LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "Logo", "PeciTech_logo_transparent.png")
if not os.path.exists(LOGO_PATH):
    LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "Logo", "PeciTech_logo_aplikace.png")

class DashboardView(ctk.CTkFrame):
    """
    Úvodní obrazovka aplikace PeciTech Studio:
    - Záhlaví s logem "PeciTech STUDIO" a ikonou nastavení
    - Kompaktní a elegantní karta zařízení PeciDeck MK.1
    - Věrná, proporčně vyvážená maketa zařízení (bez zbytečného černého prázdného prostoru)
    - Čisté rotační enkodéry (reálné otočné knoflíky z assets, žádný vykřičník)
    """
    def __init__(self, parent, serial_bridge, on_configure_cb, on_scan_cb, on_settings_cb):
        super().__init__(parent, fg_color="transparent")
        self.serial = serial_bridge
        self.on_configure_cb = on_configure_cb
        self.on_scan_cb = on_scan_cb
        self.on_settings_cb = on_settings_cb

        self._logo_image = None
        self._load_logo()
        self._build_ui()

    def _load_logo(self):
        try:
            if os.path.exists(LOGO_PATH):
                pil_img = Image.open(LOGO_PATH).convert("RGBA")
                self._logo_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(28, 28))
        except Exception:
            self._logo_image = None

    def _build_ui(self):
        # 1. Horní lišta s logem a ikonou nastavení
        top_bar = ctk.CTkFrame(self, fg_color="transparent", height=46)
        top_bar.pack(fill="x", padx=36, pady=(18, 6))

        brand_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        brand_frame.pack(side="left")

        if self._logo_image:
            lbl_logo = ctk.CTkLabel(brand_frame, image=self._logo_image, text="")
            lbl_logo.pack(side="left", padx=(0, 10))

        lbl_brand = ctk.CTkLabel(
            brand_frame, 
            text="PeciTech", 
            font=ctk.CTkFont(size=24, weight="bold"), 
            text_color="#FFFFFF"
        )
        lbl_brand.pack(side="left")

        lbl_badge = ctk.CTkLabel(
            brand_frame,
            text=" STUDIO ",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#FF7A29",
            fg_color="#241812",
            corner_radius=4
        )
        lbl_badge.pack(side="left", padx=(10, 0), pady=(3, 0))

        gear_ico = get_asset_icon("gear", size=(18, 18))
        btn_settings = ctk.CTkButton(
            top_bar,
            image=gear_ico,
            text="",
            width=38,
            height=38,
            corner_radius=19,
            fg_color="#181922",
            hover_color="#252737",
            border_width=1,
            border_color="#282A3A",
            command=self.on_settings_cb
        )
        btn_settings.pack(side="right")

        # Indikátor OBS Studio
        self.btn_obs_status = ctk.CTkButton(
            top_bar,
            text="● OBS: Odpojeno",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#E74C3C",
            fg_color="#201316",
            hover_color="#2E181D",
            border_width=1,
            border_color="#3D1D22",
            corner_radius=15,
            height=30,
            width=120,
            command=self.on_settings_cb
        )
        self.btn_obs_status.pack(side="right", padx=(0, 12))

        # 2. Nadpisy sekce
        lbl_title = ctk.CTkLabel(
            self, 
            text="Moje Zařízení", 
            font=ctk.CTkFont(size=28, weight="bold"), 
            text_color="#FFFFFF"
        )
        lbl_title.pack(anchor="w", padx=36, pady=(10, 2))

        lbl_sub = ctk.CTkLabel(
            self, 
            text="Spravujte a přizpůsobte si svá zařízení.", 
            font=ctk.CTkFont(size=14), 
            text_color="#7E849B"
        )
        lbl_sub.pack(anchor="w", padx=36, pady=(0, 18))

        # 3. Vycentrovaný kontejner pro kartu PeciDeck MK.1
        cards_container = ctk.CTkFrame(self, fg_color="transparent")
        cards_container.pack(fill="both", expand=True, padx=36, pady=(0, 24))

        # KARTA: Kompaktní a proporční PeciDeck MK.1
        self.card_deck = ctk.CTkFrame(
            cards_container, 
            width=480,
            height=380,
            fg_color="#13141C", 
            corner_radius=16, 
            border_width=1, 
            border_color="#242738"
        )
        self.card_deck.pack_propagate(False)
        self.card_deck.pack(expand=True)

        self._build_deck_card_content()

    def _build_deck_card_content(self):
        # Vnitřní rámeček vizualizace zařízení (přesně padnoucí, bez zbytečné černé prázdnoty)
        vis_frame = ctk.CTkFrame(self.card_deck, fg_color="#090A0D", corner_radius=12, border_width=1, border_color="#181A22")
        vis_frame.pack(fill="both", expand=True, padx=16, pady=(16, 12))

        # Šasi hardware makety PeciDeck MK.1
        deck_mock = ctk.CTkFrame(vis_frame, fg_color="#14151E", corner_radius=14, border_width=1, border_color="#252838")
        deck_mock.pack(expand=True, padx=12, pady=10)

        # 1. HORNÍ ČÁST: 8 KLÁVES CHERRY MX (4 sloupce x 2 řádky)
        keys_grid = ctk.CTkFrame(deck_mock, fg_color="transparent")
        keys_grid.pack(padx=14, pady=(12, 6))

        for r in range(2):
            for c in range(4):
                k = ctk.CTkFrame(
                    keys_grid, 
                    width=42, 
                    height=42, 
                    corner_radius=8, 
                    fg_color="#1B1C27", 
                    border_width=1, 
                    border_color="#2C3042"
                )
                k.pack_propagate(False)
                k.grid(row=r, column=c, padx=3, pady=3)

        # 2. STŘEDNÍ ČÁST: ST7789 IPS DISPLEJ 284x76 (Čistý realistický rámeček bez svícení)
        disp_frame = ctk.CTkFrame(
            deck_mock, 
            width=188, 
            height=36, 
            corner_radius=5, 
            fg_color="#040406", 
            border_width=1, 
            border_color="#222534"
        )
        disp_frame.pack_propagate(False)
        disp_frame.pack(padx=14, pady=(0, 8))

        disp_grid = ctk.CTkFrame(disp_frame, fg_color="transparent")
        disp_grid.place(relx=0.5, rely=0.5, anchor="center")

        for r in range(2):
            for c in range(4):
                idx = r * 4 + c + 1
                cell = ctk.CTkFrame(
                    disp_grid, 
                    width=42, 
                    height=13, 
                    corner_radius=2, 
                    fg_color="#000000", 
                    border_width=1, 
                    border_color="#181A24"
                )
                cell.pack_propagate(False)
                cell.grid(row=r, column=c, padx=1, pady=1)

                lbl_n = ctk.CTkLabel(
                    cell, 
                    text=str(idx), 
                    font=ctk.CTkFont(size=9, weight="bold"), 
                    text_color="#64748B"
                )
                lbl_n.place(relx=0.5, rely=0.5, anchor="center")

        # 3. DOLNÍ ČÁST: 3 OTOČNÉ ENKODÉRY (Vygenerovaný čistý rotary dial bez vykřičníku!)
        encs_frame = ctk.CTkFrame(deck_mock, fg_color="transparent")
        encs_frame.pack(padx=14, pady=(0, 12))

        knob_img = get_asset_icon("knob_dial", size=(34, 34))

        for i in range(3):
            dial = ctk.CTkFrame(encs_frame, fg_color="transparent")
            dial.pack(side="left", padx=14)

            if knob_img:
                lbl_knob = ctk.CTkLabel(dial, image=knob_img, text="")
                lbl_knob.pack()
            else:
                knob_box = ctk.CTkFrame(dial, width=34, height=34, corner_radius=17, fg_color="#181A24", border_width=2, border_color="#353A4E")
                knob_box.pack_propagate(False)
                knob_box.pack()
                tick = ctk.CTkFrame(knob_box, width=3, height=8, corner_radius=1, fg_color="#FF7A29", border_width=0)
                tick.place(relx=0.5, rely=0.20, anchor="center")

        # 4. DOLNÍ LIŠTA KARTY: Název, stav připojení a tlačítko Konfigurovat
        info_frame = ctk.CTkFrame(self.card_deck, fg_color="transparent")
        info_frame.pack(fill="x", padx=18, pady=(0, 14))

        f_left = ctk.CTkFrame(info_frame, fg_color="transparent")
        f_left.pack(side="left")

        lbl_name = ctk.CTkLabel(
            f_left, 
            text="PeciDeck MK.1", 
            font=ctk.CTkFont(size=17, weight="bold"), 
            text_color="#FFFFFF"
        )
        lbl_name.pack(anchor="w")

        self.badge_status = ctk.CTkFrame(
            f_left,
            fg_color="#261719",
            corner_radius=6,
            border_width=1,
            border_color="#48242A"
        )
        self.badge_status.pack(anchor="w", pady=(2, 2))

        self.lbl_dot = ctk.CTkLabel(
            self.badge_status, 
            text="●", 
            font=ctk.CTkFont(size=9), 
            text_color="#E74C3C"
        )
        self.lbl_dot.pack(side="left", padx=(5, 3), pady=1)

        self.lbl_status_text = ctk.CTkLabel(
            self.badge_status, 
            text="ODPOJENO (STANDBY)", 
            font=ctk.CTkFont(size=9, weight="bold"), 
            text_color="#E74C3C"
        )
        self.lbl_status_text.pack(side="left", padx=(0, 6), pady=1)

        self.lbl_fw = ctk.CTkLabel(
            f_left, 
            text="Verze FW: 1.1.0", 
            font=ctk.CTkFont(size=10), 
            text_color="#64748B"
        )
        self.lbl_fw.pack(anchor="w")

        # Tlačítko Konfigurovat vpravo (vždy klikatelné pro konfiguraci profilů i offline)
        self.btn_config = ctk.CTkButton(
            info_frame,
            text="Konfigurovat",
            width=130,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1A1C26",
            border_width=1,
            border_color="#FF7A29",
            text_color="#FFFFFF",
            hover_color="#282C3D",
            command=self.on_configure_cb
        )
        self.btn_config.pack(side="right", pady=4)

    def update_connection_status(self, is_connected, port_name=None):
        """Aktualizuje stav připojení na kartě PeciDeck MK.1."""
        if is_connected:
            self.lbl_dot.configure(text_color="#2ECC71")
            self.lbl_status_text.configure(text="PŘIPOJENO PŘES USB", text_color="#2ECC71")
            self.badge_status.configure(fg_color="#102B1D", border_color="#1D5A38")
            self.card_deck.configure(border_color="#1F4D32")
            self.btn_config.configure(
                fg_color="#FF6E14", 
                border_width=0,
                text_color="#0B0B0E", 
                hover_color="#FF8A35"
            )
        else:
            self.lbl_dot.configure(text_color="#E74C3C")
            self.lbl_status_text.configure(text="ODPOJENO (STANDBY)", text_color="#E74C3C")
            self.badge_status.configure(fg_color="#261719", border_color="#48242A")
            self.card_deck.configure(border_color="#242738")
            self.btn_config.configure(
                fg_color="#1A1C26", 
                border_width=1,
                border_color="#FF7A29", 
                text_color="#FFFFFF", 
                hover_color="#282C3D"
            )

    def update_obs_status(self, is_connected):
        """Aktualizuje stav připojení OBS na dashboardu."""
        if hasattr(self, "btn_obs_status"):
            if is_connected:
                self.btn_obs_status.configure(
                    text="● OBS: Připojeno",
                    text_color="#2ECC71",
                    fg_color="#102B1D",
                    hover_color="#183D29",
                    border_color="#1D5A38"
                )
            else:
                self.btn_obs_status.configure(
                    text="● OBS: Odpojeno",
                    text_color="#E74C3C",
                    fg_color="#201316",
                    hover_color="#2E181D",
                    border_color="#3D1D22"
                )

