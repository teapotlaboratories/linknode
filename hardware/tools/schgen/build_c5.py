"""ESP32-C5 sheet (T13): ESP32-C5-WROOM-1U-N16R8 (C54951857) on VCC3V3_C5 (switched TLV62569, Radio Power sheet).
Module datasheet v1.3 (esp32-c5-wroom-1_wroom-1u_datasheet_en.pdf): Fig 9-2 p.50 (22 uF + 0.1 uF on 3V3; EN RC
R = 10k, C = 1 uF), boot straps p.16-18 (GPIO28 = 1 SPI boot / 0 joint download; GPIO27 internal pull-up, GPIO26
'any' in both modes we use), Table 3-2 pins. Link to the RV1106: SPI slave on the IO_MUX FSPI pins (IO6 CLK, IO7 MOSI,
IO2 MISO, IO10 CS), handshake IO23, data-ready IO24, UART0 for console/esptool, EN and IO28 driven open-drain by the
RV1106 (10k pull-ups here). ANT1 is the module's U.FL; ANT2 (pin 31) unused (default, p.15 note 4)."""
import sys, json; sys.path.insert(0, sys.argv[1])
from blocks import *
import wires
S = Sheet(); H = S.hier
def hl(name, x, y, rot, shape): H.append((name, x, y, rot, shape))
S.part('U801', 'linknode:ESP32-C5-WROOM-1U', 'ESP32-C5-WROOM-1U-N16R8', 'linknode:ESP32-C5-WROOM-1U', 139.7, 101.6, 0, 'C54951857')
row = lambda r: round(73.66 + 2.54 * (r + 1), 2)
for r, name, sh in ((0, 'C5_SPI_CLK', 'input'), (1, 'C5_SPI_MOSI', 'input'), (2, 'C5_SPI_MISO', 'output'), (3, 'C5_SPI_CS', 'input'),
                    (5, 'C5_HANDSHAKE', 'output'), (6, 'C5_DATA_READY', 'output'), (8, 'C5_UART_TX', 'output'), (9, 'C5_UART_RX', 'input'),
                    (13, 'C5_EN', 'input'), (20, 'C5_BOOT', 'input')):
    S.w((121.92, row(r)), (88.9, row(r))); hl(name, 88.9, row(r), 180, sh)
# EN: 10k pull-up + 1 uF (p.50)
y = row(13)
S.part('R801', 'Device:R_Small', '10k', R, 106.68, y - 2.54, 0, 'C25744'); S.pwr('VCC3V3_C5', 106.68, y - 5.08)
S.part('C801', 'Device:C_Small', '1uF', C, 99.06, y + 2.54, 0, 'C52923'); S.pwr('GND', 99.06, y + 5.08)
# IO28 boot strap: 10k pull-up (SPI boot unless the RV1106 holds it low through EN reset)
y = row(20)
S.part('R802', 'Device:R_Small', '10k', R, 106.68, y - 2.54, 0, 'C25744'); S.pwr('VCC3V3_C5', 106.68, y - 5.08)
# 3V3 with 22 uF + 0.1 uF (p.50)
S.w((139.7, 71.12), (139.7, 60.96), (119.38, 60.96)); S.pwr('VCC3V3_C5', 119.38, 60.96, 90)
S.part('C802', 'Device:C_Small', '22uF', C6, 129.54, 63.5, 0, 'C59461'); S.pwr('GND', 129.54, 66.04)
S.part('C803', 'Device:C_Small', '100nF', C, 124.46, 63.5, 0, 'C1525'); S.pwr('GND', 124.46, 66.04)
S.pwr('GND', 139.7, 132.08)
NC = [['U801', p] for p in ('6', '7', '5', '17', '16', '10', '11', '13', '14', '19', '26', '27', '18', '20', '22', '31')]
plain, mir = S.payload(1400)
json.dump(dict(plain=plain, mir=mir, hier=H, nc=NC, lcsc={r: {'properties': {'LCSC': c}} for r, c in S.lcsc.items()}, wires=S.wires,
               pins=wires.pinpoints(S.parts, S.pw) + [(x, y) for _, x, y, *r in H]), open(sys.argv[1] + '/c5_w.json', 'w'))
print(len(plain), 'plain', len(mir), 'single', len(S.wires), 'polylines', len(H), 'hier')
