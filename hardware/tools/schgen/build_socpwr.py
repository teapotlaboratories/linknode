"""SoC Power sheet (T11): RV1106G3 U100 unit 1 (supply pins) and unit 6 (unused camera / Ethernet / audio pins).
Decoupling per soc/reference.md §1 (REF = RV1106G-AI-IPC-V13 p.7-10, HDG = Hardware Design Guide V1.1 §2.2.3):
 VDD_ARM 10u+1u+100n; VDD_0V9 2x10u + 2x1u + one 100n per pin (HDG text, 9 pins incl. PMU_DVDD0V9);
 VCC_DDR 2x10u+1u+100n; DDR_PLL 1u+100n; 100n on every other supply pin.
 Pin 96 (OTP/ETH/TSADC 1.8 V) through a 120R@100MHz bead (HDG §2.3.4); pins 24 (USB/SARADC 1.8 V) and 1 (MIPI/VCCIO7)
 through 1R (HDG §2.3.3, §2.3.7.1); RTC_AVDD3V3 through 100R + 1uF ("must", HDG §2.1.1).
 Unused blocks (owner-agnostic default, every reference powers them): CODEC_AVDD1V8 and FEPHY_AVDD3V3 direct + 100n,
 FEPHY_EXTR 6.04k 1%, CODEC_VCM 4.7u, CODEC_AVSS to GND, DRAM_ZQ 240R 1%, TVSS on the SoC sheet."""
import sys, json; sys.path.insert(0, sys.argv[1])
from blocks import *
import wires
S = Sheet()
SOC = 'linknode:RV1106G3'; FP = 'linknode:Rockchip_QFN-128-1EP_12.3x12.3mm_P0.35mm_EP7x7mm'
n = {'C': 600, 'R': 600}
def nxt(k): n[k] += 1; return '%s%d' % (k, n[k])
CAP = {'10uF': (C6, 'C19702'), '1uF': (C, 'C52923'), '100nF': (C, 'C1525'), '4.7uF': (C, 'C23733')}

# ===================== unit 1 at (60.96, 99.06): left pins x=35.56, right x=86.36, bottom y=147.32
UX, UY = 60.96, 99.06
S.part('U100', SOC, 'RV1106G3', FP, UX, UY, 0, None, unit=1)
L, Rx = 35.56, 86.36
# left: VDD_ARM (CPU_DVDD), VDD_0V9 group, VCC_DDR group
S.w((L, 63.5), (25.4, 63.5)); S.pwr('VDD_ARM', 25.4, 63.5, 90)
for y in (71.12, 73.66, 76.2, 78.74, 81.28, 83.82, 86.36, 88.9, 91.44):
    S.w((L, y), (30.48, y))
S.w((30.48, 71.12), (30.48, 91.44)); S.w((30.48, 81.28), (25.4, 81.28)); S.pwr('VDD_0V9', 25.4, 81.28, 90)
for y in (99.06, 101.6, 104.14):
    S.w((L, y), (30.48, y))
S.w((30.48, 99.06), (30.48, 104.14)); S.w((30.48, 101.6), (25.4, 101.6)); S.pwr('VCC_DDR', 25.4, 101.6, 90)
# right: VCC_1V8 direct group (70 OSC/PLL, 31 CODEC, 53 DDR_PLL)
for y in (63.5, 66.04, 68.58):
    S.w((Rx, y), (91.44, y))
S.w((91.44, 63.5), (91.44, 68.58)); S.w((91.44, 66.04), (96.52, 66.04)); S.pwr('VCC_1V8', 96.52, 66.04, 270)
# right: filtered pins: pin -> node (93.98) -> series part (101.6) -> rail symbol (106.68); cap at the node
def filt(y, ref, lib, val, fp, lcsc, rail, cval):
    S.w((Rx, y), (99.06, y))
    S.part(ref, lib, val, fp, 101.6, y, 90, lcsc)
    S.w((104.14, y), (106.68, y)); S.pwr(rail, 106.68, y, 270)
    cf, cl = CAP[cval]; c = nxt('C')
    S.part(c, 'Device:C_Small', cval, cf, 93.98, y + 2.54, 0, cl); S.pwr('GND', 93.98, y + 5.08)
