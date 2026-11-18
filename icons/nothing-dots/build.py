#!/usr/bin/env python3
"""Nothing Dots icon theme generator.

Every app icon is a black circle holding a 13x13 dot-matrix field:
unlit dots show faintly, lit dots are white, and 'r' dots are Nothing red.
Glyphs are ASCII bitmaps ('#' white, 'r' red, anything else off), centred in the field.

Usage: python3 build.py [output_dir]   (default ~/.local/share/icons/Nothing-Dots)
"""
import os
import sys
from pathlib import Path

BG, RING, OFF, ON, RED = "#0d0d0d", "#262626", "#232323", "#f2f2f2", "#d71921"
GRID, PITCH = 13, 6.2

G = {}  # glyph name -> rows

def g(name, art):
    rows = [r.strip() for r in art.strip("\n").split("\n")]
    w = max(len(r) for r in rows)
    G[name] = [r.ljust(w, ".") for r in rows]

# ---------- system / GNOME ----------
g("folder", """
####.......
#...#######
#.........#
###########
#.........#
#.........#
#.........#
#.........#
###########
""")
g("terminal", """
###########
#.........#
#.#.......#
#..#......#
#...#.....#
#..#......#
#.#..rrr..#
#.........#
###########
""")
g("settings", """
.....#.....
..#.###.#..
.#########.
..##...##..
.##.....##.
###..r..###
.##.....##.
..##...##..
.#########.
..#.###.#..
.....#.....
""")
g("calendar", """
..#.....#..
###########
#.........#
###########
#.........#
#.#.#.#.#.#
#.........#
#.#.#.r.#.#
#.........#
#.#.#.#...#
###########
""")
g("calculator", """
.#########.
#.........#
#.#######.#
#.........#
#.#..#..#.#
#.........#
#.#..#..#.#
#.........#
#.#..#..r.#
#.........#
.#########.
""")
g("clock", """
...#####...
.##.....##.
.#...#...#.
#....#....#
#....#....#
#....r##..#
#.........#
#.........#
.#.......#.
.##.....##.
...#####...
""")
g("weather", """
..r.r......
...........
r..rrr.....
..rrrrr....
..rrr####..
....#....#.
.####.....#
#.........#
.#########.
""")
g("camera", """
...###.....
###########
#.........#
#...###...#
#..#...#..#
#..#.r.#..#
#..#...#..#
#...###...#
###########
""")
g("image", """
###########
#.........#
#......rr.#
#......rr.#
#...#.....#
#..#.#....#
#.#...#.#.#
##.....#.##
###########
""")
g("maps", """
...#####...
..#.....#..
.#...r...#.
.#..rrr..#.
.#...r...#.
..#.....#..
...#...#...
....#.#....
.....#.....
""")
g("contacts", """
....###....
...#...#...
...#...#...
...#...#...
....###....
...........
..#######..
.#.......#.
#.........#
#.........#
""")
g("papers", """
######...
#....##..
#....#.#.
#....####
#.......#
#.###.#.#
#.......#
#.#####.#
#.......#
#.####..#
#########
""")
g("texteditor", """
###########
#.........#
#.#######.#
#.........#
#.#####...#
#.........#
#.######..#
#.........#
#.###r....#
#.........#
###########
""")
g("showtime", """
.##..##..##
##..##..##.
###########
#.........#
#....#....#
#....##...#
#....###..#
#....##...#
#....#....#
###########
""")
g("decibels", """
.....#.....
.....#.....
.#...#...#.
.#.#.#.#.#.
##.#.r.#.##
.#.#.#.#.#.
.#...#...#.
.....#.....
.....#.....
""")
g("sysmon", """
...#.......
..#.#......
..#.#......
.#...#.....
#....#...rr
......#..r.
......#.r..
.......r...
""")
g("disks", """
.#########.
#.........#
#..#####..#
#.#.....#.#
#.#..r..#.#
#.#.....#.#
#..#####..#
#.........#
#.......#.#
.#########.
""")
g("baobab", """
...#####...
.##.....##.
.#..#rr..#.
#..#..rr..#
#.#...r.#.#
#.#..#..#.#
#.#.....#.#
#..#...#..#
.#..###..#.
.##.....##.
...#####...
""")
g("boxes", """
.....#.....
...##.##...
.##.....##.
#.##...##.#
#...###...#
#....#....#
#....#....#
#....#....#
.##..#..##.
...##.##...
.....#.....
""")
g("characters", """
..###....
.#...#...
.#...#...
..#.#....
..##.....
.#..#..r.
#....##..
#....##..
.####..#.
""")
g("fonts", """
..#........
.#.#.......
.#.#..###..
#...#....#.
#####..####
#...#.#...#
#...#..####
""")
g("colorprofile", """
...#####...
.#####..##.
.#####...#.
######....#
######....#
######....#
######....#
######....#
.#####...#.
.#####..##.
...#####...
""")
g("connections", """
######.....
#....#.....
#....#.....
######.....
..#..######
..#..#....#
.###.#....#
.....######
.......#...
......###..
""")
g("extensions", """
....##.....
...#..#....
.###..###..
.#......#..
.#......##.
.#.......#.
.#......##.
.#......#..
.########..
""")
g("extmanager", """
....##.....
...#..#....
.###..###..
.#......#..
.#..r...##.
.#..r....#.
.#.rrr..##.
.#..r...#..
.########..
""")
g("logs", """
#.#######.
..........
#.#######.
..........
#.####....
..........
#.######..
..........
r.###.....
""")
g("help", """
...#####...
.##.....##.
.#..###..#.
#..#...#..#
#......#..#
#.....#...#
#....#....#
#.........#
.#...r...#.
.##.....##.
...#####...
""")
g("software", """
...#####...
...#...#...
.#########.
.#.......#.
.#.......#.
.#..r.r..#.
.#...r...#.
.#.......#.
.#########.
""")
g("scanner", """
.#########.
#.........#
###########
#.........#
#.rrrrrrr.#
#.........#
###########
""")
g("tour", """
...#####...
.##.....##.
.#......r#.
#......rr.#
#.....rr..#
#....#....#
#...##....#
#..##.....#
.###.....#.
.##.....##.
...#####...
""")
g("tweaks", """
..#........
###########
..#........
...........
.......#...
###########
.......#...
...........
....r......
###########
....r......
""")
g("theme", """
...#####...
.##.....##.
.#.#..#..#.
#.........#
#.r.......#
#.........#
#..#....##.
.#.....#...
.##...#....
...###.....
""")
g("parental", """
.....#.....
..#######..
.#.......#.
.#...#...#.
.#..###..#.
.#...#...#.
.#..#.#..#.
..#.....#..
...#...#...
....#.#....
.....#.....
""")
g("usb", """
...#####...
...#.#.#...
...#####...
..#######..
..#.....#..
..#.....#..
..#..r..#..
..#.....#..
..#.....#..
..#######..
""")
g("rygel", """
.#.......#.
#..#...#..#
#.#..#..#.#
#.#.#r#.#.#
#.#..#..#.#
#..#.#.#..#
.#...#...#.
.....#.....
....###....
""")

