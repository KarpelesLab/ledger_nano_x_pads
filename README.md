# Ledger Nano X board map

An interactive map of the Ledger Nano X main board: its 40 test pads, the copper traces between them and the
chips, and a KiCad reconstruction of the whole board.

**View it online: https://karpeleslab.github.io/ledger_nano_x_pads/**

- [Photo viewer](https://karpeleslab.github.io/ledger_nano_x_pads/flip.html): photos of both sides, with and
  without components, overlaid with every traced net, test pad and part; hover anything for details.
- [3D viewer](https://karpeleslab.github.io/ledger_nano_x_pads/kicad/viewer3d.html): the KiCad reconstruction
  with every part and its marking; hover a track, pad or chip to light up its net.

This is a reconstruction from photos, not the manufacturer's design: inner layers are assumed, footprints are
approximate, and names ending in "?" are likely but not confirmed.

## Layout

| Path | Contents |
|---|---|
| `flip.html` | Photo viewer |
| `img/` | Photos of both sides, with and without components, aligned to the same pixel grid |
| `traces.js` | Traced nets: segments per side, vias, ground connection points, names and purposes |
| `pads.js` | The 40 test pads and their signal names |
| `components.js`, `passives.js` | Chips, connectors and other parts; resistors and capacitors |
| `kicad/` | KiCad project generated from the data above, plus the 3D viewer and the scripts that build them |
| `index.html` | Landing page of the published site |

## Working on it

Open `flip.html` in a browser; no server is needed. The traces are edited directly in `traces.js`, one trace
per line with its points in pixel coordinates of the photos.

After changing the data, rebuild the KiCad reconstruction and the viewer data (needs KiCad 10 and its Python
module):

```sh
kicad/regenerate.sh   # board, schematic, zone fill, consistency check, overlay.js and scene.js
kicad/render.sh       # optional: 3D renders and a STEP file
```

`regenerate.sh` overwrites `kicad/nanox.kicad_pcb` and `kicad/nanox.kicad_sch`, so edits made in KiCad
itself would be lost.

The site is published by `.github/workflows/pages.yml` on every push to `master`.

## License

Original reverse engineering work by Karpeles Lab Inc., made available for the public good.

- **Code** (the viewers, the scripts under `kicad/` and the workflow): [MIT](LICENSE).
- **Content** (photos, board data, the KiCad project and its 3D models, and this documentation):
  [CC BY 4.0](LICENSE-CC-BY-4.0). Reuse it freely, including commercially, crediting "Karpeles Lab Inc.".

Ledger and Nano X are trademarks of Ledger SAS; this project is not affiliated with or endorsed by Ledger.
