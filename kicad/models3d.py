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
    "PWR3": ((.08, .08, .08), .5, "3T"),
    "X2": ((.55, .55, .58), .5, "2GC"),
    "X3": ((.45, .5, .6), .4, "6"),
    "X9": ((.08, .08, .08), 1.0, "P8W 26"),
    "X10": ((.08, .08, .08), 1.0, "1C4F"),
    "X11": ((.08, .08, .08), .5, "AF"),
    "Y1": ((.75, .75, .72), .5, "32k0\nJ 2B"),
    "L1": ((.55, .55, .57), 1.0, ""),
    "RFF": ((.15, .3, .7), .6, ""),
    "ANT": ((.92, .92, .9), .9, ""),
}
for i in range(1, 10):
    CUSTOM[f"P{i}"] = ((.08, .08, .08), .6, "P")

MARK = (.85, .85, .8)

# parts modelled piece by piece from the photo, in front-photo pixels: (x0, y0, x1, y1, z0, z1, colour) boxes
# (x, y, radius mm, z0, z1, colour) raised discs, and (x, y, radius mm, colour) flat dots on top. RFF: a lavender-grey ceramic body with castellated terminals on
# both long sides and on both ends, and a dark pin 1 dot by its input
SILVER = (.8, .8, .78)
DETAILED = {
    "RFF": {
        "boxes": [(2925, 1590, 3090, 1687, 0, .55, (.74, .76, .84))] +
                 [(x0, y0, x0 + 33, y0 + 14, 0, .56, SILVER) for x0 in (2937, 2990, 3047) for y0 in (1584, 1679)] +
                 [(2919, 1622, 2933, 1655, 0, .56, SILVER), (3082, 1622, 3096, 1655, 0, .56, SILVER)],
        "dots": [(2970, 1638, .13, (.28, .22, .38))],
    },
}


def _btb():
    """Hirose BM20B(0.8)-16DS-0.4V receptacle, built from the dimensions of Hirose's drawing (its 3D model is
    not redistributable, so this is our own simplified model): a dark housing 5.68 x 2.30 x 0.80 mm with a slot
    around a centre island, raised ends with guide slopes, 16 gold contacts at 0.4 mm pitch that run from
    their tails over each wall into the slot, and metal hold-down tails at the ends. u runs along the
    connector (photo y), v across it (photo x), in mm from its centre."""
    cx, cy = 4542, 1420                      # centre, from the pads in the bare back photo
    def box(u0, u1, v0, v1, z0, z1, col):
        return (cx + v0 * d_px, cy + u0 * d_px, cx + v1 * d_px, cy + u1 * d_px, z0, z1, col)
    d_px = 84
    dark, gold, tin = (.21, .2, .2), (.83, .67, .3), (.78, .78, .76)
    out = [box(-1.985, 1.985, -1.045, -.685, 0, .67, dark)]       # first box: the part's body, for hovering
    out.append(box(-1.985, 1.985, .685, 1.045, 0, .67, dark))       # the other long wall
    out.append(box(-1.895, 1.895, -.425, .425, 0, .67, dark))       # centre island
    out.append(box(-2.315, 2.315, -.685, .685, 0, .14, dark))       # slot floor
    for s in (-1, 1):
        lo, hi = sorted((s * 2.5, s * 2.835))
        out.append(box(lo, hi, -1.095, 1.095, 0, .8, dark))         # end cap
        lo, hi = sorted((s * 1.985, s * 2.5))
        out += [box(lo, hi, -1.145, -.81, 0, .8, dark), box(lo, hi, .81, 1.145, 0, .8, dark)]   # guide rails
        lo, hi = sorted((s * 2.315, s * 2.5))
        out.append(box(lo, hi, -.81, .81, 0, .47, dark))            # guide slope into the slot
        lo, hi = sorted((s * 2.565, s * 2.655))
        out += [box(lo, hi, -1.17, -1.095, 0, .1, tin), box(lo, hi, 1.095, 1.17, 0, .1, tin)]   # hold-down tails
    for u in (-1.4, -1.0, -.6, -.2, .2, .6, 1.0, 1.4):
        for s in (-1, 1):
            v = lambda a, b: sorted((s * a, s * b))
            out.append(box(u - .055, u + .055, *v(1.04, 1.17), 0, .08, gold))       # tail on the pad
            out.append(box(u - .055, u + .055, *v(.66, 1.06), .67, .69, gold))     # over the wall
            out.append(box(u - .055, u + .055, *v(.66, .69), .14, .69, gold))      # down into the slot
    return {"boxes": out}


DETAILED["BTB"] = _btb()