# ---------- terminals / editors / dev ----------
g("alacritty", """
.....#.....
....###....
....###....
...##.##...
...##.##...
..##...##..
..##.r.##..
.##..r..##.
.##.rrr.##.
##..rrr..##
##.......##
""")
g("kitty", """
#.........#
##.......##
#.#.....#.#
#..#####..#
#.........#
#..#...#..#
#.........#
#....r....#
.#.......#.
..#######..
""")
g("nvim", """
.....#.....
....#.#....
...#...#...
..##...##..
.#.##..#.#.
#..#.#.#..#
.#.#..##.#.
..##...##..
...#...#...
....#.#....
.....#.....
""")
g("vscode", """
.......###.
......####.
.#...##.##.
.##.##..##.
..###...##.
..##....##.
..###...##.
.##.##..##.
.#...##.##.
......####.
.......###.
""")
g("zed", """
###########
#.........#
#.#######.#
#......#..#
#.....#...#
#....#....#
#...#.....#
#..#......#
#.#######.#
#.........#
###########
""")
g("dacode", """
..##...##..
.#.......#.
.#.......#.
.#.......#.
#....r....#
.#.......#.
.#.......#.
.#.......#.
..##...##..
""")
g("btop", """
.........r.
.........r.
.....#...r.
.....#...r.
.#...#.#.r.
.#.#.#.#.r.
.#.#.#.#.r.
.#.#.#.#.r.
###########
""")
g("github", """
...#####...
.##.....##.
.#.#...#.#.
#..#####..#
#.#######.#
#.##.#.##.#
#..#####..#
#...###...#
.#.#.#.#.#.
.##.....##.
...#####...
""")

