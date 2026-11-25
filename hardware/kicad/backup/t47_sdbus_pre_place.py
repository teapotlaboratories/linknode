"""T47 Section 3b, microSD bus as a planned bundle (owner, 2026-11-23: option 1). Runs on a COPY first.
Usage: python3 t47_sdbus.py <board.kicad_pcb> [--swap-u401] [--rmax 2.2] [--margin 6]
Plan:
  1. Rip up the 3a nets that fence in the SD pins on the bottom (USB_CC_SENSE, SARADC_IN0, USB_VBUSDET); they are
     re-routed afterwards with t47_s3.py.
  2. --swap-u401: U401 channels D0/D1 swapped (pads 4 and 5; TPD4E05U06 channels are identical) so the order along the
     ESD array matches the socket (board-side trial; the schematic follows only after the owner approves).
  3. Socket side: J401's SD pads, U401's and U402's SD pads each get their own via (north of the pad) with a short stub.
  4. Pin side: each SD pin (pins 12, 14, 16, 17, 18) gets a top stub west to its own via; SD_CLK starts at R511 pad 1
     (bottom, after the 22 ohm series resistor).
  5. Each line is routed on the BOTTOM only, from its pin via through its ESD via to its socket via, innermost line first
     (D2, D3, CMD, CLK, D0, D1): the bus turns left (west, south, east), so each later line packs just outside the
     earlier ones and nothing crosses.
Prints each line's length and via count. Saves the board."""
import sys, os, math, json, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import netroute as nr
from geomlib import Geo, CU, bbox
from geomlib import dist as gdist
B = sys.argv[1]
opt = {sys.argv[i]: sys.argv[i + 1] for i in range(2, len(sys.argv) - 1) if sys.argv[i].startswith('--') and sys.argv[i] != '--swap-u401'}
RMAX = float(opt.get('--rmax', 2.2)); MARGIN = float(opt.get('--margin', 6)); W = 0.12
b = pcbnew.LoadBoard(B)
_eb = b.GetBoardEdgesBoundingBox(); EBOX = (_eb.GetLeft()/1e6 - 1, _eb.GetTop()/1e6 - 1, _eb.GetRight()/1e6 + 1, _eb.GetBottom()/1e6 + 1)
F, BC = pcbnew.F_Cu, pcbnew.B_Cu
KEEP = []
CLKP_NET = 'Net-(U100SD and SPI1-SDMMC_CLK{slash}GPIO3_A4)'                  # pin 15 -> R511 (3a copper, re-laid here)
RIP = ('/SoC/USB_CC_SENSE', 'Net-(U100System-SARADC_IN0{slash}GPIO4_C0)', 'Net-(U100System-USB_VBUSDET)', CLKP_NET)
for t in list(b.GetTracks()):
    if t.GetNetname() in RIP: b.Remove(t); KEEP.append(t)
def pad(ref, num): return [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
if '--swap-u401' in sys.argv:
    p4, p5 = pad('U401', '4'), pad('U401', '5'); n4, n5 = p4.GetNet(), p5.GetNet(); p4.SetNet(n5); p5.SetNet(n4)
# R511 (22 ohm SD clock series resistor, bottom) moves into the clock's lane just below its fan-out via, pad 2 (pin side)
# north. --r511 x,y places it; without it R511 is parked off the board so the fan-out can be planned first.
_r = b.FindFootprintByReference('R511')
R511_AT = tuple(float(v) for v in opt['--r511'].split(',')) if '--r511' in opt else (60.0, 60.0)
_r.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(R511_AT[0]), pcbnew.FromMM(R511_AT[1])))
for _rot in (90, 270):
    _r.SetOrientationDegrees(_rot)
    if pad('R511', '2').GetPosition().y < pad('R511', '1').GetPosition().y: break
g = Geo(b, EBOX)
def P(p): return (round(p.GetPosition().x/1e6, 4), round(p.GetPosition().y/1e6, 4))
def via_ok(x, y, net):
    G = ('pt', (x, y), 0.2)
    if not (g.hole_ok(x, y, 0.2) and all(g.clear(G, L, net) for L in CU)): return False
    for L in (F, BC):
        for r in g.near(L, bbox(G), 0.6):
            if r[4] == 'pad' and gdist(G, r[1]) < 0.09: return False
    return nr.usb_ok(g, G, F, net) and nr.usb_ok(g, G, BC, net)
def stubs(a, v):
    dx, dy = v[0] - a[0], v[1] - a[1]
    if abs(dx) < 1e-6 or abs(dy) < 1e-6 or abs(abs(dx) - abs(dy)) < 1e-6: return [[a, v]]
    m = min(abs(dx), abs(dy)); dg = (math.copysign(m, dx), math.copysign(m, dy))
    return [[a, (v[0] - dg[0], v[1] - dg[1]), v], [a, (a[0] + dg[0], a[1] + dg[1]), v]]
