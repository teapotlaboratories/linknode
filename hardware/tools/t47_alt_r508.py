"""T47 Section 2 study (owner, 2026-11-23): R508/R509 side by side instead of stacked, to compare with the current USB
pair (stacked resistors + 4 smooth deskew bumps). Runs on a COPY of the board; never on the main board.
Usage: python3 t47_alt_r508.py <copy.kicad_pcb> [--pitch 1.05] [--y 134.3]
  - R509 (D-) and R508 (D+) upright (pad 1 north), side by side: R509 west, R508 east, `pitch` apart, centre y `y`.
    D- must be the west one: the pair runs south with D- on the west, and the pins put D- north (pin 26 above pin 27).
  - RV1106 side: D- from pin 26 west, then 45 degrees down into R509 pad 1 (passing above R508); D+ from pin 27 west, then
    45 degrees down into R508 pad 1.
  - Main pair: symmetric 45-degree fan-in from the two pad 2s to the coupled pair (0.155 / 0.130 mm), then the same
    heading-aware A* centreline as t47_usb.py down to U1, 0.6 mm straight at both ends. No deskew bumps, no taps: the
    point is the skew the geometry gives by itself. Prints both path lengths."""
import sys, os, math, heapq, json, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geomlib import Geo
BRD = sys.argv[1]
opt = {sys.argv[i]: sys.argv[i + 1] for i in range(2, len(sys.argv) - 1) if sys.argv[i].startswith('--')}
PITCH, YC = float(opt.get('--pitch', 1.05)), float(opt.get('--y', 134.3))
MODE = opt.get('--mode', 'side')                      # side: R508/R509 side by side; west: resistors as placed, pair leaves west
F = pcbnew.F_Cu
DP, DN, SDP, SDN = '/SoC/USB_DP', '/SoC/USB_DN', '/SoC/USB_SOC_DP', '/SoC/USB_SOC_DN'
W, GAP = 0.155, 0.130; OFF = (W + GAP)/2; FAT = OFF + W/2; EXTRA = 0.35
b = pcbnew.LoadBoard(BRD)
_eb = b.GetBoardEdgesBoundingBox(); EBOX = (_eb.GetLeft()/1e6 - 1, _eb.GetTop()/1e6 - 1, _eb.GetRight()/1e6 + 1, _eb.GetBottom()/1e6 + 1)
KEEP = []
for t in list(b.GetTracks()):
    if t.GetNetname() in (DP, DN, SDP, SDN): b.Remove(t); KEEP.append(t)
def P(p): return (round(p.GetPosition().x/1e6, 4), round(p.GetPosition().y/1e6, 4))
def pad(ref, num): return [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
# ---- place the resistors upright, pad 1 north
if MODE == 'side':
    for ref, x in (('R509', 133.0), ('R508', 133.0 + PITCH)):
        f = b.FindFootprintByReference(ref)
        for rot in (90, 270):
            f.SetOrientationDegrees(rot); f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(YC)))
            if P(pad(ref, '1'))[1] < P(pad(ref, '2'))[1]: break
court = {}
for f in b.GetFootprints():
    if f.IsFlipped(): continue
    c = f.GetCourtyard(F).BBox(); court[f.GetReference()] = (c.GetLeft()/1e6, c.GetTop()/1e6, c.GetRight()/1e6, c.GetBottom()/1e6)
clash = [(r, o) for r in ('R508', 'R509') for o, bb in court.items() if o not in ('R508', 'R509', r) and
         not (court[r][2] <= bb[0] or bb[2] <= court[r][0] or court[r][3] <= bb[1] or bb[3] <= court[r][1])]
g = Geo(b, EBOX)
made = []
def lay(net, pts, ignore=()):
    for a, c in zip(pts, pts[1:]):
        if math.dist(a, c) > 1e-6 and not g.clear(('seg', a, c, W/2), F, net, ignore=lambda r: r[0] in ignore):
            raise SystemExit('blocked %s %s -> %s' % (net, a, c))
    for a, c in zip(pts, pts[1:]):
        if math.dist(a, c) > 1e-6: made.append(g.add_track(a, c, W, F, net))
    return sum(math.dist(a, c) for a, c in zip(pts, pts[1:]))
