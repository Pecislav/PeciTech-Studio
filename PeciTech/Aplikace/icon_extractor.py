import os
import hashlib
import configparser
import ctypes
from ctypes import wintypes
from PIL import Image
import customtkinter as ctk

# Adresář pro diskovou cache extrahovaných ikon
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache", "app_icons")
os.makedirs(CACHE_DIR, exist_ok=True)

# Paměťová cache pro okamžité zobrazení v UI
_MEM_CACHE = {}          # (cache_key, size) -> CTkImage
_PATH_TO_PNG_CACHE = {}  # raw_path -> cached_png_path

# Windows API inicializace
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
shell32 = ctypes.windll.shell32

class ICONINFO(ctypes.Structure):
    _fields_ = [
        ('fIcon', wintypes.BOOL),
        ('xHotspot', wintypes.DWORD),
        ('yHotspot', wintypes.DWORD),
        ('hbmMask', ctypes.c_void_p),
        ('hbmColor', ctypes.c_void_p)
    ]

class BITMAP(ctypes.Structure):
    _fields_ = [
        ('bmType', wintypes.LONG),
        ('bmWidth', wintypes.LONG),
        ('bmHeight', wintypes.LONG),
        ('bmWidthBytes', wintypes.LONG),
        ('bmPlanes', wintypes.WORD),
        ('bmBitsPixel', wintypes.WORD),
        ('bmBits', ctypes.c_void_p)
    ]

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ('biSize', wintypes.DWORD),
        ('biWidth', wintypes.LONG),
        ('biHeight', wintypes.LONG),
        ('biPlanes', wintypes.WORD),
        ('biBitCount', wintypes.WORD),
        ('biCompression', wintypes.DWORD),
        ('biSizeImage', wintypes.DWORD),
        ('biXPelsPerMeter', wintypes.LONG),
        ('biYPelsPerMeter', wintypes.LONG),
        ('biClrUsed', wintypes.DWORD),
        ('biClrImportant', wintypes.DWORD)
    ]

class SHFILEINFOW(ctypes.Structure):
    _fields_ = [
        ('hIcon', ctypes.c_void_p),
        ('iIcon', ctypes.c_int),
        ('dwAttributes', wintypes.DWORD),
        ('szDisplayName', wintypes.WCHAR * 260),
        ('szTypeName', wintypes.WCHAR * 80)
    ]

SHGFI_ICON = 0x000000100
SHGFI_LARGEICON = 0x000000000

gdi32.GetObjectW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
gdi32.GetObjectW.restype = ctypes.c_int

gdi32.GetDIBits.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT, wintypes.UINT, ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT]
gdi32.GetDIBits.restype = ctypes.c_int

gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
gdi32.DeleteObject.restype = wintypes.BOOL

user32.GetIconInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(ICONINFO)]
user32.GetIconInfo.restype = wintypes.BOOL

user32.DestroyIcon.argtypes = [ctypes.c_void_p]
user32.DestroyIcon.restype = wintypes.BOOL

user32.GetDC.argtypes = [ctypes.c_void_p]
user32.GetDC.restype = ctypes.c_void_p

user32.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
user32.ReleaseDC.restype = ctypes.c_int

shell32.ExtractAssociatedIconW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR, ctypes.POINTER(wintypes.WORD)]
shell32.ExtractAssociatedIconW.restype = ctypes.c_void_p

shell32.SHGetFileInfoW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(SHFILEINFOW), wintypes.UINT, wintypes.UINT]
shell32.SHGetFileInfoW.restype = ctypes.c_void_p

# Mapování běžných systémových zástupců a příkazů na reálné .exe cesty
_SYS_ROOT = os.environ.get("SystemRoot", r"C:\Windows")
_SYSTEM_EXE_MAP = {
    "calc": os.path.join(_SYS_ROOT, "System32", "calc.exe"),
    "explorer": os.path.join(_SYS_ROOT, "explorer.exe"),
    "taskmgr": os.path.join(_SYS_ROOT, "System32", "Taskmgr.exe"),
    "notepad": os.path.join(_SYS_ROOT, "notepad.exe"),
    "mspaint": os.path.join(_SYS_ROOT, "System32", "mspaint.exe"),
    "cmd": os.path.join(_SYS_ROOT, "System32", "cmd.exe"),
    "powershell": os.path.join(_SYS_ROOT, "System32", "WindowsPowerShell", "v1.0", "powershell.exe"),
    "settings": os.path.join(_SYS_ROOT, "System32", "SystemSettings.exe"),
}

def resolve_target_file(path):
    """Převede alias nebo vyhledá reálnou cestu k souboru se zdrojem ikony."""
    if not path:
        return ""
    p_lower = path.lower().strip()
    if p_lower in _SYSTEM_EXE_MAP:
        mapped = _SYSTEM_EXE_MAP[p_lower]
        if os.path.exists(mapped):
            return mapped
        return path

    # Zpracování herních zástupců .url (např. Steam hry)
    if path.lower().endswith(".url") and os.path.exists(path):
        try:
            cfg = configparser.ConfigParser()
            cfg.read(path, encoding="utf-8")
            if "InternetShortcut" in cfg and "IconFile" in cfg["InternetShortcut"]:
                ico_file = cfg["InternetShortcut"]["IconFile"].strip()
                if os.path.exists(ico_file):
                    return ico_file
        except Exception:
            pass

    return path

