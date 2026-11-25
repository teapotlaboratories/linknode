"""T47 Section 3a (2026-11-23): the two RV1106 crystals, routed by hand-set geometry before anything else (Rockchip
HDG V1.1 §3.2 item 11 p.41: crystal traces short, nothing between or under the crystal pads; keep-outs exist on the board).
Usage: python3 t47_xtal.py <board.kicad_pcb>
Y502 32.768 kHz (left side of the RV1106, pins 20 XOUT / 21 XIN), all on top, no vias:
  XOUT: pin 20 straight west into Y502 pad 2; pad 2 up, 45 degrees, into C504 pad 1.
  XIN:  pin 21 west, 45 degrees down below the keep-out between the crystal pads, west under the crystal, 45 degrees up
        into pad 1; pad 1 straight up into C503 pad 1.
Y501 24 MHz (right side, pins 69 XOUT / 68 XIN), after the cluster re-arrangement (see below):
  XIN:  pin 68 straight east into Y501 pad 3 (top); one via off that line to C502 + R502 on the bottom.
  XOUT: pin 69 east, 45 degrees up, along the crystal's top edge into R501 (upright, east of the crystal); R501's other
        pad down the east side, 45 degrees, into Y501 pad 1; C501 straight below pad 1; R502 pad 1 up through one via.
  Vias are searched (0.05 mm grid); bottom legs use the netroute A*. Every segment is checked with geomlib."""
import sys, os, math, json, itertools, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import netroute as nr
from geomlib import Geo, CU, bbox
from geomlib import dist as gdist
B = sys.argv[1]; b = pcbnew.LoadBoard(B)
# TP501 (RECOVERY test point, SARADC_IN0) sat on top between the RV1106's 32 kHz pins and Y502: both crystal traces
# would have had to cross the CC-sense / recovery pin exits. It moves to the bottom, 2.8 mm from its R510/C507 (bottom
# parts), where it is reached without a via (placement change, for the owner's approval with group 3a).
_tp = b.FindFootprintByReference('TP501')
if '--keep-tp501' not in sys.argv and not _tp.IsFlipped():
    _tp.Flip(_tp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT); _tp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(132.1), pcbnew.FromMM(132.5)))
# Y501 cluster re-arranged (owner, 2026-11-23, option 1): XOUT (pin 69) sits above XIN (pin 68) but its series resistor
# R501 sat below the crystal and XIN's load cap C502 above it, so XOUT had to cross XIN. Now:
#   R501 upright on the crystal's east side (in the gap before the ESP32-C5): XOUT runs along the crystal's top edge to it;
#   C502 to the bottom, flat, just below R502 (bottom already, not moved): both reach XIN through one via; the bottom leg
#   runs west round C622 (10 uF, VCC_DDR) because the 0.23 mm gap between C622 and the crystal's keep-out is too narrow.
#   Y501 itself does not move.
#   Y501 pad 2's GND stub + via to the east (Section 1) is removed: R501 takes that spot; pad 2 still reaches GND through
#   the top pour (and pad 4 keeps its GND via).
C502_AT = tuple(float(v) for v in (sys.argv[sys.argv.index('--c502') + 1].split(',') if '--c502' in sys.argv else ('152.0', '139.0')))
R502_AT = tuple(float(v) for v in (sys.argv[sys.argv.index('--r502') + 1].split(',') if '--r502' in sys.argv else ('152.025', '137.955')))
KEEP = []
_r501 = b.FindFootprintByReference('R501'); _c502 = b.FindFootprintByReference('C502')
_r501.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(154.35), pcbnew.FromMM(133.68)))   # top pad at y 133.17: XOUT 0.17 mm from the GND pad (Power class 0.15)
for _rot in (90, 270):
    _r501.SetOrientationDegrees(_rot)
    _p = {p.GetNumber(): p.GetPosition().y for p in _r501.Pads()}
    if _p['2'] < _p['1']: break                                 # pad 2 (XOUT) on top, pad 1 (C501 net) below
if not _c502.IsFlipped(): _c502.Flip(_c502.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
_c502.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(C502_AT[0]), pcbnew.FromMM(C502_AT[1])))
C502_ROT = float(sys.argv[sys.argv.index('--c502rot') + 1]) if '--c502rot' in sys.argv else 0.0
for _rot in ((C502_ROT,) if C502_ROT is not None else (90, 270)):  # default upright, XIN pad on top
    _c502.SetOrientationDegrees(_rot)
    _p = {p.GetNumber(): p.GetPosition().y for p in _c502.Pads()}
    if _p['1'] < _p['2']: break
