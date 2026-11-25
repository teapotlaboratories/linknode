"""Clean GND reference-zone outlines (owner, 2026-11-24: "for the pour, please dont have a bulging like shape. please do a clean
tidy solid shape"). Rebuilds the In2 GND corridor zones (made by t56_sdplane.py) so every outline edge is at 0/45/90 degrees,
with no round bulges at vias or scallops between them.
Method: each bottom-layer track of the bus becomes a thin strip along its centreline and each bus via a small square; the
union is grown by MARGIN with mitred corners (edges stay parallel to the 0/45/90 tracks, vias become axis-aligned squares),
then closed (grow CLOSE, shrink CLOSE, mitred) so the notches between vias and lane ends fill in, and opened (shrink OPEN, grow
OPEN) so small teeth go; holes are dropped (solid shape); collinear points dropped. Afterwards it prints the smallest distance
from any bus track edge on B.Cu to the zone outline (the reference margin).
Usage: python3 cleanzone.py <in.kicad_pcb> <out.kicad_pcb> ZONE_PREFIX NET[,NET...] [--margin 1.1] [--close 0.8] [--open 0.5] [--radius 1.0]
Replaces every zone whose name starts with ZONE_PREFIX by one zone per resulting outline (a zone saves only its first
outline), copying the old zone's settings and priority. Prints each outline's points and any edge not at a multiple of 45 deg."""
import sys, os, math, pcbnew
a = sys.argv[1:]; opt = {}
for k in ('--margin', '--close', '--open', '--radius'):
    if k in a: i = a.index(k); opt[k] = float(a[i+1]); del a[i:i+2]
IN, OUT, PREFIX, NETS = a[0], a[1], a[2], a[3].split(',')
MARGIN, CLOSE, OPEN = opt.get('--margin', 1.1), opt.get('--close', 0.8), opt.get('--open', 0.5)
FM = pcbnew.FromMM; MITER = pcbnew.CORNER_STRATEGY_ALLOW_ACUTE_CORNERS
b = pcbnew.LoadBoard(IN); In2, Bc = b.GetLayerID('In2.Cu'), b.GetLayerID('B.Cu')
old = [z for z in b.Zones() if z.GetZoneName().startswith(PREFIX)]
assert old, 'no zone named ' + PREFIX + '*'
ref = old[0]
# each bottom-layer lane (chain of B.Cu segments of one net) -> its own offset polygon: both sides offset by MARGIN with mitred
# 45/90-degree joints and square caps MARGIN past each end (vias sit at the chain ends, so they are inside the cap)
import collections
def key(v): return (round(v.x/1000), round(v.y/1000))          # 1 um grid
lanes = []
for net in NETS:
    adj = collections.defaultdict(list)
    for t in b.GetTracks():
        if t.GetNetname() == net and t.Type() != pcbnew.PCB_VIA_T and t.GetLayer() == Bc and t.GetLength() > 0:
            a_, c_ = key(t.GetStart()), key(t.GetEnd()); adj[a_].append(c_); adj[c_].append(a_)
    seen = set()
    starts = [n for n in adj if len(adj[n]) != 2] + list(adj)
    for s0 in starts:
        for n1 in adj[s0]:
            if (s0, n1) in seen: continue
            path = [s0, n1]; seen.add((s0, n1)); seen.add((n1, s0))
            while len(adj[path[-1]]) == 2:
                nx = [q for q in adj[path[-1]] if q != path[-2]][0]
                if (path[-1], nx) in seen: break
                seen.add((path[-1], nx)); seen.add((nx, path[-1])); path.append(nx)
            pts = [(x*1000.0, y*1000.0) for x, y in path]
            cur = [pts[0]]                                  # split where the chain doubles back (180-degree turn)
            for i in range(1, len(pts)):
                if len(cur) >= 2:
                    (ax_, ay_), (bx_, by_), (cx_, cy_) = cur[-2], cur[-1], pts[i]
                    u = (bx_-ax_, by_-ay_); v = (cx_-bx_, cy_-by_); nu, nv = math.hypot(*u), math.hypot(*v)
                    if nu and nv and (u[0]*v[0] + u[1]*v[1])/(nu*nv) < -0.9: lanes.append(cur); cur = [cur[-1]]
                cur.append(pts[i])
            lanes.append(cur)
