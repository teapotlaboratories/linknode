"""T32 trial re-pack of the whole board (owner, 2026-11-22). Run it on a COPY of linknode.kicad_pcb, never on the main board.
Usage: python3 t32_place.py <copy.kicad_pcb>   (env T32_W / T32_H set the outline in mm, default 70 x 64)

What it does, in order:
 1. Clears all tracks and vias (routing is redone after placement) and draws the new outline (rounded rectangle, r = 2 mm).
 2. Moves the RV1106 cluster rigidly (SoC + SoC Power parts within +-12 mm of U100, plus R19; R511 left out), with
    the crystal keepouts and the VDD_0V9 In2 zone. The approved T29 decoupling arrangement is kept exactly.
 3. Pins the anchors: mounting holes, edge connectors (same orientation and edge offset as before), J3/J4, the modules.
 4. Packs each sheet's remaining top parts inside its floorplan region, greedily: the part with the most connections to
    what is already placed goes next, at the 0.25 mm grid position and rotation with the least weighted pad-to-net
    distance (GND ignored, busy rails down-weighted) plus a pull toward the block's anchor. Courtyards never overlap
    (0.1 mm gap, checked on a 0.05 mm raster).
 5. Moves the small passives to the bottom and packs them the same way, under the parts they connect to. Converter
    power-loop and bulk caps, the GPS LDO caps and the RF (Antenna sheet) parts stay on top.
 6. Reshapes the copper pours to the new outline. Zone refill, DRC and renders are separate steps.
Prints a JSON report (placed, failed, cluster shift)."""
import sys, os, re, math, json, traceback
import numpy as np, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
BOARD = sys.argv[1]
X0, Y0 = 100.0, 100.0
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t32_layouts import LAYOUTS
LAY = LAYOUTS[os.environ.get('T32_LAYOUT', 'v1')]
W, H = float(os.environ.get('T32_W', LAY['W'])), float(os.environ.get('T32_H', LAY['H']))
OLD_BOTTOM = 180.0
b = pcbnew.LoadBoard(BOARD)
mm = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))
FP = {f.GetReference(): f for f in b.GetFootprints()}
def pos(f): return (f.GetPosition().x/1e6, f.GetPosition().y/1e6)
KEEP = []          # removed SWIG items must stay referenced
report = {'layout': os.environ.get('T32_LAYOUT', 'v1'), 'outline': [W, H], 'failed': [], 'placed_top': 0, 'placed_bottom': 0}

# 1. routing and outline -------------------------------------------------------------------------------------------
for t in list(b.GetTracks()): KEEP.append(t); b.Remove(t)
for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts: KEEP.append(d); b.Remove(d)
def edge(kind, *pts):
    s = pcbnew.PCB_SHAPE(b); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
    if kind == 'seg': s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*pts[0])); s.SetEnd(V(*pts[1]))
    else: s.SetShape(pcbnew.SHAPE_T_ARC); s.SetArcGeometry(V(*pts[0]), V(*pts[1]), V(*pts[2]))
    b.Add(s)
R = 2.0; X1, Y1 = X0 + W, Y0 + H; k = R*(1 - math.sqrt(0.5))
edge('seg', (X0+R, Y0), (X1-R, Y0)); edge('seg', (X1, Y0+R), (X1, Y1-R)); edge('seg', (X1-R, Y1), (X0+R, Y1)); edge('seg', (X0, Y1-R), (X0, Y0+R))
edge('arc', (X0, Y0+R), (X0+k, Y0+k), (X0+R, Y0)); edge('arc', (X1-R, Y0), (X1-k, Y0+k), (X1, Y0+R))
edge('arc', (X1, Y1-R), (X1-k, Y1-k), (X1-R, Y1)); edge('arc', (X0+R, Y1), (X0+k, Y1-k), (X0, Y1-R))

# geometry helpers ----------------------------------------------------------------------------------------------------
def crt(f):
    L = pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd; xs, ys = [], []
    for g in f.GraphicalItems():
        if g.GetLayer() == L:
            r = g.GetBoundingBox(); xs += [r.GetLeft(), r.GetRight()]; ys += [r.GetTop(), r.GetBottom()]
    if not xs:
        for p in f.Pads():
            r = p.GetBoundingBox(); xs += [r.GetLeft() - mm(0.25), r.GetRight() + mm(0.25)]; ys += [r.GetTop() - mm(0.25), r.GetBottom() + mm(0.25)]
    return (min(xs)/1e6, min(ys)/1e6, max(xs)/1e6, max(ys)/1e6)
