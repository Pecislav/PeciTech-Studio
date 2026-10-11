import os
import math
from PIL import Image, ImageDraw

OUT_DIR = os.path.join(os.path.dirname(__file__), "icons")
os.makedirs(OUT_DIR, exist_ok=True)

ORANGE = (255, 122, 41, 255)
ORANGE_LIGHT = (255, 157, 84, 255)
WHITE = (245, 245, 250, 255)
SILVER = (200, 205, 220, 255)
RED = (255, 68, 68, 255)
GREEN = (30, 215, 96, 255)
DISCORD_CLR = (88, 101, 242, 255)
PURPLE = (145, 70, 255, 255)
CYAN = (0, 229, 255, 255)
DARK_BG = (27, 28, 38, 255)

def save_icon(name, draw_fn, size=128):
    scale = 4
    canvas_size = size * scale
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_fn(draw, canvas_size)
    final = img.resize((size, size), Image.Resampling.LANCZOS)
    path = os.path.join(OUT_DIR, f"{name}.png")
    final.save(path, "PNG")

# 1. Play
def d_play(d, s):
    pad_x = s * 0.28
    pad_y = s * 0.22
    poly = [(pad_x, pad_y), (s - pad_x + s*0.06, s/2), (pad_x, s - pad_y)]
    d.polygon(poly, fill=ORANGE)
save_icon("play", d_play)

# 2. Pause
def d_pause(d, s):
    w = s * 0.16
    h = s * 0.54
    y = s * 0.23
    r = w * 0.3
    d.rounded_rectangle([s*0.28, y, s*0.28 + w, y + h], radius=r, fill=ORANGE)
    d.rounded_rectangle([s*0.56, y, s*0.56 + w, y + h], radius=r, fill=ORANGE)
save_icon("pause", d_pause)

# 3. Next
def d_next(d, s):
    pad = s * 0.24
    d.polygon([(pad, pad), (s*0.60, s/2), (pad, s - pad)], fill=ORANGE)
    bar_w = s * 0.10
    d.rounded_rectangle([s*0.66, pad, s*0.66 + bar_w, s - pad], radius=bar_w*0.3, fill=ORANGE)
save_icon("next", d_next)

# 4. Prev
def d_prev(d, s):
    pad = s * 0.24
    d.polygon([(s - pad, pad), (s*0.40, s/2), (s - pad, s - pad)], fill=ORANGE)
    bar_w = s * 0.10
    d.rounded_rectangle([s*0.34 - bar_w, pad, s*0.34, s - pad], radius=bar_w*0.3, fill=ORANGE)
save_icon("prev", d_prev)

# 5. Stop
def d_stop(d, s):
    pad = s * 0.26
    d.rounded_rectangle([pad, pad, s - pad, s - pad], radius=s*0.08, fill=ORANGE)
save_icon("stop", d_stop)

# 6. Volume Up
def d_vol_up(d, s):
    # Speaker cone
    d.polygon([(s*0.20, s*0.38), (s*0.32, s*0.38), (s*0.50, s*0.22), (s*0.50, s*0.78), (s*0.32, s*0.62), (s*0.20, s*0.62)], fill=ORANGE)
    # Small wave
    d.arc([s*0.44, s*0.34, s*0.68, s*0.66], start=-55, end=55, fill=ORANGE, width=int(s*0.06))
    # Big wave
    d.arc([s*0.44, s*0.22, s*0.84, s*0.78], start=-55, end=55, fill=ORANGE, width=int(s*0.06))
save_icon("vol_up", d_vol_up)

# 7. Volume Down
def d_vol_down(d, s):
    d.polygon([(s*0.20, s*0.38), (s*0.32, s*0.38), (s*0.50, s*0.22), (s*0.50, s*0.78), (s*0.32, s*0.62), (s*0.20, s*0.62)], fill=ORANGE)
    d.arc([s*0.44, s*0.34, s*0.68, s*0.66], start=-55, end=55, fill=ORANGE, width=int(s*0.06))
save_icon("vol_down", d_vol_down)

# 8. Mute
def d_mute(d, s):
    d.polygon([(s*0.18, s*0.38), (s*0.30, s*0.38), (s*0.48, s*0.22), (s*0.48, s*0.78), (s*0.30, s*0.62), (s*0.18, s*0.62)], fill=ORANGE)
    # Cross 'X'
    cx = s * 0.70
    cy = s * 0.50
    r = s * 0.12
    w = int(s * 0.055)
    d.line([(cx - r, cy - r), (cx + r, cy + r)], fill=RED, width=w)
    d.line([(cx - r, cy + r), (cx + r, cy - r)], fill=RED, width=w)