def _usb():
    """USB-C receptacle: a stainless shell with rounded sides (stacked slices approximate the stadium profile,
    8.94 x 3.26 mm), the dark mouth at the board's end with the tongue and its gold contacts, the six holes on
    the shell's top and the solder tails at the back, placed from the front photo (shell y 1050-1790, back at
    x 680, mouth past the board's edge at x 0). u runs along the plug (photo x), v across it (photo y)."""
    mouth, cy, k = 0, 1420, 84
    def box(u0, u1, v0, v1, z0, z1, col):
        return (mouth + u0 * k, cy + v0 * k, mouth + u1 * k, cy + v1 * k, z0, z1, col)
    steel, dark, black, gold, tin = (.8, .8, .78), (.16, .16, .17), (.04, .04, .05), (.83, .67, .3), (.76, .76, .74)
    H, W, L = 3.26, 8.94, 8.1
    def stadium(u0, u1, hw, hh, zc, col, n=24):
        """Slices of a rounded-end section (half width hw, half height hh) centred at height zc."""
        out = []
        for i in range(n):
            za, zb = zc - hh + 2 * hh * i / n, zc - hh + 2 * hh * (i + 1) / n
            t = ((za + zb) / 2 - zc) / hh
            half = hw - hh + hh * math.sqrt(max(0, 1 - t * t))
            out.append(box(u0, u1, -half, half, za, zb, col))
        return out
    zc = H / 2
    out = stadium(0, L, W / 2, H / 2, zc, steel)                       # the shell (first box is its body)
    out += stadium(-.006, .6, W / 2 - .22, H / 2 - .22, zc, black)       # the mouth, seen from the end
    out.append(box(-.012, .6, -3.35, 3.35, zc - .35, zc + .35, dark))    # the tongue
    for i in range(12):
        v = -2.75 + .5 * i
        out += [box(-.016, .5, v - .12, v + .12, zc + .35, zc + .38, gold),
                box(-.016, .5, v - .12, v + .12, zc - .38, zc - .35, gold)]
    for v in (-2.6, -1.58, -.55, .41, 1.43, 2.43):                       # holes in the shell's top
        out.append(box(6.45, 6.9, v - .24, v + .24, H, H + .01, black))
    # solder tails of the A row, behind the shell on USB1's pads (the B row is hidden under the shell)
    for y in (1156, 1202, 1245, 1289, 1330, 1374, 1418, 1460, 1502, 1546, 1589, 1633):
        v = (y - cy) / k
        out.append(box(L, L + 1.05, v - .12, v + .12, 0, .1, tin))
    for v in (-4.3, 4.3):                                                # shell legs
        out.append(box(L - 1.1, L + .1, v - .3, v + .3, 0, 1.0, steel))
    return {"boxes": out}


DETAILED["USB"] = _usb()


def _switch(cx, cy, along):
    """A flat 4-terminal tactile switch: a dark square frame 3.2 x 2.75 x 0.45 mm with a gold metal dome and its
    plunger in a circle in the middle, and two silver terminals on each of the two sides along `along` ('x' or
    'y', photo axes), placed from the back photo."""
    k = 84
    def box(a0, a1, b0, b1, z0, z1, col):
        # a runs along the terminal sides, b across them
        if along == "x":
            return (cx + a0 * k, cy + b0 * k, cx + a1 * k, cy + b1 * k, z0, z1, col)
        return (cx + b0 * k, cy + a0 * k, cx + b1 * k, cy + a1 * k, z0, z1, col)
    frame, steel = (.24, .23, .22), (.8, .8, .78)
    out = [box(-1.6, 1.6, -1.37, 1.37, 0, .45, frame)]
    for a in (-1, 1):
        for b in (-1, 1):
            lo, hi = sorted((a * 1.45, a * 1.95))
            out.append(box(lo, hi, b * .95 - .3, b * .95 + .3, 0, .2, steel))
    return {"boxes": out, "discs": [(cx, cy, 1.0, .45, .52, (.86, .74, .42)), (cx, cy, .38, .52, .58, (.8, .7, .5))]}


DETAILED["SW1"] = _switch(735, 1410, "x")
DETAILED["SW2"] = _switch(5133, 1420, "y")


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


def write_detailed(ref, cid, to_local):
    """A model built from DETAILED[cid]; to_local maps photo pixels to footprint-local mm."""
    os.makedirs(OUT_DIR, exist_ok=True)
    spec = DETAILED[cid]
    src = "#VRML V2.0 utf8\n"
    for x0, y0, x1, y1, z0, z1, col in spec["boxes"]:
        pts = [to_local(x, y) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        src += vrml_prism(ccw(pts), z0, z1, col)
    for x, y, r, z0, z1, col in spec.get("discs", []):
        cx, cy = to_local(x, y)
        circle = [(cx + r * math.cos(2 * math.pi * k / 24), cy + r * math.sin(2 * math.pi * k / 24)) for k in range(24)]
        src += vrml_prism(ccw(circle), z0, z1, col)
    top = max(b[5] for b in spec["boxes"])
    for x, y, r, col in spec.get("dots", []):
        cx, cy = to_local(x, y)
        circle = [(cx + r * math.cos(2 * math.pi * k / 16), cy + r * math.sin(2 * math.pi * k / 16)) for k in range(16)]
        src += vrml_prism(ccw(circle), top - .01, top + .01, col)
    path = os.path.join(OUT_DIR, f"{ref}.wrl")
    open(path, "w").write(src)
    return path
