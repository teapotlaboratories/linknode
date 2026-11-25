"""T53 (owner, 2026-11-24): the HaLow SDIO bus at the proper size, 50 ohm (0.17 mm on the JLC 3313 outer layers) with a
gap of at least 2 x width (Rockchip HDG V1.1 Table 3-1, p.47): lane pitch SP = 0.51 mm. Same topology as t47_sdiolanes.py
(T47 3b, kept as the record of the 0.12 mm build), with every lane position derived from SP:
  north group (CMD, D3, D2 -> module pads 21-23): top stub from each pin north then 45 deg NW into a via row at y 122.3
      (vias SP*sqrt2 apart, so the stubs' diagonals and the bottom lanes are SP apart); bottom lanes are offsets of D2's
      path: NE, north east of RN701, NW above it, north under the module, 45 deg west into the pad vias.
  west group (CLK, D0, D1 -> module pads 18-16): top from the pins north, 45 deg NW onto three levels SP apart, west to
      vias on each lane's own NW line; bottom NW to north runs SP apart, north, 45 deg west into the pad vias. R513 (22 ohm
      clock series) is flipped to the bottom inline on the clock's north run, as in the T47 copy.
Usage: python3 t53_sdiolanes.py <board.kicad_pcb> north|west   (the module-pad vias must exist: t47_padfan.py)
Every segment and via is checked with geomlib before it is laid; stops on the first conflict (<board>.failed.kicad_pcb)."""
import sys, os, math, json, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import netroute as nr
from geomlib import Geo, CU, bbox
from geomlib import dist as gdist
B, MODE = sys.argv[1], sys.argv[2]
F, BC = pcbnew.F_Cu, pcbnew.B_Cu
W = float(os.environ.get('W', 0.17)); SP = float(os.environ.get('SP', 0.51)); S2 = math.sqrt(2)
b = pcbnew.LoadBoard(B); KEEP = []
FP = {f.GetReference(): f for f in b.GetFootprints()}
def pad(ref, num): return [p for p in FP[ref].Pads() if p.GetNumber() == num][0]
def P(p): return (round(p.GetPosition().x/1e6, 4), round(p.GetPosition().y/1e6, 4))
def R(q): return (round(q[0], 4), round(q[1], 4))
CLKP = 'Net-(U100SDIO (VCCIO5)-SDIO_CLK_M0{slash}GPIO2_A2)'
if not FP['R513'].IsFlipped():                       # first run (north): R513 leaves the pins, its 3a stub goes
    for t in list(b.GetTracks()):
        if t.GetNetname() == CLKP: b.Remove(t); KEEP.append(t)          # 3a stub pin 111 -> R513 (re-laid by 'west')
    r = FP['R513']; RX, RY = 134.65, 112.5
    if not r.IsFlipped(): r.Flip(r.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    r.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(RX), pcbnew.FromMM(RY)))
    for rot in (90, 270):
        r.SetOrientationDegrees(rot)
        if {p.GetNumber(): p.GetPosition().y for p in r.Pads()}['2'] > {p.GetNumber(): p.GetPosition().y for p in r.Pads()}['1']: break
_eb = b.GetBoardEdgesBoundingBox(); g = Geo(b, (_eb.GetLeft()/1e6 - 1, _eb.GetTop()/1e6 - 1, _eb.GetRight()/1e6 + 1, _eb.GetBottom()/1e6 + 1))
def blockers(net, G, L):
    return [(r[0][-16:], r[3], r[4], round(gdist(G, r[1]), 3)) for r in g.near(L, bbox(G), 0.8) if r[0] != net and gdist(G, r[1]) < max(g.ncl(net), g.ncl(r[0])) + 0.01]
def check(net, pts, L):
    bad = []
    for a, c in zip(pts, pts[1:]):
        if math.dist(a, c) < 1e-6: continue
        G = ('seg', a, c, W/2)
        if not (g.clear(G, L, net) and nr.usb_ok(g, G, L, net)): bad.append((a, c, 'F' if L == F else 'B', blockers(net, G, L)))
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
    return [R(q) for q in out]
