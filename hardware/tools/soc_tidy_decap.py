"""T29: tidy RV1106 (U100) bottom decoupling into rows like the Rockchip RV1106 EVB (EVB1 user guide Fig 1-4 p.10).
Usage: python3 soc_tidy_decap.py <board.kicad_pcb>
1. Rip up every track and via in the SoC window (placement only: the area is left for routing).
2. GND pins 37/57: top stub into the exposed pad.
3. One via per supply-pin group in the ring between the pin row and the exposed pad (same search as T28).
4. Fixed slots per chip side, every part radial (pads along the side normal):
     inner row: power pad centre at r = 4.04 mm, the other pad inward (toward the exposed-pad vias), t = -2.1 .. 2.1 step 1.05
     outer row: power pad centre at r = 5.75 mm, the other pad outward (under the pin ring),          t = -4.2 .. 4.2 step 1.05
   Parts are assigned greedily, cheapest (via -> power pad distance, inner row preferred) first, then a short B.Cu link
   from the via to the power pad. First cap of every pin before the extra caps.
5. Bulks (10 uF) in a third row on their side, no link (routing later). C608 left = near the VDD_0V9 entry (L5), C609 right = far.
6. Y501 (24 MHz) GND pads: a GND via next to each (HDG p.41 item 10).
7. Rule areas: no tracks or vias on In2/B.Cu under Y501 and Y502, and on F.Cu between Y501's pads (HDG p.41 item 11).
8. C628 value 1uF / LCSC C52923 (schematic changed with the scripting server; footprint kept in step for parity).
Geometry is checked in plain Python (obstacle outlines read from KiCad once). kicad-cli DRC is the final check."""
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
R_IN, R_OUT, PITCH = 4.04, 5.75, 1.05
T_IN = [PITCH*k for k in range(-2, 3)]; T_OUT = [PITCH*k for k in range(-5, 6)]   # +-5.25: the corner square stays free, so this does not meet the next side's row

# ---------- 0. C628 value (schematic already changed)
c628 = b.FindFootprintByReference('C628'); c628.SetValue('1uF')
c628.SetField('LCSC', 'C52923')

# ---------- 1. rip-up
KEEP = []; rip = 0
ins = lambda p: WIN[0] < p.x/1e6 < WIN[2] and WIN[1] < p.y/1e6 < WIN[3]
for t in list(b.GetTracks()):
    if ins(t.GetStart()) or ins(t.GetEnd()): b.Remove(t); KEEP.append(t); rip += 1
print('ripped', rip, flush=True)

# ---------- geometry
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

OBS = {L: [] for L in CU}; HOLES = []
def poly_of(item, L):
    ps = pcbnew.SHAPE_POLY_SET(); item.TransformShapeToPolygon(ps, L, 0, mm(0.005), pcbnew.ERROR_INSIDE)
    return [[(ps.Outline(k).CPoint(i).x/1e6, ps.Outline(k).CPoint(i).y/1e6) for i in range(ps.Outline(k).PointCount())] for k in range(ps.OutlineCount())]
def add_obstacle(net, L, g, tag=''):
    bb = bbox(g)
    if bb[2] < NEAR[0] or bb[0] > NEAR[2] or bb[3] < NEAR[1] or bb[1] > NEAR[3]: return
    OBS[L].append((net, g, bb, tag))
def remove_tag(tag):
    for L in CU: OBS[L] = [o for o in OBS[L] if o[3] != tag]
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
        add_obstacle(t.GetNetname(), t.GetLayer(), ('seg', (t.GetStart().x/1e6, t.GetStart().y/1e6), (t.GetEnd().x/1e6, t.GetEnd().y/1e6), t.GetWidth()/2e6))
print('obstacles', sum(len(v) for v in OBS.values()), flush=True)

