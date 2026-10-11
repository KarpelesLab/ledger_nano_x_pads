"""Export the reconstruction as scene.js for viewer3d.html: the board outline and thickness, copper
(tracks, vias, pads, pours), component bodies with their markings, and the details shown on hover
(net names and purposes, pin names, part descriptions).

Coordinates are millimetres in the viewer's frame: x right and y up as in KiCad's top view, z up out of
the front side, with the board centred on its middle plane. Reads nanox.kicad_pcb after filling, so run
it from regenerate.sh.
"""
import json
import math
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nanox_data as d  # noqa: E402
import models3d as m3d  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
S = d.PX_PER_MM


def P(v):
    """A KiCad point (y down) to viewer x, y (y up), rounded."""
    return [round(pcbnew.ToMM(v.x), 3), round(-pcbnew.ToMM(v.y), 3)]


def photo(x, y):
    """Photo pixels to viewer x, y: the same point KiCad has, with its y axis turned up."""
    X, Y = d.to_mm(x, y)
    return [round(X, 3), round(-Y, 3)]


# body height (mm) and colour of the parts that are not in models3d's tables
def passive_look(kind, length):
    h = .3 if length < .85 else .35 if length < 1.35 else .45 if length < 1.85 else .6
    return h, {"R": "#1a1a1a", "C": "#8a6a4a"}.get(kind, "#d8d8d2")


def main():
    traces, comps, pads = d.load()
    trace_net, pad_net, _ = d.nets(traces, pads)
    board = pcbnew.LoadBoard(os.path.join(HERE, "nanox.kicad_pcb"))
    thick = pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness())

    # net details: the traces making each net, with their purpose and notes
    nets = {}
    for i, t in enumerate(traces):
        n = nets.setdefault(trace_net[i], {"traces": []})
        n["traces"].append({k: t[k] for k in ("name", "purpose", "notes") if t.get(k)})
    # pin names, keyed by footprint reference and pad number
    pin_names = {}
    for p in pads:
        ref = ("TP" + p["id"]) if p["kind"] == "testpad" else d.ref(p["chip"]["id"])
        num = "1" if p["kind"] == "testpad" else p["id"]
        if p.get("name"):
            pin_names[(ref, num)] = p["name"]

    scene = {"thickness": thick, "outline": [], "tracks": [], "vias": [], "pads": [], "fills": [], "parts": [], "nets": nets}
    outline = json.load(open(os.path.join(HERE, "outline.json")))
    scene["outline"] = [photo(x, y) for x, y in outline]

    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            scene["vias"].append({"at": P(t.GetPosition()), "d": round(pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)), 3),
                                  "drill": round(pcbnew.ToMM(t.GetDrillValue()), 3), "net": t.GetNetname()})
        else:
            scene["tracks"].append({"a": P(t.GetStart()), "b": P(t.GetEnd()), "w": round(pcbnew.ToMM(t.GetWidth()), 3),
                                    "side": "front" if t.GetLayer() == pcbnew.F_Cu else "back", "net": t.GetNetname()})

    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        for layer, side in ((pcbnew.F_Cu, "front"), (pcbnew.B_Cu, "back")):
            if not z.IsOnLayer(layer):
                continue
            polys = z.GetFilledPolysList(layer)
            for i in range(polys.OutlineCount()):
                rings = [polys.Outline(i)] + [polys.Hole(i, j) for j in range(polys.HoleCount(i))]
                scene["fills"].append({"side": side, "net": z.GetNetname(),
                                       "rings": [[P(r.CPoint(k)) for k in range(r.PointCount())] for r in rings]})

    meta = {d.ref(c["id"]): c for c in comps}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        side = "back" if fp.IsFlipped() else "front"
        for pad in fp.Pads():
            lay = pad.GetPrincipalLayer()
            sz = pad.GetSize(lay)
            item = {"ref": ref, "num": pad.GetNumber(), "net": pad.GetNetname(), "side": side, "at": P(pad.GetPosition()),
                    "w": round(pcbnew.ToMM(sz.x), 3), "h": round(pcbnew.ToMM(sz.y), 3),
                    "rot": round(pad.GetOrientation().AsDegrees(), 2),
                    "circle": pad.GetShape(lay) == pcbnew.PAD_SHAPE_CIRCLE}
            if (ref, pad.GetNumber()) in pin_names:
                item["pin"] = pin_names[(ref, pad.GetNumber())]
            scene["pads"].append(item)
        if ref.startswith("TP"):
            continue
        c = meta.get(ref)
        if not c:
            continue
        # body outline from the footprint's fab outline, in photo pixels
        if c.get("rect"):
            x, y, w, h = c["rect"]
            poly_px = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
        else:
            poly_px = c.get("corners") or c.get("outline")
            if not poly_px:
                pts = [v for q in c.get("pads", []) for v in q["polygon"]]
                xs, ys = [v[0] for v in pts], [v[1] for v in pts]
                poly_px = [[min(xs), min(ys)], [max(xs), min(ys)], [max(xs), max(ys)], [min(xs), max(ys)]]
        cid = c["id"]
        part = {"ref": ref, "side": side, "outline": [photo(x, y) for x, y in poly_px],
                "title": c.get("part", ""), "package": c.get("package", ""), "notes": c.get("notes", "")}
        if c.get("passive"):
            L = max(c["rect"][2], c["rect"][3]) / S
            part["height"], part["color"] = passive_look(c["passive"], L)
            part["caps"] = c["axis"]
            # the body is inset from the solder: about 75% of the measured box
            part["inset"] = .12
            if c["passive"] not in "RC":
                part["color"] = "#ecece6" if cid in ("X1", "X4") else "#9a9a9a"
        elif cid in m3d.LIBRARY:
            part["height"], part["color"] = m3d.LIBRARY_HEIGHT, "#2a2a2c"
            part["pin1"] = photo(*c["corners"][0])
            if cid in m3d.LIBRARY_MARKINGS:
                text, (i, j) = m3d.LIBRARY_MARKINGS[cid]
                a, b = photo(*c["corners"][i]), photo(*c["corners"][j])
                part["marking"] = {"text": text, "angle": math.atan2(b[1] - a[1], b[0] - a[0])}
        elif cid in m3d.CUSTOM:
            col, h, text = m3d.CUSTOM[cid]
            part["height"] = h
            part["color"] = "#%02x%02x%02x" % tuple(round(v * 255) for v in col)
            if text:
                o = part["outline"]
                e = [(o[(k + 1) % len(o)][0] - o[k][0], o[(k + 1) % len(o)][1] - o[k][1]) for k in range(len(o))]
                k = max(range(len(e)), key=lambda k: math.hypot(*e[k]))
                ang = math.atan2(e[k][1], e[k][0])
                if math.cos(ang) < -1e-6 or (abs(math.cos(ang)) < 1e-6 and math.sin(ang) < 0):
                    ang += math.pi
                part["marking"] = {"text": text, "angle": ang}
        else:
            continue
        scene["parts"].append(part)

    path = os.path.join(HERE, "scene.js")
    with open(path, "w") as f:
        f.write("// Scene for viewer3d.html, exported from nanox.kicad_pcb and the overlay data by export_scene.py.\n")
        f.write("window.SCENE = " + json.dumps(scene, separators=(",", ":"), ensure_ascii=False) + ";\n")
    print("wrote", path, {k: len(v) for k, v in scene.items() if isinstance(v, (list, dict))})


if __name__ == "__main__":
    main()
