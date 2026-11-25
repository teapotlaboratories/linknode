"""T41 Block 2: place the power section by the TI layout guidance (owner-approved floorplan B6 zones kept).
Usage: python3 blk2_place.py <board.kicad_pcb>   (edits the file in place; back it up first)

Method:
 1. Every converter is a *tile* drawn by hand from the TI layout example in its datasheet (poses relative to the IC,
    table LAYOUT below; every tile is checked for courtyard overlaps on its own):
    - TLV62569: SLVSDG1C §10.1 / Fig 20 (p.13). The six bucks share one tile (radio rails: a second Cout).
    - TPS61089: SLVSD38C §11.1 / Fig 11-1 (p.22): 100 nF Cout across VOUT/GND first (boost hot loop), 22 uF row, L, Cin.
    - BQ25798:  SLUSDV2C §8.4.1 / Fig 8-21 (p.139-140), the numbered priority list; BTST caps on the bottom (item 2).
 2. Tiles go to fixed grid positions and rotations (PLAN), searched within +-4 mm only if a fixed part is in the way,
    0.3 mm from everything else. TLV tiles at 180 deg keep every buck inductor >= 5.5 mm from the HaLow module (B6).
    Fixed: all non-power parts, the edge connectors J1-J4, SW1, U1, R1, R2, the holes.
 3. The input power path (TI Fig 10-1: J2 -> Q11 -> VDCIN -> Q3/Q4, J1 -> Q1/Q2, both into VBUS) is placed next, by
    hand-chosen anchors plus net distance. The other power-sheet parts (hold-off, battery protection, enables, test
    points) and the HaLow / ESP32-C5 bottom passives parked in the power column are packed by net distance (T32 rule),
    small R/C on the bottom.
Prints a JSON report."""
import sys, os, re, math, json, traceback
import numpy as np, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
BOARD = sys.argv[1]
b = pcbnew.LoadBoard(BOARD)
mm = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))
FP = {f.GetReference(): f for f in b.GetFootprints()}
def pos(f): return (f.GetPosition().x/1e6, f.GetPosition().y/1e6)
def ppos(p): return (p.GetPosition().x/1e6, p.GetPosition().y/1e6)
eb = b.GetBoardEdgesBoundingBox(); X0, Y0, X1, Y1 = eb.GetLeft()/1e6, eb.GetTop()/1e6, eb.GetRight()/1e6, eb.GetBottom()/1e6
RES = 0.05
report = {'tiles': {}, 'loose_failed': [], 'spilled': []}

def crt(f):
    L = pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd; xs, ys = [], []
    for g in f.GraphicalItems():
        if g.GetLayer() == L:
            r = g.GetBoundingBox(); xs += [r.GetLeft(), r.GetRight()]; ys += [r.GetTop(), r.GetBottom()]
    if not xs:
        for p in f.Pads():
            r = p.GetBoundingBox(); xs += [r.GetLeft() - mm(0.25), r.GetRight() + mm(0.25)]; ys += [r.GetTop() - mm(0.25), r.GetBottom() + mm(0.25)]
    return (min(xs)/1e6, min(ys)/1e6, max(xs)/1e6, max(ys)/1e6)
def side_of(f): return 'B' if f.IsFlipped() else 'F'
def set_side(f, s):
    if side_of(f) != s: f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
def is_tht(f): return any(p.GetDrillSizeX() > 0 for p in f.Pads())

