import os
import time
import copy
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk
from assets_manager import get_asset_icon, load_custom_image
from ui.app_picker_dialog import AppPickerDialog

# =============================================================================
#  PŘEHLEDNÉ KATEGORIE IKON PRO VÝBĚR
# =============================================================================
ICON_CATEGORIES = [
    ("Média & Zvuk", "cat_media", [
        ("play", "Play"),
        ("pause", "Pauza"),
        ("next", "Další"),
        ("prev", "Předchozí"),
        ("stop", "Stop"),
        ("vol_up", "Hlas +"),
        ("vol_down", "Hlas -"),
        ("mute", "Mute")
    ]),
    ("Hry & Komunikace", "cat_games", [
        ("discord", "Discord"),
        ("steam", "Steam"),
        ("twitch", "Twitch"),
        ("mic", "Mikrofon"),
        ("headset", "Sluchátka")
    ]),
    ("OBS & Stream", "cat_obs", [
        ("obs", "OBS"),
        ("rec", "Záznam"),
        ("screenshot", "Screenshot"),
        ("scene", "Scéna"),
        ("marker", "Značka (Marker)"),
        ("clip", "Klip (Clip)")
    ]),
    ("Systém & Nástroje", "cat_system", [
        ("lock", "Zamknout"),
        ("copy", "Kopírovat"),
        ("paste", "Vložit"),
        ("folder", "Složka"),
        ("calc", "Kalkulačka"),
        ("hotkey", "Zkratka"),
        ("app", "Aplikace")
    ]),
    ("Web & Odkazy", "cat_web", [
        ("youtube", "YouTube"),
        ("spotify", "Spotify"),
        ("web", "Web")
    ]),
    ("Ostatní", "none", [
        ("none", "Bez ikony")
    ])
]


# =============================================================================
#  MODERNÍ ZAOKROUHLENÉ KONTEXTOVÉ MENU (BEZ BÍLÉHO RÁMEČKU, DESIGN DLE APLIKACE)
# =============================================================================
class ModernContextMenu:
    """
    Moderní, dokonale zaoblené plovoucí kontextové menu ve stylu CustomTkinter.
    Zcela nahrazuje zastaralé Win32 tk.Menu s bílým ohraničením (Image 2).
    """
    def __init__(self, parent):
        self.parent = parent
        self.top = None
        self._items = []
        self._global_bind_id = None

    def add_command(self, label, command=None, shortcut="", state="normal", is_danger=False, icon="", icon_asset=""):
        self._items.append({
            "type": "command",
            "label": label,
            "command": command,
            "shortcut": shortcut,
            "state": state,
            "is_danger": is_danger,
            "icon": icon,
            "icon_asset": icon_asset
        })

    def add_separator(self):
        self._items.append({"type": "separator"})

    def show(self, x, y):
        active = getattr(self.parent, "_active_context_menu", None)
        if active and active != self:
            try:
                active.close()
            except Exception:
                pass
        self.parent._active_context_menu = self

        top_win = self.parent.winfo_toplevel()
        self.top = tk.Toplevel(top_win)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        # Jednolitý 1px rámeček v barvě #2D3142 kolem celé nabídky bez ořezu pravé a spodní strany
        self.top.configure(bg="#2D3142")

        container = ctk.CTkFrame(
            self.top,
            fg_color="#14151F",
            corner_radius=0,
            border_width=0
        )
        container.pack(fill="both", expand=True, padx=1, pady=1)

        for item in self._items:
            if item["type"] == "separator":
                sep = ctk.CTkFrame(container, height=1, fg_color="#222534")
                sep.pack(fill="x", padx=6, pady=3)
                continue

            state = item.get("state", "normal")
            is_danger = item.get("is_danger", False)
            is_enabled = (state == "normal")

            if not is_enabled:
                text_col = "#4E5572"
            elif is_danger:
                text_col = "#F87171"
            else:
                text_col = "#E2E8F0"

            row = ctk.CTkFrame(container, fg_color="transparent", corner_radius=6, height=30)
            row.pack(fill="x", padx=4, pady=1)
            row.pack_propagate(False)

            # 1. Pevný sloupec ikony (šířka 24 px) pro dokonalé zarovnání textu do sloupce
            icon_asset = item.get("icon_asset", "")
            icon_str = item.get("icon", "")
            lbl_icon = None

            if icon_asset:
                ico_img = get_asset_icon(icon_asset, size=(15, 15))
                if ico_img:
                    lbl_icon = ctk.CTkLabel(row, image=ico_img, text="", width=24)
            if not lbl_icon and icon_str:
                lbl_icon = ctk.CTkLabel(row, text=icon_str, width=24, font=ctk.CTkFont(size=12), text_color=text_col)
            elif not lbl_icon:
                lbl_icon = ctk.CTkLabel(row, text="", width=24)

            lbl_icon.pack(side="left", padx=(8, 2))

            # 2. Text položky menu
            lbl_title = ctk.CTkLabel(
                row,
                text=item["label"],
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=text_col,
                anchor="w"
            )
            lbl_title.pack(side="left", padx=(4, 14), fill="x", expand=True)

            # 3. Klávesová zkratka vpravo
            shortcut = item.get("shortcut", "")
            lbl_sc = None
            if shortcut:
                lbl_sc = ctk.CTkLabel(
                    row,
                    text=shortcut,
                    font=ctk.CTkFont(size=10),
                    text_color="#64748B" if is_enabled else "#334155",
                    anchor="e"
                )
                lbl_sc.pack(side="right", padx=(0, 10))

            if is_enabled:
                cmd = item.get("command")
                def _make_hover(r=row, dang=is_danger, c=cmd):
                    def _enter(e):
                        r.configure(fg_color="#36171D" if dang else "#222536")
                    def _leave(e):
                        r.configure(fg_color="transparent")
                    def _click(e):
                        self.close()
                        if c:
                            c()
                    return _enter, _leave, _click

                _on_ent, _on_lea, _on_clk = _make_hover()
                row_widgets = [row, lbl_title]
                if lbl_icon: row_widgets.append(lbl_icon)
                if lbl_sc: row_widgets.append(lbl_sc)
                for w in row_widgets:
                    w.bind("<Enter>", _on_ent)
                    w.bind("<Leave>", _on_lea)
                    w.bind("<Button-1>", _on_clk)

        self.top.update_idletasks()
        w = max(220, self.top.winfo_width())
        h = self.top.winfo_height()
        sw = self.top.winfo_screenwidth()
        sh = self.top.winfo_screenheight()
        nx = max(10, min(x, sw - w - 10))
        ny = max(10, min(y, sh - h - 10))
        self.top.geometry(f"{w}x{h}+{nx}+{ny}")
        try:
            import ctypes
            child_hwnd = self.top.winfo_id()
            parent_hwnd = ctypes.windll.user32.GetParent(child_hwnd)
            if parent_hwnd:
                val = ctypes.c_int(3)  # DWMWCP_ROUNDSMALL
                ctypes.windll.dwmapi.DwmSetWindowAttribute(parent_hwnd, 33, ctypes.byref(val), ctypes.sizeof(val))
        except Exception:
            pass

        self.top.bind("<Escape>", lambda e: self.close())

        def _on_global_click(e):
            if self.top:
                try:
                    tx = self.top.winfo_rootx()
                    ty = self.top.winfo_rooty()
                    tw = self.top.winfo_width()
                    th = self.top.winfo_height()
                    if not (tx <= e.x_root <= tx + tw and ty <= e.y_root <= ty + th):
                        self.close()
                except Exception:
                    self.close()

        self._global_bind_id = top_win.bind("<Button-1>", _on_global_click, add="+")

    def close(self):
        if self.top:
            try:
                if self._global_bind_id:
                    self.parent.winfo_toplevel().unbind("<Button-1>", self._global_bind_id)
            except Exception:
                pass
            try:
                self.top.destroy()
            except Exception:
                pass
            self.top = None
            if getattr(self.parent, "_active_context_menu", None) == self:
                self.parent._active_context_menu = None


# =============================================================================
#  VYSKAKOVACÍ OKNO PRO VÝBĚR IKONY (S KATEGORIEMI A VYHLEDÁVÁNÍM)
# =============================================================================
class IconPickerModal(ctk.CTkToplevel):
    def __init__(self, parent, current_icon, current_custom_path, on_select_cb):
        super().__init__(parent)
        self.title("Výběr ikony pro klávesu")
        self.geometry("540x560")
        self.minsize(500, 500)
        self.resizable(True, True)
        self.configure(fg_color="#111218")
        self.transient(parent)
        self.grab_set()

        self.current_icon = current_icon
        self.current_custom_path = current_custom_path
        self.on_select_cb = on_select_cb

        self.selected_category_filter = "Vše"
        self.search_query = ""
        self.category_widgets = []

        self._build_ui()

    def _build_ui(self):
        # 1. Horní lišta
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=22, pady=(16, 6))

        lbl_head = ctk.CTkLabel(
            top_frame, 
            text="Výběr ikony", 
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#FFFFFF"
        )
        lbl_head.pack(anchor="w")

        # 2. Tlačítko pro vlastní obrázek z PC
        folder_ico = get_asset_icon("folder", size=(18, 18))
        btn_custom = ctk.CTkButton(
            self,
            image=folder_ico,
            text="  Vybrat vlastní obrázek z PC (.png, .jpg, .ico)...",
            height=38,
            corner_radius=8,
            fg_color="#1E202C",
            hover_color="#2A2E40",
            border_width=1,
            border_color="#2E3348",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._pick_custom_file
        )
        btn_custom.pack(fill="x", padx=22, pady=(4, 10))

        # 3. Vyhledávací pole
        search_box = ctk.CTkFrame(self, fg_color="transparent")
        search_box.pack(fill="x", padx=22, pady=(0, 8))

        search_ico = get_asset_icon("search", size=(16, 16))
        self.search_entry = ctk.CTkEntry(
            search_box,
            placeholder_text="  Hledat ikonu (např. Play, OBS, Discord)...",
            height=34,
            corner_radius=8,
            fg_color="#0E0F15",
            border_color="#26293A",
            border_width=1,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12)
        )
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<KeyRelease>", self._on_search_change)

        # 4. Kategorie - filtrační tlačítka (Pill buttons)
        cat_bar = ctk.CTkFrame(self, fg_color="transparent", height=32)
        cat_bar.pack(fill="x", padx=22, pady=(0, 10))

        cat_names = ["Vše", "Média", "Hry", "OBS", "Systém", "Web"]
        self.filter_buttons = {}
        for cname in cat_names:
            is_active = (cname == "Vše")
            btn_f = ctk.CTkButton(
                cat_bar,
                text=cname,
                width=65,
                height=26,
                corner_radius=13,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#FF7A29" if is_active else "#1A1C26",
                text_color="#0A0A0E" if is_active else "#CBD5E1",
                hover_color="#FF8E3D" if is_active else "#282A3A",
                command=lambda cn=cname: self._set_category_filter(cn)
            )
            btn_f.pack(side="left", padx=(0, 6))
            self.filter_buttons[cname] = btn_f

        # 5. Hlavní rolovací plocha s rozdělenými kategoriemi
        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_area.pack(fill="both", expand=True, padx=18, pady=(0, 14))

        self._render_icon_grid()

    def _set_category_filter(self, cname):
        self.selected_category_filter = cname
        for name, btn in self.filter_buttons.items():
            active = (name == cname)
            btn.configure(
                fg_color="#FF7A29" if active else "#1A1C26",
                text_color="#0A0A0E" if active else "#CBD5E1",
                hover_color="#FF8E3D" if active else "#282A3A"
            )
        self._filter_items()

    def _on_search_change(self, e):
        self.search_query = self.search_entry.get().strip().lower()
        self._filter_items()

    def _render_icon_grid(self):
        self.category_widgets.clear()

        for cat_title, cat_icon, items in ICON_CATEGORIES:
            cat_frame = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
            cat_frame.pack(fill="x", pady=(4, 12))

            # Nadpis sekce s ikonou
            header_box = ctk.CTkFrame(cat_frame, fg_color="transparent")
            header_box.pack(anchor="w", padx=6, pady=(0, 6))

            cat_ico = get_asset_icon(cat_icon, size=(16, 16)) if cat_icon != "none" else None
            if cat_ico:
                lbl_c_ico = ctk.CTkLabel(header_box, image=cat_ico, text="")
                lbl_c_ico.pack(side="left", padx=(0, 6))

            lbl_cat = ctk.CTkLabel(
                header_box, 
                text=cat_title, 
                font=ctk.CTkFont(size=12, weight="bold"), 
                text_color="#8E95AE"
            )
            lbl_cat.pack(side="left")

            grid_box = ctk.CTkFrame(cat_frame, fg_color="transparent")
            grid_box.pack(fill="x")

            item_btns = []
            COLS = 4
            for idx, (icon_key, label_cz) in enumerate(items):
                r = idx // COLS
                c = idx % COLS

                is_active = (icon_key == self.current_icon and not self.current_custom_path)
                ico_img = get_asset_icon(icon_key, size=(24, 24))

                btn_tile = ctk.CTkButton(
                    grid_box,
                    image=ico_img,
                    text=f"\n{label_cz}",
                    compound="top",
                    width=105,
                    height=58,
                    corner_radius=8,
                    fg_color="#302018" if is_active else "#1A1C26",
                    border_width=2 if is_active else 1,
                    border_color="#FF7A29" if is_active else "#282A3A",
                    hover_color="#282A3A",
                    text_color="#FF9D54" if is_active else "#FFFFFF",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    command=lambda k=icon_key: self._select_preset(k)
                )
                btn_tile.grid(row=r, column=c, padx=5, pady=4)
                item_btns.append((icon_key, label_cz, btn_tile))

            self.category_widgets.append((cat_title, cat_frame, item_btns))

    def _filter_items(self):
        query = self.search_query
        f_cat = self.selected_category_filter

        for cat_title, cat_frame, items in self.category_widgets:
            # Kontrola kategorie
            match_cat = True
            if f_cat == "Média" and "Média" not in cat_title: match_cat = False
            elif f_cat == "Hry" and "Hry" not in cat_title: match_cat = False
            elif f_cat == "OBS" and "OBS" not in cat_title: match_cat = False
            elif f_cat == "Systém" and "Systém" not in cat_title: match_cat = False
            elif f_cat == "Web" and "Web" not in cat_title: match_cat = False

            if not match_cat:
                cat_frame.pack_forget()
                continue

            # Kontrola vyhledávacího dotazu
            visible_count = 0
            for icon_key, label_cz, btn in items:
                if not query or query in label_cz.lower() or query in icon_key.lower():
                    btn.grid()
                    visible_count += 1
                else:
                    btn.grid_remove()

            if visible_count > 0:
                cat_frame.pack(fill="x", pady=(4, 12))
            else:
                cat_frame.pack_forget()

    def _select_preset(self, icon_key):
        self.on_select_cb(icon_key=icon_key, custom_path="")
        self.destroy()

    def _pick_custom_file(self):
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Vyberte ikonu nebo obrázek",
            filetypes=[("Obrázky", "*.png;*.jpg;*.jpeg;*.ico;*.bmp"), ("Všechny soubory", "*.*")]
        )
        if file_path:
            self.on_select_cb(icon_key="custom", custom_path=file_path)
            self.destroy()


# =============================================================================
#  OBS DIALOGY PRO VÝBĚR SCÉN, ZVUKŮ A REŽIMŮ
# =============================================================================
class OBSItemPickerDialog(ctk.CTkToplevel):
    """Moderní dialog pro výběr OBS scény nebo audio stopy ze seznamu."""
    def __init__(self, parent, title, prompt, items, default_val=""):
        super().__init__(parent)
        self.title(title)
        self.geometry("440x260")
        self.resizable(False, False)
        self.configure(fg_color="#111218")
        self.transient(parent)
        self.grab_set()

        self.result = None

        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=16, weight="bold"), text_color="#FF7A29").pack(pady=(16, 6))
        ctk.CTkLabel(self, text=prompt, font=ctk.CTkFont(size=12), text_color="#CBD5E1").pack(padx=24, pady=(0, 12))

        self.combo = ctk.CTkComboBox(
            self,
            values=items if items else ["Žádné položky nenalezeny"],
            width=360,
            height=34,
            fg_color="#0E0F15",
            border_color="#282B3C",
            border_width=1,
            corner_radius=8,
            text_color="#FFFFFF"
        )
        if items:
            self.combo.set(default_val if default_val in items else items[0])
        self.combo.pack(pady=(0, 24))

        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=36)

        ctk.CTkButton(
            btn_box,
            text="Zrušit",
            width=110,
            height=34,
            corner_radius=8,
            fg_color="#1E202C",
            hover_color="#282A3A",
            border_width=1,
            border_color="#2D3042",
            text_color="#CBD5E1",
            command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_box,
            text="Potvrdit",
            width=150,
            height=34,
            corner_radius=8,
            fg_color="#FF7A29",
            hover_color="#FF8E3D",
            text_color="#0B0B0E",
            font=ctk.CTkFont(weight="bold"),
            command=self._confirm
        ).pack(side="right")

        self.wait_window()

    def _confirm(self):
        val = self.combo.get().strip()
        if val and val != "Žádné položky nenalezeny":
            self.result = val
        self.destroy()

    def get_result(self):
        return self.result


class OBSActionChooserDialog(ctk.CTkToplevel):
    """Dialog pro detailní konfiguraci OBS akce klávesy v inspektoru."""
    def __init__(self, parent, current_param, obs_controller):
        super().__init__(parent)
        self.title("Konfigurace OBS akce")
        self.geometry("480x340")
        self.resizable(False, False)
        self.configure(fg_color="#111218")
        self.transient(parent)
        self.grab_set()

        self.obs = obs_controller
        self.result = None

        ctk.CTkLabel(self, text="Konfigurace OBS Studio", font=ctk.CTkFont(size=16, weight="bold"), text_color="#FF7A29").pack(pady=(16, 4))
        ctk.CTkLabel(self, text="Vyberte požadovaný OBS příkaz pro toto tlačítko:", font=ctk.CTkFont(size=12), text_color="#CBD5E1").pack(pady=(0, 14))

        self.actions = [
            ("Spustit / Zastavit Stream", "toggle_stream", "obs"),
            ("Spustit / Zastavit Záznam", "toggle_record", "rec"),
            ("Pozastavit / Obnovit Záznam", "toggle_record_pause", "pause"),
            ("Další scéna OBS", "next_scene", "scene"),
            ("Předchozí scéna OBS", "prev_scene", "scene"),
            ("Přepnout na konkrétní scénu...", "scene:", "scene"),
            ("Ztlumit zvuk (Mute)...", "mute:", "mute"),
            ("Virtuální kamera", "toggle_virtual_cam", "obs"),
            ("Uložit Replay buffer", "save_replay_buffer", "rec")
        ]
        self.act_map = {lbl: (cmd, ico) for lbl, cmd, ico in self.actions}

        curr_label = "Spustit / Zastavit Stream"
        sub_val = ""
        p = str(current_param or "")
        if p.startswith("scene:"):
            curr_label = "Přepnout na konkrétní scénu..."
            sub_val = p[6:]
        elif p.startswith("mute:"):
            curr_label = "Ztlumit zvuk (Mute)..."
            sub_val = p[5:]
        else:
            for lbl, cmd, _ in self.actions:
                if cmd == p:
                    curr_label = lbl
                    break

        ctk.CTkLabel(self, text="Příkaz:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1").pack(anchor="w", padx=36, pady=(0, 4))
        self.combo_act = ctk.CTkComboBox(
            self,
            values=[a[0] for a in self.actions],
            command=self._on_act_change,
            width=408,
            height=32,
            fg_color="#0E0F15",
            border_color="#282B3C",
            border_width=1,
            corner_radius=8
        )
        self.combo_act.set(curr_label)
        self.combo_act.pack(padx=36, pady=(0, 12))

        # Rám pro výběr scény / audio stopy
        self.sub_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.sub_frame.pack(fill="x", padx=36, pady=(0, 16))

        self.lbl_sub = ctk.CTkLabel(self.sub_frame, text="Cíl:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1")
        self.lbl_sub.pack(anchor="w", pady=(0, 4))

        scenes = self.obs.get_scenes() if self.obs else []

        self.combo_sub = ctk.CTkComboBox(
            self.sub_frame,
            values=scenes if scenes else ["(Zadejte název ručně)"],
            width=408,
            height=32,
            fg_color="#0E0F15",
            border_color="#282B3C",
            border_width=1,
            corner_radius=8
        )
        if sub_val:
            self.combo_sub.set(sub_val)
        self.combo_sub.pack()

        self._on_act_change(curr_label)

        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=36, pady=(10, 0))

        ctk.CTkButton(
            btn_box,
            text="Zrušit",
            width=110,
            height=34,
            corner_radius=8,
            fg_color="#1E202C",
            hover_color="#282A3A",
            border_width=1,
            border_color="#2D3042",
            text_color="#CBD5E1",
            command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_box,
            text="Uložit",
            width=140,
            height=34,
            corner_radius=8,
            fg_color="#FF7A29",
            hover_color="#FF8E3D",
            text_color="#0B0B0E",
            font=ctk.CTkFont(weight="bold"),
            command=self._confirm
        ).pack(side="right")

        self.wait_window()

    def _on_act_change(self, choice):
        cmd, _ = self.act_map.get(choice, ("toggle_stream", "obs"))
        if cmd == "scene:":
            self.sub_frame.pack(fill="x", padx=36, pady=(0, 16))
            self.lbl_sub.configure(text="Scéna v OBS:")
            scenes = self.obs.get_scenes() if self.obs else []
            self.combo_sub.configure(values=scenes if scenes else ["(Zadejte název ručně)"])
            if scenes and not self.combo_sub.get():
                self.combo_sub.set(scenes[0])
        elif cmd == "mute:":
            self.sub_frame.pack(fill="x", padx=36, pady=(0, 16))
            self.lbl_sub.configure(text="Audio stopa v OBS:")
            audios = self.obs.get_audio_inputs() if self.obs else []
            self.combo_sub.configure(values=audios if audios else ["(Zadejte název ručně)"])
            if audios and not self.combo_sub.get():
                self.combo_sub.set(audios[0])
        else:
            self.sub_frame.pack_forget()

    def _confirm(self):
        choice = self.combo_act.get()
        cmd, ico = self.act_map.get(choice, ("toggle_stream", "obs"))
        if cmd == "scene:":
            sub = self.combo_sub.get().strip()
            self.result = {"param": f"scene:{sub}", "label": sub[:10] if sub else "Scéna", "icon": "scene"}
        elif cmd == "mute:":
            sub = self.combo_sub.get().strip()
            self.result = {"param": f"mute:{sub}", "label": sub[:10] if sub else "Mute OBS", "icon": "mute"}
        else:
            short_map = {
                "toggle_stream": "Stream", "toggle_record": "Záznam",
                "toggle_record_pause": "Pauza Rec", "next_scene": "Další scéna",
                "prev_scene": "Předch. scéna", "toggle_virtual_cam": "Virt. kamera",
                "save_replay_buffer": "Replay"
            }
            self.result = {"param": cmd, "label": short_map.get(cmd, cmd), "icon": ico}
        self.destroy()

    def get_result(self):
        return self.result