filt(76.2, 'FB601', 'Device:FerriteBead_Small', '120R@100MHz', 'Inductor_SMD:L_0402_1005Metric', 'C76891', 'VCC_1V8', '100nF')   # pin 96
filt(86.36, nxt('R'), 'Device:R_Small', '1R', R, 'C2906901', 'VCC_1V8', '100nF')     # pin 24 USB/SARADC 1V8
filt(96.52, nxt('R'), 'Device:R_Small', '1R', R, 'C2906901', 'VCC_1V8', '100nF')     # pin 1 MIPI/VCCIO7
filt(106.68, nxt('R'), 'Device:R_Small', '100R', R, 'C25076', 'VCC_3V3', '1uF')      # pin 19 RTC
# right: VCC_3V3 direct group (61 PMU, 28 USB, 101 FEPHY, 81/43/13/108/88 VCCIO1/3/4/5/6)
for y in (119.38, 121.92, 124.46, 127.0, 129.54, 132.08, 134.62, 137.16):
    S.w((Rx, y), (91.44, y))
S.w((91.44, 119.38), (91.44, 137.16)); S.w((91.44, 127.0), (96.52, 127.0)); S.pwr('VCC_3V3', 96.52, 127.0, 270)
# bottom: EP and CODEC_AVSS to GND, DRAM_ZQ 240R 1%
S.pwr('GND', 55.88, 147.32); S.pwr('GND', 60.96, 147.32)
r = nxt('R'); S.part(r, 'Device:R_Small', '240R 1%', R, 66.04, 149.86, 0, 'C114755'); S.pwr('GND', 66.04, 152.4)

# ===================== decoupling banks: rail wire on top, caps at 7.62 mm pitch, GND wire below
def bank(rail, x0, y, vals):
    xs = [x0 + 7.62 * (i + 1) for i in range(len(vals))]
    S.pwr(rail, x0, y); S.w((x0, y), (xs[-1], y)); S.w((xs[0], y + 5.08), (xs[-1], y + 5.08)); S.pwr('GND', xs[0], y + 5.08)
    for x, v in zip(xs, vals):
        cf, cl = CAP[v]; S.part(nxt('C'), 'Device:C_Small', v, cf, x, y + 2.54, 0, cl)
    return xs
bank('VDD_ARM', 20.32, 25.4, ['10uF', '1uF', '100nF'])
bank('VDD_0V9', 55.88, 25.4, ['10uF', '10uF', '1uF', '1uF'] + ['100nF'] * 9)
bank('VCC_DDR', 167.64, 25.4, ['10uF', '10uF', '1uF', '100nF'])
bank('VCC_1V8', 213.36, 25.4, ['100nF', '100nF', '1uF', '100nF'])          # OSC/PLL, CODEC, DDR_PLL 1u + 100n
bank('VCC_3V3', 167.64, 45.72, ['100nF'] * 8)                               # PMU, USB, FEPHY, VCCIO1/3/4/5/6

# ===================== unit 6 (unused blocks) at (220.98, 99.06): left x=193.04 (all NC), right x=248.92
S.part('U100', SOC, 'RV1106G3', FP, 220.98, 99.06, 0, None, unit=6)
S.w((248.92, 86.36), (254.0, 86.36)); r = nxt('R'); S.part(r, 'Device:R_Small', '6.04k 1%', R, 254.0, 88.9, 0, 'C97819'); S.pwr('GND', 254.0, 91.44)   # FEPHY_EXTR
S.w((248.92, 104.14), (254.0, 104.14)); c = nxt('C'); S.part(c, 'Device:C_Small', '4.7uF', C, 254.0, 106.68, 0, 'C23733'); S.pwr('GND', 254.0, 109.22)  # CODEC_VCM

# PWR_FLAG on the four filtered supply nets (power input behind a series part, ERC power_pin_not_driven)
for y in (76.2, 86.36, 96.52, 106.68):
    S.pwr('FLAG', 88.9, y, 0)
NC = [str(p) for p in (117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 2, 3, 4, 5, 7, 6, 8, 9,
                       98, 97, 100, 99, 34, 33, 36, 35, 29, 32)]
plain, mir = S.payload(1100)
json.dump(dict(plain=plain, mir=mir, hier=[], nc=[['U100', p] for p in NC],
               lcsc={r: {'properties': {'LCSC': c}} for r, c in S.lcsc.items()}, wires=S.wires,
               pins=wires.pinpoints(S.parts, S.pw)), open(sys.argv[1] + '/socpwr_w.json', 'w'))
print(len(plain), 'plain', len(mir), 'single', len(S.wires), 'polylines', n)
