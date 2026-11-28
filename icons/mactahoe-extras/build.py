"""MacTahoe extras: give every visible launcher a MacTahoe-style icon.

For each visible launcher whose Icon= name MacTahoe does not ship, either
  a) symlink it to existing MacTahoe artwork when that artwork is the app's real icon
     (ALIASES, curated by eye), or
  b) generate a MacTahoe-style tile from the app's original art: the same 64x64 canvas,
     56x56 rounded tile and drop shadow MacTahoe's own app icons use. Full-bleed tile art
     is clipped into the tile; a transparent logo is centred on a white tile (or a dark one
     when the logo would vanish on white). No art at all -> a lettered tile.

Files go into apps/scalable of MacTahoe, MacTahoe-dark and MacTahoe-light (deduplicated by
real path: MacTahoe-dark's apps/scalable is a symlink to MacTahoe's). Upstream files are
never touched; what we install is recorded in a manifest (with a hash or link target) so
rebuilds remove stale entries and --revert removes everything, but only while the file
is still exactly what we wrote.

    build.py            build + install
    build.py --revert   remove everything this script installed
"""
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
HOME = Path.home()
ICON_ROOT = HOME / ".local/share/icons"
THEMES = ["MacTahoe", "MacTahoe-dark", "MacTahoe-light"]
MANIFEST = HOME / ".local/state/mactahoe-extras/manifest.json"
# Nothing Dots repoints some launchers to nothing-* names and keeps the originals here.
NOTHING_BACKUP = HERE.parent / "nothing-dots" / "desktop-backup"

# Same launcher dirs and precedence as nothing-dots/auto.py.
APP_DIRS = [
    HOME / ".local/share/applications",
    Path("/var/lib/flatpak/exports/share/applications"),
    HOME / ".local/share/flatpak/exports/share/applications",
    Path("/usr/local/share/applications"),
    Path("/usr/share/applications"),
]
ICON_BASES = [
    HOME / ".local/share/icons", HOME / ".icons",
    HOME / ".local/share/flatpak/exports/share/icons",
    Path("/var/lib/flatpak/exports/share/icons"), Path("/usr/share/icons"),
]

# Launcher (desktop id or Icon= name) -> MacTahoe icon that IS that app's real icon.
# Checked by eye; e.g. MacTahoe's x.svg is X11 and gemini.svg is Calligra Gemini, so
# neither is used. github-desktop.svg is GitHub Desktop, not github.com.
ALIASES = {
    "chrome-fcgdpaemdckjieodcmmlpohbimhkjcob-Default.desktop": "accessories-podcast",  # Apple Podcasts
    "chatgpt": "gpt",
    "chrome-cadlkienfkclaiaibeoongdcgmdikeeg-Default.desktop": "gpt",  # ChatGPT web app
    "chrome-fmpnliohjhemenmnlpbfagaolkdacoja-Default.desktop": "claude",  # web app: Anthropic mark
    "chrome-kidfiilpilhbcocjhfkpdmecfkpifleh-Default.desktop": "notion",
    "chrome-lodlkdfmihgonocnmddehnfgiljnadcf-Default.desktop": "twitter",  # X logo
    "sklauncher.desktop": "minecraft",
    "io.github.shehawey.whatsapp": "whatsapp",
}
# Per-launcher tweaks for generated icons.
#   knockout: the art is a logo on a flat backdrop; drop the backdrop, treat as a logo
OVERRIDES = {
    "chrome-ajdemkepbiggbelkgicfebbjokenncei-Default.desktop": {"knockout": True},  # Kaggle
}

# MacTahoe app-icon geometry (64x64 canvas), taken from its own SVGs.
TX, TY, TS, TR = 4.0, 3.969, 56.0, 13.0
PX_PER_UNIT = 6  # embedded raster resolution: 56 units -> 336 px tile
LOGO_FRACTION = 0.66  # logo's longest side relative to the tile
WHITE = ("#ffffff", "#e9e9eb")
DARK = ("#2c2c2e", "#111113")


# ---------------------------------------------------------------- launchers / sources
def parse_desktop(path):
    """[Desktop Entry] keys, or None if hidden / not an application (as nothing-dots)."""
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
    if s.endswith((".svg", ".svgz")):
        return 10_000
    m = re.search(r"/(\d+)x\d+(@\d)?/", s)
    return int(m.group(1)) if m else 1