def is_tht(f): return any(p.GetDrillSizeX() > 0 for p in f.Pads())
def place_bb(ref, rot=None, left=None, top=None, right=None, bottom=None, dy=None):
    f = FP[ref]
    if rot is not None: f.SetOrientationDegrees(rot)
    l, t, r, bt = crt(f); x, y = pos(f)
    if left is not None: x += left - l
    if right is not None: x += right - r
    if top is not None: y += top - t
    if bottom is not None: y += bottom - bt
    if dy is not None: y += dy
    f.SetPosition(V(x, y))

# 2. RV1106 cluster ---------------------------------------------------------------------------------------------------
ux, uy = pos(FP['U100'])
CL = [f for f in b.GetFootprints() if f.GetReference() == 'R19' or (f.GetSheetname() in ('SoC', 'SoC Power') and
      abs(pos(f)[0] - ux) <= 12 and abs(pos(f)[1] - uy) <= 12 and f.GetReference() != 'R511')]
bbs = [crt(f) for f in CL]
cbb = (min(q[0] for q in bbs), min(q[1] for q in bbs), max(q[2] for q in bbs), max(q[3] for q in bbs))
if LAY['cluster'] == 'v1': cdx = (X1 - 0.6) - cbb[2]; cdy = (Y0 + float(os.environ.get('T32_CL_TOP', 23.7))) - cbb[1]
else: cdx = (X1 - LAY['cluster_left_from_right'] if 'cluster_left_from_right' in LAY else X0 + LAY['cluster']['left']) - cbb[0]; cdy = Y0 + LAY['cluster']['top'] - cbb[1]
for f in CL: x, y = pos(f); f.SetPosition(V(x + cdx, y + cdy))
report['cluster'] = {'parts': len(CL), 'shift': [round(cdx, 2), round(cdy, 2)],
                     'bbox': [round(cbb[0]+cdx, 2), round(cbb[1]+cdy, 2), round(cbb[2]+cdx, 2), round(cbb[3]+cdy, 2)]}
for z in b.Zones():
    if z.GetIsRuleArea():
        if 'Y50' in z.GetZoneName(): z.Move(V(cdx, cdy))
        continue
    if z.GetNetname() == 'VDD_0V9': z.Move(V(cdx, cdy)); continue
    o = z.Outline(); o.RemoveAllContours(); o.NewOutline()
    for px, py in ((X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)): o.Append(mm(px), mm(py))

# 3. anchors ----------------------------------------------------------------------------------------------------------
EDGE_DY = (Y0 + H) - OLD_BOTTOM
ANCH = LAY['anchors'](X0, Y0, X1, Y1, EDGE_DY)
for ref, kw in ANCH: place_bb(ref, **kw)
FIXED = set(f.GetReference() for f in CL) | set(r for r, _ in ANCH)

# 4/5 packer ----------------------------------------------------------------------------------------------------------
RES, GAP, EDGE_IN = 0.05, 0.10, 0.30
NX, NY = int(round(W/RES)), int(round(H/RES))
occ = {'F': np.zeros((NY, NX), np.uint8), 'B': np.zeros((NY, NX), np.uint8)}
def idx(x0, y0, x1, y1):
    return (max(0, int(math.floor((x0 - X0)/RES))), max(0, int(math.floor((y0 - Y0)/RES))),
            min(NX, int(math.ceil((x1 - X0)/RES))), min(NY, int(math.ceil((y1 - Y0)/RES))))
def mark(side, box):
    i0, j0, i1, j1 = idx(*box)
    if i1 > i0 and j1 > j0: occ[side][j0:j1, i0:i1] = 1
SAT = {}
def sat(side):
    S = np.zeros((NY + 1, NX + 1), np.int32); S[1:, 1:] = occ[side].cumsum(0).cumsum(1); SAT[side] = S
def side_of(f): return 'B' if f.IsFlipped() else 'F'
def mark_fp(f):
    mark(side_of(f), crt(f))
    if is_tht(f):
        other = 'F' if f.IsFlipped() else 'B'
        if f.GetReference().startswith('MH'): mark(other, crt(f))
        else:
            for p in f.Pads():
                if p.GetDrillSizeX() > 0:
                    r = p.GetBoundingBox(); mark(other, (r.GetLeft()/1e6 - 0.3, r.GetTop()/1e6 - 0.3, r.GetRight()/1e6 + 0.3, r.GetBottom()/1e6 + 0.3))
for z in b.Zones():
    if z.GetIsRuleArea() and z.IsOnLayer(pcbnew.B_Cu):
        bb = z.GetBoundingBox(); mark('B', (bb.GetLeft()/1e6, bb.GetTop()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6))

