"""Write implants.js for viewer3d.html: approximate 3D models of hardware implants found in Ledger Nano X
devices, placed on the reconstructed board: the two Tibane Labs examined (https://tibane.net, "Ledger Nano X:
the spy implant") and an earlier, hand-wired one.

Everything here is measured from photographs, so it is approximate (to about a millimetre)
and partly inferred where the photos don't show a part:

  Specimen A (generation 2): a translucent amber Kapton flex. Its tap layer is laminated over the back of
    the board and soldered to its test pads; a neck wraps around the board's top edge to the front, where
    a module area (LTE module, STM32G431, eSIM) and a tail with a replacement battery replace the original
    battery, with a flat antenna taped on top. The photos show it opened out flat; here it is folded back
    into place around the board. The tap outline was traced from the photo of the flex in place on the
    board, mapped onto the board by the eight solder joints on known test pads, then squared up: the flex is
    cut with straight edges along the board's axes.
  Specimen B (generation 3): a black-coated flex cut to fit under the OLED on the back of the board, around
    the board-to-board connector, carrying an nRF9151 module, a scraped MCU and eSIM and a U.FL connector,
    with a coax lead to an antenna stuck inside the case (not modelled), and a leg that wraps around the board's
    edge to the battery contacts on the front. Placed from the photo of the board
    with the screen removed, mapped onto the board by the USB shell joints, the two buttons and the BTB
    connector.
  Specimen C (generation 1): no flex at all. A small green board marked "V03", a copper coil antenna and a
    half-size 70 mAh cell (XYT 261626) sit in the case under the front of the board, where the original battery
    was, and fine enamelled wires run from the V03 board around the board's top edge to the test pads on the
    back (a blob of white glue holds them over the display pads) and to the battery contacts on the front.
    From @Us_Chan007's photographs (x.com/Us_Chan007/status/2109259136915624446 and 2109260884258554298);
    the back joints were located by fitting the photo of the back onto the board (USB shell joints, the
    button and the via grid under the secure element).

Coordinates: photo pixels of the back photo (5376x3024, 84 px/mm), converted to the viewer's millimetres:
x right, y up, z out of the front side.
"""
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nanox_data as d  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
S = d.PX_PER_MM


def thickness():
    m = re.search(r"\(thickness ([\d.]+)\)", open(os.path.join(HERE, "nanox.kicad_pcb")).read())
    return float(m.group(1))


T = thickness()
TOP, BOT = T / 2, -T / 2


def xy(x, y):
    """Back-photo pixels to viewer mm."""
    return [round(x / S, 3), round((y - d.IMG_H) / S, 3)]


def poly(pts):
    return [xy(*p) for p in pts]


def rect(x0, y0, x1, y1):
    return poly([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])


# ---- Specimen A ---------------------------------------------------------------------------------------

KAPTON = "#d9891c"
TAP_A = [[1568,1923],[1568,1973],[1188,1973],[1188,1775],[996,1775],[996,1965],[920,1965],[920,1905],[520,1905],
    [525,1558],[1020,1558],[1020,835],[1195,835],[1195,1037],[1380,1037],[1380,968],[1520,968],[1520,824],
    [1888,824],[1888,1037],[1970,1037],[1970,878],[2026,878],[2026,1050],[2860,1050],[2860,902],[2992,902],
    [2992,1036],[3285,1036],[3285,775],[3677,775],[3677,875],[4156,875],[4156,1665],[4472,1665],[4485,2075],
    [4266,2075],[4256,1770],[3978,1770],[3978,1923]]
# solder joints of the tap layer, on these test pads
JOINTS_A = ["35", "34", "36", "29", "31", "38", "14", "03", "07"]