M = FM(MARGIN)
def offset_poly(P):
    d = []; n = []
    for (x1, y1), (x2, y2) in zip(P, P[1:]):
        L = math.hypot(x2-x1, y2-y1); d.append(((x2-x1)/L, (y2-y1)/L)); n.append((-(y2-y1)/L, (x2-x1)/L))
    def side(sg):
        pts = [(P[0][0] - d[0][0]*M + sg*n[0][0]*M, P[0][1] - d[0][1]*M + sg*n[0][1]*M)]
        for i in range(1, len(P) - 1):
            a, c = n[i-1], n[i]; dot = a[0]*c[0] + a[1]*c[1]
            pts.append((P[i][0] + sg*(a[0]+c[0])/(1+dot)*M, P[i][1] + sg*(a[1]+c[1])/(1+dot)*M))
        pts.append((P[-1][0] + d[-1][0]*M + sg*n[-1][0]*M, P[-1][1] + d[-1][1]*M + sg*n[-1][1]*M))
        return pts
    q = pcbnew.SHAPE_POLY_SET(); q.NewOutline()
    for x, y in side(1) + side(-1)[::-1]: q.Append(int(round(x)), int(round(y)))
    return q
sp = pcbnew.SHAPE_POLY_SET()
for P in lanes:
    if len(P) >= 2: sp.BooleanAdd(offset_poly(P))
sp.Simplify()
print('lanes', len(lanes))
sp.Inflate(FM(CLOSE), MITER, FM(0.005), True); sp.Inflate(-FM(CLOSE), MITER, FM(0.005), True)   # closing: fill notches
if OPEN > 0: sp.Inflate(-FM(OPEN), MITER, FM(0.005), True); sp.Inflate(FM(OPEN), MITER, FM(0.005), True)   # opening: drop teeth
sp.Unfracture(); sp.Simplify()
# pockets of other copper trapped between the corridor and the VDD_0V9 island become dead islands: give them to the corridor
isl = [z for z in b.Zones() if z.IsOnLayer(In2) and z.GetNetname() == 'VDD_0V9']
if isl:
    u = sp.CloneDropTriangulation() if hasattr(sp, 'CloneDropTriangulation') else pcbnew.SHAPE_POLY_SET(sp)
    for z in isl: u.BooleanAdd(z.Outline())
    u.Simplify(); pockets = pcbnew.SHAPE_POLY_SET()
    for i in range(u.OutlineCount()):
        for h in range(u.HoleCount(i)):
            hh = u.Hole(i, h); pk = pcbnew.SHAPE_POLY_SET(); pk.NewOutline()
            for j in range(hh.PointCount()): pk.Append(hh.CPoint(j).x, hh.CPoint(j).y)
            if pk.Area() > 0: pockets.BooleanAdd(pk)
    if pockets.OutlineCount():
        print('filled pockets:', pockets.OutlineCount(), 'area mm2', round(pockets.Area()/1e12, 1))
        sp.BooleanAdd(pockets); sp.Simplify()
        sp.Inflate(FM(0.05), MITER, FM(0.005), True); sp.Inflate(-FM(0.05), MITER, FM(0.005), True); sp.Unfracture(); sp.Simplify()
