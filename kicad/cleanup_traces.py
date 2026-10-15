"""Straighten hand-drawn traces in traces.js: segments within a few degrees of horizontal, vertical or 45°
become exact, by moving the bend points between them a few pixels. Points that make connections never move:
path ends (vias, junctions, pad landings), points on a pad or via, and points other paths branch from.
Refuses to write if any pad would change net, or a point would move too far.

Usage: python3 cleanup_traces.py [--dry-run]
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nanox_data as d  # noqa: E402

TRACES = os.path.join(d.ROOT, "traces.js")
TOL = math.radians(7)   # how far from an exact direction a segment may be to be snapped
MAX_MOVE = 12           # pixels a point may move in total


def load():
    lines = open(TRACES).read().rstrip("\n").split("\n")
    assert lines[2] == "window.TRACES = [" and lines[-1] == "];"
    return lines, [json.loads(l.strip().rstrip(",")) for l in lines[3:-1]]


def anchors(traces, pads):
    """Points (side, x, y) that must not move."""
    fixed = set()
    vias = {tuple(v) for t in traces for v in t.get("vias", [])}
    ends = set()
    for t in traces:
        for q in t["paths"]:
            for p in (q["points"][0], q["points"][-1]):
                ends.add((q["side"], tuple(p)))
    for t in traces:
        for q in t["paths"]:
            pts = q["points"]
            for k, p in enumerate(pts):
                tp = tuple(p)
                key = (q["side"], tp)
                if k in (0, len(pts) - 1) or tp in vias or key in ends:
                    fixed.add(key)
                elif any(pp["side"] == q["side"] and not pp.get("body") and d.on_pad(pp, *p) for pp in pads):
                    fixed.add(key)
    return fixed


def snap_dir(dx, dy):
    """The exact direction to snap a segment to, as (ux, uy) of length 1 up to scale, or None."""
    a = math.atan2(dy, dx)
    for k in range(8):
        t = k * math.pi / 4
        diff = (a - t + math.pi) % (2 * math.pi) - math.pi
        if abs(diff) < TOL:
            return round(math.cos(t)), round(math.sin(t))
    return None


def clean_path(q, fixed):
    pts = [list(map(float, p)) for p in q["points"]]
    orig = [p[:] for p in pts]
    free = [(q["side"], tuple(p)) not in fixed for p in q["points"]]
    for _ in range(6):
        for k in range(len(pts) - 1):
            a, b = pts[k], pts[k + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            if math.hypot(dx, dy) < 3:
                continue
            u = snap_dir(dx, dy)
            if not u:
                continue
            ux, uy = u
            fa, fb = free[k], free[k + 1]
            if not (fa or fb):
                continue
            if ux == 0 or uy == 0:
                # horizontal or vertical: make the other coordinate equal
                c = 1 if ux else 0
                target = a[c] if not fa else b[c] if not fb else (a[c] + b[c]) / 2
                if fa:
                    a[c] = target
                if fb:
                    b[c] = target
            else:
                # 45°: project the free end(s) onto the exact diagonal through the segment's midpoint
                # (or through the fixed end)
                if fa and fb:
                    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                    half = (dx * ux + dy * uy) / 4
                    a[0], a[1] = mx - ux * half, my - uy * half
                    b[0], b[1] = mx + ux * half, my + uy * half
                elif fb:
                    s = (dx * ux + dy * uy) / 2
                    b[0], b[1] = a[0] + ux * s, a[1] + uy * s
                else:
                    s = (dx * ux + dy * uy) / 2
                    a[0], a[1] = b[0] - ux * s, b[1] - uy * s
    moved = max((math.dist(p, o) for p, o in zip(pts, orig)), default=0)
    return [[round(x), round(y)] for x, y in pts], moved


def seg_dist(a, b, c, e):
    """Shortest distance between segments ab and ce."""
    def pt(p, q, r):
        dx, dy = r[0] - q[0], r[1] - q[1]
        L2 = dx * dx + dy * dy or 1
        f = max(0, min(1, ((p[0] - q[0]) * dx + (p[1] - q[1]) * dy) / L2))
        return math.hypot(q[0] + f * dx - p[0], q[1] + f * dy - p[1])
    def cross(p, q, r, s_):
        def o(u, v, w): return (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
        return o(p, q, r) * o(p, q, s_) < 0 and o(r, s_, p) * o(r, s_, q) < 0
    if cross(a, b, c, e):
        return 0
    return min(pt(a, c, e), pt(b, c, e), pt(c, a, b), pt(e, a, b))


def clearance(traces, net_of, ti, q):
    """How close path q of trace ti comes to copper of other nets on its side: segments, and vias."""
    best = math.inf
    w = traces[ti].get("width", 13) / 2
    segs = list(zip(q["points"], q["points"][1:]))
    for tj, t in enumerate(traces):
        if net_of[tj] == net_of[ti]:
            continue
        w2 = t.get("width", 13) / 2
        for r in t["paths"]:
            if r["side"] != q["side"]:
                continue
            for c, e in zip(r["points"], r["points"][1:]):
                for a, b in segs:
                    best = min(best, seg_dist(a, b, c, e) - w - w2)
        for v in t.get("vias", []):
            for a, b in segs:
                best = min(best, seg_dist(a, b, v, v) - w - 19)  # KiCad vias are 0.45 mm across
    return best


def main():
    dry = "--dry-run" in sys.argv
    lines, traces = load()
    _, comps, pads = d.load()
    before = d.nets(traces, pads)[1]
    fixed = anchors(traces, pads)
    net_of = d.nets(traces, pads)[0]
    changed = 0
    worst = 0
    kept = 0
    for ti, t in enumerate(traces):
        for q in t["paths"]:
            new, moved = clean_path(q, fixed)
            if moved > MAX_MOVE:
                continue  # leave paths that would need a large change as drawn
            if new != q["points"]:
                # keep the path as drawn if straightening brings it closer to another net's copper than 2 px
                # and closer than it was
                old = q["points"]
                before_gap = clearance(traces, net_of, ti, q)
                q["points"] = new
                after_gap = clearance(traces, net_of, ti, q)
                q["points"] = old
                if after_gap < 2 and after_gap < before_gap:
                    kept += 1
                    continue
                changed += sum(a != b for a, b in zip(new, q["points"]))
                q["points"] = new
                worst = max(worst, moved)
    after = d.nets(traces, pads)[1]
    if before != after:
        diff = [(p.get("id"), a, b) for p, a, b in zip(pads, before, after) if a != b]
        sys.exit(f"connections would change, nothing written: {diff[:10]}")
    print(f"{changed} points moved, at most {worst:.1f} px; {kept} paths kept as drawn for spacing; connections unchanged")
    if not dry:
        lines[3:-1] = ["  " + json.dumps(t, separators=(",", ":"), ensure_ascii=False) + ("," if i < len(traces) - 1 else "")
                       for i, t in enumerate(traces)]
        open(TRACES, "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
