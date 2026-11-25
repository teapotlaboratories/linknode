"""T53 (owner, 2026-11-24): the microSD bus at the proper size: 50 ohm single-ended (0.17 mm on the JLC 3313 outer
layers, docs/calc/impedance.py) with a gap of at least 2 x width (Rockchip HDG V1.1 Table 3-1, p.47) = 0.51 mm lane pitch.
Owner decision 2026-11-24: a short neck where the bus passes between the Y502 keep-out and C630, and C506/R507 (VBUSDET
divider) move 0.3 mm west so the bus can turn below them at full pitch.
Usage: python3 t53_sdlanes.py <board.kicad_pcb>   (copies only; run t47_tidy for the taps and the moved 3a nets after)
Lanes (bottom), D2 east ... D1 west, card detect outermost:
  vias      one per lane, 0.17 mm below its pin's height, on the lane's own x (top stub: west, one 45-degree bend)
  upper     vertical at 0.45 mm pitch (D2 x 136.045, the last x a via clears the U100 pads; D1 clears the keep-out)
  pinch     45 degrees SW at 0.385 mm pitch between the keep-out corner (133.55, 131.38) and C630 (135.785, 132.545)
  lower     vertical at 0.51 mm pitch (D2 x 135.45, clear of C630/C637/C625)
  diagonal  45 degrees SE at 0.51 mm pitch; D2/D3/CMD turn east north of R404, CLK/D0/D1 (and card detect) south of it
  socket    each lane drops into its socket via (the clock into R511 pad 2), as in t47_sdlanes.
Every segment and via is checked with geomlib (class clearance, USB keep) before it is laid; the script stops on the
first conflict and saves <board>.failed.kicad_pcb."""
import sys, os, math, json, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import netroute as nr
from geomlib import Geo, CU, bbox
from geomlib import dist as gdist
B = sys.argv[1]; b = pcbnew.LoadBoard(B)
F, BC = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.17; WD = 0.12                                   # bus lanes 50 ohm; card detect (static) stays at the default width
CLKP = 'Net-(U100SD and SPI1-SDMMC_CLK{slash}GPIO3_A4)'
VBD = 'Net-(U100System-USB_VBUSDET)'; SAR = 'Net-(U100System-SARADC_IN0{slash}GPIO4_C0)'
N = {'D2': '/SoC/SD_D2', 'D3': '/SoC/SD_D3', 'CMD': '/SoC/SD_CMD', 'CLKP': CLKP, 'D0': '/SoC/SD_D0', 'D1': '/SoC/SD_D1',
     'DET': 'Net-(J401-DET)', 'CLK': '/SoC/SD_CLK', 'SDET': '/SoC/SD_DET'}
RIP = set(N.values()) | {VBD, SAR}                     # the two 3a nets that ran through the corridor are re-routed after
KEEP = []                                              # removed items must stay referenced (SWIG)
for t in list(b.GetTracks()):
    if t.GetNetname() in RIP: b.Remove(t); KEEP.append(t)
MOVE = {'C506': (-0.3, 0.0), 'R507': (-0.3, 0.0)}      # owner 2026-11-24
for ref, (dx, dy) in MOVE.items():
    fp = [f for f in b.GetFootprints() if f.GetReference() == ref][0]; p = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(p.x + pcbnew.FromMM(dx), p.y + pcbnew.FromMM(dy)))
_eb = b.GetBoardEdgesBoundingBox(); g = Geo(b, (_eb.GetLeft()/1e6 - 1, _eb.GetTop()/1e6 - 1, _eb.GetRight()/1e6 + 1, _eb.GetBottom()/1e6 + 1))
FP = {f.GetReference(): f for f in b.GetFootprints()}
def pad(ref, num): return [p for p in FP[ref].Pads() if p.GetNumber() == num][0]
def P(p): return (round(p.GetPosition().x/1e6, 4), round(p.GetPosition().y/1e6, 4))
def R(p): return (round(p[0], 4), round(p[1], 4))
def blockers(net, a, c, L, w):
    G = ('seg', a, c, w/2)
    return [(r[0][-16:], r[3], r[4], round(gdist(G, r[1]), 3)) for r in g.near(L, bbox(G), 0.8)
            if r[0] != net and gdist(G, r[1]) < max(g.ncl(net), g.ncl(r[0])) + 0.01]
def lay(key, pts, L, w=W):
    net = N[key]; pts = [R(p) for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 1e-6]
    for a, c in zip(pts, pts[1:]):
        if not (g.clear(('seg', a, c, w/2), L, net) and nr.usb_ok(g, ('seg', a, c, w/2), L, net)):
            b.Save(B + '.failed.kicad_pcb'); raise SystemExit('blocked %s %s -> %s on %s: %s' % (key, a, c, 'F' if L == F else 'B', blockers(net, a, c, L, w)))
    for a, c in zip(pts, pts[1:]): g.add_track(a, c, w, L, net)
    return sum(math.dist(a, c) for a, c in zip(pts, pts[1:]))
def via(key, v):
    net = N[key]; G = ('pt', v, 0.2)
    ok = g.hole_ok(v[0], v[1], 0.2) and all(g.clear(G, L, net) for L in CU) and \
        all(not (r[4] == 'pad' and gdist(G, r[1]) < 0.09) for L in (F, BC) for r in g.near(L, bbox(G), 0.6))
    if not ok:
        hits = [(r[0][-16:], r[3], r[4], round(gdist(G, r[1]), 3)) for L in CU for r in g.near(L, bbox(G), 0.8) if r[0] != net and gdist(G, r[1]) < max(g.ncl(net), g.ncl(r[0])) + 0.01]
        b.Save(B + '.failed.kicad_pcb'); raise SystemExit('via blocked %s %s: %s' % (key, v, hits))
    g.add_via(v[0], v[1], net, d=0.4, h=0.2)
