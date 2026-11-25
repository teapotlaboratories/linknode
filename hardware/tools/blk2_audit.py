"""T41 Block 2: audit the power-section placement against the TI layout guidance.
Usage: python3 blk2_audit.py <board.kicad_pcb> [out.json]

Pad-centre distances in mm. 'rule' rows carry a limit set from the TI layout example for that part (what the example
achieves with the same package sizes); 'info' rows are reported only, where the TI example itself has the same distance
(for example the TLV62569 GND pin sits on the far side of the package from VIN, SLVSDG1C Fig 20).
- TLV62569 SLVSDG1C §10.1 + Fig 20 (p.13): Cin, L, Cout close to the IC; Cout GND at the IC GND; FB divider at FB, away from SW.
- TPS61089 SLVSD38C §11.1 + Fig 11-1 (p.22): Cout at VOUT *and* GND (the boost hot loop); Cin at VIN; SW area small.
- BQ25798 SLUSDV2C §8.4.1 + Fig 8-21 (p.139-140), priority list 1-7.
Also checks: every listed part on the IC's side (BTST caps and small parts on the bottom are by design)."""
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
    """more=True: the distance must be at least lim (keep-away)."""
    ok = True if kind == 'info' else (d >= lim if more else d <= lim)
    rows.append(dict(conv=conv, what=what, ref=ref, d=round(d, 2), lim=lim, more=more, kind=kind, ok=ok, src=src,
                     side=side(ref)))
def near(conv, what, a, b_, lim, ref, src, kind='rule'): chk(conv, what, dmin(a, b_), lim, ref, src, kind)

TLV = dict(U5=('C50', 'L5', ['C53'], ['R51', 'R52', 'C52']), U6=('C60', 'L6', ['C63'], ['R61', 'R62', 'C62']),
           U7=('C70', 'L7', ['C73'], ['R71', 'R72', 'C72']), U8=('C80', 'L8', ['C83'], ['R81', 'R82', 'C82']),
           U10=('C100', 'L10', ['C102', 'C103'], ['R101', 'R102', 'C101']), U11=('C110', 'L11', ['C112', 'C113'], ['R111', 'R112', 'C111']))
S1 = 'SLVSDG1C §10.1, Fig 20'
for ic, (cin, L, couts, fb) in TLV.items():
    conv = f'{ic} TLV62569'; vout = netof(L, '2'); sw = pin(ic, '3') + pads(L, num='1'); fbn = netof(ic, '5')
    near(conv, 'Cin + at VIN', pads(cin, 'VCC5V0_SYS'), pin(ic, '4'), 2.0, cin, S1)
    near(conv, 'Cin GND to IC GND', pads(cin, 'GND'), pin(ic, '2'), 0, cin, S1 + ' (GND pin opposite VIN; via the pour)', 'info')
    near(conv, 'L pad 1 at SW', pads(L, num='1'), pin(ic, '3'), 2.5, L, S1)
    prev = None
    for c in couts:
        if prev is None:
            near(conv, 'Cout + at L pad 2', pads(c, vout), pads(L, num='2'), 2.5, c, S1)
            near(conv, 'Cout GND at IC GND', pads(c, 'GND'), pin(ic, '2'), 2.5, c, S1)
        else:
            near(conv, '2nd Cout beside the 1st (+)', pads(c, vout), pads(prev, vout), 2.0, c, S1)
            near(conv, '2nd Cout beside the 1st (GND)', pads(c, 'GND'), pads(prev, 'GND'), 2.0, c, S1)
        prev = c
    for r in fb:
        near(conv, 'FB node at FB pin', pads(r, fbn), pin(ic, '5'), 2.5, r, S1)
        chk(conv, 'FB node away from SW', dmin(pads(r, fbn), sw), 0.8, r, S1, more=True)

