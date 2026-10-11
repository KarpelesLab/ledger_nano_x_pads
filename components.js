// Chips for flip.html. corners outline the package body in pixel coordinates of the 5376x3024
// photos, in pin order: the first corner is next to pin 1, the second at the far end of pin 1's
// side. Pins are computed from these at pitch mm: pinsPerSide on each side, or pinCounts per edge in
// corner order; size is the body in mm, or [first edge, second edge].
// A component with pads lists each pad's outline polygon instead.
window.COMPONENTS = [
  {"id":"MCU","part":"STM32WB35CCU6A","package":"UFQFPN48","side":"front","size":7,"pitch":0.5,"pinsPerSide":12,"exposedPad":5.6,
   "corners":[[2208,1237],[2799,1248],[2795,1824],[2199,1821]],
   // from ST's STM32_open_pin_data, mcu/STM32WB35C(C-E)UxA.xml; the exposed pad is VSS
   "pinNames":{"1":"VBAT","2":"PC14-OSC32_IN","3":"PC15-OSC32_OUT","4":"PH3-BOOT0","5":"PB8","6":"PB9","7":"NRST","8":"VDDA","9":"PA0","10":"PA1","11":"PA2","12":"PA3","13":"PA4","14":"PA5","15":"PA6","16":"PA7","17":"PA8","18":"PA9","19":"PB2","20":"VDD","21":"RF1","22":"VSSRF","23":"VDDRF","24":"OSC_OUT","25":"OSC_IN","26":"AT0","27":"AT1","28":"PB0","29":"PB1","30":"PE4","31":"VFBSMPS","32":"VSSSMPS","33":"VLXSMPS","34":"VDDSMPS","35":"VDD","36":"PA10","37":"PA11","38":"PA12","39":"PA13","40":"VDDUSB","41":"PA14","42":"PA15","43":"PB3","44":"PB4","45":"PB5","46":"PB6","47":"PB7","48":"VDD","EP":"VSS"}},
  {"id":"SE","part":"secure element","package":"QFN20","side":"front","size":4,"pitch":0.5,"pinsPerSide":5,"exposedPad":2.7,
   "corners":[[3351,1308],[3336,964],[3687,968],[3688,1310]],"pinNames":{}},
  {"id":"USBPD","part":"STUSB4500L","package":"QFN24","side":"front","size":4,"pitch":0.5,"pinsPerSide":6,"exposedPad":2.7,
   "notes":"USB power delivery controller; pin 1 inferred from the marking orientation",
   "corners":[[988,1545],[1001,1216],[1321,1216],[1317,1543]],"pinNames":{}},
  // parts not identified yet
  {"id":"PWR1","part":"unknown","package":"16 pins, ~2.75 mm square","side":"front","size":2.75,"pitch":0.5,"pinsPerSide":4,"exposedPad":1.5,
   "notes":"Very likely power related; pin 1 not verified, numbered from the first corner outlined",
   "corners":[[1822,902],[1816,1130],[1585,1137],[1590,903]],"pinNames":{}},
  {"id":"PWR2","part":"unknown","package":"10 pins, ~2.9 x 1.9 mm","side":"front","size":[2.9,1.9],"pitch":0.5,"pinCounts":[5,0,5,0],
   "notes":"Very likely power related, on the MCU's I2C1 bus (pins 2 SDA, 3 SCL), so probably an I2C power chip; marked E058 2050; pin 1 not verified, numbered from the first corner outlined",
   "corners":[[1835,1913],[1590,1917],[1595,1760],[1839,1758]],"pinNames":{}},
  {"id":"PWR3","part":"unknown","package":"6 pins, ~1.5 mm square","side":"front","size":1.5,"pitch":0.5,"pinCounts":[3,0,3,0],
   "notes":"Very likely power related; marked TC; pin 1 not verified, numbered from the first corner outlined",
   "corners":[[1421,1848],[1293,1853],[1297,1731],[1419,1730]],"pinNames":{}},
  {"id":"ANT","part":"chip antenna","package":"ceramic, ~3.6 x 1.6 mm","side":"front",
   "notes":"2.4 GHz Bluetooth antenna, fed at its left end by Bluetooth RF 3; the copper-free area above it is its keep-out zone",
   "corners":[[3615,1903],[3958,1903],[3958,2037],[3615,2037]]},
  // large copper pads, drawn as outlines instead of computed from a package
  {"id":"BAT","part":"battery contacts","package":"copper pads","side":"front","pads":[
    {"id":"1","name":"","notes":"One of the three battery pads is +, one is -, one is the temperature sensor; which is which is not known yet","polygon":[[891,1948],[894,1699],[1010,1698],[1007,1946]]},
    {"id":"2","name":"","notes":"One of the three battery pads is +, one is -, one is the temperature sensor; which is which is not known yet","polygon":[[1106,1947],[1111,1699],[1219,1699],[1217,1946]]},
    {"id":"3","name":"","notes":"One of the three battery pads is +, one is -, one is the temperature sensor; which is which is not known yet","polygon":[[967,1009],[971,898],[1216,894],[1216,1006]]}]}
];