class OBSEncoderModeDialog(ctk.CTkToplevel):
    """Dialog pro výběr funkce rotačního enkodéru včetně podpory OBS."""
    def __init__(self, parent, enc_id, current_edata, obs_controller):
        super().__init__(parent)
        self.title(f"Režim enkodéru E{enc_id + 1}")
        self.geometry("480x300")
        self.resizable(False, False)
        self.configure(fg_color="#111218")
        self.transient(parent)
        self.grab_set()

        self.obs = obs_controller
        self.result = None

        ctk.CTkLabel(self, text=f"Konfigurace enkodéru E{enc_id + 1}", font=ctk.CTkFont(size=16, weight="bold"), text_color="#FF7A29").pack(pady=(16, 4))
        ctk.CTkLabel(self, text="Vyberte funkci pro otáčení a stisk tohoto enkodéru:", font=ctk.CTkFont(size=12), text_color="#CBD5E1").pack(pady=(0, 14))

        self.modes = [
            "Hlavní hlasitost Windows (+/- a Mute)",
            "Média Windows (Posun skladeb a Play/Pause)",
            "Jas displeje PeciDeck (+/- a Vypnout)",
            "OBS: Přepínání scén (CW další, CCW předchozí)",
            "OBS: Hlasitost zvuku v OBS (+/- a Mute)"
        ]

        cw_type = current_edata.get("cw", {}).get("action_type", "")
        cw_param = current_edata.get("cw", {}).get("action_param", "")

        curr_mode = self.modes[0]
        if cw_type == "volume":
            curr_mode = self.modes[0]
        elif cw_type == "media":
            curr_mode = self.modes[1]
        elif cw_type == "brightness":
            curr_mode = self.modes[2]
        elif cw_type == "obs" and ("scene" in cw_param):
            curr_mode = self.modes[3]
        elif cw_type == "obs" and ("vol" in cw_param):
            curr_mode = self.modes[4]

        self.combo_mode = ctk.CTkComboBox(
            self,
            values=self.modes,
            command=self._on_mode_change,
            width=408,
            height=32,
            fg_color="#0E0F15",
            border_color="#282B3C",
            border_width=1,
            corner_radius=8
        )
        self.combo_mode.set(curr_mode)
        self.combo_mode.pack(padx=36, pady=(0, 12))

        # Audio track podvýběr pro OBS
        self.f_audio = ctk.CTkFrame(self, fg_color="transparent")
        self.f_audio.pack(fill="x", padx=36, pady=(0, 16))

        ctk.CTkLabel(self.f_audio, text="Audio stopa v OBS:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1").pack(anchor="w", pady=(0, 4))
        audios = self.obs.get_audio_inputs() if self.obs else []
        self.combo_audio = ctk.CTkComboBox(
            self.f_audio,
            values=audios if audios else ["Desktop Audio"],
            width=408,
            height=32,
            fg_color="#0E0F15",
            border_color="#282B3C",
            border_width=1,
            corner_radius=8
        )
        if cw_param.startswith("vol_up:"):
            self.combo_audio.set(cw_param[7:])
        else:
            self.combo_audio.set(audios[0] if audios else "Desktop Audio")
        self.combo_audio.pack()

        self._on_mode_change(curr_mode)

        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=36, pady=(10, 0))

        ctk.CTkButton(
            btn_box,
            text="Zrušit",
            width=110,
            height=34,
            corner_radius=8,
            fg_color="#1E202C",
            hover_color="#282A3A",
            border_width=1,
            border_color="#2D3042",
            text_color="#CBD5E1",
            command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_box,
            text="Uložit",
            width=140,
            height=34,
            corner_radius=8,
            fg_color="#FF7A29",
            hover_color="#FF8E3D",
            text_color="#0B0B0E",
            font=ctk.CTkFont(weight="bold"),
            command=self._confirm
        ).pack(side="right")

        self.wait_window()

    def _on_mode_change(self, mode):
        if "Hlasitost zvuku v OBS" in mode:
            self.f_audio.pack(fill="x", padx=36, pady=(0, 16))
        else:
            self.f_audio.pack_forget()

    def _confirm(self):
        mode = self.combo_mode.get()
        if "hlavní hlasitost" in mode.lower():
            self.result = {
                "name": "Hlasitost",
                "desc": "Hlasitost",
                "cw": {"action_type": "volume", "action_param": "up"},
                "ccw": {"action_type": "volume", "action_param": "down"},
                "btn": {"action_type": "volume", "action_param": "mute"}
            }
        elif "média" in mode.lower():
            self.result = {
                "name": "Média",
                "desc": "Média",
                "cw": {"action_type": "media", "action_param": "next"},
                "ccw": {"action_type": "media", "action_param": "prev"},
                "btn": {"action_type": "media", "action_param": "play_pause"}
            }
        elif "jas" in mode.lower():
            self.result = {
                "name": "Jas displeje",
                "desc": "Jas",
                "cw": {"action_type": "brightness", "action_param": "up"},
                "ccw": {"action_type": "brightness", "action_param": "down"},
                "btn": {"action_type": "brightness", "action_param": "toggle"}
            }
        elif "přepínání scén" in mode.lower():
            self.result = {
                "name": "Scény OBS",
                "desc": "OBS Scény",
                "cw": {"action_type": "obs", "action_param": "next_scene"},
                "ccw": {"action_type": "obs", "action_param": "prev_scene"},
                "btn": {"action_type": "obs", "action_param": "toggle_stream"}
            }
        elif "hlasitost zvuku v obs" in mode.lower():
            target = self.combo_audio.get().strip() or "Desktop Audio"
            self.result = {
                "name": f"OBS: {target[:8]}",
                "desc": "OBS Zvuk",
                "cw": {"action_type": "obs", "action_param": f"vol_up:{target}"},
                "ccw": {"action_type": "obs", "action_param": f"vol_down:{target}"},
                "btn": {"action_type": "obs", "action_param": f"mute:{target}"}
            }
        self.destroy()

    def get_result(self):
        return self.result


# =============================================================================
#  DIALOGY PRO MULTI-ACTION A STRÁNKY
# =============================================================================
class AddMultiStepDialog(ctk.CTkToplevel):
    """Moderní přehledně kategorizovaný dialog pro výběr a přidání akce do řetězce (Multi-Action)."""
    def __init__(self, parent, obs_controller=None, pages=None, config_mgr=None):
        super().__init__(parent)
        self.title("Přidat krok do řetězce akcí")
        self.geometry("520x580")
        self.minsize(480, 500)
        self.resizable(True, True)
        self.configure(fg_color="#111218")
        self.transient(parent)
        self.grab_set()

        self.obs = obs_controller
        self.pages = pages or []
        self.config_mgr = config_mgr
        self.result = None

        # 1. Záhlaví dialogu
        ctk.CTkLabel(
            self,
            text="Přidat krok do řetězce akcí",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#FF7A29"
        ).pack(pady=(16, 2))

        ctk.CTkLabel(
            self,
            text="Vyberte akci z přehledných kategorií níže nebo použijte vyhledávání:",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        ).pack(padx=24, pady=(0, 10))

        # 2. Vyhledávací pole
        search_box = ctk.CTkFrame(self, fg_color="transparent")
        search_box.pack(fill="x", padx=24, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_box,
            placeholder_text="🔍 Hledat akci do řetězce...",
            height=34,
            corner_radius=8,
            fg_color="#0E0F15",
            border_color="#26293A",
            border_width=1,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12)
        )
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<KeyRelease>", self._on_search)

        # 3. Rolovací oblast s kategoriemi
        self.f_options = ctk.CTkScrollableFrame(
            self,
            fg_color="#14151E",
            corner_radius=10,
            border_width=1,
            border_color="#202232"
        )
        self.f_options.pack(fill="both", expand=True, padx=24, pady=(0, 12))

        # Logicky seřazené kategorie akcí
        categories_def = [
            ("⚙️ SYSTÉM & NÁSTROJE", [
                ("🚀 Spustit program / soubor (.exe, .lnk, .bat)", "app", ""),
                ("⌨ Klávesová zkratka (Hotkey)", "hotkey", ""),
                ("⏳ Časová pauza (Delay v ms)", "delay", ""),
                ("🎙️ Ztlumit mikrofon PC (Systém)", "system_mic", "toggle"),
                ("🌐 Otevřít webovou stránku (URL)", "url", ""),
            ]),
            ("🔴 OBS STUDIO", [
                ("🔴 Spustit / Zastavit vysílání (Stream)", "obs", "toggle_stream"),
                ("⏺ Spustit / Zastavit nahrávání (Record)", "obs", "toggle_record"),
                ("⏸ Pozastavit / Obnovit záznam", "obs", "toggle_record_pause"),
                ("🎬 Přepnout scénu v OBS...", "obs_scene", ""),
                ("🔇 Ztlumit audio stopu v OBS (Mute)...", "obs_mute", ""),
                ("📷 Virtuální webkamera OBS", "obs", "toggle_virtual_cam"),
                ("💾 Uložit Replay buffer OBS", "obs", "save_replay_buffer"),
            ]),
            ("🎧 DISCORD", [
                ("🎙️ Ztlumit mikrofon (Mute)", "discord", "mute"),
                ("🎧 Ztlumit sluchátka (Deafen)", "discord", "deafen"),
                ("🚀 Otevřít aplikaci Discord", "discord", "open"),
                ("📞 Odpojit z hlasového hovoru", "discord", "disconnect"),
            ]),
            ("🟣 TWITCH", [
                ("🔖 Značka ve streamu (Stream Marker)", "twitch", "marker"),
                ("🎬 Vytvořit klip (Create Clip)", "twitch", "clip"),
                ("📢 Spustit reklamu (30 sekund)", "twitch", "commercial:30"),
                ("🧹 Vymazat chat (Clear Chat)", "twitch", "clear_chat"),
                ("🛡️ Režim štítu (Shield Mode)", "twitch", "toggle_shield"),
                ("💬 Odeslat zprávu do chatu...", "twitch_chat", ""),
            ]),
            ("🎵 ZVUK & MÉDIA", [
                ("🔊 Hlasitost: Zvýšit (+)", "volume", "up"),
                ("🔉 Hlasitost: Snížit (-)", "volume", "down"),
                ("🔇 Hlasitost: Ztlumit (Mute)", "volume", "mute"),
                ("🎵 Přehrát / Pozastavit média", "media", "play_pause"),
                ("⏭ Další skladba", "media", "next"),
                ("⏮ Předchozí skladba", "media", "prev"),
                ("⏹ Zastavit přehrávání (Stop)", "media", "stop"),
            ]),
            ("📄 STRÁNKY & PROFILY", [
                ("🏷️ Přepnout profil...", "profile", "CUSTOM"),
            ]),
        ]

        # Přidání konkrétních profilů uživatele
        profs = self.config_mgr.list_profiles() if self.config_mgr else []
        for prof in profs:
            categories_def[-1][1].append((f"🏷️ Přepnout profil: {prof['name']}", "profile_direct", prof["id"]))

        # Přidání akcí stránek a složek
        categories_def[-1][1].extend([
            ("📄 Přejít na konkrétní stránku...", "page_goto", "CUSTOM"),
            ("📁 Otevřít podstránku (složku)...", "page_folder", "CUSTOM"),
            ("📄 Přejít na další stránku", "page", "next"),
            ("📄 Přejít na předchozí stránku", "page", "prev"),
            ("↩️ Zpět na předchozí stránku", "page", "back"),
        ])

        self.cat_groups = []
        for cat_title, items in categories_def:
            cat_frame = ctk.CTkFrame(self.f_options, fg_color="transparent")
            cat_frame.pack(fill="x", pady=(8, 4))

            # Header lišta kategorie
            hdr_badge = ctk.CTkFrame(cat_frame, fg_color="#181A26", corner_radius=6, height=28)
            hdr_badge.pack(fill="x", padx=4, pady=(2, 6))

            lbl_badge = ctk.CTkLabel(
                hdr_badge,
                text=f"  {cat_title}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#FF9D54"
            )
            lbl_badge.pack(side="left", padx=8, pady=3)

            item_btns = []
            for title, atype, detail in items:
                btn = ctk.CTkButton(
                    cat_frame,
                    text=f"  {title}",
                    anchor="w",
                    height=32,
                    corner_radius=6,
                    fg_color="#1A1C28",
                    hover_color="#282C40",
                    border_width=1,
                    border_color="#222536",
                    text_color="#FFFFFF",
                    font=ctk.CTkFont(size=11),
                    command=lambda t=atype, d=detail, tit=title: self._choose(t, d, tit)
                )
                btn.pack(fill="x", padx=8, pady=2)
                item_btns.append((btn, title.lower()))

            self.cat_groups.append((cat_frame, cat_title.lower(), item_btns))

        # 4. Spodní lišta s tlačítkem Zrušit
        btn_cancel = ctk.CTkButton(
            self,
            text="Zrušit",
            width=130,
            height=34,
            corner_radius=8,
            fg_color="#1E202C",
            hover_color="#282B3C",
            text_color="#CBD5E1",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.destroy
        )
        btn_cancel.pack(pady=(0, 14))

    def _on_search(self, e=None):
        q = self.search_entry.get().strip().lower()
        for cat_frame, cat_title, items in self.cat_groups:
            match_cat = (q in cat_title)
            visible_count = 0
            for btn, item_text in items:
                if not q or match_cat or q in item_text:
                    btn.pack(fill="x", padx=8, pady=2)
                    visible_count += 1
                else:
                    btn.pack_forget()

            if visible_count > 0:
                cat_frame.pack(fill="x", pady=(8, 4))
            else:
                cat_frame.pack_forget()

    def _choose(self, atype, detail, title):
        if atype == "app":
            dlg = AppPickerDialog(self, title="Vyberte program do řetězce akcí")
            app_res = dlg.get_result()
            if not app_res: return
            self.result = {
                "action_type": "app",
                "action_param": app_res["path"],
                "label": app_res["name"][:14],
                "icon": app_res.get("icon", "app"),
                "custom_icon": app_res.get("custom_icon", "")
            }
        elif atype == "url":
            dlg = ctk.CTkInputDialog(text="Zadejte webovou URL adresu:", title="Webová adresa")
            u = dlg.get_input()
            if not u: return
            self.result = {"action_type": "url", "action_param": u.strip(), "label": u.strip()[:14]}
        elif atype == "hotkey":
            dlg = ctk.CTkInputDialog(text="Zadejte klávesovou zkratku (např. ctrl+shift+m):", title="Klávesová zkratka")
            hk = dlg.get_input()
            if not hk: return
            self.result = {"action_type": "hotkey", "action_param": hk.strip().lower(), "label": hk.strip().upper()}
        elif atype == "delay":
            dlg = ctk.CTkInputDialog(text="Zadejte dobu čekání v ms (např. 500 = 0.5s):", title="Pauza")
            ms = dlg.get_input()
            if not ms: return
            self.result = {"action_type": "delay", "action_param": ms.strip(), "label": f"Pauza {ms.strip()}ms"}
        elif atype == "profile":
            profs = self.config_mgr.list_profiles() if self.config_mgr else []
            cur = getattr(self.config_mgr, "active_profile_id", "default") if self.config_mgr else ""
            dlg = ProfileChooserDialog(self, profs, cur)
            pid = dlg.get_result()
            if not pid: return
            prof_name = next((p["name"] for p in profs if p["id"] == pid), pid)
            self.result = {"action_type": "profile", "action_param": pid, "label": f"Profil: {prof_name[:10]}"}
        elif atype == "profile_direct":
            prof_name = title.replace("🏷️ Přepnout profil:", "").strip()
            self.result = {"action_type": "profile", "action_param": detail, "label": f"Profil: {prof_name[:10]}"}
        elif atype == "system_mic":
            self.result = {"action_type": "system_mic", "action_param": "toggle", "label": "Mic PC"}
        elif atype == "discord":
            disc_labels = {"mute": "Mute Mic", "deafen": "Deafen", "open": "Discord", "disconnect": "Odpojit"}
            self.result = {"action_type": "discord", "action_param": detail, "label": disc_labels.get(detail, "Discord")}
        elif atype == "page_goto":
            dlg = PageChooserDialog(self, self.pages, 0)
            chosen = dlg.get_result()
            if chosen is None: return
            pg_name = self.pages[chosen].get("name", f"Str. {chosen + 1}") if chosen < len(self.pages) else f"Str. {chosen + 1}"
            self.result = {"action_type": "page", "action_param": f"goto:{chosen}", "label": pg_name[:12]}
        elif atype == "page_folder":
            folders = [p for p in self.pages if p.get("is_folder")]
            if folders:
                dlg = PageChooserDialog(self, folders, 0)
                chosen = dlg.get_result()
                if chosen is None: return
                real_idx = folders[chosen].get("id", chosen)
                f_name = folders[chosen].get("name", "Složka")
                self.result = {"action_type": "page", "action_param": f"folder:{real_idx}", "label": f_name[:12]}
            else:
                dlg = ctk.CTkInputDialog(text="Zadejte název nové složky:", title="Nová složka")
                f_name = dlg.get_input()
                if not f_name or not f_name.strip(): return
                cur_page = self.config_mgr.profile.get("active_page", 0) if self.config_mgr else 0
                new_idx = self.config_mgr.create_folder(f_name.strip(), cur_page) if self.config_mgr else 0
                self.result = {"action_type": "page", "action_param": f"folder:{new_idx}", "label": f_name.strip()[:12]}
        elif atype == "obs_scene":
            scenes = self.obs.get_scenes() if self.obs else []
            if scenes:
                dlg = OBSItemPickerDialog(self, "Výběr scény", "Vyberte scénu:", scenes)
                ch = dlg.get_result()
                if not ch: return
                self.result = {"action_type": "obs", "action_param": f"scene:{ch}", "label": f"Scéna: {ch[:10]}"}
            else:
                dlg = ctk.CTkInputDialog(text="Zadejte název scény v OBS:", title="Scéna OBS")
                sc = dlg.get_input()
                if not sc: return
                self.result = {"action_type": "obs", "action_param": f"scene:{sc.strip()}", "label": f"Scéna: {sc.strip()[:10]}"}
        elif atype == "obs_mute":
            audios = self.obs.get_audio_inputs() if self.obs else []
            if audios:
                dlg = OBSItemPickerDialog(self, "Ztlumit zvuk", "Vyberte audio stopu:", audios)
                ch = dlg.get_result()
                if not ch: return
                self.result = {"action_type": "obs", "action_param": f"mute:{ch}", "label": f"Mute: {ch[:10]}"}
            else:
                dlg = ctk.CTkInputDialog(text="Zadejte název audio stopy v OBS:", title="Mute OBS")
                au = dlg.get_input()
                if not au: return
                self.result = {"action_type": "obs", "action_param": f"mute:{au.strip()}", "label": f"Mute: {au.strip()[:10]}"}
        elif atype == "twitch_chat":
            dlg = ctk.CTkInputDialog(text="Zadejte zprávu do Twitch chatu:", title="Twitch zpráva")
            msg = dlg.get_input()
            if not msg: return
            self.result = {"action_type": "twitch", "action_param": f"chat:{msg.strip()}", "label": f"Chat: {msg.strip()[:10]}"}
        elif atype == "twitch":
            tw_labels = {"marker": "Marker", "clip": "Klip", "commercial:30": "Reklama 30s", "clear_chat": "Clear Chat", "toggle_shield": "Shield"}
            self.result = {"action_type": "twitch", "action_param": detail, "label": tw_labels.get(detail, "Twitch")}
        else:
            self.result = {"action_type": atype, "action_param": detail, "label": title.split(":")[-1].strip()}
        self.destroy()

    def get_result(self):
        self.wait_window()
        return self.result


class PageChooserDialog(ctk.CTkToplevel):
    """Dialog pro rychlý přechod na vybranou stránku nebo složku."""
    def __init__(self, parent, pages, current_idx):
        super().__init__(parent)
        self.title("Přepnout stránku")
        self.geometry("420x360")
        self.resizable(False, False)
        self.configure(fg_color="#111218")
        self.transient(parent)
        self.grab_set()

        self.result = None

        ctk.CTkLabel(self, text="Seznam stránek", font=ctk.CTkFont(size=16, weight="bold"), text_color="#FF7A29").pack(pady=(16, 4))
        ctk.CTkLabel(self, text="Klikněte na stránku, na kterou chcete přepnout:", font=ctk.CTkFont(size=12), text_color="#CBD5E1").pack(padx=24, pady=(0, 14))

        f_scroll = ctk.CTkScrollableFrame(self, width=360, height=200, fg_color="#14151E", corner_radius=10)
        f_scroll.pack(padx=24, pady=(0, 16))

        for idx, pg in enumerate(pages):
            is_active = (idx == current_idx)
            name = pg.get("name", f"Stránka {idx + 1}")
            is_folder = pg.get("is_folder", False)
            prefix = "📁 " if is_folder else "📄 "

            btn = ctk.CTkButton(
                f_scroll,
                text=f"{prefix}{name} {'(Aktivní)' if is_active else ''}",
                anchor="w",
                height=34,
                corner_radius=6,
                fg_color="#2A2019" if is_active else "#1B1C27",
                hover_color="#3D291D" if is_active else "#2A2E40",
                border_width=1 if is_active else 0,
                border_color="#FF7A29" if is_active else "#282B3C",
                text_color="#FF9D54" if is_active else "#FFFFFF",
                font=ctk.CTkFont(size=12, weight="bold" if is_active else "normal"),
                command=lambda i=idx: self._select(i)
            )
            btn.pack(fill="x", padx=6, pady=3)

        ctk.CTkButton(self, text="Zavřít", width=120, height=32, corner_radius=8, fg_color="#1E202C", hover_color="#282B3C", command=self.destroy).pack(pady=(0, 12))

    def _select(self, idx):
        self.result = idx
        self.destroy()

    def get_result(self):
        self.wait_window()
        return self.result


class ProfileChooserDialog(ctk.CTkToplevel):
    """Dialog pro výběr profilu pro akci Přepnout profil."""
    def __init__(self, parent, profiles, current_id=""):
        super().__init__(parent)
        self.title("Výběr profilu")
        self.geometry("420x360")
        self.resizable(False, False)
        self.configure(fg_color="#111218")
        self.transient(parent)
        self.grab_set()

        self.result = None

        ctk.CTkLabel(self, text="Seznam profilů", font=ctk.CTkFont(size=16, weight="bold"), text_color="#FF7A29").pack(pady=(16, 4))
        ctk.CTkLabel(self, text="Vyberte profil, na který má tlačítko přepnout:", font=ctk.CTkFont(size=12), text_color="#CBD5E1").pack(padx=24, pady=(0, 14))

        f_scroll = ctk.CTkScrollableFrame(self, width=360, height=200, fg_color="#14151E", corner_radius=10)
        f_scroll.pack(padx=24, pady=(0, 16))

        for prof in profiles:
            pid = prof.get("id", "")
            pname = prof.get("name", pid)
            is_active = (pid == current_id)

            btn = ctk.CTkButton(
                f_scroll,
                text=f"🏷️  {pname} {'(Aktivní)' if is_active else ''}",
                anchor="w",
                height=34,
                corner_radius=6,
                fg_color="#2A2019" if is_active else "#1B1C27",
                hover_color="#3D291D" if is_active else "#2A2E40",
                border_width=1 if is_active else 0,
                border_color="#FF7A29" if is_active else "#282B3C",
                text_color="#FF9D54" if is_active else "#FFFFFF",
                font=ctk.CTkFont(size=12, weight="bold" if is_active else "normal"),
                command=lambda i=pid: self._select(i)
            )
            btn.pack(fill="x", padx=6, pady=3)

        ctk.CTkButton(self, text="Zrušit", width=120, height=32, corner_radius=8, fg_color="#1E202C", hover_color="#282B3C", command=self.destroy).pack(pady=(0, 12))

    def _select(self, pid):
        self.result = pid
        self.destroy()

    def get_result(self):
        self.wait_window()
        return self.result


class PageOptionsDialog(ctk.CTkToplevel):
    """Možnosti správy aktuální stránky (Přejmenovat, Duplikovat, Smazat)."""
    def __init__(self, parent, page_name, can_delete=True):
        super().__init__(parent)
        self.title("Možnosti stránky")
        self.geometry("380x280")
        self.resizable(False, False)
        self.configure(fg_color="#111218")
        self.transient(parent)
        self.grab_set()

        self.action = None

        ctk.CTkLabel(self, text="Správa stránky", font=ctk.CTkFont(size=16, weight="bold"), text_color="#FF7A29").pack(pady=(16, 4))
        ctk.CTkLabel(self, text=f"Aktuální: {page_name}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CBD5E1").pack(pady=(0, 16))

        btn_rename = ctk.CTkButton(
            self, text="✎ Přejmenovat stránku", width=260, height=36, corner_radius=8,
            fg_color="#1B1C27", hover_color="#2A2E40", text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._choose("rename")
        )
        btn_rename.pack(pady=4)

        btn_dup = ctk.CTkButton(
            self, text="📋 Duplikovat stránku", width=260, height=36, corner_radius=8,
            fg_color="#1B1C27", hover_color="#2A2E40", text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._choose("duplicate")
        )
        btn_dup.pack(pady=4)

        btn_del = ctk.CTkButton(
            self, text="🗑 Smazat stránku", width=260, height=36, corner_radius=8,
            fg_color="#2C1417" if can_delete else "#1A1718",
            hover_color="#42191F" if can_delete else "#1A1718",
            text_color="#E74C3C" if can_delete else "#555555",
            font=ctk.CTkFont(size=12, weight="bold"),
            state="normal" if can_delete else "disabled",
            command=lambda: self._choose("delete")
        )
        btn_del.pack(pady=4)

        ctk.CTkButton(self, text="Zrušit", width=120, height=30, corner_radius=8, fg_color="#1E202C", hover_color="#282B3C", command=self.destroy).pack(pady=(12, 0))

    def _choose(self, act):
        self.action = act
        self.destroy()

    def get_result(self):
        self.wait_window()
        return self.action