S2 = 'SLVSD38C §11.1, Fig 11-1'; conv = 'U4 TPS61089'; ic = 'U4'; vo = 'VCC5V0_SYS'; sw4 = netof(ic, '11')
near(conv, 'C33 100 nF + at VOUT (hot loop)', pads('C33', vo), pin(ic, '6'), 1.5, 'C33', S2)
near(conv, 'C33 100 nF GND at GND (hot loop)', pads('C33', 'GND'), pin(ic, '5'), 1.5, 'C33', S2)
prev = 'C33'
for c in ['C32', 'C30', 'C31']:
    near(conv, '22 uF row: + beside the previous', pads(c, vo), pads(prev, vo), 2.5, c, S2)
    near(conv, '22 uF row: GND beside the previous', pads(c, 'GND'), pads(prev, 'GND'), 2.5, c, S2)
    near(conv, '22 uF: + to VOUT pin', pads(c, vo), pin(ic, '6'), 0, c, S2 + ' (row of caps as in the example)', 'info'); prev = c
near(conv, 'C25 100 nF + at VIN', pads('C25', 'VSYS_SW'), pin(ic, '9'), 1.5, 'C25', S2)
near(conv, 'C24 10 uF + at L VIN pad', pads('C24', 'VSYS_SW'), pads('L2', num='1'), 3.0, 'C24', S2)
near(conv, 'L pad at SW', pads('L2', num='2'), pin(ic, '11'), 3.5, 'L2', S2)
near(conv, 'BOOT cap at BOOT', pads('C26', netof(ic, '10')), pin(ic, '10'), 2.5, 'C26', S2)
near(conv, 'BOOT cap at SW', pads('C26', sw4), pin(ic, '11') + pads('L2', num='2'), 3.0, 'C26', S2)
near(conv, 'VCC cap at VCC', pads('C27', netof(ic, '2')), pin(ic, '2'), 2.5, 'C27', S2)
sw = pin(ic, '11') + pads('L2', num='2') + pads('C26', sw4)
for r in ['R15', 'R16']:
    near(conv, 'FB node at FB pin', pads(r, netof(ic, '3')), pin(ic, '3'), 2.5, r, S2)
    chk(conv, 'FB node away from SW', dmin(pads(r, netof(ic, '3')), sw), 0.8, r, S2, more=True)
near(conv, 'COMP R at COMP', pads('R17', netof(ic, '4')), pin(ic, '4'), 2.5, 'R17', S2)