NETPADS = {}
for f in b.GetFootprints():
    for p in f.Pads(): NETPADS.setdefault(p.GetNetname(), 0); NETPADS[p.GetNetname()] += 1
def wnet(n):
    if not n or n == 'GND' or n.startswith('unconnected'): return 0.0
    return 0.25 if NETPADS.get(n, 0) > 15 else 1.0
PLACED = {}        # net -> list of (x, y)
def register(f):
    for p in f.Pads():
        n = p.GetNetname()
        if wnet(n) > 0: PLACED.setdefault(n, []).append((p.GetPosition().x/1e6, p.GetPosition().y/1e6))
for ref in FIXED: mark_fp(FP[ref]); register(FP[ref])

def variants(f):
    out = []
    for rot in (0, 90, 180, 270):
        f.SetOrientationDegrees(rot); x, y = pos(f); l, t, r, bt = crt(f)
        pads = [(p.GetNetname(), p.GetPosition().x/1e6 - x, p.GetPosition().y/1e6 - y) for p in f.Pads() if wnet(p.GetNetname()) > 0]
        out.append((rot, (l - x, t - y, r - x, bt - y), pads))
    return out
def try_place(f, rects, anchor, lam, step=0.25):
    side = side_of(f); S = SAT[side]; best = None
    for rot, (cx0, cy0, cx1, cy1), pads in variants(f):
        ccx, ccy = (cx0 + cx1)/2, (cy0 + cy1)/2
        cand = []
        for (rx0, ry0, rx1, ry1) in rects:
            gx = np.arange(rx0, rx1 + 1e-9, step); gy = np.arange(ry0, ry1 + 1e-9, step)
            if len(gx) and len(gy): GX, GY = np.meshgrid(gx, gy); cand.append(np.stack([GX.ravel(), GY.ravel()], 1))
        if not cand: continue
        C = np.unique(np.concatenate(cand), axis=0); ox = C[:, 0] - ccx; oy = C[:, 1] - ccy
        x0 = ox + cx0 - GAP; y0 = oy + cy0 - GAP; x1 = ox + cx1 + GAP; y1 = oy + cy1 + GAP
        ok = (ox + cx0 >= X0 + EDGE_IN) & (oy + cy0 >= Y0 + EDGE_IN) & (ox + cx1 <= X1 - EDGE_IN) & (oy + cy1 <= Y1 - EDGE_IN)
        if not ok.any(): continue
        ox, oy, x0, y0, x1, y1 = ox[ok], oy[ok], x0[ok], y0[ok], x1[ok], y1[ok]
        i0 = np.clip(np.floor((x0 - X0)/RES).astype(int), 0, NX); i1 = np.clip(np.ceil((x1 - X0)/RES).astype(int), 0, NX)
        j0 = np.clip(np.floor((y0 - Y0)/RES).astype(int), 0, NY); j1 = np.clip(np.ceil((y1 - Y0)/RES).astype(int), 0, NY)
        free = (S[j1, i1] - S[j0, i1] - S[j1, i0] + S[j0, i0]) == 0
        if not free.any(): continue
        ox, oy = ox[free], oy[free]
        cost = lam*np.hypot(ox + ccx - anchor[0], oy + ccy - anchor[1])
        for n, dx, dy in pads:
            T = PLACED.get(n)
            if not T: continue
            T = np.asarray(T); px = (ox + dx)[:, None]; py = (oy + dy)[:, None]
            cost = cost + wnet(n)*np.sqrt((px - T[None, :, 0])**2 + (py - T[None, :, 1])**2).min(1)
        k_ = int(np.argmin(cost))
        if best is None or cost[k_] < best[0]: best = (float(cost[k_]), rot, float(ox[k_]), float(oy[k_]))
    if best is None: return False
    f.SetOrientationDegrees(best[1]); f.SetPosition(V(best[2], best[3])); mark_fp(f); register(f); sat(side_of(f))
    return True
def area(f): l, t, r, bt = crt(f); return (r - l)*(bt - t)
def order_place(parts, rects, anchor, lam, label):
    todo = list(parts)
    while todo:
        def score(f): return (sum(wnet(p.GetNetname()) for p in f.Pads() if PLACED.get(p.GetNetname())), area(f))
        f = max(todo, key=score); todo.remove(f)
        grown = [(x0 - 6, y0 - 6, x1 + 6, y1 + 6) for x0, y0, x1, y1 in rects]
        if try_place(f, rects, anchor, lam): report['placed_top' if not f.IsFlipped() else 'placed_bottom'] += 1
        elif try_place(f, grown, anchor, lam) or try_place(f, [R_(0.6, 0.6, W - 0.6, H - 0.6)], anchor, lam):
            report['placed_top' if not f.IsFlipped() else 'placed_bottom'] += 1; report.setdefault('spilled', []).append(f.GetReference())
        else:
            report['failed'].append((f.GetReference(), label)); f.SetPosition(V(X1 + 20, Y0 + 3*len(report['failed'])))