# ---------- browsers ----------
g("zen", """
...###.....
.##.....#..
.#.......#.
#.........#
#....r....#
#.........#
#.........#
#.........#
.#.......#.
.##.....##.
...#####...
""")
g("helium", """
.....#.....
....#.#....
###.#.#.###
#.##...##.#
#..#.r.#..#
#.##...##.#
###.#.#.###
....#.#....
.....#.....
""")
g("brave", """
.##.....##.
###########
#.........#
#.#.....#.#
#..#...#..#
#...#.#...#
.#...r...#.
.#.......#.
..#.....#..
...#...#...
....###....
""")
g("chromium", """
...#####...
.##.....##.
.#.##....#.
#...###...#
#..#...####
#..#.r.#..#
#..#...#..#
#...###...#
.#..#....#.
.##.#...##.
...#####...
""")
g("firefox", """
#.........#
##.......##
#.#.....#.#
#..#####..#
#.........#
.#.#...#.#.
..#.....#..
...#...#...
....#.#....
.....r.....
""")
g("librewolf", """
...#####...
.##.....##.
.#.#...#.#.
#..##.##..#
#..#####..#
#..#.#.#..#
#...###...#
#....r....#
.#.......#.
.##.....##.
...#####...
""")

# ---------- communication / web apps ----------
g("whatsapp", """
...#####...
.##.....##.
.#.......#.
#..##.....#
#..#......#
#...#.....#
#....##...#
#.........#
.#.......#.
##.....##..
#..#####...
""")
g("discord", """
.##.....##.
###########
###########
##..###..##
##..###..##
###########
####...####
.##.....##.
""")
g("gmail", """
###########
#r.......r#
#.r.....r.#
#..r...r..#
#...r.r...#
#....r....#
#.........#
#.........#
###########
""")
g("chatgpt", """
....###....
..##...##..
.#..###..#.
#..#...#..#
#.#.....#.#
#.#..r..#.#
#.#.....#.#
#..#...#..#
.#..###..#.
..##...##..
....###....
""")
g("claude", """
.....#.....
.#...#...#.
..#..#..#..
...#.#.#...
....###....
#####r#####
....###....
...#.#.#...
..#..#..#..
.#...#...#.
.....#.....
""")
g("gemini", """
.....#.....
.....#.....
....###....
....###....
..#######..
#####r#####
..#######..
....###....
....###....
.....#.....
.....#.....
""")
g("x", """
##.......#.
.##.....#..
..##...#...
...##.#....
....###....
....#.##...
...#...##..
..#.....##.
.#.......##
""")
g("youtube", """
.#########.
#.........#
#...r.....#
#...rr....#
#...rrr...#
#...rr....#
#...r.....#
#.........#
.#########.
""")
g("drive", """
.....#.....
....#.#....
....#.#....
...#...#...
...#.r.#...
..#.....#..
..#.....#..
.#.......#.
.#########.
""")
g("vercel", """
.....#.....
....###....
....###....
...#####...
...#####...
..#######..
..#######..
.#########.
.#########.
""")
g("notion", """
.#########.
#.........#
#.#.....#.#
#.##....#.#
#.#.#...#.#
#.#..#..#.#
#.#...#.#.#
#.#....##.#
#.#.....#.#
#.........#
.#########.
""")
g("neon", """
###########
##.#####.##
##..####.##
##.#.###.##
##.##.##.##
##.###.#.##
##.####..##
##.#####r##
###########
""")
g("kaggle", """
..##.......
..##.......
..##....##.
..##...##..
..##..##...
..##.##....
..####.....
..##.##....
..##..##...
..##...##..
..##....rr.
""")
g("classroom", """
###########
#.........#
#...###...#
#...###...#
#..#####..#
#.........#
###########
....r.r....
""")
g("chess", """
....##.....
...####....
..###.##...
.#######...
.####.##...
.....###...
....####...
...#####...
..#######..
.#########.
""")
g("remotedesktop", """
###########
#.........#
#..####...#
#.....##..#
#....#.#..#
#...#..r..#
#.........#
###########
....###....
..#######..
""")
g("podcasts", """
...#####...
.##.....##.
.#..###..#.
#..#...#..#
#.#..r..#.#
#.#.###.#.#
#....#....#
.....#.....
.....#.....
....###....
""")
g("localsend", """
.....#.....
....###....
...#.#.#...
.....#.....
.....#.....
...........
.....r.....
.....r.....
...r.r.r...
....rrr....
.....r.....
""")

