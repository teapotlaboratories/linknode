"""T47 Section 3b: HaLow SDIO bus as hand-set lanes (owner, 2026-11-23: bottom over the 5 V plane with GND stitching vias;
no jagged routes). Runs on a board that already has the module-pad vias (t47_padfan.py, outside the module body).
Usage: python3 t47_sdiolanes.py <board.kicad_pcb> [--group north]
North group (CMD, D3, D2 -> the module's north-edge pads 21, 22, 23):
  top:    each pin straight north, then 45 degrees north-west; the turns are staggered so the lanes run 0.424 mm apart
          (pins are 0.35 mm apart); each lane drops through a via on its diagonal (vias staggered 0.4 mm along the bus,
          south of the module body);
  bottom: the same diagonal, then north under the module (x 137.75 / 138.174 / 138.599), one 45-degree corner west on
          three levels (y 101.725 / 101.301 / 100.877), each lane into its pad via (D2 straight in, D3 and CMD with one
          45-degree drop). Lanes are offsets of D2's path (mitred corners). Every piece is checked with geomlib."""
import sys, os, math, json, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import netroute as nr
from geomlib import Geo, CU, bbox
from geomlib import dist as gdist
B = sys.argv[1]; b = pcbnew.LoadBoard(B)
F, BC = pcbnew.F_Cu, pcbnew.B_Cu; W = 0.12
_eb = b.GetBoardEdgesBoundingBox(); g = Geo(b, (_eb.GetLeft()/1e6 - 1, _eb.GetTop()/1e6 - 1, _eb.GetRight()/1e6 + 1, _eb.GetBottom()/1e6 + 1))
def pad(ref, num): return [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
def P(p): return (round(p.GetPosition().x/1e6, 4), round(p.GetPosition().y/1e6, 4))
def blockers(net, G, L):
    return [(r[0][-16:], r[3], r[4], round(gdist(G, r[1]), 3)) for r in g.near(L, bbox(G), 0.8) if r[0] != net and gdist(G, r[1]) < max(g.ncl(net), g.ncl(r[0])) + 0.01]
def check(net, pts, L):
    bad = []
    for a, c in zip(pts, pts[1:]):
        if math.dist(a, c) < 1e-6: continue
        G = ('seg', a, c, W/2)
        if not (g.clear(G, L, net) and nr.usb_ok(g, G, L, net)): bad.append((a, c, blockers(net, G, L)))
    return bad
def lay(net, pts, L):
    for a, c in zip(pts, pts[1:]):
        if math.dist(a, c) > 1e-6: g.add_track(a, c, W, L, net)
def via_bad(net, v):
    G = ('pt', v, 0.2)
    ok = g.hole_ok(v[0], v[1], 0.2) and all(g.clear(G, L, net) for L in CU) and all(not (r[4] == 'pad' and gdist(G, r[1]) < 0.09) for L in (F, BC) for r in g.near(L, bbox(G), 0.6))
    return None if ok else [(r[0][-16:], r[3], r[4], round(gdist(G, r[1]), 3)) for L in CU for r in g.near(L, bbox(G), 0.8) if r[0] != net and gdist(G, r[1]) < max(g.ncl(net), g.ncl(r[0])) + 0.01]
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
def cut(poly, s):
    """split a polyline at arc length s -> (head points, point, tail points)"""
    acc = 0.0
    for i, (a, c) in enumerate(zip(poly, poly[1:])):
        l = math.dist(a, c)
        if acc + l >= s:
            t = (s - acc)/l; q = (round(a[0] + (c[0] - a[0])*t, 4), round(a[1] + (c[1] - a[1])*t, 4))
            return poly[:i + 1] + [q], q, [q] + poly[i + 1:]
        acc += l
    raise ValueError('cut beyond end')
N = {'D2': '/HaLow/HALOW_SDIO_D2', 'D3': '/HaLow/HALOW_SDIO_D3', 'CMD': '/HaLow/HALOW_SDIO_CMD'}
PIN = {'D2': '114', 'D3': '113', 'CMD': '112'}
PADV = {'CMD': (133.95, 101.725), 'D3': (135.45, 101.725), 'D2': (136.95, 101.725)}
SP = 0.6/math.sqrt(2)                                  # lane spacing (0.424 mm)
# North group v2 (2026-11-23): drop to the bottom at the pins, so the west group can cross over on top south of the module.
# Vias west of R513 and clear of C606's GND pad.
VIA = {'D2': (141.4, 122.3), 'D3': (142.0, 122.3), 'CMD': (142.6, 122.3)}   # one row, 0.6 mm apart: on top lines x - y and
TURN = {'D2': 123.15, 'D3': 122.9, 'CMD': 122.65}     # bottom lines x + y 0.6 apart -> 0.424 mm between a via and its neighbour's lane
X1 = 142.75; Y1 = 115.3; XN = 137.75                    # D2: north run east of RN701, NW above it, north run under the module
v2 = VIA['D2']
BASE = [v2, (X1, round(v2[1] - (X1 - v2[0]), 4)), (X1, Y1), (XN, round(Y1 - (X1 - XN), 4)), (XN, 102.2),
        (round(XN - 0.475, 4), 101.725), PADV['D2']]
OFF = {'D2': 0.0, 'D3': SP, 'CMD': 2*SP}
report = {}
for k in (() if '--west' in sys.argv else ('D2', 'D3', 'CMD')):
    net = N[k]; pin = P(pad('U100', PIN[k])); v = VIA[k]
    top = [pin, (pin[0], TURN[k]), v]
    assert abs((pin[0] - v[0]) - (TURN[k] - v[1])) < 1e-6, (k, 'stub not 45 degrees')
    lp = offset(BASE, OFF[k])
    lvl = lp[-2][1]; pv = PADV[k]; dyv = pv[1] - lvl
    end = [(round(pv[0] + dyv, 4), lvl), pv] if dyv > 1e-6 else [pv]
    bot = [v] + lp[1:-1] + end
    pb = check(net, top, F) + check(net, bot, BC); vb = via_bad(net, v)
    if pb or vb: b.Save(B + '.failed.kicad_pcb'); raise SystemExit('blocked %s: %s' % (k, json.dumps((pb[:4], vb))))
    lay(net, top, F); g.add_via(v[0], v[1], net, d=0.4, h=0.2); lay(net, bot, BC)
    report[k] = dict(top=round(sum(math.dist(a, c) for a, c in zip(top, top[1:])), 2), bottom=round(sum(math.dist(a, c) for a, c in zip(bot, bot[1:])), 2))
if '--west' not in sys.argv:
    b.Save(B); print(json.dumps(report))

# ------------------------------------------------------------------ west group (CLK, D0, D1 -> the module's west-edge pads)
# Needs R513 off the pins: it moves to the bottom, upright, inline on the clock lane under the module's west part.
if '--west' in sys.argv:
    b2 = pcbnew.LoadBoard(B)
    _K = []
    CLKP = 'Net-(U100SDIO (VCCIO5)-SDIO_CLK_M0{slash}GPIO2_A2)'; CLKN = '/HaLow/HALOW_SDIO_CLK'
    for t in list(b2.GetTracks()):
        if t.GetNetname() == CLKP: b2.Remove(t); _K.append(t)                # 3a stub pin 111 -> R513 (re-laid here)
    r = b2.FindFootprintByReference('R513'); RX, RY = 134.65, 112.5
    if not r.IsFlipped(): r.Flip(r.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    r.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(RX), pcbnew.FromMM(RY)))
    for rot in (90, 270):
        r.SetOrientationDegrees(rot)
        pp = {p.GetNumber(): p.GetPosition().y/1e6 for p in r.Pads()}
        if pp['2'] > pp['1']: break                                           # pad 2 (pin side) south, pad 1 north
    b2.Save(B)
    b = pcbnew.LoadBoard(B) if False else b2
    g = Geo(b, (_eb.GetLeft()/1e6 - 1, _eb.GetTop()/1e6 - 1, _eb.GetRight()/1e6 + 1, _eb.GetBottom()/1e6 + 1))
    def P2(ref, num): return P(pad(ref, num))
    r2, r1 = P2('R513', '2'), P2('R513', '1')
    W_ = {'CLK': CLKP, 'D0': '/HaLow/HALOW_SDIO_D0', 'D1': '/HaLow/HALOW_SDIO_D1'}
    pin = {'CLK': P2('U100', '111'), 'D0': P2('U100', '110'), 'D1': P2('U100', '109')}
    # top: north, 45 deg NW onto the level, west to the via
    TT = {'CLK': (121.6, 120.95, (138.85, 120.95)), 'D0': (121.31, 120.5, (137.557, 120.5)), 'D1': (121.02, 120.05, (136.4, 120.05))}   # vias on each lane's 45-degree line
    # bottom: from the via (NW onto the bottom level if needed), west, NW onto the north run, north, 45 deg, west on the final level
    BL = {'CLK': (120.95, 138.85, 134.65, 107.425), 'D0': (120.5, 137.557, 134.05, 108.217), 'D1': (120.05, 136.4, 133.55, 109.925)}   # D1 level = its pad via's height; it runs through R704 pad 2 (the tap)
    END = {'D1': [(130.2, 109.925)], 'D0': [(130.408, 108.217), (130.2, 108.425)], 'CLK': [(130.2, 107.425)]}      # straight in at the via's height, clear of C122; R701 joins by a tap
    rep = {}
    for k in ('CLK', 'D0', 'D1'):
        p0 = pin[k]; ty, lv, v = TT[k]
        top = [p0, (p0[0], ty), (round(p0[0] - (ty - lv), 4), lv), v]
        bl, xw, xn, fl = BL[k]
        bot = [v]
        if abs(v[1] - bl) > 1e-6: bot.append((round(v[0] - (v[1] - bl), 4), bl))
        bot += [(xw, bl), (xn, round(bl - (xw - xn), 4)), (xn, round(fl + 0.45, 4)), (round(xn - 0.45, 4), fl)] + END[k]
        if k == 'CLK':          # split at R513: pin-side net up to pad 2, HALOW_SDIO_CLK from pad 1
            i_ = [j for j, q in enumerate(bot) if abs(q[0] - xn) < 1e-6 and q[1] > r2[1]][-1]
            botA = bot[:i_ + 1] + [r2]; botB = [r1] + bot[i_ + 1:]
            segs = [(CLKP, top, F), (CLKP, botA, BC), (CLKN, botB, BC)]
        else:
            segs = [(W_[k], top, F), (W_[k], bot, BC)]
        for net, pts, L in segs:
            pb = check(net, pts, L)
            if pb: b.Save(B + '.failed.kicad_pcb'); raise SystemExit('blocked %s: %s' % (k, json.dumps(pb[:4])))
        vb = via_bad(W_[k], v)
        if vb: b.Save(B + '.failed.kicad_pcb'); raise SystemExit('via blocked %s: %s' % (k, json.dumps(vb)))
        for net, pts, L in segs: lay(net, pts, L)
        g.add_via(v[0], v[1], W_[k], d=0.4, h=0.2)
        rep[k] = round(sum(math.dist(a, c) for _, pts, _ in segs for a, c in zip(pts, pts[1:])), 2)
    b.Save(B)
    print(json.dumps(dict(west=rep, R513=(RX, RY))))
