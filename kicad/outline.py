"""Detect the board outline in the back photo and write it to outline.json as a polygon in photo pixels.

The board is everything that is not the dark foam it sits on: the largest such region, with holes
filled, traced along its edge and simplified.
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
K = 4  # work at quarter resolution


def board_mask(path):
    im = Image.open(path).convert("RGB")
    im = im.resize((im.width // K, im.height // K), Image.BILINEAR)
    a = np.asarray(im).astype(np.int16)
    mx, mn = a.max(axis=2), a.min(axis=2)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    # solder mask is clearly green; copper, solder and parts are bright; the foam is dark and grey
    m = ((G > R + 12) & (G > B + 12) & (mx > 60)) | (mx > 150)
    with tempfile.TemporaryDirectory() as tmp:
        src, out = os.path.join(tmp, "m.png"), os.path.join(tmp, "o.png")
        Image.fromarray((m * 255).astype(np.uint8)).save(src)
        # close small gaps along the board edge
        subprocess.run(["magick", src, "-morphology", "Close", "Disk:6", out], check=True)
        m = np.asarray(Image.open(out).convert("L")) > 127
    # the outside is whatever the background reaches from the image border; the rest is the board
    # with its dark parts filled in, of which only the largest region is kept
    outside = flood(~m, [(x, 0) for x in range(m.shape[1])] + [(x, m.shape[0] - 1) for x in range(m.shape[1])] +
                    [(0, y) for y in range(m.shape[0])] + [(m.shape[1] - 1, y) for y in range(m.shape[0])])
    board = ~outside
    best = None
    seen = np.zeros_like(board)
    for y, x in zip(*np.nonzero(board[::8, ::8])):
        y, x = y * 8, x * 8
        if seen[y, x]:
            continue
        region = flood(board, [(x, y)])
        seen |= region
        if best is None or region.sum() > best.sum():
            best = region
    return best


def flood(allowed, seeds):
    """Pixels of boolean image allowed reachable from seeds through 4-neighbours."""
    from collections import deque
    h, w = allowed.shape
    out = np.zeros_like(allowed)
    q = deque((x, y) for x, y in seeds if allowed[y, x])
    for x, y in q:
        out[y, x] = True
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and allowed[ny, nx] and not out[ny, nx]:
                out[ny, nx] = True
                q.append((nx, ny))
    return out


def trace_edge(b):
    """Moore-neighbour boundary tracing of the region in boolean image b, as a list of (x, y)."""
    ys, xs = np.nonzero(b)
    start = (xs[np.argmin(ys * b.shape[1] + xs)], ys.min())
    dirs = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
    h, w = b.shape
    inside = lambda x, y: 0 <= x < w and 0 <= y < h and b[y, x]
    pts, cur, d = [start], start, 0
    while True:
        for k in range(8):
            nd = (d + 6 + k) % 8
            nx, ny = cur[0] + dirs[nd][0], cur[1] + dirs[nd][1]
            if inside(nx, ny):
                cur, d = (nx, ny), nd
                break
        if cur == start:
            break
        pts.append(cur)
    return pts


def simplify(pts, eps):
    """Ramer-Douglas-Peucker on a closed polyline."""
    def rdp(seg):
        if len(seg) < 3:
            return seg
        (x0, y0), (x1, y1) = seg[0], seg[-1]
        L = max(np.hypot(x1 - x0, y1 - y0), 1e-9)
        d = [abs((y1 - y0) * x - (x1 - x0) * y + x1 * y0 - y1 * x0) / L for x, y in seg]
        i = int(np.argmax(d))
        if d[i] <= eps:
            return [seg[0], seg[-1]]
        return rdp(seg[:i + 1])[:-1] + rdp(seg[i:])
    far = max(range(len(pts)), key=lambda i: (pts[i][0] - pts[0][0]) ** 2 + (pts[i][1] - pts[0][1]) ** 2)
    return rdp(pts[:far + 1])[:-1] + rdp(pts[far:] + [pts[0]])[:-1]


if __name__ == "__main__":
    photo = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "img", "back_with_details.jpg")
    b = board_mask(photo)
    poly = [[int(x * K), int(y * K)] for x, y in simplify(trace_edge(b), 1.5)]
    json.dump(poly, open(os.path.join(HERE, "outline.json"), "w"))
    print(len(poly), "outline points")
