"""T47 (owner, 2026-11-23): 45-degree routing style. Every segment at 0/45/90 degrees, every bend exactly 45 degrees
(a 90-degree turn becomes two 45-degree bends joined by a diagonal chamfer). No arcs, no any-angle runs.
Replaces the smooth/arc style (smooth.py) the owner chose first.
Usage: python3 bend45.py <board.kicad_pcb> [NET[,NET...]] [--cmax 1.0] [--pull] [--arcs] [--check]
--arcs: also turn arcs into corners (off by default: smooth deskew bumps are allowed, owner 2026-11-23).
--pull: first straighten router staircases (farthest clear straight run or straight+diagonal dogleg); use it on new
sections only, so approved copper is not reshaped.
For every net (or the listed ones), layer and width:
 0. Arcs (PCB_ARC) become two straight legs meeting where their end tangents cross (the corner a fillet replaced).
 1. Chains: plain segments between fixed points (a pad the point lies on, a via, a point where other than exactly two
    segments meet) are walked into polylines; collinear points are merged.
 2. A segment that is not at 0/45/90 degrees and ends on a pad first has that end slid inside the pad until it is
    (the track still ends in the pad copper). Otherwise it becomes a dogleg (one straight + one diagonal, a 45-degree bend); of the
    two doglegs the one that keeps clearance (geomlib) and turns least against its neighbours is used.
 3. Every 90-degree corner gets a diagonal chamfer: legs cut back by c (cmax down to 0.05 mm, x0.7 steps, at most half
    a leg, or 90 % of a leg that ends at a fixed point), the diagonal checked for clearance. A 135-degree turn gets two
    chamfers' worth: an extra straight-diagonal step. Corners that cannot be fixed stay and are reported.
--check: change nothing, only report segments off 0/45/90 and bends other than 45 degrees.
Saves the board; refill zones and run kicad-cli DRC afterwards (the final check)."""
import sys, os, math, json, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geomlib import Geo, arc_points
import netroute as nr
mm = pcbnew.FromMM
BRD = sys.argv[1]
argv = sys.argv[2:]
CHECK = '--check' in argv
PULL = '--pull' in argv
opt = {argv[i]: argv[i + 1] for i in range(len(argv) - 1) if argv[i].startswith('--') and argv[i] not in ('--check', '--pull', '--arcs')}
pos = [a for i, a in enumerate(argv) if not a.startswith('--') and (i == 0 or argv[i - 1] not in opt)]
CMAX = float(opt.get('--cmax', 1.0))
NETS = set(pos[0].split(',')) if pos else None
EPS_ANG = 0.5                                   # degrees
b = pcbnew.LoadBoard(BRD)
eb = b.GetBoardEdgesBoundingBox()
g = None if CHECK else Geo(b, (eb.GetLeft()/1e6 - 1, eb.GetTop()/1e6 - 1, eb.GetRight()/1e6 + 1, eb.GetBottom()/1e6 + 1))
def P(v): return (round(v.x/1e6, 6), round(v.y/1e6, 6))
def key(p): return (round(p[0], 3), round(p[1], 3))
def V(p): return pcbnew.VECTOR2I(mm(p[0]), mm(p[1]))
def ang(a, c): return math.degrees(math.atan2(c[1] - a[1], c[0] - a[0]))
def octo(a, c):
    t = ang(a, c) % 45.0
    return min(t, 45.0 - t) < EPS_ANG
def turn(a, p, c):
    """direction change at p in degrees, 0..180"""
    d = abs((ang(p, c) - ang(a, p) + 180.0) % 360.0 - 180.0)
    return d
pads_by_net = {}
for fp in b.GetFootprints():
    for p in fp.Pads(): pads_by_net.setdefault(p.GetNetname(), []).append(p)
def pad_at(net, L, pt):
    for p in pads_by_net.get(net, ()):
        if p.IsOnLayer(L) and p.HitTest(V(pt)): return p
    return None
def on_pad(net, L, pt): return pad_at(net, L, pt) is not None
OCT = [(math.cos(math.radians(45*k)), math.sin(math.radians(45*k))) for k in range(8)]
def slide(fix, end, pad):
    """points inside `pad` near `end` from which the segment to `fix` is at 0/45/90 degrees, best first"""
    out = []
    for d in OCT:
        t = (end[0] - fix[0])*d[0] + (end[1] - fix[1])*d[1]
        if t <= 0.05: continue
        n = (round(fix[0] + d[0]*t, 6), round(fix[1] + d[1]*t, 6))
        if pad.HitTest(V(n)): out.append((math.dist(n, end), n))
    return [n for _, n in sorted(out)]
