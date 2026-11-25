"""T32: compare floorplans. For each bus: longest pin-to-pin distance between the two parts (straight line and along x+y,
a lower bound for the routed length). Plus the closest switching inductor to the GPS and to the HaLow module, edge to edge.
Usage: t32_buslen.py board.kicad_pcb [...]   -> one JSON line per board"""
import sys, math, json, pcbnew
BUSES = [('SDIO U100-HaLow', 'U100', 'U701', lambda n: 'SDIO' in n),
         ('SD U100-microSD', 'U100', 'J401', lambda n: n.split('/')[-1].startswith('SD_') and 'PWR' not in n and 'DET' not in n),
         ('USB U100-R508/509', 'U100', 'R509', lambda n: 'USB' in n),
         ('USB R508-USB-C', 'R508', 'U1', lambda n: True),
         ('SPI U100-ESP32', 'U100', 'U801', lambda n: 'C5_SPI' in n),
         ('UART U100-GPS', 'U100', 'U20', lambda n: 'GPS_' in n),
         ('I2C U100-charger', 'U100', 'U2', lambda n: 'I2C' in n)]
INDUCTORS = ['L1', 'L2', 'L5', 'L6', 'L7', 'L8', 'L10', 'L11']
def crt(f):
    L = pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd; xs = []; ys = []
    for g in f.GraphicalItems():
        if g.GetLayer() == L: r = g.GetBoundingBox(); xs += [r.GetLeft(), r.GetRight()]; ys += [r.GetTop(), r.GetBottom()]
    return min(xs)/1e6, min(ys)/1e6, max(xs)/1e6, max(ys)/1e6
def gap(a, c):
    dx = max(0, max(a[0], c[0]) - min(a[2], c[2])); dy = max(0, max(a[1], c[1]) - min(a[3], c[3])); return math.hypot(dx, dy)
for path in sys.argv[1:]:
    b = pcbnew.LoadBoard(path); eb = b.GetBoardEdgesBoundingBox(); out = {'board': path.split('/')[-2], 'size': [round(eb.GetWidth()/1e6), round(eb.GetHeight()/1e6)]}
    for name, a, c, pred in BUSES:
        A = {p.GetNetname(): p.GetPosition() for p in b.FindFootprintByReference(a).Pads() if p.GetNetname() and pred(p.GetNetname())}
        C = {p.GetNetname(): p.GetPosition() for p in b.FindFootprintByReference(c).Pads() if p.GetNetname() and pred(p.GetNetname())}
        common = [n for n in A if n in C and n != 'GND']
        if not common: out[name] = None; continue
        st = max(math.dist((A[n].x/1e6, A[n].y/1e6), (C[n].x/1e6, C[n].y/1e6)) for n in common)
        mh = max(abs(A[n].x - C[n].x)/1e6 + abs(A[n].y - C[n].y)/1e6 for n in common)
        out[name] = [round(st, 1), round(mh, 1)]
    for tgt in ('U20', 'U701'):
        t = crt(b.FindFootprintByReference(tgt))
        d = min((gap(t, crt(b.FindFootprintByReference(l))), l) for l in INDUCTORS)
        out['nearest inductor to ' + tgt] = [round(d[0], 1), d[1]]
    print(json.dumps(out))
