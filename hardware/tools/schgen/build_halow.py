"""HaLow sheet (T12): Heltec HT-HC01 V2 on SDIO (RV1106 SDIO_M0, VCCIO5 3.3 V).
Heltec_HT-HC01_V2.pdf p.9 notes + Heltec_HT-HC01_V2_SDIO_reference.pdf:
 SDIO CLK/CMD/D0-D3 pulled up 10k to VDD_IO; JTAG and unused GPIO 10k to GND; BUSY (GPIO_0) 10k to GND;
 VBAT, VDD_IO: 10u + 100n each; VDD_FEM: 10u + 100n. VDDIO must not exceed VBAT (p.18): both on VCC3V3_HALOW.
 ANT goes to the Antenna sheet (DC block, match, low-pass there, T14). 22R on SDIO_CLK sits on the SoC sheet."""
import sys, json; sys.path.insert(0, sys.argv[1])
from blocks import *
import wires
S = Sheet(); H = S.hier
def hl(name, x, y, rot, shape): H.append((name, x, y, rot, shape))
RN = 'Resistor_SMD:R_Array_Convex_4x0402'
UX, UY = 139.7, 101.6                 # module: left pins x=119.38, right x=160.02, top pins y=63.5, GND y=139.7
S.part('U701', 'linknode:HT-HC01_V2', 'HT-HC01_V2', 'linknode:HT-HC01_V2', UX, UY, 0, None)
row = lambda r: round(66.04 + 2.54 * (r + 1), 2)
# --- SDIO with pull-ups to VCC3V3_HALOW (VDD_IO)
n = [700]
def nxt(): n[0] += 1; return 'R%d' % n[0]
for r, name, sh in ((0, 'HALOW_SDIO_CLK', 'input'), (4, 'HALOW_SDIO_CMD', 'bidirectional'), (8, 'HALOW_SDIO_D0', 'bidirectional'),
                    (12, 'HALOW_SDIO_D1', 'bidirectional'), (16, 'HALOW_SDIO_D2', 'bidirectional'), (20, 'HALOW_SDIO_D3', 'bidirectional')):
    y = row(r)
    S.w((119.38, y), (78.74, y)); hl(name, 78.74, y, 180, sh)
    S.part(nxt(), 'Device:R_Small', '10k', R, 106.68, y - 2.54, 0, 'C25744'); S.pwr('VCC3V3_HALOW', 106.68, y - 5.08)
for r, name, sh in ((24, 'HALOW_RESET_N', 'input'), (25, 'HALOW_WAKE', 'input')):
    S.w((119.38, row(r)), (78.74, row(r))); hl(name, 78.74, row(r), 180, sh)
y = row(26); S.w((119.38, y), (78.74, y)); hl('HALOW_BUSY', 78.74, y, 180, 'output')
S.part(nxt(), 'Device:R_Small', '10k', R, 106.68, y + 2.54, 0, 'C25744'); S.pwr('GND', 106.68, y + 5.08)     # BUSY pull-down
# --- antenna to the Antenna sheet
S.w((160.02, row(0)), (172.72, row(0))); hl('HALOW_ANT', 172.72, row(0), 0, 'bidirectional')
# --- JTAG + unused GPIO pull-downs: 4x10k arrays in line, right ends on a GND bus (x=180.34)
for k, r0 in enumerate((2, 7, 12, 17)):
    yc = row(r0) + 5.08
    S.part('RN%d' % (701 + k), 'Device:R_Pack04', '4x10k', RN, 170.18, yc, 270, 'C25725')
    rows = (r0, r0 + 1, r0 + 2, r0 + 3) if r0 != 17 else (17, 18)
    for rr in rows:
        S.w((160.02, row(rr)), (165.1, row(rr))); S.w((175.26, row(rr)), (180.34, row(rr)))
S.w((180.34, row(2)), (180.34, row(18) + 2.54)); S.pwr('GND', 180.34, row(18) + 2.54)
# --- supplies with local decoupling (Heltec reference: 10u + 100n per supply)
C10 = ('10uF', C6, 'C19702'); C01 = ('100nF', C, 'C1525')
cn = [700]
def cap(x, ytop, spec):
    cn[0] += 1; v, fp, l = spec; S.part('C%d' % cn[0], 'Device:C_Small', v, fp, x, ytop + 2.54, 0, l); S.pwr('GND', x, ytop + 5.08)
S.w((134.62, 63.5), (134.62, 55.88), (119.38, 55.88)); S.pwr('VCC3V3_HALOW', 119.38, 55.88, 90)        # VBAT
cap(129.54, 55.88, C01); cap(124.46, 55.88, C10)
S.w((139.7, 63.5), (139.7, 48.26), (81.28, 48.26)); S.pwr('VCC3V3_HALOW', 81.28, 48.26, 90)              # VDD_IO
cap(93.98, 48.26, C01); cap(88.9, 48.26, C10)
S.w((144.78, 63.5), (144.78, 55.88), (167.64, 55.88)); S.pwr('VDD_FEM', 167.64, 55.88, 270)               # VDD_FEM
cap(149.86, 55.88, C01); cap(154.94, 55.88, C10)
S.pwr('GND', 139.7, 139.7)
NC = [['U701', '6'], ['U701', '10'], ['U701', '11'], ['RN704', '3'], ['RN704', '4'], ['RN704', '5'], ['RN704', '6']]
plain, mir = S.payload(1300)
json.dump(dict(plain=plain, mir=mir, hier=H, nc=NC, lcsc={r: {'properties': {'LCSC': c}} for r, c in S.lcsc.items()}, wires=S.wires,
               pins=wires.pinpoints(S.parts, S.pw) + [(x, y) for _, x, y, *r in H]), open(sys.argv[1] + '/halow_w.json', 'w'))
print(len(plain), 'plain', len(mir), 'single', len(S.wires), 'polylines', len(H), 'hier')