class Raster:
    def __init__(s, x0, y0, x1, y1):
        s.x0, s.y0, s.x1, s.y1 = x0, y0, x1, y1; s.nx = int(round((x1 - x0)/RES)); s.ny = int(round((y1 - y0)/RES))
        s.occ = {k: np.zeros((s.ny, s.nx), np.uint8) for k in 'FB'}; s.S = {}; s.dirty = {'F', 'B'}
    def idx(s, x0, y0, x1, y1):
        return (max(0, int(math.floor((x0 - s.x0)/RES))), max(0, int(math.floor((y0 - s.y0)/RES))),
                min(s.nx, int(math.ceil((x1 - s.x0)/RES))), min(s.ny, int(math.ceil((y1 - s.y0)/RES))))
    def mark(s, side, box):
        i0, j0, i1, j1 = s.idx(*box)
        if i1 > i0 and j1 > j0: s.occ[side][j0:j1, i0:i1] = 1; s.dirty.add(side)
    def mark_fp(s, f, pad=0.0):
        l, t, r, bt = crt(f); s.mark(side_of(f), (l - pad, t - pad, r + pad, bt + pad))
        if is_tht(f):
            other = 'B' if side_of(f) == 'F' else 'F'
            if f.GetReference().startswith('MH'): s.mark(other, crt(f))
            for p in f.Pads():
                if p.GetDrillSizeX() > 0:
                    q = p.GetBoundingBox(); s.mark(other, (q.GetLeft()/1e6 - 0.3, q.GetTop()/1e6 - 0.3, q.GetRight()/1e6 + 0.3, q.GetBottom()/1e6 + 0.3))
    def sat(s, side):
        if side in s.dirty:
            S = np.zeros((s.ny + 1, s.nx + 1), np.int32); S[1:, 1:] = s.occ[side].cumsum(0).cumsum(1); s.S[side] = S; s.dirty.discard(side)
        return s.S[side]
    def free(s, side, x0, y0, x1, y1, edge=0.3):
        """vectorised: boxes given as arrays; True where the box is empty and inside the raster (minus edge)."""
        S = s.sat(side)
        ok = (x0 >= s.x0 + edge) & (y0 >= s.y0 + edge) & (x1 <= s.x1 - edge) & (y1 <= s.y1 - edge)
        i0 = np.clip(np.floor((x0 - s.x0)/RES).astype(int), 0, s.nx); i1 = np.clip(np.ceil((x1 - s.x0)/RES).astype(int), 0, s.nx)
        j0 = np.clip(np.floor((y0 - s.y0)/RES).astype(int), 0, s.ny); j1 = np.clip(np.ceil((y1 - s.y0)/RES).astype(int), 0, s.ny)
        return ok & ((S[j1, i1] - S[j0, i1] - S[j1, i0] + S[j0, i0]) == 0)

def best_pose(f, R, cx, cy, half, step, costfn, gap, rots=(0, 90, 180, 270)):
    """Try f at every grid point in [cx +- half] x [cy +- half] and every rotation; costfn(rot, pads_rel, ox, oy) -> cost array."""
    side = side_of(f); best = None
    g = np.arange(-half, half + 1e-9, step); GX, GY = np.meshgrid(cx + g, cy + g); GX = GX.ravel(); GY = GY.ravel()
    for rot in rots:
        f.SetOrientationDegrees(rot); x, y = pos(f); l, t, r, bt = crt(f)
        pads = [(p.GetNetname(), p.GetNumber(), ppos(p)[0] - x, ppos(p)[1] - y) for p in f.Pads()]
        ok = R.free(side, GX + l - x - gap, GY + t - y - gap, GX + r - x + gap, GY + bt - y + gap)
        if not ok.any(): continue
        ox, oy = GX[ok], GY[ok]; c = costfn(rot, pads, ox, oy); k = int(np.argmin(c))
        if best is None or c[k] < best[0]: best = (float(c[k]), rot, float(ox[k]), float(oy[k]))
    if best is None: return None
    f.SetOrientationDegrees(best[1]); f.SetPosition(V(best[2], best[3])); R.mark_fp(f)
    return best

