"""T47 Section 2 (2026-11-23): USB 2.0 D+/D- on the approved B6 placement, 45-degree bends only. Parts are not moved.
Usage: python3 t47_usb.py <board.kicad_pcb>
Rockchip HDG V1.1 3.3.3 p.48: 90 ohm differential, skew < 30 mil, <= 6 vias, > 20 mil to other signals.
1. SoC side: U100 pin 26 (D-) -> R509 pad 1, pin 27 (D+) -> R508 pad 1 on F.Cu (series R at the transmitter).
2. Main pair R509/R508 pad 2 -> U1 (USBLC6-2SC6) pins 6 (D-) / 4 (D+): coupled 0.155 / 0.130 mm (USB90 class,
   impedance.py; built at 0.130 so DRC's 0.127 mm minimum holds) on F.Cu over the In1 GND plane. The centreline is an
   A* with heading in its state: it may only go straight or turn 45 degrees per step, so both offset lines are 0/45/90 with
   45-degree bends only; 0.6 mm straight at both ends so the mitred offset lines never fold back at an end bend. Clearance: class + 0.35 mm to other-net tracks (HDG 20 mil). Short fan-in/fan-out at the pads.
3. Connector side U1 pins 1/3 -> J1 A6/B6 (D+), A7/B7 (D-): netroute F/B with a top keep-out under the USB-C shell, so
   the interleaved pads join through vias and a bottom link.
4. BC1.2 taps to U2 pins 6/7 (west side of the QFN): a via outside the IC (D+ north-west, D- south-west of its pin) with a
   45-degree top stub into the pin's outer end; netroute (F/B) from a pair bend to that via, with the U2 body kept out on
   top (the tap that has to cross the pair passes under it on B.Cu). Run bend45.py afterwards.
Prints the lengths of each line's signal path (pad to pad) and the skew."""
import sys, os, math, heapq, json, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geomlib import Geo, CU, mm, bbox
from geomlib import dist as gdist
import netroute as nr
BRD = sys.argv[1]
b = pcbnew.LoadBoard(BRD)
F = pcbnew.F_Cu
SDP, SDM, DP, DM = 'Net-(U100System-USB_DP)', 'Net-(U100System-USB_DM)', '/SoC/USB_DP', '/SoC/USB_DM'
JDP, JDM = 'Net-(J1-D+-PadA6)', 'Net-(J1-D--PadA7)'
ALL = {SDP, SDM, DP, DM, JDP, JDM}
W, GAP = 0.155, 0.130; OFF = (W + GAP)/2; FAT = OFF + W/2
EXTRA = 0.35                         # to other-net tracks: class 0.15 + 0.35 = 0.5 mm (HDG > 20 mil)
for t in list(b.GetTracks()):
    if t.GetNetname() in ALL: b.Remove(t)
