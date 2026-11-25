"""T41 Block 4: audit the parts around the RV1106 that are not in the approved decoupling ring (T29) and the microSD.
Usage: python3 blk4_audit.py <board.kicad_pcb> [out.json]

Pad-centre distances in mm. Source: `resources/resource/Rockchip-RV1103G-RV1106G-Hardware-Design-Guide-en-V1-1-20221221.pdf`
(HDG). The HDG says "close to" without numbers, so the limits are practice and are stated per row.
- §3.2 item 9 (p.41): series resistors near the transmitter -> SD_CLK R511, SDIO_CLK R513, SPI CLK R512 at their RV1106 pin.
- §2.1.1-2.1.2 (p.14-15): 24 MHz / 32.768 kHz crystals with NPO load caps; NPOR RC close to the chip (C505, R503).
- §2.3.5 (p.27): USB controller 1.8 V through 1 ohm, decoupling at the pin.
- ADC / detect filter caps at their pins (C506 USB_DET divider, C507 recovery SARADC_IN0, C508 CC sense SARADC_IN1):
  <= 3.5 mm, the closest spots just outside the RV1106 body (its bottom is kept for fan-out vias); these inputs are slow.
- microSD: VCC3V3_SD decoupling at the socket's VDD pin; power switch Q401 near the socket.
- §3.3.1 (p.46): ESD for the TF card close to the connector -> checked for presence (schematic item)."""
import sys, json, math, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
FP = {f.GetReference(): f for f in b.GetFootprints()}
def pads(ref, net=None, num=None):
    return [p for p in FP[ref].Pads() if (net is None or p.GetNetname() == net) and (num is None or p.GetNumber() == num)]
def pos(p): return (p.GetPosition().x/1e6, p.GetPosition().y/1e6)
def dmin(a, b_): return min(math.dist(pos(p), pos(q)) for p in a for q in b_)
def side(r): return 'B' if FP[r].IsFlipped() else 'T'
def netof(ref, num): return pads(ref, num=num)[0].GetNetname()
rows = []
def chk(grp, what, d, lim, ref, src, kind='rule'):
    rows.append(dict(conv=grp, what=what, ref=ref, d=round(d, 2), lim=lim, more=False, kind=kind,
                     ok=True if kind == 'info' else d <= lim, src=src, side=side(ref) if ref in FP else '-'))
def at(grp, what, part, ic, num, lim, src, kind='rule'):
    n = netof(ic, num); chk(grp, what, dmin(pads(part, n), pads(ic, num=num)), lim, part, src, kind)
H9 = 'HDG §3.2 item 9 (p.41)'
at('Series R', 'SD_CLK 22R at RV1106 pin 15', 'R511', 'U100', '15', 3.0, H9)
at('Series R', 'SDIO_CLK 22R at RV1106 pin 111', 'R513', 'U100', '111', 3.0, H9)
at('Series R', 'SPI1 CLK 22R at RV1106 pin 38', 'R512', 'U100', '38', 3.0, H9)
HC = 'HDG §2.1.1-2.1.2 (p.14-15)'
at('Clocks', '24 MHz crystal at XIN (pin 68)', 'Y501', 'U100', '68', 4.0, HC)
at('Clocks', '24 MHz load cap C502 at XIN', 'C502', 'U100', '68', 4.0, HC)
at('Clocks', '32.768 kHz crystal at RTC pin 20', 'Y502', 'U100', '20', 0, HC + ' (placed in T30 to open the USB channel)', 'info')
at('Clocks', '32.768 kHz crystal at RTC pin 21', 'Y502', 'U100', '21', 0, HC + ' (placed in T30)', 'info')
at('Clocks', 'NPOR cap C505 at pin 66', 'C505', 'U100', '66', 2.5, HC)
at('Clocks', 'NPOR resistor R503 at pin 66', 'R503', 'U100', '66', 4.0, HC)
HU = 'HDG §2.3.5 (p.27)'
at('USB', 'USB 1.8 V series 1R (R601) at pin 24', 'R601', 'U100', '24', 0, HU + ' (series R on a supply: info)', 'info')
at('USB', 'VBUS detect: 15k R507 at pin 25', 'R507', 'U100', '25', 3.0, 'practice: divider at the ADC/detect pin')
at('USB', 'VBUS detect filter C506 at pin 25', 'C506', 'U100', '25', 3.5, 'practice: filter cap at the input pin, just outside the RV1106 body (bottom under it is kept for fan-out vias); slow / near-DC input')
at('ADC', 'Recovery SARADC_IN0 cap C507 at pin 23', 'C507', 'U100', '23', 3.5, 'practice: filter cap at the input pin, just outside the RV1106 body (bottom under it is kept for fan-out vias); slow / near-DC input')
at('ADC', 'CC sense SARADC_IN1 cap C508 at pin 22', 'C508', 'U100', '22', 3.5, 'practice: filter cap at the input pin, just outside the RV1106 body (bottom under it is kept for fan-out vias); slow / near-DC input (requirement H-15)')
at('ADC', 'DDR ZQ 240R (R604) at pin 52', 'R604', 'U100', '52', 4.0, 'practice: reference resistor at its pin')
HS = 'microSD sheet; HDG §3.3.1 (p.46)'
at('microSD', '100 nF C404 at socket VDD (pin 4)', 'C404', 'J401', '4', 2.0, HS)
at('microSD', '100 nF C402 at socket VDD', 'C402', 'J401', '4', 3.0, HS)
at('microSD', '4.7 uF C401 at socket VDD', 'C401', 'J401', '4', 4.0, HS)
chk('microSD', 'power switch Q401 drain to socket VDD', dmin(pads('Q401', num='3'), pads('J401', num='4')), 6.0, 'Q401', HS)
esd = [f.GetReference() for f in b.GetFootprints() if any(p.GetNetname().endswith(('SD_CLK', 'SD_CMD', 'SD_D0')) for p in f.Pads())
       and f.GetReference()[0] in 'UD' and f.GetReference() != 'U100']
rows.append(dict(conv='microSD', what='ESD on the TF card lines (HDG: < 1 pF, at the connector)', ref='J401', d=len(esd), lim=1, more=True,
                 kind='info', ok=True, src='HDG §3.3.1 (p.46): schematic has none', side='T'))
rule = [r for r in rows if r['kind'] == 'rule']
out = dict(rows=rows, fails=sum(not r['ok'] for r in rule), total=len(rule), info=len(rows) - len(rule))
for r in rows:
    tag = 'info' if r['kind'] == 'info' else ('ok  ' if r['ok'] else 'FAIL')
    print(f"{tag} {r['conv']:9s} {r['what']:42s} {r['ref']:5s} {r['side']} {r['d']:6.2f} {'' if r['kind']=='info' else '(<= %g)' % r['lim']}")
print(f"{out['fails']} of {out['total']} rule checks fail ({out['info']} info rows)")
if len(sys.argv) > 2: json.dump(out, open(sys.argv[2], 'w'), indent=1)