# ---------------------------------------------------------------------------------------------------------------------
# 1. tiles: hand-drawn from the TI layout examples. Poses are (dx, dy, rot, side) relative to the IC centre, mm.
#    2-pad parts: rot 0 = pad 1 left, 90 = pad 1 down, 180 = pad 1 right, 270 = pad 1 up.
def netof(ref, num): return [p for p in FP[ref].Pads() if p.GetNumber() == num][0].GetNetname()
def TLV(ic, cin, L, couts, rtop, rbot, cff, en):
    """SLVSDG1C Fig 20: IC at 180 deg (VIN top-left, FB bottom-left, SW top-right, GND mid-right, EN bottom-right).
    Cin left of the IC with its + pad level with VIN; L above, pad 1 (SW) over the SW pin's side; Cout right of the IC
    under L pad 2 (VOUT), its GND pad beside the IC GND pin. FB divider + Cff on the bottom under the VIN/FB side,
    away from SW; EN parts on the bottom under the EN side."""
    t = {ic: (0, 0, 180, 'F'), cin: (-2.98, -0.17, 270, 'F'), L: (1.9, -3.25, 0, 'F')}
    for i, c in enumerate(couts): t[c] = (2.98 + 1.66*i, -0.2, 270, 'F')
    t[cff] = (-1.6, -0.9, 0, 'B'); t[rtop] = (-1.6, 0.25, 0, 'B'); t[rbot] = (-1.6, 1.4, 0, 'B')
    for i, r_ in enumerate(en): t[r_] = (1.6, 0.25 + 1.15*i, 0, 'B')
    return t
LAYOUT = {
 'U5': TLV('U5', 'C50', 'L5', ['C53'], 'R51', 'R52', 'C52', ['R50', 'C51']),
 'U6': TLV('U6', 'C60', 'L6', ['C63'], 'R61', 'R62', 'C62', ['R60', 'C61']),
 'U7': TLV('U7', 'C70', 'L7', ['C73'], 'R71', 'R72', 'C72', ['R70', 'C71']),
 'U8': TLV('U8', 'C80', 'L8', ['C83'], 'R81', 'R82', 'C82', ['R80', 'C81']),
 'U10': TLV('U10', 'C100', 'L10', ['C102', 'C103'], 'R101', 'R102', 'C101', ['R100']),
 'U11': TLV('U11', 'C110', 'L11', ['C112', 'C113'], 'R111', 'R112', 'C111', ['R110']),
}
# SLVSD38C Fig 11-1: IC at 90 deg (SW left, VOUT/GND right, VIN/BOOT/ILIM/EN top, FSW/VCC/FB/COMP bottom).
# 100 nF C33 straddles VOUT/GND right at the pins (the boost hot loop), the 22 uF row continues to the right.
# L left with pad 2 (SW) level with the SW pin, pad 1 (VIN) down; Cin bulk C24 under L (VIN pad at L, GND to the pour),
# 100 nF C25 over the VIN pin, BOOT cap beside it to the SW side, VCC cap under the VCC pin. Small parts on the bottom.
LAYOUT['U4'] = {'U4': (0, 0, 90, 'F'), 'C33': (2.11, 0, 270, 'F'), 'C32': (3.75, 0, 270, 'F'), 'C30': (5.91, 0, 270, 'F'),
                'C31': (8.07, 0, 270, 'F'), 'L2': (-3.9, 1.5, 90, 'F'), 'C24': (-3.9, 4.98, 0, 'F'), 'C25': (0.23, -2.36, 0, 'F'),
                'C26': (-1.79, -2.36, 0, 'F'), 'C27': (-0.25, 3.38, 270, 'F'),
                'R13': (-1.6, 1.4, 0, 'B'), 'R15': (0.6, 1.4, 0, 'B'), 'R16': (0.6, 2.55, 0, 'B'), 'R17': (2.7, 1.4, 0, 'B'),
                'C29': (2.7, 2.55, 0, 'B'), 'C28': (2.7, 3.7, 0, 'B'), 'R14': (0.6, -1.4, 0, 'B'), 'R18': (2.7, -1.4, 0, 'B')}
