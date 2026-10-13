import os
from PIL import Image
import customtkinter as ctk

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets", "icons")
BASE_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
_CACHE = {}

VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".ico", ".webp", ".bmp")

def clear_icon_cache():
    """Vymaže mezipaměť načtených ikon (např. po přidání nových souborů)."""
    global _CACHE
    _CACHE.clear()

def find_asset_icon_path(name):
    """
    Najde absolutní cestu k ikoně podle názvu nebo klíče.
    Prohledává složku assets/icons/ i assets/ a podporuje různé přípony.
    """
    if not name or name == "none":
        return None

    # Pokud je už předána existující cesta
    if os.path.isabs(name) and os.path.exists(name):
        return name

    search_dirs = [ASSETS_DIR, BASE_ASSETS_DIR]

    # 1. Zkusíme přímý název (může mít příponu)
    for sdir in search_dirs:
        candidate = os.path.join(sdir, name)
        if os.path.isfile(candidate):
            return candidate

    # 2. Zkusíme s běžnými příponami obrázků
    for sdir in search_dirs:
        for ext in VALID_EXTENSIONS:
            candidate = os.path.join(sdir, f"{name}{ext}")
            if os.path.isfile(candidate):
                return candidate

    return None

def get_asset_icon(name, size=(24, 24)):
    """Načte ikonu ze složky assets/icons (nebo assets) jako CTkImage s cacheováním."""
    if not name or name == "none":
        return None
    key = (name, size)
    if key in _CACHE:
        return _CACHE[key]

    path = find_asset_icon_path(name)
    if path and os.path.exists(path):
        try:
            pil_img = Image.open(path).convert("RGBA")
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
            _CACHE[key] = ctk_img
            return ctk_img
        except Exception:
            return None
    return None

def get_all_asset_icons():
    """
    Dynamicky prohledá složku assets/icons i assets/ a vrátí slovník všech dostupných ikon.
    Klíč: název ikony bez přípony (vhodný pro uložení do profilu)
    Hodnota: slovník s metadaty {'key': stem, 'path': path, 'name': display_name, 'file': filename}
    """
    icons = {}
    search_dirs = [ASSETS_DIR, BASE_ASSETS_DIR]

    for sdir in search_dirs:
        if not os.path.exists(sdir):
            continue
        try:
            for f in os.listdir(sdir):
                full_p = os.path.join(sdir, f)
                if os.path.isfile(full_p):
                    stem, ext = os.path.splitext(f)
                    if ext.lower() in VALID_EXTENSIONS and f != "Hlavní-menu.png" and not f.startswith("."):
                        if stem not in icons:
                            # Hezký zobrazovací název
                            display_name = stem.replace("_", " ").replace("-", " ").title()
                            icons[stem] = {
                                "key": stem,
                                "path": full_p,
                                "name": display_name,
                                "file": f
                            }
        except Exception as e:
            print(f"[Assets] Chyba prohledávání {sdir}: {e}")

    return icons

def load_custom_image(path, size=(32, 32)):
    """Načte vlastní uživatelský obrázek z libovolné cesty v PC (podporuje PNG, JPG, ICO, LNK, EXE)."""
    if not path:
        return None
    key = (path, size)
    if key in _CACHE:
        return _CACHE[key]

    real_path = path
    if path.lower().endswith((".exe", ".lnk", ".url", ".bat", ".cmd")):
        try:
            from icon_extractor import get_extracted_icon_png_path
            extracted = get_extracted_icon_png_path(path)
            if extracted and os.path.exists(extracted):
                real_path = extracted
        except Exception:
            pass

    if not os.path.exists(real_path):
        return None

    try:
        pil_img = Image.open(real_path).convert("RGBA")
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        _CACHE[key] = ctk_img
        return ctk_img
    except Exception:
        return None