def clear(g, L, net, ignore_tag=None):
    bb = bbox(g)
    for n2, g2, bb2, tag in OBS[L]:
        if n2 == net or (ignore_tag and tag == ignore_tag): continue
        need = max(ncl(net), ncl(n2)) + MARG
        if bb[2] + need < bb2[0] or bb2[2] + need < bb[0] or bb[3] + need < bb2[1] or bb2[3] + need < bb[1]: continue
        if dist(g, g2) < need: return False
    return True
def hole_ok(x, y, dr): return all(math.hypot(hx-x, hy-y) >= dr/2 + hd/2 + H2H + MARG for hx, hy, hd in HOLES)
def add_via(x, y, net):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(VD)); v.SetDrill(mm(VH))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet(net)); b.Add(v)
    for L in CU: add_obstacle(net, L, ('pt', (x, y), VD/2))
    HOLES.append((x, y, VH))
def add_track(a, c, w, L, net):
    t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1]))); t.SetEnd(pcbnew.VECTOR2I(mm(c[0]), mm(c[1])))
    t.SetWidth(mm(w)); t.SetLayer(L); t.SetNet(b.FindNet(net)); b.Add(t); add_obstacle(net, L, ('seg', a, c, w/2))

pad = {p.GetNumber(): p for p in U.Pads() if p.GetNumber()}
def side_of(x, y):
    dx, dy = x - CX, y - CY
    if abs(dx) > abs(dy): return ('R' if dx > 0 else 'L')
    return ('B' if dy > 0 else 'T')
NORM = {'L': (-1, 0), 'R': (1, 0), 'T': (0, -1), 'B': (0, 1)}       # outward unit normal
def frame(s): u = NORM[s]; return u, (-u[1], u[0])
def geom(num):
    p = pad[num]; x, y = p.GetPosition().x/1e6, p.GetPosition().y/1e6; s = side_of(x, y); u, v = frame(s)
    bb = p.GetBoundingBox(); half = max(bb.GetWidth(), bb.GetHeight())/2e6
    n = (-u[0], -u[1]); return (x, y), (x + n[0]*half, y + n[1]*half), n, v, s

# ---------- 2. GND pins into the exposed pad
for num in ('37', '57'):
    _, inner, n, _, _ = geom(num); add_track(inner, (inner[0] + n[0]*2.4, inner[1] + n[1]*2.4), 0.18, pcbnew.F_Cu, 'GND')

# ---------- 3. vias
GROUPS = [
 (['1'], ['C603']), (['10'], ['C610']), (['13'], ['C629']), (['19'], ['C604']), (['24'], ['C602']), (['28'], ['C630']),
 (['30'], ['C637']), (['31'], ['C625']), (['43'], ['C631']), (['49', '50'], ['C623']), (['51'], ['C611']),
 (['54', '55'], ['C612', 'C613', 'C619']), (['53'], ['C626', 'C628']), (['56'], ['C624']),
 (['61'], ['C632']), (['66'], ['C505', 'R503']), (['67'], ['C614']), (['70'], ['C627']), (['71'], ['C615', 'C620']),
 (['81'], ['C633']), (['82'], ['C616']), (['88'], ['C634']), (['96'], ['C601']), (['101'], ['C635']),
 (['102'], ['R605']), (['103'], ['C617']), (['108'], ['C636']), (['115'], ['C606', 'C607']), (['116'], ['C618']), (['52'], ['R604'])]
