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
    board, mapped onto the board by the eight solder joints on known test pads.
  Specimen B (generation 3): a black-coated flex cut to fit under the OLED on the back of the board, around
    the board-to-board connector, carrying an nRF9151 module, a scraped MCU and eSIM and a U.FL connector,
    with a coax lead to an antenna stuck on the inside wall of the case. Placed from the photo of the board
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
TAP_A = [[1604,2004],[1584,1990],[1574,1939],[1532,1916],[1451,1975],[1388,1963],[1324,1997],[1260,1957],[1196,1993],
    [1173,1990],[1155,1931],[1216,1875],[1226,1821],[1216,1787],[1185,1764],[1065,1761],[1019,1786],[985,1873],[1012,1947],
    [974,1981],[923,1949],[939,1896],[917,1853],[855,1822],[777,1852],[752,1827],[779,1785],[783,1722],[854,1737],[904,1706],
    [905,1652],[846,1609],[847,1581],[873,1570],[1004,1579],[1042,1543],[1038,1370],[997,1313],[1004,1245],[951,1208],
    [952,1180],[1019,1118],[1067,1031],[1102,997],[1249,1060],[1301,1038],[1358,1041],[1403,965],[1465,988],[1505,971],
    [1532,926],[1536,824],[1856,824],[1862,851],[1912,900],[1874,942],[1873,1001],[1920,1055],[1951,1067],[1983,1056],
    [2007,1013],[1977,942],[1933,897],[1985,858],[2052,926],[2067,1008],[2191,1068],[2491,1070],[2574,1050],[2757,1049],
    [2858,995],[2870,964],[2854,922],[2863,905],[2998,900],[3020,923],[2987,962],[2986,1007],[3034,1047],[3087,1065],
    [3068,1169],[3090,1200],[3121,1212],[3173,1181],[3173,1071],[3268,1043],[3297,1012],[3313,856],[3291,800],[3306,777],
    [3415,778],[3387,860],[3392,888],[3417,914],[3505,945],[3539,934],[3563,892],[3514,801],[3517,778],[3737,782],
    [3751,802],[3744,865],[3791,896],[3943,891],[3996,826],[4043,880],[4143,881],[4181,952],[4255,949],[4278,972],
    [4257,1003],[4174,1011],[4137,1102],[4024,1081],[3977,1112],[3965,1143],[3987,1186],[4046,1200],[4112,1178],
    [4131,1135],[4153,1138],[4164,1158],[4158,1178],[4129,1192],[4128,1333],[4190,1393],[4169,1438],[4170,1475],
    [4195,1501],[4249,1512],[4257,1549],[4225,1574],[4177,1560],[4142,1571],[4122,1599],[4123,1656],[4171,1687],
    [4256,1682],[4329,1629],[4376,1683],[4471,1681],[4493,1703],[4466,1740],[4450,1808],[4332,1838],[4274,1883],
    [4252,1860],[4262,1798],[4237,1773],[4200,1770],[4157,1789],[4094,1766],[4034,1766],[3985,1797],[3968,1890],
    [3922,1907],[3840,1886],[3797,1903],[3617,1905],[3536,1927],[3465,1913],[3422,1929],[3345,1912],[3294,1929],
    [3234,1911],[3182,1934],[3128,1911],[3071,1933],[3017,1910],[2726,1908],[2671,1934],[2606,1911],[2137,1914],
    [2106,1925],[2062,1976],[1957,1918],[1880,1915],[1849,1926],[1808,1974],[1741,1994],[1656,1982]]
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
    out.append(dict(t="ribbon", x=[1536 / S, 1856 / S], path=[[round((y - d.IMG_H) / S, 3), round(z, 3)] for y, z in path],
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
    out.append(dict(t="slab", poly=poly(body), holes=[poly(window)], z=[zf0, zf1], color="#161618", opacity=1,
                    title="Implant flex (black-coated)", notes="Orange polyimide flex painted black, cut to fit under the OLED "
                    "around the Ledger's own parts; the window fits over the board-to-board connector"))
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
    zc = zf0 - 1.0
    coax = [b(*p) for p in [[990, 505], [800, 480], [600, 455], [500, 445], [470, 470], [455, 530]]]
    out.append(dict(t="tube", points=[[*xy(*p), zc] for p in coax], radius=.35, color="#111111",
                    title="Coax lead", notes="Thin coax from the U.FL connector to the antenna on the case wall"))
    # the antenna is stuck on the case wall along the top edge, outside the board
    x0, x1 = b(1000, 500)[0], b(150, 500)[0]
    out.append(dict(t="box", at=xy((x0 + x1) / 2, 690), size=[abs(x1 - x0) / S, .12], z=[-2.4, 2.4], color="#121212",
                    title="Antenna AC-A2016-NANO-V1.1", notes="Flexible printed antenna made for the Nano X, stuck along "
                    "the inside wall of the case shell (position approximate, as the case is not modelled)"))
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
