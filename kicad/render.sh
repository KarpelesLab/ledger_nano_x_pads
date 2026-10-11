#!/bin/sh
# Render the reconstruction in 3D (renders/) and export it as STEP. Renders include every model; the
# STEP only has the KiCad library models, as the generated parts (markings included) are VRML.
set -e
cd "$(dirname "$0")"
mkdir -p renders
for side in top bottom; do
  kicad-cli pcb render --side $side --width 3000 --height 1000 --quality high --zoom 3.2 -o renders/$side.png nanox.kicad_pcb >/dev/null
done
kicad-cli pcb render --side top --width 3000 --height 1600 --quality high --perspective --zoom 1.4 --rotate "-35,0,-20" -o renders/angle.png nanox.kicad_pcb >/dev/null
# exits non-zero when it skips the VRML models, so only fail if no file was written
rm -f nanox.step
kicad-cli pcb export step --force -o nanox.step nanox.kicad_pcb >/dev/null 2>&1 || [ -s nanox.step ]
echo "wrote renders/top.png renders/bottom.png renders/angle.png nanox.step"