# =============================================================================
#  ROZBALOVACÍ SLOŽKA V KNIHOVNĚ AKCÍ S OSTRÝMI PNG IKONAMI
# =============================================================================
class CollapsibleFolder(ctk.CTkFrame):
    def __init__(self, parent, title, icon_name, items, on_item_click, on_drag_start, on_drag_motion, on_drag_end, start_open=False):
        super().__init__(parent, fg_color="#151620", corner_radius=8, border_width=1, border_color="#202230")
        self.title_text = title
        self.icon_name = icon_name
        self.items = items
        self.on_item_click = on_item_click
        self.on_drag_start = on_drag_start
        self.on_drag_motion = on_drag_motion
        self.on_drag_end = on_drag_end
        self.is_open = start_open

        cat_ico = get_asset_icon(icon_name, size=(20, 20))
        self.btn_header = ctk.CTkButton(
            self,
            image=cat_ico,
            text=self._get_header_text(),
            compound="left",
            anchor="w",
            height=38,
            corner_radius=8,
            fg_color="#181A25",
            hover_color="#242636",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.toggle
        )
        self.btn_header.pack(fill="x")

        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.item_widgets = []

        for item in self.items:
            it_ico = get_asset_icon(item.get("icon", ""), size=(18, 18))
            btn_item = ctk.CTkButton(
                self.content_frame,
                image=it_ico,
                text=f"  {item['label']}",
                compound="left",
                anchor="w",
                height=32,
                corner_radius=6,
                fg_color="#1C1E2A",
                hover_color="#262838",
                border_width=1,
                border_color="#252737",
                text_color="#D1D5DB",
                font=ctk.CTkFont(size=12),
                command=lambda it=item: self._on_click(it)
            )
            btn_item.pack(fill="x", padx=4, pady=2)

            self._bind_drag(btn_item, item)
            self.item_widgets.append((item, btn_item))

        if self.is_open:
            self.content_frame.pack(fill="x", padx=4, pady=(2, 6))

    def _on_click(self, item):
        # Spustí se pouze v případě, že neprobíhalo tažení
        if not getattr(self, "_was_dragging", False):
            self.on_item_click(item)
        self._was_dragging = False

    def _bind_drag(self, widget, item):
        def on_press(e):
            widget._drag_sx = e.x_root
            widget._drag_sy = e.y_root
            widget._is_drag_active = False
            self._was_dragging = False

        def on_motion(e):
            dx = abs(e.x_root - getattr(widget, "_drag_sx", 0))
            dy = abs(e.y_root - getattr(widget, "_drag_sy", 0))
            if dx > 5 or dy > 5:
                if not getattr(widget, "_is_drag_active", False):
                    widget._is_drag_active = True
                    self._was_dragging = True
                    self.on_drag_start(item, e.x_root, e.y_root)
                else:
                    self.on_drag_motion(e.x_root, e.y_root)

        def on_release(e):
            if getattr(widget, "_is_drag_active", False):
                widget._is_drag_active = False
                self.on_drag_end(item, e.x_root, e.y_root)

        widget.bind("<ButtonPress-1>", on_press, add="+")
        widget.bind("<B1-Motion>", on_motion, add="+")
        widget.bind("<ButtonRelease-1>", on_release, add="+")

    def _get_header_text(self):
        arrow = "▼" if self.is_open else "▶"
        return f"  {self.title_text}   {arrow}"

    def toggle(self):
        self.is_open = not self.is_open
        self.btn_header.configure(text=self._get_header_text())
        if self.is_open:
            self.content_frame.pack(fill="x", padx=4, pady=(2, 6))
        else:
            self.content_frame.pack_forget()

    def set_open(self, open_state):
        if self.is_open != open_state:
            self.toggle()

    def filter_items(self, query):
        q = query.strip().lower()
        if not q:
            for item, btn in self.item_widgets:
                btn.pack(fill="x", padx=4, pady=2)
            self.pack(fill="x", padx=(4, 8), pady=3)
            return

        has_match = False
        for item, btn in self.item_widgets:
            if q in item["label"].lower() or q in self.title_text.lower():
                btn.pack(fill="x", padx=4, pady=2)
                has_match = True
            else:
                btn.pack_forget()

        if has_match:
            self.pack(fill="x", padx=(4, 8), pady=3)
            self.set_open(True)
        else:
            self.pack_forget()


class _EntryParamProxy:
    """Helper pro sjednocení CTkComboBox s metodami CTkEntry pro 100% stabilitu a kompatibilitu."""
    def __init__(self, combo):
        self.combo = combo
    def get(self):
        return self.combo.get().strip()
    def set(self, val):
        self.combo.set(val)
    def delete(self, start=0, end="end"):
        self.combo.set("")
    def insert(self, idx, val):
        self.combo.set(val)
    def configure(self, **kwargs):
        pass
    def bind(self, *args, **kwargs):
        pass


