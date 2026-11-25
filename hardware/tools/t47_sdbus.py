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
# Bottom corner re-placement (owner, 2026-11-23, option 1): the parts under and just south of the SD pins move out of a
# reserved corridor (CORR, bottom) to the nearest legal bottom spot west of it: C608 (VDD_0V9 bulk 10 uF), C506
# (VBUSDET), C508 (CC sense), C507 + R510 (SARADC recovery). Legal = inside the board, bottom courtyard free of every other
# bottom courtyard, pads keep class clearance to all other bottom copper. Cost = distance from where the part was.
CORR = tuple(float(v) for v in opt.get('--corr', '133.2,127.3,136.2,141.8').split(','))
MOVE = opt.get('--move', 'C608,C506,C508,C507,R510').split(',')
ANCHOR = {a_.split('=')[0]: tuple(float(v) for v in a_.split('=')[1].split(',')) for a_ in opt['--anchor'].split(';')} if '--anchor' in opt else {}
AVOID = [tuple(float(v) for v in a_.split(',')) for a_ in opt['--avoid'].split(';')] if '--avoid' in opt else []   # extra keep-clear boxes (via room for the 3a nets)
MOVED = {}
if MOVE != ['']:
    _g0 = Geo(b, EBOX)
    def _court(f):
        c = f.GetCourtyard(BC).BBox(); return (c.GetLeft()/1e6, c.GetTop()/1e6, c.GetRight()/1e6, c.GetBottom()/1e6)
    def _ov(a, c): return not (a[2] <= c[0] or c[2] <= a[0] or a[3] <= c[1] or c[3] <= a[1])
    others = [f for f in b.GetFootprints() if f.IsFlipped() and f.GetReference() not in MOVE]
    placed = []
    for ref in MOVE:
        f = b.FindFootprintByReference(ref); x0, y0 = f.GetPosition().x/1e6, f.GetPosition().y/1e6; r0 = f.GetOrientationDegrees()
        xo, yo = x0, y0                                         # where the part was (reported)
        if ref in ANCHOR: x0, y0 = ANCHOR[ref]                  # search around an anchor instead (near its partners)
        best = None
        for dx10 in range(-90, 91):
            for dy10 in range(-90, 91):
                x, y = round(x0 + dx10*0.1, 2), round(y0 + dy10*0.1, 2); d = math.hypot(x - x0, y - y0)
                if best and d >= best[0]: continue
                for rot in (r0, r0 + 90):
                    f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))); f.SetOrientationDegrees(rot)
                    cb = _court(f)
                    if cb[2] > CORR[0] or _ov(cb, CORR) or any(_ov(cb, a_) for a_ in AVOID) or any(_ov(cb, _court(o)) for o in others) or any(_ov(cb, pc) for pc in placed): continue
                    if cb[0] < _g0.edge[0] + 0.5 or cb[2] > _g0.edge[2] - 0.5 or cb[1] < _g0.edge[1] + 0.5 or cb[3] > _g0.edge[3] - 0.5: continue
                    if all(_g0.clear(('poly', pts), BC, pd.GetNetname(), ignore=lambda r: r[3] in MOVE) for pd in f.Pads() for pts in _g0.poly_of(pd, BC)):
                        best = (d, x, y, rot); break
        if not best: raise SystemExit('no spot for %s' % ref)
        f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(best[1]), pcbnew.FromMM(best[2]))); f.SetOrientationDegrees(best[3])
        placed.append(_court(f)); MOVED[ref] = (round(xo, 2), round(yo, 2), r0, best[1], best[2], best[3], round(math.hypot(best[1] - xo, best[2] - yo), 2))
    print('moved', json.dumps(MOVED), flush=True)
# R511 (22 ohm SD clock series resistor, bottom) moves into the clock's lane just below its fan-out via, pad 2 (pin side)
# north. --r511 x,y places it; without it R511 is parked off the board so the fan-out can be planned first.
_r = b.FindFootprintByReference('R511')
R511_END = opt.get('--r511') == 'end'
if R511_END:                                                  # socket end: upright in the clock's drop into its socket via
    R511_AT = (round(pad('J401', '5').GetPosition().x/1e6, 3), float(opt.get('--r511y', 142.4)))
