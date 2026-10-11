"""Write implants.js for viewer3d.html: approximate 3D models of the two hardware implants Tibane Labs
found in Ledger Nano X devices (https://tibane.net, "Ledger Nano X: the spy implant"), placed on the
reconstructed board.

Everything here is measured from Tibane Labs' photographs, so it is approximate (to about a millimetre)
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
    with a coax lead to an antenna stuck inside the case (not modelled), and a leg that wraps around the bottom
    edge to the battery contacts on the front. Placed from the photo of the board
    with the screen removed, mapped onto the board by the USB shell joints, the two buttons and the BTB
    connector.

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
TAP_A = [[1568,1923],[1568,1973],[1188,1973],[1188,1775],[996,1775],[996,1965],[920,1965],[920,1840],[768,1840],
    [768,1714],[876,1714],[876,1562],[1020,1562],[1020,1037],[1380,1037],[1380,968],[1520,968],[1520,824],
    [1888,824],[1888,1037],[1970,1037],[1970,878],[2026,878],[2026,1050],[2860,1050],[2860,902],[2992,902],
    [2992,1036],[3078,1036],[3078,1193],[3173,1193],[3173,1042],[3302,1042],[3302,778],[3404,778],[3404,917],
    [3540,917],[3540,780],[3764,780],[3764,894],[3970,894],[3970,923],[4156,923],[4156,1092],[3994,1092],
    [3994,1166],[4146,1166],[4146,1363],[4180,1363],[4180,1536],[4132,1536],[4132,1665],[4472,1665],[4472,1846],
    [4256,1846],[4256,1770],[3978,1770],[3978,1923]]
# solder joints of the tap layer, on these test pads
JOINTS_A = ["35", "34", "36", "29", "31", "14", "03", "07"]


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

# photo pixels of camo-under-screen.jpg to back-photo pixels, fitted on the USB shell joints, both buttons
# and the BTB connector (about 5 photo px residual)
MB = [[-2.7177, 0.0568], [0.29615, 2.72016], [5240.75793, -620.81032]]


def b(px, py):
    return [px * MB[0][0] + py * MB[1][0] + MB[2][0], px * MB[0][1] + py * MB[1][1] + MB[2][1]]


def b_rect(x0, y0, x1, y1):
    return poly([b(x0, y0), b(x1, y0), b(x1, y1), b(x0, y1)])


def b_centre(x0, y0, x1, y1):
    cx, cy = b((x0 + x1) / 2, (y0 + y1) / 2)
    w = math.dist(b(x0, y0), b(x1, y0)) / S
    h = math.dist(b(x0, y0), b(x0, y1)) / S
    return xy(cx, cy), [round(w, 3), round(h, 3)]


def specimen_b():
    out = []
    zf0, zf1 = BOT - .14, BOT - .06            # body, on the back under the OLED
    body = [b(*p) for p in [[165, 575], [458, 575], [458, 495], [1540, 490], [1540, 930], [165, 930]]]
    window = [b(*p) for p in [[288, 632], [388, 632], [388, 842], [288, 842]]]
    # cut-outs around three of the Ledger's capacitors, which key the flex into place: holes around C30
    # and C31, and a notch in the edge around C32, each 0.15 mm clear of the part
    caps = {q["id"]: q["box"] for q in d.load_js("passives.js", "PASSIVES") if q["id"] in ("C30", "C31", "C32")}
    m = 13
    holes = [window] + [[[x - m, y - m], [x + w + m, y - m], [x + w + m, y + h + m], [x - m, y + h + m]]
                        for x, y, w, h in (caps["C30"], caps["C31"])]
    (x0, y0), (x1, y1) = body[0], body[1]
    cx, cy, cw, ch = caps["C32"]
    at = lambda x: y0 + (y1 - y0) * (x0 - x) / (x0 - x1)
    body[1:1] = [[cx + cw + m, at(cx + cw + m)], [cx + cw + m, cy + ch + m], [cx - m, cy + ch + m], [cx - m, at(cx - m)]]
    out.append(dict(t="slab", poly=poly(body), holes=[poly(h) for h in holes], z=[zf0, zf1], color="#161618", opacity=1,
                    title="Implant flex (black-coated)", notes="Orange polyimide flex painted black, cut to fit under the OLED "
                    "around the Ledger's own parts: the window fits over the board-to-board connector, and cut-outs around C30, C31 and "
                    "C32 key it into place so it can't be misaligned"))
    parts = [
        ((772, 565, 1170, 925), 1.3, "#cfcfcc", "Nordic\nnRF9151", "Nordic nRF9151 module",
         "LTE-M / NB-IoT modem with its own regulatory markings, left unscraped"),
        ((1235, 570, 1480, 820), .75, "#2a2a2c", "", "MCU (markings scraped)",
         "QFN microcontroller with its top surface abraded; more pins than Specimen A's STM32"),
        ((525, 770, 735, 930), .6, "#2a2a2c", "", "eSIM (markings scraped)",
         "MFF2 eSIM, 5 x 6 mm, top surface abraded"),
        ((955, 475, 1025, 535), .9, "#c9a54a", "", "U.FL connector", "Antenna connector for the coax lead"),
    ]
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
    # the leg: leaves the body's bottom edge, folds around the board's bottom edge to the front and runs
    # under the battery contacts, ending in two tabs on battery + (pad 3) and battery - (pad 1)
    zl0, zl1 = TOP + .85, TOP + .92            # on the front, above the parts it crosses
    exit_x, exit_y = b(1460, 930)
    lx0, lx1 = exit_x - 50, exit_x + 50
    edge = 2074
    leg = dict(color="#161618", opacity=1, title="Leg (black-coated flex)",
               notes="Branches off the body, wraps around the board's bottom edge to the front and lands on the battery "
                     "contacts, so the implant is powered straight from the battery (+ and -)")
    out.append(dict(t="slab", poly=rect(lx0, exit_y - 20, lx1, edge), z=[zf0, zf1], **leg))
    r = (zl1 - zf1) / 2
    zc = (zl1 + zf1) / 2
    path = [[edge - 30, zf1], [edge, zf1]]
    for k in range(1, 12):
        phi = -math.pi / 2 + math.pi * k / 12
        path.append([edge + r * S * math.cos(phi), zc + r * math.sin(phi)])
    path += [[edge, zl1], [edge - 40, zl1]]
    out.append(dict(t="ribbon", x=[lx0 / S, lx1 / S], path=[[round((y - d.IMG_H) / S, 3), round(z, 3)] for y, z in path], **leg))
    out.append(dict(t="slab", poly=poly([[lx1, edge], [1015, edge], [1015, 940], [1100, 940], [1100, 1960], [lx1, 1960]]),
                    z=[zl0, zl1], **leg))
    out.append(dict(t="slab", poly=rect(930, 1780, 1015, 1880), z=[zl0, zl1], **leg))
    for (x, y), pol in (((975, 1830), "-"), ((1060, 952), "+")):
        out.append(dict(t="box", at=xy(x, y), size=[.9, .9], z=[TOP, zl0], color="#d8d8d8",
                        title=f"Leg tab on battery {pol}", notes=f"Solder tab on the battery {'+' if pol == '+' else '-'} contact "
                                                          "(battery pad 3 is likely +, pad 1 likely -)"))
    return out


def main():
    data = {
        "A": {"name": "Specimen A (generation 2)", "parts": specimen_a(),
              "summary": "Kapton flex over the back of the board, wrapped around to an LTE module and a replacement battery on the front"},
        "B": {"name": "Specimen B (generation 3)", "parts": specimen_b(),
              "summary": "Black-coated flex under the OLED with an nRF9151 modem, original battery kept"},
    }
    path = os.path.join(HERE, "implants.js")
    with open(path, "w") as f:
        f.write("// Approximate 3D models of the implants found in Ledger Nano X devices, for viewer3d.html.\n")
        f.write("// Generated by implants.py from Tibane Labs' photographs; see that file for sources and caveats.\n")
        f.write("window.IMPLANTS = " + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";\n")
    print("wrote", path, {k: len(v["parts"]) for k, v in data.items()})


if __name__ == "__main__":
    main()