def specimen_a():
    pads = {p["id"]: p for p in d.load_js("pads.js", "PADS")}
    out = []
    flex = dict(color=KAPTON, opacity=.55)
    zt0, zt1 = BOT - .14, BOT - .06            # tap layer, laminated on the back
    zm0, zm1 = TOP + 1.05, TOP + 1.12          # module area and tail, on the front above its parts
    edge = 824                                  # board top edge where the neck wraps, in photo px
    out.append(dict(t="slab", poly=poly(TAP_A), z=[zt0, zt1], **flex, title="Tap layer (Kapton flex)",
                    notes="Translucent polyimide flex laminated over the back of the board, cut to its outline, "
                          "soldered to the test pads for GND, VBAT and the display SPI lines"))
    # the neck folds around the top edge from the back to the front
    r = (zm1 - zt1) / 2
    zc = (zm1 + zt1) / 2
    yc = edge / 1.0
    path = [[(edge + 40), zt1], [yc, zt1]]
    for k in range(1, 12):
        phi = -math.pi / 2 + math.pi * k / 12
        path.append([yc - r * S * math.cos(phi), zc + r * math.sin(phi)])
    path += [[yc, zm1], [edge + 60, zm1]]
    out.append(dict(t="ribbon", x=[1520 / S, 1888 / S], path=[[round((y - d.IMG_H) / S, 3), round(z, 3)] for y, z in path],
                    **flex, title="Neck (Kapton flex)", notes="Folds around the board's top edge from the tap layer to the module area"))
    out.append(dict(t="slab", poly=rect(865, 830, 2470, 2070), z=[zm0, zm1], **flex, title="Module area (Kapton flex)",
                    notes="Carries the LTE module, the STM32G431 and the eSIM, in the space the original battery filled"))
    out.append(dict(t="slab", poly=rect(2470, 1150, 4950, 1900), z=[zm0, zm1], **flex, title="Tail (Kapton flex)",
                    notes="Runs under the replacement battery to the two battery tabs marked +"))
    out.append(dict(t="box", at=xy(1380, 1450), size=[1030 / S, 1180 / S], z=[zm1, zm1 + 1.7], color="#c9c9c6",
                    title="LTE module", notes="Shielded cellular module that sends the recovered words out"))
    out.append(dict(t="box", at=xy(2190, 1150), size=[5, 5], z=[zm1, zm1 + .55], color="#26262a", marking="ST\nSTM32G431\nKBU6",
                    title="STM32G431KBU6", notes="Arm Cortex-M4 MCU, UFQFPN32, markings intact; decodes the screen data"))
    out.append(dict(t="box", at=xy(2190, 1760), size=[2, 2], z=[zm1, zm1 + .45], color="#2e2e30",
                    title="eSIM", notes="8-pad package, about 2 x 2 mm, wired to the modem's SIM lines"))
    out.append(dict(t="box", at=xy(3620, 1455), size=[2300 / S, 1170 / S], z=[zm1, zm1 + 3.4], color="#b9bcc0",
                    title="Replacement battery", notes="Smaller, unmarked lithium-polymer cell with no protection circuit, "
                                                       "replacing the original battery"))
    for y in (1240, 1670):
        out.append(dict(t="box", at=xy(4860, y), size=[1.8, 2.2], z=[zm1, zm1 + .2], color="#d0d0cc",
                        title="Battery tab", notes="Battery soldered to the tabs at the end of the tail"))
    ztop_bat, ztop_can = zm1 + 3.4, zm1 + 1.7
    out.append(dict(t="slab", poly=rect(2470, 940, 3580, 1910), z=[ztop_bat, ztop_bat + .06], color="#151515",
                    title="Antenna", notes="Flat printed antenna taped across the battery and the LTE module"))
    out.append(dict(t="slab", poly=rect(1050, 940, 2470, 1910), z=[ztop_can, ztop_can + .06], color="#151515",
                    title="Antenna", notes="Flat printed antenna taped across the battery and the LTE module"))
    feed = xy(2940, 1590)
    out.append(dict(t="tube", points=[[*feed, ztop_bat + .1], [*xy(2470, 1420), ztop_bat + .3], [*xy(1180, 1230), ztop_can + .3],
                                      [*xy(900, 2000), ztop_can - .2], [*xy(880, 2060), zm1 + .1]],
                    radius=.12, color="#c46a3c", title="Antenna feed wire", notes="Single copper lead from the antenna to the module"))
    for pid in JOINTS_A:
        p = pads[pid]
        out.append(dict(t="dome", at=xy(p["x"], p["y"]), r=.45, z=zt0, side="back", color="#d8d8d8",
                        title=f"Solder joint on TP{pid}", notes=(p.get("name") or "anchor joint") +
                        ("" if p.get("name") else ": holds the flex in place, not wired to the implant")))
    return out


# ---- Specimen B ---------------------------------------------------------------------------------------