save_icon("mute", d_mute)

# 9. Mic
def d_mic(d, s):
    # Capsule
    w = s * 0.22
    h = s * 0.36
    x = s*0.5 - w/2
    y = s * 0.20
    d.rounded_rectangle([x, y, x + w, y + h], radius=w/2, fill=WHITE)
    # Stand arc
    d.arc([s*0.30, s*0.30, s*0.70, s*0.68], start=0, end=180, fill=WHITE, width=int(s*0.06))
    # Stem & base
    d.line([(s*0.5, s*0.68), (s*0.5, s*0.80)], fill=WHITE, width=int(s*0.06))
    d.line([(s*0.36, s*0.80), (s*0.64, s*0.80)], fill=WHITE, width=int(s*0.06))
save_icon("mic", d_mic)

# 10. Headset
def d_headset(d, s):
    # Arc
    d.arc([s*0.22, s*0.18, s*0.78, s*0.74], start=180, end=360, fill=WHITE, width=int(s*0.07))
    # Earcups
    ew = s * 0.14
    eh = s * 0.28
    d.rounded_rectangle([s*0.18, s*0.46, s*0.18 + ew, s*0.46 + eh], radius=ew*0.4, fill=ORANGE)
    d.rounded_rectangle([s*0.82 - ew, s*0.46, s*0.82, s*0.46 + eh], radius=ew*0.4, fill=ORANGE)
save_icon("headset", d_headset)

# 11. OBS
def d_obs(d, s):
    cx = s * 0.5
    cy = s * 0.5
    r = s * 0.36
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=WHITE, width=int(s*0.05))
    # 3 spiral lobes
    for ang in [0, 120, 240]:
        rad = math.radians(ang)
        lx = cx + math.cos(rad) * (r * 0.38)
        ly = cy + math.sin(rad) * (r * 0.38)
        lr = r * 0.42
        d.ellipse([lx - lr, ly - lr, lx + lr, ly + lr], outline=ORANGE, width=int(s*0.05))
save_icon("obs", d_obs)

# 12. Rec
def d_rec(d, s):
    r = s * 0.34
    d.ellipse([s*0.5 - r, s*0.5 - r, s*0.5 + r, s*0.5 + r], fill=RED)
    # Inner subtle dot
    r2 = s * 0.14
    d.ellipse([s*0.5 - r2, s*0.5 - r2, s*0.5 + r2, s*0.5 + r2], fill=(255, 200, 200, 255))
save_icon("rec", d_rec)

# 13. Discord
def d_discord(d, s):
    # Controller body
    x1, y1 = s * 0.20, s * 0.28
    x2, y2 = s * 0.80, s * 0.72
    d.rounded_rectangle([x1, y1, x2, y2], radius=s*0.12, fill=DISCORD_CLR)
    # Bottom horns
    d.polygon([(s*0.26, y2), (s*0.35, s*0.82), (s*0.42, y2)], fill=DISCORD_CLR)
    d.polygon([(s*0.58, y2), (s*0.65, s*0.82), (s*0.74, y2)], fill=DISCORD_CLR)
    # Eyes
    er = s * 0.075
    d.ellipse([s*0.38 - er, s*0.48 - er, s*0.38 + er, s*0.48 + er], fill=WHITE)
    d.ellipse([s*0.62 - er, s*0.48 - er, s*0.62 + er, s*0.48 + er], fill=WHITE)
save_icon("discord", d_discord)

# 14. Steam
def d_steam(d, s):
    cx, cy = s * 0.5, s * 0.5
    r = s * 0.36
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(30, 45, 65, 255), outline=SILVER, width=int(s*0.04))
    # Steam crank
    c1x, c1y = s * 0.62, s * 0.38
    r1 = s * 0.14
    d.ellipse([c1x - r1, c1y - r1, c1x + r1, c1y + r1], fill=WHITE)
    d.ellipse([c1x - r1*0.4, c1y - r1*0.4, c1x + r1*0.4, c1y + r1*0.4], fill=(30, 45, 65, 255))
    c2x, c2y = s * 0.38, s * 0.62
    r2 = s * 0.10
    d.line([(c1x, c1y), (c2x, c2y)], fill=WHITE, width=int(s*0.07))
    d.ellipse([c2x - r2, c2y - r2, c2x + r2, c2y + r2], fill=WHITE)
