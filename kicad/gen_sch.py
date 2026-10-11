"""Generate nanox.kicad_sch from the same data as the board: one box symbol per component with a pin per
pad, placed on a grid, and a net label on every connected pin. Labels with the same name are the same
net, so the schematic carries exactly the board's connectivity. Symbols link to the board footprints
through the same uuids generate.py gives them.

Refuses to overwrite an existing schematic, which may hold edits made in KiCad, unless --force is given.
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nanox_data as d  # noqa: E402
from generate import symbol_uuid, NS  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "nanox.kicad_sch")
SHEET = str(uuid.uuid5(NS, "sheet:root"))
G = 2.54  # grid


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def uid(*parts):
    return str(uuid.uuid5(NS, ":".join(map(str, parts))))


def lib_symbol(lib_id, ref_prefix, pins):
    """A box symbol: pins split between the left and right sides, numbered top to bottom."""
    n = len(pins)
    left, right = pins[:(n + 1) // 2], pins[(n + 1) // 2:]
    rows = max(len(left), len(right), 1)
    # wide enough for the longest pin names on both sides (about 0.85 mm per character at 1 mm text)
    longest = lambda g: max((len(nm or "") for _, nm in g), default=0)
    w = max(15.24, round(((longest(left) + longest(right)) * 0.85 + 4) / G) * G)
    top = (rows - 1) * G / 2
    out = [f'  (symbol {q(lib_id)} (in_bom yes) (on_board yes)',
           f'   (property "Reference" {q(ref_prefix)} (at 0 {top + G * 1.5:.2f} 0) (effects (font (size 1.27 1.27))))',
           f'   (property "Value" {q(lib_id)} (at 0 {-top - G * 1.5:.2f} 0) (effects (font (size 1.27 1.27))))',
           f'   (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'   (symbol {q(lib_id.split(":")[-1] + "_0_1")}',
           f'    (rectangle (start {-w / 2:.2f} {top + G:.2f}) (end {w / 2:.2f} {-top - G:.2f}) (stroke (width 0.254) (type default)) (fill (type background))))',
           f'   (symbol {q(lib_id.split(":")[-1] + "_1_1")}']
    pos = {}
    for side, group in (("L", left), ("R", right)):
        for i, (num, name) in enumerate(group):
            y = top - i * G
            x, ang = (-w / 2 - G, 0) if side == "L" else (w / 2 + G, 180)
            out.append(f'    (pin passive line (at {x:.2f} {y:.2f} {ang}) (length {G})'
                       f' (name {q(name or "~")} (effects (font (size 1.0 1.0)))) (number {q(num)} (effects (font (size 1.0 1.0)))))')
            pos[num] = (x, y, side)
    out.append('   )')
    out.append('  )')
    return "\n".join(out), pos, (w + 2 * G, (rows + 1) * G)


def main():
    if os.path.exists(OUT) and "--force" not in sys.argv:
        sys.exit(f"{OUT} exists and may hold KiCad edits; pass --force to regenerate it")
    traces, comps, pads = d.load()
    trace_net, pad_net, _ = d.nets(traces, pads)
    net_of = {id(p): n for p, n in zip(pads, pad_net)}

    parts = []  # (ref, value, footprint description, pins [(number, name, net)])
    for p in (p for p in pads if p["kind"] == "testpad"):
        parts.append(("TP" + p["id"], p.get("name") or "TestPoint", "test pad", [("1", p.get("name", ""), net_of[id(p)])]))
    for c in comps:
        cp = [p for p in pads if p["kind"] == "pin" and p["chip"] is c and not p.get("body")]
        value = c.get("part", "") if not c.get("passive") else {"R": "R", "C": "C"}.get(c["passive"], "?")
        parts.append((d.ref(c["id"]), value, c.get("package", ""), [(p["id"], p.get("name", ""), net_of[id(p)]) for p in cp]))

    libs, body = [], []
    # place parts in columns sorted by kind, tallest-first within a column
    order = sorted(parts, key=lambda t: (t[0].rstrip("0123456789") , -len(t[3]), t[0]))
    x, y, col_w, max_y = G * 10, G * 10, 0, G * 120
    for ref, value, pkg, pins in order:
        lib_id = "nanox:" + ref
        sym, pos, (w, h) = lib_symbol(lib_id, ref.rstrip("0123456789") or ref, [(n, nm) for n, nm, _ in pins])
        libs.append(sym)
        if y + h > max_y:
            x, y, col_w = x + col_w + G * 12, G * 10, 0
        cx, cy = round((x + w / 2) / G) * G, round((y + h / 2) / G) * G
        col_w = max(col_w, w)
        u = symbol_uuid(ref)
        body.append(f' (symbol (lib_id {q(lib_id)}) (at {cx:.2f} {cy:.2f} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {q(u)})')
        body.append(f'  (property "Reference" {q(ref)} (at {cx:.2f} {cy - h / 2 - G / 2:.2f} 0) (effects (font (size 1.27 1.27))))')
        body.append(f'  (property "Value" {q(value)} (at {cx:.2f} {cy + h / 2 + G / 2:.2f} 0) (effects (font (size 1.27 1.27))))')
        body.append(f'  (property "Footprint" "" (at {cx:.2f} {cy:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        body.append(f'  (property "Description" {q(pkg)} (at {cx:.2f} {cy:.2f} 0) (effects (font (size 1.27 1.27)) hide))')
        for n, _, _ in pins:
            body.append(f'  (pin {q(n)} (uuid {q(uid("pin", ref, n))}))')
        body.append(f'  (instances (project "nanox" (path "/{SHEET}" (reference {q(ref)}) (unit 1))))')
        body.append(' )')
        for n, _, net in pins:
            px, py, side = pos[n]
            ax, ay = cx + px, cy - py  # symbol y points up, sheet y down
            if net:
                ang, just = (180, "right") if side == "L" else (0, "left")
                body.append(f' (label {q(net)} (at {ax:.2f} {ay:.2f} {ang}) (effects (font (size 1.0 1.0)) (justify {just} bottom)) (uuid {q(uid("label", ref, n))}))')
            else:
                body.append(f' (no_connect (at {ax:.2f} {ay:.2f}) (uuid {q(uid("nc", ref, n))}))')
        y += h + G * 4

    lib = ["(kicad_symbol_lib (version 20231120) (generator \"nanox_gen_sch\") (generator_version \"1\")"]
    lib += [l.replace("(symbol \"nanox:", "(symbol \"", 1) for l in libs] + [")"]
    open(os.path.join(HERE, "nanox.kicad_sym"), "w").write("\n".join(lib) + "\n")
    open(os.path.join(HERE, "sym-lib-table"), "w").write(
        '(sym_lib_table\n  (version 7)\n  (lib (name "nanox")(type "KiCad")(uri "${KIPRJMOD}/nanox.kicad_sym")(options "")(descr "Reconstructed parts"))\n)\n')
    src = ["(kicad_sch (version 20231120) (generator \"nanox_gen_sch\") (generator_version \"1\")",
           f' (uuid {q(SHEET)})', ' (paper "A1")',
           ' (title_block (title "Ledger Nano X main board, reconstructed") (comment 1 "Generated from the flip.html overlay data; nets follow the traced copper"))',
           ' (lib_symbols', *libs, ' )', *body,
           f' (sheet_instances (path "/" (page "1")))', ')']
    open(OUT, "w").write("\n".join(src) + "\n")
    print("wrote", OUT, "with", len(parts), "symbols")


if __name__ == "__main__":
    main()
