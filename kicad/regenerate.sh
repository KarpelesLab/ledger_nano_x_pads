#!/bin/sh
# Rebuild the KiCad reconstruction from the flip.html data files. Overwrites nanox.kicad_pcb and
# nanox.kicad_sch, so do not run it once those have been edited in KiCad.
set -e
cd "$(dirname "$0")"
python3 outline_clean.py
python3 generate.py --force
# KiCad assigns random uuids and sorts by them on save: make them stable so unchanged boards stay identical
python3 stable_uuids.py
python3 gen_sch.py --force
# zones cannot be filled from KiCad's Python module (it crashes), so fill and save them with kicad-cli
kicad-cli pcb drc --refill-zones --save-board -o /dev/null nanox.kicad_pcb >/dev/null
python3 stable_uuids.py --sort-tracks
python3 check.py
python3 export_overlay.py
python3 export_scene.py
# 3D renders and STEP export, so they never fall behind the board
./render.sh
