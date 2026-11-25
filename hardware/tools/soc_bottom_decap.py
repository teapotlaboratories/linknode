"""RV1106 (U100) decoupling on the bottom side, per the Rockchip HDG ("place the capacitor close to the chip pins"),
T28, owner decision 2026-11-21.
Usage: python3 soc_bottom_decap.py <board.kicad_pcb>
1. Rip up every track and via inside the SoC window (re-routed afterwards).
2. GND pins 37/57: top stub straight into the exposed pad.
3. Each supply-pin group (adjacent same-net pins share one via) gets a top stub from the pad's inner end to a via in the
   ring between the pin row and the exposed pad, at the first legal spot nearest the pins.
4. Its capacitor(s) move to B.Cu right next to that via; a short B.Cu track joins the cap pad to the via. The GND pad
   is left to the B.Cu GND fill, which also ties to the 16 thermal vias of the exposed pad.
5. The 0.9 V bulks go near (left, supply side) and far (right); ARM and DDR bulks next to their pin vias.
Clearance pre-check in plain Python: every obstacle's outline is read from KiCad once (pcbnew SHAPE objects created per
candidate leak inside the SWIG bindings: an earlier version reached 3 GB). kicad-cli DRC is the final check."""
import sys, math, json, traceback, os, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
BOARD = sys.argv[1]; mm = pcbnew.FromMM
b = pcbnew.LoadBoard(BOARD)
U = b.FindFootprintByReference('U100'); CX, CY = U.GetPosition().x/1e6, U.GetPosition().y/1e6
CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
CLR = {'Default': 0.12, 'Power': 0.15, 'SoCPower': 0.12, 'RF50': 0.2, 'USB90': 0.15}
_ncl = {}
def ncl(net):
    if net not in _ncl:
        _ncl[net] = 0.12 if not net else CLR.get(b.FindNet(net).GetNetClassName().split(',')[-1], 0.12)
    return _ncl[net]
WIN = (CX-13.5, CY-13.5, CX+13.5, CY+13.5); NEAR = (WIN[0]-4, WIN[1]-4, WIN[2]+4, WIN[3]+4)
VD, VH, H2H, STUB, BTW, MARG = 0.4, 0.2, 0.25, 0.15, 0.2, 0.01

# ---------- 1. rip-up
KEEP = []; rip = 0
for t in list(b.GetTracks()):
    s, e = t.GetStart(), t.GetEnd()
    ins = lambda p: WIN[0] < p.x/1e6 < WIN[2] and WIN[1] < p.y/1e6 < WIN[3]
    if ins(s) or ins(e): b.Remove(t); KEEP.append(t); rip += 1
print('ripped', rip, 'tracks/vias in the SoC window', flush=True)

# ---------- geometry (mm, plain Python)
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
def dist(geomA, geomB):
    """geom = ('pt', p, r) | ('seg', a, b, r) | ('poly', pts); edge-to-edge distance (0 if overlapping)"""
    def core(g):
        if g[0] == 'pt': return [g[1]], [], g[2]
        if g[0] == 'seg': return [g[1], g[2]], [(g[1], g[2])], g[3]
        return g[1], edges(g[1]), 0.0
    pa, ea, ra = core(geomA); pb, eb, rb = core(geomB)
    if geomB[0] == 'poly' and any(pip(p, geomB[1]) for p in pa): return 0.0
    if geomA[0] == 'poly' and any(pip(p, geomA[1]) for p in pb): return 0.0
    if ea and eb: best = min(ssd(a, c, d, e) for a, c in ea for d, e in eb)
    elif ea: best = min(psd(pb[0], a, c) for a, c in ea)
    elif eb: best = min(psd(pa[0], d, e) for d, e in eb)
    else: best = math.hypot(pa[0][0]-pb[0][0], pa[0][1]-pb[0][1])
    return max(0.0, best - ra - rb)
