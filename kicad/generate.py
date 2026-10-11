"""Generate nanox.kicad_pcb from the flip.html overlay data: board outline, footprints with pads where
they are in the photos, our traces as tracks and vias, and the nets they form.

Run with the Python that has KiCad's pcbnew module. Refuses to overwrite an existing board, which may
hold edits made in KiCad, unless --force is given.
"""
import math
import os
import sys
import uuid
import json

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nanox_data as d  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "nanox.kicad_pcb")
# stable ids, so the generated schematic links to the same footprints
NS = uuid.UUID("6f1c3e1e-2b7a-4a52-9d0c-7a0d1c5e9b11")


def symbol_uuid(ref):
    return str(uuid.uuid5(NS, "symbol:" + ref))


def mm(x, y):
    """Photo pixels to a KiCad point."""
    X, Y = d.to_mm(x, y)
    return pcbnew.VECTOR2I(pcbnew.FromMM(X), pcbnew.FromMM(Y))


def size_mm(w, h):
    return pcbnew.VECTOR2I(pcbnew.FromMM(max(w, 0.05)), pcbnew.FromMM(max(h, 0.05)))


def deg(a):
    return pcbnew.EDA_ANGLE(a, pcbnew.DEGREES_T)


def layers(side):
    if side == "front":
        return pcbnew.F_Cu, [pcbnew.F_Cu, pcbnew.F_Mask, pcbnew.F_Paste], pcbnew.F_SilkS, pcbnew.F_Fab, pcbnew.F_CrtYd
    return pcbnew.B_Cu, [pcbnew.B_Cu, pcbnew.B_Mask, pcbnew.B_Paste], pcbnew.B_SilkS, pcbnew.B_Fab, pcbnew.B_CrtYd


def lset(ids):
    s = pcbnew.LSET()
    for i in ids:
        s.AddLayer(i)
    return s


def outline_points(c, pads):
    """The outline of a component in photo pixels."""
    if "corners" in c:
        return c["corners"]
    if "outline" in c:
        return c["outline"]
    if c.get("rect"):
        x, y, w, h = c["rect"]
        return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
    xs = [v[0] for p in pads for v in (p.get("poly") or [[p["x"], p["y"]]])]
    ys = [v[1] for p in pads for v in (p.get("poly") or [[p["x"], p["y"]]])]
    return [[min(xs), min(ys)], [max(xs), min(ys)], [max(xs), max(ys)], [min(xs), max(ys)]]


def add_poly(fp, pts, layer, width=0.08):
    for a, b in zip(pts, pts[1:] + pts[:1]):
        s = pcbnew.PCB_SHAPE(fp, pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(layer)
        s.SetStart(mm(*a))
        s.SetEnd(mm(*b))
        s.SetWidth(pcbnew.FromMM(width))
        fp.Add(s)


def chip_angle(c):
    """Rotation of a chip's first edge, in KiCad degrees (counter-clockwise, y up on screen is -y)."""
    (x0, y0), (x1, y1) = [d.to_mm(*p) for p in c["corners"][:2]]
    return math.degrees(math.atan2(-(y1 - y0), x1 - x0))


def make_footprint(board, ref, value, side, center, pads, outline, nets_by_name, desc=""):
    cu, pad_layers, silk, fab, crtyd = layers(side)
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetLayer(cu)
    fp.SetPosition(mm(*center))
    fp.SetPath(pcbnew.KIID_PATH("/" + symbol_uuid(ref)))
    if desc:
        fp.SetLibDescription(desc)
    board.Add(fp)
    fp.Reference().SetLayer(silk)
    fp.Reference().SetTextSize(size_mm(0.5, 0.5))
    fp.Reference().SetTextThickness(pcbnew.FromMM(0.08))
    fp.Reference().SetPosition(mm(*center))
    fp.Reference().SetMirrored(side == "back")
    fp.Value().SetLayer(fab)
    fp.Value().SetVisible(False)
    for p in pads:
        pad = pcbnew.PAD(fp)
        pad.SetNumber(p["number"])
        pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        pad.SetLayerSet(lset(pad_layers))
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE if p["shape"] == "circle" else pcbnew.PAD_SHAPE_RECT)
        pad.SetSize(size_mm(*p["size"]))
        fp.Add(pad)
        pad.SetPosition(mm(*p["at"]))
        pad.SetOrientation(deg(p.get("angle", 0)))
        if p.get("net"):
            pad.SetNet(nets_by_name[p["net"]])
    add_poly(fp, outline, fab)
    return fp


