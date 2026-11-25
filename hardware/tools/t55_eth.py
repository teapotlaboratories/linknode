"""T55 routing (2026-11-24): Ethernet on FPC A. The two pairs (ETH_TXP/TXN, ETH_RXP/RXN) are routed by KiCad's own diff-pair
router (ETH100: 0.13 mm lines, 0.15 mm gap; owner rule T51) on a scratch copy, from the RV1106 pins up the channel between the
HaLow BUSY trace and FB601. This script then:
  1. tidies the pin escape: KiCad steps each line 0.02-0.05 mm sideways right at the 0.35 mm-pitch pins to reach its 0.28 mm
     pair pitch, which the jagged check flags; each line instead runs straight up from its pin and joins KiCad's diagonal on
     the same line (the diagonal is unchanged, only its start moves down the line to the pin's x);
  2. lays the fan-out into the stacked 0R links R1001-R1004 (pad 1) and, after them, the four lines to vias above contacts
     1/2/4/5 with bottom stubs into the contacts (0.13 mm), plus the GND contact 3/6 vias.
Usage: python3 t55_eth.py <board.kicad_pcb>   (the board must already hold KiCad's pair copper)"""
import sys, os, subprocess, pcbnew
B = sys.argv[1]
LAY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 't53_lay.py')
PIN = {'/Expansion/ETH_TXP': 147.15, '/Expansion/ETH_TXN': 147.5, '/Expansion/ETH_RXP': 147.85, '/Expansion/ETH_RXN': 148.2}
PY = 123.705
EXT = {'/Expansion/ETH_TXP': (151.502, 117.3), '/Expansion/ETH_RXP': (150.452, 119.2)}
b = pcbnew.LoadBoard(B); KEEP = []; MM = pcbnew.FromMM
for net, xp in PIN.items():
    tr = [t for t in b.GetTracks() if t.GetNetname() == net and t.GetClass() == 'PCB_TRACK']
    diag = [t for t in tr if abs(abs(t.GetEnd().x - t.GetStart().x) - abs(t.GetEnd().y - t.GetStart().y)) < 5000 and abs(t.GetEnd().x - t.GetStart().x) > MM(1)]
    assert len(diag) == 1, (net, len(diag)); d = diag[0]
    lo = d.GetStart() if d.GetStart().y > d.GetEnd().y else d.GetEnd()        # the diagonal's south-west end
    s = (d.GetStart().x + d.GetStart().y) / 1e6
    esc = [t for t in tr if t is not d and min(t.GetStart().y, t.GetEnd().y) >= lo.y - 1000]   # the pin escape below it
    for t in esc: b.Remove(t); KEEP.append(t)
    new_lo = pcbnew.VECTOR2I(MM(xp), MM(round(s - xp, 4)))
    if d.GetStart().y > d.GetEnd().y: d.SetStart(new_lo)
    else: d.SetEnd(new_lo)
    if net in EXT:     # carry KiCad's diagonal on along its own line to the fan-out point (no collinear joint)
        hi = EXT[net]; assert abs((hi[0] + hi[1]) - s) < 0.002, (net, hi, s)
        if d.GetStart().y > d.GetEnd().y: d.SetEnd(pcbnew.VECTOR2I(MM(hi[0]), MM(hi[1])))
        else: d.SetStart(pcbnew.VECTOR2I(MM(hi[0]), MM(hi[1])))
    v = pcbnew.PCB_TRACK(b); v.SetStart(pcbnew.VECTOR2I(MM(xp), MM(PY))); v.SetEnd(new_lo); v.SetWidth(MM(0.13))
    v.SetLayer(pcbnew.F_Cu); v.SetNet(d.GetNet()); b.Add(v)
    print(net, 'escape', len(esc), 'segments -> straight leg to', round(s - xp, 3))
b.Save(B); del b

def F(*p): return 'F:' + '/'.join(f'{x:.3f},{y:.3f}' for x, y in p)
def Bc(*p): return 'B:' + '/'.join(f'{x:.3f},{y:.3f}' for x, y in p)
def V(x, y): return f'V:{x:.3f},{y:.3f}'
PLAN = [  # KiCad's pair ends: TXP (150.851,117.951), TXN (151.049,118.149), RXP (150.201,119.451), RXN (150.399,119.649)
    ('/Expansion/ETH_TXP', [F((151.502, 117.3), (151.69, 117.3))]),                                  # diagonal carried on (EXT)
    ('/Expansion/ETH_TXN', [F((151.049, 118.149), (151.6, 118.149))]),                               # straight into R1002.1
    ('/Expansion/ETH_RXP', [F((150.452, 119.2), (151.69, 119.2))]),                                  # diagonal carried on, east
    ('/Expansion/ETH_RXN', [F((150.399, 119.649), (151.25, 119.649), (151.55, 119.949))]),           # east, 45 down into R1004.1
    # after the 0R links: east, north to a via above the contact, bottom stub into the contact's north end. The via heights
    # balance each pair (HDG 3.3.2: skew < 30 mil): TX via y 117.0 / 117.345, RX 117.0 / 117.4355 (solved from the lengths)
    ('Net-(J1001-Pad1)', [F((152.71, 117.3), (154.45, 117.3), (154.75, 117.0)), V(154.75, 117.0), Bc((154.75, 117.0), (154.75, 118.6))]),
    ('Net-(J1001-Pad2)', [F((152.71, 118.25), (155.05, 118.25), (155.25, 118.05), (155.25, 117.345)), V(155.25, 117.345),
                          Bc((155.25, 117.345), (155.25, 118.6))]),
    ('Net-(J1001-Pad4)', [F((152.71, 119.2), (156.05, 119.2), (156.25, 119.0), (156.25, 117.0)), V(156.25, 117.0),
                          Bc((156.25, 117.0), (156.25, 118.6))]),
    ('Net-(J1001-Pad5)', [F((152.71, 120.15), (156.55, 120.15), (156.75, 119.95), (156.75, 117.4355)), V(156.75, 117.4355),
                          Bc((156.75, 117.4355), (156.75, 118.6))]),
    ('GND', [Bc((155.75, 118.6), (155.75, 116.1)), V(155.75, 116.1), Bc((157.25, 118.6), (157.25, 119.85)), V(157.25, 119.85)]),
]
for net, steps in PLAN:
    r = subprocess.run([sys.executable, LAY, B, net, '--w', '0.13' if 'GND' not in net else '0.12'] + steps, capture_output=True, text=True)
    out = [l for l in (r.stdout + r.stderr).strip().splitlines() if 'Debug' not in l and 'leak' not in l]
    print(net, '->', out[-1] if out else r.returncode)
    if r.returncode != 0: sys.exit(1)