else:
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
JXMAX = {'D0': 142.05}                                       # D0 drops west of R404/R406 (SD power switch parts, bottom)
for k in ('D1', 'D0', 'CLK', 'CMD', 'D3', 'D2'): pts[k].append(('J', fan('J401', J[k], 'N', xmax=JXMAX.get(k, 1e9))))
# pin fan-out: a row of vias stepping west (each >= LANE west of the previous), innermost pin first, so the bottom lanes
# heading south keep the pin order D1 D0 CLK CMD D3 D2 (west to east) and the stubs nest without crossing
PV = {}
ORDER = ('D2', 'D3', 'CMD', 'CLKP', 'D0', 'D1')
# Hand-set pin fan-out (2026-11-23): the six vias in one 45-degree row stepping up-left from D2, so each stub (straight
# west along its pin's row, then one 45-degree jog down into its via) passes the vias of the pins below it with
# clearance, and the bottom lanes leave in pin order (D1 west ... D2 east). --fan x,y,step sets D2's via and the step.
FX, FY, FS = (float(v) for v in opt.get('--fan', '136.0,130.45,0.4').split(','))
bad = []
for n_, k in enumerate(ORDER):
    p = pad('U100', PIN[k]); net = p.GetNetname(); a = P(p)
    v = (round(FX - n_*FS, 3), round(FY - n_*FS, 3))
    dy = v[1] - a[1]
    st = [a, (v[0] + abs(dy), a[1]), v] if abs(dy) > 1e-6 else [a, v]          # west, then 45 degrees into the via
    ok_v = via_ok(v[0], v[1], net)
    ok_s = all(g.clear(('seg', q, c, W/2), F, net) and nr.usb_ok(g, ('seg', q, c, W/2), F, net) for q, c in zip(st, st[1:]) if math.dist(q, c) > 1e-6)
    if not (ok_v and ok_s): bad.append((k, v, 'via' if not ok_v else 'stub')); continue
    for q, c in zip(st, st[1:]):
        if math.dist(q, c) > 1e-6: g.add_track(q, c, W, F, net)
    g.add_via(v[0], v[1], net, d=0.4, h=0.2); PV[k] = v
    if k != 'CLKP': pts[k].insert(0, ('P', v))
if bad:
    b.Save(B); raise SystemExit('fan-out blocked: %s (placed %s)' % (bad, PV))
print('pin vias', json.dumps(PV), flush=True)
NETS['CLKP'] = CLKP_NET
# socket end: each line comes down into its socket via from straight above, from its own level (D2 highest, D1 lowest),
# so the lines peel off in order after the bus's left turns (W -> S -> E) without boxing each other in
LV0, LVP = (float(v) for v in opt.get('--levels', '139.4,0.32').split(','))
TX = float(opt.get('--turnx', 138.3))
for n_, k in enumerate(('D2', 'D3', 'CMD', 'CLK', 'D0', 'D1')):
    jx, jy = pts[k][-1][1]
    pts[k].insert(len(pts[k]) - 1, ('T', (round(TX + (5 - n_)*0.13, 3), round(LV0 + n_*LVP, 3))))   # turn east here
    pts[k].insert(len(pts[k]) - 1, ('L', (jx, round(LV0 + n_*LVP, 3))))
nr.ALLOW = {2}
L = {}
def leg(k, a, c):
    net = NETS[k]
    win = (min(a[0], c[0]) - MARGIN, min(a[1], c[1]) - MARGIN, max(a[0], c[0]) + MARGIN, max(a[1], c[1]) + MARGIN)
    d = {}
    path = nr.astar(g, net, a, c, W, 0.05, win, (2,), (2,), nr.USB_KEEP, nr.USB_EXTRA, tol=0.04, max_it=3000000, diag=d)
    if not path: return None, d
    path[0] = (a[0], a[1], path[0][2]); path[-1] = (c[0], c[1], path[-1][2])
    return nr.pull(g, net, nr.simplify(path), W), d
