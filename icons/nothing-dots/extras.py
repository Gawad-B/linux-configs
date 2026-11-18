"""Non-app contexts of the Nothing Dots theme: places, mimetypes, devices, categories, status.

Three silhouettes, all dark with white dots and one red accent:
  folder  - dark folder with a faint dot field and an optional 9x9 emblem (places)
  page    - dark folded page with a glyph and a 3x5 dot-font extension label (mimetypes)
  circle  - the app-icon circle (devices, categories, status, trash, network)
"""
import re
import shutil
from functools import lru_cache
from pathlib import Path

ON, RED, OFF = "#f2f2f2", "#d71921", "#333333"
FILL, EDGE = "#151515", "#2e2e2e"


def art(s):
    rows = [r.strip() for r in s.strip("\n").split("\n")]
    w = max(map(len, rows))
    return [r.ljust(w, ".") for r in rows]


def dots(rows, cx, cy, pitch, r):
    h, w = len(rows), len(rows[0])
    out = []
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in "#r":
                out.append(f'<circle cx="{cx + (x - (w - 1) / 2) * pitch:.1f}" '
                           f'cy="{cy + (y - (h - 1) / 2) * pitch:.1f}" r="{r}" '
                           f'fill="{RED if ch == "r" else ON}"/>')
    return "".join(out)


def wrap(body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" '
            f'viewBox="0 0 128 128">{body}</svg>')


# ---------------------------------------------------------------- folder
FOLDER_PATH = ("M10 24Q10 16 18 16H46Q51 16 54 21L58 28H110Q118 28 118 36V104"
               "Q118 112 110 112H18Q10 112 10 104Z")


def folder(emblem=None):
    # Faint dots share the emblem's 6px grid (centred on 64,72) so lit dots sit on it.
    return wrap(
        '<defs><pattern id="d" width="6" height="6" x="61" y="69" patternUnits="userSpaceOnUse">'
        f'<circle cx="3" cy="3" r="1.4" fill="{OFF}"/></pattern></defs>'
        f'<path d="{FOLDER_PATH}" fill="{FILL}" stroke="{EDGE}" stroke-width="1.5"/>'
        '<rect x="16" y="36" width="96" height="70" rx="4" fill="url(#d)"/>'
        f'<circle cx="22" cy="22" r="2.6" fill="{RED}"/>'
        + (dots(emblem, 64, 72, 6, 2.5) if emblem else ""))


# ---------------------------------------------------------------- page
PAGE_PATH = "M28 8H82L104 30V114Q104 120 98 120H34Q28 120 28 114V14Q28 8 34 8Z"
FOLD_PATH = "M82 8V24Q82 30 88 30H104"

FONT3 = {
    "A": ".#. #.# ### #.# #.#", "B": "##. #.# ##. #.# ##.", "C": ".## #.. #.. #.. .##",
    "D": "##. #.# #.# #.# ##.", "E": "### #.. ##. #.. ###", "F": "### #.. ##. #.. #..",
    "G": ".## #.. #.# #.# .##", "H": "#.# #.# ### #.# #.#", "I": "### .#. .#. .#. ###",
    "J": "..# ..# ..# #.# .#.", "K": "#.# #.# ##. #.# #.#", "L": "#.. #.. #.. #.. ###",
    "M": "#.# ### ### #.# #.#", "N": "##. #.# #.# #.# #.#", "O": ".#. #.# #.# #.# .#.",
    "P": "##. #.# ##. #.. #..", "Q": ".#. #.# #.# ##. .##", "R": "##. #.# ##. #.# #.#",
    "S": ".## #.. .#. ..# ##.", "T": "### .#. .#. .#. .#.", "U": "#.# #.# #.# #.# ###",
    "V": "#.# #.# #.# #.# .#.", "W": "#.# #.# ### ### #.#", "X": "#.# #.# .#. #.# #.#",
    "Y": "#.# #.# .#. .#. .#.", "Z": "### ..# .#. #.. ###", "0": "### #.# #.# #.# ###",
    "1": ".#. ##. .#. .#. ###", "2": "##. ..# .#. #.. ###", "3": "##. ..# .#. ..# ##.",
    "4": "#.# #.# ### ..# ..#", "5": "### #.. ##. ..# ##.", "6": ".## #.. ### #.# ###",
    "7": "### ..# .#. .#. .#.", "8": "### #.# ### #.# ###", "9": "### #.# ### ..# ##.",
    "+": "... .#. ### .#. ...", "#": "#.# ### #.# ### #.#", "-": "... ... ### ... ...",
}