S3 = 'SLUSDV2C §8.4.1, Fig 8-21'; conv = 'U2 BQ25798'; ic = 'U2'
pm, vb, rg = netof(ic, '29'), netof(ic, '2'), netof(ic, '5')
near(conv, '1. 100 nF PMID + at PMID', pads('C10', pm), pin(ic, '29'), 1.5, 'C10', S3)
near(conv, '1. 100 nF PMID GND at GND', pads('C10', 'GND'), pin(ic, '27'), 2.0, 'C10', S3)
near(conv, '1. 100 nF SYS + at SYS', pads('C19', 'VSYS'), pin(ic, '25'), 1.5, 'C19', S3)
near(conv, '1. 100 nF SYS GND at GND', pads('C19', 'GND'), pin(ic, '27'), 2.0, 'C19', S3)
near(conv, '1. 10 uF PMID beside the 100 nF', pads('C9', pm), pads('C10', pm), 3.5, 'C9', S3)
near(conv, '1. 10 uF SYS beside the 100 nF', pads('C18', 'VSYS'), pads('C19', 'VSYS'), 3.5, 'C18', S3)
for a, c in (('C9', 'C8'), ('C8', 'C7')): near(conv, '1. PMID bulk chain (+)', pads(c, pm), pads(a, pm), 2.5, c, S3)
for a, c in (('C18', 'C17'), ('C17', 'C16')): near(conv, '1. SYS bulk chain (+)', pads(c, 'VSYS'), pads(a, 'VSYS'), 2.5, c, S3)
for c in ('C14', 'C15'): near(conv, '1. SYS bulk, system side', pads(c, 'VSYS'), pin(ic, '25'), 0, c, S3 + ' (system bulk, low-impedance path)', 'info')
near(conv, '2. L1 to SW1 (via under IC)', pads('L1', num='1'), pin(ic, '28'), 6.5, 'L1', S3)
near(conv, '2. L1 to SW2 (via under IC)', pads('L1', num='2'), pin(ic, '26'), 6.5, 'L1', S3)
near(conv, '2. BTST1 cap (bottom, vias)', pads('C11', netof(ic, '4')), pin(ic, '4'), 2.0, 'C11', S3)
near(conv, '2. BTST2 cap (bottom, vias)', pads('C12', netof(ic, '19')), pin(ic, '19'), 2.0, 'C12', S3)
near(conv, '3. REGN cap + at REGN', pads('C13', rg), pin(ic, '5'), 2.0, 'C13', S3)
near(conv, '4. 100 nF VBUS + at VBUS', pads('C6', vb), pin(ic, '2') + pin(ic, '3'), 2.0, 'C6', S3)
near(conv, '4. VBUS bulk beside the 100 nF', pads('C5', vb), pads('C6', vb), 3.0, 'C5', S3)
near(conv, '4. VBUS bulk chain', pads('C4', vb), pads('C5', vb), 2.5, 'C4', S3)
near(conv, '5. BAT cap + at BAT', pads('C20', 'VBAT'), pin(ic, '22') + pin(ic, '23'), 2.0, 'C20', S3)
near(conv, '5. BAT cap chain', pads('C21', 'VBAT'), pads('C20', 'VBAT'), 2.0, 'C21', S3)
sw = pin(ic, '26') + pin(ic, '28') + pads('L1')
chk(conv, '7. BATP (R4) away from SW', dmin(pads('R4', netof(ic, '18')), sw), 1.5, 'R4', S3, more=True)
for r in ['R7', 'R8']: chk(conv, '7. TS divider away from SW', dmin(pads(r, '/Battery/TS'), sw), 1.5, r, S3, more=True)

# Floorplan rule (approved B6, worklog 2026-11-23-t38-dc-input.md:172): every switching inductor >= 5.5 mm from the HaLow module.
def cbox(f):
    L = pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd; xs, ys = [], []
    for g in f.GraphicalItems():
        if g.GetLayer() == L: r = g.GetBoundingBox(); xs += [r.GetLeft(), r.GetRight()]; ys += [r.GetTop(), r.GetBottom()]
    return min(xs)/1e6, min(ys)/1e6, max(xs)/1e6, max(ys)/1e6
def boxgap(a, c): return math.hypot(max(0, a[0] - c[2], c[0] - a[2]), max(0, a[1] - c[3], c[1] - a[3]))
H = cbox(FP['U701'])
for L in ['L1', 'L2', 'L5', 'L6', 'L7', 'L8', 'L10', 'L11']:
    chk('Floorplan', 'inductor to HaLow module (courtyards)', boxgap(cbox(FP[L]), H), 5.5, L, 'B6 floorplan rule', more=True)
rule = [r for r in rows if r['kind'] == 'rule']
out = dict(rows=rows, fails=sum(not r['ok'] for r in rule), total=len(rule), info=len(rows) - len(rule))
for r in rows:
    tag = 'info' if r['kind'] == 'info' else ('ok  ' if r['ok'] else 'FAIL')
    lim = '' if r['kind'] == 'info' else f"({'>=' if r['more'] else '<='} {r['lim']})"
    print(f"{tag} {r['conv']:14s} {r['what']:36s} {r['ref']:5s} {r['side']} {r['d']:5.2f} {lim}")
print(f"{out['fails']} of {out['total']} rule checks fail ({out['info']} info rows)")
if len(sys.argv) > 2: json.dump(out, open(sys.argv[2], 'w'), indent=1)