# photo pixels of camo-under-screen.jpg to back-photo pixels. That photo shows the back of the board turned
# 180 degrees from the back photo (as does the photo of specimen A in place, whose mapping is fitted on test pads
# independently); fitted on the USB shell joints, both buttons and the BTB connector, about 10 px residual
MB = [[-2.7223, -0.06254], [0.08727, -2.72109], [5397.51359, 3461.84757]]


def b(px, py):
    return [px * MB[0][0] + py * MB[1][0] + MB[2][0], px * MB[0][1] + py * MB[1][1] + MB[2][1]]


def b_rect(x0, y0, x1, y1):
    return poly([b(x0, y0), b(x1, y0), b(x1, y1), b(x0, y1)])


def b_centre(x0, y0, x1, y1):
    cx, cy = b((x0 + x1) / 2, (y0 + y1) / 2)
    w = math.dist(b(x0, y0), b(x1, y0)) / S
    h = math.dist(b(x0, y0), b(x0, y1)) / S
    return xy(cx, cy), [round(w, 3), round(h, 3)]


# the OLED SPI test pads specimen B solders to: CS, CLK and MOSI
TAPS_B = ["31", "34", "35"]


def specimen_b():
    out = []
    zf0, zf1 = BOT - .14, BOT - .06            # body, on the back under the OLED
    # around the OLED connector the flex stops short of C33 and C34 (photo y 597)
    body = [b(*p) for p in [[163, 597], [458, 597], [458, 495], [1540, 490], [1540, 930]]]
    # along the board's top edge (in board px) the flex runs out to 0.25 mm from the edge, around the
    # board's notch next to TP31, then steps back in before C32 (Tibane Labs' close-up of the fitted flex)
    def edge_at(x):
        """Where the photo-fitted edge (photo y 930) crosses board column x."""
        (x0, y0), (x1, y1) = b(1540, 930), b(163, 930)
        return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    body += [[2190, edge_at(2190)], [2190, 760], [3750, 760], [3750, 840], [3935, 840], [3935, 800],
             [4200, 800], [4200, edge_at(4200)], b(163, 930)]
    # the window fits snugly around the board-to-board connector (its pads and hold-downs, 0.1 mm clear)
    btb = [q["polygon"] for c in d.load_js("components.js", "COMPONENTS") if c["id"] == "BTB" for q in c["pads"]]
    bx = [v[0] for pg in btb for v in pg]; by = [v[1] for pg in btb for v in pg]
    w8 = 8
    window = [[min(bx) - w8, min(by) - w8], [max(bx) + w8, min(by) - w8], [max(bx) + w8, max(by) + w8], [min(bx) - w8, max(by) + w8]]
    # cut-outs around the Ledger's own capacitors, which key the flex into place: holes around C30 and C31,
    # and a notch in the edge around C32, each 0.15 mm clear of the parts
    caps = {q["id"]: q["box"] for q in d.load_js("passives.js", "PASSIVES") if q["id"] in ("C30", "C31", "C32")}
    m = 13
    holes = [window] + [[[x - m, y - m], [x + w + m, y - m], [x + w + m, y + h + m], [x - m, y + h + m]]
                        for x, y, w, h in (caps["C30"], caps["C31"])]

    def notch(name, box):
        """Cut box (x, y, w, h) out of whichever body edge crosses it, on the side away from the body."""
        cx, cy, cw, ch = box
        for i in range(len(body)):
            (x0, y0), (x1, y1) = body[i], body[(i + 1) % len(body)]
            if abs(x1 - x0) < 1 or not min(x0, x1) <= cx + cw / 2 <= max(x0, x1):
                continue
            at = lambda x: y0 + (y1 - y0) * (x - x0) / (x1 - x0)
            if not cy - m <= at(cx + cw / 2) <= cy + ch + m:
                continue
            # the body is on the side of the edge where the part's far end is not
            inner = cy + ch + m if at(cx) < cy + ch / 2 else cy - m
            xs = (cx - m, cx + cw + m) if x1 > x0 else (cx + cw + m, cx - m)
            body[i + 1:i + 1] = [[xs[0], at(xs[0])], [xs[0], inner], [xs[1], inner], [xs[1], at(xs[1])]]
            return
        raise SystemExit(f"{name} is not on an edge of specimen B's body")
    notch("C32", caps["C32"])
    # round holes over the Ledger's OLED SPI test pads, each soldered by hand to the pad below
    pads = {p["id"]: p for p in d.load_js("pads.js", "PADS")}
    for pid in TAPS_B:
        cx, cy = pads[pid]["x"], pads[pid]["y"]
        holes.append([[cx + 36 * math.cos(a), cy + 36 * math.sin(a)] for a in (k * math.pi / 8 for k in range(16))])
    out.append(dict(t="slab", poly=poly(body), holes=[poly(h) for h in holes], z=[zf0, zf1], color="#161618", opacity=1,
                    title="Implant flex (black-coated)", notes="Orange polyimide flex painted black, cut to fit under the OLED "
                    "around the Ledger's own parts: the window fits snugly around the board-to-board connector, and cut-outs around "
                    "C30, C31 and C32 key it into place so it can't be misaligned; it stops short of C33 and C34. "
                    "It taps only the OLED SPI CS, CLK and MOSI test pads (31, 34, 35), skipping the D/C (36) and SE "
                    "RESET (29) pads specimen A also soldered to, which likely made it easier to install"))
    parts = [
        ((772, 565, 1170, 925), 1.3, "#cfcfcc", "Nordic\nnRF9151", "Nordic nRF9151 module",
         "LTE-M / NB-IoT modem with its own regulatory markings, left unscraped"),
        ((1235, 570, 1480, 820), .75, "#2a2a2c", "", "MCU (markings scraped)",
         "QFN microcontroller with its top surface abraded; more pins than Specimen A's STM32"),
        ((525, 770, 735, 930), .6, "#2a2a2c", "", "eSIM (markings scraped)",
         "MFF2 eSIM, 5 x 6 mm, top surface abraded"),
        ((955, 475, 1025, 535), .9, "#c9a54a", "", "U.FL connector", "Antenna connector for the coax lead"),
    ]
    for pid in TAPS_B:
        out.append(dict(t="dome", at=xy(pads[pid]["x"], pads[pid]["y"]), r=.4, z=BOT, side="back", color="#d8d8d8",
                        title=f"Solder joint on TP{pid}", notes=f"{pads[pid]['name']}: a round hole in the flex, soldered "
                                                              "by hand to the test pad, taps the display's SPI bus"))
    for rc, h, col, mark, title, notes in parts:
        at, size = b_centre(*rc)
        out.append(dict(t="box", at=at, size=size, z=[zf0 - h, zf0], color=col, marking=mark, flip=True,
                        title=title, notes=notes))
    # the coax runs over the outside of the nRF9151 module (away from the board), from the top of the U.FL
    zu = zf0 - .9                               # U.FL top
    zc = zf0 - 1.3 - .4                         # past the module's outer face, plus the cable radius
    coax = [b(*p) for p in [[990, 505], [800, 480], [600, 455], [500, 445], [470, 470], [455, 530]]]
    pts = [[*xy(*coax[0]), zu - .1]] + [[*xy(*p), zc] for p in coax[1:]]
    out.append(dict(t="tube", points=pts, radius=.35, color="#111111",
                    title="Coax lead", notes="Thin coax from the U.FL connector to the antenna AC-A2016-NANO-V1.1, which is "
                                             "stuck inside the case shell (not modelled, as the case isn't)"))
    # the leg: leaves the body's edge, folds around the board's top edge to the front and runs straight
    # down to PWR3, then turns 90 degrees onto battery pad 2 (-); a short branch just past the fold lands on
    # battery pad 3 (+). Battery pad 1 is the temperature sensor and isn't touched.
    zl0, zl1 = TOP + .85, TOP + .92            # on the front, above the parts it crosses
    lx0, lx1 = 1430, 1580
    exit_y = b(1460, 930)[1]
    edge = 824
    leg = dict(color="#161618", opacity=1, title="Leg (black-coated flex)",
               notes="Branches off the body, wraps around the board's edge to the front and lands on battery pads 3 (+) "
                     "and 2 (-), so the implant is powered straight from the battery")
    out.append(dict(t="slab", poly=rect(lx0, edge, lx1, exit_y + 20), z=[zf0, zf1], **leg))
    r = (zl1 - zf1) / 2
    zc = (zl1 + zf1) / 2
    path = [[edge + 30, zf1], [edge, zf1]]
    for k in range(1, 12):
        phi = -math.pi / 2 + math.pi * k / 12
        path.append([edge - r * S * math.cos(phi), zc + r * math.sin(phi)])
    path += [[edge, zl1], [edge + 40, zl1]]
    out.append(dict(t="ribbon", x=[lx0 / S, lx1 / S], path=[[round((y - d.IMG_H) / S, 3), round(z, 3)] for y, z in path], **leg))
    for rc in ((lx0, edge, lx1, 1880), (1110, 1760, lx0, 1880), (1110, 905, lx0, 995)):
        out.append(dict(t="slab", poly=rect(*rc), z=[zl0, zl1], **leg))
    for (x, y), pid, pol in (((1165, 1820), "2", "-"), ((1165, 950), "3", "+")):
        out.append(dict(t="box", at=xy(x, y), size=[.9, .9], z=[TOP, zl0], color="#d8d8d8",
                        title=f"Leg tab on battery pad {pid}", notes=f"Solder tab on battery pad {pid}, likely battery {pol}"))
    return out


