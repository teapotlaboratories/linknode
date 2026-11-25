"""T30: open a USB channel west of U100 pins 26/27 by re-placing the RTC crystal group and the VBUSDET/SARADC parts
(owner, 2026-11-22: "move the RTC corner"). Usage: python3 corner_place.py <board.kicad_pcb>
Reserved, kept free of the moved parts' courtyards:
  - the USB channel: a band 1.3 mm either side of the polyline U100 pins 26/27 -> west -> down to U2/U1;
  - exit lanes 2.4 mm long west of every left-side U100 signal pin (the fan-out strip).
Each part goes, greedy and in order, to the legal spot (0.25 mm grid, 4 rotations, top side, inside the corner box) with
the shortest connections: sum over its nets of the distance from its pad to the nearest other pad of that net
(the crystal is weighted to sit next to pins 20/21, its caps next to its pads). Routing on the affected nets is ripped up.
Prints the moves and the nets to re-route. Courtyard and copper checks are pre-checks; kicad-cli DRC is final."""
import sys, os, math, json, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(__file__))
from geomlib import Geo, pad_polys, dist, mm
BOARD = sys.argv[1]
b = pcbnew.LoadBoard(BOARD)
MOVE = ['Y502', 'C503', 'C504', 'R510', 'C507', 'TP501', 'R506', 'R507', 'C506']
WEIGHT = {'Y502': 4.0, 'C503': 2.0, 'C504': 2.0}
ABOVE = {'Y502', 'C503', 'C504', 'R510', 'C507', 'TP501', 'R507', 'C506'}   # their U100 pins (20-25) are above the channel: no crossing
U = b.FindFootprintByReference('U100'); pad = {p.GetNumber(): p for p in U.Pads() if p.GetNumber()}
P = lambda p: (p.GetPosition().x/1e6, p.GetPosition().y/1e6)
p26, p27 = P(pad['26']), P(pad['27'])
U1 = P([q for q in b.FindFootprintByReference('U1').Pads() if q.GetNumber() == '6'][0])
U2 = P([q for q in b.FindFootprintByReference('U2').Pads() if q.GetNumber() == '7'][0])
ymid = (p26[1] + p27[1])/2
CHANNEL = [(p26[0] - 0.4, ymid), (133.0, ymid), (U2[0] + 2.0, U2[1] - 2.5), (U1[0] + 1.0, U1[1] - 1.5)]
HALF = 1.3
RAIL = ('GND', 'VCC_3V3', 'VCC_1V8', 'VDD_0V9', 'VDD_ARM', 'VCC_DDR', '')
LANES = []
for q in U.Pads():
    if not q.GetNumber(): continue
    x, y = P(q); n = q.GetNetname()
    if abs(x - p26[0]) < 0.01 and n not in RAIL and not n.startswith('unconnected'):
        LANES.append((x - 0.4 - 2.4, y - 0.22, x - 0.4, y + 0.22))
BOX = (126.0, 136.5, 139.6, 157.0)          # where the moved parts may go (west of the fan-out strip)
nets_of = {r: set(q.GetNetname() for q in b.FindFootprintByReference(r).Pads()) for r in MOVE}
AFFECTED = set().union(*nets_of.values()) - set(RAIL)
# rip the affected nets (their routes follow the parts)
KEEP = []
for t in list(b.GetTracks()):
    if t.GetNetname() in AFFECTED and not t.IsLocked(): b.Remove(t); KEEP.append(t)
g = Geo(b, (BOX[0] - 2, BOX[1] - 2, 142, BOX[3] + 2))
g.remove(lambda r: r[3] in MOVE)
court = []
for fp in b.GetFootprints():
    if fp.IsFlipped() or fp.GetReference() in MOVE: continue
    c = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    if c.GetWidth() > 0: court.append((c.GetLeft()/1e6, c.GetTop()/1e6, c.GetRight()/1e6, c.GetBottom()/1e6))
def hit(box, others): return any(not (box[2] < o[0] or o[2] < box[0] or box[3] < o[1] or o[3] < box[1]) for o in others)
def in_channel(box):
    pts = [(box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3])]
    poly = ('poly', pts)
    return any(dist(('seg', a, c, HALF), poly) == 0.0 for a, c in zip(CHANNEL, CHANNEL[1:]))
def other_pads(net, ref):
    return [P(q) for fp in b.GetFootprints() if fp.GetReference() != ref for q in fp.Pads() if q.GetNetname() == net]
