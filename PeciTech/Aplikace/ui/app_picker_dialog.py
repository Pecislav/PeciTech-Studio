import os
import threading
import customtkinter as ctk
from tkinter import filedialog
from assets_manager import get_asset_icon
from icon_extractor import get_app_icon, get_extracted_icon_png_path

# Globální cache nalezených aplikací, aby se disk neprocházel při každém otevření okna
_CACHED_APPS = None

def scan_installed_applications(force_refresh=False):
    """
    Rychle a efektivně prohledá plochu uživatele, veřejnou plochu (All Users),
    nabídku Start a běžné systémové nástroje Windows.
    Výsledky jsou cachovány pro bleskový start dialogu bez zasekávání.
    """
    global _CACHED_APPS
    if _CACHED_APPS is not None and not force_refresh:
        return _CACHED_APPS

    apps = {}

    # 1. Běžné systémové nástroje Windows
    system_tools = [
        ("Kalkulačka", "calc", "calc"),
        ("Průzkumník souborů", "explorer", "folder"),
        ("Správce úloh", "taskmgr", "cat_system"),
        ("Poznámkový blok", "notepad", "cat_system"),
        ("Malování (Paint)", "mspaint", "cat_system"),
        ("Příkazový řádek (CMD)", "cmd", "cat_system"),
        ("PowerShell", "powershell", "cat_system"),
        ("Nastavení Windows", "settings", "gear"),
    ]
    for name, cmd, ico in system_tools:
        apps[cmd] = {
            "name": name,
            "path": cmd,
            "category": "system",
            "is_desktop": False,
            "is_game": False,
            "icon": ico
        }

    # 2. Složky k prohledání
    search_dirs = [
        (os.path.expanduser("~/Desktop"), True),
        (r"C:\Users\Public\Desktop", True),
        (os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"), False),
        (os.path.join(os.environ.get("PROGRAMDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"), False)
    ]

    game_keywords = {
        "steam", "epic", "riot", "game", "cyberpunk", "witcher", "gta", "minecraft",
        "fortnite", "valorant", "roblox", "ea app", "ubisoft", "battlenet", "battle.net",
        "blizzard", "call of duty", "counter-strike", "cs2", "dota", "apex", "warzone",
        "sea of thieves", "hunt", "bodycam", "black mesa", "pragmata", "hunter", "stacher"
    }

    known_fw_icons = {
        "chrome": "web",
        "edge": "web",
        "firefox": "web",
        "steam": "steam",
        "discord": "discord",
        "obs": "obs",
        "spotify": "spotify",
        "calc": "calc",
        "explorer": "folder",
    }

    for d, is_desk in search_dirs:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in (".lnk", ".url", ".exe"):
                    base = os.path.splitext(f)[0]
                    clean_name = base.replace(" - zástupce", "").replace(" – zástupce", "").strip()
                    if not clean_name or clean_name.lower().startswith("desktop") or clean_name.lower().startswith("uninstall"):
                        continue

                    full_path = os.path.join(root, f)
                    lower_name = clean_name.lower()
                    
                    is_game = (ext == ".url") or any(k in lower_name for k in game_keywords) or ("games" in root.lower())

                    # Výběr firmwarové ikony pro mikrokontrolér
                    fw_ico = "app"
                    for k, icon_key in known_fw_icons.items():
                        if k in lower_name:
                            fw_ico = icon_key
                            break
                    if is_game and fw_ico == "app":
                        fw_ico = "steam" if "steam" in lower_name or ext == ".url" else "cat_games"

                    # Upřednostnit položku z plochy před nabídkou Start
                    if clean_name not in apps or is_desk:
                        apps[clean_name] = {
                            "name": clean_name,
                            "path": full_path,
                            "category": "desktop" if is_desk else "start",
                            "is_desktop": is_desk,
                            "is_game": is_game,
                            "icon": fw_ico
                        }

    # Seřadit: Plocha -> Hry -> Systém -> Start
    sorted_apps = sorted(
        list(apps.values()),
        key=lambda x: (
            0 if x.get("is_desktop") else (1 if x.get("is_game") else (2 if x.get("category") == "system" else 3)),
            x["name"].lower()
        )
    )

    _CACHED_APPS = sorted_apps
    return sorted_apps


class AppPickerDialog(ctk.CTkToplevel):
    """
    Moderní optimalizovaný dialog pro výběr aplikace, hry nebo systémového nástroje.
    Vlevo: strom/kategorie složek (Všechny, Plocha, Hry, Nabídka Start, Systémové nástroje, Procházet disk).
    Vpravo: reálné extrahované ikony z Windows s bleskovou cache a plynulým vyhledáváním bez lagů.
    """
    PAGE_SIZE = 40  # Dávkové vykreslování položek pro okamžitou odezvu bez zasekávání

    def __init__(self, parent, title="Vyberte aplikaci nebo hru"):
        super().__init__(parent)
        self.title(title)
        self.geometry("780x590")
        self.minsize(720, 500)
        self.configure(fg_color="#0D0E12")
        self.transient(parent)
        self.grab_set()

        self.result = None
        self._all_apps = scan_installed_applications()
        self._current_filter = "all"
        self._search_debounce_job = None
        self._displayed_count = self.PAGE_SIZE
        self._category_buttons = {}

        # Asynchronní pre-caching ikon na pozadí pro okamžité zobrazení
        threading.Thread(target=self._precache_icons_background, daemon=True).start()

        self._build_ui()

    def _precache_icons_background(self):
        """Přednačte ikony na pozadí, aby se z disku nečetly během scrollování."""
        for app in self._all_apps[:50]:
            try:
                get_extracted_icon_png_path(app["path"])
            except Exception:
                pass

    def _build_ui(self):
        # 1. Horní záhlaví s vyhledávacím panelem
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(16, 10))

        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left", fill="y")

        ctk.CTkLabel(
            title_box, 
            text="Aplikace a programy v počítači", 
            font=ctk.CTkFont(size=17, weight="bold"), 
            text_color="#FFFFFF"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box, 
            text="Vyberte program pro spuštění stiskem klávesy na PeciDecku", 
            font=ctk.CTkFont(size=11), 
            text_color="#8E95AE"
        ).pack(anchor="w", pady=(1, 0))

        # Rychlé vyhledávací pole s ikonou
        self.search_entry = ctk.CTkEntry(
            top_bar,
            placeholder_text="🔍 Hledat aplikaci (např. DaVinci, Chrome, Steam, KiCad)...",
            width=320,
            height=36,
            corner_radius=8,
            fg_color="#14151E",
            border_color="#242738",
            border_width=1,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12)
        )
        self.search_entry.pack(side="right", padx=(10, 0))
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        # 2. Hlavní plocha rozdělená na levý sloupec (Složky) a pravý sloupec (Programy)
        main_split = ctk.CTkFrame(self, fg_color="transparent")
        main_split.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # --- LEVÝ SLOUPEC: SLOŽKY & KATEGORIE ---
        left_col = ctk.CTkFrame(
            main_split, 
            width=215, 
            fg_color="#12131D", 
            corner_radius=10, 
            border_width=1, 
            border_color="#242738"
        )
        left_col.pack(side="left", fill="y", padx=(0, 10))
        left_col.pack_propagate(False)

        # Nadpis složek
        ctk.CTkLabel(
            left_col, 
            text="📁 SLOŽKY A UMÍSTĚNÍ", 
            font=ctk.CTkFont(size=10, weight="bold"), 
            text_color="#64748B"
        ).pack(anchor="w", padx=14, pady=(12, 6))

        # Kategorie s počty
        all_count = len(self._all_apps)
        desk_count = len([x for x in self._all_apps if x.get("is_desktop")])
        game_count = len([x for x in self._all_apps if x.get("is_game")])
        start_count = len([x for x in self._all_apps if x.get("category") == "start"])
        sys_count = len([x for x in self._all_apps if x.get("category") == "system"])

        categories = [
            ("all", "📁 Všechny programy", all_count),
            ("desktop", "🖥️ Plocha", desk_count),
            ("games", "🎮 Hry a zábava", game_count),
            ("start", "🚀 Nabídka Start", start_count),
            ("system", "⚙️ Systémové nástroje", sys_count),
        ]

        self.cat_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        self.cat_frame.pack(fill="x", padx=8)

        for cat_id, cat_title, count in categories:
            btn = ctk.CTkButton(
                self.cat_frame,
                text=f"{cat_title}  ({count})",
                anchor="w",
                height=34,
                corner_radius=8,
                fg_color="#181A25" if cat_id != "all" else "#FF7A29",
                hover_color="#242738" if cat_id != "all" else "#E5681E",
                text_color="#8E95AE" if cat_id != "all" else "#0A0A0E",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda cid=cat_id: self._select_category(cid)
            )
            btn.pack(fill="x", pady=2)
            self._category_buttons[cat_id] = btn

        # Spodní oddělovač a tlačítko procházet disk v levém panelu
        left_bottom = ctk.CTkFrame(left_col, fg_color="transparent")
        left_bottom.pack(side="bottom", fill="x", padx=8, pady=10)

        ctk.CTkLabel(
            left_bottom,
            text="VLASTNÍ SOUBOR",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#64748B"
        ).pack(anchor="w", padx=6, pady=(0, 4))

        btn_browse_disk = ctk.CTkButton(
            left_bottom,
            text="📂 Procházet disk...",
            height=34,
            corner_radius=8,
            fg_color="#1A1C28",
            hover_color="#262A3C",
            border_width=1,
            border_color="#2E3348",
            text_color="#FF9D54",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._browse_custom_file
        )
        btn_browse_disk.pack(fill="x")

        # --- PRAVÝ SLOUPEC: SEZNAM APLIKACÍ A SKUTEČNÉ IKONY ---
        right_col = ctk.CTkFrame(main_split, fg_color="transparent")
        right_col.pack(side="left", fill="both", expand=True)

        # Záhlaví pravého sloupce
        self.right_header = ctk.CTkFrame(right_col, fg_color="transparent", height=24)
        self.right_header.pack(fill="x", pady=(0, 6))

        self.lbl_category_title = ctk.CTkLabel(
            self.right_header,
            text="Všechny programy",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#FFFFFF"
        )
        self.lbl_category_title.pack(side="left")

        self.lbl_item_counter = ctk.CTkLabel(
            self.right_header,
            text=f"Zobrazeno {all_count} aplikací",
            font=ctk.CTkFont(size=11),
            text_color="#64748B"
        )
        self.lbl_item_counter.pack(side="right")

        # Seznam aplikací (Scrollable Frame)
        self.scroll_list = ctk.CTkScrollableFrame(
            right_col,
            fg_color="#14151E",
            corner_radius=10,
            border_width=1,
            border_color="#242738",
            scrollbar_button_color="#242738",
            scrollbar_button_hover_color="#FF7A29"
        )
        self.scroll_list.pack(fill="both", expand=True)

        # 3. Spodní lišta s nápovědou a tlačítkem Zrušit
        bot_bar = ctk.CTkFrame(self, fg_color="transparent")
        bot_bar.pack(fill="x", padx=20, pady=(0, 14))

        ctk.CTkLabel(
            bot_bar,
            text="💡 Kliknutím na libovolný řádek nebo tlačítko 'Vybrat' přiřadíte program k tlačítku.",
            font=ctk.CTkFont(size=11),
            text_color="#64748B"
        ).pack(side="left")

        btn_cancel = ctk.CTkButton(
            bot_bar,
            text="Zavřít",
            width=84,
            height=32,
            corner_radius=8,
            fg_color="#1E202C",
            hover_color="#282B3C",
            text_color="#94A3B8",
            font=ctk.CTkFont(size=11),
            command=self.destroy
        )
        btn_cancel.pack(side="right")

        # Vykreslení položek
        self._render_items()

    def _select_category(self, cat_id):
        self._current_filter = cat_id
        self._displayed_count = self.PAGE_SIZE

        # Aktualizace barev tlačítek v levém panelu
        for cid, btn in self._category_buttons.items():
            if cid == cat_id:
                btn.configure(fg_color="#FF7A29", hover_color="#E5681E", text_color="#0A0A0E")
            else:
                btn.configure(fg_color="#181A25", hover_color="#242738", text_color="#8E95AE")

        titles = {
            "all": "📁 Všechny programy",
            "desktop": "🖥️ Plocha (Osobní i Veřejná)",
            "games": "🎮 Hry a herní klienti",
            "start": "🚀 Nabídka Start",
            "system": "⚙️ Systémové nástroje Windows"
        }
        self.lbl_category_title.configure(text=titles.get(cat_id, "Programy"))
        self._render_items()

    def _on_search_key(self, event=None):
        """Plynulé vyhledávání s debouncingem (120ms) pro nulové zasekávání."""
        if self._search_debounce_job is not None:
            self.after_cancel(self._search_debounce_job)
        self._search_debounce_job = self.after(120, self._render_items)

    def _get_filtered_items(self):
        query = self.search_entry.get().strip().lower()

        filtered = []
        for item in self._all_apps:
            # Kategorie filtr
            if self._current_filter == "desktop" and not item.get("is_desktop"):
                continue
            elif self._current_filter == "games" and not item.get("is_game"):
                continue
            elif self._current_filter == "start" and item.get("category") != "start":
                continue
            elif self._current_filter == "system" and item.get("category") != "system":
                continue

            # Vyhledávací filtr
            if query:
                name_match = query in item["name"].lower()
                path_match = query in item["path"].lower()
                if not name_match and not path_match:
                    continue

            filtered.append(item)

        return filtered

    def _render_items(self):
        # Vyčištění předchozích položek
        for w in self.scroll_list.winfo_children():
            w.destroy()

        filtered = self._get_filtered_items()
        total_found = len(filtered)
        self.lbl_item_counter.configure(text=f"Nalezeno {total_found} položek")

        if not filtered:
            ctk.CTkLabel(
                self.scroll_list,
                text="Žádný program neodpovídá zadanému hledání.\nMůžete použít 'Procházet disk...' vlevo dole.",
                font=ctk.CTkFont(size=12),
                text_color="#64748B",
                justify="center"
            ).pack(pady=50)
            return

        # Dávkování: zobrazíme prvních N položek pro bleskovou odezvu
        visible_items = filtered[:self._displayed_count]

        for item in visible_items:
            self._create_item_row(item)

        # Tlačítko pro načtení dalších položek, pokud je jich více
        if total_found > self._displayed_count:
            remaining = total_found - self._displayed_count
            load_more_btn = ctk.CTkButton(
                self.scroll_list,
                text=f"➕ Načíst dalších {min(self.PAGE_SIZE, remaining)} programů (zbývá ještě {remaining})...",
                height=32,
                corner_radius=8,
                fg_color="#181A25",
                hover_color="#242738",
                text_color="#FF9D54",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=self._load_more_items
            )
            load_more_btn.pack(fill="x", padx=6, pady=(6, 10))

    def _load_more_items(self):
        self._displayed_count += self.PAGE_SIZE
        self._render_items()

    def _create_item_row(self, item):
        row = ctk.CTkFrame(
            self.scroll_list, 
            fg_color="#1A1C28", 
            corner_radius=8, 
            height=46
        )
        row.pack(fill="x", pady=2, padx=4)
        row.pack_propagate(False)

        def _on_enter(e):
            row.configure(fg_color="#24273A")
        def _on_leave(e):
            row.configure(fg_color="#1A1C28")
        row.bind("<Enter>", _on_enter)
        row.bind("<Leave>", _on_leave)

        # 1. Extrakce skutečné Windows ikony z PC
        ctk_img, png_path = get_app_icon(item["path"], size=(26, 26))
        if not ctk_img:
            # Fallback na firmwarovou asset ikonu
            ctk_img = get_asset_icon(item.get("icon", "app"), size=(24, 24))

        if png_path:
            item["custom_icon"] = png_path

        lbl_ico = ctk.CTkLabel(row, image=ctk_img, text="" if ctk_img else "🚀", width=36)
        lbl_ico.pack(side="left", padx=(10, 4))

        # 2. Textový blok (Název + Cesta/Umístění)
        text_block = ctk.CTkFrame(row, fg_color="transparent")
        text_block.pack(side="left", fill="both", expand=True, padx=(2, 8), pady=4)

        lbl_name = ctk.CTkLabel(
            text_block,
            text=item["name"],
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FFFFFF",
            anchor="w"
        )
        lbl_name.pack(anchor="w", fill="x")

        # Zkrácená cesta nebo popis pro přehlednost
        display_sub = item["path"]
        if len(display_sub) > 60:
            display_sub = "..." + display_sub[-57:]
        lbl_sub = ctk.CTkLabel(
            text_block,
            text=display_sub,
            font=ctk.CTkFont(size=9),
            text_color="#64748B",
            anchor="w"
        )
        lbl_sub.pack(anchor="w", fill="x")

        # 3. Odznáček původu (Plocha, Hra, Systém, Start)
        tag_text = "Plocha" if item.get("is_desktop") else ("Hra" if item.get("is_game") else ("Systém" if item.get("category") == "system" else "Start"))
        tag_color = "#FF9D54" if tag_text == "Plocha" else ("#10B981" if tag_text == "Hra" else ("#38BDF8" if tag_text == "Systém" else "#64748B"))

        badge = ctk.CTkFrame(row, fg_color="#12131D", corner_radius=6, height=22)
        badge.pack(side="right", padx=(4, 8))
        ctk.CTkLabel(
            badge,
            text=tag_text,
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=tag_color,
            padx=8,
            pady=2
        ).pack()

        # 4. Tlačítko Vybrat
        btn_sel = ctk.CTkButton(
            row,
            text="Vybrat",
            width=64,
            height=26,
            corner_radius=6,
            fg_color="#272A3C",
            hover_color="#FF7A29",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda it=item: self._select_app(it)
        )
        btn_sel.pack(side="right", padx=(0, 4))

        # Kliknutí na jakoukoliv část řádku ihned vybere aplikaci
        select_cb = lambda e, it=item: self._select_app(it)
        row.bind("<Button-1>", select_cb)
        lbl_ico.bind("<Button-1>", select_cb)
        lbl_name.bind("<Button-1>", select_cb)
        lbl_sub.bind("<Button-1>", select_cb)
        text_block.bind("<Button-1>", select_cb)

    def _select_app(self, item):
        # Pokud custom_icon ještě nebyla uložena, extrahujeme ji nyní
        custom_icon = item.get("custom_icon", "")
        if not custom_icon:
            custom_icon = get_extracted_icon_png_path(item["path"])

        self.result = {
            "path": item["path"],
            "name": item["name"],
            "icon": item.get("icon", "app"),
            "custom_icon": custom_icon
        }
        self.destroy()

    def _browse_custom_file(self):
        types = [
            ("Všechny aplikace a zástupci (*.exe, *.lnk, *.url, *.bat)", "*.exe;*.lnk;*.url;*.bat;*.cmd"),
            ("Spustitelné soubory (*.exe)", "*.exe"),
            ("Zástupci Windows (*.lnk)", "*.lnk"),
            ("Herní zástupci (*.url)", "*.url"),
            ("Všechny soubory (*.*)", "*.*")
        ]
        path = filedialog.askopenfilename(
            parent=self,
            title="Vyberte aplikaci nebo soubor z disku",
            filetypes=types,
            initialdir=os.path.expanduser("~/Desktop")
        )
        if path:
            base = os.path.splitext(os.path.basename(path))[0]
            clean = base.replace(" - zástupce", "").replace(" – zástupce", "").strip()
            custom_icon = get_extracted_icon_png_path(path)
            self.result = {
                "path": path,
                "name": clean or base,
                "icon": "app",
                "custom_icon": custom_icon
            }
            self.destroy()

    def get_result(self):
        self.wait_window()
        return self.result
