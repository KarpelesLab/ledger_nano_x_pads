"""Export nanox.kicad_pcb as overlay.js for flip.html: tracks, vias, pads and the board outline per side,
in photo pixel coordinates, so the reconstruction can be laid over the photos. Reads the board file,
so edits made in KiCad show up in the overlay.
"""
import json
import math
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nanox_data as d  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def px(v):
    """A KiCad point to photo pixels."""
    X, Y = pcbnew.ToMM(v.x), pcbnew.ToMM(v.y)
    return [round(X * d.PX_PER_MM, 1), round(d.IMG_H - Y * d.PX_PER_MM, 1)]


def L(mm):
    return round(mm * d.PX_PER_MM, 1)


def drc_issues():
    """KiCad's design rule check, reduced to what matters for the reconstruction: copper of two nets
    touching, and items that should be connected but are not. One entry per pair of items."""
    import re
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        rep = os.path.join(tmp, "drc.json")
        subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "-o", rep, os.path.join(HERE, "nanox.kicad_pcb")],
                       capture_output=True)
        r = json.load(open(rep))
    def short(desc):
        return re.sub(r", length [\d.]+ mm| on [FB]\.Cu.*| on F\.Cu - .*| on B\.Cu - .*", "", desc)
    def at(item):
        return [round(item["pos"]["x"] * d.PX_PER_MM), round(d.IMG_H - item["pos"]["y"] * d.PX_PER_MM)]
    issues, seen = [], set()
    for v in r["violations"]:
        if v["type"] != "shorting_items":
            continue
        items = [short(i["description"]) for i in v["items"]]
        key = tuple(sorted(items))
        if key in seen:
            continue
        seen.add(key)
        side = "front" if "F.Cu" in v["items"][0]["description"] else "back"
        issues.append({"kind": "overlap", "side": side, "at": at(v["items"][0]), "items": items})
    for v in r["unconnected_items"]:
        items = [short(i["description"]) for i in v["items"]]
        side = "front" if "F.Cu" in v["items"][0]["description"] else "back"
        issues.append({"kind": "unconnected", "side": side, "at": at(v["items"][0]), "to": at(v["items"][-1]), "items": items})
    issues.sort(key=lambda i: (i["kind"], i["side"], i["at"][0]))
    return issues


def main():
    board = pcbnew.LoadBoard(os.path.join(HERE, "nanox.kicad_pcb"))
    out = {"front": [], "back": [], "outline": []}
    side_of = {pcbnew.F_Cu: "front", pcbnew.B_Cu: "back"}
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            item = {"t": "via", "net": t.GetNetname(), "at": px(t.GetPosition()), "d": L(pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)))}
            out["front"].append(item)
            out["back"].append(item)
        elif t.GetLayer() in side_of:
            out[side_of[t.GetLayer()]].append({"t": "track", "net": t.GetNetname(), "a": px(t.GetStart()), "b": px(t.GetEnd()),
                                               "w": L(pcbnew.ToMM(t.GetWidth()))})
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            side = "front" if pad.IsOnLayer(pcbnew.F_Cu) else "back"
            c = px(pad.GetPosition())
            w, h = L(pcbnew.ToMM(pad.GetSize(pad.GetPrincipalLayer()).x)), L(pcbnew.ToMM(pad.GetSize(pad.GetPrincipalLayer()).y))
            item = {"t": "pad", "ref": fp.GetReference(), "num": pad.GetNumber(), "net": pad.GetNetname()}
            if pad.GetShape(pad.GetPrincipalLayer()) == pcbnew.PAD_SHAPE_CIRCLE:
                item.update(at=c, r=round(w / 2, 1))
            else:
                # KiCad angles turn counter-clockwise on a y-down board; the photo frame flips y, so they turn clockwise here
                a = math.radians(pad.GetOrientation().AsDegrees())
                ca, sa = math.cos(a), math.sin(a)
                corners = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
                item["poly"] = [[round(c[0] + x * ca - y * sa, 1), round(c[1] + x * sa + y * ca, 1)] for x, y in corners]
            out[side].append(item)
    # filled copper pours, as SVG paths (outer outline plus holes) per side; needs a filled board
    out["fill"] = {"front": [], "back": []}
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        for layer, side in side_of.items():
            if not z.IsOnLayer(layer):
                continue
            polys = z.GetFilledPolysList(layer)
            for i in range(polys.OutlineCount()):
                rings = [polys.Outline(i)] + [polys.Hole(i, j) for j in range(polys.HoleCount(i))]
                d_ = ""
                for ring in rings:
                    pts = [px(ring.CPoint(k)) for k in range(ring.PointCount())]
                    d_ += "M" + "L".join(f"{x:.0f},{y:.0f}" for x, y in pts) + "Z"
                out["fill"][side].append(d_)
    for s in board.GetDrawings():
        if s.GetLayer() == pcbnew.Edge_Cuts and s.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            out["outline"].append([px(s.GetStart()), px(s.GetEnd())])
    out["issues"] = drc_issues()
    path = os.path.join(HERE, "overlay.js")
    with open(path, "w") as f:
        f.write("// KiCad reconstruction for flip.html, exported from nanox.kicad_pcb by export_overlay.py.\n")
        f.write("// Coordinates are pixels in the 5376x3024 photos.\n")
        f.write("window.KICAD = " + json.dumps(out, separators=(",", ":")) + ";\n")
    print("wrote", path, {k: len(v) for k, v in out.items() if k != "fill"}, "fill", {k: len(v) for k, v in out["fill"].items()})


if __name__ == "__main__":
    main()