def fan(ref, num, d, rmax=RMAX, L=F, xmax=1e9):
    p = pad(ref, num); net = p.GetNetname(); a = P(p); best = None; n = int(rmax/0.05)
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            v = (round(a[0] + i*0.05, 3), round(a[1] + j*0.05, 3)); r = math.dist(a, v)
            if r > rmax or r < 0.3 or (best and r >= best[0]): continue
            if (d == 'N' and v[1] >= a[1] - 0.2) or (d == 'S' and v[1] <= a[1] + 0.2) or (d == 'E' and v[0] <= a[0] + 0.2) or (d == 'W' and v[0] >= a[0] - 0.2) or (d == 'SW' and (v[0] >= a[0] - 0.2 or v[1] < a[1] - 1e-6)): continue
            if v[0] > xmax: continue
            if not via_ok(v[0], v[1], net): continue
            for pts in stubs(a, v):
                if all(g.clear(('seg', q, c, W/2), L, net) and nr.usb_ok(g, ('seg', q, c, W/2), L, net) for q, c in zip(pts, pts[1:]) if math.dist(q, c) > 1e-6):
                    best = (r, v, pts); break
    if not best: raise SystemExit('no fan-out via for %s.%s (%s); so far %s' % (ref, num, d, json.dumps(DONE)))
    for q, c in zip(best[2], best[2][1:]):
        if math.dist(q, c) > 1e-6: g.add_track(q, c, W, L, net)
    g.add_via(best[1][0], best[1][1], net, d=0.4, h=0.2); DONE.append((ref, num, best[1]))
    return best[1]
DONE = []
NETS = {'D2': '/SoC/SD_D2', 'D3': '/SoC/SD_D3', 'CMD': '/SoC/SD_CMD', 'CLK': '/SoC/SD_CLK', 'D0': '/SoC/SD_D0', 'D1': '/SoC/SD_D1'}
PIN = {'D2': '18', 'D3': '17', 'CMD': '16', 'CLKP': '15', 'D0': '14', 'D1': '12'}
J = {'D2': '1', 'D3': '2', 'CMD': '3', 'CLK': '5', 'D0': '7', 'D1': '8'}
ESD = {}
for ref in ('U401', 'U402'):
    for p in b.FindFootprintByReference(ref).Pads():
        for k, n in NETS.items():
            if p.GetNetname() == n: ESD[k] = (ref, p.GetNumber())
pts = {k: [] for k in NETS}
# socket side first (tightest), then the ESD pads, then the pin fan (innermost first)
for k in ('D1', 'D0', 'CLK', 'CMD', 'D3', 'D2'): pts[k].append(('J', fan('J401', J[k], 'N')))
for k in ('D1', 'D0', 'CLK', 'CMD', 'D3', 'D2'): pts[k].insert(0, ('E', fan(*ESD[k], 'N')))
# pin fan-out: a row of vias stepping west (each >= LANE west of the previous), innermost pin first, so the bottom lanes
# heading south keep the pin order D1 D0 CLK CMD D3 D2 (west to east) and the stubs nest without crossing
LANE = float(opt.get('--lane', 0.5)); PV = {}
ORDER = ('D2', 'D3', 'CMD', 'CLKP', 'D0', 'D1')
def cands(k):
    """legal (via, stub) choices for pin k: west of the pin row (side W) or in the ring between the pins and the exposed
    pad (side E, x < 139.2); the stub is straight or one 45-degree dogleg"""
    p = pad('U100', PIN[k]); net = p.GetNetname(); a = P(p); out = {}; n = int(RMAX/0.05)
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            v = (round(a[0] + i*0.05, 3), round(a[1] + j*0.05, 3)); r = math.dist(a, v)
            side = 'W' if v[0] <= a[0] - 0.3 else ('E' if a[0] + 0.3 <= v[0] <= 139.2 else None)
            if not side or r > RMAX or not via_ok(v[0], v[1], net): continue
            for st in stubs(a, v):
                if all(g.clear(('seg', q, c, W/2), F, net) and nr.usb_ok(g, ('seg', q, c, W/2), F, net) for q, c in zip(st, st[1:]) if math.dist(q, c) > 1e-6):
                    L_ = sum(math.dist(q, c) for q, c in zip(st, st[1:])); out[v] = (L_, st, side); break
    lst = sorted(((L_, v, st, sd) for v, (L_, st, sd) in out.items()))
    nc = int(opt.get('--ncand', 60))
    return net, [c for c in lst if c[3] == 'W'][:nc] + [c for c in lst if c[3] == 'E'][:nc]