save_icon("steam", d_steam)

# 15. Lock
def d_lock(d, s):
    # Body
    bw = s * 0.44
    bh = s * 0.36
    bx = s*0.5 - bw/2
    by = s * 0.46
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=s*0.06, fill=ORANGE)
    # Shackle
    sw = s * 0.28
    sh = s * 0.30
    sx = s*0.5 - sw/2
    sy = s * 0.22
    d.arc([sx, sy, sx + sw, sy + sh*1.5], start=180, end=360, fill=WHITE, width=int(s*0.07))
    # Keyhole
    d.ellipse([s*0.5 - s*0.035, by + bh*0.35 - s*0.035, s*0.5 + s*0.035, by + bh*0.35 + s*0.035], fill=WHITE)
    d.line([(s*0.5, by + bh*0.35), (s*0.5, by + bh*0.65)], fill=WHITE, width=int(s*0.03))
save_icon("lock", d_lock)

# 16. Copy
def d_copy(d, s):
    w = s * 0.36
    h = s * 0.46
    # Back sheet
    d.rounded_rectangle([s*0.22, s*0.20, s*0.22 + w, s*0.20 + h], radius=s*0.04, outline=SILVER, width=int(s*0.045))
    # Front sheet
    d.rounded_rectangle([s*0.38, s*0.34, s*0.38 + w, s*0.34 + h], radius=s*0.04, fill=(24, 25, 35, 255), outline=ORANGE, width=int(s*0.05))
save_icon("copy", d_copy)

# 17. Paste
def d_paste(d, s):
    # Clipboard
    bw = s * 0.48
    bh = s * 0.54
    bx = s*0.5 - bw/2
    by = s * 0.28
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=s*0.05, outline=SILVER, width=int(s*0.045))
    # Clip
    cw = s * 0.24
    ch = s * 0.12
    cx = s*0.5 - cw/2
    cy = s * 0.20
    d.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=s*0.03, fill=ORANGE)
    # Content sheet inside
    d.line([(bx + bw*0.25, by + bh*0.40), (bx + bw*0.75, by + bh*0.40)], fill=WHITE, width=int(s*0.03))
    d.line([(bx + bw*0.25, by + bh*0.60), (bx + bw*0.75, by + bh*0.60)], fill=WHITE, width=int(s*0.03))
    d.line([(bx + bw*0.25, by + bh*0.80), (bx + bw*0.55, by + bh*0.80)], fill=WHITE, width=int(s*0.03))
save_icon("paste", d_paste)

# 18. Folder
def d_folder(d, s):
    # Tab
    d.polygon([(s*0.20, s*0.32), (s*0.45, s*0.32), (s*0.52, s*0.40), (s*0.20, s*0.40)], fill=ORANGE)
    # Body
    d.rounded_rectangle([s*0.20, s*0.38, s*0.80, s*0.76], radius=s*0.06, fill=ORANGE)
    # Inner front flap
    d.polygon([(s*0.20, s*0.48), (s*0.80, s*0.48), (s*0.76, s*0.76), (s*0.24, s*0.76)], fill=ORANGE_LIGHT)
save_icon("folder", d_folder)

# 19. Calc
def d_calc(d, s):
    w = s * 0.46
    h = s * 0.60
    x = s*0.5 - w/2
    y = s * 0.20
    d.rounded_rectangle([x, y, x + w, y + h], radius=s*0.06, outline=SILVER, width=int(s*0.045))
    # Display screen
    d.rounded_rectangle([x + s*0.05, y + s*0.05, x + w - s*0.05, y + s*0.18], radius=s*0.02, fill=ORANGE)
    # Buttons grid
    for r in range(3):
        for c in range(3):
            bx = x + s*0.07 + c*s*0.11
            by = y + s*0.24 + r*s*0.11
            d.ellipse([bx, by, bx + s*0.06, by + s*0.06], fill=WHITE)
save_icon("calc", d_calc)

# 20. YouTube
def d_youtube(d, s):
    w = s * 0.60
    h = s * 0.44
    x = s*0.5 - w/2
    y = s*0.5 - h/2
    d.rounded_rectangle([x, y, x + w, y + h], radius=s*0.10, fill=RED)
    # Centered play triangle
    tw = s * 0.16
    th = s * 0.18
    tx = s * 0.5 - tw*0.3
    ty = s * 0.5
    d.polygon([(tx - tw/2, ty - th/2), (tx + tw/2, ty), (tx - tw/2, ty + th/2)], fill=WHITE)
