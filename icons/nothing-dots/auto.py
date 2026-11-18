"""Automatic Nothing Dots glyphs for apps that have no hand-drawn glyph.

For each visible launcher, the app's real icon is found, rendered small, and traced onto
the dot grid: pixels that stand out from the icon's background become lit dots. If the
trace is a blob or nearly empty, a dot-matrix monogram of the app name is used instead.
"""
import os
import re
import subprocess
from io import BytesIO
from pathlib import Path

from PIL import Image

HOME = Path.home()
APP_DIRS = [
    HOME / ".local/share/applications",
    Path("/var/lib/flatpak/exports/share/applications"),
    HOME / ".local/share/flatpak/exports/share/applications",
    Path("/usr/local/share/applications"),
    Path("/usr/share/applications"),
]
USER_APP_DIR = APP_DIRS[0]
ICON_BASES = [
    HOME / ".local/share/icons", HOME / ".icons",
    HOME / ".local/share/flatpak/exports/share/icons",
    Path("/var/lib/flatpak/exports/share/icons"), Path("/usr/share/icons"),
]
# Original app art first (hicolor), then the previous theme as a fallback source.
SOURCE_THEMES = ["hicolor", "MacTahoe-dark", "MacTahoe", "Adwaita"]

FONT = {  # 5x7 dot font for monograms
    "A": "01110 10001 10001 11111 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01111 10000 10000 10000 10000 10000 01111", "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111", "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01111 10000 10000 10011 10001 10001 01111", "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "11111 00100 00100 00100 00100 00100 11111", "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001", "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001", "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110", "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101", "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110", "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110", "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010", "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100", "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10011 10101 10101 11001 10001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11110 00001 00001 01110 00001 00001 11110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
}
RING = [
    "...#####...", ".##.....##.", ".#.......#.", "#.........#", "#.........#", "#.........#",
    "#.........#", "#.........#", ".#.......#.", ".##.....##.", "...#####...",
]


def monogram(name):
    ch = next((c for c in name.upper() if c in FONT), None)
    rows = [list(r) for r in RING]
    rows[9][5] = "r"  # red accent at the bottom of the ring
    if ch:
        for y, bits in enumerate(FONT[ch].split()):
            for x, b in enumerate(bits):
                if b == "1":
                    rows[y + 2][x + 3] = "#"
    return ["".join(r) for r in rows]


def parse_desktop(path):
    """Return the [Desktop Entry] keys we care about, or None if the entry is hidden."""
    keys, in_entry = {}, False
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("["):
            in_entry = line == "[Desktop Entry]"
            continue
        if in_entry and "=" in line:
            k, v = line.split("=", 1)
            keys.setdefault(k.strip(), v.strip())
    if keys.get("Type", "Application") != "Application":
        return None
    if keys.get("NoDisplay", "").lower() == "true" or keys.get("Hidden", "").lower() == "true":
        return None
    only = keys.get("OnlyShowIn")
    if only and "GNOME" not in only.split(";"):
        return None
    if "GNOME" in keys.get("NotShowIn", "").split(";"):
        return None
    return keys if keys.get("Icon") else None


def launchers():
    """Visible launchers, first match per desktop id wins (same precedence as GNOME)."""
    seen = {}
    for d in APP_DIRS:
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.desktop")):
            if p.name in seen:
                continue
            seen[p.name] = None  # shadowed ids stay shadowed even when hidden
            keys = parse_desktop(p)
            if keys:
                seen[p.name] = (p, keys)
    return [v for v in seen.values() if v]


def _size_rank(path):
    s = str(path)
    if s.endswith((".svg", ".svgz")) and "symbolic" not in s:
        return 10_000
    m = re.search(r"/(\d+)x\d+(@\d)?/", s)
    return int(m.group(1)) if m else 1


def icon_index():
    """stem -> best source file, preferring earlier themes, then SVG, then larger PNG."""
    index = {}
    for theme in SOURCE_THEMES:
        found = {}
        for base in ICON_BASES:
            root = base / theme
            if not root.is_dir():
                continue
            for dirpath, _dirs, files in os.walk(root, followlinks=True):
                if "symbolic" in dirpath:
                    continue
                for f in files:
                    stem, ext = os.path.splitext(f)
                    if ext.lower() not in (".svg", ".svgz", ".png") or stem.endswith("-symbolic"):
                        continue
                    p = Path(dirpath, f)
                    if stem not in found or _size_rank(p) > _size_rank(found[stem]):
                        found[stem] = p
        for stem, p in found.items():
            index.setdefault(stem, p)
    pix = Path("/usr/share/pixmaps")
    if pix.is_dir():
        for p in pix.iterdir():
            if p.suffix.lower() in (".svg", ".png", ".xpm"):
                index.setdefault(p.stem, p)
    return index