C = {k: cands(k) for k in ORDER}
print('candidates', {k: len(C[k][1]) for k in ORDER}, flush=True)
if '--show' in opt:
    for k in ORDER:
        vs = [v for _, v, _ in C[k][1]]
        print(k, 'x %.2f..%.2f y %.2f..%.2f' % (min(v[0] for v in vs), max(v[0] for v in vs), min(v[1] for v in vs), max(v[1] for v in vs)), 'n', len(vs), flush=True)
    import collections
    for k in ORDER:
        rows = collections.defaultdict(list)
        for _, v, _ in C[k][1]: rows[round(v[1], 1)].append(v[0])
        print(k, ' '.join('%.1f:[%.2f..%.2f]' % (y, min(xs), max(xs)) for y, xs in sorted(rows.items())), flush=True)
    raise SystemExit(0)
def shapes(v, st): return [('pt', v, 0.2)] + [('seg', q, c, W/2) for q, c in zip(st, st[1:]) if math.dist(q, c) > 1e-6]
def compatible(sa, sb):
    for x in sa:
        for y in sb:
            if gdist(x, y) < 0.16: return False
    return True
best = [1e9, None]
DEEP = [0, None]
def dfs(i, chosen, tot):
    if i > DEEP[0]: DEEP[0] = i; DEEP[1] = [(c[0], c[1], c[4]) for c in chosen]
    if tot >= best[0]: return
    if i == len(ORDER): best[0] = tot; best[1] = list(chosen); return
    k = ORDER[i]
    for L_, v, st, sd in C[k][1]:
        if chosen:
            pk, pv, pst, psh, psd = chosen[-1]
            if psd == 'W' and (sd != 'W' or v[0] > pv[0] - LANE): continue       # west group steps west
            if psd == 'E' and sd == 'E' and v[1] > pv[1] - 0.45: continue        # ring group stacks north
        sh = shapes(v, st)
        if all(compatible(sh, c[3]) for c in chosen):
            chosen.append((k, v, st, sh, sd)); dfs(i + 1, chosen, tot + L_); chosen.pop()
dfs(0, [], 0.0)
if not best[1]: raise SystemExit('no joint pin fan-out (lane %.2f); deepest %d: %s' % (LANE, DEEP[0], DEEP[1]))
for k, v, st, sh, sd in best[1]:
    net = C[k][0]
    for q, c in zip(st, st[1:]):
        if math.dist(q, c) > 1e-6: g.add_track(q, c, W, F, net)
    g.add_via(v[0], v[1], net, d=0.4, h=0.2); PV[k] = v
    if k != 'CLKP': pts[k].insert(0, ('P', v))
print('stub total %.2f mm' % best[0], 'sides', {c[0]: c[4] for c in best[1]}, flush=True)
print('pin vias', json.dumps(PV), flush=True)
if '--r511' not in opt:
    b.Save(B); raise SystemExit('plan only: place R511 below the CLK via %s with --r511 x,y' % (PV['CLKP'],))
pts['CLK'].insert(0, ('R', P(pad('R511', '1'))))
pts['CLKP'] = [('P', PV['CLKP']), ('R', P(pad('R511', '2')))]
NETS['CLKP'] = CLKP_NET
print('fan-out', json.dumps({k: [(t, v) for t, v in pts[k]] for k in pts}), flush=True)
# bottom-only legs, innermost line first
nr.ALLOW = {2}
L = {}; VIAS = {}
for k in ('D2', 'D3', 'CMD', 'CLKP', 'CLK', 'D0', 'D1'):
    net = NETS[k]; tot = 0.0
    for (ta, a), (tc, c) in zip(pts[k], pts[k][1:]):
        win = (min(a[0], c[0]) - MARGIN, min(a[1], c[1]) - MARGIN, max(a[0], c[0]) + MARGIN, max(a[1], c[1]) + MARGIN)
        d = {}
        path = nr.astar(g, net, a, c, W, 0.05, win, (2,), (2,), nr.USB_KEEP, nr.USB_EXTRA, tol=0.04, max_it=3000000, diag=d)
        if not path: raise SystemExit('no bottom path for %s %s->%s %s' % (k, a, c, d))
        path[0] = (a[0], a[1], path[0][2]); path[-1] = (c[0], c[1], path[-1][2])
        path = nr.pull(g, net, nr.simplify(path), W)
        nr.emit(g, net, path, W)
        tot += sum(math.dist(p[:2], q[:2]) for p, q in zip(path, path[1:]))
    L[k] = round(tot, 2)
    print('routed', k, L[k], 'mm on the bottom', flush=True)
b.Save(B)
print(json.dumps(dict(bottom_lengths=L)))
