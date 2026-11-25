"""T47 Section 3b tidy-up (owner, 2026-11-23: "make sure no jagged route"; card-detect on the bottom, adjacent to SD_D1):
rebuild the microSD bus as hand-set parallel lanes instead of grid-router paths.
Usage: python3 t47_sdlanes.py <board.kicad_pcb>
  1. Rip the copper of the SD nets, the pin-side clock net and both card-detect nets (parts stay where they are).
  2. Pin side: the 45-degree via row (D2 (136.0, 130.45) stepping 0.4 up-left; D1 at 133.98 so its lane needs no jog);
     each pin: straight west, one 45-degree bend into its via. Each lane leaves its via with ONE 45-degree jog.
  3. Lanes: D2's centreline goes down x 135.48 to y 136.5, 45 degrees south-east, then east at y 139.6. Lane k is that
     path offset outward by d_k (mitred corners): D3 0.3, CMD 0.6, CLK 0.9, D0 1.2, D1 1.5, card detect 2.0. Each lane
     ends on its level straight above its target and drops into it (socket via; R511 pad 2 for the clock).
  4. Socket side: one via north of each socket pad with a straight top stub (positions kept from the approved bus);
     SD_CLK = R511 pad 1 straight down to its socket via.
  5. Card detect (J401 DET): R402 pad 2 -> its via -> top across the bus -> a via on its lane -> lane -> socket via.
  6. ESD taps (U401/U402 pads to their lines) and SD_DET's pin side are routed afterwards by t47_sdtaps (netroute).
Every segment and via is checked with geomlib before it is laid; the script stops on the first conflict."""
import sys, os, math, json, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import netroute as nr
from geomlib import Geo, CU, bbox
from geomlib import dist as gdist
B = sys.argv[1]; b = pcbnew.LoadBoard(B)
F, BC = pcbnew.F_Cu, pcbnew.B_Cu; W = 0.12; KEEP = []
CLKP = 'Net-(U100SD and SPI1-SDMMC_CLK{slash}GPIO3_A4)'
N = {'D2': '/SoC/SD_D2', 'D3': '/SoC/SD_D3', 'CMD': '/SoC/SD_CMD', 'CLKP': CLKP, 'D0': '/SoC/SD_D0', 'D1': '/SoC/SD_D1',
     'DET': 'Net-(J401-DET)', 'CLK': '/SoC/SD_CLK', 'SDET': '/SoC/SD_DET'}
for t in list(b.GetTracks()):
    if t.GetNetname() in N.values(): b.Remove(t); KEEP.append(t)