SMALL = re.compile(r'(0402|0603)')
TOPCAPS = set('C80 C60 C50 C70 C83 C73 C63 C53 C33 C26 C27 C25 C100 C110 C102 C103 C112 C113 '
              'C11 C12 C6 C10 C14 C15 C16 C17 C18 C19 C20 C21 C1 C3 C200 C201 C202 C203 C204'.split())
def bottomable(f):
    r = f.GetReference()
    if r == 'J501': return True          # T37: debug UART test pads live on the bottom
    if f.GetSheetname() in LAY.get('bottom_sheets', ()) and r not in LAY.get('keep_top', ()) and r not in FIXED: return True   # trial C
    return (r[0] in 'RC' and not r.startswith('CN') and SMALL.search(f.GetFPIDAsString()) and f.GetSheetname() != 'Antenna'
            and r not in TOPCAPS and r not in FIXED)
BOT = [f for f in b.GetFootprints() if bottomable(f)]
for f in BOT:
    if not f.IsFlipped(): f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
TOP = [f for f in b.GetFootprints() if f.GetReference() not in FIXED and not bottomable(f)]
for f in TOP:
    if f.IsFlipped(): f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
sat('F'); sat('B')
def R_(fx0, fy0, fx1, fy1): return (X0 + fx0, Y0 + fy0, X0 + fx1, Y0 + fy1)
def A_(fx, fy): return (X0 + fx, Y0 + fy)
GROUPS = [(sh, [R_(*r) for r in rects], A_(*a)) for sh, rects, a in (LAY['groups'](W, H) if callable(LAY['groups']) else LAY['groups'])]   # sheet, region rects, anchor
seen = set()
# RF chain (owner, 2026-11-23: "HaLow RF filter looks not tidy"): series parts in one straight line from the RF pin, each
# shunt cap at its node on the same side with its ground pad away from the line, the U.FL at the end with its signal
# pad facing the chain. Placed before the packer so the space is reserved.
def place_chain(spec):
    src = [p for p in FP[spec['src'][0]].Pads() if p.GetNumber() == spec['src'][1]][0]
    o = spec.get('origin', (0.0, 0.0)); p0 = (src.GetPosition().x/1e6 + o[0], src.GetPosition().y/1e6 + o[1]); d = spec['dir']
    n = (-d[1]*spec['side'], d[0]*spec['side'])   # origin (above): offset from the pin to the corner where the line turns
    def put(ref, centre, along, sig_near):
        f = FP[ref]; best = None
        for rot in (0, 90, 180, 270):
            f.SetOrientationDegrees(rot); f.SetPosition(V(*centre))
            pads = [q for q in f.Pads() if q.GetNumber()]
            sig = [q for q in pads if q.GetNetname() != 'GND']
            ax = [abs((q.GetPosition().x/1e6 - centre[0])*along[0] + (q.GetPosition().y/1e6 - centre[1])*along[1]) for q in pads]
            if max(ax) < 0.2: continue                                  # pads must lie along `along`
            dist = min(math.dist((q.GetPosition().x/1e6, q.GetPosition().y/1e6), sig_near) for q in sig)
            if best is None or dist < best[0]: best = (dist, rot)
        f.SetOrientationDegrees(best[1]); f.SetPosition(V(*centre)); return f
    x = spec['start']; placed = []
    for k, ref in enumerate(spec['series']):
        c = (p0[0] + d[0]*x, p0[1] + d[1]*x); placed.append(put(ref, c, d, p0 if k == 0 else (c[0] - d[0], c[1] - d[1])))
        node = (p0[0] + d[0]*(x + spec['pitch']/2), p0[1] + d[1]*(x + spec['pitch']/2))
        if k < len(spec['shunts']):
            off = spec['shunt_off']; sc = (node[0] + n[0]*off, node[1] + n[1]*off)
            placed.append(put(spec['shunts'][k], sc, n, node))
        x += spec['pitch']
    # connector: signal pad on the line just past the last node, body beyond it
    f = FP[spec['conn']]; tgt = (p0[0] + d[0]*(x - spec['pitch']/2 + spec['conn_gap']), p0[1] + d[1]*(x - spec['pitch']/2 + spec['conn_gap']))
    for rot in (0, 90, 180, 270):
        f.SetOrientationDegrees(rot); sig = [q for q in f.Pads() if q.GetNetname() != 'GND'][0]
        v = ((sig.GetPosition().x - f.GetPosition().x)/1e6, (sig.GetPosition().y - f.GetPosition().y)/1e6)
        body = spec.get('conn_body', d)                  # direction from the signal pad to the connector body (default: beyond the line)
        perp = (-body[1], body[0])
        if v[0]*body[0] + v[1]*body[1] < -0.5 and abs(v[0]*perp[0] + v[1]*perp[1]) < 0.1: break
    sig = [q for q in f.Pads() if q.GetNetname() != 'GND'][0]
    f.SetPosition(f.GetPosition() + V(tgt[0] - sig.GetPosition().x/1e6, tgt[1] - sig.GetPosition().y/1e6)); placed.append(f)
    for f in placed:
        if f.IsFlipped(): f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        mark_fp(f); register(f); seen.add(f.GetReference())
    sat('F'); report['rf_chain'] = [(f.GetReference(), f.GetOrientationDegrees()) for f in placed]