save_icon("youtube", d_youtube)

# 21. Spotify
def d_spotify(d, s):
    r = s * 0.36
    d.ellipse([s*0.5 - r, s*0.5 - r, s*0.5 + r, s*0.5 + r], fill=GREEN)
    # 3 black sound arcs
    w = int(s * 0.055)
    d.arc([s*0.32, s*0.28, s*0.68, s*0.64], start=205, end=335, fill=(18, 18, 20, 255), width=w)
    d.arc([s*0.35, s*0.38, s*0.65, s*0.68], start=205, end=335, fill=(18, 18, 20, 255), width=int(w*0.85))
    d.arc([s*0.38, s*0.48, s*0.62, s*0.72], start=205, end=335, fill=(18, 18, 20, 255), width=int(w*0.75))
save_icon("spotify", d_spotify)

# 22. Twitch
def d_twitch(d, s):
    w = s * 0.52
    h = s * 0.52
    x = s*0.5 - w/2
    y = s*0.5 - h/2
    # Chat bubble
    d.polygon([
        (x, y), (x + w, y), (x + w, y + h*0.75), 
        (x + w*0.75, y + h), (x + w*0.55, y + h*0.75), 
        (x + w*0.30, y + h*0.75), (x, y + h*0.50)
    ], fill=PURPLE)
    # Eyes
    ew = s * 0.06
    eh = s * 0.14
    d.rounded_rectangle([x + w*0.35, y + h*0.25, x + w*0.35 + ew, y + h*0.25 + eh], radius=ew*0.3, fill=WHITE)
    d.rounded_rectangle([x + w*0.65 - ew, y + h*0.25, x + w*0.65, y + h*0.25 + eh], radius=ew*0.3, fill=WHITE)
save_icon("twitch", d_twitch)

# 23. Web / Globe
def d_web(d, s):
    r = s * 0.34
    cx, cy = s * 0.5, s * 0.5
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=CYAN, width=int(s*0.05))
    d.ellipse([cx - r*0.45, cy - r, cx + r*0.45, cy + r], outline=CYAN, width=int(s*0.04))
    d.line([(cx - r, cy), (cx + r, cy)], fill=CYAN, width=int(s*0.04))
    d.line([(cx - r*0.85, cy - r*0.5), (cx + r*0.85, cy - r*0.5)], fill=CYAN, width=int(s*0.035))
    d.line([(cx - r*0.85, cy + r*0.5), (cx + r*0.85, cy + r*0.5)], fill=CYAN, width=int(s*0.035))
save_icon("web", d_web)

# 24. App / Program (Lightning / Rocket)
def d_app(d, s):
    poly = [
        (s*0.54, s*0.16), (s*0.32, s*0.50), (s*0.48, s*0.50),
        (s*0.44, s*0.84), (s*0.70, s*0.44), (s*0.54, s*0.44)
    ]
    d.polygon(poly, fill=ORANGE)
save_icon("app", d_app)

# 25. Hotkey / Keyboard
def d_hotkey(d, s):
    w = s * 0.54
    h = s * 0.44
    x = s*0.5 - w/2
    y = s*0.5 - h/2
    d.rounded_rectangle([x, y, x + w, y + h], radius=s*0.08, outline=ORANGE, width=int(s*0.05))
    # Keycap bevel line
    d.rounded_rectangle([x + s*0.04, y + s*0.04, x + w - s*0.04, y + h - s*0.04], radius=s*0.04, outline=(70, 75, 95, 255), width=int(s*0.025))
    # Command / key glyph
    d.line([(x + w*0.30, y + h*0.55), (x + w*0.70, y + h*0.55)], fill=WHITE, width=int(s*0.04))
save_icon("hotkey", d_hotkey)

# 26. Screenshot
def d_screenshot(d, s):
    pad = s * 0.22
    w = int(s * 0.05)
    # 4 crop corners
    l = s * 0.16
    # Top Left
    d.line([(pad, pad + l), (pad, pad), (pad + l, pad)], fill=CYAN, width=w)
    # Top Right
    d.line([(s - pad - l, pad), (s - pad, pad), (s - pad, pad + l)], fill=CYAN, width=w)
    # Bottom Left
    d.line([(pad, s - pad - l), (pad, s - pad), (pad + l, s - pad)], fill=CYAN, width=w)
    # Bottom Right
    d.line([(s - pad - l, s - pad), (s - pad, s - pad), (s - pad, s - pad - l)], fill=CYAN, width=w)
    # Center dot
    d.ellipse([s*0.5 - s*0.04, s*0.5 - s*0.04, s*0.5 + s*0.04, s*0.5 + s*0.04], fill=WHITE)