eb = b.GetBoardEdgesBoundingBox()
g = Geo(b, (eb.GetLeft()/1e6 - 1, eb.GetTop()/1e6 - 1, eb.GetRight()/1e6 + 1, eb.GetBottom()/1e6 + 1))
def P(p): return (p.GetPosition().x/1e6, p.GetPosition().y/1e6)
def pad(ref, num): return [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
made = []
def seg_ok(a, c, net, ignore=()):
    return g.clear(('seg', a, c, W/2), F, net, ignore=lambda r: r[0] in ignore)
def lay(net, pts, check=True, ignore=()):
    for a, c in zip(pts, pts[1:]):
        if math.dist(a, c) < 1e-6: continue
        if check and not seg_ok(a, c, net, ignore): raise SystemExit('blocked %s %s -> %s' % (net, a, c))
    for a, c in zip(pts, pts[1:]):
        if math.dist(a, c) < 1e-6: continue
        made.append(g.add_track(a, c, W, F, net))
    return sum(math.dist(a, c) for a, c in zip(pts, pts[1:]))
L = {}
# ---- 1. SoC side
p26, p27 = P(pad('U100', '26')), P(pad('U100', '27'))
r9a, r8a = P(pad('R509', '1')), P(pad('R508', '1'))
L[SDM] = lay(SDM, [p26, (r9a[0], p26[1])])              # on the pin's centre line (pin pitch 0.35); ends inside R509 pad 1
dy = r8a[1] - p27[1]; xd = r8a[0] + 0.45                 # diagonal ends 0.45 mm east of the pad centre
L[SDP] = lay(SDP, [p27, (xd + dy, p27[1]), (xd, r8a[1]), r8a])
# ---- 2. main pair, centreline A* with heading
r9b, r8b = P(pad('R509', '2')), P(pad('R508', '2'))
u6, u4 = P(pad('U1', '6')), P(pad('U1', '4'))
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
GRID = 0.05
# pair start just west of R508 pad 2, heading south (D- west). D+ (R508, south pad) leaves it on a 45-degree diagonal
# straight onto its line; D- (R509, north pad) runs a diagonal then straight down beside it, so the two never cross.
RUN = 0.60                                              # straight lead-in/out at both ends, so the mitred offsets of
cx1 = (u6[0] + u4[0])/2                                 # the first/last bend never fold back on a short end segment
cxs = cx1 + round((r8b[0] - 0.52 - OFF - cx1)/GRID)*GRID   # start and goal on one 0.05 mm lattice: no snapping error
START = (cxs, r8b[1] + (r8b[0] - (cxs + OFF))); K0 = 2
GOAL1 = (cx1, START[1] + round((u6[1] - 2.20 - START[1])/GRID)*GRID); GOAL = (cx1, GOAL1[1] - RUN); K1 = 2  # end north of U1, heading south
WIN = (START[0] - 240*GRID, START[1] - 40*GRID, START[0] + 120*GRID, GOAL[1] + 1.5)   # origin on the START lattice
ig = lambda r: r[0] in ALL
cache = {}
def free(i, j):
    k = (i, j)
    if k not in cache:
        pt = (WIN[0] + i*GRID, WIN[1] + j*GRID)
        cache[k] = g.clear(('pt', pt, FAT + 0.02), F, DP, ignore=ig) and g.clear(('pt', pt, FAT + 0.02), F, DP, extra_tracks=EXTRA, ignore=lambda r: ig(r) or r[4] != 'track')
    return cache[k]
TURN = 0.6                                              # mm-equivalent cost of a 45-degree bend (fewer, longer runs)
def astar():
    si, sj = round((START[0] - WIN[0])/GRID), round((START[1] - WIN[1])/GRID)
    gi, gj = round((GOAL[0] - WIN[0])/GRID), round((GOAL[1] - WIN[1])/GRID)
    nx, ny = int((WIN[2] - WIN[0])/GRID) + 1, int((WIN[3] - WIN[1])/GRID) + 1
    s = (si, sj, K0); gs = {s: 0.0}; came = {s: None}; q = [(0.0, 0.0, s)]; it = 0
    while q:
        f, gg, n = heapq.heappop(q); it += 1
        if gg > gs.get(n, 1e18) + 1e-9: continue
        i, j, k = n
        if (i, j, k) == (gi, gj, K1):
            path = []
            while n is not None: path.append(n); n = came[n]
            return [(round(WIN[0] + i*GRID, 6), round(WIN[1] + j*GRID, 6)) for i, j, k in reversed(path)], it
        if it > 3000000: return None, it
        for dk in (-1, 0, 1):
            if dk and gg < RUN: continue                       # straight lead-out from the start
            k2 = (k + dk) % 8; d = DIRS[k2]; m = (i + d[0], j + d[1], k2)
            if not (0 <= m[0] < nx and 0 <= m[1] < ny) or not free(m[0], m[1]): continue
            ng = gg + GRID*math.hypot(*d) + (TURN if dk else 0.0)
            if ng < gs.get(m, 1e18) - 1e-9:
                gs[m] = ng; came[m] = n
                h = math.hypot(WIN[0] + m[0]*GRID - GOAL[0], WIN[1] + m[1]*GRID - GOAL[1])
                heapq.heappush(q, (ng + h, ng, m))
    return None, it
path, its = astar()
if not path: raise SystemExit('main pair: no centreline path (%d iterations)' % its)
def merge(pts):
    out = [pts[0]]
    for q in pts[1:]:
        if len(out) >= 2:
            a, c = out[-2], out[-1]
            if abs((c[0] - a[0])*(q[1] - c[1]) - (c[1] - a[1])*(q[0] - c[0])) < 1e-9: out[-1] = q; continue
        out.append(q)
    return out
cl = merge(path + [GOAL1])
def offset(poly, d):
    """offset a polyline by d to the right of its heading (screen coords, y down), mitred corners"""
    out = []
    def nrm(a, c):
        dx, dy = c[0] - a[0], c[1] - a[1]; l = math.hypot(dx, dy); return (-dy/l, dx/l)
    for k, p in enumerate(poly):
        if k == 0: n = nrm(poly[0], poly[1]); out.append((p[0] + n[0]*d, p[1] + n[1]*d)); continue
        if k == len(poly) - 1: n = nrm(poly[-2], poly[-1]); out.append((p[0] + n[0]*d, p[1] + n[1]*d)); continue
        n1, n2 = nrm(poly[k - 1], p), nrm(p, poly[k + 1]); m = (n1[0] + n2[0], n1[1] + n2[1]); lm = math.hypot(*m)
        m = (m[0]/lm, m[1]/lm); cv = m[0]*n1[0] + m[1]*n1[1]; out.append((p[0] + m[0]*d/cv, p[1] + m[1]*d/cv))
    return out
# n = (-dy, dx) is the right-hand side of the heading on screen (y down): heading west it is north (D-, R509), heading
# south it is west (D-, U1 pin 6). So D- is the +OFF line all the way.
lm_ = offset(cl, OFF); lp_ = offset(cl, -OFF)
def fan(p_pad, p_line, diag_first):
    """45-degree dogleg between a pad centre and a pair line end (diagonal at the pad end, or next to the pair)"""
    dx, dy = p_line[0] - p_pad[0], p_line[1] - p_pad[1]; m = min(abs(dx), abs(dy))
    dg = (math.copysign(m, dx), math.copysign(m, dy))
    if diag_first: return [p_pad, (p_pad[0] + dg[0], p_pad[1] + dg[1]), p_line]
    return [p_pad, (p_line[0] - dg[0], p_line[1] - dg[1]), p_line]
dm_pts = fan(r9b, lm_[0], True)[:-1] + lm_ + fan(u6, lm_[-1], False)[::-1][1:]
dp_pts = fan(r8b, lp_[0], True)[:-1] + lp_ + fan(u4, lp_[-1], False)[::-1][1:]
dm_pts, dp_pts = merge(dm_pts), merge(dp_pts)
def plen(pts): return sum(math.dist(a, c) for a, c in zip(pts, pts[1:]))
# skew: D- leaves R509, 1.05 mm north of R508, so it is longer. A 45-degree trapezoid bump on D+ (outward, away from D-)
# near that end adds 0.828 * amplitude (two diagonals of a*sqrt2 replace 2a of straight). Target: equal SoC-to-U1 paths,
# plus the mean connector-side difference of the two plug orientations (A7/A6 and B7/B6, measured below, CONN_BIAS).
# Shape (env, for comparing styles): USB_BUMP_N bumps (default: fewest that fit), USB_BUMP_FLAT top length (0.25),
# USB_BUMP_SPACE straight between bumps (0.3). Every bump is a trapezoid: a V would need a 90-degree apex.
CONN_BIAS = float(os.environ.get('USB_CONN_BIAS', '0'))
need = (L[SDM] + plen(dm_pts)) - (L[SDP] + plen(dp_pts)) + CONN_BIAS
def bumped(pts, need, partner):
    if need < 0.05: return pts, None
    NBS = [int(os.environ['USB_BUMP_N'])] if os.environ.get('USB_BUMP_N') else (1, 2, 3)
    for nb in NBS:
        a = need/nb/(2*math.sqrt(2) - 2); f = float(os.environ.get('USB_BUMP_FLAT', '0.25'))
        for k in range(len(pts) - 1):
            A, C = pts[k], pts[k + 1]; ln = math.dist(A, C)
            SP = float(os.environ.get('USB_BUMP_SPACE', '0.3'))         # straight between bumps
            if ln < nb*(2*a + f) + (nb - 1)*SP + 0.4: continue
            u = ((C[0] - A[0])/ln, (C[1] - A[1])/ln)
            for o in ((-u[1], u[0]), (u[1], -u[0])):
                # outward = away from the partner line
                mid = ((A[0] + C[0])/2 + o[0]*0.2, (A[1] + C[1])/2 + o[1]*0.2)
                if min(math.dist(mid, q) for q in partner) < min(math.dist(((A[0] + C[0])/2, (A[1] + C[1])/2), q) for q in partner): continue
                for s0 in [0.2 + 0.05*i for i in range(int((ln - nb*(2*a + f) - (nb - 1)*SP - 0.4)/0.05) + 1)]:
                    new = [A]; x = (A[0] + u[0]*s0, A[1] + u[1]*s0)
                    for _ in range(nb):
                        p1 = (x[0] + (u[0] + o[0])*a, x[1] + (u[1] + o[1])*a); p2 = (p1[0] + u[0]*f, p1[1] + u[1]*f)
                        p3 = (p2[0] + (u[0] - o[0])*a, p2[1] + (u[1] - o[1])*a)
                        new += [x, p1, p2, p3]; x = (p3[0] + u[0]*SP, p3[1] + u[1]*SP)
                    new.append(C)
                    if all(g.clear(('seg', q, r, W/2), F, DP, extra_tracks=EXTRA, ignore=lambda rr: rr[0] in ALL) for q, r in zip(new, new[1:])):
                        return pts[:k] + new + pts[k + 2:], (nb, round(a, 3), k)
    return pts, 'no room'
dense = lambda pts: [(pts[0][0] + (pts[-1][0] - pts[0][0])*t/20, pts[0][1] + (pts[-1][1] - pts[0][1])*t/20) for t in range(21)]
dm_dense = [q for a, c in zip(dm_pts, dm_pts[1:]) for q in dense([a, c])]
dp_pts, bump = bumped(dp_pts, need, dm_dense)
print('skew before tuning %.3f mm (D- longer), bump %s' % (need, bump), flush=True)
L[DM] = lay(DM, dm_pts, ignore=(DP,)); L[DP] = lay(DP, dp_pts, ignore=(DM,))
print('pair centreline: %d points, %d bends, %d A* steps' % (len(cl), len(cl) - 2, its), flush=True)
# ---- 3. connector side: netroute F/B. No top copper under the USB-C shell (J1 courtyard south of its pad row), so the
#      interleaved A6/A7/B6/B7 join through vias and a short bottom link.
def via_ok(x, y, net, r=0.225, drill=0.25, own_gap=0.09):
    """via legal: class clearance to other nets on every layer, hole spacing, and >= own_gap from any pad edge (own net
    included: no via in or touching an SMD pad, so no solder wicking)"""
    if not (g.hole_ok(x, y, drill) and all(g.clear(('pt', (x, y), r), Lc, net) for Lc in CU)): return False
    G = ('pt', (x, y), r)
    for Lc in (F, pcbnew.B_Cu):
        for rec in g.near(Lc, bbox(G), 0.6):
            if rec[4] == 'pad' and rec[0] == net and gdist(G, rec[1]) < own_gap: return False
    return True
def keepout(L, box, tag):
    x0, y0, x1, y1 = box; g.add('__keepout__', L, ('poly', [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]), tag, 'keepout')
J1 = b.FindFootprintByReference('J1'); cj = J1.GetCourtyard(F).BBox()
padbot = max(p.GetBoundingBox().GetBottom()/1e6 for p in J1.Pads() if p.GetNumber() and p.GetNumber()[0] in 'AB')
keepout(F, (cj.GetLeft()/1e6, padbot + 0.05, cj.GetRight()/1e6, cj.GetBottom()/1e6), 'tmpJ1')
u1p1, u1p3 = P(pad('U1', '1')), P(pad('U1', '3'))
a6, a7, b6, b7 = (P(pad('J1', n)) for n in ('A6', 'A7', 'B6', 'B7'))
u1bot = max(p.GetBoundingBox().GetBottom()/1e6 for p in b.FindFootprintByReference('U1').Pads() if p.GetNumber() in ('1', '2', '3'))
BAR = u1bot + 0.24                                       # D- bar under U1 pins 1-3, 0.16 mm from their ends
VD = 0.40; VA = (a6[0], BAR + 0.44); VB = (b6[0], BAR + 0.44)  # D+ vias: above A6, and on the line into B6
def lay_all(net, polys, layer=F):
    for pts in polys:
        for a, c in zip(pts, pts[1:]):
            if math.dist(a, c) > 1e-6 and not g.clear(('seg', a, c, W/2), layer, net): raise SystemExit('J1 side blocked %s %s %s' % (net, a, c))
    for pts in polys:
        for a, c in zip(pts, pts[1:]):
            if math.dist(a, c) > 1e-6: made.append(g.add_track(a, c, W, layer, net))
for v in (VA, VB):
    if not via_ok(v[0], v[1], JDP, r=VD/2, drill=0.2): raise SystemExit('J1 side via blocked %s' % (v,))
# D-: U1 pin 1 down; at J' it forks 45 degrees: straight on into B7 (the pin's x lies inside B7), and a bar east under
#     U1 pin 2 that turns 45 degrees down into A7. A6 sits inside that fork.
Jm = (u1p1[0], BAR - 0.2)
lay_all(JDM, [[u1p1, Jm, (u1p1[0], b7[1])], [Jm, (u1p1[0] + 0.2, BAR), (a7[0] - 0.2, BAR), (a7[0], BAR + 0.2), a7]])
# D+: U1 pin 3 -> 45 degrees -> down into B6 (via VB on the way); VB -> bottom link -> VA -> up into A6
s3 = (u1p3[0], BAR - (u1p3[0] - b6[0]))
lay_all(JDP, [[u1p3, s3, (b6[0], BAR), VB, b6], [VA, a6]])          # split at VB so the via sits on a track end
made.append(g.add_via(VA[0], VA[1], JDP, d=VD, h=0.2)); made.append(g.add_via(VB[0], VB[1], JDP, d=VD, h=0.2))
lay_all(JDP, [[VA, VB]], pcbnew.B_Cu)
fail = []
# ---- 4. BC1.2 taps to U2 pins 6 (D+) / 7 (D-). The pins face west, boxed in by the IC body (east) and C/R pads (west):
#      D+ comes down the channel west of pins 1-5 from a via north-west of the pin, D- up from a via south-west of pin 7,
#      so the two never meet. No tap copper under the U2 body on top.
U2 = b.FindFootprintByReference('U2'); cu = U2.GetCourtyard(F).BBox()
U2BOX = (cu.GetLeft()/1e6, cu.GetTop()/1e6, cu.GetRight()/1e6, cu.GetBottom()/1e6)
p6, p7 = P(pad('U2', '6')), P(pad('U2', '7'))
def dogleg_paths(a, c):
    dx, dy = c[0] - a[0], c[1] - a[1]; m = min(abs(dx), abs(dy)); dg = (math.copysign(m, dx), math.copysign(m, dy))
    yield [a, (a[0] + dg[0], a[1] + dg[1]), c]; yield [a, (c[0] - dg[0], c[1] - dg[1]), c]
    for d in (0.15, 0.2, 0.25, 0.3, 0.4, 0.5):              # up/down the channel, 45 degrees, then straight into the pin
        if c[0] - a[0] > d: yield [a, (a[0], c[1] + math.copysign(d, a[1] - c[1])), (a[0] + d, c[1]), c]
def tap_via(net, pin, box):
    """nearest legal via in `box` with a clear 45-degree F.Cu stub to the pin (entering it from the west, its outer end)"""
    best = None
    for ix in range(int((box[2] - box[0])/0.05) + 1):
        for iy in range(int((box[3] - box[1])/0.05) + 1):
            x, y = box[0] + ix*0.05, box[1] + iy*0.05
            if not via_ok(x, y, net): continue
            for pth in dogleg_paths((x, y), pin):
                if pth[-2][0] > pin[0] - 0.25 + 1e-6 and abs(pth[-2][1] - pin[1]) > 1e-6: continue   # last leg must be the horizontal pin entry
                if all(seg_ok(a, c, net) for a, c in zip(pth, pth[1:]) if math.dist(a, c) > 1e-6):
                    l = sum(math.dist(a, c) for a, c in zip(pth, pth[1:]))
                    if best is None or l < best[0]: best = (l, (x, y), pth)
    return best
taps = {}
for net, pin, box in ((DP, p6, (U2BOX[0] - 1.2, p6[1] - 2.0, p6[0] - 0.35, p6[1] - 0.45)),
                      (DM, p7, (U2BOX[0] - 1.2, p7[1] + 0.45, p7[0] - 0.35, p7[1] + 2.0))):
    tv = tap_via(net, pin, box)
    if tv is None: raise SystemExit('no tap via for %s' % net)
    taps[net] = tv
    made.append(g.add_via(tv[1][0], tv[1][1], net, d=0.45, h=0.25)); lay(net, tv[2])
keepout(F, U2BOX, 'tmpU2')
for net, line in ((DM, dm_pts), (DP, dp_pts)):
    vx, vy = taps[net][1]
    verts = sorted(line[1:-1], key=lambda q: math.dist(q, (vx, vy)))[:3]       # a pair bend: the tap joins at a vertex
    ok = False
    for v in verts:
        gx0 = math.ceil((v[0] - min(v[0], vx) + 4)/0.05); gy0 = math.ceil((v[1] - min(v[1], vy) + 4)/0.05)
        win = (v[0] - gx0*0.05, v[1] - gy0*0.05, max(v[0], vx) + 4, max(v[1], vy) + 4)   # the pair bend sits on the A* lattice
        pth = nr.astar(g, net, v, (vx, vy), W, 0.05, win, (0,), (0, 1, 2), viacost=1.5, tol=0.04)
        if not pth: continue
        pth[0] = (v[0], v[1], pth[0][2]); pth[-1] = (vx, vy, pth[-1][2])
        nr.emit(g, net, nr.pull(g, net, nr.simplify(pth), W), W, made); ok = True; break
    if not ok: fail.append(net + ' tap')
b.Save(BRD)
vias = {n: sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == n) for n in ALL}
sig_m = L[SDM] + 2.2 + L[DM]; sig_p = L[SDP] + 2.2 + L[DP]     # rough; pathlen.py gives the exact pad-to-pad numbers
print(json.dumps(dict(failed=fail, soc_side={'D-': round(L[SDM], 3), 'D+': round(L[SDP], 3)},
                      main_pair={'D-': round(L[DM], 3), 'D+': round(L[DP], 3)}, vias=vias,
                      unrouted=b.GetConnectivity().GetUnconnectedCount(False))))