if LAY.get('rf_chain'): place_chain(LAY['rf_chain'])
# T35: the USB ESD chip U1 goes first, right behind J1's data pins (USBLC6 at the connector)
_j1 = [p for p in FP['J1'].Pads() if 'D+' in p.GetNetname() or 'D-' in p.GetNetname()]
_px = [p.GetPosition().x/1e6 for p in _j1]; _py = min(p.GetPosition().y/1e6 for p in _j1)
order_place([FP['U1']], [(min(_px) - 3, _py - 7, max(_px) + 3, _py - 1.5)], ((min(_px) + max(_px))/2, _py - 3), 1.0, 'U1 at J1')
seen.add('U1')
for sheet, rects, anchor in GROUPS:
    parts = [f for f in TOP if f.GetSheetname() == sheet and f.GetReference() not in seen]; seen |= {f.GetReference() for f in parts}
    order_place(parts, rects, anchor, 0.4, sheet)
rest = [f for f in TOP if f.GetReference() not in seen]
order_place(rest, [R_(0.6, 0.6, W - 0.6, H - 0.6)], A_(W/2, H/2), 0.05, 'other-top')
report['other_top'] = [f.GetReference() for f in rest]
# bottom passives: anywhere on the board, near what they connect to
def bot_window(f):
    pts = [q for p in f.Pads() for q in PLACED.get(p.GetNetname(), [])] if any(PLACED.get(p.GetNetname()) for p in f.Pads()) else []
    if not pts: return [R_(0.6, 0.6, W - 0.6, H - 0.6)], A_(W/2, H/2)
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]; cx, cy = sum(xs)/len(xs), sum(ys)/len(ys)
    return [(max(X0 + 0.6, min(xs) - 4), max(Y0 + 0.6, min(ys) - 4), min(X1 - 0.6, max(xs) + 4), min(Y1 - 0.6, max(ys) + 4))], (cx, cy)
# trial C: the power sheets' bigger parts first, inside their underside regions (the small passives follow below)
if LAY.get('bottom_groups'):
    for sheet, rects, anchor in LAY['bottom_groups'](W, H):
        big = [f for f in BOT if f.GetSheetname() == sheet and not (f.GetReference()[0] in 'RC' and SMALL.search(f.GetFPIDAsString()))]
        order_place(big, [R_(*r) for r in rects], A_(*anchor), 0.4, 'bottom ' + sheet)
        for f in big: BOT.remove(f)
todo = list(BOT)
while todo:
    f = max(todo, key=lambda f: (sum(wnet(p.GetNetname()) for p in f.Pads() if PLACED.get(p.GetNetname())), area(f))); todo.remove(f)
    rects, anchor = bot_window(f)
    if try_place(f, rects, anchor, 0.05): report['placed_bottom'] += 1
    elif try_place(f, [R_(0.6, 0.6, W - 0.6, H - 0.6)], anchor, 0.05): report['placed_bottom'] += 1
    else: report['failed'].append((f.GetReference(), 'bottom')); f.SetPosition(V(X1 + 30, Y0 + 3*len(report['failed'])))
report['top_parts'] = sum(1 for f in b.GetFootprints() if not f.IsFlipped())
report['bottom_parts'] = sum(1 for f in b.GetFootprints() if f.IsFlipped())
report['top_fill_pct'] = round(100*occ['F'].mean(), 1); report['bottom_fill_pct'] = round(100*occ['B'].mean(), 1)
b.Save(BOARD)
print(json.dumps(report))
