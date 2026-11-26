"""T53 (2026-11-24): lay a hand-planned path for one net, checked piece by piece with geomlib (class clearance, the USB
20 mil keep, hole spacing, no via against a pad) before anything is written.
Usage: python3 t53_lay.py <board.kicad_pcb> NET [--w 0.12] STEP...
  STEP = F:x,y/x,y/...   a polyline on F.Cu          B:x,y/x,y/...   a polyline on B.Cu
         V:x,y           a through via, 0.4/0.2 mm unless --via D,H (T67: 0.6,0.3 for the battery and input paths)
Stops on the first conflict (nothing saved) and prints what blocks it; otherwise saves the board and prints the length."""
import sys, os, math, json, pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import netroute as nr
from geomlib import Geo, CU, bbox
from geomlib import dist as gdist
B, NET = sys.argv[1], sys.argv[2]; args = sys.argv[3:]; W = 0.12
if '--w' in args: i = args.index('--w'); W = float(args[i + 1]); del args[i:i + 2]
VD, VH = 0.4, 0.2
if '--via' in args: i = args.index('--via'); VD, VH = (float(v) for v in args[i + 1].split(',')); del args[i:i + 2]
b = pcbnew.LoadBoard(B)
_eb = b.GetBoardEdgesBoundingBox(); g = Geo(b, (_eb.GetLeft()/1e6 - 1, _eb.GetTop()/1e6 - 1, _eb.GetRight()/1e6 + 1, _eb.GetBottom()/1e6 + 1))
def hits(G, Ls):
    return [(r[0][-16:], r[3], r[4], round(gdist(G, r[1]), 3)) for L in Ls for r in g.near(L, bbox(G), 0.8)
            if r[0] != NET and gdist(G, r[1]) < max(g.ncl(NET), g.ncl(r[0])) + 0.01]
plan = []
for s in args:
    kind, body = s.split(':', 1); pts = [tuple(float(v) for v in q.split(',')) for q in body.split('/')]
    plan.append((kind, pts))
total = 0.0
for kind, pts in plan:                                   # check everything first
    if kind == 'V':
        v = pts[0]; G = ('pt', v, VD/2)
        ok = g.hole_ok(v[0], v[1], VH) and all(g.clear(G, L, NET) for L in CU) and \
            all(not (r[4] == 'pad' and r[0] != NET and gdist(G, r[1]) < 0.09) for L in (pcbnew.F_Cu, pcbnew.B_Cu) for r in g.near(L, bbox(G), 0.6))
        if not ok: raise SystemExit('via blocked %s: %s' % (v, hits(G, CU)))
        for L_ in CU: g.add(NET, L_, G)   # T54: the planned via is the net's own copper on every layer (segments of the net may end on it)
        continue
    L = pcbnew.F_Cu if kind == 'F' else pcbnew.B_Cu
    for a, c in zip(pts, pts[1:]):
        G = ('seg', a, c, W/2)
        if not (g.clear(G, L, NET) and nr.usb_ok(g, G, L, NET)): raise SystemExit('blocked %s %s -> %s: %s' % (kind, a, c, hits(G, [L])))
        total += math.dist(a, c)
for kind, pts in plan:
    if kind == 'V': g.add_via(pts[0][0], pts[0][1], NET, d=VD, h=VH); continue
    L = pcbnew.F_Cu if kind == 'F' else pcbnew.B_Cu
    for a, c in zip(pts, pts[1:]): g.add_track(a, c, W, L, NET)
b.Save(B); print(json.dumps(dict(net=NET, length=round(total, 3))))