def main():
    if os.path.exists(OUT) and "--force" not in sys.argv:
        sys.exit(f"{OUT} exists and may hold KiCad edits; pass --force to regenerate it")
    traces, comps, pads = d.load()
    trace_net, pad_net, merges = d.nets(traces, pads)
    for kept, members in merges:
        print("merged into", kept, ":", ", ".join(members))

    board = pcbnew.BOARD()
    nets_by_name = {}
    for name in sorted(set(trace_net.values()) | {n for n in pad_net if n}):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets_by_name[name] = ni

    # board outline
    outline = json.load(open(os.path.join(HERE, "outline.json")))
    for a, b in zip(outline, outline[1:] + outline[:1]):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(mm(*a))
        s.SetEnd(mm(*b))
        s.SetWidth(pcbnew.FromMM(0.1))
        board.Add(s)

    S = d.PX_PER_MM
    net_of = {id(p): n for p, n in zip(pads, pad_net)}

    # test pads: round pads on their side, named TP01..TP40
    for p in (p for p in pads if p["kind"] == "testpad"):
        dia = 2 * p["r"] / S
        make_footprint(board, "TP" + p["id"], p.get("name") or "TestPoint", p["side"], (p["x"], p["y"]),
                       [dict(number="1", shape="circle", size=(dia, dia), at=(p["x"], p["y"]), net=net_of[id(p)])],
                       [[p["x"] - p["r"], p["y"] - p["r"]], [p["x"] + p["r"], p["y"] - p["r"]],
                        [p["x"] + p["r"], p["y"] + p["r"]], [p["x"] - p["r"], p["y"] + p["r"]]], nets_by_name)

    # components: chips with computed pins, parts with drawn pads, passives, and outline-only parts
    for c in comps:
        cpads = [p for p in pads if p["kind"] == "pin" and p["chip"] is c]
        out = []
        if d.pin_counts(c):
            ang = chip_angle(c)
            for p in cpads:
                if p.get("ep"):
                    e = c["exposedPad"]
                    out.append(dict(number=p["id"], shape="rect", size=(e, e), at=(p["x"], p["y"]),
                                    angle=ang, net=net_of[id(p)]))
                else:
                    # pad 0.25 mm across, 0.6 mm deep, turned to point out of its edge; the photo-derived
                    # position is a little off, so keep pads narrow enough not to touch their neighbours
                    out.append(dict(number=p["id"], shape="rect", size=(0.6, 0.25), at=(p["x"], p["y"]),
                                    angle=ang + (90 if p["edge"] % 2 == 0 else 0), net=net_of[id(p)]))
        else:
            for p in cpads:
                if p.get("body"):
                    continue
                xs, ys = [v[0] for v in p["poly"]], [v[1] for v in p["poly"]]
                out.append(dict(number=p["id"], shape="rect",
                                size=((max(xs) - min(xs)) / S, (max(ys) - min(ys)) / S),
                                at=((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2), net=net_of[id(p)]))
        pts = outline_points(c, cpads)
        center = (sum(v[0] for v in pts) / len(pts), sum(v[1] for v in pts) / len(pts))
        value = c.get("part", "") if not c.get("passive") else {"R": "R", "C": "C"}.get(c["passive"], "?")
        make_footprint(board, d.ref(c["id"]), value, c["side"], center, out, pts, nets_by_name,
                       desc=(c.get("package", "") + "; " + c.get("notes", "")).strip("; "))

    # tracks and vias
    for i, t in enumerate(traces):
        net = nets_by_name[trace_net[i]]
        w = pcbnew.FromMM(t.get("width", 20) / S)
        for q in t["paths"]:
            layer = pcbnew.F_Cu if q["side"] == "front" else pcbnew.B_Cu
            for a, b in zip(q["points"], q["points"][1:]):
                if a == b:
                    continue
                tr = pcbnew.PCB_TRACK(board)
                tr.SetStart(mm(*a))
                tr.SetEnd(mm(*b))
                tr.SetWidth(w)
                tr.SetLayer(layer)
                tr.SetNet(net)
                board.Add(tr)
        for v in t.get("vias", []):
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(mm(*v))
            via.SetDrill(pcbnew.FromMM(0.2))
            via.SetWidth(pcbnew.FromMM(0.45))
            via.SetNet(net)
            board.Add(via)

    # ground runs in an inner plane, which the photos cannot show: model it as a filled GND zone on an
    # inner layer, with each ground connection made through the vias and pins we traced
    board.SetCopperLayerCount(4)

    def polygon(pts):
        chain = pcbnew.SHAPE_LINE_CHAIN()
        for x, y in pts:
            chain.Append(mm(x, y))
        chain.SetClosed(True)
        return chain

    # GND pours: the inner plane (assumed) and the copper fill visible on both outer layers in the
    # bare photos. Islands are kept, as not every stitching via that ties them to ground is traced.
    for layer, name in ((pcbnew.In1_Cu, "GND plane (assumed)"), (pcbnew.F_Cu, "GND pour, front"), (pcbnew.B_Cu, "GND pour, back")):
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        zone.SetNet(nets_by_name["GND"])
        zone.SetIsRuleArea(False)
        zone.Outline().AddOutline(polygon(outline))
        zone.SetZoneName(name)
        zone.SetLocalClearance(pcbnew.FromMM(0.15))
        zone.SetMinThickness(pcbnew.FromMM(0.12))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
        zone.SetAssignedPriority(0 if layer == pcbnew.In1_Cu else 1)
        board.Add(zone)

    # no copper fill around the chip antenna: a window seen on both sides of the bare board, from the
    # antenna up to y 1530 (front) / 1550 (back) in the photos; applied to the inner plane too, as is usual
    for layers, top in (([pcbnew.F_Cu, pcbnew.In1_Cu], 1530), ([pcbnew.B_Cu, pcbnew.In2_Cu], 1550)):
        keep = pcbnew.ZONE(board)
        keep.SetIsRuleArea(True)
        keep.SetLayerSet(lset(layers))
        keep.SetDoNotAllowZoneFills(True)
        keep.SetDoNotAllowTracks(False)
        keep.SetDoNotAllowVias(False)
        keep.SetDoNotAllowPads(False)
        keep.SetDoNotAllowFootprints(False)
        keep.Outline().AddOutline(polygon([[3620, top], [3965, top], [3965, d.IMG_H], [3620, d.IMG_H]]))
        keep.SetZoneName("Antenna keep-out")
        board.Add(keep)
    for t in traces:
        if t["name"] != "GND":
            continue
        # each ground pin drops into the plane through a via, marked as assumed
        for q in t.get("pins", []):
            via = pcbnew.PCB_VIA(board)
            # blind, from the pin's side down to the plane only, so it cannot touch copper on the other side
            via.SetViaType(pcbnew.VIATYPE_BLIND)
            via.SetLayerPair(pcbnew.F_Cu if q["side"] == "front" else pcbnew.B_Cu, pcbnew.In1_Cu)
            via.SetPosition(mm(q["x"], q["y"]))
            # small enough to sit on a 0.5 mm pitch pin without touching its neighbours' tracks
            via.SetDrill(pcbnew.FromMM(0.1))
            via.SetWidth(pcbnew.FromMM(0.2))
            via.SetNet(nets_by_name["GND"])
            board.Add(via)
    # filling the zone from Python crashes KiCad 10's pcbnew module: it is filled on first open in KiCad,
    # or by kicad-cli pcb drc --refill-zones

    board.Save(OUT)
    print("wrote", OUT, "with", len(nets_by_name), "nets")


if __name__ == "__main__":
    main()