p26, p27 = P(pad('U100', '26')), P(pad('U100', '27'))
r9a, r8a, r9b, r8b = P(pad('R509', '1')), P(pad('R508', '1')), P(pad('R509', '2')), P(pad('R508', '2'))
def west_then_down(pin, pd):
    d = pd[1] - pin[1]; return [pin, (pd[0] + d, pin[1]), pd]
L = {}
if MODE == 'side':
    L[SDN] = lay(SDN, west_then_down(p26, r9a))
    L[SDP] = lay(SDP, west_then_down(p27, r8a))
else:                                                       # stacked as placed: D- on pin 26's line, D+ one 45-degree step
    L[SDN] = lay(SDN, [p26, (r9a[0], p26[1])])
    dy = r8a[1] - p27[1]; xd = r8a[0] + 0.45
    L[SDP] = lay(SDP, [p27, (xd + dy, p27[1]), (xd, r8a[1]), r8a])
# ---- main pair: symmetric fan-in, then A* centreline heading south
cx = (r9b[0] + r8b[0])/2; inward = (r8b[0] - r9b[0] - 2*OFF)/2
GRID = 0.05; RUN = 0.6
u6, u4 = P(pad('U1', '6')), P(pad('U1', '4')); cx1 = (u6[0] + u4[0])/2
if MODE == 'side':
    START = (cx, r9b[1] + inward + 0.3); K0 = 2
    cx = cx1 + round((cx - cx1)/GRID)*GRID; START = (cx, START[1])
else:                                                       # pair heads west from the stacked pads, D- (north) on its right
    RUN = float(opt.get('--run', 0.2))
    cy = (r9b[1] + r8b[1])/2; inw = (r8b[1] - r9b[1] - 2*OFF)/2
    K0 = int(opt.get('--k0', 4))                             # 4 = west, 3 = south-west
    sx = r9b[0] - inw - float(opt.get('--dx', 0.1)); sx = cx1 + round((sx - cx1)/GRID)*GRID
    sy = cy + float(opt.get('--dy', 0.0)); sy = START0y = sy
    START = (sx, sy)
GOAL1 = (cx1, START[1] + round((u6[1] - 2.20 - START[1])/GRID)*GRID); GOAL = (cx1, GOAL1[1] - RUN); K1 = 2
WIN = (START[0] - 240*GRID, START[1] - 40*GRID, START[0] + 120*GRID, GOAL[1] + 1.5)
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
ALLN = (DP, DN, SDP, SDN, '/USB and Charger/USB_CONN_DP', '/USB and Charger/USB_CONN_DN')
ig = lambda r: r[0] in ALLN
cache = {}
def free(i, j):
    k = (i, j)
    if k not in cache:
        pt = (WIN[0] + i*GRID, WIN[1] + j*GRID)
        cache[k] = g.clear(('pt', pt, FAT + 0.02), F, DP, ignore=ig) and g.clear(('pt', pt, FAT + 0.02), F, DP, extra_tracks=EXTRA, ignore=lambda r: ig(r) or r[4] != 'track')
    return cache[k]