BULK = [('C608', 'L', None), ('C609', 'R', None), ('C605', None, '115'), ('C621', None, '49'), ('C622', None, '56')]
MANAGED = [r for _, parts in GROUPS for r in parts] + [r for r, _, _ in BULK]
for r in MANAGED: remove_tag(r)          # their current spots are about to change
viapos = {}; report = {}
for pins, parts in GROUPS:
    net = pad[pins[0]].GetNetname(); gs = [geom(p) for p in pins]; n, tan = gs[0][2], gs[0][3]
    ax = sum(g[1][0] for g in gs)/len(gs); ay = sum(g[1][1] for g in gs)/len(gs)
    best = None; LATMAX = 25 if pins == ['52'] else 17
    for r in [0.55 + 0.05*k for k in range(24)]:
        for lat in [0.05*k for k in range(LATMAX)]:
            for sgn in (1, -1):
                vx, vy = ax + n[0]*r + tan[0]*lat*sgn, ay + n[1]*r + tan[1]*lat*sgn
                if max(abs(vx-CX), abs(vy-CY)) < 3.5 + VD/2 + 0.16 or not hole_ok(vx, vy, VH): continue
                if not all(clear(('pt', (vx, vy), VD/2), L, net) for L in CU): continue
                if not all(clear(('seg', g[1], (vx, vy), STUB/2), pcbnew.F_Cu, net) for g in gs): continue
                cost = r + 1.5*lat
                if best is None or cost < best[0]: best = (cost, vx, vy)
        if best and best[0] <= r + 0.05: break
    if not best: print('NO VIA for pins', pins, flush=True); continue
    _, vx, vy = best; add_via(vx, vy, net); [add_track(g[1], (vx, vy), STUB, pcbnew.F_Cu, net) for g in gs]
    viapos[pins[0]] = (vx, vy, net, gs[0][4])
    report['/'.join(pins)] = {'via': [round(vx, 3), round(vy, 3)], 'p2v': round(math.hypot(vx-ax, vy-ay), 2), 'parts': {}}
print('vias', len(viapos), flush=True)

# ---------- 4. slots
def pad_polys(fp):
    out = []
    for p in fp.Pads():
        if not p.GetNumber(): continue
        x, y = p.GetPosition().x/1e6, p.GetPosition().y/1e6; sx, sy = p.GetSizeX()/2e6, p.GetSizeY()/2e6
        a = math.radians(p.GetOrientationDegrees()); ca, sa = math.cos(a), math.sin(a)
        out.append((p.GetNetname(), [(x + dx*ca + dy*sa, y - dx*sa + dy*ca) for dx, dy in ((-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy))], (x, y)))
    return out
SLOTS = []   # (side, row, t, rpower): rows are fixed, the position along the row is free (0.05 mm steps)
for sd in 'LRTB':
    for k in range(-46, 47): SLOTS.append((sd, 'in', round(0.05*k, 2), R_IN))
    for k in range(-105, 106): SLOTS.append((sd, 'out', round(0.05*k, 2), R_OUT))
used = set(); boxes = []
def try_slot(fp, net, slot, link_from=None):
    """put fp radially in slot with its `net` pad at the slot's power radius; return (cost, state) or None"""
    s, row, t, rp = slot; u, v = frame(s)
    if not fp.IsFlipped(): fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    best = None
    for rot in (0, 90, 180, 270):
        fp.SetOrientationDegrees(rot); fp.SetPosition(pcbnew.VECTOR2I(mm(CX), mm(CY)))
        pp = pad_polys(fp); mine = [q for q in pp if q[0] == net]; other = [q for q in pp if q[0] != net]
        if not mine or not other: return None
        # radial direction of (power pad -> other pad) must point inward on the inner row, outward on the outer row
        d = (other[0][2][0]-mine[0][2][0], other[0][2][1]-mine[0][2][1]); sp = math.hypot(*d)
        radial = (d[0]*u[0] + d[1]*u[1])/sp
        if (row == 'in' and radial > -0.99) or (row == 'out' and radial < 0.99): continue
        # move so the power pad sits at (rp, t)
        want = (CX + u[0]*rp + v[0]*t, CY + u[1]*rp + v[1]*t)
        off = (want[0]-mine[0][2][0], want[1]-mine[0][2][1])
        fp.SetPosition(pcbnew.VECTOR2I(mm(CX + off[0]), mm(CY + off[1])))
        pp = pad_polys(fp); mine = [q for q in pp if q[0] == net][0]
        if any(dist(('pt', (hx, hy), hd/2), ('poly', pts)) < 0.12 for _, pts, _ in pp for hx, hy, hd in HOLES): return None
        if not all(clear(('poly', pts), pcbnew.B_Cu, n2, ignore_tag=fp.GetReference()) for n2, pts, _ in pp): return None
        xs = [p[0] for _, pts, _ in pp for p in pts]; ys = [p[1] for _, pts, _ in pp for p in pts]
        cy = fp.GetCourtyard(pcbnew.B_CrtYd).BBox()
        box = (cy.GetLeft()/1e6 - 0.01, cy.GetTop()/1e6 - 0.01, cy.GetRight()/1e6 + 0.01, cy.GetBottom()/1e6 + 0.01) if cy.GetWidth() > 0 else (min(xs)-0.18, min(ys)-0.18, max(xs)+0.18, max(ys)+0.18)
        if any(not (box[2] < o[0] or o[2] < box[0] or box[3] < o[1] or o[3] < box[1]) for o in boxes): return None
        cost = 0.0
        if link_from:
            if not clear(('seg', mine[2], link_from, BTW/2), pcbnew.B_Cu, net): return None
            cost = math.hypot(mine[2][0]-link_from[0], mine[2][1]-link_from[1])
        best = (cost, rot, fp.GetPosition(), mine[2], box)
    return best
