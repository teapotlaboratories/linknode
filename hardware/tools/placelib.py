"""Shared placement helpers (from T41 Block 2): courtyard boxes, a two-sided occupancy raster, and a pose search
(best_pose). Import with: from placelib import *"""
import math, numpy as np, pcbnew
mm = pcbnew.FromMM
RES = 0.05
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))
def pos(f): return (f.GetPosition().x/1e6, f.GetPosition().y/1e6)
def ppos(p): return (p.GetPosition().x/1e6, p.GetPosition().y/1e6)
def crt(f):
    L = pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd; xs, ys = [], []
    for g in f.GraphicalItems():
        if g.GetLayer() == L:
            r = g.GetBoundingBox(); xs += [r.GetLeft(), r.GetRight()]; ys += [r.GetTop(), r.GetBottom()]
    if not xs:
        for p in f.Pads():
            r = p.GetBoundingBox(); xs += [r.GetLeft() - mm(0.25), r.GetRight() + mm(0.25)]; ys += [r.GetTop() - mm(0.25), r.GetBottom() + mm(0.25)]
    if not xs: return None   # graphics-only footprint (e.g. the silkscreen logo, T46): occupies nothing
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
        c = crt(f)
        if c is None: return
        l, t, r, bt = c; s.mark(side_of(f), (l - pad, t - pad, r + pad, bt + pad))
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


def place_moves(b, moves, gap=0.1, step=0.1, keepout=()):
    """Lift every part in moves = [(ref, side 'F'/'B', radius mm, [(target ref, target pin, weight)])], then place each in
    order at the pose with the least weighted pad-centre distance from its pad on the target pin's net to that pin
    (0.1 mm grid, 4 rotations, given side, within radius of the first target). Nothing else moves. keepout: extra
    (side, (x0, y0, x1, y1)) boxes to keep free. Returns a report."""
    FP = {f.GetReference(): f for f in b.GetFootprints()}
    eb = b.GetBoardEdgesBoundingBox(); X0, Y0, X1, Y1 = eb.GetLeft()/1e6, eb.GetTop()/1e6, eb.GetRight()/1e6, eb.GetBottom()/1e6
    MOV = {m[0] for m in moves}; rep = {'moved': {}, 'failed': []}
    R = Raster(X0, Y0, X1, Y1)
    for ref in MOV: FP[ref].SetPosition(V(X1 + 30, Y0))
    for f in b.GetFootprints():
        if f.GetReference() not in MOV: R.mark_fp(f)
    for z in b.Zones():
        if z.GetIsRuleArea():
            q = z.GetBoundingBox(); box = (q.GetLeft()/1e6, q.GetTop()/1e6, q.GetRight()/1e6, q.GetBottom()/1e6)
            if z.IsOnLayer(pcbnew.B_Cu): R.mark('B', box)
            if z.IsOnLayer(pcbnew.F_Cu): R.mark('F', box)
    for sd, box in keepout: R.mark(sd, box)
    def tpad(ref, num): return [p for p in FP[ref].Pads() if p.GetNumber() == num][0]
    for ref, side, rad, targets in moves:
        f = FP[ref]; set_side(f, side)
        T = [(tpad(t, n).GetNetname(), np.array(ppos(tpad(t, n))), w) for t, n, w in targets]
        def cost(rot, pads, ox, oy, T=T):
            c = np.zeros(ox.shape)
            for net, tp, w in T:
                mine = [(dx, dy) for n, _, dx, dy in pads if n == net]
                if mine: c = c + w*np.min([np.hypot(ox + dx - tp[0], oy + dy - tp[1]) for dx, dy in mine], axis=0)
            return c
        r = best_pose(f, R, T[0][1][0], T[0][1][1], rad, step, cost, gap)
        if r is None: rep['failed'].append(ref); continue
        rep['moved'][ref] = [round(pos(f)[0], 2), round(pos(f)[1], 2), f.GetOrientationDegrees(), side_of(f), round(r[0], 2)]
    return rep