save_icon("screenshot", d_screenshot)

# 27. Scene
def d_scene(d, s):
    w = s * 0.46
    h = s * 0.32
    # Layer 1 (back)
    d.rounded_rectangle([s*0.32, s*0.22, s*0.32 + w, s*0.22 + h], radius=s*0.04, outline=SILVER, width=int(s*0.04))
    # Layer 2 (front)
    d.rounded_rectangle([s*0.22, s*0.44, s*0.22 + w, s*0.44 + h], radius=s*0.04, fill=(20, 22, 30, 255), outline=ORANGE, width=int(s*0.05))
save_icon("scene", d_scene)

# 28. None / Empty
def d_none(d, s):
    r = s * 0.26
    cx, cy = s*0.5, s*0.5
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(100, 105, 125, 255), width=int(s*0.045))
    d.line([(cx - r*0.7, cy - r*0.7), (cx + r*0.7, cy + r*0.7)], fill=(100, 105, 125, 255), width=int(s*0.045))
save_icon("none", d_none)

# Category Icons:
# Cat Media
def d_cat_media(d, s):
    # Two eighth notes connected
    d.ellipse([s*0.24, s*0.56, s*0.42, s*0.74], fill=ORANGE)
    d.ellipse([s*0.58, s*0.48, s*0.76, s*0.66], fill=ORANGE)
    d.line([(s*0.40, s*0.65), (s*0.40, s*0.28)], fill=ORANGE, width=int(s*0.06))
    d.line([(s*0.74, s*0.57), (s*0.74, s*0.20)], fill=ORANGE, width=int(s*0.06))
    d.line([(s*0.37, s*0.28), (s*0.77, s*0.20)], fill=ORANGE, width=int(s*0.09))
save_icon("cat_media", d_cat_media)

# Cat Games
def d_cat_games(d, s):
    # Gamepad
    w = s * 0.58
    h = s * 0.38
    x = s*0.5 - w/2
    y = s*0.5 - h/2
    d.rounded_rectangle([x, y, x + w, y + h], radius=s*0.12, outline=WHITE, width=int(s*0.05))
    # D-pad cross on left
    d.line([(x + w*0.22, y + h*0.35), (x + w*0.22, y + h*0.65)], fill=WHITE, width=int(s*0.04))
    d.line([(x + w*0.14, y + h*0.50), (x + w*0.30, y + h*0.50)], fill=WHITE, width=int(s*0.04))
    # Buttons on right
    d.ellipse([x + w*0.75, y + h*0.38, x + w*0.83, y + h*0.46], fill=ORANGE)
    d.ellipse([x + w*0.67, y + h*0.54, x + w*0.75, y + h*0.62], fill=ORANGE)
save_icon("cat_games", d_cat_games)

# Cat OBS
def d_cat_obs(d, s):
    d_obs(d, s)
save_icon("cat_obs", d_cat_obs)

# Cat System
def d_cat_system(d, s):
    # Cpu chip
    w = s * 0.44
    x = s*0.5 - w/2
    y = s*0.5 - w/2
    d.rounded_rectangle([x, y, x + w, y + w], radius=s*0.06, outline=WHITE, width=int(s*0.05))
    # Pins
    for i in [-0.10, 0.10]:
        d.line([(s*0.5 + i*s, y), (s*0.5 + i*s, y - s*0.08)], fill=WHITE, width=int(s*0.04))
        d.line([(s*0.5 + i*s, y + w), (s*0.5 + i*s, y + w + s*0.08)], fill=WHITE, width=int(s*0.04))
        d.line([(x, s*0.5 + i*s), (x - s*0.08, s*0.5 + i*s)], fill=WHITE, width=int(s*0.04))
        d.line([(x + w, s*0.5 + i*s), (x + w + s*0.08, s*0.5 + i*s)], fill=WHITE, width=int(s*0.04))
save_icon("cat_system", d_cat_system)

# Cat Web
def d_cat_web(d, s):
    d_web(d, s)
save_icon("cat_web", d_cat_web)

# Cat Apps
def d_cat_apps(d, s):
    d_app(d, s)
save_icon("cat_apps", d_cat_apps)