_r502 = b.FindFootprintByReference('R502')                     # bottom already; beside C502, XIN pad facing it
_r502.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(R502_AT[0]), pcbnew.FromMM(R502_AT[1])))
for _rot in (0, 180):
    _r502.SetOrientationDegrees(_rot)
    _p = {p.GetNumber(): p.GetPosition().x for p in _r502.Pads()}
    if _p['2'] < _p['1']: break                                 # pad 2 (XIN) west, pad 1 (C501 net) east
for _t in list(b.GetTracks()):
    if _t.GetNetname() != 'GND': continue
    _q = (_t.GetPosition().x/1e6, _t.GetPosition().y/1e6) if _t.GetClass() == 'PCB_VIA' else None
    _ends = [(_t.GetStart().x/1e6, _t.GetStart().y/1e6), (_t.GetEnd().x/1e6, _t.GetEnd().y/1e6)]
    if (_q and math.dist(_q, (154.0, 134.1)) < 0.02) or (_t.GetClass() == 'PCB_TRACK' and any(math.dist(e, (154.0, 134.1)) < 0.02 for e in _ends)):
        b.Remove(_t); KEEP.append(_t)
_eb = b.GetBoardEdgesBoundingBox(); EBOX = (_eb.GetLeft()/1e6 - 1, _eb.GetTop()/1e6 - 1, _eb.GetRight()/1e6 + 1, _eb.GetBottom()/1e6 + 1)
F, BC = pcbnew.F_Cu, pcbnew.B_Cu
W = 0.12
g = Geo(b, EBOX)
def P(p): return (round(p.GetPosition().x/1e6, 4), round(p.GetPosition().y/1e6, 4))
def pad(ref, num): return [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
def NET(ref, num): return pad(ref, num).GetNetname()
made = []
def ok_path(net, pts, L=F):
    return all(g.clear(('seg', a, c, W/2), L, net) for a, c in zip(pts, pts[1:]) if math.dist(a, c) > 1e-6)
def lay(net, pts, L=F):
    if not ok_path(net, pts, L): raise SystemExit('blocked %s %s' % (net, pts))
    for a, c in zip(pts, pts[1:]):
        if math.dist(a, c) > 1e-6: made.append(g.add_track(a, c, W, L, net))
    return sum(math.dist(a, c) for a, c in zip(pts, pts[1:]))
def via_ok(x, y, net, r=0.2):
    if not (g.hole_ok(x, y, 0.2) and all(g.clear(('pt', (x, y), r), Lc, net) for Lc in CU)): return False
    G = ('pt', (x, y), r)
    for Lc in (F, BC):
        for rec in g.near(Lc, bbox(G), 0.6):
            if rec[4] == 'pad' and rec[0] == net and gdist(G, rec[1]) < 0.09: return False
    return True
L = {}
# ------------------------------------------------------------------ Y502 32.768 kHz
p20, p21 = P(pad('U100', '20')), P(pad('U100', '21'))
y1, y2 = P(pad('Y502', '1')), P(pad('Y502', '2'))
c3, c4 = P(pad('C503', '1')), P(pad('C504', '1'))
XO, XI = NET('U100', '20'), NET('U100', '21')
h2 = pad('Y502', '2').GetBoundingBox().GetHeight()/2e6; h1 = pad('Y502', '1').GetBoundingBox().GetHeight()/2e6
L['RTC XOUT pin-pad'] = lay(XO, [p20, (y2[0], p20[1])])                       # pin 20's y lies inside pad 2
top2 = y2[1] - h2
L['RTC XOUT pad-C504'] = lay(XO, [y2, (y2[0], c4[1] + (y2[0] - c4[0])), c4])
ylow = 131.38 + 0.06 + 0.16                                                   # below the keep-out between the pads
xs = 135.6                                                                    # leave the pin column first
L['RTC XIN pin-pad'] = lay(XI, [p21, (xs, p21[1]), (xs - (ylow - p21[1]), ylow), (y1[0] + (ylow - (y1[1] + h1 - 0.1)), ylow), (y1[0], y1[1] + h1 - 0.1), y1])
L['RTC XIN pad-C503'] = lay(XI, [y1, (y1[0], c3[1]), c3])
# ------------------------------------------------------------------ Y501 24 MHz
p68, p69 = P(pad('U100', '68')), P(pad('U100', '69'))
y3, y1p = P(pad('Y501', '3')), P(pad('Y501', '1'))
r1t, r1b = P(pad('R501', '2')), P(pad('R501', '1'))                         # top (XOUT), bottom (C501 net)
c1 = P(pad('C501', '1')); r2x, r2c = P(pad('R502', '2')), P(pad('R502', '1')); cx = P(pad('C502', '1'))
SI, SO, SC = NET('U100', '68'), NET('U100', '69'), NET('Y501', '1')
L['SOC XIN pin-Y501'] = lay(SI, [(p68[0], y3[1]), y3])                        # pin 68's y range holds Y501 pad 3's y
yo = r1t[1]                                                                   # XOUT along the crystal's top edge
L['SOC XOUT pin-R501'] = lay(SO, [p69, (149.4, p69[1]), (149.4 + (p69[1] - yo), yo), r1t])
w1 = y1p[0] + 0.55                                                            # into pad 1 from the east
L['SOC XOUT R501-Y501'] = lay(SC, [r1b, (r1b[0], y1p[1] - (r1b[0] - w1)), (w1, y1p[1]), y1p])
L['SOC XOUT Y501-C501'] = lay(SC, [c1, (c1[0], y1p[1] + 0.6)])
def grid(cx_, cy_, rx, ry):
    for i_ in range(int(2*rx/0.05) + 1):
        for j_ in range(int(2*ry/0.05) + 1): yield (round(cx_ - rx + i_*0.05, 3), round(cy_ - ry + j_*0.05, 3))
def leg(net, a, c, la, lc):
    gx0 = math.ceil((a[0] - min(a[0], c[0]) + 3)/0.05); gy0 = math.ceil((a[1] - min(a[1], c[1]) + 3)/0.05)
    win = (a[0] - gx0*0.05, a[1] - gy0*0.05, max(a[0], c[0]) + 3, max(a[1], c[1]) + 3)
    pth = nr.astar(g, net, a, c, W, 0.05, win, la, lc, viacost=2.0, tol=0.04, max_it=400000)
    if not pth: return None
    pth[0] = (a[0], a[1], pth[0][2]); pth[-1] = (c[0], c[1], pth[-1][2])
    return nr.pull(g, net, nr.simplify(pth), W)
def plen(pth): return sum(math.dist(p[:2], q[:2]) for p, q in zip(pth, pth[1:])) + sum(1.0 for p, q in zip(pth, pth[1:]) if p[2] != q[2])
# XIN via on a short stub off the XIN line, then a bottom leg to C502/R502 (bottom)
best = None
for v in grid(149.6, 134.65, 0.3, 0.3):
    stub = [(v[0], y3[1]), v]
    if not via_ok(v[0], v[1], SI) or not ok_path(SI, stub): continue
    g.add_via(v[0], v[1], SI, d=0.4, h=0.2, tag='try'); lg = leg(SI, v, cx, (2,), (2,)); g.remove(lambda r: r[3] == 'try')
    if lg and (best is None or plen(lg) + math.dist(*stub) < best[0]): best = (plen(lg) + math.dist(*stub), v, stub, lg)
if not best: raise SystemExit('no XIN via to C502/R502')
_, v, stub, lg = best
lay(SI, stub); made.append(g.add_via(v[0], v[1], SI, d=0.4, h=0.2)); nr.emit(g, SI, lg, W, made); L['SOC XIN via-C502'] = best[0]
lg = leg(SI, cx, r2x, (2,), (2,))                                            # C502 to R502 on the bottom
if not lg: raise SystemExit('no C502-R502 link')
nr.emit(g, SI, lg, W, made); L['SOC XIN C502-R502'] = plen(lg)
# R502 pad 1 (bottom) to the C501 net (top): one via
lg = leg(SC, r2c, c1, (2,), (0,))
if not lg: raise SystemExit('no R502-C501 link')
nr.emit(g, SC, lg, W, made); L['SOC R502-C501'] = plen(lg)
_seen = set()                                                                 # an A* leg that starts on a via spot can emit
for _t in list(b.GetTracks()):                                                # a second via there: keep one per spot and net
    if _t.GetClass() != 'PCB_VIA': continue
    _k = (_t.GetNetname(), round(_t.GetPosition().x/1e6, 3), round(_t.GetPosition().y/1e6, 3))
    if _k in _seen: b.Remove(_t); KEEP.append(_t)
    else: _seen.add(_k)
b.Save(B)
print(json.dumps({k: round(v, 2) for k, v in L.items()}))