def fail(msg): b.Save(B + '.failed.kicad_pcb'); raise SystemExit(msg)
def plen(pts): return sum(math.dist(a, c) for a, c in zip(pts, pts[1:]))
report = {}
if MODE == 'north':
    N = {'D2': '/HaLow/HALOW_SDIO_D2', 'D3': '/HaLow/HALOW_SDIO_D3', 'CMD': '/HaLow/HALOW_SDIO_CMD'}
    PIN = {'D2': '114', 'D3': '113', 'CMD': '112'}
    PADV = {'CMD': (133.95, 101.725), 'D3': (135.45, 101.725), 'D2': (136.95, 101.725)}
    VY = 122.3; VX0 = float(os.environ.get('VX0', 141.4))
    X1 = float(os.environ.get('X1', 142.75)); Y1 = 115.3; XN = float(os.environ.get('XN', 137.75))
    VIA = {k: (R((VX0 + i*SP*S2, VY))) for i, k in enumerate(('D2', 'D3', 'CMD'))}
    v2 = VIA['D2']
    BASE = [v2, (X1, round(v2[1] - (X1 - v2[0]), 4)), (X1, Y1), (XN, round(Y1 - (X1 - XN), 4)), (XN, 102.2),
            (round(XN - 0.475, 4), 101.725), PADV['D2']]
    for i, k in enumerate(('D2', 'D3', 'CMD')):
        net = N[k]; pin = P(pad('U100', PIN[k])); v = VIA[k]
        turn = round(v[1] + (pin[0] - v[0]), 4)
        top = [pin, (pin[0], turn), v]
        lp = offset(BASE, i*SP); lvl = lp[-2][1]; pv = PADV[k]; dyv = pv[1] - lvl
        end = [(round(pv[0] + dyv, 4), lvl), pv] if dyv > 1e-6 else [pv]
        bot = [v] + lp[1:-1] + end
        pb = check(net, top, F) + check(net, bot, BC); vb = via_bad(net, v)
        if pb or vb: fail('blocked %s: %s' % (k, json.dumps((pb[:4], vb))))
        lay(net, top, F); g.add_via(v[0], v[1], net, d=0.4, h=0.2); lay(net, bot, BC)
        report[k] = dict(top=round(plen(top), 2), bottom=round(plen(bot), 2), via=v)
else:
    CLKN = '/HaLow/HALOW_SDIO_CLK'
    r2, r1 = P(pad('R513', '2')), P(pad('R513', '1'))
    NW_ = {'CLK': CLKP, 'D0': '/HaLow/HALOW_SDIO_D0', 'D1': '/HaLow/HALOW_SDIO_D1'}
    pin = {'CLK': P(pad('U100', '111')), 'D0': P(pad('U100', '110')), 'D1': P(pad('U100', '109'))}
    TY0 = float(os.environ.get('TY0', 122.15)); XG = float(os.environ.get('XG', 0.03));   # XG: extra CLK-D0 gap for R513's pads
    LV0 = float(os.environ.get('LV0', 121.0)); XW0 = 138.85 + (LV0 - 120.95); XN0 = 134.65
    FL = {'CLK': 107.425, 'D0': 108.217, 'D1': 109.925}
    END = {'D1': [(130.2, 109.925)], 'D0': [(130.408, 108.217), (130.2, 108.425)], 'CLK': [(130.2, 107.425)]}
    dtop = pin['CLK'][0] - TY0; dbot = XW0 - LV0                       # the CLK lane's top and bottom NW lines: x - y
    for i, k in enumerate(('CLK', 'D0', 'D1')):
        p0 = pin[k]; lv = round(LV0 - i*SP, 4); ty = round(p0[0] - (dtop + i*SP*S2), 4)
        xw = round(lv + dbot - i*SP*S2, 4); v = (xw, lv); xn = round(XN0 - i*SP - (XG if i else 0.0), 4); fl = FL[k]
        top = [p0, (p0[0], ty), (round(p0[0] - (ty - lv), 4), lv), v]
        bot = [v, (xn, round(lv - (xw - xn), 4)), (xn, round(fl + 0.45, 4)), (round(xn - 0.45, 4), fl)] + END[k]
        if k == 'CLK':          # split at R513: pin-side net up to pad 2, HALOW_SDIO_CLK from pad 1
            i_ = [j for j, q in enumerate(bot) if abs(q[0] - xn) < 1e-6 and q[1] > r2[1]][-1]
            segs = [(CLKP, top, F), (CLKP, bot[:i_ + 1] + [r2], BC), (CLKN, [r1] + bot[i_ + 1:], BC)]
        else:
            segs = [(NW_[k], top, F), (NW_[k], bot, BC)]
        pb = [x for net, pts, L in segs for x in check(net, pts, L)]
        if pb: fail('blocked %s: %s' % (k, json.dumps(pb[:4])))
        vb = via_bad(NW_[k], v)
        if vb: fail('via blocked %s %s: %s' % (k, v, json.dumps(vb)))
        for net, pts, L in segs: lay(net, pts, L)
        g.add_via(v[0], v[1], NW_[k], d=0.4, h=0.2)
        report[k] = dict(len=round(sum(plen(pts) for _, pts, _ in segs), 2), via=v, turn=ty, north_x=xn)
b.Save(B)
print(json.dumps(report))
