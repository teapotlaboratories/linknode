"""RETIRED 2026-11-23: the owner changed the style to 45-degree bends only (bend45.py). Kept for reference.
T47 (owner, 2026-11-23): smooth, hand-taped routing style. Any-angle runs joined by tangent arcs, no sharp corners.
Usage: python3 smooth.py <board.kicad_pcb> [NET[,NET...]] [--rmax 2.0]
For every net (or the listed ones) and copper layer:
 1. Chains: plain segments (PCB_TRACK) between fixed points are walked into polylines. Fixed = a pad (the point lies on
    one), a via, an arc end, or a point where other than exactly two segments meet.
 2. Pull: the chain is redrawn with the fewest straight runs whose segments keep clearance (geomlib), at any angle.
 3. Fillet: every interior corner becomes a tangent arc (PCB_ARC), radius from rmax down to 0.1 mm, the largest whose
    arc (checked as 12 segments) keeps clearance and fits on both legs (half a leg, or 90 % of a leg that ends at a
    fixed point). Corners that cannot take an arc stay sharp and are reported.
Saves the board; refill zones and run kicad-cli DRC afterwards (the final check)."""
import sys, os, math, json, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geomlib import Geo, arc_points
mm = pcbnew.FromMM
BRD = sys.argv[1]
args = [a for a in sys.argv[2:] if not a.startswith('--')]
opt = dict(zip(sys.argv[2:][::1], sys.argv[3:]))
RMAX = float(opt.get('--rmax', 2.0))
NETS = set(args[0].split(',')) if args and not args[0].startswith('--') else None
b = pcbnew.LoadBoard(BRD)
eb = b.GetBoardEdgesBoundingBox()
g = Geo(b, (eb.GetLeft()/1e6 - 1, eb.GetTop()/1e6 - 1, eb.GetRight()/1e6 + 1, eb.GetBottom()/1e6 + 1))
def P(v): return (round(v.x/1e6, 4), round(v.y/1e6, 4))
def key(p): return (round(p[0], 3), round(p[1], 3))
pads_by_net = {}
for fp in b.GetFootprints():
    for p in fp.Pads(): pads_by_net.setdefault(p.GetNetname(), []).append(p)
def on_pad(net, L, pt):
    for p in pads_by_net.get(net, ()):
        if p.IsOnLayer(L) and p.HitTest(pcbnew.VECTOR2I(mm(pt[0]), mm(pt[1]))): return True
    return False
def seg_ok(a, c, w, L, net):
    return g.clear(('seg', a, c, w/2 + 0.01), L, net)
def arc_ok(pts, w, L, net):
    return all(seg_ok(a, c, w, L, net) for a, c in zip(pts, pts[1:]))
rep = dict(chains=0, segs_before=0, segs_after=0, arcs=0, sharp=[])
tracks = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and (NETS is None or t.GetNetname() in NETS)]
groups = {}
for t in tracks: groups.setdefault((t.GetNetname(), t.GetLayer(), t.GetWidth()), []).append(t)
vias = {}
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA': vias.setdefault(t.GetNetname(), set()).add(key(P(t.GetPosition())))
arcends = {}
for t in b.GetTracks():
    if t.GetClass() == 'PCB_ARC':
        for q in (P(t.GetStart()), P(t.GetEnd())): arcends.setdefault((t.GetNetname(), t.GetLayer()), set()).add(key(q))