def bbox(g):
    if g[0] == 'pt': x, y = g[1]; r = g[2]; return (x-r, y-r, x+r, y+r)
    if g[0] == 'seg': r = g[3]; return (min(g[1][0], g[2][0])-r, min(g[1][1], g[2][1])-r, max(g[1][0], g[2][0])+r, max(g[1][1], g[2][1])+r)
    xs = [p[0] for p in g[1]]; ys = [p[1] for p in g[1]]; return (min(xs), min(ys), max(xs), max(ys))

# ---------- obstacles, read once
OBS = {L: [] for L in CU}; HOLES = []
def poly_of(item, L):
    ps = pcbnew.SHAPE_POLY_SET(); item.TransformShapeToPolygon(ps, L, 0, mm(0.005), pcbnew.ERROR_INSIDE)
    out = []
    for k in range(ps.OutlineCount()):
        ch = ps.Outline(k); out.append([(ch.CPoint(i).x/1e6, ch.CPoint(i).y/1e6) for i in range(ch.PointCount())])
    return out
def add_obstacle(net, L, g, tag=''):
    bb = bbox(g)
    if bb[2] < NEAR[0] or bb[0] > NEAR[2] or bb[3] < NEAR[1] or bb[1] > NEAR[3]: return
    OBS[L].append((net, g, bb, tag))
for fp in b.GetFootprints():
    bb = fp.GetBoundingBox(False, False)
    if bb.GetRight()/1e6 < NEAR[0] or bb.GetLeft()/1e6 > NEAR[2] or bb.GetBottom()/1e6 < NEAR[1] or bb.GetTop()/1e6 > NEAR[3]: continue
    for p in fp.Pads():
        for L in CU:
            if p.IsOnLayer(L):
                for pts in poly_of(p, L): add_obstacle(p.GetNetname(), L, ('poly', pts), fp.GetReference())
        if p.GetDrillSizeX() > 0: HOLES.append((p.GetPosition().x/1e6, p.GetPosition().y/1e6, p.GetDrillSizeX()/1e6))
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        x, y = t.GetPosition().x/1e6, t.GetPosition().y/1e6
        for L in CU: add_obstacle(t.GetNetname(), L, ('pt', (x, y), t.GetWidth(pcbnew.F_Cu)/2e6))
        HOLES.append((x, y, t.GetDrill()/1e6))
    else:
        g = ('seg', (t.GetStart().x/1e6, t.GetStart().y/1e6), (t.GetEnd().x/1e6, t.GetEnd().y/1e6), t.GetWidth()/2e6)
        add_obstacle(t.GetNetname(), t.GetLayer(), g)
print('obstacles', sum(len(v) for v in OBS.values()), 'holes', len(HOLES), flush=True)

def clear(g, L, net, ignore_tag=None):
    bb = bbox(g)
    for n2, g2, bb2, tag in OBS[L]:
        if n2 == net or (ignore_tag and tag == ignore_tag): continue
        need = max(ncl(net), ncl(n2)) + MARG
        if bb[2] + need < bb2[0] or bb2[2] + need < bb[0] or bb[3] + need < bb2[1] or bb2[3] + need < bb[1]: continue
        if dist(g, g2) < need: return False
    return True
def hole_ok(x, y, dr):
    return all(math.hypot(hx-x, hy-y) >= dr/2 + hd/2 + H2H + MARG for hx, hy, hd in HOLES)

def add_via(x, y, net):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(VD)); v.SetDrill(mm(VH))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet(net)); b.Add(v)
    for L in CU: add_obstacle(net, L, ('pt', (x, y), VD/2))
    HOLES.append((x, y, VH))
def add_track(a, c, w, L, net):
    t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1]))); t.SetEnd(pcbnew.VECTOR2I(mm(c[0]), mm(c[1])))
    t.SetWidth(mm(w)); t.SetLayer(L); t.SetNet(b.FindNet(net)); b.Add(t); add_obstacle(net, L, ('seg', a, c, w/2))