def icon_index():
    """stem -> best original-art file in hicolor (SVG, else largest PNG), then pixmaps."""
    index = {}
    for base in ICON_BASES:
        root = base / "hicolor"
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
                if stem not in index or _size_rank(p) > _size_rank(index[stem]):
                    index[stem] = p
    pix = Path("/usr/share/pixmaps")
    if pix.is_dir():
        for p in sorted(pix.iterdir()):
            if p.suffix.lower() in (".svg", ".png", ".xpm"):
                index.setdefault(p.stem, p)
    return index


def original_source(did, name, index):
    """The app's own art. nothing-* names were set by Nothing Dots: use its backup."""
    if name.startswith("nothing-") and (NOTHING_BACKUP / did).exists():
        orig = (parse_desktop(NOTHING_BACKUP / did) or {}).get("Icon", "")
        if orig.startswith("/"):
            p = Path(orig)
            # Same icon at a larger size, if hicolor has one.
            return index.get(p.stem, p) if p.exists() or p.stem in index else None
        name = orig or name
    return index.get(name)


def load(path, px=1024):
    try:
        if str(path).lower().endswith((".svg", ".svgz")):
            import gi
            gi.require_version("Rsvg", "2.0")
            import cairo
            from gi.repository import Rsvg
            h = Rsvg.Handle.new_from_file(str(path))
            surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, px, px)
            vp = Rsvg.Rectangle()
            vp.x, vp.y, vp.width, vp.height = 0, 0, px, px
            h.render_document(cairo.Context(surf), vp)
            buf = BytesIO()
            surf.write_to_png(buf)
            return Image.open(BytesIO(buf.getvalue())).convert("RGBA")
        return Image.open(path).convert("RGBA")
    except Exception:
        try:  # last resort, e.g. no PyGObject
            png = subprocess.run(["magick", "-background", "none", str(path), "png:-"],
                                 capture_output=True, timeout=20, check=True).stdout
            return Image.open(BytesIO(png)).convert("RGBA")
        except Exception:
            return None


# ---------------------------------------------------------------- image analysis
def _lum(r, g, b):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def _pixels(img):
    return list(img.get_flattened_data() if hasattr(img, "get_flattened_data") else img.getdata())


def _dominant(pixels):
    buckets = {}
    for r, g, b, a in pixels:
        if a >= 200:
            k = (r >> 3, g >> 3, b >> 3)
            buckets[k] = buckets.get(k, 0) + 1
    if not buckets:
        return (255, 255, 255)
    k = max(buckets, key=buckets.get)
    return tuple(c * 8 + 4 for c in k)


def crop_alpha(img, cutoff=16):
    bbox = img.getchannel("A").point(lambda a: 255 if a > cutoff else 0).getbbox()
    return img.crop(bbox) if bbox else None


def is_tile(img):
    """Square, (almost) fully opaque art = an app tile, maybe with rounded corners."""
    w, h = img.size
    if not 0.92 <= w / h <= 1.08:
        return False
    small = img.resize((64, 64), Image.BILINEAR)
    opaque = sum(1 for p in _pixels(small) if p[3] >= 200)
    return opaque / 64 ** 2 >= 0.9


def ring_colour(img):
    """Backdrop colour of a tile: dominant colour just inside its edge."""
    w, h = img.size
    small = img.resize((100, 100), Image.BILINEAR)
    px = _pixels(small)
    ring = [px[y * 100 + x] for y in range(100) for x in range(100)
            if (min(x, y, 99 - x, 99 - y) in (5, 6, 7))]
    return _dominant(ring)


def knockout(img):
    """Make the flat backdrop transparent (soft edge by colour distance)."""
    br, bg, bb = ring_colour(img)
    out = img.copy()
    data = []
    for r, g, b, a in _pixels(img):
        d = ((r - br) ** 2 + (g - bg) ** 2 + (b - bb) ** 2) ** 0.5
        data.append((r, g, b, int(a * max(0.0, min(1.0, (d - 25) / 50)))))
    out.putdata(data)
    return crop_alpha(out)


def vanishes_on_white(img):
    """True when most of the logo has too little contrast against white."""
    px = [p for p in _pixels(img.resize((64, 64), Image.BILINEAR)) if p[3] >= 128]
    if not px:
        return False
    faint = sum(1 for r, g, b, _ in px if 1.05 / (_lum(r, g, b) + 0.05) < 1.7)
    return faint / len(px) > 0.5


