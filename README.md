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

## Test pads

The 40 numbered test pads on the back of the board, as labelled in the photos. Names ending in "?" are likely but
not confirmed; the others were measured or follow from what the pad connects to.

<!-- test-pads:start -->
| Pad | Signal | Notes |
|---|---|---|
| 01 | USB CC2 |  |
| 02 | Left button power | Lets the left button also act as the power button; exact role not yet known |
| 03 | *not identified* |  |
| 04 | MCU PB7 | MCU PB7 through R30; role not known |
| 05 | PD SCL | STUSB4500L pin 7, I2C clock (not to the MCU, likely for configuration), as TP09 is its SDA |
| 06 | BAT NTC | The battery's temperature sensor (NTC): battery pad 1, and through R1 the charger's TH pin (PWR1 pin 8) |
| 07 | Charger input? | Input supply of the L6924D charger (PWR1 pins 1, 2), fed from VBUS by the X12 power switch, also the anode of the X9 Zener; R31 feeds it to the MCU PA1 voltage sense; not measured |
| 08 | *not identified* |  |
| 09 | PD SDA | STUSB4500L pin 8, I2C data (not to the MCU, likely for configuration), as TP05 is its SCL |
| 10 | I2C1 SCL |  |
| 11 | PD VBUS_EN_SNK |  |
| 12 | VBUS |  |
| 13 | Charger VREF | 1.8 V reference of the L6924D charger (PWR1 pin 12), decoupled by C37 |
| 14 | VBAT | Battery +: battery pad 3, the charger's battery sense (PWR1 VOSNS, pin 10), the fuel gauge (PWR2 pin 9) and X9's unconnected pin |
| 15 | Charger ST2 | Status output ST2 of the L6924D charger (PWR1 pin 3) to MCU PA2, a wake-up input |
| 16 | MCU PB3 | MCU PB3 through R16, with R28 and R29 (to TP07's net); role not known |
| 17 | I2C1 SDA |  |
| 18 | Charger IPRG | Charge current program pin of the L6924D charger (PWR1 pin 15), with R14 to ground |
| 19 | Left button power | Lets the left button also act as the power button; exact role not yet known |
| 20 | SWCLK | Legacy SWD debug access: Ledger originally left the STM32 unlocked so users could verify the device's state over SWD. That was shown to be a risk, and the STM32 now ships locked, so this port can no longer be used |
| 21 | SWDIO | Legacy SWD debug access: Ledger originally left the STM32 unlocked so users could verify the device's state over SWD. That was shown to be a risk, and the STM32 now ships locked, so this port can no longer be used |
| 22 | Supply sense (MCU PA1) | Voltage sense into MCU PA1 (ADC1_IN6): R31 and R32 divide down the supply on TP07's net, R32 to ground |
| 23 | GND |  |
| 24 | +3.3V rail |  |
| 25 | MCU PA5 | MCU PA5, with R19 and R37; role not known |
| 26 | MCU NRST |  |
| 27 | Charger SD | MCU PA7 (pin 16), joined on an inner layer to the shutdown pin (SD, pin 7) of the L6924D charger, which R11 holds low to enable it: PA7 can likely switch charging off |
| 28 | Left button |  |
| 29 | SE RESET |  |
| 30 | SE CLK-IN |  |
| 31 | OLED SPI CS |  |
| 32 | SEPROXYHAL |  |
| 33 | OLED RESET? | Likely OLED reset, not confirmed: goes to the main MCU, not the secure element |
| 34 | OLED CLK |  |
| 35 | OLED MOSI |  |
| 36 | OLED D/C |  |
| 37 | OLED VCOMH? | BTB pin 9, filtered by C31 to ground: likely the OLED controller's VCOMH, which only needs a capacitor; not measured |
| 38 | OLED VCC | The OLED panel supply (7.5 to 16.5 V for an SSD1312): output of the X10 TLV61046A boost converter, to BTB pin 12; voltage not measured |
| 39 | OLED IREF? | Likely the OLED controller's IREF, with R33 to ground setting the segment current; not measured |
| 40 | Right button |  |
<!-- test-pads:end -->

## Layout

| Path | Contents |
|---|---|
| `flip.html` | Photo viewer |
| `img/` | Photos of both sides, with and without components, aligned to the same pixel grid; `xray.png`, an X-ray mosaic of the whole board, seen from the back like the photos; `se1_die/`, microscope photos of the decapped secure element die, a 50x overview and four 100x quarters, in the die's own orientation (ST logo top left) |
| `traces.js` | Traced nets: segments per side, vias, ground connection points, names and purposes |
| `pads.js` | The 40 test pads and their signal names |
| `components.js`, `passives.js` | Chips, connectors and other parts; resistors and capacitors |
| `kicad/` | KiCad project generated from the data above, plus the 3D viewer and the scripts that build them |
| `kicad/se1_ct.js` | Model of the secure element from an X-ray CT scan, which the 3D viewer loads when zoomed in on it |
| `kicad/se1_die.jpg` | Photo of the secure element die's top metal layer (the ST K500A die), stitched from the four 100x shots in `img/se1_die/`, cropped to the die edge and turned to match the CT model; the 3D viewer lays it on the die of the CT model |
| `index.html` | Landing page of the published site |

## Working on it

Open `flip.html` in a browser; no server is needed. The traces are edited directly in `traces.js`, one trace
per line with its points in pixel coordinates of the photos. After drawing, `kicad/cleanup_traces.py` then
`kicad/octilinear.py` square the segments to 0/45/90 degrees without changing any connection.

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
