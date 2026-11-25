"""T47 Section 3b (2026-11-23): the three 3a nets that must cross the microSD bus (USB_CC_SENSE pin 22, SARADC_IN0 pin 23,
USB_VBUSDET pin 25) leave the RV1106 on top in three rows under the 32 kHz XIN line (y 131.6) and above the USB SoC-side
line (y 133.03), each ending in its own via west of the bus. Rows keep pin order; the vias step west going up (VBUSDET
east, CC west) so every row passes the vias below it with clearance. Hand-set geometry, checked with geomlib.
Usage: python3 t47_3arows.py <board.kicad_pcb>     (then t47_s3.py routes the bottom side to the parts)"""
import sys, os, math, json, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import netroute as nr
from geomlib import Geo, CU, bbox
from geomlib import dist as gdist
B = sys.argv[1]; b = pcbnew.LoadBoard(B)
_eb = b.GetBoardEdgesBoundingBox(); g = Geo(b, (_eb.GetLeft()/1e6 - 1, _eb.GetTop()/1e6 - 1, _eb.GetRight()/1e6 + 1, _eb.GetBottom()/1e6 + 1))
F = pcbnew.F_Cu; W = 0.12
U = b.FindFootprintByReference('U100')
def pin(n): p = [q for q in U.Pads() if q.GetNumber() == n][0]; return p.GetNetname(), (round(p.GetPosition().x/1e6, 3), round(p.GetPosition().y/1e6, 3))
def via_ok(x, y, net):
    G = ('pt', (x, y), 0.2)
    if not (g.hole_ok(x, y, 0.2) and all(g.clear(G, L, net) for L in CU)): return False
    return all(not (r[4] == 'pad' and gdist(G, r[1]) < 0.09) for L in (F, pcbnew.B_Cu) for r in g.near(L, bbox(G), 0.6))
#        pin   x where it leaves the pin row   row y    via
ROWS = [('22', 135.75, 131.90, (132.50, 132.02)),
        ('23', 135.80, 132.20, (133.05, 132.32)),
        ('25', 135.00, 132.62, (133.55, 132.62))]
out = {}; bad = []
for num, x1, yr, v in ROWS:
    net, a = pin(num)
    d = yr - a[1]
    pts = [a, (x1, a[1]), (x1 - abs(d), yr) if abs(d) > 1e-6 else (x1, yr)]
    dv = v[1] - yr
    pts += [(v[0] + abs(dv), yr), v] if abs(dv) > 1e-6 else [v]
    pts = [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 1e-6]
    ok = all(g.clear(('seg', p, q, W/2), F, net) and nr.usb_ok(g, ('seg', p, q, W/2), F, net) for p, q in zip(pts, pts[1:])) and via_ok(v[0], v[1], net)
    if not ok:
        hits = []
        for p, q in zip(pts, pts[1:]):
            G_ = ('seg', p, q, W/2)
            for r in g.near(F, bbox(G_), 0.8):
                if r[0] != net and gdist(G_, r[1]) < max(g.ncl(net), g.ncl(r[0])) + 0.01: hits.append((r[0][-16:], r[3], r[4], round(gdist(G_, r[1]), 3)))
        bad.append((num, pts, hits[:6], 'via ok' if via_ok(v[0], v[1], net) else 'via blocked')); continue
    for p, q in zip(pts, pts[1:]): g.add_track(p, q, W, F, net)
    g.add_via(v[0], v[1], net, d=0.4, h=0.2)
    out[net[-20:]] = round(sum(math.dist(p, q) for p, q in zip(pts, pts[1:])), 2)
if bad: raise SystemExit('blocked: %s' % json.dumps(bad))
b.Save(B); print(json.dumps(dict(rows=out)))