STEP = FM(float(os.environ.get("STEP", "1.6")))
def octi(a, c):          # the two 0/45/90 two-segment paths from a to c (via a corner), plus the chord if it is already octilinear
    dx, dy = c[0]-a[0], c[1]-a[1]; ax_, ay_ = abs(dx), abs(dy); sx, sy = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
    out = []
    if min(ax_, ay_) < 1000 or abs(ax_ - ay_) < 1000: out.append([])
    m = min(ax_, ay_)
    out.append([(a[0] + sx*m, a[1] + sy*m)]); out.append([(c[0] - sx*m, c[1] - sy*m)])
    return out
def area(pts): return abs(sum(p[0]*q[1] - q[0]*p[1] for p, q in zip(pts, pts[1:] + pts[:1])))/2
def poly(pts):
    q = pcbnew.SHAPE_POLY_SET(); q.NewOutline()
    for x, y in pts: q.Append(int(x), int(y))
    return q
def selfx(P):            # proper self-intersection test of a closed polygon (non-adjacent edges crossing or touching)
    n = len(P)
    def orient(a, b, c): v = (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0]); return (v > 1e-3) - (v < -1e-3)
    def onseg(a, b, c): return min(a[0], b[0]) - 1 <= c[0] <= max(a[0], b[0]) + 1 and min(a[1], b[1]) - 1 <= c[1] <= max(a[1], b[1]) + 1
    def inter(p1, p2, q1, q2):
        o1, o2, o3, o4 = orient(p1, p2, q1), orient(p1, p2, q2), orient(q1, q2, p1), orient(q1, q2, p2)
        if o1 != o2 and o3 != o4: return True
        return (o1 == 0 and onseg(p1, p2, q1)) or (o2 == 0 and onseg(p1, p2, q2)) or (o3 == 0 and onseg(q1, q2, p1)) or (o4 == 0 and onseg(q1, q2, p2))
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1: continue
            if inter(P[i], P[(i+1) % n], P[j], P[(j+1) % n]): return True
    return False
def pip(P, q):            # point in polygon or on its boundary (pure python, nm)
    x, y = q; inside = False; n = len(P)
    for k in range(n):
        a, c = P[k], P[(k+1) % n]
        # on edge?
        cr = (c[0]-a[0])*(y-a[1]) - (c[1]-a[1])*(x-a[0]); L = math.dist(a, c)
        if L and abs(cr)/L < 20 and min(a[0], c[0]) - 20 <= x <= max(a[0], c[0]) + 20 and min(a[1], c[1]) - 20 <= y <= max(a[1], c[1]) + 20: return True
        if (a[1] > y) != (c[1] > y):
            xi = a[0] + (y - a[1])*(c[0] - a[0])/(c[1] - a[1])
            if xi > x: inside = not inside
    return inside
def destair(pts):
    """replace runs of >= 3 short edges (< STEP) by a 0/45/90 path of <= 2 segments that only adds area: every vertex of
    the old run lies inside or on the new outline, every new vertex lies outside or on the old one, and the new path stays
    within STEP of the run's bounding box."""
    pts = [tuple(map(float, q)) for q in pts]
    for _ in range(200):
        n = len(pts); done = True
        for i in range(n):
            L = 0
            while L < min(12, n - 4) and math.dist(pts[(i+L) % n], pts[(i+L+1) % n]) < STEP: L += 1
            if L < int(os.environ.get('MINRUN', '2')): continue
            a, c = pts[i], pts[(i+L) % n]; run = [pts[(i+k) % n] for k in range(1, L)]
            xs = [q[0] for q in run + [a, c]]; ys = [q[1] for q in run + [a, c]]
            box = (min(xs) - STEP, min(ys) - STEP, max(xs) + STEP, max(ys) + STEP)
            rest = [pts[(i+L+k) % n] for k in range(1, n - L)]
            best = None
            for mid in octi(a, c):
                if any(not (box[0] <= q[0] <= box[2] and box[1] <= q[1] <= box[3]) for q in mid): continue
                cand = [a] + [tuple(map(float, q)) for q in mid] + [c] + rest
                cand = [q for k_, q in enumerate(cand) if math.dist(q, cand[k_-1]) > 50]
                if len(cand) < 3 or selfx(cand): continue
                if not all(pip(cand, q) for q in run): continue
                if any(pip(pts, q) and not any(math.dist(q, r) < 50 for r in pts) and not pip_strict_on(pts, q) for q in mid): continue
                gain = area(cand) - area(pts)
                if gain < -1e6: continue
                if best is None or gain < best[0]: best = (gain, cand)
            if best: pts = best[1]; done = False; break
        if done: break
    return pts
