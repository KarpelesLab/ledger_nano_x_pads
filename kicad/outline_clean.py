"""Board outline built from measured features instead of the raw traced edge, which picks up photo
noise and the USB connector shell sticking out past the board. Edges, steps and slots were measured
from the edge profile of the back photo (outline.py's mask); writes outline.json in photo pixels.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LEFT, RIGHT = 100, 5285


def slot(x0, x1, edge, depth, down):
    """A U-shaped slot cut into a horizontal edge at y=edge, between x0 and x1, reaching y=depth;
    down is True when the slot goes down from the top edge. Points run left to right."""
    r = (x1 - x0) / 2
    cx, cy = (x0 + x1) / 2, depth - r if down else depth + r
    pts = [[x0, edge], [x0, cy]]
    for k in range(1, 8):
        a = math.pi * k / 8
        pts.append([cx - r * math.cos(a), cy + r * math.sin(a) if down else cy - r * math.sin(a)])
    return pts + [[x1, cy], [x1, edge]]


def main():
    top = ([[LEFT, 808], [430, 808]] + slot(430, 512, 808, 846, True) + [[512, 808], [606, 808], [606, 740],
           [1344, 740]] + slot(1344, 1434, 740, 910, True)[:-1] + [[1434, 824], [2190, 824], [2190, 740],
           [3765, 740], [3765, 830], [3920, 830], [3920, 744], [4815, 744], [4815, 815], [4905, 815]] +
           slot(4905, 5000, 815, 922, True)[1:-1] + [[5000, 820], [RIGHT, 820]])
    bottom = ([[LEFT, 2008], [436, 2008]] + slot(436, 520, 2008, 1964, False) + [[520, 2004], [616, 2004], [616, 2074],
              [2122, 2074], [2122, 1994], [2405, 1994], [2405, 2076], [4030, 2076], [4030, 1992], [4150, 1992]] +
              slot(4150, 4245, 1992, 1866, False)[1:-1] + [[4245, 2078], [4815, 2078], [4815, 2008], [4905, 2008]] +
              slot(4905, 5000, 2008, 1900, False)[1:-1] + [[5000, 2008], [RIGHT, 2008]])
    # clockwise in the photo: along the top left to right, down the right side, back along the bottom
    poly = top + bottom[::-1]
    poly = [[round(x), round(y)] for x, y in poly]
    clean = [p for i, p in enumerate(poly) if p != poly[i - 1]]
    json.dump(clean, open(os.path.join(HERE, "outline.json"), "w"))
    print(len(clean), "outline points")


if __name__ == "__main__":
    main()
