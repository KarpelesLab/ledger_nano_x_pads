"""Make every hand-drawn trace segment horizontal, vertical or 45 degrees, by adding one bend to each segment
that isn't: a segment from a to b becomes a straight run and a 45-degree run. Of the two ways round (straight
first or diagonal first), it keeps the one that lies more on copper in the bare photo of that side, where
traces under the solder mask show lighter than the board. Existing points never move, so pad landings, vias
and junctions stay put. Refuses to write if any pad would change net. Paths on the inner layer are left alone,
as no photo shows them. Run cleanup_traces.py first: it straightens what moving a bend point can fix. Before
adding bends, an end that lands on a pad and is only slightly off slides within that pad instead.

Usage: python3 octilinear.py [--dry-run] [--flip TRACE:PATH:SEG ...]
  --flip takes the other way round for one segment (1-based trace number, 0-based path and segment), for
  when the photo picks wrong or the chosen bend runs too close to other copper.
"""
import json
import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nanox_data as d  # noqa: E402

TRACES = os.path.join(d.ROOT, "traces.js")
PHOTO = {"front": "img/front_empty.jpg", "back": "img/back_empty.jpg"}


def off_angle(a, b):
    ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 45
    return min(ang, 45 - ang)


def corners(a, b):
    """The two bends that split a->b into a straight and a 45-degree run: straight first, diagonal first."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    sx, sy = (dx > 0) - (dx < 0), (dy > 0) - (dy < 0)
    diag = min(abs(dx), abs(dy))
    # the diagonal run, from either end
    return [b[0] - sx * diag, b[1] - sy * diag], [a[0] + sx * diag, a[1] + sy * diag]


class Copper:
    """How much a polyline lies on traces in a bare photo: mean brightness along it, against its surroundings."""
    def __init__(self, path):
        im = Image.open(os.path.join(d.ROOT, path)).convert("L")
        self.w, self.h = im.size
        self.px = im.load()

    def at(self, x, y):
        x, y = min(max(int(x), 0), self.w - 1), min(max(int(y), 0), self.h - 1)
        return self.px[x, y]

    def score(self, pts):
        vals = []
        for a, b in zip(pts, pts[1:]):
            n = max(1, int(math.dist(a, b) / 2))
            for k in range(n + 1):
                x, y = a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n
                vals.append(sum(self.at(x + i, y + j) for i in (-2, 0, 2) for j in (-2, 0, 2)) / 9)
        return sum(vals) / len(vals)


def align_ends(traces, pads):
    """First, where a slightly-off segment ends on a pad, slide that end within the pad onto the exact direction
    instead of adding a jog. Only path ends that nothing else uses (no via, junction or other path) move."""
    used = {}
    for t in traces:
        for q in t["paths"]:
            for p in q["points"]:
                used[(q["side"], tuple(p))] = used.get((q["side"], tuple(p)), 0) + 1
    vias = {tuple(v) for t in traces for v in t.get("vias", [])}
    moved = 0
    for t in traces:
        for q in t["paths"]:
            if q["side"] not in PHOTO or len(q["points"]) < 2:
                continue
            pts = q["points"]
            for end, nb in ((0, 1), (len(pts) - 1, len(pts) - 2)):
                e, o = pts[end], pts[nb]
                if e == o or off_angle(o, e) <= .5 or tuple(e) in vias or used[(q["side"], tuple(e))] > 1:
                    continue
                on = [p for p in pads if p["side"] == q["side"] and not p.get("body") and d.on_pad(p, *e)]
                if len(on) != 1:
                    continue
                dx, dy = e[0] - o[0], e[1] - o[1]
                ang = round(math.atan2(dy, dx) / (math.pi / 4)) * (math.pi / 4)
                ux, uy = math.cos(ang), math.sin(ang)
                L = dx * ux + dy * uy
                n = [round(o[0] + ux * L), round(o[1] + uy * L)]
                if math.dist(n, e) > 10 or off_angle(o, n) > .5 or not d.on_pad(on[0], *n):
                    continue
                if any(p is not on[0] and p["side"] == q["side"] and not p.get("body") and d.on_pad(p, *n) for p in pads):
                    continue
                pts[end] = n
                moved += 1
    return moved


def load():
    lines = open(TRACES).read().rstrip("\n").split("\n")
    idx = [i for i, l in enumerate(lines) if l.strip().startswith("{")]
    return lines, idx, [json.loads(lines[i].strip().rstrip(",")) for i in idx]


def main():
    dry = "--dry-run" in sys.argv
    flips = {tuple(int(v) for v in s.split(":")) for s in sys.argv[sys.argv.index("--flip") + 1:]} if "--flip" in sys.argv else set()
    lines, idx, traces = load()
    _, _, pads = d.load()
    before = d.nets(traces, pads)[1]
    copper = {side: Copper(p) for side, p in PHOTO.items()}
    slid = align_ends(traces, pads)
    fixed = total = 0
    for ti, t in enumerate(traces):
        for qi, q in enumerate(t["paths"]):
            if q["side"] not in copper:
                continue
            pts = q["points"]
            out = [pts[0]]
            for si, (a, b) in enumerate(zip(pts, pts[1:])):
                if a != b and off_angle(a, b) > .5:
                    total += 1
                    c1, c2 = corners(a, b)
                    s1, s2 = (copper[q["side"]].score(p) for p in ([a, c1, b], [a, c2, b]))
                    c = c1 if s1 >= s2 else c2
                    if (ti + 1, qi, si) in flips:
                        c = c2 if c is c1 else c1
                    if c not in (a, b):
                        out.append(c)
                        fixed += 1
                out.append(b)
            q["points"] = out
    after = d.nets(traces, pads)[1]
    changed = [p for p, x, y in zip(pads, before, after) if x != y]
    if changed:
        sys.exit("refusing: pads would change net: " + ", ".join(f"{p.get('chip', {}).get('id', 'TP')} {p['id']}" for p in changed[:10]))
    print(f"{slid} pad landings slid into line; {total} segments still off 0/45/90 degrees, {fixed} bends added; "
          "connections unchanged")
    if dry:
        return
    for i, t in zip(idx, traces):
        s = lines[i].strip()
        lines[i] = "  " + json.dumps(t, separators=(",", ":"), ensure_ascii=False) + ("," if s.endswith(",") else "")
    open(TRACES, "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