def commit(fp, net, st, link_from):
    cost, rot, pos, lp, box = st
    fp.SetOrientationDegrees(rot); fp.SetPosition(pos); boxes.append(box)
    remove_tag(fp.GetReference())
    for n2, pts, _ in pad_polys(fp): add_obstacle(n2, pcbnew.B_Cu, ('poly', pts), fp.GetReference())
    if link_from: add_track(link_from, lp, BTW, pcbnew.B_Cu, net)
ORIG = {}
for r in MANAGED:
    f = b.FindFootprintByReference(r); ORIG[r] = (f.GetPosition(), f.GetOrientationDegrees(), f.IsFlipped())
def restore(ref):
    raise SystemExit('no legal spot for %s: stop rather than leave it overlapping the new rows' % ref)
    f = b.FindFootprintByReference(ref); pos, rot, fl = ORIG[ref]
    if f.IsFlipped() != fl: f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    f.SetOrientationDegrees(rot); f.SetPosition(pos)
def candidates(ref, pin):
    vx, vy, net, sd = viapos[pin]; u, v = frame(sd); tv = (vx-CX)*v[0] + (vy-CY)*v[1]
    out = []
    for slot in SLOTS:
        if slot[0] == sd:
            if abs(slot[2] - tv) > 2.6: continue
        elif not (slot[1] == 'out' and abs(slot[2]) > 4.0): continue     # a neighbour's corner end of the outer row
        out.append(slot)
    return out
def best_slot(ref, pin):
    vx, vy, net, sd = viapos[pin]; fp = b.FindFootprintByReference(ref); best = None
    for slot in candidates(ref, pin):
        st = try_slot(fp, net, slot, (vx, vy))
        if not st: continue
        c = st[0] + (0.0 if slot[1] == 'in' else 0.35) + (0.0 if slot[0] == sd else 0.8)
        if best is None or c < best[0]: best = (c, slot, st)
    return best
def assign(jobs):
    """hardest first (fewest legal spots), each to its cheapest legal spot"""
    n = {}
    for ref, pin in jobs:
        vx, vy, net, sd = viapos[pin]; fp = b.FindFootprintByReference(ref)
        n[ref] = sum(1 for sl in candidates(ref, pin) if try_slot(fp, net, sl, (vx, vy)))
    PRIORITY = ('C624',)          # pin 56 sits in the crowded 49-56 run; it lost its spot when placed by count
    for ref, pin in sorted(jobs, key=lambda j: (j[0] not in PRIORITY, n[j[0]])):
        best = best_slot(ref, pin)
        if not best:                       # no legal link: nearest free row spot, no link (routing connects it)
            vx, vy, net, sd = viapos[pin]; fp = b.FindFootprintByReference(ref); fb = None
            for slot in SLOTS:
                if slot[0] != sd and not (slot[1] == 'out' and abs(slot[2]) > 4.0): continue
                st = try_slot(fp, net, slot)
                if not st: continue
                d = math.hypot(st[3][0]-vx, st[3][1]-vy) + (0.0 if slot[0] == sd else 0.8)
                if fb is None or d < fb[0]: fb = (d, slot)
            if fb:
                st = try_slot(fp, net, fb[1]); commit(fp, net, st, None)
                report['/'.join(next(g[0] for g in GROUPS if g[0][0] == pin))]['parts'][ref] = [fb[1][0], fb[1][1], fb[1][2], 'no link %.2f' % fb[0]]
                print('no link for', ref, 'pin', pin, 'spot %.2f mm from via' % fb[0], flush=True)
            else: print('NO SLOT for', ref, 'pin', pin, flush=True); restore(ref)
            continue
        c, slot, st = best; vx, vy, net, sd = viapos[pin]; fp = b.FindFootprintByReference(ref)
        st = try_slot(fp, net, slot, (vx, vy)); commit(fp, net, st, (vx, vy))
        report['/'.join(next(g[0] for g in GROUPS if g[0][0] == pin))]['parts'][ref] = [slot[0], slot[1], slot[2], round(st[0], 2)]