def lineint(p1, p2, q1, q2):   # intersection of infinite lines p1p2 and q1q2 (None if parallel)
    d = (p2[0]-p1[0])*(q2[1]-q1[1]) - (p2[1]-p1[1])*(q2[0]-q1[0])
    if abs(d) < 1e-6: return None
    t = ((q1[0]-p1[0])*(q2[1]-q1[1]) - (q1[1]-p1[1])*(q2[0]-q1[0]))/d
    return (p1[0] + t*(p2[0]-p1[0]), p1[1] + t*(p2[1]-p1[1]))
def dejog(pts, JOG):
    """a short edge k (< JOG) between parallel edges k-1 and k+1 is a jog: shift edge k-1 onto edge k+1's line (or edge k+1
    onto k-1's), re-intersecting with the next edge out; keep the option that only adds area and stays octilinear"""
    pts = [tuple(map(float, q)) for q in pts]
    for _ in range(100):
        n = len(pts); best = None
        for k in range(n):
            a, b_ = pts[k], pts[(k+1) % n]
            if math.dist(a, b_) >= JOG: continue
            pa, pb = pts[(k-1) % n], pts[(k+2) % n]
            u = (a[0]-pa[0], a[1]-pa[1]); v = (pb[0]-b_[0], pb[1]-b_[1])
            if abs(u[0]*v[1] - u[1]*v[0]) > 1e-3*math.hypot(*u)*math.hypot(*v): continue      # not parallel
            # option 1: move edge (k-1) onto line of edge (k+1): new vertex = line(k-2) x line(k+1)
            ppa = pts[(k-2) % n]; X = lineint(ppa, pa, b_, pb)
            cands = []
            if X: cands.append([q for i_, q in enumerate(pts) if i_ not in ((k-1) % n, k, (k+1) % n)] and
                               [X if i_ == (k-1) % n else q for i_, q in enumerate(pts) if i_ not in (k, (k+1) % n)])
            pnb = pts[(k+3) % n]; Y = lineint(pa, a, pb, pnb)
            if Y: cands.append([Y if i_ == (k+2) % n else q for i_, q in enumerate(pts) if i_ not in (k, (k+1) % n)])
            for cand in cands:
                cand = [q for i_, q in enumerate(cand) if math.dist(q, cand[i_-1]) > 50]
                if len(cand) < 3 or selfx(cand): continue
                if not all(pip(cand, q) for q in pts): continue          # only adds area
                g = area(cand) - area(pts)
                if g > (JOG*JOG*4e12): continue                          # small local change only
                if best is None or g < best[0]: best = (g, cand)
        if not best: break
        pts = best[1]
    return pts