# ---------------------------------------------------------------- SVG output
def png_b64(img):
    buf = BytesIO()
    img.save(buf, "PNG", optimize=True)
    data = buf.getvalue()
    if len(data) > 40_000:  # grainy art: a 256-colour palette is visually identical, far smaller
        q = BytesIO()
        img.quantize(256, method=Image.Quantize.FASTOCTREE if img.mode == "RGBA"
                     else Image.Quantize.MEDIANCUT).save(q, "PNG", optimize=True)
        data = min(data, q.getvalue(), key=len)
    return base64.b64encode(data).decode()


def svg_doc(defs, body):
    shadow = (f'<rect x="{TX}" y="{TY + 1.1:.3f}" width="{TS}" height="{TS}" rx="{TR}" '
              f'fill="#000" opacity=".32" filter="url(#sh)"/>')
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        'width="64" height="64" viewBox="0 0 64 64"><defs>'
        '<filter id="sh" x="-.2" y="-.2" width="1.4" height="1.4" color-interpolation-filters="sRGB">'
        '<feGaussianBlur stdDeviation="1.1"/></filter>'
        f'<clipPath id="tile"><rect x="{TX}" y="{TY}" width="{TS}" height="{TS}" rx="{TR}"/></clipPath>'
        f'{defs}</defs>{shadow}{body}</svg>\n')


def tile_bg(colours):
    top, bottom = colours
    defs = (f'<linearGradient id="bg" x1="0" x2="0" y1="{TY}" y2="{TY + TS}" '
            f'gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{top}"/>'
            f'<stop offset="1" stop-color="{bottom}"/></linearGradient>')
    return defs, f'<rect x="{TX}" y="{TY}" width="{TS}" height="{TS}" rx="{TR}" fill="url(#bg)"/>'


def gen_tile(img):
    """Full-bleed art clipped into the tile; transparent corners filled with its backdrop."""
    r, g, b = ring_colour(img)
    side = min(int(TS * PX_PER_UNIT), max(192, img.width))  # upscaling adds bytes, not detail
    base = Image.new("RGBA", img.size, (r, g, b, 255))
    base.alpha_composite(img)
    base = base.convert("RGB").resize((side, side), Image.LANCZOS)
    return svg_doc("", f'<image clip-path="url(#tile)" x="{TX}" y="{TY}" width="{TS}" height="{TS}" '
                       f'preserveAspectRatio="none" xlink:href="data:image/png;base64,{png_b64(base)}"/>')


def gen_logo(img):
    """Transparent logo centred on a white (or dark) tile, with a faint glyph shadow."""
    w, h = img.size
    longest = TS * (LOGO_FRACTION if max(w, h) / min(w, h) < 1.6 else 0.78)
    lw, lh = (longest, longest * h / w) if w >= h else (longest * w / h, longest)
    px = (max(1, round(lw * PX_PER_UNIT)), max(1, round(lh * PX_PER_UNIT)))
    logo = img.resize(px, Image.LANCZOS)
    x, y = 32 - lw / 2, TY + TS / 2 - lh / 2
    bg_defs, bg = tile_bg(DARK if vanishes_on_white(img) else WHITE)
    defs = bg_defs + (
        f'<image id="logo" x="{x:.3f}" y="{y:.3f}" width="{lw:.3f}" height="{lh:.3f}" '
        f'preserveAspectRatio="none" xlink:href="data:image/png;base64,{png_b64(logo)}"/>'
        '<filter id="gs" x="-.2" y="-.2" width="1.4" height="1.4" color-interpolation-filters="sRGB">'
        '<feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"/>'
        '<feGaussianBlur stdDeviation=".7"/></filter>')
    body = (bg + '<use xlink:href="#logo" transform="translate(0 .6)" filter="url(#gs)" opacity=".18"/>'
            '<use xlink:href="#logo"/>')
    return svg_doc(defs, body)


def gen_letter(label):
    ch = next((c for c in label if c.isalnum()), "?").upper()
    bg_defs, bg = tile_bg(WHITE)
    return svg_doc(bg_defs, bg + (
        f'<text x="32" y="{TY + TS / 2:.3f}" dy=".35em" text-anchor="middle" '
        'font-family="Inter, Cantarell, sans-serif" font-weight="600" font-size="30" '
        f'fill="#6e6e73">{ch}</text>'))


def make_icon(source, label, opts):
    img = load(source) if source else None
    img = crop_alpha(img) if img else None
    if img is None:
        return gen_letter(label), "letter"
    if opts.get("knockout"):
        img = knockout(img) or img
        return gen_logo(img), "logo"
    # Ignore a soft baked-in shadow around tile art when deciding (and cropping).
    solid = crop_alpha(img, 160)
    if solid and is_tile(solid):
        return gen_tile(solid), "tile"
    return gen_logo(img), "logo"


