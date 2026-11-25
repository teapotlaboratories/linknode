"""T65 (owner, 2026-11-25): plane taps. For every pad of a plane net that is not yet joined to its plane, add one short
straight tap (0/45/90 degrees) from the pad centre to a 0.4/0.2 through via that lands inside that net's plane fill:
GND -> In1 (solid), VCC5V0_SYS -> the In2 5 V plane, VDD_0V9 -> its In2 island.
Usage: python3 t65_taps.py <board.kicad_pcb> --from <drc.json> [--nets GND,VCC5V0_SYS,VDD_0V9] [--exclude x0,y0,x1,y1] [--skip REF,REF] [--dry]
The pads to tap are the plane-net pads named in the kicad-cli DRC JSON's unconnected items (pcbnew's per-item
connectivity does not tell which pour fragment a pad touches, so the DRC list is the authority).
Checks per candidate (0.05 mm steps along 8 directions, up to --rmax mm from the pad edge):
  via: class clearance to every other net on all copper layers, hole-to-hole, >= 0.09 mm from other pads' copper,
       and a disc of via radius + 0.25 mm inside the target plane's filled copper on the plane layer;
  tap: class clearance on the pad's layer (own pad and same-net copper allowed).
Saves the board unless --dry; refill
zones and run DRC afterwards (kicad-cli DRC is the final check)."""
import sys, os, math, pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geomlib import Geo, CU, bbox, pip
from geomlib import dist as gdist

B = sys.argv[1]; args = sys.argv[2:]
opt = {args[i]: args[i + 1] for i in range(len(args) - 1) if args[i].startswith('--') and not args[i + 1].startswith('--')}
DRY = '--dry' in args
NETS = opt.get('--nets', 'GND,VCC5V0_SYS,VDD_0V9').split(',')
EXC = [tuple(map(float, e.split(','))) for e in opt.get('--exclude', '').split(';') if e]
RMAX = float(opt.get('--rmax', 1.5))
SKIP = set(opt.get('--skip', '').split(','))   # refs left for their own section (e.g. RF filter caps, 4e)
PLANE = {'GND': pcbnew.In1_Cu, 'VCC5V0_SYS': pcbnew.In2_Cu, 'VDD_0V9': pcbnew.In2_Cu}
VD, VH = 0.4, 0.2

b = pcbnew.LoadBoard(B)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.BuildConnectivity(); conn = b.GetConnectivity()
eb = b.GetBoardEdgesBoundingBox()
g = Geo(b, (eb.GetLeft()/1e6 - 1, eb.GetTop()/1e6 - 1, eb.GetRight()/1e6 + 1, eb.GetBottom()/1e6 + 1))

# filled copper of each plane net on its plane layer, as plain polygons (outer outlines + holes)
fills = {}
for z in b.Zones():
    if z.GetIsRuleArea(): continue
    n = z.GetNetname()
    if n in PLANE and z.IsOnLayer(PLANE[n]):
        ps = z.GetFilledPolysList(PLANE[n])
        for k in range(ps.OutlineCount()):
            o = ps.Outline(k); outer = [(o.CPoint(i).x/1e6, o.CPoint(i).y/1e6) for i in range(o.PointCount())]
            holes = []
            for h in range(ps.HoleCount(k)):
                hh = ps.Hole(k, h); holes.append([(hh.CPoint(i).x/1e6, hh.CPoint(i).y/1e6) for i in range(hh.PointCount())])
            fills.setdefault(n, []).append((outer, holes))

def in_plane(net, x, y, r):
    """disc (x,y,r) lies inside one filled region of net's plane, clear of its holes"""
    for outer, holes in fills.get(net, []):
        if not pip((x, y), outer): continue
        # distance to the outer boundary edges and to every hole must be >= r
        def edge_d(poly):
            best = 1e9
            for i in range(len(poly)):
                a, c = poly[i], poly[(i + 1) % len(poly)]
                ax, ay = a; bx, by = c; dx, dy = bx - ax, by - ay; L = dx*dx + dy*dy
                t = 0 if L == 0 else max(0, min(1, ((x-ax)*dx + (y-ay)*dy)/L)); best = min(best, math.hypot(x-ax-t*dx, y-ay-t*dy))
            return best
        if edge_d(outer) < r: continue
        if any(pip((x, y), h) or edge_d(h) < r for h in holes): continue
        return True
    return False

import json, re
WANT = set()
for u in json.load(open(opt['--from']))['unconnected_items']:
    for it in u['items']:
        m = re.match(r'Pad (\S+) \[([^\]]+)\] of (\S+) on', it['description'])
        if m: WANT.add((m.group(3), m.group(1)))

def other_pad_ok(G, net, own):
    for L in (pcbnew.F_Cu, pcbnew.B_Cu):
        for r in g.near(L, bbox(G), 0.6):
            if r[4] == 'pad' and r[3] != own and gdist(G, r[1]) < 0.09: return False
    return True

added, skipped, failed = [], [], []
DIRS = [(math.cos(k*math.pi/4), math.sin(k*math.pi/4)) for k in range(8)]
for fp in b.GetFootprints():
    ref = fp.GetReference()
    for p in fp.Pads():
        net = p.GetNetname()
        if net not in NETS or p.GetDrillSizeX() > 0: continue
        px, py = p.GetPosition().x/1e6, p.GetPosition().y/1e6
        if any(x0 <= px <= x1 and y0 <= py <= y1 for x0, y0, x1, y1 in EXC): continue
        if (ref, p.GetNumber()) not in WANT or ref in SKIP: continue
        L = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
        sz = p.GetBoundingBox(); w = max(0.15, min(0.3, min(p.GetSizeX(), p.GetSizeY())/1e6 * 0.9))
        pads_poly = g.poly_of(p, L)
        best = None
        for d in [i*0.05 for i in range(4, int((RMAX + 1.0)/0.05))]:
            for ux, uy in DIRS:
                vx, vy = round(px + ux*d, 4), round(py + uy*d, 4)   # exact direction from the pad centre, so the tap is a true 0/45/90 line
                V = ('pt', (vx, vy), VD/2)
                # via copper must sit off the own pad (no via-in-pad): annulus edge >= 0.09 from it
                if any(gdist(V, ('poly', pp)) < 0.09 for pp in pads_poly): continue
                if min(gdist(V, ('poly', pp)) for pp in pads_poly) > RMAX: continue
                if not g.hole_ok(vx, vy, VH): continue
                if not all(g.clear(V, LL, net, extra=0.03) for LL in CU): continue
                if not other_pad_ok(V, net, ref): continue
                if not in_plane(net, vx, vy, VD/2 + 0.25): continue
                T = ('seg', (px, py), (vx, vy), w/2)
                if not g.clear(T, L, net, extra=0.03): continue
                best = (vx, vy, d); break
            if best: break
        if not best: failed.append((ref, p.GetNumber(), net, px, py)); continue
        vx, vy, d = best
        g.add_track((px, py), (vx, vy), w, L, net); g.add_via(vx, vy, net, VD, VH)
        added.append((ref, p.GetNumber(), net, px, py, vx, vy, w))

for a in added: print('tap %s.%s %-11s pad (%.2f,%.2f) -> via (%.3f,%.3f) w %.2f' % a)
for f in failed: print('FAIL %s.%s %s pad (%.2f,%.2f): no legal via in plane within rmax' % f)
print('added', len(added), 'failed', len(failed))
if not DRY: b.Save(B)