def denotch(pts, EMAX=3e6, AMAX=2e12):
    """fill small concave notches: a reflex vertex whose two edges are < EMAX is replaced by a 0/45/90 path (<= 2 segments)
    between its neighbours that only adds area (at most AMAX nm^2)"""
    pts = [tuple(map(float, q)) for q in pts]
    for _ in range(100):
        n = len(pts); best = None; sgn = 1 if sum(p[0]*q[1] - q[0]*p[1] for p, q in zip(pts, pts[1:] + pts[:1])) > 0 else -1
        for k in range(n):
            a, v, c = pts[k-1], pts[k], pts[(k+1) % n]
            if math.dist(a, v) > EMAX or math.dist(v, c) > EMAX: continue
            cr = (v[0]-a[0])*(c[1]-v[1]) - (v[1]-a[1])*(c[0]-v[0])
            if cr*sgn >= 0: continue                               # convex vertex
            for mid in octi(a, c):
                cand = [q for i_, q in enumerate(pts) if i_ != k]
                pos = (k - 1) % n if k > 0 else n - 1
                cand = pts[:k] + [tuple(map(float, q)) for q in mid] + pts[k+1:]
                cand = [q for i_, q in enumerate(cand) if math.dist(q, cand[i_-1]) > 50]
                if len(cand) < 3 or selfx(cand) or not pip(cand, v): continue
                g = area(cand) - area(pts)
                if g < 0 or g > AMAX: continue
                if best is None or g < best[0]: best = (g, cand)
        if not best: break
        pts = best[1]
    return pts
BUSSEG = []                 # bottom-layer bus segments (x1, y1, x2, y2, half width), filled below
def segdist(p, a, c):
    dx, dy = c[0]-a[0], c[1]-a[1]; L = dx*dx + dy*dy
    u = 0 if L == 0 else max(0, min(1, ((p[0]-a[0])*dx + (p[1]-a[1])*dy)/L)); return math.hypot(p[0]-a[0]-u*dx, p[1]-a[1]-u*dy)
def busmargin(P):           # smallest distance from a bus track edge to the outline P (negative if a track leaves P)
    m = 9e18; n = len(P)
    for x1, y1, x2, y2, hw in BUSSEG:
        L = math.hypot(x2-x1, y2-y1); k = max(1, int(L/50000))
        for i in range(k + 1):
            q = (x1 + (x2-x1)*i/k, y1 + (y2-y1)*i/k)
            d = min(segdist(q, P[j], P[(j+1) % n]) for j in range(n))
            if not pip(P, q): d = -d
            m = min(m, d - hw)
    return m
def interior(P, k, sgn):
    n = len(P); a, v, c = P[k-1], P[k], P[(k+1) % n]
    u = (v[0]-a[0], v[1]-a[1]); w = (c[0]-v[0], c[1]-v[1])
    return 180 - math.degrees(math.atan2(u[0]*w[1] - u[1]*w[0], u[0]*w[0] + u[1]*w[1]))*sgn
