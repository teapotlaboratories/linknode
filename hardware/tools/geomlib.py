"""Shared plain-Python board geometry for the LinkNode layout scripts (T30, 2026-11-22).
Obstacle outlines are read from pcbnew once (pcbnew SHAPE objects made per query leak in the SWIG bindings), then every
check is done here: points, segments (capsules) and polygons, with a spatial hash for speed.
    g = Geo(board, window=(x0, y0, x1, y1))        # mm; only items touching the window (+4 mm) are loaded
    g.clear(shape, layer, net, extra=0.0)          # True if `shape` keeps class clearance (+extra) to every other net
    g.add_track(...), g.add_via(...)               # write to the board and register as obstacles
Shapes: ('pt', (x, y), r) | ('seg', (x1, y1), (x2, y2), r) | ('poly', [(x, y), ...]).
kicad-cli DRC remains the final check."""
import math, pcbnew

mm = pcbnew.FromMM
CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
CLR = {'Default': 0.12, 'Power': 0.15, 'SoCPower': 0.12, 'RF50': 0.2, 'USB90': 0.15}

def pip(p, poly):
    x, y = p; c = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i+1) % n]
        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1) + x1: c = not c
    return c
def psd(p, a, c):
    ax, ay = a; bx, by = c; px, py = p; dx, dy = bx-ax, by-ay; L = dx*dx + dy*dy
    t = 0 if L == 0 else max(0, min(1, ((px-ax)*dx + (py-ay)*dy)/L)); return math.hypot(px-ax-t*dx, py-ay-t*dy)
def ssd(a, b_, c, d):
    def ccw(p, q, r): return (r[1]-p[1])*(q[0]-p[0]) > (q[1]-p[1])*(r[0]-p[0])
    if ccw(a, c, d) != ccw(b_, c, d) and ccw(a, b_, c) != ccw(a, b_, d): return 0.0
    return min(psd(a, c, d), psd(b_, c, d), psd(c, a, b_), psd(d, a, b_))
def edges(poly): return [(poly[i], poly[(i+1) % len(poly)]) for i in range(len(poly))]
def dist(gA, gB):
    def core(g):
        if g[0] == 'pt': return [g[1]], [], g[2]
        if g[0] == 'seg': return [g[1], g[2]], [(g[1], g[2])], g[3]
        return g[1], edges(g[1]), 0.0
    pa, ea, ra = core(gA); pb, eb, rb = core(gB)
    if gB[0] == 'poly' and any(pip(p, gB[1]) for p in pa): return 0.0
    if gA[0] == 'poly' and any(pip(p, gA[1]) for p in pb): return 0.0
    if ea and eb: best = min(ssd(a, c, d, e) for a, c in ea for d, e in eb)
    elif ea: best = min(psd(pb[0], a, c) for a, c in ea)
    elif eb: best = min(psd(pa[0], d, e) for d, e in eb)
    else: best = math.hypot(pa[0][0]-pb[0][0], pa[0][1]-pb[0][1])
    return max(0.0, best - ra - rb)
def bbox(g):
    if g[0] == 'pt': x, y = g[1]; r = g[2]; return (x-r, y-r, x+r, y+r)
    if g[0] == 'seg': r = g[3]; return (min(g[1][0], g[2][0])-r, min(g[1][1], g[2][1])-r, max(g[1][0], g[2][0])+r, max(g[1][1], g[2][1])+r)
    xs = [p[0] for p in g[1]]; ys = [p[1] for p in g[1]]; return (min(xs), min(ys), max(xs), max(ys))