# SLUSDV2C Fig 8-21: IC at 0 deg (PMID SW1 GND SW2 SYS along the top edge, VBUS/BTST1/REGN left, BAT/BTST2/BATP right).
# 1. 100 nF PMID (C10) and SYS (C19) straddle PMID-GND and GND-SYS at the top edge; 10 uF in parallel beside L.
# 2. L above (pad 1 = SW1 left, pad 2 = SW2 right), reached by vias under the IC; BTST caps on the bottom under the IC.
# 3. REGN cap at the REGN pin. 4. 100 nF VBUS at the VBUS pins, bulk further left. 5. BAT caps at the BAT pins.
# Two of the five SYS 10 uF (C14, C15) are system bulk and go with the loose parts.
LAYOUT['U2'] = {'U2': (0, 0, 0, 'F'), 'C10': (-1.0, -3.06, 0, 'F'), 'C19': (1.0, -3.06, 180, 'F'), 'L1': (0, -6.02, 0, 'F'),
                'C9': (-3.48, -4.35, 90, 'F'), 'C8': (-5.64, -4.35, 90, 'F'), 'C7': (-7.8, -4.35, 90, 'F'),
                'C18': (3.23, -4.45, 90, 'F'), 'C17': (4.89, -4.45, 90, 'F'), 'C16': (6.55, -4.45, 90, 'F'),
                'C6': (-3.11, -1.0, 270, 'F'), 'C5': (-5.29, -0.5, 270, 'F'), 'C4': (-7.45, -0.5, 270, 'F'),
                'C13': (-3.38, 1.59, 270, 'F'), 'C20': (3.38, -1.0, 270, 'F'), 'C21': (5.04, -1.0, 270, 'F'),
                'C11': (-1.3, -0.6, 0, 'B'), 'C12': (1.3, -0.6, 0, 'B'), 'R4': (3.4, 0.9, 0, 'B')}
SWNETS = {netof(k, '3') for k in ('U5', 'U6', 'U7', 'U8', 'U10', 'U11')} | {netof('U4', '11'), netof('U2', '28'), netof('U2', '26')}
TILE_PARTS = set(r for t in LAYOUT.values() for r in t)
FIXED_POWER = {'J1', 'J2', 'J3', 'J4', 'SW1', 'U1', 'R1', 'R2'}
POWER_SHEETS = {'Power', 'Radio Power', 'USB and Charger', 'Battery', 'Hold-off'}
GUESTS = [f for f in b.GetFootprints() if f.GetSheetname() in ('HaLow', 'ESP32-C5') and f.IsFlipped() and pos(f)[0] < 131.5]
MOVABLE = [f for f in b.GetFootprints() if (f.GetSheetname() in POWER_SHEETS and f.GetReference() not in FIXED_POWER
           and f.GetReference() != 'R19') or f in GUESTS]
MOV = set(f.GetReference() for f in MOVABLE)
report['movable'] = len(MOVABLE); report['guests'] = sorted(f.GetReference() for f in GUESTS)