def label_rows(text):
    chars = [c for c in text.upper() if c in FONT3][:4]
    if not chars:
        return None
    rows = [""] * 5
    for i, c in enumerate(chars):
        for y, part in enumerate(FONT3[c].split()):
            rows[y] += ("." if i else "") + part
    return rows


def page(glyph, label=None):
    lab = label_rows(label) if label else None
    gy = 52 if lab else 64
    return wrap(
        f'<path d="{PAGE_PATH}" fill="{FILL}" stroke="{EDGE}" stroke-width="1.5"/>'
        f'<path d="{FOLD_PATH}" fill="none" stroke="{EDGE}" stroke-width="1.5"/>'
        f'<circle cx="38" cy="18" r="2.4" fill="{RED}"/>'
        + dots(glyph, 66, gy, 5.6 if len(glyph[0]) > 9 else 6, 2.3)
        + (dots(lab, 66, 99, 4.4, 1.75) if lab else ""))


# ---------------------------------------------------------------- glyphs
E = {}  # 9x9-ish emblems / page glyphs
E["home"] = art("""
....#....
...###...
..##.##..
.##...##.
##.....##
.#.....#.
.#..r..#.
.#..r..#.
.#######.
""")
E["documents"] = art("""
#######..
#.....##.
#.###..#.
#......#.
#.####.#.
#......#.
#.###..#.
#......#.
########.
""")
E["download"] = art("""
....#....
....#....
....#....
.#..#..#.
..#.#.#..
...###...
....#....
.........
rrrrrrrrr
""")
E["music"] = art("""
...######
...#....#
...######
...#....#
...#....#
.###..###
####.####
.##...##.
""")
E["pictures"] = art("""
#########
#.......#
#.....r.#
#.......#
#..#....#
#.#.#.#.#
##...#.##
#########
""")
E["videos"] = art("""
#########
#.......#
#..r....#
#..rr...#
#..rrr..#
#..rr...#
#..r....#
#.......#
#########
""")
E["templates"] = art("""
#.#.#.#.#
.........
#.......#
.........
#...r...#
.........
#.......#
.........
#.#.#.#.#
""")
E["share"] = art("""
......###
......###
....##...
..##.....
rrr......
..##.....
....##...
......###
......###
""")
E["globe"] = art("""
..#####..
.#..#..#.
#..#.#..#
#########
#..#.#..#
#########
#..#.#..#
.#..#..#.
..#####..
""")
E["recent"] = art("""
..#####..
.#.....#.
#...#...#
#...#...#
#...r##.#
#.......#
#.......#
.#.....#.
..#####..
""")
E["desktop"] = art("""
#########
#.......#
#.......#
#.......#
#.......#
#########
....#....
...###...
""")
E["search"] = art("""
.####....
#....#...
#....#...
#....#...
.####....
.....#...
......#..
.......#.
........r
""")
E["projects"] = art("""
......#....
......#....
..#...#.#..
.#...#...#.
#....#....#
.#...#...#.
..#.#...#..
....#......
....#......
""")
E["bookmark"] = art("""
#######
#.....#
#.....#
#.....#
#..r..#
#.....#
#.#.#.#
##...##
#.....#
""")
E["drop"] = art("""
....#....
....#....
..#.#.#..
...###...
....#....
.........
#.......#
#.......#
#########
""")
# page glyphs
E["text"] = art("""
#######..
.........
#########
.........
######...
.........
########.
.........
####.....
""")
E["code"] = E["projects"]
E["script"] = art("""
#########
#.......#
#.#.....#
#..#....#
#.#..rr.#
#.......#
#########
""")
E["image"] = art("""
#########
#.......#
#....rr.#
#....rr.#
#..#....#
#.#.#...#
##...#.##
#########
""")
E["audio"] = E["music"]
E["video"] = E["videos"]
E["archive"] = art("""
...#.#...
....#....
...#.#...
....#....
...#.#...
...###...
...#r#...
...###...
""")
E["doc"] = art("""
#########
.........
#########
.........
#########
.........
#####....
""")
E["sheet"] = art("""
rrrrrrrrr
#...#...#
#########
#...#...#
#########
#...#...#
#########
""")
E["slides"] = art("""
#########
#.......#
#.....r.#
#...#.r.#
#.#.#.r.#
#.......#
#########
....#....
...#.#...
""")
E["pdf"] = art("""
rrrrrrrrr
.........
#########
.........
#########
.........
#####....
""")
E["drawing"] = art("""
.......##
......###
.....###.
....###..
...###...
..r##....
.rr#.....
rrr......
""")
E["binary"] = art("""
.#...##..
##..#..#.
.#..#..#.
.#..#..#.
###..##..
""")
E["package"] = art("""
....#....
..##.##..
##.....##
#.##.##.#
#...#...#
#...#...#
#...r...#
.##.#.##.
...###...
""")
E["disc"] = art("""
..#####..
.#.....#.
#.......#
#...#...#
#..#r#..#
#...#...#
#.......#
.#.....#.
..#####..
""")
E["data"] = art("""
.#######.
#.......#
.#######.
#.......#
.#######.
#.......#
.###r###.
""")
E["font"] = art("""
..#........
.#.#.......
.#.#..###..
#...#....#.
#####..####
#...#.#...#
#...#..####
""")
E["calendar"] = art("""
.#.....#.
#########
#.......#
#########
#.#.#.#.#
#.......#
#.#.r.#.#
#########
""")
E["contact"] = art("""
...###...
..#...#..
..#...#..
...###...
.........
.#######.
#.......#
#.......#
""")
E["book"] = art("""
##.....##
#.##.##.#
#...#...#
#...#...#
#...#...#
#...#...#
##.###.##
...r.r...
""")
E["mail"] = art("""
#########
#r.....r#
#.r...r.#
#..r.r..#
#...r...#
#.......#
#########
""")
E["key"] = art("""
.###.....
#...#....
#.r.#####
#...#.#.#
.###..#.#
""")
E["app"] = art("""
....#....
..#####..
.##...##.
.#.....#.
##..r..##
.#.....#.
.##...##.
..#####..
....#....
""")
E["file"] = art("""
.........
.........
.........
.#..#..r.
""")
E["model"] = E["package"]
E["web"] = E["globe"]
E["addon"] = art("""
...##....
..#..#...
###..###.
#......#.
#..r...##
#......#.
#......##
#......#.
########.
""")
E["torrent"] = E["download"]
E["cert"] = art("""
#########
#.......#
#.#####.#
#.......#
#.###...#
#.....r.#
#....rrr#
#########
""")
E["firmware"] = art("""
.#.#.#.#.
#########
##.....##
.#.....#.
##..r..##
.#.....#.
##.....##
#########
.#.#.#.#.
""")

