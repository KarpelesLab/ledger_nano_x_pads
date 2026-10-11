"""Board data shared by the KiCad generators: reads the overlay data files of flip.html, computes chip
pins the same way the page does, and works out which pads each trace connects to and the nets.

Coordinates are pixels in the 5376x3024 photos, in the frame of the back photo (the front photo is
mirrored to match). to_mm() turns them into KiCad millimetres seen from the top of the board.
"""
import json
import math
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_W, IMG_H = 5376, 3024
# pixels per millimetre, from the 7 mm MCU package outline
PX_PER_MM = 84.0


def ref(pid):
    """KiCad reference for a component id: references must end in a number, so MCU becomes MCU1."""
    return pid if pid[-1:].isdigit() else pid + "1"


def to_mm(x, y):
    """Photo pixels to KiCad mm, top view: the photo frame is the board seen from the back, so the
    top view is mirrored vertically."""
    return x / PX_PER_MM, (IMG_H - y) / PX_PER_MM


def load_js(name, var):
    """The array assigned to window.<var> in a data file, with // comment lines dropped."""
    src = open(os.path.join(ROOT, name)).read()
    body = src.split(f"window.{var} =", 1)[1]
    body = re.sub(r"^\s*//[^\n]*$", "", body, flags=re.M).strip().rstrip(";")
    return json.loads(body)


def pin_counts(c):
    if "pinCounts" in c:
        return c["pinCounts"]
    if "pinsPerSide" in c:
        return [c["pinsPerSide"]] * 4
    return None


def chip_pins(c):
    """Pads of a component, as in flip.html: QFN-style pins computed from the outline corners,
    drawn polygon pads, or the whole body for a part whose pins are not known."""
    def poly_pad(pid, name, notes, polygon, **extra):
        xs, ys = [p[0] for p in polygon], [p[1] for p in polygon]
        return dict(id=pid, name=name or "", notes=notes or "", side=c["side"], poly=polygon, chip=c,
                    x=round(sum(xs) / len(xs)), y=round(sum(ys) / len(ys)),
                    r=round(min(max(xs) - min(xs), max(ys) - min(ys)) / 2), **extra)
    if "pads" in c:
        return [poly_pad(q["id"], q.get("name"), q.get("notes"), q["polygon"]) for q in c["pads"]]
    counts = pin_counts(c)
    if not counts:
        return [poly_pad(c["id"], "", c.get("notes"), c["corners"], body=True)]
    C = c["corners"]
    size = c["size"] if isinstance(c["size"], list) else [c["size"], c["size"]]
    W, H = size

    def at(u, v):
        return [round((1 - u) * (1 - v) * C[0][k] + u * (1 - v) * C[1][k] + u * v * C[2][k] + (1 - u) * v * C[3][k]) for k in (0, 1)]
    px_per_mm = sum(math.dist(C[i], C[(i + 1) % 4]) / (H if i % 2 else W) for i in range(4)) / 4
    names = c.get("pinNames", {})
    out = []
    for e in range(4):
        n, L = counts[e], (H if e % 2 else W)
        for j in range(n):
            t = (L / 2 - (n - 1) / 2 * c["pitch"] + j * c["pitch"]) / L
            u, v = [(t, 0), (1, t), (1 - t, 1), (0, 1 - t)][e]
            x, y = at(u, v)
            pid = str(len(out) + 1)
            out.append(dict(id=pid, name=names.get(pid, ""), notes="", side=c["side"], x=x, y=y,
                            r=round(c["pitch"] / 2 * px_per_mm), chip=c, edge=e))
    if c.get("exposedPad"):
        x, y = at(.5, .5)
        out.append(dict(id="EP", name=names.get("EP", ""), notes="", side=c["side"], x=x, y=y,
                        r=round(c["exposedPad"] / 2 * px_per_mm), chip=c, ep=True))
    return out


def passive(q):
    """A resistor or capacitor from passives.js as a component with one pad per end cap."""
    x, y, w, h = q["box"]
    e = round((w if q["axis"] == "h" else h) * .3)
    rect = lambda x0, y0, x1, y1: [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
    ends = ([rect(x, y, x + e, y + h), rect(x + w - e, y, x + w, y + h)] if q["axis"] == "h"
            else [rect(x, y, x + w, y + e), rect(x, y + h - e, x + w, y + h)])
    part = {"R": "resistor", "C": "capacitor"}.get(q["kind"], "unknown two-terminal part")
    return dict(id=q["id"], part=part, package="two-terminal SMD", side=q["side"], passive=q["kind"],
                rect=q["box"], axis=q["axis"], notes=q.get("notes", ""),
                pads=[dict(id=str(i + 1), name="", polygon=p) for i, p in enumerate(ends)])


def in_poly(poly, x, y):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        (xi, yi), (xj, yj) = poly[i], poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def on_pad(p, x, y):
    if p.get("poly"):
        return in_poly(p["poly"], x, y)
    return math.hypot(x - p["x"], y - p["y"]) <= (p.get("r") or 45)


def connected(t, p):
    """A trace connects to a pad when one of its points or pins on the pad's side lies on the pad."""
    return (any(q["side"] == p["side"] and any(on_pad(p, x, y) for x, y in q["points"]) for q in t["paths"]) or
            any(q["side"] == p["side"] and on_pad(p, q["x"], q["y"]) for q in t.get("pins", [])) or
            # a via goes through the board, so it connects pads on either side
            any(on_pad(p, x, y) for x, y in t.get("vias", [])))


def load():
    """Everything the generators need: traces, components (with passives) and every pad."""
    traces = load_js("traces.js", "TRACES")
    test_pads = load_js("pads.js", "PADS")
    comps = load_js("components.js", "COMPONENTS") + [passive(q) for q in load_js("passives.js", "PASSIVES")]
    pads = [dict(p, kind="testpad") for p in test_pads]
    for c in comps:
        for p in chip_pins(c):
            pads.append(dict(p, kind="pin"))
    return traces, comps, pads


def nets(traces, pads):
    """Group traces into nets: traces sharing a pad are one net (body outlines of connectors and
    unidentified parts carry many nets and join nothing). Returns (net name per trace index,
    net name per pad index, list of merges as (kept name, merged names))."""
    parent = list(range(len(traces)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    pad_traces = []
    for p in pads:
        ts = [i for i, t in enumerate(traces) if connected(t, p)]
        pad_traces.append(ts)
        if not p.get("body"):
            for i in ts[1:]:
                parent[find(i)] = find(ts[0])
    groups = {}
    for i in range(len(traces)):
        groups.setdefault(find(i), []).append(i)

    def label(i):
        return traces[i]["name"] or f"Net-T{i + 1}"
    name = {}
    merges = []
    for root, members in groups.items():
        named = [traces[i]["name"] for i in members if traces[i]["name"]]
        # GND wins, then the first named trace, else the first trace's number
        n = "GND" if "GND" in named else (named[0] if named else label(members[0]))
        for i in members:
            name[i] = n
        if len(members) > 1:
            merges.append((n, [label(i) for i in members]))
    pad_net = [None if (p.get("body") or not ts) else name[ts[0]] for p, ts in zip(pads, pad_traces)]
    return name, pad_net, merges