class Geo:
    CELL = 1.0
    def __init__(self, board, window, H2H=0.25):
        self.b = board; self.H2H = H2H
        x0, y0, x1, y1 = window; self.NEAR = (x0-4, y0-4, x1+4, y1+4)
        self.obs = {L: {} for L in CU}; self.holes = []; self._ncl = {}
        eb = board.GetBoardEdgesBoundingBox()
        self.edge = (eb.GetLeft()/1e6, eb.GetTop()/1e6, eb.GetRight()/1e6, eb.GetBottom()/1e6)
        N = self.NEAR
        for fp in board.GetFootprints():
            bb = fp.GetBoundingBox(False, False)
            if bb.GetRight()/1e6 < N[0] or bb.GetLeft()/1e6 > N[2] or bb.GetBottom()/1e6 < N[1] or bb.GetTop()/1e6 > N[3]: continue
            for p in fp.Pads():
                for L in CU:
                    if p.IsOnLayer(L):
                        for pts in self.poly_of(p, L): self.add(p.GetNetname(), L, ('poly', pts), fp.GetReference(), 'pad')
                if p.GetDrillSizeX() > 0: self.holes.append((p.GetPosition().x/1e6, p.GetPosition().y/1e6, p.GetDrillSizeX()/1e6))
        for t in board.GetTracks(): self.add_item(t)
        # rule areas that forbid tracks/vias (e.g. the crystal keepouts, HDG p.41 item 11) are obstacles on their layers
        for z in board.Zones():
            if not z.GetIsRuleArea() or not (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias()): continue
            o = z.Outline()
            for k in range(o.OutlineCount()):
                ch = o.Outline(k); pts = [(ch.CPoint(i).x/1e6, ch.CPoint(i).y/1e6) for i in range(ch.PointCount())]
                for L in CU:
                    if z.IsOnLayer(L): self.add('__keepout__', L, ('poly', pts), z.GetZoneName(), 'keepout')
    def poly_of(self, item, L):
        ps = pcbnew.SHAPE_POLY_SET(); item.TransformShapeToPolygon(ps, L, 0, mm(0.005), pcbnew.ERROR_INSIDE)
        return [[(ps.Outline(k).CPoint(i).x/1e6, ps.Outline(k).CPoint(i).y/1e6) for i in range(ps.Outline(k).PointCount())] for k in range(ps.OutlineCount())]
    def add_item(self, t, tag=''):
        if t.GetClass() == 'PCB_VIA':
            x, y = t.GetPosition().x/1e6, t.GetPosition().y/1e6
            for L in CU: self.add(t.GetNetname(), L, ('pt', (x, y), t.GetWidth(pcbnew.F_Cu)/2e6), tag, 'via')
            self.holes.append((x, y, t.GetDrill()/1e6))
        elif t.GetClass() == 'PCB_ARC':   # T47 smooth routing: an arc is held as 12 segments along its true curve
            pts = arc_points((t.GetStart().x/1e6, t.GetStart().y/1e6), (t.GetMid().x/1e6, t.GetMid().y/1e6), (t.GetEnd().x/1e6, t.GetEnd().y/1e6), 12)
            for a, c in zip(pts, pts[1:]): self.add(t.GetNetname(), t.GetLayer(), ('seg', a, c, t.GetWidth()/2e6), tag, 'track')
        else:
            self.add(t.GetNetname(), t.GetLayer(), ('seg', (t.GetStart().x/1e6, t.GetStart().y/1e6), (t.GetEnd().x/1e6, t.GetEnd().y/1e6), t.GetWidth()/2e6), tag, 'track')
    def add(self, net, L, g, tag='', kind=''):
        bb = bbox(g); N = self.NEAR
        if bb[2] < N[0] or bb[0] > N[2] or bb[3] < N[1] or bb[1] > N[3]: return
        rec = (net, g, bb, tag, kind)
        for key in self._cells(bb): self.obs[L].setdefault(key, []).append(rec)
    def remove(self, pred):
        for L in CU:
            for k in list(self.obs[L]): self.obs[L][k] = [r for r in self.obs[L][k] if not pred(r)]
    def _cells(self, bb):
        c = self.CELL
        for i in range(int(math.floor(bb[0]/c)), int(math.floor(bb[2]/c))+1):
            for j in range(int(math.floor(bb[1]/c)), int(math.floor(bb[3]/c))+1): yield (i, j)
    def ncl(self, net):
        if net not in self._ncl:
            n = self.b.FindNet(net) if net else None
            self._ncl[net] = 0.12 if not n else CLR.get(n.GetNetClassName().split(',')[-1], 0.12)
        return self._ncl[net]
    def near(self, L, bb, grow):
        seen = set()
        for key in self._cells((bb[0]-grow, bb[1]-grow, bb[2]+grow, bb[3]+grow)):
            for r in self.obs[L].get(key, ()):
                if id(r) not in seen: seen.add(id(r)); yield r
    def clear(self, g, L, net, extra=0.0, extra_tracks=0.0, ignore=lambda r: False, same_net_ok=True):
        """g keeps class clearance (+extra; +extra_tracks against other-net tracks) to every other-net object on layer L"""
        bb = bbox(g)
        for r in self.near(L, bb, 0.6 + extra + extra_tracks):
            n2, g2, bb2, tag, kind = r
            if (same_net_ok and n2 == net) or ignore(r): continue
            need = max(self.ncl(net), self.ncl(n2)) + extra + (extra_tracks if kind == 'track' else 0.0) + 0.01
            if bb[2] + need < bb2[0] or bb2[2] + need < bb[0] or bb[3] + need < bb2[1] or bb2[3] + need < bb[1]: continue
            if dist(g, g2) < need: return False
        x0, y0, x1, y1 = self.edge; e = 0.3
        return bb[0] > x0 + e and bb[1] > y0 + e and bb[2] < x1 - e and bb[3] < y1 - e
    def hole_ok(self, x, y, dr):
        return all(math.hypot(hx-x, hy-y) >= dr/2 + hd/2 + self.H2H + 0.01 for hx, hy, hd in self.holes)
    def add_track(self, a, c, w, L, net, tag='new'):
        t = pcbnew.PCB_TRACK(self.b); t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1]))); t.SetEnd(pcbnew.VECTOR2I(mm(c[0]), mm(c[1])))
        t.SetWidth(mm(w)); t.SetLayer(L); t.SetNet(self.b.FindNet(net)); self.b.Add(t); self.add_item(t, tag); return t
    def add_via(self, x, y, net, d=0.4, h=0.2, tag='new'):
        v = pcbnew.PCB_VIA(self.b); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(d)); v.SetDrill(mm(h))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(self.b.FindNet(net)); self.b.Add(v); self.add_item(v, tag); return v

