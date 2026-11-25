# Handheld solar panel options (P-11)

Collected 2026-11-20 with a headless browser (Playwright with the existing Chromium build; scripts in
`hardware/tools/web/`). Prices are qty 1 in USD, shown to a US visitor. AliExpress prices are the regular
(struck-through) price, not the new-shopper coupon price ($1.09 on every variant). LCSC sells no solar panels, so
the panel is a non-LCSC part (H-7).

Seller ratings for the cheap panels are not datasheet figures. One buyer measured a "1.92 W" panel at about
0.85 W (170 mA at 5.03 V). Buy samples and measure Voc, Isc and the I-V curve before choosing.

## AliExpress

SunMoonMall store, "4V 5.5V 5V 6V 7V 10V 12V Mono/Polycrystalline Solar Panel … Epoxy Board PET", 5,000+ sold:
https://www.aliexpress.us/item/3256809207132616.html. Variant names are the seller's (voltage, rated current, size
in mm). Watts are voltage × rated current.

| Variant | Rated W | Size (mm) | Price |
|---|---|---|---|
| 6V 500mA 145x145 Cable | 3.0 | 145 × 145 | $5.99 |
| 6V 250mA 165x65 Cable | 1.5 | 165 × 65 | $4.88 |
| 6V 220mA 120x90 Cable | 1.3 | 120 × 90 | $3.68 |
| 6V 183mA 133x72 Cable | 1.1 | 133 × 72 | $4.04 |
| 5.5V 240mA 147x90 Cable | 1.3 | 147 × 90 | $4.02 |
| 5V 230mA 100.8x82.5 | 1.15 | 101 × 83 | $3.08 (a buyer measured Voc 6.10 V, Isc 252 mA) |
| 7V 120mA 110x110 Cable | 0.84 | 110 × 110 | $4.14 |

TZT "6V 320mA 1.92W Solar Panel Polycrystalline 140*104MM", $3.19 ($2.93 on sale):
https://www.aliexpress.us/item/3256807713324066.html

## DigiKey (datasheet-backed, but 3–10× the price)

From https://www.digikey.com/en/products/result?keywords=solar%20panel%206V (Solar Cells, 10 results):

| Part | W (max) | Vmp | Voc | Size (mm) | Price |
|---|---|---|---|---|---|
| Voltaic P124 | 1.22 | 6.07 V | 7.09 V | 113 × 66 | $14.00 |
| Voltaic P105 | 5.75 | 6.12 V | 7.13 V | 222 × 137 | $35.00 |
| Adafruit 5366 (Voltaic ETFE) | 2.37 | 7.28 V | 8.51 V | 136 × 112 | $26.19 |
| Voltaic P110 | 9.54 | 5.71 V | 6.94 V | 274 × 223 | $65.00 |

The Voltaic P105 drawing (`hardware/datasheets/Voltaic_P105_dwg.pdf`, rev R9C, 2025-09-03) gives these figures,
±10 % on voltage and current:

- Size: 223 × 148 mm.
- Voc: 7.28 V nominal, 7.07 V expected.
- Vmp: 6.23 V nominal, 6.01 V expected.
- Isc: 1.00 A nominal, 0.93 A expected.
- Pmax: 5.89 W nominal, 4.98 W expected.
- Cells: SunPower Maxeon Gen III.

The drawing gives no temperature coefficient.

## What this means for the design

- **Voc against the BQ25798's VAC_OVP.** A "6 V" panel has a Voc of 7.0–8.5 V (7.28 V ±10 % for the P105), and Voc
  rises in the cold. If the VAC_OVP POR default is 7 V (the p.72 contradiction, T17a), many of these panels trip it
  before firmware runs, and the cold start (P-8) fails. A "5 V" panel (a buyer measured 6.1 V Voc) clears 7 V but
  gives less power. Settle VAC_OVP first. If it really is 7 V, choose a 5 V panel or add a hardware fix.
- **Energy.** Using the budget's assumptions (4 peak-sun hours, 75 % harvest, **EST**):
  - A 3 W panel (145 × 145 mm, $5.99) gives about 9 Wh a day, a 0.375 W average.
  - A 1.3 W panel gives about 3.9 Wh, a 0.16 W average.
  - A 5 W P105 (expected rating) gives about 15 Wh, a 0.62 W average.
  - All of these are far below the always-listening 1.8 W (Q-13).
- **Suggested samples** (about $13 plus shipping) to measure before choosing:
  - 6V 500mA 145×145 ($5.99).
  - 5.5V 240mA 147×90 ($4.02).
  - TZT 6V 1.92 W 140×104 ($3.19).

## Connector on the node (H-13, owner 2026-11-20)

The panel plugs in from outside through a board-edge DC-005 barrel jack: 5.5 × 2.1 mm plug, centre pin positive,
LCSC C16214, $0.06. Its rating is DC 12 V 1 A (`hardware/datasheets/XKB_DC-005.pdf`). Every panel above needs a
5.5 × 2.1 mm plug on its cable. The AliExpress "Cable" variants come with bare wires, so fit a plug or a pigtail.