def seg_ok(a, c, w, L, net):                     # class clearance + the DRU's 0.5 mm USB spacing (netroute.usb_ok)
    return CHECK or (g.clear(('seg', a, c, w/2 + 0.01), L, net) and nr.usb_ok(g, ('seg', a, c, w/2 + 0.01), L, net))
def path_ok(pts, w, L, net):
    return all(seg_ok(a, c, w, L, net) for a, c in zip(pts, pts[1:]) if math.dist(a, c) > 1e-6)
rep = dict(arcs_removed=0, chains=0, segs_before=0, segs_after=0, pulled=0, slides=0, doglegs=0, chamfers=0, left=[])
def in_scope(t): return NETS is None or t.GetNetname() in NETS
# ---- 0. arcs -> two legs at the tangent crossing (opt-in --arcs: since 2026-11-23 the owner allows smooth arcs in deskew
#      bumps only, so arcs are left alone by default; chains end at arc ends)
if not CHECK and '--arcs' in argv:
    for t in [t for t in b.GetTracks() if t.GetClass() == 'PCB_ARC' and in_scope(t)]:
        S, M, E = P(t.GetStart()), P(t.GetMid()), P(t.GetEnd())
        ap = arc_points(S, M, E, 24)
        dS = (ap[1][0] - S[0], ap[1][1] - S[1]); dE = (E[0] - ap[-2][0], E[1] - ap[-2][1])
        den = dS[0]*dE[1] - dS[1]*dE[0]
        if abs(den) < 1e-12: rep['left'].append(('arc-180', t.GetNetname(), S, E)); continue
        k = ((E[0] - S[0])*dE[1] - (E[1] - S[1])*dE[0]) / den
        K = (S[0] + dS[0]*k, S[1] + dS[1]*k)
        net, L, wi = t.GetNetname(), t.GetLayer(), t.GetWidth()
        b.Remove(t); rep['arcs_removed'] += 1
        for a, c in ((S, K), (K, E)):
            n = pcbnew.PCB_TRACK(b); n.SetStart(V(a)); n.SetEnd(V(c)); n.SetWidth(wi); n.SetLayer(L); n.SetNet(b.FindNet(net)); b.Add(n)
# ---- chains
vias = {}
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA': vias.setdefault(t.GetNetname(), set()).add(key(P(t.GetPosition())))
    if t.GetClass() == 'PCB_ARC':                                     # arc ends are fixed: chains stop there
        for q in (P(t.GetStart()), P(t.GetEnd())): vias.setdefault(t.GetNetname(), set()).add(key(q))
groups = {}
for t in b.GetTracks():
    if t.GetClass() == 'PCB_TRACK' and in_scope(t): groups.setdefault((t.GetNetname(), t.GetLayer(), t.GetWidth()), []).append(t)
def merge(pts):
    out = [pts[0]]
    for q in pts[1:]:
        if math.dist(out[-1], q) < 1e-6: continue
        if len(out) >= 2 and turn(out[-2], out[-1], q) < 1e-3: out[-1] = q; continue
        out.append(q)
    return out
def dogleg(a, c, diag_first):
    dx, dy = c[0] - a[0], c[1] - a[1]; m = min(abs(dx), abs(dy))
    dg = (math.copysign(m, dx), math.copysign(m, dy))
    if diag_first: return (a[0] + dg[0], a[1] + dg[1])
    return (c[0] - dg[0], c[1] - dg[1])
def pad_pts(pad, near, step=0.025, n=40):
    """the n points of a step grid inside `pad` closest to `near` (near itself first)"""
    bb = pad.GetBoundingBox(); out = []
    x0, y0, x1, y1 = bb.GetLeft()/1e6, bb.GetTop()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6
    for ix in range(int((x1 - x0)/step) + 1):
        for iy in range(int((y1 - y0)/step) + 1):
            p = (round(x0 + ix*step, 4), round(y0 + iy*step, 4))
            if pad.HitTest(V(p)): out.append((math.dist(p, near), p))
    return [near] + [p for _, p in sorted(out)[:n]]
def shapes(a, c):
    dx, dy = c[0] - a[0], c[1] - a[1]; m = min(abs(dx), abs(dy))
    dg = (math.copysign(m, dx), math.copysign(m, dy)); st = (dx - dg[0], dy - dg[1])
    yield [a, c]
    yield [a, (a[0] + dg[0], a[1] + dg[1]), c]
    yield [a, (a[0] + st[0], a[1] + st[1]), c]
    for f in (0.25, 0.5, 0.75):
        m1 = (a[0] + st[0]*f, a[1] + st[1]*f); m2 = (m1[0] + dg[0], m1[1] + dg[1])
        yield [a, m1, m2, c]