first = [(parts[0], pins[0]) for pins, parts in GROUPS if pins[0] in viapos]
extra = [(r, pins[0]) for pins, parts in GROUPS if pins[0] in viapos for r in parts[1:]]
assign(first); assign(extra)
for pins, parts in GROUPS:          # parts of a group without a via: outer row slot nearest its pin, no link
    if pins[0] in viapos: continue
    p = pad[pins[0]]; x, y = p.GetPosition().x/1e6, p.GetPosition().y/1e6; s = side_of(x, y); u, v = frame(s)
    tp = (x-CX)*v[0] + (y-CY)*v[1]
    for ref in parts:
        fp = b.FindFootprintByReference(ref); net = p.GetNetname()
        for slot in sorted([q for q in SLOTS if q[0] == s], key=lambda q: (q[1] != 'out', abs(q[2]-tp))):
            st = try_slot(fp, net, slot)
            if st: commit(fp, net, st, None); report.setdefault('/'.join(pins), {'parts': {}})['parts'][ref] = [slot[0], slot[1], round(slot[2], 2), 'no via']; break
        else: print('NO SLOT for', ref, flush=True); restore(ref)

# ---------- 5. bulks: third row, radial, power pad inward at r = 7.6, no link
R_BULK = 7.6
for ref, side, pin in BULK:
    fp = b.FindFootprintByReference(ref); net = [q.GetNetname() for q in fp.Pads() if q.GetNetname() != 'GND'][0]
    if side is None:
        p = pad[pin]; x, y = p.GetPosition().x/1e6, p.GetPosition().y/1e6; side = side_of(x, y); u, v = frame(side)
        tp = (x-CX)*v[0] + (y-CY)*v[1]
    else: tp = 0.0
    done = False
    for rb in (R_BULK, 8.2, 8.8, 9.4):
        for dt in sorted([0.25*k for k in range(-20, 21)], key=abs):
            st = try_slot(fp, net, (side, 'out', tp + dt, rb))
            if st: commit(fp, net, st, None); report.setdefault('bulk', {})[ref] = [side, round(tp + dt, 2), rb]; done = True; break
        if done: break
    if not done: print('NO SPOT for bulk', ref, flush=True); restore(ref)