# ---------- office / media / misc ----------
g("writer", """
######...
#....##..
#....#.#.
#....####
#.......#
#.#...#.#
#.#.#.#.#
#.#.#.#.#
#..#.#..#
#.......#
#########
""")
g("calc", """
######...
#....##..
#....#.#.
#....####
#.......#
#.#####.#
#.#.#r#.#
#.#####.#
#.#.#.#.#
#.#####.#
#########
""")
g("impress", """
######...
#....##..
#....#.#.
#....####
#.......#
#.#####.#
#.#.r.#.#
#.#####.#
#...#...#
#..###..#
#########
""")
g("mpv", """
...#####...
.##.....##.
.#.......#.
#...#.....#
#...##....#
#...#r#...#
#...##....#
#...#.....#
.#.......#.
.##.....##.
...#####...
""")
g("obs", """
...#####...
.##.....##.
.#..###..#.
#...###...#
#.........#
#.###.###.#
#.###.rrr.#
#.........#
.#.......#.
.##.....##.
...#####...
""")
g("steam", """
...#####...
.##.....##.
.#....###.#
#....#...##
#....#.r.##
#....#...##
#...#.###.#
#..#......#
.##......#.
.##.....##.
...#####...
""")
g("qbittorrent", """
.......#...
.......#...
.###...###.
#..#...#..#
#..#...#..#
#..#...#..#
.###...###.
...#.......
...r.......
""")
g("minecraft", """
###########
#.........#
#.##...##.#
#.##...##.#
#....#....#
#...###...#
#...###...#
#...#.#...#
#.........#
###########
""")