# 11x11 circle glyphs for devices / status / categories / special places
C = {}
C["trash"] = art("""
....###....
###########
.#.......#.
.#.#.#.#.#.
.#.#.#.#.#.
.#.#.#.#.#.
.#.#.#.#.#.
.#.#.#.#.#.
.#.......#.
..#######..
""")
C["trash-full"] = art("""
....###....
###########
.#.......#.
.#.r.r.r.#.
.#.r.r.r.#.
.#.r.r.r.#.
.#.r.r.r.#.
.#.r.r.r.#.
.#.......#.
..#######..
""")
C["server"] = art("""
###########
#.......r.#
###########
#.......#.#
###########
#.......#.#
###########
.....#.....
...#####...
""")
C["workgroup"] = art("""
....###....
....#.#....
....###....
.....#.....
.#########.
.#...#...#.
###.###.###
#.#.#.#.#.#
###.###.###
""")
C["harddisk"] = art("""
###########
#.........#
#..#####..#
#.#.....#.#
#.#..r..#.#
#.#.....#.#
#..#####..#
#.........#
###########
""")
C["ssd"] = art("""
.#.#.#.#.#.
###########
#.........#
#.#######.#
#.#.....#.#
#.#..r..#.#
#.#######.#
#.........#
###########
.#.#.#.#.#.
""")
C["multidisk"] = art("""
###########
#.......r.#
###########
...........
###########
#.......#.#
###########
...........
###########
#.......#.#
###########
""")
C["optical"] = art("""
...#####...
.##.....##.
.#.......#.
#....#....#
#...#.#...#
#..#.r.#..#
#...#.#...#
#....#....#
.#.......#.
.##.....##.
...#####...
""")
C["usb"] = art("""
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
C["flash"] = art("""
...######..
..#.#.#.#..
.#.#.#.#.#.
#.........#
#.........#
#.........#
#....r....#
#.........#
###########
""")
C["computer"] = art("""
###########
#.........#
#.........#
#.........#
#....r....#
#.........#
###########
....#.#....
..#######..
""")
C["laptop"] = art("""
..#######..
..#.....#..
..#.....#..
..#..r..#..
..#.....#..
..#######..
.#########.
###########
""")
C["phone"] = art("""
..#######..
..#.....#..
..#.....#..
..#.....#..
..#.....#..
..#.....#..
..#.....#..
..#..r..#..
..#######..
""")
C["camera"] = art("""
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
C["webcam"] = art("""
...#####...
..#.....#..
.#..###..#.
.#.#.r.#.#.
.#..###..#.
..#.....#..
...#####...
....#.#....
..#######..
""")
C["printer"] = art("""
...#####...
...#...#...
###########
#.........#
#.......r.#
#.........#
###########
..#.....#..
..#######..
""")
C["scanner"] = art("""
.#########.
#.........#
###########
#.........#
#.rrrrrrr.#
#.........#
###########
""")
C["headphones"] = art("""
...#####...
.##.....##.
.#.......#.
#.........#
#.........#
###.....###
###.....###
###.....###
.#.......#.
""")
C["headset"] = art("""
...#####...
.##.....##.
.#.......#.
#.........#
###.....###
###.....###
###.....###
.#......#..
..##..rr...
""")
C["speaker"] = art("""
.#######.
#.......#
#...#...#
#.......#
#..###..#
#.#.r.#.#
#..###..#
#.......#
.#######.
""")
C["microphone"] = art("""
....###....
...#...#...
...#...#...
...#.r.#...
...#...#...
.#.#...#.#.
.#..###..#.
..#.....#..
....###....
.....#.....
...#####...
""")
C["keyboard"] = art("""
###########
#.........#
#.#.#.#.#.#
#.........#
#.#.#.#.#.#
#.........#
#..rrrrr..#
###########
""")
C["mouse"] = art("""
...#####...
..#..#..#..
.#...#...#.
.#...r...#.
.#########.
.#.......#.
.#.......#.
..#.....#..
...#####...
""")
C["gamepad"] = art("""
.#########.
#.........#
#.#.....r.#
###...r...#
#.#.....r.#
#.........#
#...###...#
.###...###.
""")
C["tablet"] = art("""
#########
#.......#
#.......#
#.......#
#.......#
#.......#
#.......#
#...r...#
#########
""")
C["display"] = C["computer"]
C["ereader"] = art("""
.#######.
#.......#
#.#####.#
#.......#
#.#####.#
#.......#
#.###...#
#.......#
#...r...#
.#######.
""")
C["network-wired"] = art("""
...#####...
...#...#...
...#...#...
...##r##...
.....#.....
.....#.....
#####.#####
#...#.#...#
#.#.#.#.#.#
#####.#####
""")
C["wireless"] = art("""
.#########.
#.........#
...#####...
..#.....#..
....###....
...#...#...
...........
.....r.....
""")
C["battery"] = art("""
....###....
..#######..
..#.....#..
..#.....#..
..#.....#..
..#rrrrr#..
..#rrrrr#..
..#rrrrr#..
..#######..
""")
C["chip"] = art("""
.#.#.#.#.#.
###########
.#.......#.
##.#####.##
.#.#.r.#.#.
##.#####.##
.#.......#.
###########
.#.#.#.#.#.
""")
C["modem"] = art("""
.#.......#.
#..#...#..#
#.#..#..#.#
#.#.#r#.#.#
#.#..#..#.#
#..#.#.#..#
.#...#...#.
.....#.....
...#####...
""")
C["info"] = art("""
.....r.....
...........
....##.....
.....#.....
.....#.....
.....#.....
.....#.....
....###....
""")
C["warning"] = art("""
.....#.....
....#.#....
....#.#....
...#.r.#...
...#.r.#...
..#..r..#..
..#.....#..
.#...r...#.
.#.......#.
###########
""")
C["error"] = art("""
.rr.....rr.
..rr...rr..
...rr.rr...
....rrr....
...rr.rr...
..rr...rr..
.rr.....rr.
""")
C["question"] = art("""
...#####...
..#.....#..
.......#...
......#....
.....#.....
.....#.....
...........
.....r.....
""")
C["password"] = art("""
.###.......
#...#......
#.r.#######
#...#.#.#.#
.###..#.#.#
""")
C["avatar"] = art("""
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
C["missing"] = art("""
#.#.#.#.#.#
...........
#.........#
.....r.....
#...r.r...#
.....r.....
#.........#
...........
#.#.#.#.#.#
""")
C["loading"] = art("""
.#...#...r.
""")
C["start"] = art("""
...#####...
.##.....##.
.#.......#.
#.........#
#.........#
#....r....#
#.........#
#.........#
.#.......#.
.##.....##.
...#####...
""")
# categories
C["tools"] = art("""
.......##..
......#..#.
......#.##.
.....#.#...
....#.#....
...#.#.....
..#.#......
.#r#.......
.rr........
""")
C["dev"] = E["projects"]
C["games"] = C["gamepad"]
C["graphics"] = art("""
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
C["internet"] = art("""
...#####...
..#..#..#..
.#..#.#..#.
###########
#...#.#...#
#...#r#...#
###########
.#..#.#..#.
..#..#..#..
...#####...
""")
C["multimedia"] = art("""
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
C["office"] = art("""
...#####...
...#...#...
###########
#.........#
#.........#
#####r#####
#.........#
#.........#
###########
""")
C["other"] = art("""
#...#...#
.........
.........
.........
#...r...#
.........
.........
.........
#...#...#
""")
C["science"] = art("""
...#####...
....#.#....
....#.#....
....#.#....
...#...#...
..#.....#..
.#.rrrrr.#.
#.rrrrrrr.#
###########
""")
C["system"] = art("""
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
C["prefs"] = art("""
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
C["help"] = art("""
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

PLACES = {  # name -> folder emblem key (None = plain folder) or ("circle", glyph)
    "folder": None, "inode-directory": None, "folder-open": None, "folder-visiting": None,
    "folder-drag-accept": "drop", "folder-documents": "documents", "folder-download": "download",
    "folder-music": "music", "folder-pictures": "pictures", "folder-videos": "videos",
    "folder-templates": "templates", "folder-publicshare": "share", "folder-remote": "globe",
    "folder-recent": "recent", "folder-saved-search": "search", "folder-projects": "projects",
    "user-home": "home", "user-desktop": "desktop", "user-bookmarks": "bookmark",
    "user-trash": ("circle", "trash"), "user-trash-full": ("circle", "trash-full"),
    "network-server": ("circle", "server"), "network-workgroup": ("circle", "workgroup"),
    "start-here": ("circle", "start"), "distributor-logo": ("circle", "start"),
}
DEVICES = {
    "drive-harddisk": "harddisk", "drive-harddisk-solidstate": "ssd", "drive-harddisk-system": "harddisk",
    "drive-harddisk-usb": "usb", "drive-multidisk": "multidisk", "drive-optical": "optical",
    "drive-removable-media": "usb", "drive-removable-media-usb": "usb", "media-removable": "usb",
    "media-optical": "optical", "media-optical-cd": "optical", "media-optical-dvd": "optical",
    "media-flash": "flash", "media-floppy": "flash", "media-memory": "chip", "media-zip": "usb",
    "computer": "computer", "computer-laptop": "laptop", "video-display": "display",
    "phone": "phone", "ebook-reader": "ereader", "multimedia-player": "phone",
    "camera-photo": "camera", "camera-video": "camera", "camera-web": "webcam",
    "printer": "printer", "printer-network": "printer", "scanner": "scanner",
    "audio-headphones": "headphones", "audio-headset": "headset", "audio-speakers": "speaker",
    "audio-card": "chip", "audio-input-microphone": "microphone", "microphone": "microphone",
    "input-keyboard": "keyboard", "input-mouse": "mouse", "input-gaming": "gamepad",
    "input-tablet": "tablet", "network-wired": "network-wired", "network-wireless": "wireless",
    "battery": "battery", "modem": "modem", "pda": "phone", "bluetooth": "wireless",
}
STATUS = {
    "dialog-information": "info", "dialog-warning": "warning", "dialog-error": "error",
    "dialog-question": "question", "dialog-password": "password", "avatar-default": "avatar",
    "image-missing": "missing", "image-loading": "loading", "user-trash-full": "trash-full",
    "folder-open": None, "security-high": "password",
}
CATEGORIES = {
    "applications-accessories": "tools", "applications-utilities": "tools",
    "applications-development": "dev", "applications-engineering": "science",
    "applications-games": "games", "applications-graphics": "graphics",
    "applications-internet": "internet", "applications-multimedia": "multimedia",
    "applications-office": "office", "applications-other": "other",
    "applications-science": "science", "applications-system": "system",
    "preferences-desktop": "prefs", "preferences-system": "system",
    "preferences-other": "other", "system-help": "help", "help-browser": "help",
}

# ---------------------------------------------------------------- mimetypes
GENERIC = {  # generic-icon name -> (glyph, label)
    "text-x-generic": ("text", "TXT"), "text-x-generic-template": ("templates", "TPL"),
    "text-x-script": ("script", "SH"), "text-html": ("web", "HTML"), "text-x-preview": ("text", None),
    "application-x-executable": ("binary", "BIN"), "application-x-sharedlib": ("binary", "LIB"),
    "application-x-generic": ("file", None), "application-octet-stream": ("file", None),
    "application-x-addon": ("addon", "EXT"), "application-x-firmware": ("firmware", "FW"),
    "application-certificate": ("cert", "CRT"), "package-x-generic": ("package", "PKG"),
    "x-package-repository": ("package", "REPO"), "image-x-generic": ("image", "IMG"),
    "audio-x-generic": ("audio", "AUD"), "video-x-generic": ("video", "VID"),
    "font-x-generic": ("font", "FONT"), "x-office-document": ("doc", "DOC"),
    "x-office-document-template": ("doc", "DOTX"), "x-office-spreadsheet": ("sheet", "XLS"),
    "x-office-spreadsheet-template": ("sheet", "XLT"), "x-office-presentation": ("slides", "PPT"),
    "x-office-presentation-template": ("slides", "POT"), "x-office-drawing": ("drawing", "DRAW"),
    "x-office-calendar": ("calendar", "ICS"), "x-office-addressbook": ("contact", "VCF"),
    "x-office-address-book": ("contact", "VCF"), "model": ("model", "3D"),
    "media-optical": ("disc", "ISO"), "emblem-mail": ("mail", "EML"), "inode-symlink": ("share", "LINK"),
    "text-x-generic-symlink": ("share", "LINK"), "emblem-symbolic-link": ("share", "LINK"),
}
COMMON_EXT = set("""
py pyw js mjs cjs ts tsx jsx json jsonc yaml yml toml xml html htm css scss sass less md markdown
txt log csv tsv sql db sqlite c h cpp cxx cc hpp rs go java kt kts swift rb php pl lua sh bash zsh
fish ps1 bat r jl dart scala hs ex exs cs fs vue svelte ipynb tex bib asm s pdf doc docx odt rtf xls
xlsx ods ppt pptx odp odg epub mobi djvu png jpg jpeg gif webp svg bmp ico tif tiff heic avif psd xcf
cr2 nef dng mp3 wav flac ogg oga opus m4a aac mid midi mp4 mkv webm avi mov wmv flv m4v 3gp zip tar
gz tgz bz2 xz zst 7z rar lz lzma cab iso img dmg qcow2 rpm deb apk flatpak flatpakref appimage exe
msi dll so jar war class wasm ttf otf woff woff2 ics vcf eml mbox torrent pem key crt cer gpg asc
desktop service conf ini env patch diff dockerfile makefile cmake gradle lock blend obj stl gltf glb
""".split())

FAMILY_RULES = [  # (keywords in mime name, glyph) - first match wins
    (("pdf",), "pdf"),
    (("spreadsheet", "excel", "csv", "tab-separated", ".sheet", "calc"), "sheet"),
    (("presentation", "powerpoint", "slide", "impress"), "slides"),
    (("drawing", "graphics", "draw"), "drawing"),
    (("wordprocessing", "msword", "opendocument.text", "rtf", "abiword", "writer", "-text",
      "office-document", "oasis-master"), "doc"),
    (("epub", "mobipocket", "ebook", "djvu", "comicbook", "fictionbook"), "book"),
    (("rpm", "debian", "flatpak", "appimage", "snap", "android.package", "x-msi", "java-archive",
      "web-app"), "package"),
    (("iso9660", "efi.iso", "cd-image", "disk-image", "raw-disk", "apple-diskimage", "qemu",
      "vmdk"), "disc"),
    (("zip", "tar", "compress", "7z", "rar", "gzip", "bzip", "xz", "zstd", "lzma", "lzip", "lzop",
      "archive", "cpio", "arj", "cab", "lha", "ace"), "archive"),
    (("certificate", "x509", "pkcs", "pgp", "pem", "x-ssh-key"), "cert"),
    (("executable", "sharedlib", "x-object", "x-core", "elf", "dosexec", "msdownload", "x-ms-",
      "wasm", "java-vm", "x-firmware"), "binary"),
    (("calendar", "icalendar"), "calendar"),
    (("vcard", "contact"), "contact"),
    (("epub", "mobipocket", "ebook", "djvu", "comicbook", "fictionbook"), "book"),
    (("message/", "mbox", "rfc822", "email"), "mail"),
    (("x-desktop", "desktop-entry"), "app"),
    (("font",), "font"),
    (("torrent",), "torrent"),
    (("ipynb", "jupyter"), "code"),
    (("json", "yaml", "toml", "sql", "sqlite", "database", "x-xml", "/xml", "xml-dtd", "x-ini",
      "netcdf", "hdf"), "data"),
    (("html", "xhtml", "css"), "web"),
    (("shellscript", "x-sh", "x-csh", "x-fish", "powershell", "x-bat", "makefile",
      "dockerfile"), "script"),
    (("model/", "gltf", "x-blender", "stl", "wavefront"), "model"),
    (("image/",), "image"),
    (("audio/",), "audio"),
    (("video/",), "video"),
    (("src", "python", "java", "javascript", "typescript", "rust", "x-go", "x-c", "x-c++", "x-php",
      "x-ruby", "x-perl", "x-lua", "kotlin", "swift", "csharp", "haskell", "scala", "x-dart",
      "x-elixir", "x-erlang", "x-julia", "x-r", "x-asm", "x-vala", "x-zig", "x-nim", "x-ocaml",
      "x-fortran", "x-pascal", "vue", "svelte", "x-tex", "x-patch", "x-diff", "x-cmake"), "code"),
    (("text/",), "text"),
    (("inode/",), "file"),
]


def family(mime):
    for keys, glyph in FAMILY_RULES:
        if any(k in mime for k in keys):
            return glyph
    return "file"


@lru_cache(maxsize=1)
def mime_db():
    """(mime -> best extension by glob weight, mime type list)."""
    root = Path("/usr/share/mime")
    ext = {}
    globs = root / "globs2"
    if globs.exists():
        for line in globs.read_text(errors="replace").splitlines():
            parts = line.split(":")
            if line.startswith("#") or len(parts) < 3:
                continue
            weight, mime, pat = int(parts[0]), parts[1], parts[2]
            m = re.fullmatch(r"\*\.([A-Za-z0-9+]+)", pat)
            if m:
                ext.setdefault(mime, []).append((-weight, m.group(1).lower()))
    tpath = root / "types"
    types = tpath.read_text().split() if tpath.exists() else []
    best = {}
    for mime, cands in ext.items():
        names = [e for _, e in sorted(cands, key=lambda c: c[0])]  # stable: file order per weight
        best[mime] = next((e for e in names if e in COMMON_EXT), names[0])
    return best, types


def mime_icons():
    """icon name -> svg for generic names, common extensions, and hicolor-shipped names."""
    exts, types = mime_db()
    out = {name: page(E[glyph], label) for name, (glyph, label) in GENERIC.items()}
    for mime in types:
        e = exts.get(mime)
        if e and e in COMMON_EXT:
            short = {"appimage": "APP", "flatpakref": "FPAK", "markdown": "MD",
                     "dockerfile": "DOCK", "makefile": "MAKE"}.get(e, e[:4])
            out[mime.replace("/", "-")] = page(E[family(mime)], short)
    # Names other installed themes ship (e.g. LibreOffice's) would otherwise win over ours.
    for base in (Path("/usr/share/icons/hicolor"), Path.home() / ".local/share/icons/hicolor"):
        for p in base.glob("*/mimetypes/*"):
            name = p.stem
            if name in out or name.endswith("-symbolic"):
                continue
            oasis = "oasis" in name
            label = next((lab for key, lab in (
                ("spreadsheet", "ODS" if oasis else "XLS"), ("presentation", "ODP" if oasis else "PPT"),
                ("drawing", "ODG"), ("database", "ODB"), ("formula", "ODF"),
                ("text", "ODT" if oasis else "DOC"), ("web", "HTML"), ("extension", "OXT"))
                if key in name), None)
            out[name] = page(E[family(name)] if family(name) != "file" else E["doc"], label)
    out["inode-directory"] = folder()
    return out


INDEX_DIRS = ["apps", "places", "mimetypes", "devices", "categories", "status"]
CONTEXT = {"apps": "Applications", "places": "Places", "mimetypes": "MimeTypes",
           "devices": "Devices", "categories": "Categories", "status": "Status"}


def build(out, circle_svg):
    """Write every non-app context into the theme at `out`. Returns {context: count}."""
    root = Path(out) / "scalable"
    counts = {}

    def write(ctx, files):
        d = root / ctx
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
        for name, data in files.items():
            (d / f"{name}.svg").write_text(data)
        counts[ctx] = len(files)

    write("places", {name: circle_svg(C[spec[1]]) if isinstance(spec, tuple)
                     else folder(E[spec] if spec else None) for name, spec in PLACES.items()})
    write("devices", {n: circle_svg(C[g]) for n, g in DEVICES.items()})
    write("categories", {n: circle_svg(C[g]) for n, g in CATEGORIES.items()})
    write("status", {n: folder() if g is None else circle_svg(C[g]) for n, g in STATUS.items()})
    write("mimetypes", mime_icons())
    return counts


def preview_tiles(circle_svg, tile):
    """One tile per distinct design, for the preview page. tile(svg_text, label) -> html."""
    tiles = [tile(circle_svg(C[s[1]]) if isinstance(s, tuple) else folder(E[s] if s else None), n)
             for n, s in PLACES.items()]
    seen = set()
    for group in (DEVICES, STATUS, CATEGORIES):
        for name, g in group.items():
            if g and g not in seen:
                seen.add(g)
                tiles.append(tile(circle_svg(C[g]), name))
    tiles += [tile(page(E[g], lab), n) for n, (g, lab) in GENERIC.items()]
    exts = mime_db()[0]
    for sample in ("text/x-python", "application/pdf", "application/zip", "image/png",
                   "audio/mpeg", "video/mp4", "application/json", "text/x-rust",
                   "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                   "application/vnd.ms-excel", "application/x-iso9660-image", "application/x-rpm"):
        tiles.append(tile(page(E[family(sample)], exts.get(sample, "")[:4]),
                          sample.split("/")[1][:20]))
    return tiles