# ---------------------------------------------------------------- install
def theme_dirs():
    """Real apps/scalable dirs of the MacTahoe variants, deduplicated."""
    out = []
    for t in THEMES:
        d = ICON_ROOT / t / "apps/scalable"
        if d.is_dir() and d.resolve() not in out:
            out.append(d.resolve())
    return out


def load_manifest():
    try:
        return json.loads(MANIFEST.read_text())
    except (OSError, ValueError):
        return {}


def save_manifest(m):
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")


def is_ours(path, entry):
    """Still exactly what we installed? (never touch anything else)"""
    if entry.get("link"):
        return path.is_symlink() and os.readlink(path) == entry["link"]
    if path.is_symlink() or not path.is_file():
        return False
    return hashlib.sha256(path.read_bytes()).hexdigest() == entry.get("sha256")


def upstream_names(manifest):
    """Icon names MacTahoe itself provides in any app dir (excluding our own files)."""
    names = set()
    for t in THEMES:
        root = ICON_ROOT / t
        for sub in ("apps", "apps@2x"):
            for dirpath, _dirs, files in os.walk(root / sub, followlinks=True):
                for f in files:
                    stem, ext = os.path.splitext(f)
                    if ext in (".svg", ".png", ".xpm"):
                        p = Path(dirpath, f)
                        key = str(Path(os.path.realpath(dirpath)) / f)
                        if key in manifest and is_ours(p, manifest[key]):
                            continue
                        names.add(stem)
    return names


def remove_entry(key, entry):
    p = Path(key)
    if (p.exists() or p.is_symlink()) and is_ours(p, entry):
        p.unlink()
        return True
    return False


def revert():
    m = load_manifest()
    n = sum(remove_entry(k, e) for k, e in m.items())
    MANIFEST.unlink(missing_ok=True)
    print(f"removed {n} MacTahoe extras")


def main():
    if "--revert" in sys.argv:
        return revert()
    dirs = theme_dirs()
    if not dirs:
        print("MacTahoe is not installed; nothing to do.")
        return
    manifest = load_manifest()
    upstream = upstream_names(manifest)
    index = icon_index()

    plan, report = {}, []  # icon name -> ("link", target) | ("file", svg text)
    for path, keys in launchers():
        did, icon, label = path.name, keys["Icon"], keys.get("Name", path.stem)
        if "/" in icon:
            continue  # absolute path: not looked up in the theme
        name = re.sub(r"\.(svg|png|xpm)$", "", icon)
        if name in upstream or name in plan:
            continue
        alias = ALIASES.get(did) or ALIASES.get(name)
        if alias and all((d / f"{alias}.svg").exists() for d in dirs):
            plan[name] = ("link", f"{alias}.svg")
            report.append((label, name, f"alias -> {alias}"))
            continue
        svg, kind = make_icon(original_source(did, name, index), label,
                              OVERRIDES.get(did) or OVERRIDES.get(name) or {})
        plan[name] = ("file", svg)
        report.append((label, name, f"generated ({kind})"))

    new_manifest = {}
    for d in dirs:
        for name, (kind, value) in plan.items():
            dst = d / f"{name}.svg"
            key = str(dst)
            if kind == "link":
                entry = {"link": value}
            else:
                data = value.encode()
                entry = {"sha256": hashlib.sha256(data).hexdigest()}
            old = manifest.get(key)
            if dst.exists() or dst.is_symlink():
                if not (old and is_ours(dst, old)):
                    print(f"skip {dst}: not ours (upstream file)", file=sys.stderr)
                    continue
                if old == entry:
                    new_manifest[key] = entry
                    continue
                dst.unlink()
            if kind == "link":
                dst.symlink_to(value)
            else:
                tmp = dst.with_name(f".{dst.name}.tmp")
                tmp.write_bytes(data)
                tmp.replace(dst)
            new_manifest[key] = entry
    stale = 0
    for key, entry in manifest.items():
        if key not in new_manifest:
            stale += remove_entry(key, entry)
    save_manifest(new_manifest)

    for label, name, what in sorted(report, key=lambda r: r[0].lower()):
        print(f"  {label:<36} {name:<58} {what}")
    links = sum(1 for k, _ in plan.values() if k == "link")
    print(f"{links} aliased, {len(plan) - links} generated, {stale} stale removed "
          f"-> {', '.join(map(str, dirs))}")


if __name__ == "__main__":
    main()