pad = {p.GetNumber(): p for p in U.Pads() if p.GetNumber()}
def geom(num):
    p = pad[num]; x, y = p.GetPosition().x/1e6, p.GetPosition().y/1e6; dx, dy = x - CX, y - CY
    n = (-math.copysign(1, dx), 0.0) if abs(dx) > abs(dy) else (0.0, -math.copysign(1, dy))
    bb = p.GetBoundingBox(); half = max(bb.GetWidth(), bb.GetHeight())/2e6
    return (x, y), (x + n[0]*half, y + n[1]*half), n, (-n[1], n[0])

# ---------- 2. GND pins into the exposed pad
for num in ('37', '57'):
    _, inner, n, _ = geom(num)
    add_track(inner, (inner[0] + n[0]*2.4, inner[1] + n[1]*2.4), 0.18, pcbnew.F_Cu, 'GND'); print('GND pin', num, 'stub into EP')

# ---------- 3. vias for supply groups
GROUPS = [
 (['1'], ['C603']), (['10'], ['C610']), (['13'], ['C629']), (['19'], ['C604']), (['24'], ['C602']), (['28'], ['C630']),
 (['30'], ['C637']), (['31'], ['C625']), (['43'], ['C631']), (['49', '50'], ['C623']), (['51'], ['C611']),
 (['54', '55'], ['C612', 'C613', 'C619']), (['53'], ['C626', 'C628']), (['56'], ['C624']),
 (['61'], ['C632']), (['66'], ['C505', 'R503']), (['67'], ['C614']), (['70'], ['C627']), (['71'], ['C615', 'C620']),
 (['81'], ['C633']), (['82'], ['C616']), (['88'], ['C634']), (['96'], ['C601']), (['101'], ['C635']),
 (['102'], ['R605']), (['103'], ['C617']), (['108'], ['C636']), (['115'], ['C606', 'C607']), (['116'], ['C618']), (['52'], ['R604'])]
BULK = [('C608', '10'), ('C609', '71'), ('C605', '115'), ('C621', '49'), ('C622', '56')]
report = {}; viapos = {}
for pins, parts in GROUPS:
    net = pad[pins[0]].GetNetname(); gs = [geom(p) for p in pins]; n, tan = gs[0][2], gs[0][3]
    ax = sum(g[1][0] for g in gs)/len(gs); ay = sum(g[1][1] for g in gs)/len(gs)
    best = None
    for r in [0.55 + 0.05*k for k in range(24)]:
        for lat in [0.05*k for k in range(17)]:
            for sgn in (1, -1):
                vx, vy = ax + n[0]*r + tan[0]*lat*sgn, ay + n[1]*r + tan[1]*lat*sgn
                if max(abs(vx-CX), abs(vy-CY)) < 3.5 + VD/2 + 0.16 or not hole_ok(vx, vy, VH): continue
                if not all(clear(('pt', (vx, vy), VD/2), L, net) for L in CU): continue
                if not all(clear(('seg', g[1], (vx, vy), STUB/2), pcbnew.F_Cu, net) for g in gs): continue
                cost = r + 1.5*lat
                if best is None or cost < best[0]: best = (cost, vx, vy)
        if best and best[0] <= r + 0.05: break
    if not best: print('NO VIA for pins', pins, net, flush=True); continue
    _, vx, vy = best
    add_via(vx, vy, net); [add_track(g[1], (vx, vy), STUB, pcbnew.F_Cu, net) for g in gs]
    viapos[pins[0]] = (vx, vy, net)
    report['/'.join(pins)] = {'net': net.split('/')[-1][-20:], 'via': [round(vx, 3), round(vy, 3)],
                              'pin_to_via_mm': round(math.hypot(vx-ax, vy-ay), 2)}
print('vias placed', len(viapos), flush=True)