# ---------- icon name -> glyph ----------
# Names are the Icon= values the launchers ask for (plus a few common aliases).
# "nothing-*" names are for launchers that used absolute PNG paths; apply.sh repoints them.
ICONS = {
    "org.gnome.Nautilus": "folder", "system-file-manager": "folder",
    "org.gnome.Ptyxis": "terminal", "utilities-terminal": "terminal",
    "org.gnome.Settings": "settings", "preferences-system": "settings",
    "org.gnome.Calendar": "calendar",
    "org.gnome.Calculator": "calculator", "accessories-calculator": "calculator",
    "org.gnome.clocks": "clock",
    "org.gnome.Weather": "weather",
    "org.gnome.Snapshot": "camera",
    "org.gnome.Loupe": "image",
    "org.gnome.Maps": "maps",
    "org.gnome.Contacts": "contacts",
    "org.gnome.Papers": "papers",
    "org.gnome.TextEditor": "texteditor", "accessories-text-editor": "texteditor",
    "org.gnome.Showtime": "showtime",
    "org.gnome.Decibels": "decibels",
    "org.gnome.SystemMonitor": "sysmon", "utilities-system-monitor": "sysmon",
    "org.gnome.DiskUtility": "disks",
    "org.gnome.baobab": "baobab",
    "org.gnome.Boxes": "boxes",
    "org.gnome.Characters": "characters",
    "org.gnome.font-viewer": "fonts",
    "gnome-color-manager": "colorprofile",
    "org.gnome.Connections": "connections",
    "org.gnome.Extensions": "extensions",
    "com.mattjakeman.ExtensionManager": "extmanager",
    "org.gnome.Logs": "logs",
    "org.gnome.Yelp": "help", "help-browser": "help",
    "org.gnome.Software": "software",
    "org.gnome.SimpleScan": "scanner",
    "org.gnome.Tour": "tour",
    "org.gnome.tweaks": "tweaks",
    "preferences-desktop-theme": "theme",
    "org.freedesktop.MalcontentControl": "parental",
    "org.fedoraproject.MediaWriter": "usb",
    "rygel": "rygel",
    "Alacritty": "alacritty",
    "kitty": "kitty",
    "nvim": "nvim",
    "vscode": "vscode", "com.visualstudio.code": "vscode", "code": "vscode",
    "dev.zed.Zed": "zed",
    "dacode": "dacode",
    "btop": "btop",
    "chrome-mjoklplbddabcmpepnokjaffbmgbkkgg-Default": "github",
    "app.zen_browser.zen": "zen",
    "helium": "helium",
    "brave-browser": "brave",
    "chromium-browser": "chromium", "chromium": "chromium",
    "firefox": "firefox", "org.mozilla.firefox": "firefox",
    "io.gitlab.librewolf-community": "librewolf",
    "io.github.shehawey.whatsapp": "whatsapp",
    "dev.vencord.Vesktop": "discord", "discord": "discord",
    "chrome-fmgjjmmmlfnkbppncabfkddbjimcfncm-Default": "gmail",
    "chatgpt": "chatgpt", "chrome-cadlkienfkclaiaibeoongdcgmdikeeg-Default": "chatgpt",
    "claude-desktop-unofficial": "claude", "nothing-claude-web": "claude",
    "chrome-gdfaincndogidkdcdkhapmbffkckdkhn-Default": "gemini",
    "nothing-x": "x",
    "chrome-agimnkijcaahngcdmfeangaknmldooml-Default": "youtube",
    "chrome-aghbiahbpaijignceidepookljebhfak-Default": "drive",
    "nothing-vercel": "vercel",
    "nothing-notion": "notion",
    "nothing-neon": "neon",
    "nothing-kaggle": "kaggle",
    "nothing-classroom": "classroom",
    "chrome-kinpkbniadkppecjaginbegiljofpcfc-Default": "chess",
    "chrome-cmkncekebbebpfilplodngbpllndjkfo-Default": "remotedesktop",
    "chrome-fcgdpaemdckjieodcmmlpohbimhkjcob-Default": "podcasts",
    "org.localsend.localsend_app": "localsend",
    "libreoffice-writer": "writer",
    "libreoffice-calc": "calc",
    "libreoffice-impress": "impress",
    "mpv": "mpv",
    "com.obsproject.Studio": "obs",
    "com.valvesoftware.Steam": "steam", "steam": "steam",
    "org.qbittorrent.qBittorrent": "qbittorrent", "qbittorrent": "qbittorrent",
    "nothing-minecraft": "minecraft",
}


def svg(rows):
    h, w = len(rows), len(rows[0])
    r0, c0 = (GRID - h) // 2, (GRID - w) // 2
    lit = {}
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch in "#r":
                lit[(r + r0, c + c0)] = RED if ch == "r" else ON
    half = (GRID - 1) / 2
    off, on = [], []
    for r in range(GRID):
        for c in range(GRID):
            x, y = 64 + (c - half) * PITCH, 64 + (r - half) * PITCH
            if (r, c) in lit:
                on.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.55" fill="{lit[(r, c)]}"/>')
            elif (x - 64) ** 2 + (y - 64) ** 2 <= 45 ** 2:
                off.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.35"/>')
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">'
        f'<circle cx="64" cy="64" r="60" fill="{BG}" stroke="{RING}" stroke-width="1.5"/>'
        f'<g fill="{OFF}">{"".join(off)}</g>{"".join(on)}</svg>'
    )


def index_theme():
    from extras import INDEX_DIRS, CONTEXT
    # Inherit Adwaita (not MacTahoe): MacTahoe's many specific mimetype icons would
    # otherwise win over our generic ones. Small symbolic UI icons come from Adwaita.
    head = ("[Icon Theme]\nName=Nothing Dots\n"
            "Comment=Monochrome dot-matrix icons in the Nothing style\n"
            "Inherits=Adwaita,hicolor\n"
            f"Directories={','.join('scalable/' + d for d in INDEX_DIRS)}\n")
    return head + "".join(
        f"\n[scalable/{d}]\nSize=128\nMinSize=16\nMaxSize=512\nType=Scalable\n"
        f"Context={CONTEXT[d]}\n" for d in INDEX_DIRS)