# =============================================================================
#  HLAVNÍ KONFIGURAČNÍ OBRAZOVKA PECIDECKU (MODULÁRNÍ, RESPONZIVNÍ STYL)
# =============================================================================
class DeckView(ctk.CTkFrame):
    def __init__(self, parent, config_mgr, serial_bridge, action_handler, on_back_cb, on_settings_cb, obs_controller=None, discord_controller=None, twitch_controller=None):
        super().__init__(parent, fg_color="transparent")
        self.config_mgr = config_mgr
        self.serial = serial_bridge
        self.action_handler = action_handler
        self.on_back_cb = on_back_cb
        self.on_settings_cb = on_settings_cb
        self.obs_controller = obs_controller
        self.discord = discord_controller
        self.twitch_controller = twitch_controller

        self.selected_item = None
        self.btn_widgets = []
        self.disp_cells = []
        self.enc_widgets = []
        self.folders = []
        self._debounce_timer = None

        # Plovoucí indikátor v rámci stejného okna (zabraňuje zamrznutí)
        self._drag_badge = None
        self._active_drag_item = None

        # Drag & drop tlačítek a schránka pro kopírování/vkládání zkratkami
        self._btn_drag_badge = None
        self._btn_drag_active = False
        self._btn_drag_src = None
        self._btn_drag_candidate = None
        self._btn_drag_start = None
        self._button_clipboard = None

        self._build_ui()

    def update_obs_status(self, is_connected):
        """Aktualizuje stavový indikátor OBS v záhlaví."""
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

    def _on_obs_status_clicked(self):
        """Kliknutí na indikátor OBS zkusí připojit nebo otevře nastavení."""
        if self.obs_controller and not self.obs_controller.is_connected:
            self.btn_obs_status.configure(text="● OBS: Připojuji...", text_color="#38BDF8")
            def _cb(ok):
                self.after(0, lambda: self.update_obs_status(ok))
            self.obs_controller.connect_async(_cb)
        else:
            self.on_settings_cb()

    def _build_ui(self):
        # 1. Horní lišta
        top_bar = ctk.CTkFrame(self, fg_color="transparent", height=44)
        top_bar.pack(fill="x", padx=26, pady=(14, 8))

        back_ico = get_asset_icon("back", size=(14, 14))
        btn_back = ctk.CTkButton(
            top_bar,
            image=back_ico,
            text="  Moje Zařízení",
            compound="left",
            width=140,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1A1C26",
            hover_color="#262837",
            border_width=1,
            border_color="#2B2D3E",
            text_color="#E2E8F0",
            command=self.on_back_cb
        )
        btn_back.pack(side="left")

        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left", padx=18)

        lbl_device = ctk.CTkLabel(
            title_box, 
            text="PeciDeck MK.1", 
            font=ctk.CTkFont(size=20, weight="bold"), 
            text_color="#FFFFFF"
        )
        lbl_device.pack(side="left")

        lbl_engine = ctk.CTkLabel(
            title_box,
            text=" STREAM ENGINE ",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#FF7A29",
            fg_color="#241C15",
            corner_radius=4
        )
        lbl_engine.pack(side="left", padx=(10, 0), pady=(2, 0))

        gear_ico = get_asset_icon("gear", size=(18, 18))
        btn_settings = ctk.CTkButton(
            top_bar,
            image=gear_ico,
            text="",
            width=36,
            height=36,
            corner_radius=18,
            fg_color="#1A1C26",
            hover_color="#262837",
            border_width=1,
            border_color="#2B2D3E",
            command=self.on_settings_cb
        )
        btn_settings.pack(side="right")

        # OBS Live Status Pill
        is_obs = bool(self.obs_controller and self.obs_controller.is_connected)
        self.btn_obs_status = ctk.CTkButton(
            top_bar,
            text="● OBS: Připojeno" if is_obs else "● OBS: Odpojeno",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#2ECC71" if is_obs else "#E74C3C",
            fg_color="#102B1D" if is_obs else "#201316",
            hover_color="#183D29" if is_obs else "#2E181D",
            border_width=1,
            border_color="#1D5A38" if is_obs else "#3D1D22",
            corner_radius=14,
            height=28,
            width=120,
            command=self._on_obs_status_clicked
        )
        self.btn_obs_status.pack(side="right", padx=(0, 10))

        # 2. Hlavní rozdělení (Modulární split - obě části se přizpůsobují oknu)
        main_split = tk.Frame(self, bg="#0D0E12", bd=0, highlightthickness=0)
        main_split.pack(fill="both", expand=True, padx=26, pady=(0, 16))

        # LEVÝ SLOUPEC (Hardware šasi + Spodní inspektor)
        self.left_col = tk.Frame(main_split, bg="#0D0E12", bd=0, highlightthickness=0)
        self.left_col.pack(side="left", fill="both", expand=True, padx=(0, 16))

        # PRAVÝ SLOUPEC (Knihovna akcí o šířce 320 px)
        right_col = ctk.CTkFrame(main_split, width=320, fg_color="#13141C", corner_radius=14, border_width=1, border_color="#222432")
        right_col.pack(side="right", fill="y", padx=(14, 0))
        right_col.pack_propagate(False)

        self._build_hardware_chassis(self.left_col)
        self._build_inspector_panel(self.left_col)
        self._build_action_palette(right_col)
        self._render_profile_bar()
        self._render_pages_pill()

        # Záchranný escape, uvolnění myši a klávesové zkratky (Ctrl+C, Ctrl+V, Ctrl+X, Delete)
        try:
            top = self.winfo_toplevel()
            top.bind("<Escape>", lambda e: self._cleanup_drag(), add="+")
            top.bind("<ButtonRelease-1>", self._on_global_mouse_up, add="+")
            top.bind("<B1-Motion>", self._on_global_b1_motion, add="+")
            top.bind("<Control-c>", self._on_key_ctrl_c, add="+")
            top.bind("<Control-C>", self._on_key_ctrl_c, add="+")
            top.bind("<Control-v>", self._on_key_ctrl_v, add="+")
            top.bind("<Control-V>", self._on_key_ctrl_v, add="+")
            top.bind("<Control-x>", self._on_key_ctrl_x, add="+")
            top.bind("<Control-X>", self._on_key_ctrl_x, add="+")
            top.bind("<Delete>", self._on_key_delete, add="+")
            top.bind("<BackSpace>", self._on_key_delete, add="+")
        except Exception:
            pass

    # =========================================================================
    #  PŘEPÍNAČ PROFILŮ VEDLE STRÁNEK (MULTITASKING DLE POŽADAVKU)
    # =========================================================================
    def _render_profile_bar(self):
        """Aktualizuje rozbalovací nabídku profilů vedle stránek."""
        if not hasattr(self, "combo_profile"):
            return
        profs = self.config_mgr.list_profiles()
        self._prof_map = {p["name"]: p["id"] for p in profs}
        self._prof_id_map = {p["id"]: p["name"] for p in profs}

        curr_id = getattr(self.config_mgr, "active_profile_id", "default")
        curr_name = self.config_mgr.profile.get("name", "Výchozí")
        for p in profs:
            if p["id"] == curr_id:
                curr_name = p["name"]
                break
        self.combo_profile.configure(text=f"{curr_name}  ▾")

    def _open_profile_dropdown(self):
        """Otevře moderní tmavé kontextové menu pro výběr profilu (zcela bez bílých okrajů Win32 tk.Menu)."""
        profs = self.config_mgr.list_profiles() if self.config_mgr else []
        curr_id = getattr(self.config_mgr, "active_profile_id", "default")

        menu = ModernContextMenu(self)
        for p in profs:
            pid = p["id"]
            pname = p["name"]
            is_active = (pid == curr_id)
            label = f"✓  {pname}" if is_active else f"    {pname}"
            def _choose(target_id=pid):
                self._switch_profile_by_id(target_id)
            menu.add_command(label, _choose)

        menu.add_separator()
        menu.add_command("+ Nový profil...", self._add_profile_dialog)

        try:
            bx = self.combo_profile.winfo_rootx()
            by = self.combo_profile.winfo_rooty() + self.combo_profile.winfo_height() + 4
        except Exception:
            bx, by = 200, 200
        menu.show(bx, by)

    def _switch_profile_by_id(self, pid):
        if pid and pid != getattr(self.config_mgr, "active_profile_id", None):
            self.config_mgr.switch_profile(pid)
            self._render_profile_bar()
            self._render_pages_pill()
            self._refresh_all_buttons_ui()
            self._refresh_all_encoders_ui()
            self.select_button(0)
            if self.serial and self.serial.is_connected:
                self.serial.sync_profile(self.config_mgr.profile)

    def _on_profile_selected(self, choice):
        pid = getattr(self, "_prof_map", {}).get(choice)
        if pid:
            self._switch_profile_by_id(pid)

    def _add_profile_dialog(self):
        dlg = ctk.CTkInputDialog(text="Zadejte název nového profilu (např. DaVinci Resolve, OBS, Hry):", title="Nový profil")
        name = dlg.get_input()
        if name and name.strip():
            self.config_mgr.create_profile(name.strip())
            self._render_profile_bar()
            self._render_pages_pill()
            self._refresh_all_buttons_ui()
            self._refresh_all_encoders_ui()
            self.select_button(0)
            if self.serial and self.serial.is_connected:
                self.serial.sync_profile(self.config_mgr.profile)

    def _on_profile_right_click(self, e):
        curr_id = getattr(self.config_mgr, "active_profile_id", "default")
        curr_name = self.config_mgr.profile.get("name", "Profil")
        profs = self.config_mgr.list_profiles() if self.config_mgr else []

        menu = ModernContextMenu(self)
        menu.add_command(f"Přejmenovat profil '{curr_name}'...", lambda: self._rename_profile_dialog(curr_id), icon_asset="edit")
        menu.add_command(f"Duplikovat profil '{curr_name}'", lambda: self._duplicate_profile_quick(curr_id), icon_asset="copy")
        if len(profs) > 1:
            menu.add_separator()
            menu.add_command(f"Smazat profil '{curr_name}'", lambda: self._delete_profile_quick(curr_id), icon_asset="trash", is_danger=True)
        menu.show(e.x_root, e.y_root)

    def _rename_profile_dialog(self, pid):
        curr_name = self.config_mgr.profile.get("name", "Profil")
        dlg = ctk.CTkInputDialog(text=f"Přejmenovat profil '{curr_name}':", title="Přejmenovat profil")
        new_name = dlg.get_input()
        if new_name and new_name.strip():
            self.config_mgr.rename_profile(pid, new_name.strip())
            self._render_profile_bar()

    def _duplicate_profile_quick(self, pid):
        self.config_mgr.duplicate_profile(pid)
        self._render_profile_bar()
        self._render_pages_pill()
        self._refresh_all_buttons_ui()
        self._refresh_all_encoders_ui()
        self.select_button(0)
        if self.serial and self.serial.is_connected:
            self.serial.sync_profile(self.config_mgr.profile)

    def _delete_profile_quick(self, pid):
        self.config_mgr.delete_profile(pid)
        self._render_profile_bar()
        self._render_pages_pill()
        self._refresh_all_buttons_ui()
        self._refresh_all_encoders_ui()
        self.select_button(0)
        if self.serial and self.serial.is_connected:
            self.serial.sync_profile(self.config_mgr.profile)

    def _refresh_all_encoders_ui(self):
        encoders_data = self.config_mgr.profile.get("encoders", [])
        for i in range(3):
            if i < len(self.enc_widgets):
                edata = encoders_data[i] if i < len(encoders_data) else {}
                name = edata.get("name", f"E{i+1}")
                self.enc_widgets[i]._lbl_tag.configure(text=name)
                cw_act = edata.get("cw", {}).get("action_type", "none")
                desc = "Hlasitost" if cw_act == "volume" else ("OBS" if cw_act == "obs" else ("Discord" if cw_act == "discord" else "Prázdné"))
                self.enc_widgets[i]._lbl_desc.configure(text=name if name != f"E{i+1}" else desc)

    # =========================================================================
    #  PILULKOVÝ PŘEPÍNAČ STRÁNEK POD ENKODÉRY (Dle Fotky 2: Pages: ( 1  2  + ))
    # =========================================================================
    def _render_pages_pill(self):
        """Vykreslí pilulkový přepínač stránek přesně dle Fotky 2 pod enkodéry."""
        if not hasattr(self, "pill_container"):
            return
        for child in self.pill_container.winfo_children():
            child.destroy()

        pages = self.config_mgr.profile.get("pages", [])
        act_page = self.config_mgr.profile.get("active_page", 0)

        for p_idx, page in enumerate(pages):
            is_active = (p_idx == act_page)
            num_str = str(p_idx + 1)

            if is_active:
                btn_p = ctk.CTkButton(
                    self.pill_container,
                    text=num_str,
                    width=32,
                    height=22,
                    corner_radius=11,
                    fg_color="#FFFFFF",
                    hover_color="#FFFFFF",
                    text_color="#0D0E15",
                    font=ctk.CTkFont(size=11, weight="bold")
                )
            else:
                btn_p = ctk.CTkButton(
                    self.pill_container,
                    text=num_str,
                    width=28,
                    height=22,
                    corner_radius=11,
                    fg_color="transparent",
                    hover_color="#252838",
                    text_color="#8E95AE",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    command=lambda i=p_idx: self.switch_to_page(i)
                )

            btn_p.pack(side="left", padx=2, pady=2)

            # Pravé tlačítko pro smazání stránky ("mazat pravim tlacitkem")
            btn_p.bind("<Button-3>", lambda e, i=p_idx: self._on_page_pill_right_click(e, i))

        # Tlačítko + na konci ("pridavat tim pluskem")
        btn_add = ctk.CTkButton(
            self.pill_container,
            text="+",
            width=26,
            height=22,
            corner_radius=11,
            fg_color="transparent",
            hover_color="#252838",
            text_color="#8E95AE",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._add_quick_page
        )
        btn_add.pack(side="left", padx=(1, 4), pady=2)

    def _on_page_pill_right_click(self, e, p_idx):
        """Pravé tlačítko myši pro správu a smazání stránky."""
        pages = self.config_mgr.profile.get("pages", [])
        if not (0 <= p_idx < len(pages)):
            return

        pg_name = pages[p_idx].get("name", f"Stránka {p_idx + 1}")
        menu = ModernContextMenu(self)
        menu.add_command(f"Přejmenovat stránku {p_idx + 1}...", lambda: self._rename_page_quick(p_idx), icon_asset="edit")
        menu.add_command(f"Duplikovat stránku {p_idx + 1}", lambda: self._duplicate_page_quick(p_idx), icon_asset="copy")
        if len(pages) > 1:
            menu.add_separator()
            menu.add_command(f"Smazat stránku {p_idx + 1} ({pg_name})", lambda: self._delete_page_quick(p_idx), icon_asset="trash", is_danger=True)
        menu.show(e.x_root, e.y_root)

    def _delete_page_quick(self, p_idx):
        pages = self.config_mgr.profile.get("pages", [])
        if len(pages) <= 1:
            return
        self.config_mgr.delete_page(p_idx)
        new_cur = self.config_mgr.profile.get("active_page", 0)
        self.switch_to_page(new_cur)

    def _rename_page_quick(self, p_idx):
        pages = self.config_mgr.profile.get("pages", [])
        if not (0 <= p_idx < len(pages)):
            return
        cur_name = pages[p_idx].get("name", f"Stránka {p_idx + 1}")
        dlg = ctk.CTkInputDialog(text=f"Nový název pro stránku {p_idx + 1}:", title="Přejmenovat stránku")
        new_name = dlg.get_input()
        if new_name and new_name.strip():
            self.config_mgr.rename_page(p_idx, new_name.strip())
            self._render_pages_pill()

    def _duplicate_page_quick(self, p_idx):
        new_idx = self.config_mgr.duplicate_page(p_idx)
        if new_idx >= 0:
            self.switch_to_page(new_idx)

    def _add_quick_page(self):
        pages = self.config_mgr.profile.get("pages", [])
        new_name = f"Stránka {len(pages) + 1}"
        new_idx = self.config_mgr.add_page(new_name)
        self.switch_to_page(new_idx)

    def _update_page_bar_ui(self):
        self._render_pages_pill()

    def _prev_page(self):
        pages = self.config_mgr.profile.get("pages", [])
        if not pages: return
        cur = self.config_mgr.profile.get("active_page", 0)
        new_idx = (cur - 1) % len(pages)
        self.switch_to_page(new_idx)

    def _next_page(self):
        pages = self.config_mgr.profile.get("pages", [])
        if not pages: return
        cur = self.config_mgr.profile.get("active_page", 0)
        new_idx = (cur + 1) % len(pages)
        self.switch_to_page(new_idx)

    def _open_page_menu(self):
        pages = self.config_mgr.profile.get("pages", [])
        cur = self.config_mgr.profile.get("active_page", 0)
        dlg = PageChooserDialog(self, pages, cur)
        chosen = dlg.get_result()
        if chosen is not None and chosen != cur:
            self.switch_to_page(chosen)

    def _add_page_dialog(self):
        pages = self.config_mgr.profile.get("pages", [])
        dlg = ctk.CTkInputDialog(text="Zadejte název nové stránky:", title="Nová stránka")
        name = dlg.get_input()
        if name is not None:
            name = name.strip() or f"Stránka {len(pages) + 1}"
            new_idx = self.config_mgr.add_page(name)
            self.switch_to_page(new_idx)

    def _add_folder_dialog(self):
        dlg = ctk.CTkInputDialog(text="Zadejte název nové složky:", title="Nová složka")
        name = dlg.get_input()
        if name is not None:
            name = name.strip() or "Složka"
            cur_page = self.config_mgr.profile.get("active_page", 0)
            new_idx = self.config_mgr.create_folder(name, cur_page)
            self.switch_to_page(new_idx)

    def _open_page_options_dialog(self):
        pages = self.config_mgr.profile.get("pages", [])
        cur = self.config_mgr.profile.get("active_page", 0)
        if not (0 <= cur < len(pages)): return
        pg_name = pages[cur].get("name", f"Stránka {cur + 1}")
        dlg = PageOptionsDialog(self, pg_name, can_delete=(len(pages) > 1))
        act = dlg.get_result()
        if act == "rename":
            ren_dlg = ctk.CTkInputDialog(text=f"Nový název pro '{pg_name}':", title="Přejmenovat stránku")
            new_name = ren_dlg.get_input()
            if new_name and new_name.strip():
                self.config_mgr.rename_page(cur, new_name.strip())
                self._update_page_bar_ui()
        elif act == "duplicate":
            new_idx = self.config_mgr.duplicate_page(cur)
            if new_idx >= 0:
                self.switch_to_page(new_idx)
        elif act == "delete":
            if len(pages) > 1:
                self.config_mgr.delete_page(cur)
                new_cur = self.config_mgr.profile.get("active_page", 0)
                self.switch_to_page(new_cur)

    def switch_to_page(self, page_idx):
        if self.config_mgr.switch_page(page_idx):
            self._render_pages_pill()
            self._refresh_all_buttons_ui()
            if self.selected_item and self.selected_item[0] == "button":
                self.select_button(self.selected_item[1])
            if self.serial and self.serial.is_connected:
                self.serial.sync_profile(self.config_mgr.profile)

    def _refresh_all_buttons_ui(self):
        buttons_data = self.config_mgr.profile.get("buttons", [])
        for idx in range(8):
            bdata = buttons_data[idx] if idx < len(buttons_data) else {}
            icon = bdata.get("icon", "")
            label = bdata.get("label", "")
            custom = bdata.get("custom_icon", "")
            if idx < len(self.btn_widgets):
                self._update_button_widget_ui(self.btn_widgets[idx], icon, label, custom)

    # =========================================================================
    #  LEVÝ PANEL: HARDWARE PECIDECK (POUZE TLAČÍTKA + ENKODÉRY + STRÁNKY)
    # =========================================================================
    def _build_hardware_chassis(self, parent):
        self.chassis = ctk.CTkFrame(parent, fg_color="#14151E", corner_radius=16, border_width=1, border_color="#242738")
        self.chassis.pack(side="top", fill="x", expand=False, pady=(0, 8))

        # 1. SEKCE: TLAČÍTKA
        lbl_btns = ctk.CTkLabel(self.chassis, text="Tlačítka", font=ctk.CTkFont(size=12, weight="bold"), text_color="#8E95AE", height=16)
        lbl_btns.pack(anchor="w", padx=28, pady=(6, 2))

        grid_btns = ctk.CTkFrame(self.chassis, fg_color="transparent", bg_color="#14151E")
        grid_btns.pack(padx=24, pady=(0, 2))

        buttons_data = self.config_mgr.profile.get("buttons", [])
        for idx in range(8):
            row = idx // 4
            col = idx % 4
            bdata = buttons_data[idx] if idx < len(buttons_data) else {"id": idx, "label": "", "icon": "", "action_type": "none"}
            btn_w = self._create_square_button_widget(grid_btns, idx, bdata)
            btn_w.grid(row=row, column=col, padx=8, pady=3)
            self.btn_widgets.append(btn_w)

        # 2. SEKCE: ENKODÉRY
        lbl_encs = ctk.CTkLabel(self.chassis, text="Enkodéry", font=ctk.CTkFont(size=12, weight="bold"), text_color="#8E95AE", height=16)
        lbl_encs.pack(anchor="w", padx=28, pady=(2, 2))

        grid_encs = ctk.CTkFrame(self.chassis, fg_color="transparent", bg_color="#14151E")
        grid_encs.pack(padx=24, pady=(0, 2))

        encoders_data = self.config_mgr.profile.get("encoders", [])
        for i in range(3):
            edata = encoders_data[i] if i < len(encoders_data) else {"id": i, "name": f"E{i+1}"}
            enc_w = self._create_circular_encoder_widget(grid_encs, i, edata)
            enc_w.grid(row=0, column=i, padx=46, pady=0)
            self.enc_widgets.append(enc_w)

        # 3. SEKCE: PROFILY A STRÁNKY POD ENKODÉRY (Dle požadavku: Profily vedle stránek a vše dokonale veprostřed)
        f_bar_outer = ctk.CTkFrame(self.chassis, fg_color="transparent", height=36)
        f_bar_outer.pack(fill="x", padx=16, pady=(4, 6))
        f_bar_outer.pack_propagate(False)

        f_bar_center = ctk.CTkFrame(f_bar_outer, fg_color="transparent")
        f_bar_center.place(relx=0.5, rely=0.5, anchor="center")

        # A) PROFILY (Multitasking dle požadavku uživatele)
        lbl_prof_tag = ctk.CTkLabel(
            f_bar_center,
            text="Profil:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#8E95AE"
        )
        lbl_prof_tag.pack(side="left", padx=(0, 6))

        self.combo_profile = ctk.CTkButton(
            f_bar_center,
            text="Výchozí  ▾",
            width=135,
            height=28,
            corner_radius=12,
            fg_color="#181A25",
            hover_color="#242738",
            border_width=1,
            border_color="#242738",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._open_profile_dropdown
        )
        self.combo_profile.pack(side="left", padx=(0, 4))
        self.combo_profile.bind("<Button-3>", self._on_profile_right_click)
        self.combo_profile.set = lambda val: self.combo_profile.configure(text=f"{val}  ▾")

        btn_add_prof = ctk.CTkButton(
            f_bar_center,
            text="+",
            width=26,
            height=24,
            corner_radius=12,
            fg_color="#181A25",
            hover_color="#242738",
            text_color="#8E95AE",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._add_profile_dialog
        )
        btn_add_prof.pack(side="left", padx=(0, 8))

        # ODDĚLOVACÍ ČÁRA
        sep = ctk.CTkFrame(f_bar_center, width=1, height=20, fg_color="#26293A")
        sep.pack(side="left", padx=(4, 12))

        # B) STRÁNKY
        lbl_pages_tag = ctk.CTkLabel(
            f_bar_center,
            text="Stránky:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#8E95AE"
        )
        lbl_pages_tag.pack(side="left", padx=(0, 8))

        self.pill_container = ctk.CTkFrame(
            f_bar_center,
            fg_color="#181A25",
            corner_radius=14,
            height=28,
            border_width=1,
            border_color="#242738"
        )
        self.pill_container.pack(side="left")

    def _create_square_button_widget(self, parent, btn_id, bdata):
        """Klávesa s dokonale centrovanou ikonou a celistvým rámečkem bez ořezu."""
        frame = ctk.CTkFrame(
            parent,
            width=86,
            height=86,
            corner_radius=12,
            fg_color="#1B1C27",
            border_width=1,
            border_color="#2C3042"
        )
        frame.pack_propagate(False)

        lbl_num = ctk.CTkLabel(
            frame, 
            text=f"K{btn_id + 1}", 
            font=ctk.CTkFont(size=9, weight="bold"), 
            text_color="#646C85",
            fg_color="transparent"
        )
        lbl_num.place(x=8, y=5)

        icon = bdata.get("icon", "")
        custom_icon = bdata.get("custom_icon", "")
        label = bdata.get("label", "")

        lbl_icon = ctk.CTkLabel(frame, text="", fg_color="transparent")
        lbl_text = ctk.CTkLabel(
            frame, 
            text="", 
            font=ctk.CTkFont(size=10, weight="bold"), 
            text_color="#FFFFFF",
            fg_color="transparent",
            height=16
        )

        def on_press(e):
            self._btn_drag_start = (e.x_root, e.y_root)
            self._btn_drag_candidate = btn_id
            self.select_button(btn_id)

        def on_motion(e):
            if getattr(self, "_btn_drag_candidate", None) == btn_id and getattr(self, "_btn_drag_start", None):
                dx = abs(e.x_root - self._btn_drag_start[0])
                dy = abs(e.y_root - self._btn_drag_start[1])
                if (dx > 5 or dy > 5) and not getattr(self, "_btn_drag_active", False):
                    self._start_btn_to_btn_drag(btn_id, e.x_root, e.y_root)
                elif getattr(self, "_btn_drag_active", False):
                    self._on_btn_to_btn_drag_motion(e.x_root, e.y_root)

        def on_release(e):
            if getattr(self, "_btn_drag_active", False):
                self._end_btn_to_btn_drag(e.x_root, e.y_root)
            self._btn_drag_candidate = None
            self._btn_drag_start = None

        def on_right_click(e):
            self.select_button(btn_id)
            self._show_button_context_menu(e, btn_id)

        def on_enter(e):
            if self.selected_item != ("button", btn_id):
                frame.configure(border_color="#4D5472")

        def on_leave(e):
            if self.selected_item != ("button", btn_id):
                frame.configure(border_color="#2C3042")

        for w_target in (frame, lbl_num, lbl_icon, lbl_text):
            w_target.bind("<Button-1>", on_press)
            w_target.bind("<B1-Motion>", on_motion)
            w_target.bind("<ButtonRelease-1>", on_release)
            w_target.bind("<Button-3>", on_right_click)

        frame.bind("<Enter>", on_enter)
        frame.bind("<Leave>", on_leave)

        frame._lbl_num = lbl_num
        frame._lbl_icon = lbl_icon
        frame._lbl_text = lbl_text

        self._update_button_widget_ui(frame, icon, label, custom_icon)
        return frame

    def _update_button_widget_ui(self, frame, icon, label, custom_icon=""):
        """Aktualizuje ikonu a text klávesy s dokonalým centrováním bez zásahu do spodního okraje."""
        lbl_icon = frame._lbl_icon
        lbl_text = frame._lbl_text

        img = None
        if custom_icon:
            img = load_custom_image(custom_icon, size=(38, 38))
        elif icon and icon != "none":
            img = get_asset_icon(icon, size=(38, 38))

        if img:
            lbl_icon.configure(image=img, text="")
        else:
            plus_img = get_asset_icon("empty_plus", size=(22, 22))
            if plus_img:
                lbl_icon.configure(image=plus_img, text="")
            else:
                lbl_icon.configure(image=None, text="+", font=ctk.CTkFont(size=18, weight="bold"), text_color="#3E4358")

        clean_label = label.strip()
        if clean_label:
            lbl_text.configure(text=clean_label, text_color="#FFFFFF")
            lbl_icon.place(relx=0.5, rely=0.38, anchor="center")
            lbl_text.place(relx=0.5, rely=0.76, anchor="center")
        else:
            lbl_text.place_forget()
            lbl_icon.place(relx=0.5, rely=0.50, anchor="center")

    def _create_circular_encoder_widget(self, parent, enc_id, edata):
        """JEDNODUCHÝ a čistý otočný enkodér (minimalistický styl bez složitostí)."""
        frame = ctk.CTkFrame(parent, fg_color="transparent", bg_color="#14151E")

        # Čistý jednoduchý kulatý knoflík
        knob_circle = ctk.CTkFrame(
            frame,
            width=50,
            height=50,
            corner_radius=25,
            fg_color="#1C1E2A",
            border_width=3,
            border_color="#363A4E",
            bg_color="#14151E"
        )
        knob_circle.pack_propagate(False)
        knob_circle.pack(pady=(0, 2))

        # Jednoduchá oranžová ryska na 12 hodinách
        tick_notch = ctk.CTkFrame(
            knob_circle,
            width=4,
            height=9,
            corner_radius=2,
            fg_color="#FF7A29",
            border_width=0
        )
        tick_notch.place(relx=0.5, rely=0.18, anchor="center")

        # Popisky pod knoflíkem (jednoduché, čisté)
        lbl_tag = ctk.CTkLabel(
            frame, 
            text=f"E{enc_id + 1}", 
            font=ctk.CTkFont(size=11, weight="bold"), 
            text_color="#FFFFFF",
            fg_color="transparent",
            bg_color="#14151E",
            height=16
        )
        lbl_tag.pack(pady=(0, 0))

        cw = edata.get("cw", {}).get("action_type", "none")
        desc = "Prázdné" if cw == "none" else ("Hlasitost" if cw == "volume" else ("Média" if cw == "media" else "Přiřazeno"))
        lbl_desc = ctk.CTkLabel(
            frame, 
            text=desc, 
            font=ctk.CTkFont(size=10, weight="bold"), 
            text_color="#FF7A29" if desc != "Prázdné" else "#7E849B",
            fg_color="transparent",
            bg_color="#14151E",
            height=14
        )
        lbl_desc.pack(pady=(0, 0))

        def on_click(e):
            self.select_encoder(enc_id)

        def on_enter(e):
            if self.selected_item != ("encoder", enc_id):
                knob_circle.configure(border_color="#4E5572")

        def on_leave(e):
            if self.selected_item != ("encoder", enc_id):
                knob_circle.configure(border_color="#363A4E")

        frame.bind("<Button-1>", on_click)
        knob_circle.bind("<Button-1>", on_click)
        tick_notch.bind("<Button-1>", on_click)
        lbl_tag.bind("<Button-1>", on_click)
        lbl_desc.bind("<Button-1>", on_click)

        knob_circle.bind("<Enter>", on_enter)
        knob_circle.bind("<Leave>", on_leave)

        frame._knob_circle = knob_circle
        frame._tick_notch = tick_notch
        frame._lbl_tag = lbl_tag
        frame._lbl_desc = lbl_desc
        return frame

    def _update_display_cell_ui(self, idx, icon="", label="", custom_icon=""):
        """Virtuální displej byl odebrán z UI; metoda ponechána pro zpětnou kompatibilitu."""
        pass

    # =========================================================================
    #  STREAM DECK INSPEKTOR (MODULÁRNÍ, ZAOBLENÝ, STREAM DECK STYL DLE PŘEDLOHY)
    # =========================================================================
    def _build_inspector_panel(self, parent):
        """Spodní lišta konfigurace inspirovaná Elgato Stream Deck (se zaoblenými rohy a plně viditelným ohraničením)."""
        self.inspector_height = 250
        self.inspector_frame = ctk.CTkFrame(
            parent,
            height=self.inspector_height,
            fg_color="#14151E", 
            corner_radius=16, 
            border_width=1, 
            border_color="#242738"
        )
        self.inspector_frame.pack_propagate(False)
        self.inspector_frame.pack(side="top", fill="both", expand=True, pady=(0, 0))

        # Nápověda při prázdném výběru (plynulé centrování se zaoblenými rohy)
        self.lbl_empty_hint = ctk.CTkLabel(
            self.inspector_frame,
            text="Vyberte klávesu nebo enkodér pro konfiguraci, nebo přetáhněte akci z knihovny vpravo.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#64748B",
            fg_color="transparent"
        )
        self.lbl_empty_hint.pack(fill="both", expand=True, padx=20, pady=20)

        # Kontejner editoru jako čistý tk.Frame – nezasahuje do zaoblených rohů mateřského rámečku
        self.f_editor = tk.Frame(self.inspector_frame, bg="#14151E", bd=0, highlightthickness=0)

        # 1. HORNÍ ZÁHLAVÍ: Akce/Kategorie vlevo + Tlačítko koše vpravo
        h_row = ctk.CTkFrame(self.f_editor, fg_color="transparent", height=28)
        h_row.pack(fill="x", padx=10, pady=(6, 2))

        self.lbl_insp_title = ctk.CTkLabel(
            h_row, 
            text="Systém:  Otevřít program", 
            font=ctk.CTkFont(size=12, weight="bold"), 
            text_color="#FFFFFF"
        )
        self.lbl_insp_title.pack(side="left")

        trash_ico = get_asset_icon("trash", size=(15, 15))
        self.btn_clear = ctk.CTkButton(
            h_row,
            image=trash_ico,
            text="  Vymazat",
            width=94,
            height=28,
            corner_radius=6,
            fg_color="#1E171E",
            hover_color="#36171E",
            border_width=1,
            border_color="#431C24",
            text_color="#F87171",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._clear_selected
        )
        self.btn_clear.pack(side="right")

        # 2. ODDĚLOVACÍ ČÁRA
        divider = ctk.CTkFrame(self.f_editor, height=1, fg_color="#222534")
        divider.pack(fill="x", padx=10, pady=(2, 6))

        # 3. HLAVNÍ TĚLO: Levá dlaždice + Pravý panel nastavení
        body = ctk.CTkFrame(self.f_editor, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        # Levá dlaždice klávesy (+ vlevo nahoře, ▾ vpravo nahoře, ikona uprostřed, název dole)
        self.tile_frame = ctk.CTkFrame(
            body,
            width=76,
            height=76,
            corner_radius=12,
            fg_color="#181A25",
            border_width=1.5,
            border_color="#2E3348",
            cursor="hand2"
        )
        self.tile_frame.pack_propagate(False)
        self.tile_frame.pack(side="left", anchor="n", padx=(0, 16), pady=4)

        self.lbl_tile_plus = ctk.CTkLabel(
            self.tile_frame,
            text="+",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#64748B",
            fg_color="transparent"
        )
        self.lbl_tile_plus.place(x=6, y=4)

        self.lbl_tile_arrow = ctk.CTkLabel(
            self.tile_frame,
            text="▾",
            font=ctk.CTkFont(size=10),
            text_color="#64748B",
            fg_color="transparent"
        )
        self.lbl_tile_arrow.place(x=60, y=4)

        self.lbl_tile_icon = ctk.CTkLabel(self.tile_frame, text="", fg_color="transparent")
        self.lbl_tile_icon.place(relx=0.5, rely=0.38, anchor="center")

        self.lbl_tile_text = ctk.CTkLabel(
            self.tile_frame,
            text="",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#FFFFFF",
            fg_color="transparent",
            height=16
        )
        self.lbl_tile_text.place(relx=0.5, rely=0.76, anchor="center")

        def _on_tile_enter(e):
            self.tile_frame.configure(border_color="#FF7A29")

        def _on_tile_leave(e):
            self.tile_frame.configure(border_color="#2E3348")

        for w in (self.tile_frame, self.lbl_tile_plus, self.lbl_tile_arrow, self.lbl_tile_icon, self.lbl_tile_text):
            w.bind("<Button-1>", lambda e: self._on_tile_clicked())
            w.bind("<Enter>", _on_tile_enter)
            w.bind("<Leave>", _on_tile_leave)

        # Pravý panel s řádky (Název, Cíl/Akce, Podrobnosti)
        props_col = ctk.CTkFrame(body, fg_color="transparent")
        props_col.pack(side="left", fill="both", expand=True)

        # Řádek 1: Title / Název + [T ▾]
        r1 = ctk.CTkFrame(props_col, fg_color="transparent", height=30)
        r1.pack(fill="x", pady=(0, 6))

        self.lbl_r1_title = ctk.CTkLabel(
            r1, 
            text="Název:", 
            width=70, 
            anchor="w", 
            font=ctk.CTkFont(size=12), 
            text_color="#8E95AE"
        )
        self.lbl_r1_title.pack(side="left")

        self.entry_label = ctk.CTkEntry(
            r1,
            width=320,
            height=30,
            corner_radius=6,
            fg_color="#0D0E15",
            border_color="#26293A",
            border_width=1,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=11),
            placeholder_text="Název tlačítka..."
        )
        self.entry_label.pack(side="left", padx=(0, 8))
        self.entry_label.bind("<KeyRelease>", self._on_label_changed)

        self.btn_font_style = ctk.CTkButton(
            r1,
            text="T ▾",
            width=36,
            height=30,
            corner_radius=6,
            fg_color="#1E202C",
            hover_color="#2A2E40",
            border_width=1,
            border_color="#2E3348",
            text_color="#CBD5E1",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._toggle_font_style
        )
        self.btn_font_style.pack(side="left")

        # Řádek 2: App / File / Cíl + Roztahovací výběr možností (CTkComboBox) + [📁 Vybrat soubor...]
        self.row_target = ctk.CTkFrame(props_col, fg_color="transparent", height=30)
        self.row_target.pack(fill="x", pady=(0, 6))

        self.lbl_r2_caption = ctk.CTkLabel(
            self.row_target, 
            text="Cíl / Akce:", 
            width=70, 
            anchor="w", 
            font=ctk.CTkFont(size=12), 
            text_color="#8E95AE"
        )
        self.lbl_r2_caption.pack(side="left")

        self.combo_target_choice = ctk.CTkComboBox(
            self.row_target,
            width=320,
            height=30,
            corner_radius=6,
            fg_color="#0D0E15",
            border_color="#26293A",
            border_width=1,
            button_color="#1E202C",
            button_hover_color="#FF7A29",
            dropdown_fg_color="#14151E",
            dropdown_hover_color="#242738",
            dropdown_text_color="#FFFFFF",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=11),
            command=self._on_combo_target_selected
        )
        self.combo_target_choice.pack(side="left")
        self.combo_target_choice.bind("<KeyRelease>", self._on_combo_key_released)

        folder_ico = get_asset_icon("folder", size=(15, 15))
        self.btn_browse = ctk.CTkButton(
            self.row_target,
            image=folder_ico,
            text=" Vybrat soubor...",
            compound="left",
            width=120,
            height=30,
            corner_radius=6,
            fg_color="#1E202C",
            hover_color="#2A2E40",
            border_width=1,
            border_color="#2E3348",
            text_color="#CBD5E1",
            font=ctk.CTkFont(size=11),
            command=self._browse_action_target
        )

        self._combo_param_map = {}
        self.entry_param = _EntryParamProxy(self.combo_target_choice)

        # Řádek 3: Textová podrobnost (např. plná cesta k programu v uvozovkách)
        self.row_detail = ctk.CTkFrame(props_col, fg_color="transparent")
        self.row_detail.pack(fill="x")

        lbl_r3_pad = ctk.CTkLabel(self.row_detail, text="", width=70)
        lbl_r3_pad.pack(side="left")

        self.lbl_param_detail = ctk.CTkLabel(
            self.row_detail,
            text="",
            anchor="w",
            font=ctk.CTkFont(size=11),
            text_color="#7E849B",
            wraplength=460,
            justify="left"
        )
        self.lbl_param_detail.pack(side="left")

        # Panel pro Multi-Action (Řetězec více akcí naskládaných za sebou)
        self.f_multi_panel = ctk.CTkFrame(props_col, fg_color="transparent")

        h_multi = ctk.CTkFrame(self.f_multi_panel, fg_color="transparent")
        h_multi.pack(fill="x", pady=(0, 4))

        self.lbl_multi_count = ctk.CTkLabel(
            h_multi,
            text="Kroky v řetězci akcí (0):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FF9D54"
        )
        self.lbl_multi_count.pack(side="left")

        btn_add_step = ctk.CTkButton(
            h_multi,
            text="+ Přidat krok",
            width=100,
            height=26,
            corner_radius=6,
            fg_color="#1E202C",
            hover_color="#2A2E40",
            border_width=1,
            border_color="#FF7A29",
            text_color="#FF7A29",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._add_multi_action_step_dialog
        )
        btn_add_step.pack(side="right", padx=4)

        self.multi_steps_scroll = ctk.CTkScrollableFrame(
            self.f_multi_panel,
            height=150,
            fg_color="#0D0E15",
            corner_radius=8,
            border_width=1,
            border_color="#222534"
        )
        self.multi_steps_scroll.pack(fill="both", expand=True)

        # Kompatibilní aliasy
        self.lbl_act_summary = self.lbl_insp_title
        self.lbl_label_caption = self.lbl_r1_title
        self.btn_pick_icon = self.tile_frame

    def _add_multi_action_step_dialog(self):
        if not self.selected_item or self.selected_item[0] != "button":
            return
        idx = self.selected_item[1]
        buttons = self.config_mgr.profile.get("buttons", [])
        if idx >= len(buttons): return
        bdata = buttons[idx]

        pages = self.config_mgr.profile.get("pages", [])
        dlg = AddMultiStepDialog(self, obs_controller=self.obs_controller, pages=pages, config_mgr=self.config_mgr)
        step = dlg.get_result()
        if step:
            bdata.setdefault("actions", []).append(step)
            self.config_mgr.save_profile()
            self._render_multi_steps(bdata)
            self.lbl_insp_title.configure(text=f"Multi-Action:  Řetězec akcí ({len(bdata['actions'])} kroků)")

    def _delete_multi_step(self, step_idx):
        if not self.selected_item or self.selected_item[0] != "button":
            return
        idx = self.selected_item[1]
        buttons = self.config_mgr.profile.get("buttons", [])
        if idx >= len(buttons): return
        bdata = buttons[idx]
        actions = bdata.get("actions", [])
        if 0 <= step_idx < len(actions):
            actions.pop(step_idx)
            self.config_mgr.save_profile()
            self._render_multi_steps(bdata)
            self.lbl_insp_title.configure(text=f"Multi-Action:  Řetězec akcí ({len(bdata['actions'])} kroků)")

    def _move_multi_step(self, step_idx, direction):
        if not self.selected_item or self.selected_item[0] != "button":
            return
        idx = self.selected_item[1]
        buttons = self.config_mgr.profile.get("buttons", [])
        if idx >= len(buttons): return
        bdata = buttons[idx]
        actions = bdata.get("actions", [])
        new_idx = step_idx + direction
        if 0 <= new_idx < len(actions):
            actions[step_idx], actions[new_idx] = actions[new_idx], actions[step_idx]
            self.config_mgr.save_profile()
            self._render_multi_steps(bdata)

    def _render_multi_steps(self, bdata):
        for child in self.multi_steps_scroll.winfo_children():
            child.destroy()

        actions = bdata.get("actions", [])
        if hasattr(self, "lbl_multi_count"):
            self.lbl_multi_count.configure(text=f"Kroky v řetězci akcí ({len(actions)}):")

        if not actions:
            lbl_empty = ctk.CTkLabel(
                self.multi_steps_scroll,
                text="Řetězec je prázdný. Klikněte na '+ Přidat krok' nebo přetáhněte akce z knihovny vpravo.",
                font=ctk.CTkFont(size=11),
                text_color="#64748B"
            )
            lbl_empty.pack(pady=8)
            return

        for s_idx, step in enumerate(actions):
            row = ctk.CTkFrame(self.multi_steps_scroll, height=34, fg_color="#141620", corner_radius=6, border_width=1, border_color="#242738")
            row.pack(fill="x", pady=3, padx=2)
            row.pack_propagate(False)

            lbl_num = ctk.CTkLabel(row, text=f"{s_idx + 1}.", font=ctk.CTkFont(size=11, weight="bold"), text_color="#FF7A29", width=22)
            lbl_num.pack(side="left", padx=(6, 2))

            stype = step.get("action_type", "")
            sparam = step.get("action_param", "")
            slabel = step.get("label", "")
            summary = self._format_multi_step_summary(stype, sparam, slabel)

            lbl_txt = ctk.CTkLabel(row, text=summary, font=ctk.CTkFont(size=11), text_color="#E2E8F0", anchor="w")
            lbl_txt.pack(side="left", fill="x", expand=True, padx=4)

            if s_idx > 0:
                btn_up = ctk.CTkButton(
                    row, text="▲", width=24, height=24, corner_radius=4,
                    fg_color="#1E202C", hover_color="#2A2E40", text_color="#CBD5E1",
                    font=ctk.CTkFont(size=9), command=lambda si=s_idx: self._move_multi_step(si, -1)
                )
                btn_up.pack(side="right", padx=1)

            if s_idx < len(actions) - 1:
                btn_down = ctk.CTkButton(
                    row, text="▼", width=24, height=24, corner_radius=4,
                    fg_color="#1E202C", hover_color="#2A2E40", text_color="#CBD5E1",
                    font=ctk.CTkFont(size=9), command=lambda si=s_idx: self._move_multi_step(si, 1)
                )
                btn_down.pack(side="right", padx=1)

            btn_del = ctk.CTkButton(
                row, text="✕", width=24, height=24, corner_radius=4,
                fg_color="#241418", hover_color="#3A171D", text_color="#E74C3C",
                font=ctk.CTkFont(size=11, weight="bold"), command=lambda si=s_idx: self._delete_multi_step(si)
            )
            btn_del.pack(side="right", padx=(2, 6))

    def _format_multi_step_summary(self, stype, sparam, slabel):
        if stype == "delay":
            return f"⏳ Čekání / Pauza: {sparam} ms"
        elif stype == "app":
            name = os.path.basename(sparam) if sparam else "Program"
            return f"🚀 Spustit program: {name}"
        elif stype == "url":
            return f"🌐 Otevřít web: {sparam}"
        elif stype == "hotkey":
            return f"⌨ Klávesová zkratka: {sparam.upper()}"
        elif stype == "obs":
            p = str(sparam or "")
            if p.startswith("scene:"): return f"🔴 OBS: Přepnout scénu ({p[6:]})"
            elif p.startswith("mute:"): return f"🔇 OBS: Ztlumit ({p[5:]})"
            elif p == "toggle_stream": return "🔴 OBS: Vysílání (Stream)"
            elif p == "toggle_record": return "⏺ OBS: Nahrávání (Record)"
            return f"🔴 OBS: {p}"
        elif stype == "media":
            return f"🎵 Média: {sparam.upper()}"
        elif stype == "volume":
            return f"🔊 Hlasitost: {sparam.upper()}"
        elif stype == "profile":
            profs = self.config_mgr.list_profiles() if self.config_mgr else []
            prof_name = next((p["name"] for p in profs if p["id"] == str(sparam)), str(sparam))
            return f"🏷️ Přepnout profil: {prof_name}"
        elif stype == "discord":
            disc_labels = {"mute": "Ztlumit mikrofon", "deafen": "Ztlumit sluchátka", "open": "Otevřít Discord", "disconnect": "Odpojit z hovoru"}
            return f"🎙️ Discord: {disc_labels.get(sparam, sparam)}"
        elif stype == "system_mic":
            return "🎙️ Ztlumit mikrofon PC (Systém)"
        elif stype == "twitch":
            tw_labels = {
                "marker": "Značka ve streamu (Marker)",
                "clip": "Vytvořit klip (Clip)",
                "clear_chat": "Vymazat chat",
                "toggle_shield": "Režim štítu (Shield Mode)",
                "open_dashboard": "Panel vysílání",
                "toggle_emote_only": "Chat: Pouze emote",
                "toggle_sub_only": "Chat: Pouze subs",
                "toggle_slow_mode": "Chat: Pomalý režim",
            }
            if str(sparam).startswith("commercial:"):
                return f"🟣 Twitch: Reklama {str(sparam).split(':')[1]}s"
            if str(sparam).startswith("chat:"):
                return f"🟣 Twitch Chat: {str(sparam)[5:]}"
            return f"🟣 Twitch: {tw_labels.get(sparam, sparam)}"
        elif stype == "page":
            return f"📄 Stránka: {sparam}"
        return f"{stype}: {sparam or slabel}"

    def _needs_target_row(self, act_type, act_param):
        """Vrací True, pokud akce vyžaduje výběr cíle/parametru v Property Inspectoru."""
        if act_type in ("none", "multi"):
            return False
        if act_type in ("discord", "media", "volume", "system_mic"):
            return False
        if act_type == "profile":
            return True
        if act_type == "twitch":
            p = str(act_param or "")
            if p.startswith("commercial:") or p.startswith("chat:") or p.startswith("marker:"):
                return True
            return False
        if act_type == "obs":
            p = str(act_param or "")
            if p.startswith("scene:") or p.startswith("mute:") or p.startswith("vol_"):
                return True
            return False
        if act_type == "page":
            p = str(act_param or "")
            if p.startswith("goto:"):
                return True
            return False
        if act_type == "folder":
            return False
        if act_type in ("app", "url", "delay"):
            return True
        if act_type == "hotkey":
            p = str(act_param or "").lower()
            if p in ("win+shift+s", "screenshot", "win+l", "lock", "ctrl+c", "ctrl+v", "win+e"):
                return False
            return True
        return False

    def _get_target_row_caption(self, act_type, act_param):
        """Vrací vhodný popisek pro řádek výběru cíle v inspektoru."""
        if act_type == "profile":
            return "Cílový profil:"
        elif act_type == "app":
            return "Program / Aplikace:"
        elif act_type == "url":
            return "Webová adresa:"
        elif act_type == "delay":
            return "Doba čekání:"
        elif act_type == "hotkey":
            return "Klávesová zkratka:"
        elif act_type == "obs":
            p = str(act_param or "")
            if p.startswith("scene:"):
                return "Cílová scéna OBS:"
            elif p.startswith("mute:") or p.startswith("vol_"):
                return "Audio stopa OBS:"
            return "Cíl OBS:"
        elif act_type == "page":
            return "Cílová stránka:"
        elif act_type == "twitch":
            p = str(act_param or "")
            if p.startswith("commercial:"):
                return "Délka reklamy:"
            elif p.startswith("chat:"):
                return "Zpráva do chatu:"
            elif p.startswith("marker:"):
                return "Popis značky:"
            return "Twitch cíl:"
        return "Cíl / Akce:"

    def _format_action_title(self, act_type, act_param, idx):
        """Formátuje nadpis akce ve stylu Stream Deck (např. Discord: Ztlumit mikrofon)."""
        if act_type == "multi":
            return "Multi-Action:  Řetězec akcí"
        elif act_type == "twitch":
            p = str(act_param or "")
            if p == "marker" or p.startswith("marker:"):
                desc = p[7:].strip() if p.startswith("marker:") else ""
                return f"Twitch:  Značka ve streamu ({desc})" if desc else "Twitch:  Značka ve streamu (Stream Marker)"
            elif p in ("clip", "create_clip"):
                return "Twitch:  Vytvořit klip (Create Clip)"
            elif p.startswith("commercial:"):
                sec = p.split(":", 1)[1]
                return f"Twitch:  Spustit reklamu ({sec}s)"
            elif p == "commercial":
                return "Twitch:  Spustit reklamu (30s)"
            elif p in ("clear_chat", "clear"):
                return "Twitch:  Vymazat chat (Clear Chat)"
            elif p in ("toggle_shield", "shield"):
                return "Twitch:  Režim štítu (Shield Mode)"
            elif p in ("toggle_emote_only", "emote_only"):
                return "Twitch:  Chat: Pouze emoce (Emote-Only)"
            elif p in ("toggle_sub_only", "sub_only"):
                return "Twitch:  Chat: Pouze odběratelé (Sub-Only)"
            elif p in ("toggle_slow_mode", "slow_mode"):
                return "Twitch:  Chat: Pomalý režim (Slow Mode)"
            elif p.startswith("chat:"):
                return f"Twitch:  Chat: {p[5:]}"
            elif p in ("open_dashboard", "dashboard"):
                return "Twitch:  Panel vysílání (Stream Manager)"
            elif p in ("open_channel", "channel", "open"):
                return "Twitch:  Otevřít Twitch kanál"
            return f"Twitch:  {p}"
        elif act_type == "page":
            p = str(act_param or "")
            pages = self.config_mgr.profile.get("pages", []) if self.config_mgr else []
            if p == "next": return "Stránka:  Další stránka"
            elif p == "prev": return "Stránka:  Předchozí stránka"
            elif p.startswith("goto:"):
                try:
                    idx = int(p[5:])
                    p_name = pages[idx].get("name", f"Stránka {idx + 1}") if 0 <= idx < len(pages) else f"Stránka {idx + 1}"
                    return f"Stránka:  Přejít na '{p_name}'"
                except Exception:
                    return f"Stránka:  Přejít na #{p[5:]}"
            elif p.startswith("folder:"):
                try:
                    idx = int(p[7:])
                    p_name = pages[idx].get("name", f"Složka {idx + 1}") if 0 <= idx < len(pages) else f"Složka {idx + 1}"
                    return f"Složka:  Otevřít '{p_name}'"
                except Exception:
                    return f"Složka:  Vstoupit #{p[7:]}"
            elif p == "back": return "Stránka:  Zpět"
            return f"Stránka:  {p}"
        elif act_type == "delay":
            return f"Časovač:  Pauza ({act_param} ms)"
        elif act_type == "obs":
            p = str(act_param or "")
            if p == "toggle_stream": return "OBS:  Spustit / Zastavit vysílání"
            elif p == "toggle_record": return "OBS:  Spustit / Zastavit záznam"
            elif p in ("toggle_record_pause", "pause_record"): return "OBS:  Pozastavit záznam"
            elif p == "next_scene": return "OBS:  Další scéna"
            elif p == "prev_scene": return "OBS:  Předchozí scéna"
            elif p == "toggle_virtual_cam": return "OBS:  Virtuální webkamera"
            elif p in ("save_replay_buffer", "replay_buffer"): return "OBS:  Uložit Replay buffer"
            elif p == "toggle_replay_buffer": return "OBS:  Zapnout / Vypnout Replay buffer"
            elif p.startswith("scene:"): return f"OBS:  Přepnout scénu ({p[6:]})"
            elif p.startswith("mute:"): return f"OBS:  Ztlumit zvuk ({p[5:]})"
            elif p.startswith("vol_up:"): return f"OBS:  Hlasitost + ({p[7:]})"
            elif p.startswith("vol_down:"): return f"OBS:  Hlasitost - ({p[9:]})"
            return f"OBS Studio:  {p}"
        elif act_type == "discord":
            p = str(act_param or "")
            disc_titles = {
                "mute": "Discord:  Ztlumit mikrofon",
                "deafen": "Discord:  Ztlumit sluchátka (Deafen)",
                "ptt": "Discord:  Push-to-Talk (PTT)",
                "open": "Discord:  Otevřít aplikaci",
                "disconnect": "Discord:  Odpojit hovor"
            }
            return disc_titles.get(p, "Discord:  Hlas & Komunikace")
        elif act_type == "media":
            p = str(act_param or "")
            med_titles = {
                "play_pause": "Média:  Přehrát / Pozastavit",
                "next": "Média:  Další skladba",
                "prev": "Média:  Předchozí skladba",
                "stop": "Média:  Zastavit přehrávání"
            }
            return med_titles.get(p, "Média:  Ovládání přehrávání")
        elif act_type == "volume":
            p = str(act_param or "")
            vol_titles = {
                "up": "Zvuk:  Zvýšit hlasitost (+)",
                "down": "Zvuk:  Snížit hlasitost (-)",
                "mute": "Zvuk:  Ztlumit zvuk (Mute)"
            }
            return vol_titles.get(p, "Zvuk:  Hlasitost")
        elif act_type == "app":
            p = str(act_param or "").lower()
            app_names = {
                "chrome": "Google Chrome", "edge": "Microsoft Edge", "spotify": "Spotify",
                "discord": "Discord", "steam": "Steam", "obs": "OBS Studio", "calc": "Kalkulačka",
                "explorer": "Průzkumník souborů", "taskmgr": "Správce úloh", "notepad": "Poznámkový blok",
                "mspaint": "Malování", "cmd": "Příkazový řádek", "powershell": "PowerShell",
                "settings": "Nastavení Windows", "code": "VS Code",
                "davinci": "DaVinci Resolve", "resolve": "DaVinci Resolve",
                "epic": "Epic Games Launcher", "epicgames": "Epic Games Launcher"
            }
            if p in app_names:
                return f"Aplikace:  {app_names[p]}"
            elif act_param:
                base = os.path.splitext(os.path.basename(act_param))[0]
                return f"Aplikace:  {base}"
            return "Aplikace:  Otevřít program"
        elif act_type == "profile":
            profs = self.config_mgr.list_profiles() if self.config_mgr else []
            prof_name = next((p["name"] for p in profs if p["id"] == str(act_param)), str(act_param))
            return f"Profil:  {prof_name}"
        elif act_type == "system_mic":
            return "Systém:  Ztlumit mikrofon PC"
        elif act_type == "hotkey":
            p = str(act_param or "").lower()
            hk_names = {
                "win+shift+s": "Systém:  Screenshot (Výstřižek)",
                "screenshot": "Systém:  Screenshot",
                "win+l": "Systém:  Zamknout PC",
                "lock": "Systém:  Zamknout PC",
                "ctrl+c": "Systém:  Kopírovat (Ctrl+C)",
                "ctrl+v": "Systém:  Vložit (Ctrl+V)",
                "win+e": "Systém:  Průzkumník souborů"
            }
            if p in hk_names:
                return hk_names[p]
            return f"Systém:  Zkratka ({act_param.upper()})" if act_param else "Systém:  Klávesová zkratka"

        titles = {
            "url": "Web:  Otevřít stránku",
            "none": f"Klávesa K{idx + 1}:  Nepřiřazeno"
        }
        return titles.get(act_type, f"{act_type.capitalize()}:  {act_param or 'Přiřazeno'}")

    def _format_action_detail(self, act_type, act_param):
        """Formátuje detailní cestu nebo popis pod řádkem akce."""
        if act_type == "multi":
            return "Spustí sekvenci naskládaných akcí za sebou (Multi-Action)."
        elif act_type == "page":
            p = str(act_param or "")
            pages = self.config_mgr.profile.get("pages", []) if self.config_mgr else []
            if p == "next": return "Přepne zobrazení na následující stránku tlačítek."
            elif p == "prev": return "Přepne zobrazení na předchozí stránku tlačítek."
            elif p.startswith("goto:"):
                try:
                    idx = int(p[5:])
                    p_name = pages[idx].get("name", f"Stránka {idx + 1}") if 0 <= idx < len(pages) else f"Stránka {idx + 1}"
                    return f"Okamžitě přepne na {p_name}."
                except Exception:
                    return f"Okamžitě přepne na stránku #{p[5:]}."
            elif p.startswith("folder:"):
                try:
                    idx = int(p[7:])
                    p_name = pages[idx].get("name", "Složka") if 0 <= idx < len(pages) else "Složka"
                    return f"Otevře podstránku (složku) '{p_name}'."
                except Exception:
                    return f"Otevře podstránku (složku) #{p[7:]}."
            elif p == "back": return "Vrátí se na nadřazenou stránku."
            return f"Přepnutí stránky: {p}"
        elif act_type == "delay":
            return f"Čeká {act_param} milisekund před provedením další akce."
        elif act_type == "app":
            p = str(act_param or "").lower()
            app_descs = {
                "chrome": "Spustí webový prohlížeč Google Chrome.",
                "edge": "Spustí webový prohlížeč Microsoft Edge.",
                "spotify": "Spustí aplikaci Spotify pro poslech hudby a podcastů.",
                "discord": "Spustí aplikaci Discord nebo ji přenese do popředí.",
                "steam": "Spustí herní platformu Steam.",
                "obs": "Spustí streamovací software OBS Studio.",
                "calc": "Otevře aplikaci Kalkulačka (Windows Calc).",
                "explorer": "Otevře okno Průzkumníka souborů Windows.",
                "taskmgr": "Otevře Správce úloh Windows (Task Manager).",
                "notepad": "Otevře textový editor Poznámkový blok.",
                "mspaint": "Otevře grafický editor Malování.",
                "cmd": "Otevře Příkazový řádek (CMD).",
                "powershell": "Otevře Windows PowerShell konzoli.",
                "settings": "Otevře systémové Nastavení Windows.",
                "code": "Otevře vývojové prostředí Visual Studio Code.",
                "davinci": "Spustí profesionální editor videa DaVinci Resolve.",
                "resolve": "Spustí profesionální editor videa DaVinci Resolve.",
                "epic": "Spustí herního klienta Epic Games Launcher.",
                "epicgames": "Spustí herního klienta Epic Games Launcher."
            }
            if p in app_descs:
                return app_descs[p]
            return f'Spustí program: "{act_param}"' if act_param else "Vyberte program z rozbalovací nabídky nebo zvolte soubor z počítače."
        elif act_type == "profile":
            profs = self.config_mgr.list_profiles() if self.config_mgr else []
            prof_name = next((p["name"] for p in profs if p["id"] == str(act_param)), str(act_param))
            return f"Okamžitě přepne profil zařízení na '{prof_name}'."
        elif act_type == "system_mic":
            return "Ztlumí/odtlumí hardwarový nahrávací mikrofon Windows bez ovlivnění jiných nastavení."
        elif act_type == "url":
            return f'"{act_param}"' if act_param else "Zadejte webovou URL adresu (např. https://youtube.com)."
        elif act_type == "hotkey":
            p = str(act_param or "").lower()
            if p in ("win+shift+s", "screenshot"): return "Spustí nástroj Výstřižky (Win+Shift+S) pro vytvoření snímku obrazovky."
            elif p in ("win+l", "lock"): return "Okamžitě uzamkne počítač (Win+L)."
            elif p == "ctrl+c": return "Zkopíruje označený text nebo soubory do schránky (Ctrl+C)."
            elif p == "ctrl+v": return "Vloží obsah ze schránky na pozici kurzoru (Ctrl+V)."
            elif p == "win+e": return "Otevře okno Průzkumníka souborů (Win+E)."
            return f'Stiskne klávesovou zkratku: {act_param.upper()}' if act_param else "Klikněte pro zadání klávesové zkratky."
        elif act_type == "volume":
            p = str(act_param or "")
            if p == "up": return "Zvýší hlavní systémovou hlasitost Windows (+2%)."
            elif p == "down": return "Sníží hlavní systémovou hlasitost Windows (-2%)."
            elif p == "mute": return "Ztlumí nebo obnoví hlavní systémový zvuk Windows (Mute)."
            return "Ovládání hlavní hlasitosti systému Windows."
        elif act_type == "media":
            p = str(act_param or "")
            if p == "play_pause": return "Spustí nebo pozastaví přehrávání hudby či videa (Play / Pause)."
            elif p == "next": return "Přeskočí na následující skladbu nebo stopu."
            elif p == "prev": return "Přeskočí na předchozí skladbu nebo stopu."
            elif p == "stop": return "Zastaví přehrávání multimédií (Stop)."
            return "Ovládání multimediálního přehrávače Windows."
        elif act_type == "discord":
            p = str(act_param or "")
            if p == "mute":
                return "Ztlumí/odtlumí mikrofon v Discordu (Ctrl+Shift+M). Pro fungování na pozadí v hrách a DaVinci přidejte zkratku v nastavení Discordu."
            elif p == "deafen":
                return "Ztlumí/odtlumí sluchátka v Discordu (Ctrl+Shift+D). Pro fungování na pozadí přidejte zkratku v nastavení Discordu."
            elif p == "ptt":
                return "Push-to-Talk pro Discord (Ctrl+Shift+P). Pro pozadí nastavte klávesovou zkratku v nastavení Discordu."
            elif p == "open":
                return "Spustí aplikaci Discord nebo ji přenese do popředí."
            elif p == "disconnect":
                return "Okamžitě odpojí probíhající hovor v Discordu (Ctrl+Shift+H)."
            return f"Discord akce: {act_param}"
        elif act_type == "obs":
            p = str(act_param or "")
            if p == "toggle_stream": return "Jedním stiskem spustí nebo zastaví živé vysílání v OBS."
            elif p == "toggle_record": return "Jedním stiskem spustí nebo zastaví nahrávání v OBS."
            elif p in ("toggle_record_pause", "pause_record"): return "Pozastaví nebo obnoví probíhající nahrávání videa."
            elif p == "next_scene": return "Přepne na následující scénu v seznamu scén OBS."
            elif p == "prev_scene": return "Přepne na předchozí scénu v seznamu scén OBS."
            elif p == "toggle_virtual_cam": return "Zapne nebo vypne virtuální webkameru OBS pro Discord/Meet."
            elif p in ("save_replay_buffer", "replay_buffer"): return "Uloží herní klip z Replay bufferu do souboru."
            elif p == "toggle_replay_buffer": return "Spustí nebo zastaví paměťový Replay buffer v OBS."
            elif p.startswith("scene:"): return f'Okamžitě přepne vysílání na programovou scénu "{p[6:]}".'
            elif p.startswith("mute:"): return f'Přepne stav ztlumení (Mute/Unmute) pro audio stopu "{p[5:]}".'
            elif p.startswith("vol_up:"): return f'Zvýší hlasitost audio stopy "{p[7:]}" o 2 dB.'
            elif p.startswith("vol_down:"): return f'Sníží hlasitost audio stopy "{p[9:]}" o 2 dB.'
            return f'OBS příkaz: {act_param}'
        elif act_type == "twitch":
            p = str(act_param or "")
            if p == "marker" or p.startswith("marker:"):
                return "Vloží do běžícího živého vysílání Twitch časovou značku pro snadné vyhledání při střihu."
            elif p in ("clip", "create_clip"):
                return "Vytvoří klip z posledních sekund streamu a zkopíruje odkaz na editaci do schránky Windows."
            elif p.startswith("commercial:"):
                return f"Spustí pro diváky reklamu v délce {p.split(':')[1]} sekund."
            elif p in ("clear_chat", "clear"):
                return "Okamžitě smaže všechny předchozí zprávy v chatu živého vysílání."
            elif p in ("toggle_shield", "shield"):
                return "Přepne bezpečnostní Režim štítu (Shield Mode) v moderaci streamu."
            elif p in ("toggle_emote_only", "emote_only"):
                return "Přepne režim chatu, kdy lze posílat pouze emotikony."
            elif p in ("toggle_sub_only", "sub_only"):
                return "Přepne režim chatu, kdy mohou psát pouze předplatitelé (odběratelé)."
            elif p in ("toggle_slow_mode", "slow_mode"):
                return "Přepne pomalý režim chatu (Slow Mode) s omezením frekvence zpráv."
            elif p.startswith("chat:"):
                return f'Odešle do chatu zprávu nebo příkaz: "{p[5:]}".'
            elif p in ("open_dashboard", "dashboard"):
                return "Otevře webový Panel vysílání (Twitch Creator Dashboard / Stream Manager)."
            elif p in ("open_channel", "channel", "open"):
                return "Otevře domovskou stránku vašeho Twitch kanálu."
            return f"Twitch akce: {act_param}"
        elif act_type == "none":
            return "Přetáhněte akci z knihovny vpravo nebo klikněte na dlaždici pro výběr ikony."
        return str(act_param) if act_param else ""

    def _update_inspector_tile(self, icon, label, custom_icon=""):
        """Aktualizuje vzhled levé dlaždice v inspektoru."""
        img = None
        if custom_icon:
            img = load_custom_image(custom_icon, size=(36, 36))
        elif icon and icon != "none":
            img = get_asset_icon(icon, size=(36, 36))

        if img:
            self.lbl_tile_icon.configure(image=img, text="")
        else:
            plus_img = get_asset_icon("empty_plus", size=(20, 20))
            if plus_img:
                self.lbl_tile_icon.configure(image=plus_img, text="")
            else:
                self.lbl_tile_icon.configure(image=None, text="+", font=ctk.CTkFont(size=16, weight="bold"), text_color="#3E4358")

        clean = label.strip()
        if clean:
            self.lbl_tile_text.configure(text=clean, text_color="#FFFFFF")
            self.lbl_tile_icon.place(relx=0.5, rely=0.38, anchor="center")
            self.lbl_tile_text.place(relx=0.5, rely=0.76, anchor="center")
        else:
            self.lbl_tile_text.place_forget()
            self.lbl_tile_icon.place(relx=0.5, rely=0.50, anchor="center")

    def _on_tile_clicked(self):
        """Kliknutí na dlaždici otevře výběr ikony."""
        if not self.selected_item:
            return
        itype = self.selected_item[0]
        if itype == "button":
            self._open_icon_picker()

    def _toggle_font_style(self):
        """Přepne formát textu (Velká písmena / Standardní)."""
        if not self.selected_item or self.selected_item[0] != "button":
            return
        idx = self.selected_item[1]
        buttons = self.config_mgr.profile.get("buttons", [])
        if idx >= len(buttons):
            return
        bdata = buttons[idx]
        lbl = bdata.get("label", "")
        if not lbl:
            return
        if lbl.isupper():
            new_lbl = lbl.title()
        else:
            new_lbl = lbl.upper()
        self.entry_label.delete(0, "end")
        self.entry_label.insert(0, new_lbl)
        self._on_label_changed()

    def _browse_action_target(self):
        """Tlačítko procházení souborů pro řádek akce (složka)."""
        if not self.selected_item or self.selected_item[0] != "button":
            return
        idx = self.selected_item[1]
        buttons = self.config_mgr.profile.get("buttons", [])
        bdata = buttons[idx] if idx < len(buttons) else {}
        atype = bdata.get("action_type", "none")

        new_p = None
        if atype in ("app", "none"):
            dlg = AppPickerDialog(self, title="Výběr aplikace z počítače a plochy")
            app_res = dlg.get_result()
            if app_res:
                new_p = app_res["path"]
                bdata["action_type"] = "app"
                bdata["action_param"] = new_p
                clean_name = app_res.get("name", "")
                if not bdata.get("label"):
                    bdata["label"] = clean_name[:10]
                    self.entry_label.delete(0, "end")
                    self.entry_label.insert(0, bdata["label"])
                bdata["icon"] = app_res.get("icon", "app")
                if app_res.get("custom_icon"):
                    bdata["custom_icon"] = app_res["custom_icon"]
        elif atype == "url":
            dialog = ctk.CTkInputDialog(text="Zadejte webovou URL adresu:", title="Webová adresa")
            new_p = dialog.get_input()
            if new_p:
                bdata["action_param"] = new_p
        elif atype == "hotkey":
            dialog = ctk.CTkInputDialog(text="Zadejte klávesovou zkratku (např. ctrl+shift+m):", title="Klávesová zkratka")
            new_p = dialog.get_input()
            if new_p:
                bdata["action_param"] = new_p

        elif atype == "obs":
            dlg = OBSActionChooserDialog(self, bdata.get("action_param", ""), self.obs_controller)
            res = dlg.get_result()
            if res:
                bdata["action_type"] = "obs"
                bdata["action_param"] = res["param"]
                bdata["label"] = res["label"]
                bdata["icon"] = res["icon"]
                new_p = res["param"]

        elif atype == "page":
            pages = self.config_mgr.profile.get("pages", [])
            cur = self.config_mgr.profile.get("active_page", 0)
            dlg = PageChooserDialog(self, pages, cur)
            res = dlg.get_result()
            if res is not None:
                new_p = f"goto:{res}"
                bdata["action_type"] = "page"
                bdata["action_param"] = new_p
                pg_name = pages[res].get("name", f"Stránka {res+1}")
                bdata["label"] = pg_name[:10]
                bdata["icon"] = "folder" if pages[res].get("is_folder") else "next"

        elif atype == "profile":
            profs = self.config_mgr.list_profiles() if self.config_mgr else []
            cur = getattr(self.config_mgr, "active_profile_id", "default")
            dlg = ProfileChooserDialog(self, profs, cur)
            res = dlg.get_result()
            if res is not None:
                new_p = res
                bdata["action_type"] = "profile"
                bdata["action_param"] = new_p
                prof_name = next((p["name"] for p in profs if p["id"] == res), res)
                bdata["label"] = prof_name[:10]
                bdata["icon"] = "folder"

        if new_p:
            self.config_mgr.profile["buttons"][idx] = bdata
            self.config_mgr.save_profile()
            self.entry_param.delete(0, "end")
            self.entry_param.insert(0, bdata["action_param"])
            self.entry_label.delete(0, "end")
            self.entry_label.insert(0, bdata.get("label", ""))
            self.lbl_insp_title.configure(text=self._format_action_title(bdata["action_type"], bdata["action_param"], idx))
            self.lbl_param_detail.configure(text=self._format_action_detail(bdata["action_type"], bdata["action_param"]))
            w = self.btn_widgets[idx]
            self._update_button_widget_ui(w, bdata.get("icon", ""), bdata.get("label", ""), bdata.get("custom_icon", ""))
            self._update_display_cell_ui(idx, bdata.get("icon", ""), bdata.get("label", ""), bdata.get("custom_icon", ""))
            self._update_inspector_tile(bdata.get("icon", ""), bdata.get("label", ""), bdata.get("custom_icon", ""))
            if self.serial and self.serial.is_connected:
                self.serial.update_button(idx, bdata.get("icon", ""), bdata.get("label", ""))

    def _on_param_entry_changed(self, e=None):
        """Při ručním vepsání do pole cíle/akce."""
        if not self.selected_item or self.selected_item[0] != "button":
            return
        idx = self.selected_item[1]
        new_val = self.entry_param.get().strip()
        bdata = self.config_mgr.profile["buttons"][idx]
        bdata["action_param"] = new_val
        self.config_mgr.save_profile()
        self.lbl_param_detail.configure(text=self._format_action_detail(bdata.get("action_type", "none"), new_val))

    def _open_icon_picker(self):
        """Otevře okno s výběrem ikony."""
        if not self.selected_item or self.selected_item[0] != "button":
            return
        idx = self.selected_item[1]
        buttons = self.config_mgr.profile.get("buttons", [])
        bdata = buttons[idx] if idx < len(buttons) else {}

        current_icon = bdata.get("icon", "none")
        current_custom = bdata.get("custom_icon", "")

        def _on_chosen(icon_key, custom_path):
            if custom_path:
                self.config_mgr.profile["buttons"][idx]["icon"] = "custom"
                self.config_mgr.profile["buttons"][idx]["custom_icon"] = custom_path
            else:
                self.config_mgr.profile["buttons"][idx]["icon"] = icon_key
                self.config_mgr.profile["buttons"][idx]["custom_icon"] = ""

            self.config_mgr.save_profile()

            label = self.config_mgr.profile["buttons"][idx].get("label", "")
            w = self.btn_widgets[idx]
            self._update_button_widget_ui(w, icon_key, label, custom_path)
            self._update_display_cell_ui(idx, icon_key, label, custom_path)
            self._update_inspector_tile(icon_key, label, custom_path)

            if self.serial and self.serial.is_connected:
                self.serial.update_button(idx, icon_key if icon_key != "none" else "", label)

        IconPickerModal(self, current_icon, current_custom, _on_chosen)

    def _edit_action_param(self):
        """Umožňuje přímou úpravu URL, klávesové zkratky, OBS nebo režimu enkodéru v inspektoru."""
        if not self.selected_item:
            return
        itype, idx = self.selected_item[0], self.selected_item[1]

        if itype == "encoder":
            encoders = self.config_mgr.profile.get("encoders", [])
            edata = encoders[idx] if idx < len(encoders) else {}
            dlg = OBSEncoderModeDialog(self, idx, edata, self.obs_controller)
            res = dlg.get_result()
            if res:
                edata["name"] = res["name"]
                edata["cw"] = res["cw"]
                edata["ccw"] = res["ccw"]
                edata["btn"] = res["btn"]
                self.config_mgr.profile["encoders"][idx] = edata
                self.config_mgr.save_profile()

                self.entry_label.delete(0, "end")
                self.entry_label.insert(0, res["name"])
                self.enc_widgets[idx]._lbl_tag.configure(text=res["name"])
                self.enc_widgets[idx]._lbl_desc.configure(text=res["desc"], text_color="#FF7A29")

                self.lbl_insp_title.configure(text=f"Enkodér:  E{idx + 1} ({res['name']})")
                self.entry_param.configure(state="normal")
                self.entry_param.delete(0, "end")
                self.entry_param.insert(0, res["cw"]["action_type"].upper())
                detail_text = f"Otáčení CW: {res['cw']['action_param']} | CCW: {res['ccw']['action_param']} | Stisk: {res['btn']['action_param']}"
                self.lbl_param_detail.configure(text=detail_text)
            return

        buttons = self.config_mgr.profile.get("buttons", [])
        bdata = buttons[idx] if idx < len(buttons) else {}
        atype = bdata.get("action_type", "none")

        new_p = None
        if atype == "url":
            dialog = ctk.CTkInputDialog(text="Zadejte webovou URL adresu:", title="Webová adresa")
            new_p = dialog.get_input()
        elif atype == "hotkey":
            dialog = ctk.CTkInputDialog(text="Zadejte klávesovou zkratku (např. ctrl+shift+m):", title="Klávesová zkratka")
            new_p = dialog.get_input()
        elif atype == "app":
            new_p = filedialog.askopenfilename(title="Vyberte program k spuštění", filetypes=[("Programy", "*.exe;*.bat;*.cmd;*.*")])
        elif atype == "obs":
            dlg = OBSActionChooserDialog(self, bdata.get("action_param", ""), self.obs_controller)
            res = dlg.get_result()
            if res:
                bdata["action_type"] = "obs"
                bdata["action_param"] = res["param"]
                bdata["label"] = res["label"]
                bdata["icon"] = res["icon"]
                new_p = res["param"]
        elif atype == "page":
            pages = self.config_mgr.profile.get("pages", [])
            cur = self.config_mgr.profile.get("active_page", 0)
            dlg = PageChooserDialog(self, pages, cur)
            res = dlg.get_result()
            if res is not None:
                new_p = f"goto:{res}"
                bdata["action_type"] = "page"
                bdata["action_param"] = new_p
                pg_name = pages[res].get("name", f"Stránka {res+1}")
                bdata["label"] = pg_name[:10]
        elif atype == "delay":
            dlg = ctk.CTkInputDialog(text="Zadejte dobu čekání v ms:", title="Pauza / Časovač")
            val = dlg.get_input()
            if val and val.strip():
                new_p = val.strip()
                bdata["action_type"] = "delay"
                bdata["action_param"] = new_p
                bdata["label"] = f"Pauza {new_p}ms"[:10]

        if new_p:
            bdata["action_param"] = new_p
            self.config_mgr.profile["buttons"][idx] = bdata
            self.config_mgr.save_profile()
            self.entry_param.delete(0, "end")
            self.entry_param.insert(0, new_p)
            self.entry_label.delete(0, "end")
            self.entry_label.insert(0, bdata.get("label", ""))
            self.lbl_insp_title.configure(text=self._format_action_title(bdata.get("action_type", "none"), new_p, idx))
            self.lbl_param_detail.configure(text=self._format_action_detail(bdata.get("action_type", "none"), new_p))
            w = self.btn_widgets[idx]
            self._update_button_widget_ui(w, bdata.get("icon", ""), bdata.get("label", ""), bdata.get("custom_icon", ""))
            self._update_display_cell_ui(idx, bdata.get("icon", ""), bdata.get("label", ""), bdata.get("custom_icon", ""))
            self._update_inspector_tile(bdata.get("icon", ""), bdata.get("label", ""), bdata.get("custom_icon", ""))
            if self.serial and self.serial.is_connected:
                self.serial.update_button(idx, bdata.get("icon", ""), bdata.get("label", ""))

    # =========================================================================
    #  PRAVÝ PANEL: KNIHOVNA AKCÍ S OSTRÝMI PNG IKONAMI
    # =========================================================================
    def _build_action_palette(self, parent):
        lbl_head = ctk.CTkLabel(parent, text="KNIHOVNA AKCÍ", font=ctk.CTkFont(size=12, weight="bold"), text_color="#7E849B")
        lbl_head.pack(anchor="w", padx=16, pady=(14, 6))

        search_box = ctk.CTkFrame(parent, fg_color="transparent")
        search_box.pack(fill="x", padx=14, pady=(0, 10))

        search_ico = get_asset_icon("search", size=(16, 16))
        self.search_entry = ctk.CTkEntry(
            search_box, 
            placeholder_text="  Hledat akci...", 
            height=34, 
            corner_radius=8, 
            fg_color="#0E0F15", 
            border_color="#26293A", 
            border_width=1, 
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12)
        )
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<KeyRelease>", self._on_search_filter)

        self.folders_scroll = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            scrollbar_button_color="#2B2E42",
            scrollbar_button_hover_color="#FF7A29"
        )
        self.folders_scroll.pack(fill="both", expand=True, padx=(8, 4), pady=(0, 10))

        categories = [
            {
                "title": "Stránky & Složky",
                "icon_name": "folder",
                "start_open": True,
                "items": [
                    {"label": "Další stránka",             "short": "Další str.", "icon": "next",       "type": "page", "param": "next"},
                    {"label": "Předchozí stránka",         "short": "Předch. str.","icon": "prev",       "type": "page", "param": "prev"},
                    {"label": "Přejít na stránku...",      "short": "Stránka",    "icon": "folder",     "type": "page", "param": "CUSTOM_PAGE"},
                    {"label": "Vytvořit novou složku...",  "short": "Složka",     "icon": "folder",     "type": "page", "param": "CUSTOM_FOLDER"},
                    {"label": "Zpět (Návrat)",             "short": "Zpět",       "icon": "back",       "type": "page", "param": "back"}
                ]
            },
            {
                "title": "Profily & Multitasking",
                "icon_name": "cat_system",
                "start_open": False,
                "items": [
                    {"label": "Přepnout profil...",        "short": "Profil",     "icon": "folder",     "type": "profile", "param": "CUSTOM_PROFILE"},
                    {"label": "Ztlumit mikrofon PC (Systém)", "short": "Mic PC",   "icon": "mic",        "type": "system_mic", "param": "toggle"}
                ]
            },
            {
                "title": "Řetězec akcí (Multi)",
                "icon_name": "cat_system",
                "start_open": False,
                "items": [
                    {"label": "Multi-Action tlačítko",     "short": "Multi",      "icon": "app",        "type": "multi", "param": ""},
                    {"label": "Časová pauza (Delay)...",   "short": "Pauza",      "icon": "pause",      "type": "delay", "param": "CUSTOM_DELAY"}
                ]
            },
            {
                "title": "OBS Studio",
                "icon_name": "cat_obs",
                "start_open": False,
                "items": [
                    {"label": "Spustit / Zastavit Stream", "short": "Stream",     "icon": "obs",        "type": "obs", "param": "toggle_stream"},
                    {"label": "Spustit / Zastavit Záznam", "short": "Záznam",     "icon": "rec",        "type": "obs", "param": "toggle_record"},
                    {"label": "Pozastavit Záznam",         "short": "Pauza Rec",  "icon": "pause",      "type": "obs", "param": "toggle_record_pause"},
                    {"label": "Další scéna OBS",          "short": "Další scéna","icon": "scene",      "type": "obs", "param": "next_scene"},
                    {"label": "Předchozí scéna OBS",      "short": "Předch. scéna","icon": "scene",    "type": "obs", "param": "prev_scene"},
                    {"label": "Přepnout na scénu...",      "short": "Scéna",      "icon": "scene",      "type": "obs", "param": "CUSTOM_SCENE"},
                    {"label": "Ztlumit zvuk (Mute OBS)...","short": "Mute OBS",   "icon": "mute",       "type": "obs", "param": "CUSTOM_MUTE"},
                    {"label": "Virtuální webkamera",       "short": "Virt. kamera","icon": "obs",       "type": "obs", "param": "toggle_virtual_cam"},
                    {"label": "Uložit Replay Buffer",      "short": "Replay",     "icon": "rec",        "type": "obs", "param": "save_replay_buffer"}
                ]
            },
            {
                "title": "Discord",
                "icon_name": "discord",
                "start_open": False,
                "items": [
                    {"label": "Ztlumit mikrofon",       "short": "Mute Mic",   "icon": "mic",     "type": "discord", "param": "mute"},
                    {"label": "Ztlumit sluchátka",       "short": "Deafen",     "icon": "headset", "type": "discord", "param": "deafen"},
                    {"label": "Otevřít Discord",         "short": "Discord",    "icon": "discord", "type": "discord", "param": "open"},
                    {"label": "Odpojit z hovoru",        "short": "Odpojit",    "icon": "mute",    "type": "discord", "param": "disconnect"}
                ]
            },
            {
                "title": "Twitch",
                "icon_name": "twitch",
                "start_open": False,
                "items": [
                    {"label": "Vytvořit značku (Stream Marker)", "short": "Značka",     "icon": "marker",  "type": "twitch", "param": "marker"},
                    {"label": "Vytvořit klip (Create Clip)",     "short": "Klip",       "icon": "clip",    "type": "twitch", "param": "clip"},
                    {"label": "Spustit reklamu 30s",            "short": "Reklama 30s","icon": "twitch",  "type": "twitch", "param": "commercial:30"},
                    {"label": "Spustit reklamu 60s",            "short": "Reklama 60s","icon": "twitch",  "type": "twitch", "param": "commercial:60"},
                    {"label": "Vymazat chat (Clear Chat)",       "short": "Smazat chat","icon": "trash",   "type": "twitch", "param": "clear_chat"},
                    {"label": "Režim štítu (Shield Mode)",       "short": "Štít",       "icon": "lock",    "type": "twitch", "param": "toggle_shield"},
                    {"label": "Režim chatu: Pouze emote",        "short": "Pouze emote","icon": "twitch",  "type": "twitch", "param": "toggle_emote_only"},
                    {"label": "Režim chatu: Pouze subs",         "short": "Pouze subs", "icon": "twitch",  "type": "twitch", "param": "toggle_sub_only"},
                    {"label": "Režim chatu: Pomalý režim",       "short": "Slow mode",  "icon": "twitch",  "type": "twitch", "param": "toggle_slow_mode"},
                    {"label": "Odeslat zprávu do chatu...",     "short": "Zpráva",     "icon": "twitch",  "type": "twitch", "param": "CUSTOM_CHAT"},
                    {"label": "Panel vysílání (Stream Manager)", "short": "Dashboard",  "icon": "twitch",  "type": "twitch", "param": "open_dashboard"},
                    {"label": "Otevřít Twitch kanál",            "short": "Twitch",     "icon": "twitch",  "type": "twitch", "param": "open_channel"}
                ]
            },
            {
                "title": "Zvuk & Média",
                "icon_name": "vol_up",
                "start_open": False,
                "items": [
                    {"label": "Zvýšit hlasitost (+)",  "short": "Hlas +",     "icon": "vol_up", "type": "volume", "param": "up"},
                    {"label": "Snížit hlasitost (-)",  "short": "Hlas -",     "icon": "vol_down", "type": "volume", "param": "down"},
                    {"label": "Ztlumit zvuk (Mute)",    "short": "Mute",       "icon": "mute", "type": "volume", "param": "mute"},
                    {"label": "Přehrát / Pozastavit",  "short": "Play/Pauza", "icon": "play", "type": "media", "param": "play_pause"},
                    {"label": "Další skladba",        "short": "Další",      "icon": "next", "type": "media", "param": "next"},
                    {"label": "Předchozí skladba",    "short": "Předchozí",  "icon": "prev", "type": "media", "param": "prev"},
                    {"label": "Zastavit přehrávání",  "short": "Stop",       "icon": "stop", "type": "media", "param": "stop"}
                ]
            },
            {
                "title": "Systém & Nástroje",
                "icon_name": "cat_system",
                "start_open": False,
                "items": [
                    {"label": "Otevřít aplikaci / hru...", "short": "Aplikace",   "icon": "cat_apps",   "type": "app",    "param": "CUSTOM"},
                    {"label": "Vlastní zkratka...",        "short": "Zkratka",    "icon": "hotkey",     "type": "hotkey", "param": "CUSTOM"},
                    {"label": "Screenshot (Win+Shift+S)",  "short": "Screenshot", "icon": "screenshot", "type": "hotkey", "param": "win+shift+s"},
                    {"label": "Zamknout PC (Win+L)",       "short": "Zamknout",   "icon": "lock",       "type": "hotkey", "param": "win+l"},
                    {"label": "Průzkumník souborů (Win+E)","short": "Soubory",    "icon": "folder",     "type": "hotkey", "param": "win+e"},
                    {"label": "Kopírovat (Ctrl+C)",        "short": "Kopírovat",  "icon": "copy",       "type": "hotkey", "param": "ctrl+c"},
                    {"label": "Vložit (Ctrl+V)",           "short": "Vložit",     "icon": "paste",      "type": "hotkey", "param": "ctrl+v"},
                    {"label": "Kalkulačka",                "short": "Kalkulačka", "icon": "calc",       "type": "app",    "param": "calc"}
                ]
            },
            {
                "title": "Web & Odkazy",
                "icon_name": "cat_web",
                "start_open": False,
                "items": [
                    {"label": "Webová adresa...",          "short": "Web",        "icon": "web",        "type": "url", "param": "CUSTOM"},
                    {"label": "YouTube",                   "short": "YouTube",    "icon": "youtube",    "type": "url", "param": "https://youtube.com"},
                    {"label": "Spotify",                   "short": "Spotify",    "icon": "spotify",    "type": "url", "param": "https://open.spotify.com"},
                    {"label": "Twitch",                    "short": "Twitch",     "icon": "twitch",     "type": "url", "param": "https://twitch.tv"}
                ]
            }
        ]

        for cat in categories:
            folder = CollapsibleFolder(
                self.folders_scroll,
                title=cat["title"],
                icon_name=cat["icon_name"],
                items=cat["items"],
                on_item_click=self._apply_palette_action,
                on_drag_start=self._on_drag_start,
                on_drag_motion=self._on_drag_motion,
                on_drag_end=self._on_drag_end,
                start_open=cat.get("start_open", False)
            )
            folder.pack(fill="x", padx=(4, 8), pady=3)
            self.folders.append(folder)

    def _on_search_filter(self, e):
        q = self.search_entry.get()
        for folder in self.folders:
            folder.filter_items(q)

    # =========================================================================
    #  ROBUSTNÍ DRAG & DROP (PLOVOUCÍ TOPLEVEL BEZ ZDVOJENÍ A GHOSTINGU)
    # =========================================================================
    def _on_drag_start(self, item, start_x, start_y):
        self._active_drag_item = item
        self._cleanup_drag_badge()

        # Plovoucí Toplevel okno - v systému Windows kresleno DWM kompozitorem,
        # což zcela eliminuje zdvojení (ghosting / smearing) na podkladových widgetech.
        try:
            top = tk.Toplevel(self.winfo_toplevel())
            top.overrideredirect(True)
            top.attributes("-topmost", True)
            top.configure(bg="#0D0E12")

            badge_frame = tk.Frame(top, bg="#FF7A29", padx=8, pady=4)
            badge_frame.pack()

            it_ico = get_asset_icon(item.get("icon", ""), size=(18, 18))
            tk_img = None
            if it_ico and hasattr(it_ico, "_dark_image"):
                resample = getattr(Image, "Resampling", Image).LANCZOS
                tk_img = ImageTk.PhotoImage(it_ico._dark_image.resize((18, 18), resample))

            lbl = tk.Label(
                badge_frame,
                text=f" {item['label']} ",
                font=("Segoe UI", 10, "bold"),
                fg="#0A0A0E",
                bg="#FF7A29",
                compound="left"
            )
            if tk_img:
                lbl.configure(image=tk_img)
                lbl.image = tk_img
            lbl.pack()

            self._drag_badge = top
            self._update_badge_pos(start_x, start_y)
        except Exception:
            self._drag_badge = None

    def _on_drag_motion(self, x_root, y_root):
        if self._drag_badge:
            self._update_badge_pos(x_root, y_root)
            self._highlight_hovered_target(x_root, y_root)

    def _update_badge_pos(self, x_root, y_root):
        if self._drag_badge:
            try:
                self._drag_badge.geometry(f"+{x_root + 14}+{y_root + 14}")
            except Exception:
                pass

    def _on_global_b1_motion(self, e):
        if getattr(self, "_is_resizing_inspector", False):
            now = time.time()
            self._pending_sp_y = e.y_root
            if now - getattr(self, "_last_sp_update", 0) >= 0.016:
                self._last_sp_update = now
                self._apply_inspector_resize(e.y_root)
                self._pending_sp_y = None
            else:
                if not getattr(self, "_sp_timer_active", False):
                    self._sp_timer_active = True
                    self.after(16, self._flush_pending_resize)
        elif getattr(self, "_btn_drag_active", False):
            self._on_btn_to_btn_drag_motion(e.x_root, e.y_root)
        elif self._active_drag_item is not None:
            self._on_drag_motion(e.x_root, e.y_root)

    def _flush_pending_resize(self):
        self._sp_timer_active = False
        if getattr(self, "_is_resizing_inspector", False) and getattr(self, "_pending_sp_y", None) is not None:
            self._last_sp_update = time.time()
            y = self._pending_sp_y
            self._pending_sp_y = None
            self._apply_inspector_resize(y)

    def _apply_inspector_resize(self, y_root):
        delta = self._sp_start_y - y_root
        col_h = self.left_col.winfo_height() if hasattr(self, "left_col") and self.left_col.winfo_height() > 100 else 686
        min_chassis_h = 330
        splitter_overhead = 18 + 16 + 6
        max_h = max(180, min(500, col_h - min_chassis_h - splitter_overhead))
        min_h = 135
        new_h = max(min_h, min(max_h, self._sp_start_h + delta))
        if new_h != self.inspector_height:
            self.inspector_height = new_h
            self.inspector_frame.configure(height=new_h)

    def _on_left_col_configure(self, e):
        if getattr(self, "_is_resizing_inspector", False):
            return
        if getattr(self, "left_col", None) is None or e.widget != self.left_col:
            return
        if hasattr(self, "inspector_frame") and hasattr(self, "chassis"):
            col_h = e.height
            if col_h > 100:
                min_chassis_h = 330
                splitter_overhead = 18 + 16 + 6
                max_h = max(180, min(500, col_h - min_chassis_h - splitter_overhead))
                if self.inspector_height > max_h:
                    self.inspector_height = max_h
                    self.inspector_frame.configure(height=max_h)

    def _on_global_mouse_up(self, e):
        if getattr(self, "_is_resizing_inspector", False):
            self._is_resizing_inspector = False
            self.splitter_handle.configure(fg_color="#363A4E")
            if getattr(self, "_pending_sp_y", None) is not None:
                self._apply_inspector_resize(self._pending_sp_y)
                self._pending_sp_y = None
            try:
                self.update_idletasks()
            except Exception:
                pass
        if getattr(self, "_btn_drag_active", False):
            self._end_btn_to_btn_drag(e.x_root, e.y_root)
            self._btn_drag_candidate = None
            self._btn_drag_start = None
        if self._active_drag_item is not None:
            item = self._active_drag_item
            self._on_drag_end(item, e.x_root, e.y_root)

    def _on_drag_end(self, item, x_root, y_root):
        target = None
        try:
            target = self._find_target_at_pos(x_root, y_root)
        finally:
            self._cleanup_drag()

        if target:
            target_type, target_idx = target
            if target_type == "button":
                self.select_button(target_idx)
                self._apply_palette_action(item)
            elif target_type == "encoder":
                self.select_encoder(target_idx)
                self._apply_palette_action(item)

    def _cleanup_drag_badge(self):
        if self._drag_badge:
            try:
                self._drag_badge.destroy()
            except Exception:
                pass
            self._drag_badge = None

    def _cleanup_drag(self):
        self._cleanup_drag_badge()
        self._cleanup_btn_drag_badge()
        self._active_drag_item = None
        self._btn_drag_active = False
        self._btn_drag_src = None
        self._btn_drag_candidate = None
        self._btn_drag_start = None

        for i, w in enumerate(self.btn_widgets):
            is_sel = (self.selected_item == ("button", i))
            w.configure(border_color="#FF7A29" if is_sel else "#2C3042", border_width=2 if is_sel else 1)

        for i, w in enumerate(self.enc_widgets):
            is_sel = (self.selected_item == ("encoder", i))
            w._knob_circle.configure(border_color="#FF7A29" if is_sel else "#363A4E", border_width=3 if is_sel else 2)

    def _find_target_at_pos(self, x_root, y_root):
        # 1. Klávesy
        for idx, w in enumerate(self.btn_widgets):
            try:
                wx = w.winfo_rootx()
                wy = w.winfo_rooty()
                ww = w.winfo_width()
                wh = w.winfo_height()
                if wx <= x_root <= wx + ww and wy <= y_root <= wy + wh:
                    return ("button", idx)
            except Exception:
                pass

        # 2. Enkodéry
        for idx, w in enumerate(self.enc_widgets):
            try:
                ex = w.winfo_rootx()
                ey = w.winfo_rooty()
                ew = w.winfo_width()
                eh = w.winfo_height()
                if ex <= x_root <= ex + ew and ey <= y_root <= ey + eh:
                    return ("encoder", idx)
            except Exception:
                pass

        return None

    def _highlight_hovered_target(self, x_root, y_root):
        target = self._find_target_at_pos(x_root, y_root)

        for idx, w in enumerate(self.btn_widgets):
            if target == ("button", idx):
                w.configure(border_color="#FF7A29", border_width=2)
            else:
                is_sel = (self.selected_item == ("button", idx))
                w.configure(border_color="#FF7A29" if is_sel else "#2C3042", border_width=2 if is_sel else 1)

        for idx, w in enumerate(self.enc_widgets):
            if target == ("encoder", idx):
                w._knob_circle.configure(border_color="#FF7A29", border_width=3)
            else:
                is_sel = (self.selected_item == ("encoder", idx))
                w._knob_circle.configure(border_color="#FF7A29" if is_sel else "#363A4E", border_width=3 if is_sel else 2)

    # =========================================================================
    #  PŘESOUVÁNÍ A PROHAZOVÁNÍ TLAČÍTEK TAŽENÍM MYŠÍ (DRAG & DROP)
    # =========================================================================
    def _start_btn_to_btn_drag(self, btn_id, start_x, start_y):
        buttons = self.config_mgr.profile.get("buttons", [])
        bdata = buttons[btn_id] if btn_id < len(buttons) else {}
        if bdata.get("action_type", "none") in ("none", "") and not bdata.get("label"):
            return

        self._btn_drag_active = True
        self._btn_drag_src = btn_id
        self._cleanup_btn_drag_badge()

        try:
            top = tk.Toplevel(self.winfo_toplevel())
            top.overrideredirect(True)
            top.attributes("-topmost", True)
            top.configure(bg="#0D0E12")

            badge_frame = tk.Frame(top, bg="#FF7A29", padx=8, pady=4)
            badge_frame.pack()

            btn_lbl = bdata.get("label") or f"Klávesa K{btn_id + 1}"
            it_ico = None
            if bdata.get("custom_icon"):
                it_ico = load_custom_image(bdata["custom_icon"], size=(18, 18))
            elif bdata.get("icon") and bdata["icon"] != "none":
                it_ico = get_asset_icon(bdata["icon"], size=(18, 18))

            tk_img = None
            if it_ico and hasattr(it_ico, "_dark_image"):
                resample = getattr(Image, "Resampling", Image).LANCZOS
                tk_img = ImageTk.PhotoImage(it_ico._dark_image.resize((18, 18), resample))

            lbl = tk.Label(
                badge_frame,
                text=f" ↔ K{btn_id + 1}: {btn_lbl} ",
                font=("Segoe UI", 10, "bold"),
                fg="#0A0A0E",
                bg="#FF7A29",
                compound="left"
            )
            if tk_img:
                lbl.configure(image=tk_img)
                lbl.image = tk_img
            lbl.pack()

            self._btn_drag_badge = top
            self._update_btn_drag_badge_pos(start_x, start_y)
        except Exception:
            self._btn_drag_badge = None

    def _update_btn_drag_badge_pos(self, x_root, y_root):
        if getattr(self, "_btn_drag_badge", None):
            try:
                self._btn_drag_badge.geometry(f"+{x_root + 14}+{y_root + 14}")
            except Exception:
                pass

    def _on_btn_to_btn_drag_motion(self, x_root, y_root):
        if getattr(self, "_btn_drag_badge", None):
            self._update_btn_drag_badge_pos(x_root, y_root)
            self._highlight_hovered_target(x_root, y_root)

    def _end_btn_to_btn_drag(self, x_root, y_root):
        src_id = getattr(self, "_btn_drag_src", None)
        target = None
        try:
            target = self._find_target_at_pos(x_root, y_root)
        finally:
            self._cleanup_btn_drag()

        if src_id is not None and target and target[0] == "button":
            dst_id = target[1]
            if src_id != dst_id:
                self._swap_or_move_buttons(src_id, dst_id)

    def _cleanup_btn_drag_badge(self):
        if getattr(self, "_btn_drag_badge", None):
            try:
                self._btn_drag_badge.destroy()
            except Exception:
                pass
            self._btn_drag_badge = None

    def _cleanup_btn_drag(self):
        self._cleanup_btn_drag_badge()
        self._btn_drag_active = False
        self._btn_drag_src = None
        self._btn_drag_candidate = None
        self._btn_drag_start = None

        for i, w in enumerate(self.btn_widgets):
            is_sel = (self.selected_item == ("button", i))
            w.configure(border_color="#FF7A29" if is_sel else "#2C3042", border_width=2 if is_sel else 1)

    def _swap_or_move_buttons(self, src_id, dst_id):
        """Přesune nebo prohodí konfiguraci tlačítek src a dst."""
        buttons = self.config_mgr.profile.get("buttons", [])
        if not (0 <= src_id < len(buttons) and 0 <= dst_id < len(buttons)):
            return

        src_data = copy.deepcopy(buttons[src_id])
        dst_data = copy.deepcopy(buttons[dst_id])

        is_dst_empty = (dst_data.get("action_type", "none") in ("none", "") and not dst_data.get("label"))

        src_data["id"] = dst_id
        if is_dst_empty:
            new_src = {
                "id": src_id,
                "label": "",
                "icon": "",
                "custom_icon": "",
                "action_type": "none",
                "action_param": "",
                "actions": []
            }
            buttons[src_id] = new_src
            buttons[dst_id] = src_data
        else:
            dst_data["id"] = src_id
            buttons[src_id] = dst_data
            buttons[dst_id] = src_data

        self.config_mgr.save_profile()

        w_src = self.btn_widgets[src_id]
        b_src = buttons[src_id]
        self._update_button_widget_ui(w_src, b_src.get("icon", ""), b_src.get("label", ""), b_src.get("custom_icon", ""))
        self._update_display_cell_ui(src_id, b_src.get("icon", ""), b_src.get("label", ""), b_src.get("custom_icon", ""))

        w_dst = self.btn_widgets[dst_id]
        b_dst = buttons[dst_id]
        self._update_button_widget_ui(w_dst, b_dst.get("icon", ""), b_dst.get("label", ""), b_dst.get("custom_icon", ""))
        self._update_display_cell_ui(dst_id, b_dst.get("icon", ""), b_dst.get("label", ""), b_dst.get("custom_icon", ""))

        self.select_button(dst_id)

        if self.serial and self.serial.is_connected:
            self.serial.update_button(src_id, b_src.get("icon", ""), b_src.get("label", ""))
            self.serial.update_button(dst_id, b_dst.get("icon", ""), b_dst.get("label", ""))

    # =========================================================================
    #  SCHRÁNKA A KLÁVESOVÉ ZKRATKY (Ctrl+C, Ctrl+V, Ctrl+X, Delete)
    # =========================================================================
    def _is_entry_focused(self):
        try:
            w = self.focus_get()
            if not w:
                return False
            w_cls = w.__class__.__name__.lower()
            if isinstance(w, (tk.Entry, tk.Text)) or "entry" in w_cls or "text" in w_cls:
                return True
        except Exception:
            pass
        return False

    def _copy_selected_button(self):
        if not self.selected_item or self.selected_item[0] != "button":
            return
        idx = self.selected_item[1]
        buttons = self.config_mgr.profile.get("buttons", [])
        if 0 <= idx < len(buttons):
            bdata = copy.deepcopy(buttons[idx])
            bdata.pop("id", None)
            self._button_clipboard = bdata

    def _paste_selected_button(self):
        if not getattr(self, "_button_clipboard", None):
            return
        if not self.selected_item or self.selected_item[0] != "button":
            return
        idx = self.selected_item[1]
        buttons = self.config_mgr.profile.get("buttons", [])
        if 0 <= idx < len(buttons):
            bdata = copy.deepcopy(self._button_clipboard)
            bdata["id"] = idx
            buttons[idx] = bdata
            self.config_mgr.save_profile()

            w = self.btn_widgets[idx]
            self._update_button_widget_ui(w, bdata.get("icon", ""), bdata.get("label", ""), bdata.get("custom_icon", ""))
            self._update_display_cell_ui(idx, bdata.get("icon", ""), bdata.get("label", ""), bdata.get("custom_icon", ""))
            self._update_inspector_tile(bdata.get("icon", ""), bdata.get("label", ""), bdata.get("custom_icon", ""))
            self.select_button(idx)
            if self.serial and self.serial.is_connected:
                self.serial.update_button(idx, bdata.get("icon", ""), bdata.get("label", ""))

    def _cut_selected_button(self):
        if not self.selected_item or self.selected_item[0] != "button":
            return
        self._copy_selected_button()
        self._clear_selected()

    def _on_key_ctrl_c(self, e=None):
        if self._is_entry_focused():
            return
        self._copy_selected_button()

    def _on_key_ctrl_v(self, e=None):
        if self._is_entry_focused():
            return
        self._paste_selected_button()

    def _on_key_ctrl_x(self, e=None):
        if self._is_entry_focused():
            return
        self._cut_selected_button()

    def _on_key_delete(self, e=None):
        if self._is_entry_focused():
            return
        self._clear_selected()

    def _show_button_context_menu(self, e, btn_id):
        self.select_button(btn_id)
        buttons = self.config_mgr.profile.get("buttons", [])
        bdata = buttons[btn_id] if btn_id < len(buttons) else {}
        is_empty = (bdata.get("action_type", "none") in ("none", "") and not bdata.get("label"))
        has_clipboard = bool(getattr(self, "_button_clipboard", None))

        menu = ModernContextMenu(self)
        menu.add_command("Kopírovat akci", self._copy_selected_button, shortcut="Ctrl+C", icon_asset="copy", state="normal" if not is_empty else "disabled")
        menu.add_command("Vložit akci", self._paste_selected_button, shortcut="Ctrl+V", icon_asset="paste", state="normal" if has_clipboard else "disabled")
        menu.add_command("Vyjmout akci", self._cut_selected_button, shortcut="Ctrl+X", icon="✂", state="normal" if not is_empty else "disabled")
        menu.add_separator()
        menu.add_command("Smazat / Vyčistit akci", self._clear_selected, shortcut="Delete", icon_asset="trash", state="normal" if not is_empty else "disabled", is_danger=True)
        menu.show(e.x_root, e.y_root)

    # =========================================================================
    #  LOGIKA VÝBĚRU A SYNCHRONIZACE DISPLEJE
    # =========================================================================
    def select_button(self, btn_id):
        self.selected_item = ("button", btn_id)

        for i, w in enumerate(self.btn_widgets):
            if i == btn_id:
                w.configure(border_color="#FF7A29", fg_color="#2A2019", border_width=2)
                w._lbl_num.configure(text_color="#FF9D54")
            else:
                w.configure(border_color="#2C3042", fg_color="#1B1C27", border_width=1)
                w._lbl_num.configure(text_color="#646C85")

        for w in self.enc_widgets:
            w._knob_circle.configure(border_color="#363A4E", border_width=2, fg_color="#1C1E2A")
            w._lbl_tag.configure(text_color="#FFFFFF")

        self.lbl_empty_hint.pack_forget()
        self.f_editor.pack(fill="both", expand=True, padx=8, pady=4)

        buttons = self.config_mgr.profile.get("buttons", [])
        bdata = buttons[btn_id] if btn_id < len(buttons) else {}

        act_type = bdata.get("action_type", "none")
        act_param = bdata.get("action_param", "")
        label = bdata.get("label", "")
        icon = bdata.get("icon", "")
        custom_icon = bdata.get("custom_icon", "")

        # 1. Horní záhlaví ve stylu Stream Deck
        if act_type == "multi":
            cnt = len(bdata.get("actions", []))
            self.lbl_insp_title.configure(text=f"Multi-Action:  Řetězec akcí ({cnt} kroků)")
        else:
            self.lbl_insp_title.configure(text=self._format_action_title(act_type, act_param, btn_id))

        # Aktualizace tlačítka Vymazat
        is_empty = (act_type in ("none", "") and not label and not icon and not custom_icon)
        if hasattr(self, "btn_clear"):
            if is_empty:
                self.btn_clear.configure(state="disabled", fg_color="#181924", border_color="#242738", text_color="#4E5572")
            else:
                self.btn_clear.configure(state="normal", fg_color="#1E171E", border_color="#431C24", text_color="#F87171")

        # 2. Levá dlaždice (ikona, popisek, +, ▾)
        self._update_inspector_tile(icon, label, custom_icon)

        # 3. Řádek 1: Název
        self.lbl_r1_title.configure(text="Název:")
        self.entry_label.delete(0, "end")
        self.entry_label.insert(0, label)
        self.btn_font_style.pack(side="left")

        # 4. Řádek 2 & 3: Cíl / Akce (Roztahovací výběr) + Podrobnosti NEBO Multi-Action panel
        if act_type == "multi":
            self.row_target.pack_forget()
            self.row_detail.pack_forget()
            self.f_multi_panel.pack(fill="both", expand=True)
            self._render_multi_steps(bdata)
        else:
            self.f_multi_panel.pack_forget()
            if self._needs_target_row(act_type, act_param):
                self.row_target.pack(fill="x", pady=(0, 6))
                self.lbl_r2_caption.configure(text=self._get_target_row_caption(act_type, act_param))
                self._populate_target_combo(act_type, act_param, bdata)
            else:
                self.row_target.pack_forget()
            self.row_detail.pack(fill="x")
            self.lbl_param_detail.configure(text=self._format_action_detail(act_type, act_param))

    def select_encoder(self, enc_id):
        self.selected_item = ("encoder", enc_id)

        for i, w in enumerate(self.btn_widgets):
            w.configure(border_color="#2C3042", fg_color="#1B1C27", border_width=1)
            w._lbl_num.configure(text_color="#646C85")

        for i, w in enumerate(self.enc_widgets):
            if i == enc_id:
                w._knob_circle.configure(border_color="#FF7A29", border_width=3, fg_color="#2A1E16")
                w._lbl_tag.configure(text_color="#FF9D54")
            else:
                w._knob_circle.configure(border_color="#363A4E", border_width=2, fg_color="#1C1E2A")
                w._lbl_tag.configure(text_color="#FFFFFF")

        self.lbl_empty_hint.pack_forget()
        self.f_editor.pack(fill="both", expand=True, padx=8, pady=4)
        self.f_multi_panel.pack_forget()
        self.row_target.pack(fill="x", pady=(0, 6))
        self.row_detail.pack(fill="x")

        encoders = self.config_mgr.profile.get("encoders", [])
        edata = encoders[enc_id] if enc_id < len(encoders) else {}

        name = edata.get("name", f"Enkodér E{enc_id + 1}")

        self.lbl_insp_title.configure(text=f"Enkodér:  E{enc_id + 1} ({name})")

        if hasattr(self, "btn_clear"):
            self.btn_clear.configure(state="normal", fg_color="#1E171E", border_color="#431C24", text_color="#F87171")

        # Knob ikona do dlaždice
        knob_ico = get_asset_icon("knob_dial", size=(40, 40))
        self.lbl_tile_icon.configure(image=knob_ico, text="" if knob_ico else "🎛")
        self.lbl_tile_icon.place(relx=0.5, rely=0.38, anchor="center")
        self.lbl_tile_text.configure(text=f"E{enc_id + 1}", text_color="#FF7A29")
        self.lbl_tile_text.place(relx=0.5, rely=0.76, anchor="center")

        self.lbl_r1_title.configure(text="Název:")
        self.entry_label.delete(0, "end")
        self.entry_label.insert(0, name)
        self.btn_font_style.pack_forget()

        self.lbl_r2_caption.configure(text="Režim:")
        self._populate_encoder_combo(enc_id, edata)

        cw_act = edata.get("cw", {}).get("action_param", "none")
        ccw_act = edata.get("ccw", {}).get("action_param", "none")
        btn_act = edata.get("btn", {}).get("action_param", "none")
        detail_text = f"Otáčení CW: {cw_act} | CCW: {ccw_act} | Stisk: {btn_act}"
        self.lbl_param_detail.configure(text=detail_text)

    def _populate_target_combo(self, act_type, act_param, bdata):
        """Naplní rozbalovací nabídku (ComboBox) možnostmi dle vybrané akce (roztahování dle Fotky 3)."""
        self.btn_browse.pack_forget()
        self.combo_target_choice.pack(side="left")
        self._combo_param_map = {}

        if act_type == "obs":
            std_obs = [
                ("OBS: Vysílání (Stream)", "toggle_stream"),
                ("OBS: Záznam (Record)", "toggle_record"),
                ("OBS: Pauza / Obnovit záznam", "toggle_record_pause"),
                ("OBS: Další scéna", "next_scene"),
                ("OBS: Předchozí scéna", "prev_scene"),
                ("OBS: Virtuální webkamera", "toggle_virtual_cam"),
                ("OBS: Uložit Replay buffer", "save_replay_buffer")
            ]
            for label, p in std_obs:
                self._combo_param_map[label] = p

            scenes = self.obs_controller.get_scenes() if self.obs_controller else []
            for sc in scenes:
                self._combo_param_map[f"OBS Scéna: {sc}"] = f"scene:{sc}"

            audios = self.obs_controller.get_audio_inputs() if self.obs_controller else []
            for au in audios:
                self._combo_param_map[f"OBS Ztlumit: {au}"] = f"mute:{au}"

            vals = list(self._combo_param_map.keys())
            self.combo_target_choice.configure(values=vals)

            curr_val = vals[0] if vals else ""
            for lbl, p in self._combo_param_map.items():
                if p == act_param:
                    curr_val = lbl
                    break
            self.combo_target_choice.set(curr_val)

        elif act_type == "page":
            self._combo_param_map = {
                "Další stránka": "next",
                "Předchozí stránka": "prev",
                "Zpět do hl. nabídky": "back"
            }
            pages = self.config_mgr.profile.get("pages", [])
            for i, p in enumerate(pages):
                p_name = p.get("name", f"Stránka {i + 1}")
                self._combo_param_map[f"Přejít na: Stránka {i + 1} ({p_name})"] = f"goto:{i}"

            vals = list(self._combo_param_map.keys())
            self.combo_target_choice.configure(values=vals)

            curr_val = vals[0] if vals else ""
            for lbl, p in self._combo_param_map.items():
                if p == act_param:
                    curr_val = lbl
                    break
            self.combo_target_choice.set(curr_val)

        elif act_type == "media":
            media_opts = [
                ("Přehrát / Pozastavit", "play_pause"),
                ("Další skladba", "next"),
                ("Předchozí skladba", "prev"),
                ("Zastavit (Stop)", "stop")
            ]
            self._combo_param_map = {lbl: p for lbl, p in media_opts}
            vals = list(self._combo_param_map.keys())
            self.combo_target_choice.configure(values=vals)

            curr_val = vals[0] if vals else ""
            for lbl, p in self._combo_param_map.items():
                if p == act_param:
                    curr_val = lbl
                    break
            self.combo_target_choice.set(curr_val)

        elif act_type == "volume":
            vol_opts = [
                ("Zvýšit hlasitost (+)", "up"),
                ("Snížit hlasitost (-)", "down"),
                ("Ztlumit zvuk (Mute)", "mute")
            ]
            self._combo_param_map = {lbl: p for lbl, p in vol_opts}
            vals = list(self._combo_param_map.keys())
            self.combo_target_choice.configure(values=vals)

            curr_val = vals[0] if vals else ""
            for lbl, p in self._combo_param_map.items():
                if p == act_param:
                    curr_val = lbl
                    break
            self.combo_target_choice.set(curr_val)

        elif act_type == "discord":
            discord_opts = [
                ("Ztlumit mikrofon (Mute)", "mute"),
                ("Ztlumit sluchátka (Deafen)", "deafen"),
                ("Otevřít / Přepnout Discord", "open"),
                ("Odpojit z hlasového hovoru", "disconnect")
            ]
            self._combo_param_map = {lbl: p for lbl, p in discord_opts}
            vals = list(self._combo_param_map.keys())
            self.combo_target_choice.configure(values=vals)

            curr_val = vals[0] if vals else ""
            for lbl, p in self._combo_param_map.items():
                if p == act_param:
                    curr_val = lbl
                    break
            self.combo_target_choice.set(curr_val)

        elif act_type == "profile":
            profs = self.config_mgr.list_profiles() if self.config_mgr else []
            self._combo_param_map = {f"🏷️  {p['name']}": p["id"] for p in profs}
            vals = list(self._combo_param_map.keys())
            self.combo_target_choice.configure(values=vals)
            curr_val = vals[0] if vals else ""
            for lbl, p in self._combo_param_map.items():
                if p == act_param:
                    curr_val = lbl
                    break
            self.combo_target_choice.set(curr_val)

        elif act_type == "app":
            presets = [
                ("Google Chrome", "chrome"),
                ("Microsoft Edge", "edge"),
                ("Spotify", "spotify"),
                ("Discord", "discord"),
                ("Steam", "steam"),
                ("Epic Games", "epic"),
                ("DaVinci Resolve", "davinci"),
                ("OBS Studio", "obs"),
                ("Kalkulačka", "calc"),
                ("Průzkumník souborů", "explorer"),
                ("Správce úloh (Task Manager)", "taskmgr"),
                ("Poznámkový blok", "notepad"),
                ("Malování (MS Paint)", "mspaint"),
                ("Příkazový řádek (CMD)", "cmd"),
                ("PowerShell", "powershell"),
                ("Nastavení Windows", "settings"),
                ("Visual Studio Code", "code")
            ]
            self._combo_param_map = {lbl: p for lbl, p in presets}
            if act_param and act_param not in [p for _, p in presets]:
                base = os.path.basename(act_param)
                self._combo_param_map[f"Vybraný: {base}"] = act_param
                vals = [f"Vybraný: {base}"] + [lbl for lbl, _ in presets]
            else:
                vals = [lbl for lbl, _ in presets]

            self.combo_target_choice.configure(values=vals)
            curr_val = ""
            for lbl, p in self._combo_param_map.items():
                if p == act_param:
                    curr_val = lbl
                    break
            self.combo_target_choice.set(curr_val or (os.path.basename(act_param) if act_param else "Vyberte program..."))
            self.btn_browse.pack(side="left", padx=(8, 0))

        elif act_type == "url":
            presets = [
                ("YouTube", "https://youtube.com"),
                ("Twitch", "https://twitch.tv"),
                ("Spotify", "https://open.spotify.com"),
                ("Discord Web", "https://discord.com/app"),
                ("Google", "https://google.com"),
                ("Steam", "steam://")
            ]
            self._combo_param_map = {lbl: p for lbl, p in presets}
            vals = [lbl for lbl, _ in presets]
            self.combo_target_choice.configure(values=vals)
            curr_val = act_param if act_param else vals[0]
            for lbl, p in self._combo_param_map.items():
                if p == act_param:
                    curr_val = lbl
                    break
            self.combo_target_choice.set(curr_val)

        elif act_type == "hotkey":
            presets = [
                ("Kopírovat (Ctrl+C)", "ctrl+c"),
                ("Vložit (Ctrl+V)", "ctrl+v"),
                ("Screenshot (Win+Shift+S)", "win+shift+s"),
                ("Zamknout PC (Win+L)", "win+l"),
                ("Průzkumník (Win+E)", "win+e"),
                ("Ztlumit mikrofon (Ctrl+Shift+M)", "ctrl+shift+m"),
                ("Deafen sluchátka (Ctrl+Shift+D)", "ctrl+shift+d")
            ]
            self._combo_param_map = {lbl: p for lbl, p in presets}
            vals = [lbl for lbl, _ in presets]
            self.combo_target_choice.configure(values=vals)
            curr_val = act_param if act_param else vals[0]
            for lbl, p in self._combo_param_map.items():
                if p.lower() == str(act_param).lower():
                    curr_val = lbl
                    break
            self.combo_target_choice.set(curr_val)

        elif act_type == "delay":
            presets = [
                ("Pauza 100 ms (0.1s)", "100"),
                ("Pauza 250 ms (0.25s)", "250"),
                ("Pauza 500 ms (0.5s)", "500"),
                ("Pauza 1000 ms (1.0s)", "1000"),
                ("Pauza 2000 ms (2.0s)", "2000")
            ]
            self._combo_param_map = {lbl: p for lbl, p in presets}
            vals = [lbl for lbl, _ in presets]
            self.combo_target_choice.configure(values=vals)
            curr_val = f"Pauza {act_param} ms" if act_param else vals[2]
            for lbl, p in self._combo_param_map.items():
                if p == str(act_param):
                    curr_val = lbl
                    break
            self.combo_target_choice.set(curr_val)

        elif act_type == "twitch":
            tw_opts = [
                ("Značka ve streamu (Stream Marker)", "marker"),
                ("Vytvořit klip (Create Clip)", "clip"),
                ("Spustit reklamu 30s", "commercial:30"),
                ("Spustit reklamu 60s", "commercial:60"),
                ("Spustit reklamu 90s", "commercial:90"),
                ("Vymazat chat (Clear Chat)", "clear_chat"),
                ("Režim štítu (Shield Mode)", "toggle_shield"),
                ("Chat: Pouze emote", "toggle_emote_only"),
                ("Chat: Pouze odběratelé (Subs)", "toggle_sub_only"),
                ("Chat: Pomalý režim (Slow)", "toggle_slow_mode"),
                ("Panel vysílání (Stream Manager)", "open_dashboard"),
                ("Otevřít Twitch kanál", "open_channel")
            ]
            self._combo_param_map = {lbl: p for lbl, p in tw_opts}
            p_str = str(act_param or "")
            if p_str.startswith("chat:"):
                msg = p_str[5:]
                self._combo_param_map[f"Zpráva v chatu: {msg}"] = act_param
                vals = [f"Zpráva v chatu: {msg}"] + [lbl for lbl, _ in tw_opts]
            elif p_str.startswith("marker:") and p_str != "marker":
                desc = p_str[7:]
                self._combo_param_map[f"Značka: {desc}"] = act_param
                vals = [f"Značka: {desc}"] + [lbl for lbl, _ in tw_opts]
            else:
                vals = [lbl for lbl, _ in tw_opts]

            self.combo_target_choice.configure(values=vals)
            curr_val = vals[0] if vals else ""
            for lbl, p in self._combo_param_map.items():
                if p == act_param:
                    curr_val = lbl
                    break
            self.combo_target_choice.set(curr_val)

        else:
            self._combo_param_map = {}
            self.combo_target_choice.configure(values=["(Vyberte akci z knihovny vpravo)"])
            self.combo_target_choice.set("(Vyberte akci z knihovny vpravo)")

    def _on_combo_target_selected(self, choice):
        """Vybrání možnosti z roztahovacího výběru (ComboBox dle Fotky 3)."""
        if not self.selected_item:
            return
        itype, idx = self.selected_item[0], self.selected_item[1]

        if itype == "encoder":
            self._on_encoder_mode_selected(choice)
            return

        if itype == "button":
            bdata = self.config_mgr.profile["buttons"][idx]
            new_param = self._combo_param_map.get(choice, choice)
            bdata["action_param"] = new_param

            if not bdata.get("label"):
                atype = bdata.get("action_type", "")
                if atype == "obs":
                    short = choice.replace("OBS: ", "").replace("OBS Scéna: ", "").replace("OBS Ztlumit: ", "")
                    bdata["label"] = short[:10]
                elif atype == "twitch":
                    short = choice.replace("Značka ve streamu", "Značka").replace("Vytvořit klip", "Klip").replace("Spustit reklamu", "Reklama")
                    bdata["label"] = short[:10]
                elif atype == "page":
                    short = choice.replace("Přejít na: ", "").replace("Stránka ", "Str.")
                    bdata["label"] = short[:10]
                elif atype == "media":
                    bdata["label"] = choice[:10]
                elif atype == "volume":
                    bdata["label"] = choice.split()[0]
                elif atype == "app":
                    bdata["label"] = choice[:10]
                elif atype == "profile":
                    bdata["label"] = choice.replace("🏷️  ", "").strip()[:10]
                self.entry_label.delete(0, "end")
                self.entry_label.insert(0, bdata.get("label", ""))

            self.config_mgr.save_profile()
            self.lbl_insp_title.configure(text=self._format_action_title(bdata.get("action_type", "none"), new_param, idx))
            self.lbl_param_detail.configure(text=self._format_action_detail(bdata.get("action_type", "none"), new_param))

            w = self.btn_widgets[idx]
            self._update_button_widget_ui(w, bdata.get("icon", ""), bdata.get("label", ""), bdata.get("custom_icon", ""))
            self._update_inspector_tile(bdata.get("icon", ""), bdata.get("label", ""), bdata.get("custom_icon", ""))

            if self.serial and self.serial.is_connected:
                self.serial.update_button(idx, bdata.get("icon", ""), bdata.get("label", ""))

    def _on_combo_key_released(self, e):
        """Při ručním vepsání do ComboBoxu (vlastní URL či klávesová zkratka)."""
        if not self.selected_item or self.selected_item[0] != "button":
            return
        idx = self.selected_item[1]
        new_val = self.combo_target_choice.get().strip()
        bdata = self.config_mgr.profile["buttons"][idx]
        bdata["action_param"] = new_val
        self.config_mgr.save_profile()
        self.lbl_param_detail.configure(text=self._format_action_detail(bdata.get("action_type", "none"), new_val))

    def _populate_encoder_combo(self, enc_id, edata):
        modes = [
            "Hlavní hlasitost Windows (+/- a Mute)",
            "Discord: Hlasitost a Mute mikrofonu",
            "Média Windows (Posun skladeb a Play/Pause)",
            "Jas displeje PeciDeck (+/- a Vypnout)",
            "OBS: Přepínání scén (CW další, CCW předchozí)",
            "OBS: Hlasitost Desktop Audio (+/- a Mute)"
        ]
        self.btn_browse.pack_forget()
        self.combo_target_choice.configure(values=modes)

        cw_type = edata.get("cw", {}).get("action_type", "")
        cw_param = edata.get("cw", {}).get("action_param", "")
        btn_type = edata.get("btn", {}).get("action_type", "")
        curr = modes[0]
        if cw_type == "volume" and btn_type == "discord": curr = modes[1]
        elif cw_type == "volume": curr = modes[0]
        elif cw_type == "media": curr = modes[2]
        elif cw_type == "brightness": curr = modes[3]
        elif cw_type == "obs" and "scene" in cw_param: curr = modes[4]
        elif cw_type == "obs": curr = modes[5]
        self.combo_target_choice.set(curr)
        self.combo_target_choice.pack(side="left")

    def _on_encoder_mode_selected(self, choice):
        idx = self.selected_item[1]
        encoders = self.config_mgr.profile.get("encoders", [])
        edata = encoders[idx] if idx < len(encoders) else {}

        if "discord" in choice.lower():
            edata["name"] = "Discord"
            edata["cw"] = {"action_type": "volume", "action_param": "up"}
            edata["ccw"] = {"action_type": "volume", "action_param": "down"}
            edata["btn"] = {"action_type": "discord", "action_param": "mute"}
            desc = "Discord"
        elif "hlasitost windows" in choice.lower():
            edata["name"] = "Hlasitost"
            edata["cw"] = {"action_type": "volume", "action_param": "up"}
            edata["ccw"] = {"action_type": "volume", "action_param": "down"}
            edata["btn"] = {"action_type": "volume", "action_param": "mute"}
            desc = "Hlasitost"
        elif "média" in choice.lower():
            edata["name"] = "Média"
            edata["cw"] = {"action_type": "media", "action_param": "next"}
            edata["ccw"] = {"action_type": "media", "action_param": "prev"}
            edata["btn"] = {"action_type": "media", "action_param": "play_pause"}
            desc = "Média"
        elif "jas displeje" in choice.lower():
            edata["name"] = "Jas displeje"
            edata["cw"] = {"action_type": "brightness", "action_param": "up"}
            edata["ccw"] = {"action_type": "brightness", "action_param": "down"}
            edata["btn"] = {"action_type": "brightness", "action_param": "toggle"}
            desc = "Jas"
        elif "scén" in choice.lower():
            edata["name"] = "Scény OBS"
            edata["cw"] = {"action_type": "obs", "action_param": "next_scene"}
            edata["ccw"] = {"action_type": "obs", "action_param": "prev_scene"}
            edata["btn"] = {"action_type": "obs", "action_param": "toggle_stream"}
            desc = "OBS Scény"
        else:
            target = "Desktop Audio"
            edata["name"] = "OBS Zvuk"
            edata["cw"] = {"action_type": "obs", "action_param": f"vol_up:{target}"}
            edata["ccw"] = {"action_type": "obs", "action_param": f"vol_down:{target}"}
            edata["btn"] = {"action_type": "obs", "action_param": f"mute:{target}"}
            desc = "OBS Zvuk"

        self.config_mgr.profile["encoders"][idx] = edata
        self.config_mgr.save_profile()
        self.entry_label.delete(0, "end")
        self.entry_label.insert(0, edata["name"])
        self.enc_widgets[idx]._lbl_tag.configure(text=edata["name"])
        self.enc_widgets[idx]._lbl_desc.configure(text=desc, text_color="#FF7A29")
        self.lbl_insp_title.configure(text=f"Enkodér:  E{idx + 1} ({edata['name']})")
        detail_text = f"Otáčení CW: {edata['cw']['action_param']} | CCW: {edata['ccw']['action_param']} | Stisk: {edata['btn']['action_param']}"
        self.lbl_param_detail.configure(text=detail_text)

    def _apply_palette_action(self, item):
        if not self.selected_item:
            return

        itype, idx = self.selected_item[0], self.selected_item[1]
        param = item["param"]

        if param == "CUSTOM":
            if item["type"] == "url":
                dialog = ctk.CTkInputDialog(text="Zadejte webovou URL adresu:", title="Webová adresa")
                param = dialog.get_input()
                if not param: return
            elif item["type"] == "hotkey":
                dialog = ctk.CTkInputDialog(text="Zadejte klávesovou zkratku (např. ctrl+shift+m):", title="Klávesová zkratka")
                param = dialog.get_input()
                if not param: return
            elif item["type"] == "app":
                dlg = AppPickerDialog(self, title="Výběr aplikace z počítače a plochy")
                app_res = dlg.get_result()
                if not app_res: return
                param = app_res["path"]
                item = dict(item)
                item["short"] = app_res["name"][:10]
                item["icon"] = app_res.get("icon", "app")
                if app_res.get("custom_icon"):
                    item["custom_icon"] = app_res["custom_icon"]

        elif param == "CUSTOM_SCENE":
            scenes = self.obs_controller.get_scenes() if self.obs_controller else []
            if scenes:
                dlg = OBSItemPickerDialog(self, "Výběr scény OBS", "Vyberte scénu, na kterou má tlačítko přepnout:", scenes)
                chosen = dlg.get_result()
                if not chosen: return
                param = f"scene:{chosen}"
                item = dict(item)
                item["short"] = chosen[:10]
            else:
                dialog = ctk.CTkInputDialog(text="Zadejte název scény v OBS:", title="Výběr scény OBS")
                chosen = dialog.get_input()
                if not chosen: return
                param = f"scene:{chosen.strip()}"
                item = dict(item)
                item["short"] = chosen.strip()[:10]

        elif param == "CUSTOM_MUTE":
            audios = self.obs_controller.get_audio_inputs() if self.obs_controller else []
            if audios:
                dlg = OBSItemPickerDialog(self, "Ztlumit zvuk OBS", "Vyberte audio stopu, kterou má tlačítko ztlumit/nahlasit:", audios)
                chosen = dlg.get_result()
                if not chosen: return
                param = f"mute:{chosen}"
                item = dict(item)
                item["short"] = chosen[:10]
            else:
                dialog = ctk.CTkInputDialog(text="Zadejte název audio stopy v OBS (např. Mic/Aux):", title="Ztlumit zvuk OBS")
                chosen = dialog.get_input()
                if not chosen: return
                param = f"mute:{chosen.strip()}"
                item = dict(item)
                item["short"] = chosen.strip()[:10]

        elif param == "CUSTOM_PAGE":
            pages = self.config_mgr.profile.get("pages", [])
            cur = self.config_mgr.profile.get("active_page", 0)
            dlg = PageChooserDialog(self, pages, cur)
            chosen = dlg.get_result()
            if chosen is None: return
            param = f"goto:{chosen}"
            pg_name = pages[chosen].get("name", f"Stránka {chosen + 1}") if chosen < len(pages) else f"Stránka {chosen + 1}"
            item = dict(item)
            item["short"] = pg_name[:10]

        elif param == "CUSTOM_FOLDER":
            dlg = ctk.CTkInputDialog(text="Zadejte název nové složky:", title="Nová složka")
            chosen = dlg.get_input()
            if not chosen or not chosen.strip(): return
            cur = self.config_mgr.profile.get("active_page", 0)
            f_name = chosen.strip()
            new_idx = self.config_mgr.create_folder(f_name, cur)
            param = f"folder:{new_idx}"
            item = dict(item)
            item["short"] = f_name[:10]

        elif param == "CUSTOM_PROFILE":
            profs = self.config_mgr.list_profiles() if self.config_mgr else []
            cur = getattr(self.config_mgr, "active_profile_id", "default")
            dlg = ProfileChooserDialog(self, profs, cur)
            chosen = dlg.get_result()
            if not chosen: return
            param = chosen
            prof_name = next((p["name"] for p in profs if p["id"] == chosen), chosen)
            item = dict(item)
            item["short"] = prof_name[:10]

        elif param == "CUSTOM_DELAY":
            dlg = ctk.CTkInputDialog(text="Zadejte dobu čekání v ms (např. 500 = 0.5s):", title="Pauza")
            chosen = dlg.get_input()
            if not chosen or not chosen.strip(): return
            ms = chosen.strip()
            param = ms
            item = dict(item)
            item["short"] = f"Pauza {ms}ms"[:10]

        elif param == "CUSTOM_CHAT":
            dlg = ctk.CTkInputDialog(text="Zadejte zprávu nebo příkaz do chatu (např. !discord):", title="Twitch zpráva")
            chosen = dlg.get_input()
            if not chosen or not chosen.strip(): return
            msg = chosen.strip()
            param = f"chat:{msg}"
            item = dict(item)
            item["short"] = msg[:10]

        if itype == "button":
            buttons = self.config_mgr.profile.get("buttons", [])
            curr_bdata = buttons[idx] if idx < len(buttons) else {}
            is_curr_multi = (curr_bdata.get("action_type") == "multi")

            if is_curr_multi and item["type"] != "multi":
                step = {
                    "action_type": item["type"],
                    "action_param": param,
                    "label": item.get("short", item["label"][:10])
                }
                curr_bdata.setdefault("actions", []).append(step)
                self.config_mgr.save_profile()
                self._render_multi_steps(curr_bdata)
                self.lbl_insp_title.configure(text=f"Multi-Action:  Řetězec akcí ({len(curr_bdata['actions'])} kroků)")
                return

            new_label = item.get("short", item["label"][:10])
            new_icon = item["icon"]

            custom_icon_val = item.get("custom_icon", "")
            if item["type"] == "multi":
                bdata = {
                    "id": idx,
                    "label": new_label,
                    "icon": new_icon,
                    "custom_icon": custom_icon_val,
                    "action_type": "multi",
                    "action_param": "",
                    "actions": curr_bdata.get("actions", []) if is_curr_multi else []
                }
            else:
                bdata = {
                    "id": idx,
                    "label": new_label,
                    "icon": new_icon,
                    "custom_icon": custom_icon_val,
                    "action_type": item["type"],
                    "action_param": param
                }

            self.config_mgr.profile["buttons"][idx] = bdata
            self.config_mgr.save_profile()

            w = self.btn_widgets[idx]
            self._update_button_widget_ui(w, new_icon, new_label, custom_icon_val)
            self._update_display_cell_ui(idx, new_icon, new_label, custom_icon_val)
            self._update_inspector_tile(new_icon, new_label, custom_icon_val)

            self.select_button(idx)

            if self.serial and self.serial.is_connected:
                self.serial.update_button(idx, new_icon, new_label)

        elif itype == "encoder":
            new_name = item.get("short", item["label"][:10])
            self.entry_label.delete(0, "end")
            self.entry_label.insert(0, new_name)

            if item["type"] == "volume":
                edata = {
                    "id": idx,
                    "name": new_name,
                    "cw":  {"action_type": "volume", "action_param": "up"},
                    "ccw": {"action_type": "volume", "action_param": "down"},
                    "btn": {"action_type": "volume", "action_param": "mute"}
                }
                desc = "Hlasitost"
            elif item["type"] == "discord":
                edata = {
                    "id": idx,
                    "name": new_name,
                    "cw":  {"action_type": "volume", "action_param": "up"},
                    "ccw": {"action_type": "volume", "action_param": "down"},
                    "btn": {"action_type": "discord", "action_param": item.get("param", "mute")}
                }
                desc = "Discord"
            elif item["type"] == "media":
                edata = {
                    "id": idx,
                    "name": new_name,
                    "cw":  {"action_type": "media", "action_param": "next"},
                    "ccw": {"action_type": "media", "action_param": "prev"},
                    "btn": {"action_type": "media", "action_param": "play_pause"}
                }
                desc = "Média"
            elif item["type"] == "obs":
                if "scene" in str(param):
                    edata = {
                        "id": idx,
                        "name": new_name,
                        "cw":  {"action_type": "obs", "action_param": "next_scene"},
                        "ccw": {"action_type": "obs", "action_param": "prev_scene"},
                        "btn": {"action_type": "obs", "action_param": "toggle_stream"}
                    }
                    desc = "OBS Scény"
                else:
                    target_audio = param[5:] if str(param).startswith("mute:") else "Desktop Audio"
                    edata = {
                        "id": idx,
                        "name": new_name,
                        "cw":  {"action_type": "obs", "action_param": f"vol_up:{target_audio}"},
                        "ccw": {"action_type": "obs", "action_param": f"vol_down:{target_audio}"},
                        "btn": {"action_type": "obs", "action_param": f"mute:{target_audio}"}
                    }
                    desc = "OBS Zvuk"
            else:
                edata = {
                    "id": idx,
                    "name": new_name,
                    "cw":  {"action_type": item["type"], "action_param": param},
                    "ccw": {"action_type": item["type"], "action_param": param},
                    "btn": {"action_type": item["type"], "action_param": param}
                }
                desc = "Přiřazeno"

            self.config_mgr.profile["encoders"][idx] = edata
            self.config_mgr.save_profile()

            self.enc_widgets[idx]._lbl_tag.configure(text=new_name)
            self.enc_widgets[idx]._lbl_desc.configure(text=desc, text_color="#FF7A29")

            self.lbl_insp_title.configure(text=f"Enkodér:  E{idx + 1} ({new_name})")
            self._populate_encoder_combo(idx, edata)
            detail_text = f"Otáčení CW: {edata['cw']['action_param']} | CCW: {edata['ccw']['action_param']} | Stisk: {edata['btn']['action_param']}"
            self.lbl_param_detail.configure(text=detail_text)

    def _on_label_changed(self, e=None):
        if not self.selected_item:
            return
        itype, idx = self.selected_item[0], self.selected_item[1]
        new_label = self.entry_label.get().strip()

        if itype == "button":
            self.config_mgr.profile["buttons"][idx]["label"] = new_label
            self.config_mgr.save_profile()

            w = self.btn_widgets[idx]
            icon = self.config_mgr.profile["buttons"][idx].get("icon", "")
            custom_icon = self.config_mgr.profile["buttons"][idx].get("custom_icon", "")
            self._update_button_widget_ui(w, icon, new_label, custom_icon)
            self._update_display_cell_ui(idx, icon, new_label, custom_icon)
            self._update_inspector_tile(icon, new_label, custom_icon)

            if self._debounce_timer is not None:
                self.after_cancel(self._debounce_timer)
            self._debounce_timer = self.after(250, lambda: self._send_button_hw(idx, icon, new_label))
        elif itype == "encoder":
            self.config_mgr.profile["encoders"][idx]["name"] = new_label
            self.config_mgr.save_profile()
            self.enc_widgets[idx]._lbl_tag.configure(text=new_label or f"E{idx+1}")
            self.lbl_insp_title.configure(text=f"Enkodér:  E{idx + 1} ({new_label})")

    def _send_button_hw(self, idx, icon, label):
        if self.serial and self.serial.is_connected:
            self.serial.update_button(idx, icon if icon != "none" else "", label)

    def _clear_selected(self):
        if not self.selected_item:
            return
        itype, idx = self.selected_item[0], self.selected_item[1]

        if itype == "button":
            bdata = {"id": idx, "label": "", "icon": "", "custom_icon": "", "action_type": "none", "action_param": "", "actions": []}
            self.config_mgr.profile["buttons"][idx] = bdata
            self.config_mgr.save_profile()

            w = self.btn_widgets[idx]
            self._update_button_widget_ui(w, "", "", "")
            self._update_display_cell_ui(idx, "", "", "")
            self._update_inspector_tile("", "", "")

            self.select_button(idx)

            if self.serial and self.serial.is_connected:
                self.serial.update_button(idx, "", "")

        elif itype == "encoder":
            edata = {
                "id": idx,
                "name": f"E{idx+1}",
                "cw": {"action_type": "none", "action_param": ""},
                "ccw": {"action_type": "none", "action_param": ""},
                "btn": {"action_type": "none", "action_param": ""}
            }
            self.config_mgr.profile["encoders"][idx] = edata
            self.config_mgr.save_profile()
            self.entry_label.delete(0, "end")
            self.entry_label.insert(0, f"E{idx+1}")
            self.entry_param.delete(0, "end")
            self.entry_param.insert(0, "Nepřiřazeno")
            self.enc_widgets[idx]._lbl_desc.configure(text="Prázdné", text_color="#7E849B")
            self.enc_widgets[idx]._lbl_tag.configure(text=f"E{idx+1}")
            self.lbl_insp_title.configure(text=f"Enkodér:  E{idx + 1} (E{idx + 1})")
            self.lbl_param_detail.configure(text="Enkodér byl vymazán.")

    def highlight_button(self, btn_id, pressed):
        """Animace stisknutí fyzického tlačítka s garantovaným vizuálním impulsem."""
        if 0 <= btn_id < len(self.btn_widgets):
            w = self.btn_widgets[btn_id]
            is_selected = (self.selected_item == ("button", btn_id))
            timer_attr = f"_btn_restore_timer_{btn_id}"
            down_attr = f"_btn_phys_down_{btn_id}"

            if pressed:
                setattr(self, down_attr, True)
                old_timer = getattr(self, timer_attr, None)
                if old_timer:
                    try:
                        self.after_cancel(old_timer)
                    except Exception:
                        pass
                w.configure(fg_color="#FF7A29", border_color="#FFFFFF")
                if hasattr(w, "_lbl_text"):
                    w._lbl_text.configure(text_color="#000000")
                if hasattr(w, "_lbl_num"):
                    w._lbl_num.configure(text_color="#000000")
            else:
                setattr(self, down_attr, False)
                def _do_restore():
                    if not getattr(self, down_attr, False):
                        w.configure(
                            fg_color="#2A2019" if is_selected else "#1B1C27", 
                            border_color="#FF7A29" if is_selected else "#2C3042"
                        )
                        if hasattr(w, "_lbl_text"):
                            w._lbl_text.configure(text_color="#FFFFFF")
                        if hasattr(w, "_lbl_num"):
                            w._lbl_num.configure(text_color="#FF9D54" if is_selected else "#646C85")
                # Zajištění minimální doby trvání animace 140 ms pro jasnou viditelnost
                new_timer = self.after(140, _do_restore)
                setattr(self, timer_attr, new_timer)

    def highlight_encoder(self, enc_id, pressed):
        """Animace stisknutí fyzického otočného enkodéru."""
        if 0 <= enc_id < len(self.enc_widgets):
            w = self.enc_widgets[enc_id]
            is_selected = (self.selected_item == ("encoder", enc_id))
            timer_attr = f"_enc_restore_timer_{enc_id}"
            down_attr = f"_enc_phys_down_{enc_id}"

            if pressed:
                setattr(self, down_attr, True)
                old_timer = getattr(self, timer_attr, None)
                if old_timer:
                    try:
                        self.after_cancel(old_timer)
                    except Exception:
                        pass
                w._knob_circle.configure(fg_color="#FF7A29", border_color="#FFFFFF")
                w._lbl_tag.configure(text_color="#FFFFFF")
            else:
                setattr(self, down_attr, False)
                def _do_restore():
                    if not getattr(self, down_attr, False):
                        w._knob_circle.configure(
                            fg_color="#2A1E16" if is_selected else "#1C1E2A",
                            border_color="#FF7A29" if is_selected else "#363A4E",
                            border_width=3 if is_selected else 2
                        )
                        w._lbl_tag.configure(text_color="#FF9D54" if is_selected else "#FFFFFF")
                new_timer = self.after(140, _do_restore)
                setattr(self, timer_attr, new_timer)

    def animate_encoder_rotate(self, enc_id, direction):
        """Animace otočení enkodéru."""
        if 0 <= enc_id < len(self.enc_widgets):
            w = self.enc_widgets[enc_id]
            is_selected = (self.selected_item == ("encoder", enc_id))
            
            w._knob_circle.configure(border_color="#FFA05C")
            w._tick_notch.configure(fg_color="#FFA05C")

            def _restore():
                w._knob_circle.configure(border_color="#FF7A29" if is_selected else "#363A4E")
                w._tick_notch.configure(fg_color="#FF7A29")

            self.after(140, _restore)