def _hicon_to_pil(h_icon):
    """Převede HICON handle na 32-bit RGBA PIL.Image."""
    if not h_icon:
        return None
    icon_info = ICONINFO()
    if not user32.GetIconInfo(h_icon, ctypes.byref(icon_info)):
        user32.DestroyIcon(h_icon)
        return None
    try:
        bmp = BITMAP()
        gdi32.GetObjectW(icon_info.hbmColor, ctypes.sizeof(BITMAP), ctypes.byref(bmp))
        width, height = bmp.bmWidth, bmp.bmHeight
        if width <= 0 or height <= 0:
            return None

        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = width
        bmi.biHeight = -height # top-down
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = 0

        buffer = ctypes.create_string_buffer(width * height * 4)
        hdc = user32.GetDC(0)
        gdi32.GetDIBits(hdc, icon_info.hbmColor, 0, height, buffer, ctypes.byref(bmi), 0)
        user32.ReleaseDC(0, hdc)

        img = Image.frombuffer('RGBA', (width, height), buffer.raw, 'raw', 'BGRA', 0, 1)

        # Ošetření alfa kanálu pro starší formáty ikon
        r, g, b, a = img.split()
        if a.getextrema() == (0, 0):
            img.putalpha(255)

        return img
    except Exception:
        return None
    finally:
        if icon_info.hbmColor:
            gdi32.DeleteObject(icon_info.hbmColor)
        if icon_info.hbmMask:
            gdi32.DeleteObject(icon_info.hbmMask)
        user32.DestroyIcon(h_icon)

def _extract_native_hicon_pil(file_path):
    """Extrahuje ikonu z Windows pomocí SHGetFileInfoW nebo ExtractAssociatedIconW."""
    if not os.path.exists(file_path):
        return None
        
    # Pokud jde přímo o .ico soubor, načíst přes PIL
    if file_path.lower().endswith(".ico"):
        try:
            with Image.open(file_path) as im:
                return im.convert("RGBA")
        except Exception:
            pass

    # 1. Metoda: SHGetFileInfoW (oficiální Windows Shell ikona pro jakýkoliv soubor/zástupce)
    try:
        sfi = SHFILEINFOW()
        res = shell32.SHGetFileInfoW(file_path, 0, ctypes.byref(sfi), ctypes.sizeof(SHFILEINFOW), SHGFI_ICON | SHGFI_LARGEICON)
        if res and sfi.hIcon:
            pil_img = _hicon_to_pil(sfi.hIcon)
            if pil_img:
                return pil_img
    except Exception:
        pass

    # 2. Metoda: ExtractAssociatedIconW
    try:
        icon_index = wintypes.WORD(0)
        h_icon = shell32.ExtractAssociatedIconW(0, file_path, ctypes.byref(icon_index))
        if h_icon:
            pil_img = _hicon_to_pil(h_icon)
            if pil_img:
                return pil_img
    except Exception:
        pass

    return None

def get_extracted_icon_png_path(raw_path):
    """
    Získá cestu k uloženému PNG souboru s extrahovanou ikonou.
    Pokud ikona ještě nebyla uložena v cache, extrahuje ji a uloží.
    """
    if not raw_path:
        return ""
    
    if raw_path in _PATH_TO_PNG_CACHE:
        return _PATH_TO_PNG_CACHE[raw_path]

    target = resolve_target_file(raw_path)
    if not target or not os.path.exists(target):
        return ""

    try:
        mtime = str(os.path.getmtime(target))
    except Exception:
        mtime = "0"

    hash_key = hashlib.md5(f"{target.lower()}_{mtime}".encode("utf-8")).hexdigest()
    png_path = os.path.join(CACHE_DIR, f"{hash_key}.png")

    if os.path.exists(png_path):
        _PATH_TO_PNG_CACHE[raw_path] = png_path
        return png_path

    # Extrahovat a uložit
    pil_img = _extract_native_hicon_pil(target)
    if pil_img:
        try:
            pil_img.save(png_path, "PNG")
            _PATH_TO_PNG_CACHE[raw_path] = png_path
            return png_path
        except Exception:
            pass

    return ""

def get_app_icon(raw_path, size=(30, 30)):
    """
    Vrátí tuple (CTkImage, cached_png_path).
    Pokud ikonu nelze extrahovat, vrátí (None, "").
    """
    if not raw_path:
        return None, ""

    mem_key = (raw_path.lower(), size)
    if mem_key in _MEM_CACHE:
        return _MEM_CACHE[mem_key], _PATH_TO_PNG_CACHE.get(raw_path, "")

    png_path = get_extracted_icon_png_path(raw_path)
    if not png_path or not os.path.exists(png_path):
        return None, ""

    try:
        pil_img = Image.open(png_path).convert("RGBA")
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        _MEM_CACHE[mem_key] = ctk_img
        return ctk_img, png_path
    except Exception:
        return None, ""