def apply_tile(layout, ox, oy, rot):
    """Put the tile parts at their relative poses, rotate the whole tile by rot about the IC, move to (ox, oy)."""
    for ref, (dx, dy, r, s) in layout.items():
        f = FP[ref]; set_side(f, s); f.SetOrientationDegrees(r); f.SetPosition(V(dx, dy))
        if rot: f.Rotate(V(0, 0), pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
        f.Move(V(ox, oy))
# check every tile on its own: no courtyard overlap inside it (0.1 mm gap)
for k, lay in LAYOUT.items():
    apply_tile(lay, 0, 0, 0); R = Raster(-25, -25, 25, 25); bad = []
    for ref in lay:
        f = FP[ref]; l, t, r, bt = crt(f)
        if not R.free(side_of(f), np.array([l - 0.05]), np.array([t - 0.05]), np.array([r + 0.05]), np.array([bt + 0.05]))[0]: bad.append(ref)
        R.mark_fp(f)
    report['tiles'][k] = {'overlap': bad}

# 2. board raster with everything fixed ------------------------------------------------------------------------------
BR = Raster(X0, Y0, X1, Y1)
for f in MOVABLE: f.SetPosition(V(X1 + 30, Y0))           # park
for f in b.GetFootprints():
    if f.GetReference() not in MOV: BR.mark_fp(f)
for z in b.Zones():
    if z.GetIsRuleArea() and z.IsOnLayer(pcbnew.B_Cu):
        q = z.GetBoundingBox(); BR.mark('B', (q.GetLeft()/1e6, q.GetTop()/1e6, q.GetRight()/1e6, q.GetBottom()/1e6))

def tile_rects(layout, rot):
    apply_tile(layout, 0, 0, rot); rs = {'F': [], 'B': []}
    for ref in layout: rs[side_of(FP[ref])].append(crt(FP[ref]))
    return rs
# Tile plan (board mm, IC centre, tile rotation), floorplan B6 power column:
#  radio rails side by side along the top edge (HaLow rail U11 nearest the HaLow module);
#  SoC rails in a 2 x 2 grid, all at the same rotation (U5 VDD_0V9 and U6 VCC_DDR in the column nearer the RV1106); the boost under them; the charger under the boost, between the DC and USB inputs.
#  Grid pitch = tile size + 0.3 mm. The search only moves a tile (same rotation) if a fixed part is in the way.
PLAN = {'U11': (124.9, 102.85, 180), 'U10': (115.47, 102.85, 180),
        'U6': (124.9, 109.5, 180), 'U7': (117.0, 109.5, 180), 'U5': (124.9, 116.15, 180), 'U8': (117.0, 116.15, 180),
        'U4': (115.2, 124.0, 0), 'U2': (124.0, 139.0, 0)}
# Tiles at 180 deg put each TLV62569 inductor on the left of its IC, so every buck inductor ends at x <= 125.0, i.e.
# >= 5.5 mm from the HaLow module (U701 left courtyard edge x = 130.5), as in the approved B6 floorplan (5.6 mm).
TGAP = float(os.environ.get('BLK2_TGAP', 0.3))
for k in ('U2', 'U4', 'U5', 'U6', 'U8', 'U7', 'U11', 'U10'):
    tx, ty, prot = PLAN[k]; best = None
    gx = np.arange(tx - 4, tx + 4 + 1e-9, 0.05); gy = np.arange(ty - 4, ty + 4 + 1e-9, 0.05); GX, GY = np.meshgrid(gx, gy); GX = GX.ravel(); GY = GY.ravel()
    for rot in (prot,):
        rs = tile_rects(LAYOUT[k], rot); ok = np.ones(GX.shape, bool)
        for s in 'FB':
            for (l, t, r, bt) in rs[s]: ok &= BR.free(s, GX + l - TGAP, GY + t - TGAP, GX + r + TGAP, GY + bt + TGAP)
        if not ok.any(): continue
        c = np.hypot(GX[ok] - tx, GY[ok] - ty); i = int(np.argmin(c))
        if best is None or c[i] < best[0]: best = (float(c[i]), rot, float(GX[ok][i]), float(GY[ok][i]))
    assert best, ('no room for tile', k)
    apply_tile(LAYOUT[k], best[2], best[3], best[1])
    for ref in LAYOUT[k]: BR.mark_fp(FP[ref])
    report['tiles'][k].update(at=[round(best[2], 2), round(best[3], 2)], rot=best[1], pull=round(best[0], 2), parts=len(LAYOUT[k]))

# 3. loose parts: net-distance packer (T32 rule) ---------------------------------------------------------------------
NETPADS = {}
for f in b.GetFootprints():
    for p in f.Pads(): NETPADS[p.GetNetname()] = NETPADS.get(p.GetNetname(), 0) + 1
def wnet(n):
    if not n or n == 'GND' or n.startswith('unconnected'): return 0.0
    return 0.25 if NETPADS.get(n, 0) > 15 else 1.0
PLACED = {}
LOOSE = [f for f in MOVABLE if f.GetReference() not in TILE_PARTS]
for f in b.GetFootprints():
    if f not in LOOSE:
        for p in f.Pads():
            if wnet(p.GetNetname()) > 0: PLACED.setdefault(p.GetNetname(), []).append(ppos(p))
SMALL = re.compile(r'(0402|0603)')
TOPKEEP = {'C1', 'C3', 'C2', 'C121', 'D2'}
for f in LOOSE:
    r = f.GetReference()
    bottom = (r[0] in 'RC' and SMALL.search(f.GetFPIDAsString()) and r not in TOPKEEP) or f in GUESTS
    set_side(f, 'B' if bottom else 'F')
LZONE = {'Battery': (100, 115, 118, 137), 'Hold-off': (100, 128, 118, 153), 'USB and Charger': (104, 128, 137, 153),
         'Power': (104, 113, 131, 135), 'Radio Power': (104, 100, 131, 117)}
def loose_cost(f, R):
    def cost(rot, pads, ox, oy):
        c = np.zeros(ox.shape)
        for n, _, dx, dy in pads:
            T = PLACED.get(n)
            if not T or wnet(n) == 0: continue
            T = np.asarray(T); c = c + wnet(n)*np.sqrt(((ox + dx)[:, None] - T[None, :, 0])**2 + ((oy + dy)[:, None] - T[None, :, 1])**2).min(1)
        return c
    return cost
# Input power path, placed first and by hand-chosen anchors (TI SLUSDV2C Fig 10-1 order, signal flow J -> FETs -> VBUS):
#  DC: J2 pin 1 -> Q11 (reverse P-FET, D3 + R22 on its gate) -> VDCIN (D1 TVS, C3, R3 + C2 snubber, TP2) -> Q3/Q4 -> VBUS pins
#  USB: J1 VBUS -> Q1/Q2 (D4, R20) -> VBUS pins. Both pairs sit between their connector and the charger's VBUS side.
ANCH = [('Q11', (111.8, 147.0)), ('D3', (111.5, 143.6)), ('D1', (115.6, 147.4)), ('Q3', (115.2, 143.9)),
        ('Q4', (119.2, 144.3)), ('D5', (119.2, 147.8)), ('Q1', (126.6, 147.6)), ('Q2', (126.0, 144.2)),
        ('D4', (122.6, 148.0)), ('C3', (113.0, 149.6)), ('C2', (117.3, 150.3)), ('C1', (128.0, 150.3)),
        ('TP2', (108.6, 144.0)), ('TP1', (123.0, 151.0))]
for ref, (ax, ay) in ANCH:
    f = FP[ref]; base = loose_cost(f, BR)
    def cost(rot, pads, ox, oy, base=base, ax=ax, ay=ay): return base(rot, pads, ox, oy) + 1.5*np.hypot(ox - ax, oy - ay)
    r = best_pose(f, BR, ax, ay, 6, 0.1, cost, 0.1)
    if r is None: report['loose_failed'].append(ref); continue
    report.setdefault('anchored', {})[ref] = [round(pos(f)[0], 2), round(pos(f)[1], 2), f.GetOrientationDegrees()]
    for p in f.Pads():
        if wnet(p.GetNetname()) > 0: PLACED.setdefault(p.GetNetname(), []).append(ppos(p))
LOOSE = [f for f in LOOSE if f.GetReference() not in dict(ANCH)]
todo = list(LOOSE)
while todo:
    def score(f): return (sum(wnet(p.GetNetname()) for p in f.Pads() if PLACED.get(p.GetNetname())), (crt(f)[2] - crt(f)[0])*(crt(f)[3] - crt(f)[1]))
    f = max(todo, key=score); todo.remove(f)
    zone = LZONE.get(f.GetSheetname())
    if zone is None:   # guest: around the pads it connects to
        pts = [q for p in f.Pads() for q in PLACED.get(p.GetNetname(), []) if wnet(p.GetNetname()) > 0]
        cx, cy = (np.mean([q[0] for q in pts]), np.mean([q[1] for q in pts])) if pts else (115, 110); half = 12
    else:
        cx, cy = (zone[0] + zone[2])/2, (zone[1] + zone[3])/2; half = max(zone[2] - zone[0], zone[3] - zone[1])/2
    r = best_pose(f, BR, cx, cy, half, 0.25, loose_cost(f, BR), 0.1)
    if r is None:
        r = best_pose(f, BR, (X0 + X1)/2, (Y0 + Y1)/2, (X1 - X0)/2, 0.25, loose_cost(f, BR), 0.1)
        if r: report['spilled'].append(f.GetReference())
    if r is None: report['loose_failed'].append(f.GetReference()); continue
    for p in f.Pads():
        if wnet(p.GetNetname()) > 0: PLACED.setdefault(p.GetNetname(), []).append(ppos(p))
report['loose'] = len(LOOSE)
b.Save(BOARD)
print(json.dumps(report))