MINRUN = 6                                                   # straight steps (x0.05 mm) required between two bends
def astar():
    si, sj = round((START[0] - WIN[0])/GRID), round((START[1] - WIN[1])/GRID)
    gi, gj = round((GOAL[0] - WIN[0])/GRID), round((GOAL[1] - WIN[1])/GRID)
    nx, ny = int((WIN[2] - WIN[0])/GRID) + 1, int((WIN[3] - WIN[1])/GRID) + 1
    s = (si, sj, K0, 0); gs = {s: 0.0}; came = {s: None}; q = [(0.0, 0.0, s)]
    while q:
        f, gg, n = heapq.heappop(q)
        if gg > gs.get(n, 1e18) + 1e-9: continue
        i, j, k, c = n
        if (i, j, k) == (gi, gj, K1):
            path = []
            while n is not None: path.append(n); n = came[n]
            return [(round(WIN[0] + i*GRID, 6), round(WIN[1] + j*GRID, 6)) for i, j, k, c in reversed(path)]
        for dk in (-1, 0, 1):
            if dk and (gg < RUN or c < MINRUN): continue
            k2 = (k + dk) % 8; d = DIRS[k2]; m = (i + d[0], j + d[1], k2, 0 if dk else min(c + 1, MINRUN))
            if not (0 <= m[0] < nx and 0 <= m[1] < ny) or not free(m[0], m[1]): continue
            ng = gg + GRID*math.hypot(*d) + (0.6 if dk else 0.0)
            if ng < gs.get(m, 1e18) - 1e-9:
                gs[m] = ng; came[m] = n; heapq.heappush(q, (ng + math.hypot(WIN[0] + m[0]*GRID - GOAL[0], WIN[1] + m[1]*GRID - GOAL[1]), ng, m))
    return None
path = astar()
if not path: raise SystemExit('no centreline path')
def merge(pts):
    out = [pts[0]]
    for q in pts[1:]:
        if len(out) >= 2:
            a, c = out[-2], out[-1]
            if abs((c[0] - a[0])*(q[1] - c[1]) - (c[1] - a[1])*(q[0] - c[0])) < 1e-9: out[-1] = q; continue
        out.append(q)
    return out
cl = merge(path + [GOAL1])
if os.environ.get('ALT_DEBUG'): print('cl', cl[:5], 'START', START, 'RUN', RUN, flush=True)
def offset(poly, d):
    out = []
    def nrm(a, c):
        dx, dy = c[0] - a[0], c[1] - a[1]; l = math.hypot(dx, dy); return (-dy/l, dx/l)
    for k, p in enumerate(poly):
        if k in (0, len(poly) - 1):
            n = nrm(poly[0], poly[1]) if k == 0 else nrm(poly[-2], poly[-1]); out.append((p[0] + n[0]*d, p[1] + n[1]*d)); continue
        n1, n2 = nrm(poly[k - 1], p), nrm(p, poly[k + 1]); m = (n1[0] + n2[0], n1[1] + n2[1]); lm = math.hypot(*m)
        m = (m[0]/lm, m[1]/lm); cv = m[0]*n1[0] + m[1]*n1[1]; out.append((p[0] + m[0]*d/cv, p[1] + m[1]*d/cv))
    return out
lm_, lp_ = offset(cl, OFF), offset(cl, -OFF)
def fan(p_pad, p_line, diag_first):
    dx, dy = p_line[0] - p_pad[0], p_line[1] - p_pad[1]; m = min(abs(dx), abs(dy)); dg = (math.copysign(m, dx), math.copysign(m, dy))
    return [p_pad, (p_pad[0] + dg[0], p_pad[1] + dg[1]), p_line] if diag_first else [p_pad, (p_line[0] - dg[0], p_line[1] - dg[1]), p_line]
dm = merge(fan(r9b, lm_[0], True)[:-1] + lm_ + fan(u6, lm_[-1], False)[::-1][1:])
dp = merge(fan(r8b, lp_[0], True)[:-1] + lp_ + fan(u4, lp_[-1], False)[::-1][1:])
L[DN] = lay(DN, dm, ignore=(DP,)); L[DP] = lay(DP, dp, ignore=(DN,))
b.Save(BRD)
tot = {'D-': L[SDN] + L[DN], 'D+': L[SDP] + L[DP]}
print(json.dumps(dict(placement={'R509': P(b.FindFootprintByReference('R509')), 'R508': P(b.FindFootprintByReference('R508'))}, courtyard_clash=clash,
                      soc_side={'D-': round(L[SDN], 3), 'D+': round(L[SDP], 3)}, main_pair={'D-': round(L[DN], 3), 'D+': round(L[DP], 3)},
                      total={k: round(v, 3) for k, v in tot.items()}, skew=round(tot['D-'] - tot['D+'], 3))))
