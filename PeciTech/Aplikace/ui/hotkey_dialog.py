"""
PeciTech Studio – Interaktivní dialog pro záznam klávesových zkratek
Umožňuje uživateli fyzicky stisknout libovolnou kombinaci kláves na klávesnici,
zobrazit vizuální náhled v podobě moderních tlačítek (badge) a potvrdit zkratku.
"""

import sys
import threading
import tkinter as tk
import customtkinter as ctk

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    keyboard = None
    HAS_KEYBOARD = False

MODIFIER_MAP = {
    "ctrl": "ctrl",
    "control": "ctrl",
    "left ctrl": "ctrl",
    "right ctrl": "ctrl",
    "shift": "shift",
    "left shift": "shift",
    "right shift": "shift",
    "alt": "alt",
    "left alt": "alt",
    "right alt": "alt",
    "alt gr": "alt",
    "windows": "windows",
    "win": "windows",
    "left windows": "windows",
    "right windows": "windows",
    "super": "windows",
}

KEYSYM_FALLBACK = {
    "control_l": "ctrl",
    "control_r": "ctrl",
    "shift_l": "shift",
    "shift_r": "shift",
    "alt_l": "alt",
    "alt_r": "alt",
    "super_l": "windows",
    "super_r": "windows",
    "win_l": "windows",
    "win_r": "windows",
    "return": "enter",
    "escape": "esc",
    "backspace": "backspace",
    "delete": "delete",
    "insert": "insert",
    "home": "home",
    "end": "end",
    "prior": "page up",
    "next": "page down",
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
    "space": "space",
    "tab": "tab",
}

MODIFIER_SCAN_CODES = {
    29: "ctrl", 57629: "ctrl", 57373: "ctrl",
    56: "alt", 57400: "alt",
    42: "shift", 54: "shift",
    57435: "windows", 57436: "windows", 91: "windows", 92: "windows"
}

# Fyzické hardwarové scan-kódy kláves (100% nezávislé na českém rozložení klávesnice v OS)
SCAN_CODE_MAP = {
    # Číselná řada (VŽDY 1, 2, 3... bez ohledu na české znaky +, ě, š, č, ...)
    2: "1", 3: "2", 4: "3", 5: "4", 6: "5",
    7: "6", 8: "7", 9: "8", 10: "9", 11: "0",
    12: "-", 13: "=",

    # Písmena (QWERTY – Y je scan 21, Z je scan 44)
    16: "q", 17: "w", 18: "e", 19: "r", 20: "t", 21: "y", 22: "u", 23: "i", 24: "o", 25: "p",
    26: "[", 27: "]",
    30: "a", 31: "s", 32: "d", 33: "f", 34: "g", 35: "h", 36: "j", 37: "k", 38: "l",
    39: ";", 40: "'", 41: "`",
    43: "\\", 44: "z", 45: "x", 46: "c", 47: "v", 48: "b", 49: "n", 50: "m",
    51: ",", 52: ".", 53: "/",

    # F1 - F12
    59: "f1", 60: "f2", 61: "f3", 62: "f4", 63: "f5", 64: "f6",
    65: "f7", 66: "f8", 67: "f9", 68: "f10", 87: "f11", 88: "f12",
    100: "f13", 101: "f14", 102: "f15", 103: "f16", 104: "f17", 105: "f18",
    106: "f19", 107: "f20", 108: "f21", 109: "f22", 110: "f23", 118: "f24",

    # Řídicí klávesy
    1: "esc", 14: "backspace", 15: "tab", 28: "enter", 57: "space",
    58: "caps lock",

    # Numpad
    55: "*", 71: "7", 72: "8", 73: "9", 74: "-",
    75: "4", 76: "5", 77: "6", 78: "+",
    79: "1", 80: "2", 81: "3", 82: "0", 83: ".",

    # Navigační a editační klávesy
    57419: "left", 57421: "right", 57416: "up", 57424: "down",
    57426: "insert", 57427: "delete", 57415: "home", 57423: "end",
    57417: "page up", 57425: "page down"
}

# Převodní mapa pro případ, že z hooku nebo Tkinteru přijdou české znaky
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

TK_CZECH_KEYSYMS = {
    "plus": "1",
    "ecaron": "2",
    "scaron": "3",
    "ccaron": "4",
    "rcaron": "5",
    "zcaron": "6",
    "yacute": "7",
    "aacute": "8",
    "iacute": "9",
    "eacute": "0",
    "uring": ";",
    "uacute": "[",
    "section": "'",
    "dead_acute": "=",
    "dead_diaeresis": "\\",
}