def lay_leg(k, path):
    nr.emit(g, NETS[k], path, W); return sum(math.dist(p[:2], q[:2]) for p, q in zip(path, path[1:]))
def route(k):
    tot = 0.0
    for (ta, a), (tc, c) in zip(pts[k], pts[k][1:]):
        path, d = leg(k, a, c)
        if not path:
            G_ = ('seg', a, c, W/2); hits = []
            for r in g.near(BC, bbox(G_), 0.8):
                if r[0] == NETS[k]: continue
                need = max(g.ncl(NETS[k]), g.ncl(r[0])) + 0.01; dd = gdist(G_, r[1])
                if dd < need: hits.append((r[0][-14:], r[3], r[4], round(dd, 3), round(need, 3)))
            b.Save(B); raise SystemExit('no bottom path for %s %s->%s %s; straight-line blockers %s' % (k, a, c, d, hits))
        tot += lay_leg(k, path)
    L[k] = round(tot, 2); print('routed', k, L[k], 'mm on the bottom', flush=True)
if R511_END:
    # the long clock line is the pin-side net (pin 15 via -> lanes -> R511 pad 2); SD_CLK is the short R511 pad 1 -> socket
    pts['CLKP'] = [('P', PV['CLKP'])] + pts['CLK'][:-1] + [('R', P(pad('R511', '2')))]
    pts['CLK'] = [('R', P(pad('R511', '1'))), pts['CLK'][-1]]
    for k, xl in {'D1': 134.05, 'D0': 134.35, 'CLKP': 134.65, 'CMD': 134.95, 'D3': 135.25, 'D2': 135.55}.items():
        pts[k].insert(1, ('W', (xl, float(opt.get('--corry', 133.6)))))
    for k in ('D2', 'D3', 'CMD', 'CLKP', 'D0', 'D1', 'CLK'): route(k)
elif '--r511' in opt:                                         # R511 fixed before routing (placed with the board)
    pts['CLKP'] = [('P', PV['CLKP']), ('R', P(pad('R511', '2')))]
    pts['CLK'].insert(0, ('R', P(pad('R511', '1'))))
    # lane waypoints (hand-set): beside R511 (D1/D0 west of it, CMD/D3/D2 east), then the corridor at a 0.3 mm pitch
    rx = P(fr := b.FindFootprintByReference('R511'))[0]
    LANES = {round(P(fr)[1], 3): {'D1': rx - 0.84, 'D0': rx - 0.55, 'CMD': rx + 0.50, 'D3': rx + 0.79, 'D2': rx + 1.08},
             float(opt.get('--corry', 133.6)): {'D1': 134.05, 'D0': 134.35, 'CLK': 134.65, 'CMD': 134.95, 'D3': 135.25, 'D2': 135.55}}
    for yl in sorted(LANES):
        for k, xl in LANES[yl].items():
            i_ = 1 if k != 'CLK' else 1                      # after the start point (pin via, or R511 pad 1 for CLK)
            while i_ < len(pts[k]) and pts[k][i_][0] == 'W': i_ += 1
            pts[k].insert(i_, ('W', (round(xl, 3), yl)))
    for k in ('D2', 'D3', 'CMD', 'CLKP', 'CLK', 'D0', 'D1'): route(k)