# ---- Specimen C ---------------------------------------------------------------------------------------

# test pads wired to the V03 board: VBUS and GND, SE RESET and the display's SPI lines (D/C under the glue)
WIRES_C = ["12", "23", "29", "31", "34", "35", "36"]
# white glue over the display pads and the wires running into it, traced on the photo of the back
GLUE_C = [[3827, 1435], [3774, 1644], [3566, 1771], [3260, 1802], [3101, 1717], [2888, 1575], [2675, 1527],
          [2407, 1490], [2270, 1375], [2349, 1229], [2562, 1197], [2877, 1185], [3032, 1165], [3185, 1119],
          [3439, 1131], [3695, 1273]]
COPPER = "#c47a3a"


def specimen_c():
    pads = {p["id"]: p for p in d.load_js("pads.js", "PADS")}
    bat = {q["id"]: q["polygon"] for c in d.load_js("components.js", "COMPONENTS") if c["id"] == "BAT" for q in c["pads"]}
    centre = lambda pg: [sum(v[0] for v in pg) / len(pg), sum(v[1] for v in pg) / len(pg)]
    out = []
    # the case floor under the front, where the original battery was: the cell and the V03 board lie on it
    floor = TOP + 3.65
    out.append(dict(t="box", at=xy(3010, 1450), size=[26, 16], z=[floor - 2.6, floor], color="#c3c5c9",
                    marking="XYT 261626 70mAh\n+3.7V 0.259Wh", flip=True,
                    title="Replacement battery", notes="Half-size 70 mAh lithium-polymer cell (XYT 261626, 26 x 16 x 2.6 mm) "
                                                       "in place of the original battery; its label faces the board"))
    out.append(dict(t="box", at=xy(4190, 1450), size=[1.8, 9], z=[floor - 1.2, floor], color="#d6d6d2",
                    title="Battery tabs", notes="The cell's protection board and tabs, wired to the Ledger's battery contacts"))
    out.append(dict(t="slab", poly=rect(690, 930, 1900, 1970), z=[floor - .6, floor], color="#2f5d2a", opacity=1,
                    title="Implant board (V03)", notes="Small green board marked V03, lying in the case next to the "
                    "battery, components towards the Ledger. Its wire pads are labelled for the display lines (DI, CLK, "
                    "CS, DC), reset, power and GND, plus SWD, BOOT and USB pads to program it; an eSIM sits on it, on its own small board"))
    # parts on the V03 board, placed from the photo of it in the case (its board-facing side)
    zp = floor - .6
    for (x, y), w, h, title in (((1183, 1707), 1.2, 1.8, "IC (8 pins)"), ((1372, 1748), .9, .9, "Transistor"),
                                ((845, 1776), 1.1, 1.1, "IC"), ((1147, 1381), .9, .9, "IC")):
        out.append(dict(t="box", at=xy(x, y), size=[w, h], z=[zp - .4, zp], color="#1d1d1f",
                        title=f"V03 board: {title}", notes="Small unmarked part on the implant board"))
    # the eSIM: a small carrier board soldered onto V03 by a row of 8 contacts, at the coil end
    out.append(dict(t="slab", poly=rect(715, 1346, 943, 1720), z=[zp - .45, zp - .05], color="#1c3a1a", opacity=1,
                    title="eSIM", notes="Small board soldered onto V03 by 8 contacts: the eSIM giving the implant "
                                        "its cellular identity"))
    for k in range(8):
        out.append(dict(t="box", at=xy(925, 1365 + k * 48.5), size=[.45, .3], z=[zp - .45, zp], color="#c9a54a",
                        title="eSIM contact", notes=f"Contact {k + 1} of 8 between the eSIM board and V03"))
    # a flat spiral coil antenna beside the board, at the USB end of the case
    coil = []
    for k in range(6 * 24 + 1):
        a = 2 * math.pi * k / 24
        r = 1 - .1 * k / 24
        coil.append([*xy(500 + 140 * r * math.cos(a), 1450 + 270 * r * math.sin(a)), floor - .1])
    out.append(dict(t="tube", points=coil, radius=.08, color=COPPER, title="Coil antenna",
                    notes="Flat spiral of copper wire in the end of the case, the implant's antenna"))
    # wires: from the V03 board's pad row, around the board's top edge to the back, to each test pad
    def wire(points, title, notes):
        out.append(dict(t="tube", points=points, radius=.06, color=COPPER, title=title, notes=notes))
    edge = 824
    for i, pid in enumerate(WIRES_C):
        p = pads[pid]
        sx, ex = 980 + 110 * i, 2010 + 22 * i
        mid = [(ex + p["x"]) / 2, (edge + p["y"]) / 2]
        wire([[*xy(sx, 990), floor - .6], [*xy(sx + 200, 900), TOP + 2.2], [*xy(ex, edge - 30), TOP + .8],
              [*xy(ex, edge - 40), BOT - .5], [*xy(*mid), BOT - .45 - .05 * i], [*xy(p["x"], p["y"]), BOT - .05]],
             f"Wire to TP{pid}", f"Enamelled wire from the V03 board to test pad {pid} ({p['name']})")
        out.append(dict(t="dome", at=xy(p["x"], p["y"]), r=.4, z=BOT, side="back", color="#d8d8d8",
                        title=f"Solder joint on TP{pid}", notes=f"{p['name']}: wire soldered straight onto the test pad"))
    out.append(dict(t="slab", poly=poly(GLUE_C), z=[BOT - .5, BOT - .02], color="#efefe9", opacity=1,
                    title="Glue", notes="White glue over the display test pads, holding the wires down"))
    # power: the cell feeds the Ledger through its own battery contacts, pad 3 (+) and pad 2 (-)
    for pid, start, pol in (("3", [*xy(1700, 990), floor - .6], "+"), ("2", [*xy(4190, 1800), floor - 1.2], "-")):
        cx, cy = centre(bat[pid])
        wire([start, [*xy((start[0] * S + cx) / 2, (cy + 1450) / 2), TOP + 1.6], [*xy(cx, cy), TOP + .05]],
             f"Wire to battery pad {pid}", f"Battery {pol} from the implant to the Ledger's battery pad {pid}")
        out.append(dict(t="dome", at=xy(cx, cy), r=.6, z=TOP, side="front", color="#d8d8d8",
                        title=f"Solder joint on battery pad {pid}", notes=f"Battery {pol} wire soldered to the Ledger's battery contact"))
    return out


def main():
    data = {
        "A": {"name": "Specimen A (generation 2)", "parts": specimen_a(),
              "summary": "Kapton flex over the back of the board, wrapped around to an LTE module and a replacement battery on the front",
              "source": "Tibane Labs"},
        "B": {"name": "Specimen B (generation 3)", "parts": specimen_b(),
              "summary": "Black-coated flex under the OLED with an nRF9151 modem, original battery kept",
              "source": "Tibane Labs"},
        "C": {"name": "Specimen C (generation 1)", "parts": specimen_c(),
              "summary": "Hand-wired: a small board, a coil antenna and a half-size battery in the case, enamelled "
                         "wires to the test pads and battery contacts",
              "source": "@Us_Chan007"},
    }
    path = os.path.join(HERE, "implants.js")
    with open(path, "w") as f:
        f.write("// Approximate 3D models of the implants found in Ledger Nano X devices, for viewer3d.html.\n")
        f.write("// Generated by implants.py from photographs; see that file for sources and caveats.\n")
        f.write("window.IMPLANTS = " + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";\n")
    print("wrote", path, {k: len(v["parts"]) for k, v in data.items()})


if __name__ == "__main__":
    main()