def normalize_hotkey(hotkey):
    """
    Normalizuje klávesovou zkratku na univerzální standardní zápis:
    - Převede české znaky (ě -> 2, + -> 1, š -> 3, ...) na standardní klávesy
    - Očistí zdvojená pluska (např. 'alt++' -> 'alt+1')
    - Ořeže mezery a převede na malá písmena
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

DISPLAY_NAMES = {
    "ctrl": "Ctrl",
    "shift": "Shift",
    "alt": "Alt",
    "windows": "Win",
    "enter": "Enter",
    "esc": "Esc",
    "backspace": "Backspace",
    "delete": "Delete",
    "insert": "Insert",
    "home": "Home",
    "end": "End",
    "page up": "Page Up",
    "page down": "Page Down",
    "up": "↑",
    "down": "↓",
    "left": "←",
    "right": "→",
    "space": "Mezerník",
    "tab": "Tab",
}


class HotkeyRecorderDialog(ctk.CTkToplevel):
    def __init__(self, parent, current_value="", title="Záznam klávesové zkratky"):
        super().__init__(parent)
        self.parent = parent
        self.result = None
        self.recorded_hotkey = normalize_hotkey(current_value)

        self.active_modifiers = set()
        self._hook_handle = None
        self._is_closed = False

        self.title(title)
        self.geometry("500x360")
        self.resizable(False, False)
        self.configure(fg_color="#0D0E15")

        # Okno vždy nahoře a modální vůči rodiči
        self.transient(parent)
        self.grab_set()

        # Vycentrování nad rodičovským oknem
        self._center_window(parent)

        self._build_ui()

        # Inicializace stávající hodnoty pokud existuje
        if self.recorded_hotkey:
            self._update_display(self.recorded_hotkey)

        # Spuštění zachytávání kláves
        self._start_capture()

        # Ošetření zavření okna
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Destroy>", self._on_destroy_event)

    def _center_window(self, parent):
        self.update_idletasks()
        try:
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            w = 500
            h = 360
            x = px + max(0, (pw - w) // 2)
            y = py + max(0, (ph - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            self.geometry("500x360+300+250")

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        # 1. Horní záhlaví s ikonou a vysvětlením
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))

        lbl_icon = ctk.CTkLabel(
            header,
            text="⌨",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#FF7A29"
        )
        lbl_icon.pack(side="left", padx=(0, 12))

        header_text = ctk.CTkFrame(header, fg_color="transparent")
        header_text.pack(side="left", fill="x", expand=True)

        lbl_title = ctk.CTkLabel(
            header_text,
            text="Záznam klávesové zkratky",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FFFFFF"
        )
        lbl_title.pack(anchor="w")

        lbl_sub = ctk.CTkLabel(
            header_text,
            text="Stiskněte libovolné klávesy na klávesnici (např. Ctrl+Shift+M, F10 apod.)",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        )
        lbl_sub.pack(anchor="w")

        # 2. Centrální rámeček pro živou vizualizaci kláves
        self.preview_card = ctk.CTkFrame(
            container,
            height=100,
            fg_color="#131520",
            corner_radius=12,
            border_width=1,
            border_color="#242838"
        )
        self.preview_card.pack_propagate(False)
        self.preview_card.pack(fill="x", pady=(0, 12))

        self.badges_container = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        self.badges_container.place(relx=0.5, rely=0.5, anchor="center")

        # Výchozí zpráva čekání
        self.lbl_placeholder = ctk.CTkLabel(
            self.badges_container,
            text="● Čekám na stisk kláves...",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#64748B"
        )
        self.lbl_placeholder.pack()

        # 3. Informační stavový řádek a manuální zobrazení
        info_row = ctk.CTkFrame(container, fg_color="transparent")
        info_row.pack(fill="x", pady=(0, 16))

        self.lbl_raw_value = ctk.CTkLabel(
            info_row,
            text="Kód zkratky: (zatím nezadáno)",
            font=ctk.CTkFont(size=11),
            text_color="#64748B"
        )
        self.lbl_raw_value.pack(side="left")

        # 4. Spodní lišta s tlačítky
        btn_bar = ctk.CTkFrame(container, fg_color="transparent")
        btn_bar.pack(fill="x", side="bottom")

        self.btn_cancel = ctk.CTkButton(
            btn_bar,
            text="Zrušit",
            width=90,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            fg_color="#181A24",
            border_width=1,
            border_color="#282C3D",
            text_color="#94A3B8",
            hover_color="#222534",
            command=self._on_cancel
        )
        self.btn_cancel.pack(side="left")

        self.btn_reset = ctk.CTkButton(
            btn_bar,
            text="Znovu stisknout",
            width=120,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            fg_color="#181A24",
            border_width=1,
            border_color="#3B4256",
            text_color="#E2E8F0",
            hover_color="#2A2F42",
            command=self._on_reset
        )
        self.btn_reset.pack(side="left", padx=10)

        self.btn_confirm = ctk.CTkButton(
            btn_bar,
            text="Potvrdit zkratku",
            width=150,
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#241E1A",
            border_width=1,
            border_color="#4D331C",
            text_color="#888888",
            hover_color="#332417",
            command=self._on_confirm
        )
        self.btn_confirm.pack(side="right")

    def _start_capture(self):
        """Spustí zachytávání kláves přes keyboard hook a Tkinter bindings."""
        # Nastavíme standardní US rozložení (00000409) pro tento proces,
        # aby nízkoúrovňový hook neovlivňovala česká klávesnice v OS
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hkl_us = user32.LoadKeyboardLayoutW("00000409", 1)
            if hkl_us:
                user32.ActivateKeyboardLayout(hkl_us, 0x00000100) # KLF_SETFORPROCESS
        except Exception:
            pass

        if HAS_KEYBOARD:
            try:
                self._hook_handle = keyboard.hook(self._on_keyboard_event)
            except Exception as e:
                print(f"[HotkeyRecorder] Keyboard hook selhal: {e}, použije se Tkinter fallback.")
                self._hook_handle = None

        # Tkinter fallback bindings pro jistotu
        self.bind("<KeyPress>", self._on_tk_key_press)
        self.bind("<KeyRelease>", self._on_tk_key_release)
        self.focus_force()

    def _stop_capture(self):
        """Bezpečně odregistruje klávesový hook."""
        if self._hook_handle is not None and HAS_KEYBOARD:
            try:
                keyboard.unhook(self._hook_handle)
            except Exception:
                pass
            self._hook_handle = None

    def _on_keyboard_event(self, e):
        """Zpracovává nízkoúrovňové události z modulu keyboard s garancí standardního rozložení."""
        if self._is_closed:
            return

        event_type = e.event_type
        sc = getattr(e, "scan_code", None)
        raw_name = str(e.name or "").strip().lower()

        # 1. Zjistíme modifikátor (podle scan kódu nebo názvu)
        mod_key = MODIFIER_SCAN_CODES.get(sc) or MODIFIER_MAP.get(raw_name)

        if event_type == "down":
            if mod_key:
                self.active_modifiers.add(mod_key)
                self.after(0, lambda: self._update_modifiers_preview())
            else:
                # 2. Určíme standardní název klávesy nezávisle na jazyku
                resolved_key = None
                if sc in SCAN_CODE_MAP:
                    resolved_key = SCAN_CODE_MAP[sc]
                elif raw_name in CZECH_CHAR_TO_STANDARD:
                    resolved_key = CZECH_CHAR_TO_STANDARD[raw_name]
                else:
                    resolved_key = raw_name

                if not resolved_key:
                    return

                # Běžná klávesa -> sestavíme kompletní zkratku
                mods_ordered = [m for m in ["ctrl", "shift", "alt", "windows"] if m in self.active_modifiers]
                combo_parts = mods_ordered + [resolved_key]
                shortcut = normalize_hotkey("+".join(combo_parts))
                self.after(0, lambda s=shortcut: self._on_shortcut_captured(s))

        elif event_type == "up":
            if mod_key:
                self.active_modifiers.discard(mod_key)
                if not self.recorded_hotkey:
                    self.after(0, lambda: self._update_modifiers_preview())

    def _on_tk_key_press(self, event):
        """Tkinter záložní zachycení, pokud hook neběží."""
        if self._hook_handle is not None:
            return  # Hlavní zachytávání řídí hook

        sym = (event.keysym or "").strip().lower()
        sym = TK_CZECH_KEYSYMS.get(sym, sym)
        mapped = KEYSYM_FALLBACK.get(sym, sym)
        mapped = CZECH_CHAR_TO_STANDARD.get(mapped, mapped)

        # Kontrola standardních VK kódů (čísla 0-9)
        if hasattr(event, "keycode"):
            kc = event.keycode
            if 48 <= kc <= 57:  # VK_0 - VK_9
                mapped = chr(kc)

        if mapped in ["ctrl", "shift", "alt", "windows"]:
            self.active_modifiers.add(mapped)
            self._update_modifiers_preview()
        else:
            mods_ordered = [m for m in ["ctrl", "shift", "alt", "windows"] if m in self.active_modifiers]
            combo_parts = mods_ordered + [mapped]
            shortcut = normalize_hotkey("+".join(combo_parts))
            self._on_shortcut_captured(shortcut)

    def _on_tk_key_release(self, event):
        if self._hook_handle is not None:
            return
        sym = (event.keysym or "").strip().lower()
        mapped = KEYSYM_FALLBACK.get(sym, sym)
        if mapped in ["ctrl", "shift", "alt", "windows"]:
            self.active_modifiers.discard(mapped)
            if not self.recorded_hotkey:
                self._update_modifiers_preview()

    def _update_modifiers_preview(self):
        """Zobrazí aktuálně držené modifikátory."""
        if self._is_closed:
            return
        if not self.active_modifiers:
            if not self.recorded_hotkey:
                self._clear_badges()
                self.lbl_placeholder = ctk.CTkLabel(
                    self.badges_container,
                    text="● Čekám na stisk kláves...",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color="#64748B"
                )
                self.lbl_placeholder.pack()
                self.preview_card.configure(border_color="#242838")
            return

        mods_ordered = [m for m in ["ctrl", "shift", "alt", "windows"] if m in self.active_modifiers]
        self._render_badges(mods_ordered + ["..."])
        self.preview_card.configure(border_color="#FF7A29")
        self.lbl_raw_value.configure(text=f"Držíte: {' + '.join(mods_ordered)}...", text_color="#FF7A29")

    def _on_shortcut_captured(self, shortcut):
        """Zaznamená stisknutou klávesovou zkratku a aktualizuje UI."""
        if self._is_closed or not shortcut:
            return
        self.recorded_hotkey = shortcut
        self._update_display(shortcut)

        # Povolit tlačítko potvrzení
        self.btn_confirm.configure(
            fg_color="#FF7A29",
            border_width=0,
            text_color="#0B0B0E",
            hover_color="#FF944D"
        )
        self.preview_card.configure(border_color="#2ECC71")

    def _update_display(self, shortcut):
        """Rozdělí zkratku na části a vykreslí pro každou tlačítkový badge."""
        parts = [p.strip() for p in shortcut.split("+") if p.strip()]
        self._render_badges(parts)
        self.lbl_raw_value.configure(
            text=f"Zaznamenaná zkratka:  {shortcut}",
            text_color="#CBD5E1"
        )
        self.btn_confirm.configure(
            fg_color="#FF7A29",
            border_width=0,
            text_color="#0B0B0E",
            hover_color="#FF944D"
        )

    def _clear_badges(self):
        for child in self.badges_container.winfo_children():
            child.destroy()

    def _render_badges(self, parts):
        self._clear_badges()
        for idx, part in enumerate(parts):
            disp = DISPLAY_NAMES.get(part.lower(), part.upper() if len(part) <= 3 else part.capitalize())
            
            # Badge tlačítko
            is_active = (part != "...")
            badge = ctk.CTkFrame(
                self.badges_container,
                fg_color="#FF7A29" if is_active else "#1E2230",
                corner_radius=7,
                border_width=1 if not is_active else 0,
                border_color="#3B4256"
            )
            badge.pack(side="left", padx=4, pady=6)

            lbl = ctk.CTkLabel(
                badge,
                text=disp,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#0B0B0E" if is_active else "#94A3B8"
            )
            lbl.pack(padx=12, pady=6)

            # Znaménko plus mezi klávesami
            if idx < len(parts) - 1:
                plus = ctk.CTkLabel(
                    self.badges_container,
                    text="+",
                    font=ctk.CTkFont(size=15, weight="bold"),
                    text_color="#64748B"
                )
                plus.pack(side="left", padx=2)

    def _on_reset(self):
        """Vymaže stávající záznam a umožní stisknout novou kombinaci."""
        self.recorded_hotkey = ""
        self.active_modifiers.clear()
        self._clear_badges()
        self.lbl_placeholder = ctk.CTkLabel(
            self.badges_container,
            text="● Čekám na stisk kláves...",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#64748B"
        )
        self.lbl_placeholder.pack()
        self.preview_card.configure(border_color="#242838")
        self.lbl_raw_value.configure(text="Kód zkratky: (zatím nezadáno)", text_color="#64748B")
        self.btn_confirm.configure(
            fg_color="#241E1A",
            border_width=1,
            border_color="#4D331C",
            text_color="#888888",
            hover_color="#332417"
        )

    def _on_confirm(self):
        """Potvrdí zaznamenanou zkratku a uzavře dialog."""
        if not self.recorded_hotkey:
            return
        self.result = self.recorded_hotkey
        self._close()

    def _on_cancel(self):
        """Zruší záznam a uzavře dialog bez uložení."""
        self.result = None
        self._close()

    def _on_destroy_event(self, event):
        if event.widget == self:
            self._stop_capture()
            self._is_closed = True

    def _close(self):
        if not self._is_closed:
            self._is_closed = True
            self._stop_capture()
            try:
                self.grab_release()
            except Exception:
                pass
            self.destroy()

    def get_hotkey(self):
        """Blokuje běh dokud uživatel nepotvrdí nebo nezruší okno, a vrací zkratku jako string."""
        self.wait_window(self)
        return self.result