# Launchers that used absolute PNG paths and have a hand-drawn glyph.
# Any other launcher with an absolute path gets an automatic "nothing-auto-*" name.
REPOINT = {
    "chrome-ajdemkepbiggbelkgicfebbjokenncei-Default.desktop": "nothing-kaggle",
    "chrome-bocepchmlplpompaekheomlocobjfjfc-Default.desktop": "nothing-neon",
    "chrome-fmpnliohjhemenmnlpbfagaolkdacoja-Default.desktop": "nothing-claude-web",
    "chrome-ghndfpepcnhknllapbniphpdikinonlm-Default.desktop": "nothing-vercel",
    "chrome-kidfiilpilhbcocjhfkpdmecfkpifleh-Default.desktop": "nothing-notion",
    "chrome-kjcjfjccmpngedeildfijeanhihmolck-Default.desktop": "nothing-classroom",
    "chrome-lodlkdfmihgonocnmddehnfgiljnadcf-Default.desktop": "nothing-x",
    "sklauncher.desktop": "nothing-minecraft",
}


def tile_svg(svg_text, label):
    return f'<figure><div>{svg_text}</div><figcaption>{label}</figcaption></figure>'


def tile(rows, label):
    return tile_svg(svg(rows), label)


def main():
    import shutil
    import auto
    import extras

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    preview_all = "--preview-auto" in sys.argv  # trace every app, to judge the fallback
    out = Path(args[0] if args else os.path.expanduser("~/.local/share/icons/Nothing-Dots"))
    backup = Path(__file__).with_name("desktop-backup")
    apps = out / "scalable" / "apps"
    shutil.rmtree(apps, ignore_errors=True)  # rebuilt from scratch so removed apps disappear
    apps.mkdir(parents=True)
    (out / "index.theme").write_text(index_theme())
    extra_counts = extras.build(out, svg)
    for name, glyph in ICONS.items():
        (apps / f"{name}.svg").write_text(svg(G[glyph]))

    index = auto.icon_index()
    auto_tiles, counts, repointed, skipped = [], {"traced": 0, "monogram": 0}, [], []
    for path, keys in auto.launchers():
        did, icon, label = path.name, keys["Icon"], keys.get("Name", path.stem)
        if icon.startswith("/"):
            source = Path(icon)
            if path.parent != auto.USER_APP_DIR:
                skipped.append(did)  # system launcher with an absolute path: can't repoint
                continue
            icon = REPOINT.get(did) or auto.auto_name(did)
            if auto.repoint(path, icon, backup):
                repointed.append(did)
        elif icon.startswith("nothing-auto-"):
            orig = (auto.parse_desktop(backup / did) or {}) if (backup / did).exists() else {}
            source = Path(orig["Icon"]) if orig.get("Icon", "").startswith("/") else None
        else:
            source = index.get(icon)
        if icon in ICONS and not preview_all:
            continue
        if not preview_all and (apps / f"{icon}.svg").exists():
            continue
        rows, kind = auto.auto_glyph(source, label, did)
        counts[kind] += 1
        auto_tiles.append(tile(rows, f"{label} · {kind}"))
        if icon not in ICONS:
            (apps / f"{icon}.svg").write_text(svg(rows))

    style = ("<!doctype html><meta charset=utf-8><title>Nothing Dots</title><style>"
             "body{background:#000;color:#bbb;font:12px monospace;margin:24px}"
             "h2{font-weight:normal;color:#888;margin:28px 0 14px}"
             "main{display:grid;grid-template-columns:repeat(auto-fill,104px);gap:18px}"
             "figure{margin:0;text-align:center}svg{width:80px;height:80px}</style>")
    Path(__file__).with_name("preview.html").write_text(
        style + "<h2>hand-drawn</h2><main>" + "".join(tile(G[k], k) for k in G) + "</main>"
        + "<h2>places · devices · status · categories · file types</h2><main>"
        + "".join(extras.preview_tiles(svg, tile_svg)) + "</main>"
        + (f"<h2>automatic</h2><main>{''.join(auto_tiles)}</main>" if auto_tiles else ""))

    print(f"{len(ICONS)} hand-drawn icons, {counts['traced']} traced, "
          f"{counts['monogram']} monogram -> {out}")
    print("other contexts:", ", ".join(f"{k} {v}" for k, v in extra_counts.items()))
    if repointed:
        print("repointed launchers:", ", ".join(repointed))
    if skipped:
        print("system launchers with absolute icon paths (left alone):", ", ".join(skipped))


if __name__ == "__main__":
    main()