else:
  # 1. the inner lines
  for k in ('D2', 'D3', 'CMD'): route(k)
  # 2. R511 (bottom, upright, pad 2 = pin side north): the legal spot nearest the CLK via from which the CLK via reaches pad 2
  #    on the bottom; tried nearest first. Then the clock (pin side, then SD_CLK on to U401/J401), then the outer lines.
  RB = tuple(float(v) for v in opt.get('--r511box', '133.3,130.8,137.3,139.5').split(','))
  fr = b.FindFootprintByReference('R511'); cv = PV['CLKP']
  others = [f for f in b.GetFootprints() if f.IsFlipped() and f.GetReference() != 'R511']
  def _court(f):
      c = f.GetCourtyard(BC).BBox(); return (c.GetLeft()/1e6, c.GetTop()/1e6, c.GetRight()/1e6, c.GetBottom()/1e6)
  def _ov(a, c): return not (a[2] <= c[0] or c[2] <= a[0] or a[3] <= c[1] or c[3] <= a[1])
  oc = [_court(o) for o in others]
  spots = sorted(((math.dist(cv, (RB[0] + i*0.05, RB[1] + j*0.05)), round(RB[0] + i*0.05, 3), round(RB[1] + j*0.05, 3))
                  for i in range(int((RB[2] - RB[0])/0.05) + 1) for j in range(int((RB[3] - RB[1])/0.05) + 1)))
  placed = None; tried = 0
  for dd, x, y in spots:
      fr.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
      if any(_ov(_court(fr), c) for c in oc): continue
      polys = [(pd.GetNetname(), pts_) for pd in fr.Pads() for pts_ in g.poly_of(pd, BC)]
      if not all(g.clear(('poly', pts_), BC, n_, ignore=lambda r: r[3] == 'R511') for n_, pts_ in polys): continue
      g.remove(lambda r: r[3] == 'R511')
      for n_, pts_ in polys: g.add(n_, BC, ('poly', pts_), 'R511', 'pad')
      tried += 1
      path, d = leg('CLKP', cv, P(pad('R511', '2')))
      if path: placed = (x, y, path); break
      if tried > int(opt.get('--r511tries', 60)): break
  if not placed: b.Save(B); raise SystemExit('no R511 spot (tried %d)' % tried)
  print('R511 at', placed[:2], flush=True)
  L['CLKP'] = round(lay_leg('CLKP', placed[2]), 2)
  pts['CLK'].insert(0, ('R', P(pad('R511', '1'))))
  for k in ('CLK', 'D0', 'D1'): route(k)
# 3. ESD taps: each U401/U402 pad joins its own line by the shortest path (top or bottom, one via allowed), after all the
#    lines are down, so the taps never decide the bus order. Goal = the nearest point of the line's bottom copper.
nr.ALLOW = {0, 2}
def seg_near(net, q):
    best = None
    for t in b.GetTracks():
        if t.GetNetname() != net or t.GetClass() == 'PCB_VIA' or t.GetLayer() != BC: continue
        a = (t.GetStart().x/1e6, t.GetStart().y/1e6); c = (t.GetEnd().x/1e6, t.GetEnd().y/1e6)
        dx, dy = c[0] - a[0], c[1] - a[1]; l2 = dx*dx + dy*dy
        u = 0 if l2 == 0 else max(0, min(1, ((q[0] - a[0])*dx + (q[1] - a[1])*dy)/l2))
        m = (round(a[0] + u*dx, 3), round(a[1] + u*dy, 3)); dd = math.dist(m, q)
        if not best or dd < best[0]: best = (dd, m)
    return best[1]
TAP = {}
for k in ('D1', 'D0', 'CLK', 'CMD', 'D3', 'D2'):
    ref, num = ESD[k]; e = P(pad(ref, num)); m = seg_near(NETS[k], e); net = NETS[k]
    win = (min(e[0], m[0]) - 3, min(e[1], m[1]) - 3, max(e[0], m[0]) + 3, max(e[1], m[1]) + 3)
    d = {}
    path = nr.astar(g, net, e, m, W, 0.05, win, (0,), (2,), nr.USB_KEEP, nr.USB_EXTRA, viacost=1.0, tol=0.04, max_it=2000000, diag=d)
    if not path: b.Save(B); raise SystemExit('no ESD tap for %s %s->%s %s' % (k, e, m, d))
    path[0] = (e[0], e[1], path[0][2]); path[-1] = (m[0], m[1], path[-1][2])
    path = nr.pull(g, net, nr.simplify(path), W)
    TAP[k] = (round(sum(math.dist(p_[:2], q_[:2]) for p_, q_ in zip(path, path[1:])), 2), sum(1 for p_, q_ in zip(path, path[1:]) if p_[2] != q_[2]))
    nr.emit(g, net, path, W)
print('ESD taps (mm, vias)', json.dumps(TAP), flush=True)
b.Save(B)
print(json.dumps(dict(bottom_lengths=L)))
