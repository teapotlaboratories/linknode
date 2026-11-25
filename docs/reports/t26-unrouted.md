# T26 layout: unrouted connections for the owner to finish in KiCad

Board: `hardware/kicad/klepon.kicad_pcb`, generated 2026-11-21 from kicad-cli DRC (zones refilled). 24 unconnected, parity 0, no clearance/short/hole errors.

Rules already set: Default 0.12/0.12, via 0.4/0.2; SoCPower (U100 rails) 0.2/0.12; Power 0.3/0.15; USB90 0.155/0.127 gap; RF50 0.17/0.2.
In1 is the solid GND plane (keep it unbroken). In2 carries signals plus VCC5V0_SYS/VDD_0V9 pours. Coordinates are in mm, board origin as in KiCad.

| # | Net | From | To | Hint |
|---|---|---|---|---|
| 1 | `GND` | Zone on F.Cu | Pad 2 of C6 on F.Cu (123.73, 160.25) | drop a GND via next to the pad (or let the F.Cu GND fill reach it); for zone-only rows, add one stitching via in that F.Cu GND island |
| 2 | `GND` | Zone on F.Cu | Pad 2 of U7 on F.Cu (141.11, 158.00) | drop a GND via next to the pad (or let the F.Cu GND fill reach it); for zone-only rows, add one stitching via in that F.Cu GND island |
| 3 | `GND` | Zone on F.Cu | Zone on F.Cu | drop a GND via next to the pad (or let the F.Cu GND fill reach it); for zone-only rows, add one stitching via in that F.Cu GND island |
| 4 | `GND` | Track on F.Cu, 0.6500 mm (149.73, 149.50) | Pad 57 of U100 on F.Cu (150.97, 148.00) | drop a GND via next to the pad (or let the F.Cu GND fill reach it); for zone-only rows, add one stitching via in that F.Cu GND island |
| 5 | `GND` | Zone on F.Cu | Zone on F.Cu | drop a GND via next to the pad (or let the F.Cu GND fill reach it); for zone-only rows, add one stitching via in that F.Cu GND island |
| 6 | `VSYS` | Track on F.Cu, 0.7500 mm (118.03, 153.00) | Track on F.Cu, 0.4525 mm (120.75, 155.73) | short F.Cu link between C16/C19 VSYS pads; nudge C16 if needed |
| 7 | `VDD_0V9` | Pad 71 of U100 on F.Cu (154.00, 145.32) | Pad 67 of U100 on F.Cu (154.00, 146.72) | 0.2 mm stub out of the U100 pad to a via onto the In2 VDD_0V9 island |
| 8 | `VDD_0V9` | Pad 71 of U100 on F.Cu (154.00, 145.32) | Track on In2.Cu, 4.6337 mm (150.03, 147.22) | 0.2 mm stub out of the U100 pad to a via onto the In2 VDD_0V9 island |
| 9 | `Net-(U4-FB)` | Pad 3 of U4 on F.Cu (111.83, 142.25) | Pad 2 of R15 on F.Cu (108.76, 139.25) | a VCC5V0_SYS via about 0.3 mm left of U4 pin 3 blocks the exit; move that via, then route FB to R15 |
| 10 | `Net-(U4-ILIM)` | Pad 8 of U4 on F.Cu (114.17, 142.25) | Pad 1 of R14 on F.Cu (115.00, 145.74) | route U4 pin 8 down to R14; same congestion as FB |
| 11 | `Net-(U100Power-SARADC_USB_AVDD1V8)` | Pad 1 of C602 on F.Cu (138.00, 144.48) | Pad 24 of U100 on F.Cu (142.00, 144.62) | C602/R601 to U100 pin 24; nudge C602 closer to the pin if needed |
| 12 | `Net-(U100Power-SARADC_USB_AVDD1V8)` | Pad 1 of R601 on F.Cu (138.51, 140.50) | Pad 1 of C602 on F.Cu (138.00, 144.48) | C602/R601 to U100 pin 24; nudge C602 closer to the pin if needed |
| 13 | `VCC_3V3` | Track on F.Cu, 0.5210 mm (142.52, 140.78) | Track on F.Cu, 0.2900 mm (140.50, 143.27) | 0.2 mm stub to a via; 3V3 runs on In2 nearby |
| 14 | `VCC_3V3` | Track on F.Cu, 0.8108 mm (145.29, 146.77) | Track on In2.Cu, 2.3773 mm (142.88, 146.19) | 0.2 mm stub to a via; 3V3 runs on In2 nearby |
| 15 | `VCC_3V3` | Pad 1 of C632 on F.Cu (155.02, 151.75) | Track on F.Cu, 2.0506 mm (156.50, 154.51) | 0.2 mm stub to a via; 3V3 runs on In2 nearby |
| 16 | `VCC_1V8` | Track on In2.Cu, 2.4119 mm (147.09, 151.04) | Pad 53 of U100 on F.Cu (149.57, 148.00) | 0.2 mm stub out of the pad, then via to In2 |
| 17 | `VCC_1V8` | Pad 53 of U100 on F.Cu (149.57, 148.00) | Pad 70 of U100 on F.Cu (154.00, 145.68) | 0.2 mm stub out of the pad, then via to In2 |
| 18 | `/SoC/SD_D1` | Pad 12 of U100 on F.Cu (142.00, 140.43) | Track on F.Cu, 0.2418 mm (151.17, 164.57) | about 26 mm, U100 left side to the microSD; route with the other SD lines (they need length matching anyway) |
| 19 | `/SoC/SD_D3` | Track on F.Cu, 0.0375 mm (158.10, 164.43) | Pad 17 of U100 on F.Cu (142.00, 142.18) | about 27 mm, same as SD_D1 |
| 20 | `Net-(U100System-USB_DP)` | Pad 27 of U100 on F.Cu (142.00, 145.68) | Track on F.Cu, 0.6972 mm (144.24, 149.69) | U100 pin 27 to R508; reroute DM with it as a coupled 90 ohm pair (USB90) |
| 21 | `Net-(U2-ILIM_HIZ)` | Track on F.Cu, 0.2000 mm (128.04, 152.97) | Track on B.Cu, 0.3295 mm (128.04, 152.97) | tracks on two layers meet with no via at (128.04, 152.97) / (128.04, 153.70); add one via |
| 22 | `Net-(U2-ILIM_HIZ)` | Track on F.Cu, 0.0578 mm (128.09, 153.67) | Track on In2.Cu, 0.7290 mm (128.04, 153.70) | tracks on two layers meet with no via at (128.04, 152.97) / (128.04, 153.70); add one via |
| 23 | `VBUS` | Track on F.Cu, 1.5510 mm (125.20, 166.40) | Pad 9 of U2 on F.Cu (125.85, 158.40) | U2 pin 9 (VAC1 sense, low current) to the VBUS track near (125.2, 166.4) |
| 24 | `Net-(U2-PMID)` | Track on F.Cu, 0.0519 mm (119.57, 158.85) | Track on In2.Cu, 1.7621 mm (119.52, 158.84) | tracks on two layers meet with no via at (119.5, 158.8); add one via |

After you finish, report back; DRC with parity runs next, then the quality pass:
1. USB D+/D- as a coupled 90 ohm pair (USB90 class).
2. SD (SDMMC0) and HaLow SDIO length matching.
3. Power paths widened (charger, boost, battery).
4. Dangling vias and tracks swept (14 vias, 5 tracks right now).
5. Silkscreen tidy.
6. Final DRC and parity, then exports and the report.