for (net, L, wi), segs in groups.items():
    w = wi/1e6
    adj = {}
    for t in segs:
        a, c = P(t.GetStart()), P(t.GetEnd())
        adj.setdefault(key(a), []).append((t, c)); adj.setdefault(key(c), []).append((t, a))
    fixed = {k for k, v in adj.items() if len(v) != 2 or k in vias.get(net, ()) or k in arcends.get((net, L), ()) or on_pad(net, L, k)}
    used = set()
    def walk(start, t0, nxt):
        pts = [start]; chain = [t0]; cur = nxt
        while True:
            pts.append(cur); k = key(cur)
            if k in fixed: return pts, chain
            nb = [(t, o) for t, o in adj[k] if t.m_Uuid.AsString() not in {c.m_Uuid.AsString() for c in chain}]
            if not nb: return pts, chain
            t, o = nb[0]; chain.append(t); cur = o
    chains = []
    for k in fixed:
        for t, o in adj[k]:
            if t.m_Uuid.AsString() in used: continue
            pts, chain = walk(k, t, o)
            for c in chain: used.add(c.m_Uuid.AsString())
            chains.append((pts, chain))
    for pts, chain in chains:
        rep['chains'] += 1; rep['segs_before'] += len(chain)
        # remove the chain from the clearance model (same net is ignored anyway) and from the board
        for c in chain: b.Remove(c)
        # 2. pull, any angle
        out = [pts[0]]; i = 0; n = len(pts)
        while i < n - 1:
            jb = i + 1
            for j in range(n - 1, i + 1, -1):
                if seg_ok(pts[i], pts[j], w, L, net): jb = j; break
            out.append(pts[jb]); i = jb
        # 3. fillet interior corners
        geo = [('L', out[0], out[1])] if len(out) == 2 else None
        if geo is None:
            legs = [[out[k], out[k + 1]] for k in range(len(out) - 1)]   # mutable leg ends
            arcs = []
            for k in range(1, len(out) - 1):
                A, Pc, C = legs[k - 1][0], out[k], legs[k][1]
                u = (Pc[0] - A[0], Pc[1] - A[1]); v = (C[0] - Pc[0], C[1] - Pc[1]); lu, lv = math.hypot(*u), math.hypot(*v)
                if lu < 1e-6 or lv < 1e-6: continue
                u = (u[0]/lu, u[1]/lu); v = (v[0]/lv, v[1]/lv)
                th = math.acos(max(-1.0, min(1.0, u[0]*v[0] + u[1]*v[1])))
                if th < math.radians(2) or th > math.radians(170): continue
                fa = 0.9 if k == 1 else 0.5; fc = 0.9 if k == len(out) - 2 else 0.5
                dmax = min(lu*fa, lv*fc); t2 = math.tan(th/2)
                r = min(RMAX, dmax/t2); done = False
                while r >= 0.1:
                    d = r*t2; T1 = (Pc[0] - u[0]*d, Pc[1] - u[1]*d); T2 = (Pc[0] + v[0]*d, Pc[1] + v[1]*d)
                    cross = u[0]*v[1] - u[1]*v[0]; nrm = (-u[1], u[0]) if cross > 0 else (u[1], -u[0])
                    cen = (T1[0] + nrm[0]*r, T1[1] + nrm[1]*r)
                    q = (Pc[0] - cen[0], Pc[1] - cen[1]); lq = math.hypot(*q); M = (cen[0] + q[0]/lq*r, cen[1] + q[1]/lq*r)
                    ap = arc_points(T1, M, T2, 12)
                    if arc_ok(ap, w, L, net):
                        legs[k - 1][1] = T1; legs[k][0] = T2; arcs.append((T1, M, T2)); done = True; break
                    r *= 0.7
                if not done: rep['sharp'].append((net, b.GetLayerName(L), round(Pc[0], 2), round(Pc[1], 2)))
            geo = [('L', a, c) for a, c in legs] + [('A',) + a for a in arcs]
        for item in geo:
            if item[0] == 'L':
                a, c = item[1], item[2]
                if math.dist(a, c) < 1e-4: continue
                t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1]))); t.SetEnd(pcbnew.VECTOR2I(mm(c[0]), mm(c[1])))
                rep['segs_after'] += 1
            else:
                t = pcbnew.PCB_ARC(b); t.SetStart(pcbnew.VECTOR2I(mm(item[1][0]), mm(item[1][1]))); t.SetMid(pcbnew.VECTOR2I(mm(item[2][0]), mm(item[2][1])))
                t.SetEnd(pcbnew.VECTOR2I(mm(item[3][0]), mm(item[3][1]))); rep['arcs'] += 1
            t.SetWidth(wi); t.SetLayer(L); t.SetNet(b.FindNet(net)); b.Add(t); g.add_item(t, 'smooth')
b.Save(BRD)
print(json.dumps(rep))