def unit(a, c):
    l = math.dist(a, c); return ((c[0] - a[0])/l, (c[1] - a[1])/l), l
bad_total = []
for (net, L, wi), segs in groups.items():
    w = wi/1e6; LN = b.GetLayerName(L)
    adj = {}
    for t in segs:
        a, c = P(t.GetStart()), P(t.GetEnd())
        adj.setdefault(key(a), []).append((t, c, a)); adj.setdefault(key(c), []).append((t, a, c))
    fixed = {k for k, v in adj.items() if len(v) != 2 or k in vias.get(net, ()) or on_pad(net, L, k)}
    used = set(); chains = []
    def walk(start, t0, nxt):
        pts = [start]; chain = [t0]; seen = {t0.m_Uuid.AsString()}; cur = nxt
        while True:
            pts.append(cur); k = key(cur)
            if k in fixed: return pts, chain
            nb = [(t, o) for t, o, _ in adj[k] if t.m_Uuid.AsString() not in seen]
            if not nb: return pts, chain
            t, o = nb[0]; chain.append(t); seen.add(t.m_Uuid.AsString()); cur = o
    for k in list(fixed) + [k for k in adj if k not in fixed]:          # loops without a fixed point start anywhere
        for t, o, me in adj[k]:
            if t.m_Uuid.AsString() in used: continue
            pts, chain = walk(me, t, o)
            for c in chain: used.add(c.m_Uuid.AsString())
            chains.append((pts, chain))
    for pts, chain in chains:
        if CHECK:
            q = merge(pts)
            for a, c in zip(q, q[1:]):
                if not octo(a, c): bad_total.append(('angle', net, LN, a, c, round(ang(a, c), 1)))
            for i in range(1, len(q) - 1):
                tn = turn(q[i - 1], q[i], q[i + 1])
                if abs(tn - 45) > EPS_ANG: bad_total.append(('bend', net, LN, q[i], round(tn, 1)))
            continue
        rep['chains'] += 1; rep['segs_before'] += len(chain)
        for c in chain: b.Remove(c)
        q = merge(pts)
        # 1b (--pull). straighten staircases: from each point jump to the farthest later point reachable by one 0/45/90
        #     run or one dogleg (straight + diagonal, either order) that keeps clearance; only when it saves segments
        if PULL and len(q) > 2:
            out = [q[0]]; i = 0
            while i < len(q) - 1:
                nxt = None
                for j in range(len(q) - 1, i + 1, -1):
                    a, c = q[i], q[j]
                    cands = [[a, c]] if octo(a, c) else ([[a, dogleg(a, c, True), c], [a, dogleg(a, c, False), c]] if j - i >= 3 else [])
                    for pth in cands:
                        if path_ok(pth, w, L, net): nxt = (j, pth); break
                    if nxt: break
                if nxt is None: out.append(q[i + 1]); i += 1
                else: out.extend(nxt[1][1:]); i = nxt[0]; rep['pulled'] += 1
            q = merge(out)
        # 2. doglegs for off-angle segments
        i = 0
        while i < len(q) - 1:
            a, c = q[i], q[i + 1]
            if octo(a, c): i += 1; continue
            # 2a. a segment that ends on a pad: slide that end inside the pad until the segment is at 0/45/90
            slid = False
            for endi, other in ((0, 1), (len(q) - 1, len(q) - 2)):
                if slid or {i, i + 1} != {endi, other}: continue
                pad = pad_at(net, L, q[endi])
                if pad is None: continue
                for n in slide(q[other], q[endi], pad):
                    if seg_ok(q[other], n, w, L, net):
                        q[endi] = n; rep['slides'] += 1; slid = True; break
            if slid: continue
            # 2b. doglegs: straight+diagonal, diagonal+straight, straight+diagonal+straight (split 1/4, 1/2, 3/4);
            #     an end on a pad may also start from other points inside that pad (0.025 mm grid)
            starts, ends = [a], [c]
            if i == 0 and pad_at(net, L, a) is not None: starts = pad_pts(pad_at(net, L, a), a)
            if i + 1 == len(q) - 1 and pad_at(net, L, c) is not None: ends = pad_pts(pad_at(net, L, c), c)
            best = None
            for a2 in starts:
                for c2 in ends:
                    for path in shapes(a2, c2):
                        if any(not octo(x, y) for x, y in zip(path, path[1:]) if math.dist(x, y) > 1e-6): continue
                        cost = sum(math.dist(x, y) for x, y in zip(path, path[1:])) + 0.1*(len(path) - 2)
                        cost += 0.01*sum(turn(path[k - 1], path[k], path[k + 1]) for k in range(1, len(path) - 1))
                        if i > 0: cost += 0.01*turn(q[i - 1], path[0], path[1])
                        if i + 2 < len(q): cost += 0.01*turn(path[-2], path[-1], q[i + 2])
                        if best is not None and cost >= best[0]: continue
                        if path_ok(path, w, L, net): best = (cost, path)
            if best is None: rep['left'].append(('off-angle', net, LN, a, c)); i += 1; continue
            q[i:i + 2] = best[1]; rep['doglegs'] += 1; i += len(best[1]) - 1
        q = merge(q)
        # 3. chamfer 90 and 135 degree corners (repeat until stable)
        for _ in range(4):
            changed = False; i = 1
            while i < len(q) - 1:
                A, Pc, C = q[i - 1], q[i], q[i + 1]
                tn = turn(A, Pc, C)
                if abs(tn - 45) <= EPS_ANG or tn < EPS_ANG: i += 1; continue
                u, lu = unit(A, Pc); v, lv = unit(Pc, C)
                fa = 0.9 if (i - 1 == 0) else 0.5; fc = 0.9 if (i + 1 == len(q) - 1) else 0.5
                if abs(tn - 90) <= EPS_ANG:
                    c = min(CMAX, lu*fa, lv*fc); done = False
                    while c >= 0.05:
                        T1 = (Pc[0] - u[0]*c, Pc[1] - u[1]*c); T2 = (Pc[0] + v[0]*c, Pc[1] + v[1]*c)
                        if seg_ok(T1, T2, w, L, net):
                            q[i:i + 1] = [T1, T2]; rep['chamfers'] += 1; done = changed = True; break
                        c *= 0.7
                    if not done: rep['left'].append(('bend90', net, LN, Pc)); i += 1
                    else: i += 2
                elif abs(tn - 135) <= EPS_ANG:
                    # u -> w1 (45 toward v) -> w2 (90) -> v: T1 on leg A, a diagonal w1, a straight w2, back onto leg C
                    cr = u[0]*v[1] - u[1]*v[0]; s = 1 if cr > 0 else -1
                    def rot(d, deg):
                        r = math.radians(deg*s); return (d[0]*math.cos(r) - d[1]*math.sin(r), d[0]*math.sin(r) + d[1]*math.cos(r))
                    w1 = rot(u, 45); w2 = rot(u, 90)
                    c = min(CMAX, lu*fa, lv*fc); done = False
                    while c >= 0.05:
                        # T1 = Pc - u*x, then +w1*c, then +w2*e, landing on Pc + v*y; solve x, e, y for given c
                        # Pc - u x + w1 c + w2 e = Pc + v y  ->  -u x + w2 e - v y = -w1 c  (2 eq, 3 unknowns): take e = c
                        rhs = (-w1[0]*c - w2[0]*c, -w1[1]*c - w2[1]*c)
                        den = (-u[0])*(-v[1]) - (-v[0])*(-u[1])
                        if abs(den) < 1e-9: break
                        x = (rhs[0]*(-v[1]) - (-v[0])*rhs[1]) / den; y = ((-u[0])*rhs[1] - rhs[0]*(-u[1])) / den
                        if x > 0 and y > 0 and x <= lu*fa and y <= lv*fc:
                            T1 = (Pc[0] - u[0]*x, Pc[1] - u[1]*x); M1 = (T1[0] + w1[0]*c, T1[1] + w1[1]*c)
                            T2 = (Pc[0] + v[0]*y, Pc[1] + v[1]*y)
                            if path_ok([T1, M1, T2], w, L, net):
                                q[i:i + 1] = [T1, M1, T2]; rep['chamfers'] += 2; done = changed = True; break
                        c *= 0.7
                    if not done: rep['left'].append(('bend135', net, LN, Pc)); i += 1
                    else: i += 3
                else:
                    rep['left'].append(('bend%d' % round(tn), net, LN, Pc)); i += 1
            q = merge(q)
            if not changed: break
        for a, c in zip(q, q[1:]):
            if math.dist(a, c) < 1e-6: continue
            t = pcbnew.PCB_TRACK(b); t.SetStart(V(a)); t.SetEnd(V(c)); t.SetWidth(wi); t.SetLayer(L); t.SetNet(b.FindNet(net))
            b.Add(t); g.add_item(t, 'bend45'); rep['segs_after'] += 1
if CHECK:
    arcs = sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_ARC' and in_scope(t))
    print(json.dumps(dict(arcs=arcs, bad=len(bad_total), items=bad_total[:40])))
else:
    b.Save(BRD); print(json.dumps(rep))
