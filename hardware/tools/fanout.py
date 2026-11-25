"""T31: re-create the U100 (RV1106) decoupling fan-out on a cleared board, parts left where they are (T29 placement).
Usage: python3 fanout.py <board.kicad_pcb>
- GND pins 37/57: a top stub into the exposed pad.
- Each supply-pin group: one via in the ring between the pin row and the exposed pad, nearest legal spot (same search as
  soc_tidy_decap.py), a 0.15 mm top stub from each pin's inner end, and a straight 0.2 mm bottom link from the via to the
  supply pad of each of the group's bottom-side parts when that link keeps clearance (the rest is left to netroute).
- Y501 (24 MHz) GND pads: a GND via just outside the crystal keepout (HDG p.41 item 10).
Clearance is checked with geomlib (rule-area keepouts included); kicad-cli DRC is the final check."""
import sys, os, math, json, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(__file__))
from geomlib import Geo, CU, mm
BOARD = sys.argv[1]
b = pcbnew.LoadBoard(BOARD)
U = b.FindFootprintByReference('U100'); CX, CY = U.GetPosition().x/1e6, U.GetPosition().y/1e6
g = Geo(b, (CX - 14, CY - 14, CX + 14, CY + 14))
F, B = pcbnew.F_Cu, pcbnew.B_Cu
VD, VH, STUB, BTW = 0.4, 0.2, 0.15, 0.2
pad = {p.GetNumber(): p for p in U.Pads() if p.GetNumber()}
def geom(num):
    p = pad[num]; x, y = p.GetPosition().x/1e6, p.GetPosition().y/1e6; dx, dy = x - CX, y - CY
    n = (-math.copysign(1, dx), 0.0) if abs(dx) > abs(dy) else (0.0, -math.copysign(1, dy))
    bb = p.GetBoundingBox(); half = max(bb.GetWidth(), bb.GetHeight())/2e6
    return (x, y), (x + n[0]*half, y + n[1]*half), n, (-n[1], n[0])
report = {'gnd_stubs': 0, 'vias': 0, 'links': 0, 'links_left': [], 'no_via': []}
for num in ('37', '57'):
    _, inner, n, _ = geom(num); g.add_track(inner, (inner[0] + n[0]*2.4, inner[1] + n[1]*2.4), 0.18, F, 'GND'); report['gnd_stubs'] += 1
GROUPS = [
 (['1'], ['C603']), (['10'], ['C610']), (['13'], ['C629']), (['19'], ['C604']), (['24'], ['C602']), (['28'], ['C630']),
 (['30'], ['C637']), (['31'], ['C625']), (['43'], ['C631']), (['49', '50'], ['C623']), (['51'], ['C611']),
 (['54', '55'], ['C612', 'C613', 'C619']), (['53'], ['C626', 'C628']), (['56'], ['C624']),
 (['61'], ['C632']), (['66'], ['C505', 'R503']), (['67'], ['C614']), (['70'], ['C627']), (['71'], ['C615', 'C620']),
 (['81'], ['C633']), (['82'], ['C616']), (['88'], ['C634']), (['96'], ['C601']), (['101'], ['C635']),
 (['102'], ['R605']), (['103'], ['C617']), (['108'], ['C636']), (['115'], ['C606', 'C607']), (['116'], ['C618']), (['52'], ['R604'])]
for pins, parts in GROUPS:
    net = pad[pins[0]].GetNetname(); gs = [geom(p) for p in pins]; n, tan = gs[0][2], gs[0][3]
    ax = sum(q[1][0] for q in gs)/len(gs); ay = sum(q[1][1] for q in gs)/len(gs)
    best = None
    for r in [0.55 + 0.05*k for k in range(24)]:
        for lat in [0.05*k for k in range(25)]:
            for sgn in (1, -1):
                vx, vy = ax + n[0]*r + tan[0]*lat*sgn, ay + n[1]*r + tan[1]*lat*sgn
                if max(abs(vx - CX), abs(vy - CY)) < 3.5 + VD/2 + 0.16 or not g.hole_ok(vx, vy, VH): continue
                if not all(g.clear(('pt', (vx, vy), VD/2), L, net) for L in CU): continue
                if not g.clear(('pt', (vx, vy), VD/2), F, net, ignore=lambda rr: rr[4] != 'pad', same_net_ok=False): continue   # not in a pad
                if not all(g.clear(('seg', q[1], (vx, vy), STUB/2), F, net) for q in gs): continue
                cost = r + 1.5*lat
                if best is None or cost < best[0]: best = (cost, vx, vy)
        if best and best[0] <= r + 0.05: break
    if not best: report['no_via'].append(pins); continue
    _, vx, vy = best
    g.add_via(vx, vy, net); [g.add_track(q[1], (vx, vy), STUB, F, net) for q in gs]; report['vias'] += 1
    for ref in parts:
        fp = b.FindFootprintByReference(ref)
        if not fp.IsFlipped(): continue
        tgt = [q for q in fp.Pads() if q.GetNetname() == net]
        if not tgt: continue
        q = min(tgt, key=lambda q: math.dist((q.GetPosition().x/1e6, q.GetPosition().y/1e6), (vx, vy)))
        pp = (q.GetPosition().x/1e6, q.GetPosition().y/1e6)
        if math.dist(pp, (vx, vy)) < 3.0 and g.clear(('seg', (vx, vy), pp, BTW/2), B, net, ignore=lambda rr, ref=ref: rr[3] == ref and rr[0] == net):
            g.add_track((vx, vy), pp, BTW, B, net); report['links'] += 1
        else: report['links_left'].append(ref)
# Y501 GND vias, just outside its keepout
y = b.FindFootprintByReference('Y501'); _yb = y.GetBoundingBox(False, False)
ybb = (_yb.GetLeft()/1e6, _yb.GetTop()/1e6, _yb.GetRight()/1e6, _yb.GetBottom()/1e6); yc = ((ybb[0]+ybb[2])/2, (ybb[1]+ybb[3])/2)
report['y501_vias'] = []
for p in y.Pads():
    if p.GetNetname() != 'GND': continue
    px, py = p.GetPosition().x/1e6, p.GetPosition().y/1e6; best = None
    for k in range(60):
        rr = 0.05*k
        for dx, dy in ((math.copysign(1, px-yc[0]), 0), (0, math.copysign(1, py-yc[1]))):
            vx = px + dx*(abs(px - (ybb[0] if dx < 0 else ybb[2])) + 0.25 + VD/2 + rr) if dx else px
            vy = py + dy*(abs(py - (ybb[1] if dy < 0 else ybb[3])) + 0.25 + VD/2 + rr) if dy else py
            if not g.hole_ok(vx, vy, VH) or not all(g.clear(('pt', (vx, vy), VD/2), L, 'GND') for L in CU): continue
            if not g.clear(('seg', (px, py), (vx, vy), 0.125), F, 'GND', ignore=lambda r_: r_[3] == 'Y501' and r_[0] == 'GND'): continue
            d = math.dist((px, py), (vx, vy))
            if best is None or d < best[0]: best = (d, vx, vy)
        if best: break
    if best:
        g.add_via(best[1], best[2], 'GND'); g.add_track((px, py), (best[1], best[2]), 0.25, F, 'GND'); report['y501_vias'].append(round(best[0], 2))
b.Save(BOARD)
print(json.dumps(report))
