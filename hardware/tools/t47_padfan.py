"""T47 (2026-11-23): fan chosen pads out to their own via with a short top stub (straight or one 45-degree dogleg), so
the router can join a bus on the bottom where the pads themselves are too tight to reach (0.5 mm pitch ESD arrays, pin
orders that don't line up). Used for the microSD side of group 3b: U401/U402 (TPD4E05U06 ESD) and J401's signal pads.
Usage: python3 t47_padfan.py <board.kicad_pcb> REF:PAD[:DIR],...  [--rmax 1.6] [--w 0.12]
  DIR (optional) restricts where the via may go relative to the pad: N, S, E, W (e.g. N = via north of the pad centre).
For each pad, in the order given: the nearest legal 0.4/0.2 mm via within rmax (0.05 mm grid; class clearance on all
copper layers, hole spacing, >= 0.09 mm from any pad edge), whose stub keeps clearance. Saves the board."""
import sys, os, math, json, pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geomlib import Geo, CU, bbox
from geomlib import dist as gdist
B = sys.argv[1]; SPEC = sys.argv[2].split(',')
opt = {sys.argv[i]: sys.argv[i + 1] for i in range(3, len(sys.argv) - 1) if sys.argv[i].startswith('--')}
RMAX = float(opt.get('--rmax', 1.6)); W = float(opt.get('--w', 0.12))   # --w (T53): 0.17 for 50-ohm SD/SDIO pads
VIANO = [tuple(float(v) for v in bx.split(',')) for bx in opt['--no-via'].split(';')] if '--no-via' in opt else []   # e.g. a module body
b = pcbnew.LoadBoard(B)
_eb = b.GetBoardEdgesBoundingBox(); g = Geo(b, (_eb.GetLeft()/1e6 - 1, _eb.GetTop()/1e6 - 1, _eb.GetRight()/1e6 + 1, _eb.GetBottom()/1e6 + 1))
F = pcbnew.F_Cu
def pad(ref, num): return [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
def via_ok(x, y, net):
    G = ('pt', (x, y), 0.2)
    if not (g.hole_ok(x, y, 0.2) and all(g.clear(G, L, net) for L in CU)): return False
    for L in (F, pcbnew.B_Cu):
        for r in g.near(L, bbox(G), 0.6):
            if r[4] == 'pad' and gdist(G, r[1]) < 0.09: return False      # no via in or against any pad (own net too)
    return True
def stubs(a, v):
    dx, dy = v[0] - a[0], v[1] - a[1]
    if abs(dx) < 1e-6 or abs(dy) < 1e-6 or abs(abs(dx) - abs(dy)) < 1e-6: return [[a, v]]
    m = min(abs(dx), abs(dy)); dg = (math.copysign(m, dx), math.copysign(m, dy))
    return [[a, (v[0] - dg[0], v[1] - dg[1]), v], [a, (a[0] + dg[0], a[1] + dg[1]), v]]   # straight first, then diagonal
out = []
for s in SPEC:
    ref, num, *d = s.split(':'); p = pad(ref, num); net = p.GetNetname(); a = (p.GetPosition().x/1e6, p.GetPosition().y/1e6)
    SL = F if p.IsOnLayer(F) else pcbnew.B_Cu                    # stub on the pad's own layer
    best = None; n = int(RMAX/0.05)
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            v = (round(a[0] + i*0.05, 3), round(a[1] + j*0.05, 3)); r = math.dist(a, v)
            if r > RMAX or r < 0.45 or (best and r >= best[0]): continue
            if d and ((d[0] == 'N' and v[1] >= a[1] - 0.2) or (d[0] == 'S' and v[1] <= a[1] + 0.2) or
                      (d[0] == 'E' and v[0] <= a[0] + 0.2) or (d[0] == 'W' and v[0] >= a[0] - 0.2)): continue
            if any(b0 - 0.25 <= v[0] <= b2 + 0.25 and b1 - 0.25 <= v[1] <= b3 + 0.25 for b0, b1, b2, b3 in VIANO): continue
            if not via_ok(v[0], v[1], net): continue
            for pts in stubs(a, v):
                if all(g.clear(('seg', q, c, W/2), SL, net) for q, c in zip(pts, pts[1:]) if math.dist(q, c) > 1e-6):
                    best = (r, v, pts); break
    if not best: out.append((s, None)); print('no via for', s, flush=True); continue
    r, v, pts = best
    for q, c in zip(pts, pts[1:]):
        if math.dist(q, c) > 1e-6: g.add_track(q, c, W, SL, net)
    g.add_via(v[0], v[1], net, d=0.4, h=0.2)
    out.append((s, v, round(r, 2)))
b.Save(B)
print(json.dumps(out))