# ---------- 6. Y501 GND vias
y = b.FindFootprintByReference('Y501'); yc = (y.GetPosition().x/1e6, y.GetPosition().y/1e6)
_yb = y.GetBoundingBox(False, False); ybb = (_yb.GetLeft()/1e6, _yb.GetTop()/1e6, _yb.GetRight()/1e6, _yb.GetBottom()/1e6)
for p in y.Pads():
    if p.GetNetname() != 'GND': continue
    px, py = p.GetPosition().x/1e6, p.GetPosition().y/1e6; sx, sy = p.GetBoundingBox().GetWidth()/2e6, p.GetBoundingBox().GetHeight()/2e6
    ox, oy = math.copysign(1, px-yc[0]), math.copysign(1, py-yc[1])   # away from the crystal centre
    best = None
    for k in range(0, 40):
        for (dx, dy) in ((ox, 0), (0, oy), (ox*0.7, oy*0.7)):
            r = 0.05*k
            vx = px + dx*(sx + VD/2 + 0.02 + r) if dx else px
            vy = py + dy*(sy + VD/2 + 0.02 + r) if dy else py
            if dx and dy: vx, vy = px + dx*(sx + 0.3 + r), py + dy*(sy + 0.3 + r)
            if ybb[0] - 0.25 < vx < ybb[2] + 0.25 and ybb[1] - 0.25 < vy < ybb[3] + 0.25: continue   # outside the crystal keepout
            if not hole_ok(vx, vy, VH) or not all(clear(('pt', (vx, vy), VD/2), L, 'GND') for L in CU): continue
            if not clear(('seg', (px, py), (vx, vy), 0.125), pcbnew.F_Cu, 'GND', ignore_tag='Y501'): continue
            d = math.hypot(vx-px, vy-py)
            if best is None or d < best[0]: best = (d, vx, vy)
        if best: break
    if best:
        add_via(best[1], best[2], 'GND'); add_track((px, py), (best[1], best[2]), 0.25, pcbnew.F_Cu, 'GND')
        report.setdefault('Y501_gnd_vias', []).append([p.GetNumber(), round(best[0], 2)])
    else: print('NO GND via for Y501 pad', p.GetNumber(), flush=True)

# ---------- 7. crystal keepouts (rule areas: no tracks, no vias; copper fill and pads allowed)
def rule_area(name, rect, layers):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetZoneName(name)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    z.SetDoNotAllowZoneFills(False)
    ls = pcbnew.LSET()
    for L in layers: ls.AddLayer(L)
    z.SetLayerSet(ls)
    o = z.Outline(); o.NewOutline()
    for x, yy in ((rect[0], rect[1]), (rect[2], rect[1]), (rect[2], rect[3]), (rect[0], rect[3])): o.Append(mm(x), mm(yy))
    b.Add(z); return z
for ref in ('Y501', 'Y502'):
    fp = b.FindFootprintByReference(ref); bb = fp.GetBoundingBox(False, False)
    r = (bb.GetLeft()/1e6, bb.GetTop()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6)
    rule_area('Keepout under %s (HDG p.41 item 11)' % ref, r, [pcbnew.In2_Cu, pcbnew.B_Cu])
    ps = [q for q in fp.Pads() if q.GetNumber()]
    xs = [q.GetPosition().x/1e6 for q in ps]; ys = [q.GetPosition().y/1e6 for q in ps]
    cx, cy = fp.GetPosition().x/1e6, fp.GetPosition().y/1e6
    if max(xs) - min(xs) >= max(ys) - min(ys):     # pads spread along x: keep out the band between them
        lo = max(q.GetPosition().x/1e6 + q.GetBoundingBox().GetWidth()/2e6 for q in ps if q.GetPosition().x/1e6 < cx)
        hi = min(q.GetPosition().x/1e6 - q.GetBoundingBox().GetWidth()/2e6 for q in ps if q.GetPosition().x/1e6 > cx)
        rect = (lo + 0.15, r[1], hi - 0.15, r[3])
    else:
        lo = max(q.GetPosition().y/1e6 + q.GetBoundingBox().GetHeight()/2e6 for q in ps if q.GetPosition().y/1e6 < cy)
        hi = min(q.GetPosition().y/1e6 - q.GetBoundingBox().GetHeight()/2e6 for q in ps if q.GetPosition().y/1e6 > cy)
        rect = (r[0], lo + 0.15, r[2], hi - 0.15)
    if min(rect[2]-rect[0], rect[3]-rect[1]) > 0.3: rule_area('Keepout between %s pads (HDG p.41 item 11)' % ref, rect, [pcbnew.F_Cu])
    report.setdefault('keepouts', []).append(ref)
b.Save(BOARD)
print(json.dumps(report, indent=0))