# UI Icons:
# Gear
def d_gear(d, s):
    cx, cy = s*0.5, s*0.5
    r = s * 0.28
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=SILVER, width=int(s*0.08))
    # Center hole
    r_in = s * 0.12
    d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=(0, 0, 0, 0), outline=SILVER, width=int(s*0.04))
    # 8 teeth
    for i in range(8):
        ang = math.radians(i * 45)
        tx = cx + math.cos(ang) * (r + s*0.06)
        ty = cy + math.sin(ang) * (r + s*0.06)
        d.ellipse([tx - s*0.05, ty - s*0.05, tx + s*0.05, ty + s*0.05], fill=SILVER)
save_icon("gear", d_gear)

# Back Arrow
def d_back(d, s):
    d.line([(s*0.68, s*0.5), (s*0.32, s*0.5)], fill=WHITE, width=int(s*0.08))
    d.line([(s*0.48, s*0.32), (s*0.32, s*0.5), (s*0.48, s*0.68)], fill=WHITE, width=int(s*0.08))
save_icon("back", d_back)

# Search
def d_search(d, s):
    r = s * 0.20
    cx, cy = s * 0.44, s * 0.44
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=SILVER, width=int(s*0.065))
    d.line([(cx + r*0.7, cy + r*0.7), (s*0.76, s*0.76)], fill=SILVER, width=int(s*0.08))
save_icon("search", d_search)

# Chevron Down
def d_chevron_down(d, s):
    d.line([(s*0.30, s*0.42), (s*0.50, s*0.62), (s*0.70, s*0.42)], fill=SILVER, width=int(s*0.07))
save_icon("chevron_down", d_chevron_down)

# Chevron Right
def d_chevron_right(d, s):
    d.line([(s*0.42, s*0.30), (s*0.62, s*0.50), (s*0.42, s*0.70)], fill=SILVER, width=int(s*0.07))
save_icon("chevron_right", d_chevron_right)

# Trash
def d_trash(d, s):
    w = s * 0.36
    h = s * 0.42
    x = s*0.5 - w/2
    y = s * 0.38
    d.rounded_rectangle([x, y, x + w, y + h], radius=s*0.04, outline=RED, width=int(s*0.05))
    d.line([(x - s*0.06, y), (x + w + s*0.06, y)], fill=RED, width=int(s*0.05))
    d.line([(s*0.42, y), (s*0.42, y - s*0.07), (s*0.58, y - s*0.07), (s*0.58, y)], fill=RED, width=int(s*0.04))
    # Vertical slats
    d.line([(x + w*0.35, y + s*0.08), (x + w*0.35, y + h - s*0.08)], fill=RED, width=int(s*0.035))
    d.line([(x + w*0.65, y + s*0.08), (x + w*0.65, y + h - s*0.08)], fill=RED, width=int(s*0.035))
save_icon("trash", d_trash)

# Palette
def d_palette(d, s):
    cx, cy = s*0.5, s*0.5
    r = s * 0.34
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=WHITE, width=int(s*0.05))
    # Color dots
    d.ellipse([s*0.36, s*0.34, s*0.46, s*0.44], fill=ORANGE)
    d.ellipse([s*0.54, s*0.30, s*0.64, s*0.40], fill=CYAN)
    d.ellipse([s*0.64, s*0.48, s*0.74, s*0.58], fill=PURPLE)
save_icon("palette", d_palette)

# Empty Plus
def d_empty_plus(d, s):
    d.line([(s*0.5, s*0.32), (s*0.5, s*0.68)], fill=(75, 80, 100, 255), width=int(s*0.07))
    d.line([(s*0.32, s*0.5), (s*0.68, s*0.5)], fill=(75, 80, 100, 255), width=int(s*0.07))
save_icon("empty_plus", d_empty_plus)

# 3D Rotary Knob Dial (Pure high-end audio console dial with single orange notch)
def d_knob(d, s):
    cx, cy = s*0.5, s*0.5
    # Outer bezel ring
    r_out = s * 0.44
    d.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], fill=(28, 30, 42, 255), outline=(55, 60, 80, 255), width=int(s*0.03))
    # Concentric inner dial face
    r_in = s * 0.35
    d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=(18, 20, 28, 255), outline=(40, 44, 58, 255), width=int(s*0.02))
    # Single indicator notch on the perimeter (pointing straight up)
    notch_w = s * 0.055
    notch_len = s * 0.16
    d.rounded_rectangle([cx - notch_w/2, cy - r_in + s*0.02, cx + notch_w/2, cy - r_in + s*0.02 + notch_len], radius=notch_w*0.3, fill=ORANGE)
save_icon("knob_dial", d_knob)

print("All assets generated successfully!")