S2 = math.sqrt(2)
ORDER = ['D2', 'D3', 'CMD', 'CLKP', 'D0', 'D1']        # east -> west on the vertical parts, north -> south on the east run
PIN = {'D2': '18', 'D3': '17', 'CMD': '16', 'CLKP': '15', 'D0': '14', 'D1': '12'}
PU, PN, PF = 0.45, 0.385, 0.51                          # upper, pinch and full pitch
XU0, C0, XL0, YSE0 = 136.045, 267.99, 135.45, 136.35   # D2: upper x, pinch line x + y, lower x, lower -> SE corner y
E0 = XL0 - YSE0                                        # D2's SE diagonal: x - y = E0
LVL = {'D2': 139.55, 'D3': 140.06, 'CMD': 140.57, 'CLKP': 141.89, 'D0': 142.40, 'D1': 142.91}
VDY = {'D2': 0.17, 'D3': 0.17, 'CMD': 0.17, 'CLKP': 0.17, 'D0': 0.22, 'D1': 0.63}   # via below its pin (D1: below R601's pad)
JV = {'D1': (141.325, 144.5), 'D0': (141.925, 144.55), 'CMD': (146.825, 144.5), 'D3': (147.925, 144.5), 'D2': (149.675, 145.35),
      'DET': (140.225, 144.4)}
JP = {'D1': ('J401', '8'), 'D0': ('J401', '7'), 'CMD': ('J401', '3'), 'D3': ('J401', '2'), 'D2': ('J401', '1'), 'DET': ('J401', '9')}
TARGET = dict(JV); TARGET['CLKP'] = P(pad('R511', '2'))
TAPY = {'D2': 141.6, 'D3': 143.6, 'CMD': 142.815, 'D0': 142.815, 'D1': 142.815}   # drops split where the ESD tap joins
L = {}; LANE = {}; VIA = {}
for k_, key in enumerate(ORDER):
    pin = P(pad('U100', PIN[key])); xu = XU0 - PU*k_; c = C0 - PN*S2*k_; xl = XL0 - PF*k_; e = E0 - PF*S2*k_
    v = (xu, round(pin[1] + VDY[key], 4)); VIA[key] = v
    stub = [pin, (v[0] + VDY[key], pin[1]), v]
    L[key] = lay(key, stub, F); via(key, v)
    tx, ty = TARGET[key]; lv = LVL[key]
    pts = [v, (xu, c - xu), (xl, c - xl), (xl, xl - e), (lv + e, lv), (tx, lv)]
    if key in TAPY and lv < TAPY[key] < ty: pts.append((tx, TAPY[key]))
    pts.append((tx, ty)); LANE[key] = pts
for key in ORDER: L[key] += lay(key, LANE[key], BC)
# ---- socket side (as t47_sdlanes)
for key, (ref, num) in JP.items():
    v = JV[key]; p = P(pad(ref, num)); dx = p[0] - v[0]; dy = p[1] - v[1]
    if key == 'DET': continue
    via(key, v)
    m = min(abs(dx), abs(dy))
    stub = [v, (p[0] - math.copysign(m, dx), p[1] - math.copysign(m, dy)) if abs(dx) > 1e-6 and abs(dy) > 1e-6 else v, p]
    lay(key, [q for i, q in enumerate(stub) if i == 0 or math.dist(q, stub[i - 1]) > 1e-6], F)
cv = (144.625, 144.35); via('CLK', cv); lay('CLK', [P(pad('R511', '1')), cv], BC); lay('CLK', [cv, P(pad('J401', '5'))], F)
# ---- card detect: R402 pad 2 -> via -> top -> via on its lane (outside D1) -> lane -> socket via -> pad 9
DGAP = float(os.environ.get('DGAP', 0.45))             # card detect centre to D1 centre
eD = E0 - PF*S2*5 - DGAP*S2; lvD = LVL['D1'] + DGAP
DX = float(os.environ.get('DET_START', 135.0)); dv = (DX, round(DX - eD, 4))
via('DET', JV['DET']); lay('DET', [JV['DET'], P(pad('J401', '9'))], F, WD)
r2 = P(pad('R402', '2')); via('DET', dv)
L['DET'] = lay('DET', [dv, (lvD + eD, lvD), (JV['DET'][0], lvD), JV['DET']], BC, WD)
rv = (round(r2[0] + 0.45, 3), round(r2[1] + 0.6, 3))
lay('DET', [r2, (r2[0], rv[1] - 0.45), rv], BC, WD); via('DET', rv)
dx, dy = dv[0] - rv[0], dv[1] - rv[1]; m = min(abs(dx), abs(dy))
top = [rv, (rv[0] + math.copysign(abs(dx) - m, dx), rv[1]), dv] if abs(dx) >= abs(dy) else [rv, (rv[0], rv[1] + math.copysign(abs(dy) - m, dy)), dv]
L['DET top'] = lay('DET', top, F, WD)
b.Save(B)
print(json.dumps(dict(lengths={k: round(v, 2) for k, v in L.items()}, vias=VIA, det_via=dv)))
