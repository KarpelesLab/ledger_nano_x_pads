"""Give every item in nanox.kicad_pcb a UUID derived from its content, replacing the random ones KiCad
assigns. KiCad sorts items by UUID when saving, so random UUIDs reorder the whole file on every
regeneration; stable ones keep an unchanged board byte-for-byte identical, and its diffs meaningful.

Each UUID is derived from the item that holds it and the top-level item (footprint, track, zone...)
around it, with all UUIDs blanked, so identical fields in different footprints still differ.

Run between generate.py and the kicad-cli step that fills zones and re-saves the board.
"""
import hashlib
import os
import re
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "nanox.kicad_pcb")
NS = uuid.UUID("2c1f6a3e-8b4d-4f0a-9e57-3d6b1c0a7f21")
UUID_RE = re.compile(r'\(uuid "[0-9a-fA-F-]+"\)')


def main():
    src = open(PCB).read()
    # one pass over the parentheses: for each uuid, the start of the block holding it and of the
    # top-level block around it; and the end of every block
    end_of, stack, found = {}, [], []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == '"':
            i += 1
            while src[i] != '"':
                i += 2 if src[i] == "\\" else 1
        elif c == "(":
            if src.startswith('(uuid "', i):
                found.append((i, stack[-1], stack[1] if len(stack) > 1 else stack[0]))
            stack.append(i)
        elif c == ")":
            end_of[stack.pop()] = i + 1
        i += 1
    seen, repl = {}, []
    for start, own, top in found:
        m = UUID_RE.match(src, start)
        content = UUID_RE.sub("(uuid)", src[own:end_of[own]] + "\0" + src[top:end_of[top]])
        key = hashlib.sha1(content.encode()).hexdigest()
        # identical items (if any) are told apart by how many came before
        k = seen.get(key, 0)
        seen[key] = k + 1
        repl.append((m.start(), m.end(), f'(uuid "{uuid.uuid5(NS, key + ":" + str(k))}")'))
    out, last = [], 0
    for s, e, r in repl:
        out.append(src[last:s])
        out.append(r)
        last = e
    out.append(src[last:])
    open(PCB, "w").write("".join(out))
    dupes = sum(v - 1 for v in seen.values())
    print(len(repl), "uuids made stable" + (f" ({dupes} for identical items)" if dupes else ""))


def sort_tracks():
    """KiCad writes tracks and vias in its internal order, which zone filling shuffles: sort them by
    their (stable) uuid. Run after the last KiCad save."""
    src = open(PCB).read()
    items = list(re.finditer(r'^\t\((?:segment|via|arc)\b.*?^\t\)\n', src, re.S | re.M))
    if not items:
        return
    first, last = items[0].start(), items[-1].end()
    # tracks and vias form one run in the file; refuse to reorder if anything else sits between them
    between = src[first:last]
    assert len("".join(m.group(0) for m in items)) == len(between), "tracks are not contiguous"
    key = lambda m: UUID_RE.search(m.group(0)).group(0)
    open(PCB, "w").write(src[:first] + "".join(m.group(0) for m in sorted(items, key=key)) + src[last:])
    print(len(items), "tracks and vias sorted")


if __name__ == "__main__":
    import sys
    sort_tracks() if "--sort-tracks" in sys.argv else main()