def cost(fp, ref):
    c = 0.0
    for q in fp.Pads():
        n = q.GetNetname()
        if n in RAIL: continue
        o = other_pads(n, ref)
        if o: c += min(math.dist(P(q), x) for x in o)
    return c*WEIGHT.get(ref, 1.0)
moves = {}
for ref in MOVE:
    fp = b.FindFootprintByReference(ref); orig = (fp.GetPosition(), fp.GetOrientationDegrees())
    best = None
    for xi in range(int((BOX[2]-BOX[0])/0.25) + 1):
        for yi in range(int((BOX[3]-BOX[1])/0.25) + 1):
            x, y = BOX[0] + 0.25*xi, BOX[1] + 0.25*yi
            for rot in (0, 90, 180, 270):
                fp.SetOrientationDegrees(rot); fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                c_ = fp.GetCourtyard(pcbnew.F_CrtYd).BBox(); box = (c_.GetLeft()/1e6, c_.GetTop()/1e6, c_.GetRight()/1e6, c_.GetBottom()/1e6)
                if box[0] < BOX[0] or box[2] > BOX[2] + 0.3 or box[1] < BOX[1] or box[3] > BOX[3]: continue
                if hit(box, court) or hit(box, LANES) or in_channel(box): continue
                if ref in ABOVE and box[3] > ymid - HALF: continue
                if not all(g.clear(('poly', pts), pcbnew.F_Cu, n2) for n2, pts, _ in pad_polys(fp)): continue
                k = cost(fp, ref)
                if best is None or k < best[0]: best = (k, x, y, rot, box)
    if not best:
        fp.SetPosition(orig[0]); fp.SetOrientationDegrees(orig[1]); print('NO SPOT for', ref, flush=True); continue
    k, x, y, rot, box = best
    fp.SetOrientationDegrees(rot); fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    court.append(box)
    for n2, pts, _ in pad_polys(fp): g.add(n2, pcbnew.F_Cu, ('poly', pts), ref, 'pad')
    moves[ref] = {'from': [round(orig[0].x/1e6, 2), round(orig[0].y/1e6, 2), orig[1]], 'to': [round(x, 2), round(y, 2), rot], 'cost_mm': round(k, 2)}
    print(ref, moves[ref], flush=True)
# the crystal keepouts (HDG p.41 item 11) follow Y502
KZ = []
for z in list(b.Zones()):
    if z.GetIsRuleArea() and 'Y502' in z.GetZoneName(): b.Remove(z); KZ.append(z)
def rule_area(name, rect, layers):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True); z.SetZoneName(name)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False); z.SetDoNotAllowZoneFills(False)
    ls = pcbnew.LSET()
    for L in layers: ls.AddLayer(L)
    z.SetLayerSet(ls); o = z.Outline(); o.NewOutline()
    for x_, y_ in ((rect[0], rect[1]), (rect[2], rect[1]), (rect[2], rect[3]), (rect[0], rect[3])): o.Append(mm(x_), mm(y_))
    b.Add(z)
y5 = b.FindFootprintByReference('Y502'); bb = y5.GetBoundingBox(False, False)
r = (bb.GetLeft()/1e6, bb.GetTop()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6)
rule_area('Keepout under Y502 (HDG p.41 item 11)', r, [pcbnew.In2_Cu, pcbnew.B_Cu])
ps = [q for q in y5.Pads() if q.GetNumber()]; xs = [P(q)[0] for q in ps]; ys = [P(q)[1] for q in ps]; cx, cy = P(y5.GetPosition()) if False else (y5.GetPosition().x/1e6, y5.GetPosition().y/1e6)
if max(xs) - min(xs) >= max(ys) - min(ys):
    lo = max(P(q)[0] + q.GetBoundingBox().GetWidth()/2e6 for q in ps if P(q)[0] < cx); hi = min(P(q)[0] - q.GetBoundingBox().GetWidth()/2e6 for q in ps if P(q)[0] > cx)
    rect = (lo + 0.15, r[1], hi - 0.15, r[3])
else:
    lo = max(P(q)[1] + q.GetBoundingBox().GetHeight()/2e6 for q in ps if P(q)[1] < cy); hi = min(P(q)[1] - q.GetBoundingBox().GetHeight()/2e6 for q in ps if P(q)[1] > cy)
    rect = (r[0], lo + 0.15, r[2], hi - 0.15)
if min(rect[2]-rect[0], rect[3]-rect[1]) > 0.3: rule_area('Keepout between Y502 pads (HDG p.41 item 11)', rect, [pcbnew.F_Cu])
b.Save(BOARD)
print(json.dumps({'moves': moves, 'ripped_nets': sorted(AFFECTED), 'channel': CHANNEL}, indent=1))
