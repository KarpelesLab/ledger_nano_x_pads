"""3D models for the reconstruction: picks a KiCad library look-alike where one exists, and otherwise
writes a simple VRML body (a prism from the part's outline, in its colour) with its marking as raised
pixel text, since KiCad's 3D viewer cannot show textures.

VRML geometry is built in footprint-local coordinates, millimetres, x right and y up as KiCad's 3D
view expects; KiCad reads VRML in units of 0.1 inch, so everything is scaled by 1/2.54.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "3d")
LIB = "/usr/share/kicad/3dmodels/"
FONT = "/usr/share/fonts/dejavu/DejaVuSansMono-Bold.ttf"
U = 1 / 2.54

# library look-alikes for footprints whose pads follow the library's own layout around the origin
LIBRARY = {
    "MCU": "Package_DFN_QFN.3dshapes/QFN-48-1EP_7x7mm_P0.5mm_EP5.15x5.15mm.step",
    "SE": "Package_DFN_QFN.3dshapes/QFN-20-1EP_4x4mm_P0.5mm_EP2.5x2.5mm.step",
    "USBPD": "Package_DFN_QFN.3dshapes/QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm.step",
    "PWR1": "Package_DFN_QFN.3dshapes/QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm.step",
}

# markings read from the photos, laid on the library models (whose bodies are 0.78 mm tall), each reading
# along the direction it has on the part. The SE marking is hard to read: some characters are a best guess
LIBRARY_MARKINGS = {
    # text, and the two outline corners whose direction the text reads along
    "MCU": ("STM32WB35\nCCU6A\nGQ239139R\nCHN GQ 132", (0, 1)),
    "SE": ("Ledger\n02MJCH\n13N\n471", (0, 1)),
    "USBPD": ("4500L\nM20700", (0, 3)),
}
LIBRARY_HEIGHT = .78

# generated bodies: colour (r, g, b), height in mm, marking
CUSTOM = {
    "PWR2": ((.08, .08, .08), .55, "E058\n2050"),
    "PWR3": ((.08, .08, .08), .5, "TC"),
    "X2": ((.55, .55, .58), .5, "2GC"),
    "X3": ((.45, .5, .6), .4, "6"),
    "X9": ((.08, .08, .08), 1.0, "P8W 26"),
    "X10": ((.08, .08, .08), 1.0, "1C4F"),
    "Y1": ((.75, .75, .72), .5, "32k0\nJ 2B"),
    "L1": ((.55, .55, .57), 1.0, ""),
    "RFF": ((.15, .3, .7), .6, ""),
    "BTB": ((.12, .12, .12), .6, ""),
    "ANT": ((.92, .92, .9), .9, ""),
    "USB": ((.7, .7, .72), 3.2, ""),
    "SW1": ((.2, .2, .2), 1.5, ""),
    "SW2": ((.2, .2, .2), 1.5, ""),
}
for i in range(1, 10):
    CUSTOM[f"P{i}"] = ((.08, .08, .08), .6, "P")

MARK = (.85, .85, .8)


def vrml_prism(poly, z0, z1, color):
    """A prism with polygon poly (list of (x, y) in mm, convex or not, counter-clockwise) as its section."""
    n = len(poly)
    pts = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
    faces = [list(range(n - 1, -1, -1)), list(range(n, 2 * n))]
    faces += [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    coords = ", ".join(f"{x * U:.5f} {y * U:.5f} {z * U:.5f}" for x, y, z in pts)
    index = ", ".join(", ".join(map(str, f)) + ", -1" for f in faces)
    r, g, b = color
    return (f"Shape {{ appearance Appearance {{ material Material {{ diffuseColor {r} {g} {b} specularColor .2 .2 .2 shininess .3 }} }}\n"
            f" geometry IndexedFaceSet {{ solid FALSE coord Coordinate {{ point [ {coords} ] }} coordIndex [ {index} ] }} }}\n")


def ccw(poly):
    area = sum(poly[i][0] * poly[i - 1][1] - poly[i - 1][0] * poly[i][1] for i in range(len(poly)))
    return poly if area < 0 else poly[::-1]


def text_pixels(text, rows=11):
    """The marking as a grid of on-pixels: list of (col, row), plus the grid size."""
    lines = text.split("\n")
    font = ImageFont.truetype(FONT, 60)
    w = max(font.getbbox(l)[2] for l in lines) + 8
    h = 72 * len(lines) + 8
    im = Image.new("L", (w, h), 0)
    dr = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        dr.text((4, 4 + 72 * i), l, fill=255, font=font)
    im = im.crop(im.getbbox())
    gh = rows * len(lines)
    gw = max(1, round(im.width * gh / im.height))
    small = im.resize((gw, gh), Image.BOX)
    on = [(x, y) for y in range(gh) for x in range(gw) if small.getpixel((x, y)) > 100]
    return on, gw, gh


def marking(text, center, axis_angle, length, width, z):
    """Raised text centred on a part's top face, reading along axis_angle (radians, 0 = +x)."""
    if not text:
        return ""
    on, gw, gh = text_pixels(text)
    cell = min(length * .8 / gw, width * .7 / gh)
    ca, sa = math.cos(axis_angle), math.sin(axis_angle)
    out = []
    for cx, cy in on:
        # grid x along the axis, grid y down the page (so up is +perpendicular)
        u, v = (cx - gw / 2 + .5) * cell, (gh / 2 - cy - .5) * cell
        x, y = center[0] + u * ca - v * sa, center[1] + u * sa + v * ca
        s = cell / 2
        sq = [(x + dx * ca - dy * sa, y + dx * sa + dy * ca) for dx, dy in ((-s, -s), (s, -s), (s, s), (-s, s))]
        out.append(vrml_prism(sq, z, z + .02, MARK))
    return "".join(out)