def load(path, px=64):
    try:
        if str(path).lower().endswith((".svg", ".svgz", ".xpm")):
            png = subprocess.run(
                ["magick", "-background", "none", "-density", "300", str(path),
                 "-resize", f"{px * 2}x{px * 2}", "png:-"],
                capture_output=True, timeout=20, check=True).stdout
            img = Image.open(BytesIO(png))
        else:
            img = Image.open(path)
        return img.convert("RGBA")
    except Exception:
        return None


def trace(img, cells=11):
    """Turn an icon image into an 11x11 glyph, or None if the result isn't usable."""
    bbox = img.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
    if not bbox:
        return None
    img = img.crop(bbox)
    side = max(img.size)
    sq = Image.new("RGBA", (side, side))
    sq.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    n = cells * 4
    small = sq.resize((n, n), Image.LANCZOS)
    px = list(small.get_flattened_data() if hasattr(small, "get_flattened_data") else small.getdata())

    opaque = [p for p in px if p[3] >= 128]
    if not opaque:
        return None
    if len(opaque) / len(px) < 0.6:
        # Logo on a transparent background: the shape itself is the glyph.
        lit = [p[3] >= 128 for p in px]
    else:
        # Logo on a filled tile: lit = pixels far from the tile's dominant colour.
        buckets = {}
        for r, g, b, _ in opaque:
            k = (r >> 4, g >> 4, b >> 4)
            buckets[k] = buckets.get(k, 0) + 1
        br, bg, bb = (c * 16 + 8 for c in max(buckets, key=buckets.get))
        lit = [p[3] >= 128 and (p[0] - br) ** 2 + (p[1] - bg) ** 2 + (p[2] - bb) ** 2 > 90 ** 2
               for p in px]

    grid = [[sum(lit[(cy * 4 + y) * n + cx * 4 + x] for y in range(4) for x in range(4)) >= 7
             for cx in range(cells)] for cy in range(cells)]
    return ["".join("#" if v else "." for v in row) for row in grid] if looks_clean(grid) else None


def looks_clean(grid):
    """Accept only line-art-like traces: not sparse, not a solid blob, not scattered noise."""
    n = len(grid)
    lit = [(y, x) for y in range(n) for x in range(n) if grid[y][x]]
    if not lit or not 0.14 <= len(lit) / n ** 2 <= 0.40:
        return False

    def on(y, x):
        return 0 <= y < n and 0 <= x < n and grid[y][x]

    around = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]
    isolated = sum(sum(on(y + dy, x + dx) for dy, dx in around) <= 1 for y, x in lit)
    interior = sum(all(on(y + dy, x + dx) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                   for y, x in lit)
    seen, biggest = set(), 0
    for start in lit:
        if start in seen:
            continue
        stack, size = [start], 0
        seen.add(start)
        while stack:
            y, x = stack.pop()
            size += 1
            for dy, dx in around:
                q = (y + dy, x + dx)
                if on(*q) and q not in seen:
                    seen.add(q)
                    stack.append(q)
        biggest = max(biggest, size)
    k = len(lit)
    return isolated / k <= 0.06 and biggest / k >= 0.95 and interior / k <= 0.25


def auto_glyph(source, app_name, desktop_id=""):
    img = load(source) if source else None
    rows = trace(img) if img else None
    if rows:
        return rows, "traced"
    # Names without a Latin letter/digit (e.g. Arabic) fall back to the desktop id's letters.
    label = app_name if any(c in FONT for c in app_name.upper()) else desktop_id.split(".")[-2:][0]
    return monogram(label), "monogram"


def auto_name(desktop_id):
    return "nothing-auto-" + re.sub(r"[^A-Za-z0-9_.-]", "-", desktop_id.removesuffix(".desktop"))


def repoint(path, icon_name, backup_dir):
    """Point a user launcher's Icon= at a theme name; write only on change."""
    text = path.read_text(errors="replace")
    new = re.sub(r"(?m)^Icon=.*$", f"Icon={icon_name}", text, count=1)
    if new == text:
        return False
    backup_dir.mkdir(parents=True, exist_ok=True)
    bak = backup_dir / path.name
    if not bak.exists():
        bak.write_text(text)
    path.write_text(new)
    return True
