import os
from PIL import Image
import customtkinter as ctk

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets", "icons")
_CACHE = {}

def get_asset_icon(name, size=(24, 24)):
    """Načte ikonu ze složky assets/icons jako CTkImage s cacheováním."""
    if not name or name == "none":
        return None
    key = (name, size)
    if key in _CACHE:
        return _CACHE[key]

    path = os.path.join(ASSETS_DIR, f"{name}.png")
    if os.path.exists(path):
        try:
            pil_img = Image.open(path).convert("RGBA")
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
            _CACHE[key] = ctk_img
            return ctk_img
        except Exception:
            return None
    return None

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