def write_custom(ref, cid, outline_mm, color, height, text):
    """Write a generated model for footprint ref; outline_mm is the body outline in footprint-local mm."""
    os.makedirs(OUT_DIR, exist_ok=True)
    poly = ccw(outline_mm)
    body = vrml_prism(poly, 0, height, color)
    # read along the longer side, upright on screen
    e = [(poly[(i + 1) % len(poly)][0] - poly[i][0], poly[(i + 1) % len(poly)][1] - poly[i][1]) for i in range(len(poly))]
    lens = [math.hypot(*v) for v in e]
    k = max(range(len(e)), key=lambda i: lens[i])
    ang = math.atan2(e[k][1], e[k][0])
    if math.cos(ang) < -1e-6 or (abs(math.cos(ang)) < 1e-6 and math.sin(ang) < 0):
        ang += math.pi
    width = min(lens)
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    src = "#VRML V2.0 utf8\n" + body + marking(text, (cx, cy), ang, lens[k], width, height)
    path = os.path.join(OUT_DIR, f"{ref}.wrl")
    open(path, "w").write(src)
    return path


def passive_model(kind, length_mm):
    """A library resistor or capacitor of the nearest size to the measured part length."""
    size = "0201_0603Metric" if length_mm < .85 else "0402_1005Metric" if length_mm < 1.35 else "0603_1608Metric" if length_mm < 1.85 else "0805_2012Metric"
    lib, p = ("Resistor_SMD", "R_") if kind == "R" else ("Capacitor_SMD", "C_")
    return f"{LIB}{lib}.3dshapes/{p}{size}.step"


def ceramic_model(ref, length_mm, width_mm, vertical, color):
    """A two-terminal ceramic part not in the library colours: body with silver end caps."""
    os.makedirs(OUT_DIR, exist_ok=True)
    L, W = length_mm * .85, width_mm * .8
    cap = L * .22
    def rect(x0, x1):
        pts = [(x0, -W / 2), (x1, -W / 2), (x1, W / 2), (x0, W / 2)]
        return [(-y, x) for x, y in pts] if vertical else pts
    src = ("#VRML V2.0 utf8\n" + vrml_prism(ccw(rect(-L / 2 + cap, L / 2 - cap)), 0, W * .9, color) +
           vrml_prism(ccw(rect(-L / 2, -L / 2 + cap)), 0, W * .9, (.82, .82, .82)) +
           vrml_prism(ccw(rect(L / 2 - cap, L / 2)), 0, W * .9, (.82, .82, .82)))
    path = os.path.join(OUT_DIR, f"{ref}.wrl")
    open(path, "w").write(src)
    return path


def write_marking(ref, local_outline, spec, z):
    """Only the marking, for a library model: centred on the outline, reading from corner i to corner j."""
    text, (i, j) = spec
    os.makedirs(OUT_DIR, exist_ok=True)
    (x0, y0), (x1, y1) = local_outline[i], local_outline[j]
    ang = math.atan2(y1 - y0, x1 - x0)
    side = math.hypot(x1 - x0, y1 - y0)
    cx = sum(p[0] for p in local_outline) / len(local_outline)
    cy = sum(p[1] for p in local_outline) / len(local_outline)
    path = os.path.join(OUT_DIR, f"{ref}_marking.wrl")
    open(path, "w").write("#VRML V2.0 utf8\n" + marking(text, (cx, cy), ang, side, side, z))
    return path