def desharp(pts, MINM):
    """no sharp corners (owner 2026-11-24): an inward spike (> 270 deg) is filled with a 0/45/90 path between its
    neighbours; a point sharper than 90 deg is cut by a 0/45/90 line leaving 90/135-degree corners, as far back as the bus
    margin MINM allows (<= 1.5 mm)"""
    pts = [tuple(map(float, q)) for q in pts]
    for _ in range(50):
        n = len(pts); sgn = 1 if sum(p[0]*q[1] - q[0]*p[1] for p, q in zip(pts, pts[1:] + pts[:1])) > 0 else -1
        ks = [k for k in range(n) if interior(pts, k, sgn) > 270.5 or interior(pts, k, sgn) < 89.5]
        if not ks: break
        k = ks[0]; ang = interior(pts, k, sgn); a, v, c = pts[k-1], pts[k], pts[(k+1) % n]; done = False
        if ang > 270.5:
            for mid in octi(a, c):
                cand = pts[:k] + [tuple(map(float, q)) for q in mid] + pts[k+1:]
                cand = [q for i_, q in enumerate(cand) if math.dist(q, cand[i_-1]) > 50]
                if len(cand) >= 3 and not selfx(cand) and pip(cand, v) and area(cand) >= area(pts):
                    nk = len(cand); sg2 = sgn
                    if all(89.5 <= interior(cand, j, sg2) <= 270.5 for j in range(nk) if cand[j] not in pts or cand[j] == a or cand[j] == c):
                        pts = cand; done = True; break
        else:
            ua = ((a[0]-v[0])/math.dist(a, v), (a[1]-v[1])/math.dist(a, v)); uc = ((c[0]-v[0])/math.dist(c, v), (c[1]-v[1])/math.dist(c, v))
            best = None
            for d in [x*FM(0.05) for x in range(30, 1, -1)]:
                if d >= math.dist(a, v) - 1000 or d >= math.dist(c, v) - 1000: continue
                # cut points: along v->a at distance da, along v->c at distance dc, with the cut line at a 0/45/90 angle
                for da in (d,):
                    pa = (v[0] + ua[0]*da, v[1] + ua[1]*da)
                    for ang8 in range(8):
                        w = (math.cos(math.radians(45*ang8)), math.sin(math.radians(45*ang8)))
                        den = w[0]*uc[1] - w[1]*uc[0]
                        if abs(den) < 1e-9: continue
                        t_ = ((pa[0]-v[0])*w[1] - (pa[1]-v[1])*w[0])/(-den) if False else None
                        # intersect line pa + s*w with ray v + r*uc
                        r = ((pa[0]-v[0])*w[1] - (pa[1]-v[1])*w[0])/(uc[0]*w[1] - uc[1]*w[0])
                        if r <= 1000 or r >= math.dist(c, v) - 1000: continue
                        pc = (v[0] + uc[0]*r, v[1] + uc[1]*r)
                        cand = pts[:k] + [pa, pc] + pts[k+1:]
                        if selfx(cand): continue
                        nk = len(cand)
                        if not all(89.5 <= interior(cand, j, sgn) <= 270.5 for j in (k, k+1)): continue
                        mg = busmargin(cand)
                        if mg < MINM: continue
                        if best is None or d > best[0]: best = (d, cand)
                if best: break
            if best: pts = best[1]; done = True
        if not done: print('  could not fix sharp corner at', (round(v[0]/1e6, 3), round(v[1]/1e6, 3)), round(ang)); break
    return pts
def pip_strict_on(P, q):     # q on the boundary of P
    n = len(P)
    for k in range(n):
        a, c = P[k], P[(k+1) % n]; L = math.dist(a, c)
        if L and abs((c[0]-a[0])*(q[1]-a[1]) - (c[1]-a[1])*(q[0]-a[0]))/L < 20 and min(a[0], c[0]) - 20 <= q[0] <= max(a[0], c[0]) + 20 and min(a[1], c[1]) - 20 <= q[1] <= max(a[1], c[1]) + 20: return True
    return False
def tidy(pts):            # drop duplicates and exactly collinear points (pure python)
    pts = list(pts); changed = True
    while changed and len(pts) > 3:
        changed = False
        for j in range(len(pts)):
            p0, p1, p2 = pts[j-1], pts[j], pts[(j+1) % len(pts)]
            cr = (p1[0]-p0[0])*(p2[1]-p1[1]) - (p1[1]-p0[1])*(p2[0]-p1[0])
            if abs(cr) <= 10*max(1, math.dist(p0, p2)) or math.dist(p0, p1) < 50: del pts[j]; changed = True; break
    return pts
def clean(o):                      # drop collinear points and sub-micron jogs
    pts = [(o.CPoint(j).x, o.CPoint(j).y) for j in range(o.PointCount())]
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for j in range(len(pts)):
            p0, p1, p2 = pts[j-1], pts[j], pts[(j+1) % len(pts)]
            cr = (p1[0]-p0[0])*(p2[1]-p1[1]) - (p1[1]-p0[1])*(p2[0]-p1[0])
            if abs(cr) <= 10*max(1, math.dist(p0, p2)) or math.dist(p0, p1) < 50:   # exactly collinear (< 10 nm off) or a duplicate point
                del pts[j]; changed = True; break
    return pts
