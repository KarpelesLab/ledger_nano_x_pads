"""Write the test pad table into README.md, between its "test-pads" markers, from pads.js."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nanox_data as d  # noqa: E402

README = os.path.join(d.ROOT, "README.md")
START, END = "<!-- test-pads:start -->", "<!-- test-pads:end -->"


def cell(s):
    return s.replace("|", "\\|").replace("\n", " ")


def main():
    rows = ["| Pad | Signal | Notes |", "|---|---|---|"]
    for p in sorted(d.load_js("pads.js", "PADS"), key=lambda p: p["id"]):
        rows.append(f"| {p['id']} | {cell(p['name']) or '*not identified*'} | {cell(p.get('notes', ''))} |")
    src = open(README).read()
    head, rest = src.split(START, 1)
    _, tail = rest.split(END, 1)
    open(README, "w").write(head + START + "\n" + "\n".join(rows) + "\n" + END + tail)
    print("wrote the test pad table into", README)


if __name__ == "__main__":
    main()