# ---------- 4/5. parts on the bottom
def pad_polys(fp):
    out = []
    for p in fp.Pads():
        if not p.GetNumber(): continue
        x, y = p.GetPosition().x/1e6, p.GetPosition().y/1e6; sx, sy = p.GetSizeX()/2e6, p.GetSizeY()/2e6
        a = math.radians(p.GetOrientationDegrees()); ca, sa = math.cos(a), math.sin(a)
        pts = [(x + dx*ca + dy*sa, y - dx*sa + dy*ca) for dx, dy in ((-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy))]
        out.append((p.GetNetname(), pts, (x, y)))
    return out
placed_boxes = []
def place_bottom(ref, anchor_pin, maxd=4.0):
    vx, vy, net = viapos[anchor_pin]
    fp = b.FindFootprintByReference(ref)
    orig = (fp.GetPosition(), fp.GetOrientationDegrees(), fp.IsFlipped())
    if not fp.IsFlipped(): fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    best = None
    for rot in (0, 90, 180, 270):
        fp.SetOrientationDegrees(rot)
        for k in range(int(maxd/0.05)):
            R = 0.35 + 0.05*k
            if best and best[0] < R - 0.6: break
            steps = max(8, int(2*math.pi*R/0.1))
            for j in range(steps):
                ang = 2*math.pi*j/steps
                fp.SetPosition(pcbnew.VECTOR2I(mm(vx + R*math.cos(ang)), mm(vy + R*math.sin(ang))))
                pp = pad_polys(fp)
                mine = [q for q in pp if q[0] == net]
                if not mine: return None
                d = math.hypot(mine[0][2][0]-vx, mine[0][2][1]-vy)
                if d < VD/2 + 0.33 or (best and d >= best[0]): continue
                if any(math.hypot(hx-c[0], hy-c[1]) < hd/2 + 0.4 for _, _, c in pp for hx, hy, hd in HOLES): continue
                if not all(clear(('poly', pts), pcbnew.B_Cu, n2, ignore_tag=ref) for n2, pts, _ in pp): continue
                xs = [p[0] for _, pts, _ in pp for p in pts]; ys = [p[1] for _, pts, _ in pp for p in pts]
                box = (min(xs)-0.2, min(ys)-0.2, max(xs)+0.2, max(ys)+0.2)
                if any(not (box[2] < o[0] or o[2] < box[0] or box[3] < o[1] or o[3] < box[1]) for o in placed_boxes): continue
                if not clear(('seg', mine[0][2], (vx, vy), BTW/2), pcbnew.B_Cu, net): continue
                best = (d, rot, (vx + R*math.cos(ang), vy + R*math.sin(ang)), mine[0][2], box)
    if not best:                     # put it back where it was (top side) for manual placement
        if not orig[2]: fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetOrientationDegrees(orig[1]); fp.SetPosition(orig[0]); return None
    d, rot, pos, lp, box = best
    fp.SetOrientationDegrees(rot); fp.SetPosition(pcbnew.VECTOR2I(mm(pos[0]), mm(pos[1])))
    add_track(lp, (vx, vy), BTW, pcbnew.B_Cu, net); placed_boxes.append(box)
    for n2, pts, _ in pad_polys(fp): add_obstacle(n2, pcbnew.B_Cu, ('poly', pts), ref)
    return round(d, 2)

for pas in (0, 1):                   # first cap of every pin first, then the extra caps
    for pins, parts in GROUPS:
        if pins[0] not in viapos: continue
        for ref in (parts[:1] if pas == 0 else parts[1:]):
            d = place_bottom(ref, pins[0])
            report['/'.join(pins)].setdefault('parts', {})[ref] = d
            if d is None: print('NO SPOT for', ref, 'at pin', pins[0], flush=True)
for ref, pin in BULK:
    d = place_bottom(ref, pin, maxd=4.5) if pin in viapos else None
    report.setdefault('bulk', {})[ref] = [pin, d]
    if d is None: print('NO SPOT for bulk', ref, 'near pin', pin, flush=True)
b.Save(BOARD)
print(json.dumps(report, indent=1))