_eb = b.GetBoardEdgesBoundingBox(); g = Geo(b, (_eb.GetLeft()/1e6 - 1, _eb.GetTop()/1e6 - 1, _eb.GetRight()/1e6 + 1, _eb.GetBottom()/1e6 + 1))
def pad(ref, num): return [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
def P(p): return (round(p.GetPosition().x/1e6, 4), round(p.GetPosition().y/1e6, 4))
def blockers(net, a, c, L):
    G = ('seg', a, c, W/2); out = []
    for r in g.near(L, bbox(G), 0.8):
        if r[0] != net and gdist(G, r[1]) < max(g.ncl(net), g.ncl(r[0])) + 0.01: out.append((r[0][-16:], r[3], r[4], round(gdist(G, r[1]), 3)))
    return out
def lay(key, pts, L):
    net = N[key]; pts = [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 1e-6]
    for a, c in zip(pts, pts[1:]):
        if not (g.clear(('seg', a, c, W/2), L, net) and nr.usb_ok(g, ('seg', a, c, W/2), L, net)):
            b.Save(B + '.failed.kicad_pcb'); raise SystemExit('blocked %s %s -> %s on %s: %s' % (key, a, c, 'F' if L == F else 'B', blockers(net, a, c, L)))
    for a, c in zip(pts, pts[1:]): g.add_track(a, c, W, L, net)
    return sum(math.dist(a, c) for a, c in zip(pts, pts[1:]))
def via(key, v):
    net = N[key]; G = ('pt', v, 0.2)
    ok = g.hole_ok(v[0], v[1], 0.2) and all(g.clear(G, L, net) for L in CU) and \
        all(not (r[4] == 'pad' and gdist(G, r[1]) < 0.09) for L in (F, BC) for r in g.near(L, bbox(G), 0.6))
    if not ok:
        hits = [(r[0][-16:], r[3], r[4], round(gdist(G, r[1]), 3)) for L in CU for r in g.near(L, bbox(G), 0.8) if r[0] != net and gdist(G, r[1]) < max(g.ncl(net), g.ncl(r[0])) + 0.01]
        b.Save(B + '.failed.kicad_pcb'); raise SystemExit('via blocked %s %s: %s' % (key, v, hits))
    g.add_via(v[0], v[1], net, d=0.4, h=0.2)
L = {}
# ---- 2. pin side: via row, stubs
PIN = {'D2': '18', 'D3': '17', 'CMD': '16', 'CLKP': '15', 'D0': '14', 'D1': '12'}
ORDER = ['D2', 'D3', 'CMD', 'CLKP', 'D0', 'D1']
VIA = {k: (round(136.0 - n*0.4, 3), round(130.45 - n*0.4, 3)) for n, k in enumerate(ORDER)}
VIA['D1'] = (133.98, 128.45)
for k in ORDER:
    a = P(pad('U100', PIN[k])); v = VIA[k]; dy = v[1] - a[1]
    L[k] = lay(k, [a, (v[0] + abs(dy), a[1]), v] if abs(dy) > 1e-6 else [a, v], F); via(k, v)
# ---- 3. lanes
D = {'D2': 0.0, 'D3': 0.3, 'CMD': 0.6, 'CLKP': 0.9, 'D0': 1.2, 'D1': 1.5, 'DET': 2.0}
X0, YT, YL = 135.48, 136.5, 139.6                       # centreline: down x X0 to YT, 45 deg SE to level YL, then east
BASE = [(X0, 130.0), (X0, YT), (X0 + (YL - YT), YL), (152.0, YL)]
def offset(poly, d):
    out = []
    def nrm(a, c):
        dx, dy = c[0] - a[0], c[1] - a[1]; l = math.hypot(dx, dy); return (-dy/l, dx/l)
    for i, p in enumerate(poly):
        if i in (0, len(poly) - 1):
            n = nrm(poly[0], poly[1]) if i == 0 else nrm(poly[-2], poly[-1]); out.append((p[0] + n[0]*d, p[1] + n[1]*d)); continue
        n1, n2 = nrm(poly[i - 1], p), nrm(p, poly[i + 1]); m = (n1[0] + n2[0], n1[1] + n2[1]); lm = math.hypot(*m)
        m = (m[0]/lm, m[1]/lm); cv = m[0]*n1[0] + m[1]*n1[1]; out.append((p[0] + m[0]*d/cv, p[1] + m[1]*d/cv))
    return [(round(x, 4), round(y, 4)) for x, y in out]
JV = {'D1': (141.325, 144.5), 'D0': (141.925, 144.55), 'CMD': (146.825, 144.5), 'D3': (147.925, 144.5), 'D2': (149.675, 145.35),
      'DET': (140.225, 144.4)}
JP = {'D1': ('J401', '8'), 'D0': ('J401', '7'), 'CMD': ('J401', '3'), 'D3': ('J401', '2'), 'D2': ('J401', '1'), 'DET': ('J401', '9')}
TARGET = dict(JV); TARGET['CLKP'] = P(pad('R511', '2'))
# ESD tap points: the drop of each lane is split level with its ESD pad, so the tap (routed later) joins the line there
TAPY = {'D2': 141.6, 'D3': 143.6, 'CMD': 142.815, 'D0': 142.815, 'D1': 142.815}
DET_START = float(os.environ.get('DET_START', 135.0))   # x where card detect joins its lane (on the 45-degree part)
LANE = {}
for k in ORDER + ['DET']:
    lp = offset(BASE, D[k])
    tx, ty = TARGET[k]; yl = lp[2][1]                   # level y of this lane (east part)
    assert lp[2][0] < tx, (k, lp[2], tx)
    pts = lp[1:3] + [(tx, yl), (tx, ty)]                # corner S->SE, corner SE->E, above target, target
    if k in TAPY and yl < TAPY[k] < ty: pts = pts[:-1] + [(tx, TAPY[k]), (tx, ty)]   # a track end where the ESD tap joins
    if k == 'DET':
        c0 = lp[1]; s = (DET_START, round(c0[1] + (DET_START - c0[0]), 4))      # a point on DET's 45-degree part
        pts = [s] + pts[1:]
    else:
        v = VIA[k]; fx = lp[1][0]                        # the lane's x on the vertical part
        jog = round(v[0] - fx, 4); fe = (fx, round(v[1] + jog, 4))
        pts = [v, fe] + pts if jog > 1e-6 else [v] + pts
    LANE[k] = pts
# lay inner first (any order is planar; inner first only matters for error messages)
for k in ORDER: L[k] += lay(k, LANE[k], BC)
# ---- 4. socket side
for k, (ref, num) in JP.items():
    v = JV[k]; p = P(pad(ref, num)); dx = p[0] - v[0]; dy = p[1] - v[1]
    via(k, v) if k != 'DET' else None
    stub = [v, (p[0] - math.copysign(min(abs(dx), abs(dy)), dx), p[1] - math.copysign(min(abs(dx), abs(dy)), dy)) if abs(dx) > 1e-6 and abs(dy) > 1e-6 else v, p]
    stub = [q for i, q in enumerate(stub) if i == 0 or math.dist(q, stub[i - 1]) > 1e-6]
    if k != 'DET': lay(k, stub, F)
cv = (144.625, 144.35); via('CLK', cv); lay('CLK', [P(pad('R511', '1')), cv], BC)
p5 = P(pad('J401', '5')); lay('CLK', [cv, p5], F)
# ---- 5. card detect: R402 pad 2 -> via -> top -> via on its lane -> lane -> socket via -> pad 9
via('DET', JV['DET']); p9 = P(pad('J401', '9')); lay('DET', [JV['DET'], p9], F)
r2 = P(pad('R402', '2')); dv = LANE['DET'][0]
via('DET', dv); L['DET'] = lay('DET', LANE['DET'], BC)
rv = (round(r2[0] + 0.45, 3), round(r2[1] + 0.6, 3))                 # R402 pad 2's via, as before
lay('DET', [r2, (r2[0], rv[1] - 0.45), rv], BC); via('DET', rv)
dx, dy = dv[0] - rv[0], dv[1] - rv[1]; m = min(abs(dx), abs(dy))
top = [rv, (rv[0] + math.copysign(abs(dx) - m, dx), rv[1]), dv] if abs(dx) >= abs(dy) else [rv, (rv[0], rv[1] + math.copysign(abs(dy) - m, dy)), dv]
L['DET top'] = lay('DET', top, F)
b.Save(B)
print(json.dumps({k: round(v, 2) for k, v in L.items()}))