BUSSEG[:] = [(t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetWidth()/2) for t in b.GetTracks() if t.GetNetname() in NETS and t.Type() != pcbnew.PCB_VIA_T and t.GetLayer() == Bc]
outs = []
for i in range(sp.OutlineCount()):
    pts = clean(sp.Outline(i))
    if not os.environ.get("NODESTAIR"): pts = tidy([(int(round(x)), int(round(y))) for x, y in denotch(tidy(dejog(tidy(destair(pts)), FM(float(os.environ.get("JOG", "1.0"))))))])
    pts = tidy([(int(round(x)), int(round(y))) for x, y in desharp(pts, FM(float(os.environ.get("MINM", "0.75"))))])
    outs.append(pts)
    chk = pcbnew.SHAPE_POLY_SET(); chk.NewOutline()
    for x, y in pts: chk.Append(int(x), int(y))
    assert not selfx(pts), 'outline %d self-intersects' % i
    bad = []
    for j in range(len(pts)):
        p, q = pts[j], pts[(j+1) % len(pts)]; ang = math.degrees(math.atan2(q[1]-p[1], q[0]-p[0])) % 45
        if min(ang, 45 - ang) > 0.5: bad.append((round(p[0]/1e6, 3), round(p[1]/1e6, 3), round(q[0]/1e6, 3), round(q[1]/1e6, 3)))
    print(f'outline {i+1}: {len(pts)} points, {sp.HoleCount(i)} holes, off-angle edges: {len(bad)}', bad[:6])
for z in old: b.Remove(z)
for i, pts in enumerate(outs):
    z = pcbnew.ZONE(b); z.SetLayer(In2); z.SetNet(b.FindNet('GND')); z.SetAssignedPriority(ref.GetAssignedPriority())
    z.SetZoneName(PREFIX if len(outs) == 1 else f'{PREFIX}_{i+1}')
    z.SetCornerSmoothingType(pcbnew.ZONE_SETTINGS.CORNER_SMOOTHING_FILLET); z.SetCornerRadius(FM(opt.get('--radius', 1.0)))   # owner 2026-11-24: round the corners
    for f in ('LocalClearance', 'MinThickness', 'PadConnection', 'ThermalReliefGap', 'ThermalReliefSpokeWidth', 'IslandRemovalMode', 'FillMode'):
        getattr(z, 'Set' + f)(getattr(ref, 'Get' + f)())
    ol = z.Outline(); ol.RemoveAllContours(); ol.NewOutline()
    for x, y in pts: ol.Append(int(x), int(y))
    b.Add(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(OUT)
for z in b.Zones():
    if z.GetZoneName().startswith(PREFIX):
        fp = z.GetFilledPolysList(In2); print(z.GetZoneName(), 'outline area', round(z.Outline().Area()/1e12, 1), 'fill pieces', fp.OutlineCount())

# margin check: smallest distance from a bus track edge (B.Cu) to the new outline(s)
zs = [z for z in b.Zones() if z.GetZoneName().startswith(PREFIX)]
mind = 9e9; where = None
for t in b.GetTracks():
    if t.GetNetname() in NETS and t.Type() != pcbnew.PCB_VIA_T and t.GetLayer() == Bc:
        L = t.GetLength(); k = max(1, int(L/FM(0.05)))
        for i in range(k + 1):
            P = pcbnew.VECTOR2I(int(t.GetStart().x + (t.GetEnd().x - t.GetStart().x)*i/k), int(t.GetStart().y + (t.GetEnd().y - t.GetStart().y)*i/k))
            inside = [z for z in zs if z.Outline().Contains(P)]
            def edged(z):
                o = z.Outline().Outline(0); return min(o.Segment(j).Distance(P) for j in range(o.SegmentCount()))
            d = max((edged(z) for z in inside), default=-1e9) - t.GetWidth()/2
            if d < mind: mind = d; where = (round(P.x/1e6, 2), round(P.y/1e6, 2))
print('min bus track edge -> corridor edge:', round(mind/1e6, 3), 'mm at', where)