def arc_points(s, m, e, n=12):
    """points along the circular arc start-mid-end (inclusive), n segments"""
    ax, ay = s; bx, by = m; cx, cy = e
    d = 2*(ax*(by-cy) + bx*(cy-ay) + cx*(ay-by))
    if abs(d) < 1e-12: return [s, e]
    ux = ((ax*ax+ay*ay)*(by-cy) + (bx*bx+by*by)*(cy-ay) + (cx*cx+cy*cy)*(ay-by))/d
    uy = ((ax*ax+ay*ay)*(cx-bx) + (bx*bx+by*by)*(ax-cx) + (cx*cx+cy*cy)*(bx-ax))/d
    r = math.hypot(ax-ux, ay-uy); a0 = math.atan2(ay-uy, ax-ux); a1 = math.atan2(by-uy, bx-ux); a2 = math.atan2(cy-uy, cx-ux)
    def norm(t): return (t + 2*math.pi) % (2*math.pi)
    sweep = norm(a2 - a0)
    if norm(a1 - a0) > sweep: sweep -= 2*math.pi      # the mid point decides the direction
    return [(ux + r*math.cos(a0 + sweep*k/n), uy + r*math.sin(a0 + sweep*k/n)) for k in range(n + 1)]

def pad_polys(fp):
    """[(net, polygon, centre)] for a footprint's numbered pads (rectangles; good enough for 0402/0603 parts)"""
    out = []
    for p in fp.Pads():
        if not p.GetNumber(): continue
        x, y = p.GetPosition().x/1e6, p.GetPosition().y/1e6; sx, sy = p.GetSizeX()/2e6, p.GetSizeY()/2e6
        a = math.radians(p.GetOrientationDegrees()); ca, sa = math.cos(a), math.sin(a)
        out.append((p.GetNetname(), [(x + dx*ca + dy*sa, y - dx*sa + dy*ca) for dx, dy in ((-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy))], (x, y)))
    return out
