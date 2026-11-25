"""T41 Block 3: audit the radio placement (HaLow HT-HC01 V2, ESP32-C5-WROOM-1U, ATGM336H GPS and its LDOs).
Usage: python3 blk3_audit.py <board.kicad_pcb> [out.json]

Pad-centre distances in mm. Sources:
- HaLow: Heltec HT-HC01 V2 SDIO reference (`Heltec_HT-HC01_V2_SDIO_reference.pdf`): 100 nF + 10 uF on each supply pin
  (VDD_IO 19, VBAT 25, VDD_FEM 32), 10k pulls on SDIO/GPIO. Heltec publishes no layout guide, so the limits are the usual
  decoupling practice: 100 nF pad <= 2.0 mm from its pin, 10 uF <= 3.5 mm; pulls are info only.
- ESP32-C5: `esp32-c5-wroom-1_wroom-1u_datasheet_en.pdf` §9 Fig 9-2 (p.50): 22 uF + 0.1 uF on 3V3 (pin 2), RC delay
  10k / 1 uF on EN (pin 3). Same limits.
- GPS: `ZHONGKEWEI_ATGM336H-5NR32-G.pdf` §2.8 (p.11): antenna connector as close as possible to RF_IN (pin 11), low-ripple
  LDO, keep fast digital signals away. LDO caps (ME6211 U21, XC6206 U22) at their pins (datasheet application circuits;
  neither datasheet gives a distance, so <= 2.0 mm as practice). L20 feeds VCC_RF (pin 14) to the RF line.
- Floorplan: switching inductors >= 5.5 mm from the HaLow module (B6), and reported for the GPS module."""
import sys, json, math, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
FP = {f.GetReference(): f for f in b.GetFootprints()}
def pads(ref, net=None, num=None):
    return [p for p in FP[ref].Pads() if (net is None or p.GetNetname() == net) and (num is None or p.GetNumber() == num)]
def pos(p): return (p.GetPosition().x/1e6, p.GetPosition().y/1e6)
def dmin(a, b_): return min(math.dist(pos(p), pos(q)) for p in a for q in b_)
def side(r): return 'B' if FP[r].IsFlipped() else 'T'
def pin(ic, num): return pads(ic, num=num)
def netof(ref, num): return pin(ref, num)[0].GetNetname()
rows = []
def chk(conv, what, d, lim, ref, src, kind='rule', more=False):
    ok = True if kind == 'info' else (d >= lim if more else d <= lim)
    rows.append(dict(conv=conv, what=what, ref=ref, d=round(d, 2), lim=lim, more=more, kind=kind, ok=ok, src=src, side=side(ref)))
def at(conv, what, cap, ic, num, lim, src, kind='rule'):
    n = netof(ic, num); chk(conv, what, dmin(pads(cap, n), pin(ic, num)), lim, cap, src, kind)

H = 'Heltec SDIO reference'; conv = 'U701 HaLow'
for p_, small, big, name in (('19', 'C703', 'C704', 'VDD_IO'), ('25', 'C701', 'C702', 'VBAT'), ('32', 'C705', 'C706', 'VDD_FEM')):
    at(conv, f'100 nF at {name} (pin {p_})', small, 'U701', p_, 2.0, H)
    at(conv, f'10 uF at {name} (pin {p_})', big, 'U701', p_, 3.5, H)
for r, p_ in (('R701', '18'), ('R702', '21'), ('R703', '17'), ('R704', '16'), ('R705', '23'), ('R706', '22'), ('R707', '34')):
    at(conv, f'pull on pin {p_}', r, 'U701', p_, 0, H, 'info')
E = 'ESP32-C5-WROOM-1U datasheet §9, Fig 9-2'; conv = 'U801 ESP32-C5'
at(conv, '0.1 uF at 3V3 (pin 2)', 'C803', 'U801', '2', 2.0, E)
at(conv, '22 uF at 3V3 (pin 2)', 'C802', 'U801', '2', 3.5, E)
at(conv, 'EN RC: 1 uF at EN (pin 3)', 'C801', 'U801', '3', 2.5, E)
at(conv, 'EN RC: 10k at EN (pin 3)', 'R801', 'U801', '3', 2.5, E)
at(conv, 'BOOT pull-up at pin 15', 'R802', 'U801', '15', 0, E, 'info')
G = 'ATGM336H manual §2.8 + LDO application circuits'; conv = 'U20 GPS'
chk(conv, 'U.FL signal pad to RF_IN (pin 11)', dmin(pads('J20', num='1'), pin('U20', '11')), 3.0, 'J20', G)
chk(conv, 'L20 at VCC_RF (pin 14)', dmin(pads('L20', netof('U20', '14')), pin('U20', '14')), 3.0, 'L20', G)
chk(conv, 'L20 at the RF line', dmin(pads('L20', netof('U20', '11')), pin('U20', '11') + pads('J20', num='1')), 2.5, 'L20', G)
chk(conv, 'LDO U21 out to GPS VCC (pin 8)', dmin(pin('U21', '5'), pin('U20', '8')), 6.0, 'U21', G)
at(conv, 'U21 input cap C200', 'C200', 'U21', '1', 2.0, G)
at(conv, 'U21 output cap C201', 'C201', 'U21', '5', 2.0, G)
at(conv, '10 uF C202 at GPS VCC (pin 8)', 'C202', 'U20', '8', 2.5, G)
at(conv, 'U22 input cap C203', 'C203', 'U22', '3', 2.0, G)
at(conv, 'U22 output cap C204 at GPS VBAT (pin 6)', 'C204', 'U20', '6', 2.5, G)
def cbox(f):
    L = pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd; xs, ys = [], []
    for g in f.GraphicalItems():
        if g.GetLayer() == L: r = g.GetBoundingBox(); xs += [r.GetLeft(), r.GetRight()]; ys += [r.GetTop(), r.GetBottom()]
    return min(xs)/1e6, min(ys)/1e6, max(xs)/1e6, max(ys)/1e6
def boxgap(a, c): return math.hypot(max(0, a[0] - c[2], c[0] - a[2]), max(0, a[1] - c[3], c[1] - a[3]))
for L in ['L1', 'L2', 'L5', 'L6', 'L7', 'L8', 'L10', 'L11']:
    chk('Floorplan', 'inductor to HaLow module', boxgap(cbox(FP[L]), cbox(FP['U701'])), 5.5, L, 'B6 floorplan rule', more=True)
chk('Floorplan', 'nearest switching inductor to GPS module', min(boxgap(cbox(FP[L]), cbox(FP['U20'])) for L in ['L1', 'L2', 'L5', 'L6', 'L7', 'L8', 'L10', 'L11']),
    0, 'U20', G + ' (keep noise away)', 'info')
rule = [r for r in rows if r['kind'] == 'rule']
out = dict(rows=rows, fails=sum(not r['ok'] for r in rule), total=len(rule), info=len(rows) - len(rule))
for r in rows:
    tag = 'info' if r['kind'] == 'info' else ('ok  ' if r['ok'] else 'FAIL')
    lim = '' if r['kind'] == 'info' else f"({'>=' if r['more'] else '<='} {r['lim']})"
    print(f"{tag} {r['conv']:14s} {r['what']:40s} {r['ref']:5s} {r['side']} {r['d']:6.2f} {lim}")
print(f"{out['fails']} of {out['total']} rule checks fail ({out['info']} info rows)")
if len(sys.argv) > 2: json.dump(out, open(sys.argv[2], 'w'), indent=1)
