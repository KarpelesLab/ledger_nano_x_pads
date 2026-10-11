"""Check that the schematic and the board describe the same connections: exports the schematic netlist
with kicad-cli and compares every net's pins with the pads of the same net on the board.
"""
import os
import re
import subprocess
import sys
import tempfile

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))


def sexpr_nets(path):
    src = open(path).read()
    nets = {}
    for block in re.split(r"\(net\s+\(code", src)[1:]:
        name = re.search(r'\(name\s+"((?:[^"\\]|\\.)*)"\)', block).group(1)
        nodes = re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', block)
        nets[name] = set(nodes)
    return nets


def main():
    with tempfile.TemporaryDirectory() as tmp:
        net = os.path.join(tmp, "sch.net")
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", net,
                        os.path.join(HERE, "nanox.kicad_sch")], check=True, capture_output=True)
        # KiCad escapes "/" in label names, as it separates sheet paths
        sch = {k.lstrip("/").replace("{slash}", "/"): v for k, v in sexpr_nets(net).items() if not k.startswith("unconnected-")}
    board = pcbnew.LoadBoard(os.path.join(HERE, "nanox.kicad_pcb"))
    pcb = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            n = pad.GetNetname()
            if n:
                pcb.setdefault(n, set()).add((fp.GetReference(), pad.GetNumber()))
    # single-pin nets are fine on the board (a trace to one pad) but unnamed in the schematic
    pcb_multi = {k: v for k, v in pcb.items() if len(v) > 1}
    sch_multi = {k: v for k, v in sch.items() if len(v) > 1}
    bad = 0
    for name in sorted(set(pcb_multi) | set(sch_multi)):
        a, b = pcb_multi.get(name, set()), sch_multi.get(name, set())
        if a != b:
            bad += 1
            print(f"{name}: board only {sorted(a - b)}, schematic only {sorted(b - a)}")
    print(f"{len(pcb_multi)} board nets with 2+ pads, {len(sch_multi)} schematic nets, {bad} differing")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
