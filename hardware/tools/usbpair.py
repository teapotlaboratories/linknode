"""T30: USB2 D+/D- as a coupled 90-ohm pair (Rockchip HDG 3.3.3 p.48: skew < 30 mil, <= 6 vias, > 20 mil to other signals).
Usage: python3 usbpair.py <board.kicad_pcb>
1. Rip up the four USB nets (SoC side U100 -> R508/R509, connector side R508/R509 -> U2 BC1.2 pins and U1 ESD).
2. Place R509 (D-) and R508 (D+) as a stacked pair close to U100 pins 26/27 (series R near the transmitter, HDG p.41),
   pad 1 (SoC side) toward the chip, D- above D+ so the pair keeps its order down to U1 (D- pin 6 west, D+ pin 4 east).
3. SoC side: one short route per line, pin -> pad 1.
4. Connector side: A* on the pair centreline (F.Cu over the In1 GND plane), cleared for the whole pair plus 0.5 mm to
   other tracks; then offset +-0.141 mm into two 0.155 mm lines (gap 0.127 mm, the USB90 class), fanned into R508/R509
   pad 2 and U1 pins 4/6.
5. Stubs to U2 pins 6 (D+) / 7 (D-) (BC1.2 detection); the one that must cross the pair drops to In2 through vias.
Pre-checked with geomlib; kicad-cli DRC is the final check. Prints lengths and skew."""
import sys, math, heapq, json, traceback, os, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(__file__))
from geomlib import Geo, pad_polys, dist, mm, CU, ssd
import netroute as nr
BOARD = sys.argv[1]
b = pcbnew.LoadBoard(BOARD)
SDP, SDM, DP, DM = 'Net-(U100System-USB_DP)', 'Net-(U100System-USB_DM)', '/SoC/USB_DP', '/SoC/USB_DM'
PAIR = {SDP, SDM, DP, DM}
W, GAP = 0.155, 0.130; S = W + GAP; HALF = S/2 + W/2      # built at 0.130 mm so corner rounding stays above the 0.127 mm DRU minimum
SPACE_EXTRA = 0.35            # class 0.15 + 0.35 = 0.5 mm to other tracks (HDG > 20 mil)
F, IN2 = pcbnew.F_Cu, pcbnew.In2_Cu
KEEP = []
for t in list(b.GetTracks()):
    if t.GetNetname() in PAIR: b.Remove(t); KEEP.append(t)
# nets that crowd the USB corridor on F.Cu: rip their unlocked routing, re-route after the pair (step 6)
ZONE = pcbnew.BOX2I(pcbnew.VECTOR2I(mm(122), mm(142)), pcbnew.VECTOR2L(mm(20), mm(27)))
YIELD = set()
for t in b.GetTracks():
    n = t.GetNetname()
    if n in PAIR or n in ('GND', 'VCC_1V8', 'VCC_3V3', 'VDD_0V9', 'VDD_ARM', 'VCC_DDR', '') or t.IsLocked(): continue
    if t.GetClass() != 'PCB_VIA' and t.GetLayer() == pcbnew.F_Cu and t.GetBoundingBox().Intersects(ZONE): YIELD.add(n)
for t in list(b.GetTracks()):
    if t.GetNetname() in YIELD and not t.IsLocked(): b.Remove(t); KEEP.append(t)
if os.environ.get('USBPAIR_YIELD_EXTRA'): YIELD |= set(os.environ['USBPAIR_YIELD_EXTRA'].split('|'))
print('yield nets', sorted(YIELD), flush=True)
WIN = (116, 136, 152, 172)
g = Geo(b, WIN)
U = b.FindFootprintByReference('U100'); pad = {p.GetNumber(): p for p in U.Pads()}
P = lambda p: (p.GetPosition().x/1e6, p.GetPosition().y/1e6)
pin_dp, pin_dm = P(pad['27']), P(pad['26'])
u1 = b.FindFootprintByReference('U1'); u1p = {q.GetNumber(): q for q in u1.Pads()}
u2 = b.FindFootprintByReference('U2'); u2p = {q.GetNumber(): q for q in u2.Pads()}
U1DP, U1DM = P(u1p['4']), P(u1p['6']); U2DP, U2DM = P(u2p['6']), P(u2p['7'])
print('pins', pin_dm, pin_dp, 'U1', U1DM, U1DP, 'U2', U2DP, U2DM, flush=True)

# ---------- 2. place R509 (D-) over R508 (D+)
r508, r509 = b.FindFootprintByReference('R508'), b.FindFootprintByReference('R509')
g.remove(lambda r: r[3] in ('R508', 'R509'))
court = []
for fp in b.GetFootprints():
    if fp.IsFlipped() or fp.GetReference() in ('R508', 'R509'): continue
    c = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    if c.GetWidth() > 0: court.append((fp.GetReference(), (c.GetLeft()/1e6, c.GetTop()/1e6, c.GetRight()/1e6, c.GetBottom()/1e6)))
def boxes_hit(box, grow=0.0):
    return any(not (box[2] + grow < o[0] or o[2] + grow < box[0] or box[3] + grow < o[1] or o[3] + grow < box[1]) for _, o in court)
def set_r(fp, x, y, rot):
    if fp.IsFlipped(): fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(rot); fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
def pads_of(fp): return {q.GetNumber(): P(q) for q in fp.Pads()}
y2 = b.FindFootprintByReference('Y502').GetCourtyard(pcbnew.F_CrtYd).BBox()
Y502 = (y2.GetLeft()/1e6, y2.GetTop()/1e6, y2.GetRight()/1e6, y2.GetBottom()/1e6)
# ---------- generic A*
def astar(net, start, goal, w, layers, grid, window, extra_tracks=0.0, ignore=lambda r: False, viacost=1.5, goal_tol=None, start_li=None, goal_li=(0,), usb_extra=0.0, max_it=600000, partner=None):
    x0, y0, x1, y1 = window; nx, ny = int((x1-x0)/grid)+1, int((y1-y0)/grid)+1
    tol = goal_tol if goal_tol is not None else grid*0.75
    gx, gy = goal
    cache = {}
    def free(li, i, j):
        k = (li, i, j)
        if k not in cache:
            pt = ('pt', (x0 + i*grid, y0 + j*grid), w/2 + 0.03)
            cache[k] = g.clear(pt, layers[li], net, extra_tracks=extra_tracks, ignore=ignore) and \
                (usb_extra == 0 or g.clear(pt, layers[li], net, extra_tracks=usb_extra, ignore=lambda r: r[0] not in (DP, DM)))   # HDG spacing: the routed pair (connector side)
        return cache[k]
    pcache = {}
    def pfree(li, i, j):                                   # partner gap, enforced everywhere except at the exact ends
        if partner is None: return True
        k = (li, i, j)
        if k not in pcache:
            xx, yy = x0 + i*grid, y0 + j*grid
            pcache[k] = math.hypot(xx - gx, yy - gy) < 0.04 or math.hypot(xx - start[0], yy - start[1]) < 0.04 or \
                g.clear(('pt', (xx, yy), w/2), layers[li], net, extra=-0.031, ignore=lambda r: r[0] != partner)
        return pcache[k]
    vcache = {}
    def vfree(i, j):
        k = (i, j)
        if k not in vcache:
            xx, yy = x0 + i*grid, y0 + j*grid
            vcache[k] = g.hole_ok(xx, yy, 0.2) and all(g.clear(('pt', (xx, yy), 0.23), L, net, ignore=ignore) for L in CU) and \
                g.clear(('pt', (xx, yy), 0.23), F, net, ignore=lambda r: r[4] != 'pad', same_net_ok=False)   # never inside an SMD pad, own net included
        return vcache[k]
    si, sj = int(round((start[0]-x0)/grid)), int(round((start[1]-y0)/grid))
    gx, gy = goal
    def h(i, j): return math.hypot(x0 + i*grid - gx, y0 + j*grid - gy)/grid
    openq = []; came = {}; gs = {}
    for li in (start_li if start_li is not None else range(len(layers))):
        s = (li, si, sj); gs[s] = 0; came[s] = None; heapq.heappush(openq, (h(si, sj), 0, s))
    D8 = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1), (-1, -1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (1, 1, 1.414)]
    it = 0
    while openq:
        f, gg, n = heapq.heappop(openq); it += 1
        li, i, j = n
        if math.hypot(x0 + i*grid - gx, y0 + j*grid - gy) <= tol and li in goal_li:
            path = []
            while n is not None: path.append(n); n = came[n]
            path.reverse()
            return [(x0 + i*grid, y0 + j*grid, layers[li]) for li, i, j in path]
        if it > max_it: return None
        for di, dj, c in D8:
            m = (li, i+di, j+dj)
            if not (0 <= m[1] < nx and 0 <= m[2] < ny): continue
            if not free(*m) and math.hypot(x0 + m[1]*grid - start[0], y0 + m[2]*grid - start[1]) > 0.3: continue
            if not pfree(*m): continue
            ng = gg + c
            if ng < gs.get(m, 1e18): gs[m] = ng; came[m] = n; heapq.heappush(openq, (ng + h(m[1], m[2]), ng, m))
        if len(layers) > 1 and vfree(i, j):
            for lj in range(len(layers)):
                if lj == li or not free(lj, i, j): continue
                m = (lj, i, j); ng = gg + viacost/grid
                if ng < gs.get(m, 1e18): gs[m] = ng; came[m] = n; heapq.heappush(openq, (ng + h(i, j), ng, m))
    return None
def simplify(pts):
    out = [pts[0]]
    for q in range(1, len(pts)-1):
        a, c, d = out[-1], pts[q], pts[q+1]
        if c[2] != a[2] or d[2] != c[2]: out.append(c); continue
        if abs((c[0]-a[0])*(d[1]-c[1]) - (c[1]-a[1])*(d[0]-c[0])) > 1e-9: out.append(c)
    out.append(pts[-1]); return out
def emit(net, pts, w):
    """pts [(x, y, layer)] -> tracks and vias; returns copper length"""
    L = 0.0
    for a, c in zip(pts, pts[1:]):
        if a[2] != c[2]: g.add_via(a[0], a[1], net); continue
        if math.dist(a[:2], c[:2]) < 1e-6: continue
        g.add_track(a[:2], c[:2], w, a[2], net); L += math.dist(a[:2], c[:2])
    return L

# ---------- candidates: both stacking orders, best few first
# exit lanes: every other left-side U100 signal pin keeps a 2 mm lane west of its pad free (rails leave inward through ring vias)
RAILN = ('GND', 'VCC_3V3', 'VCC_1V8', 'VDD_0V9', 'VDD_ARM', 'VCC_DDR', '')
LANES = []
for q in U.Pads():
    if not q.GetNumber(): continue
    qx, qy = P(q); n = q.GetNetname()
    if abs(qx - pin_dp[0]) < 0.01 and n not in RAILN and not n.startswith('unconnected'):
        LANES.append((qx - 0.4 - 2.3, qy - 0.25, qx - 0.4, qy + 0.25))
print('exit lanes kept', len(LANES), flush=True)
cands = []
for xi in range(0, 61):
    x = 129.0 + 0.2*xi
    for yi in range(0, 51):
        y = 141.5 + 0.2*yi
        for pitch in (1.05, 1.15):           # 0402 courtyards are ~0.98 mm tall: closer stacks overlap
            for top, bot in ((r509, r508), (r508, r509)):
                set_r(top, x, y, 180); set_r(bot, x, y + pitch, 180)     # rot 180: pad 1 east (toward U100)
                ok = True
                for fp in (top, bot):
                    c = fp.GetCourtyard(pcbnew.F_CrtYd).BBox(); box = (c.GetLeft()/1e6, c.GetTop()/1e6, c.GetRight()/1e6, c.GetBottom()/1e6)
                    if any(not (box[2] < l[0] or l[2] < box[0] or box[3] < l[1] or l[3] < box[1]) for l in LANES): ok = False; break
                    if box[2] > pin_dp[0] - 2.75: ok = False; break      # west of the escape-stub ends, chip-side pad facing them
                    if boxes_hit(box) or not (box[2] < Y502[0] - 0.5 or box[0] > Y502[2] + 0.5 or box[3] < Y502[1] - 0.5 or box[1] > Y502[3] + 0.5): ok = False; break
                    for n2, pts, _ in pad_polys(fp):
                        if not g.clear(('poly', pts), F, n2): ok = False; break
                    if not ok: break
                if not ok: continue
                a, c = pads_of(r509), pads_of(r508)
                cost = 2*(math.dist((pin_dm[0] - 2.4, pin_dm[1]), a['1']) + math.dist((pin_dp[0] - 2.4, pin_dp[1]), c['1'])) + math.dist(((a['2'][0]+c['2'][0])/2, (a['2'][1]+c['2'][1])/2), ((U1DP[0]+U1DM[0])/2, (U1DP[1]+U1DM[1])/2))
                cands.append((cost, x, y, pitch, top.GetReference()))
cands.sort()
print('legal resistor spots', len(cands), flush=True)

made = []
def track(a, c, w, L, net):
    made.append(g.add_track(a, c, w, L, net, tag='attempt'))
def via(x, y, net):
    made.append(g.add_via(x, y, net, tag='attempt'))
def emit(net, pts, w):
    L = 0.0
    for a, c in zip(pts, pts[1:]):
        if a[2] != c[2]: via(a[0], a[1], net); continue
        if math.dist(a[:2], c[:2]) < 1e-6: continue
        track(a[:2], c[:2], w, a[2], net); L += math.dist(a[:2], c[:2])
    return L
def undo():
    for o in made: b.Remove(o); KEEP.append(o)
    made.clear(); g.remove(lambda r: r[3] in ('attempt', 'new', 'fanout', 'R508', 'R509'))   # everything an attempt adds
    nr.REMAP.clear()
def offset(poly, d):
    out = []
    for k, p in enumerate(poly):
        if k == 0 or k == len(poly)-1:
            q = poly[1] if k == 0 else p; r0 = p if k == 0 else poly[k-1]
            dx, dy = q[0]-r0[0], q[1]-r0[1]; n = (-dy, dx); L = math.hypot(*n); out.append((p[0] + n[0]/L*d, p[1] + n[1]/L*d)); continue
        a = (p[0]-poly[k-1][0], p[1]-poly[k-1][1]); c = (poly[k+1][0]-p[0], poly[k+1][1]-p[1])
        la, lc = math.hypot(*a), math.hypot(*c); n1 = (-a[1]/la, a[0]/la); n2 = (-c[1]/lc, c[0]/lc)
        m = (n1[0]+n2[0], n1[1]+n2[1]); lm = math.hypot(*m); m = (m[0]/lm, m[1]/lm); cosv = m[0]*n1[0] + m[1]*n1[1]
        out.append((p[0] + m[0]*d/cosv, p[1] + m[1]*d/cosv))
    return out
ig_pair = lambda r: r[0] in PAIR


import subprocess, re as _re, tempfile
LMAP = {'F.Cu': 0, 'In2.Cu': 1, 'B.Cu': 2}
def _ends(it):
    d = it['description']; lay = _re.search(r' on (\S+)', d).group(1)
    if d.startswith('Pad') and lay in ('F.Cu', 'B.Cu'): return (it['pos']['x'], it['pos']['y']), (LMAP[lay],)
    if d.startswith('Pad') or d.startswith('Via'): return (it['pos']['x'], it['pos']['y']), (0, 1, 2)
    return (it['pos']['x'], it['pos']['y']), (LMAP.get(lay, 0),)
def reroute_yield():
    """re-route the nets that made room (netroute), 0.5 mm from the routed USB pair on the same layer"""
    return nr.route_nets(b, BOARD, g, YIELD, keep_from=(DP, DM), keep=0.35, made=made)

def attempt(cand):
    cost, x, y, pitch, topref = cand
    top, bot = (r509, r508) if topref == 'R509' else (r508, r509)
    set_r(top, x, y, 180); set_r(bot, x, y + pitch, 180)
    for fp in (r509, r508):
        for n2, pts, _ in pad_polys(fp): g.add(n2, F, ('poly', pts), fp.GetReference(), 'pad')
    R9, R8 = pads_of(r509), pads_of(r508); lengths = {}
    # fan-out first: a straight 0.8 mm escape stub west from every left-side U100 pin of the USB and moved nets, so no
    # route can cut across a neighbour's exit (sequential routing made them block each other)
    esc = {}
    for q in U.Pads():
        n = q.GetNetname(); qx, qy = P(q)
        if abs(qx - pin_dp[0]) > 0.01 or not (n in YIELD or n in (SDP, SDM)): continue
        a0, c0 = (qx - 0.40, qy), (qx - 2.40, qy); wq = W if n in (SDP, SDM) else 0.12
        if g.clear(('seg', a0, c0, wq/2), F, n):
            track((qx, qy), c0, wq, F, n); esc[q.GetNumber()] = c0; nr.REMAP[(round(qx, 2), round(qy, 2))] = c0
    if '26' not in esc or '27' not in esc: return None, 'no escape for the USB pins'
    lengths[SDM] = lengths[SDP] = 2.0
    # the fan-out strip (pin row to stub ends) is reserved: no other copper or via may enter it on any layer
    ys = [c[1] for c in esc.values()]
    strip = [(pin_dp[0] - 2.45, min(ys) - 0.2), (pin_dp[0] - 0.45, min(ys) - 0.2), (pin_dp[0] - 0.45, max(ys) + 0.2), (pin_dp[0] - 2.45, max(ys) + 0.2)]
    for Lc in CU: g.add('__fanout__', Lc, ('poly', strip), 'attempt', 'keepout')
    jobs = ((SDM, pin_dm, R9['1']), (SDP, pin_dp, R8['1']))
    soc_ok = False
    for order in (jobs, jobs[::-1]):                 # the first line routed can box the other in: try both orders
        n0 = len(made); good = True
        for net, pin, pd in order:
            start = esc['26'] if net == SDM else esc['27']
            path = nr.astar(g, net, start, pd, W, 0.05, (min(start[0], pd[0]) - 3, min(start[1], pd[1]) - 3, max(start[0], pd[0]) + 3, max(start[1], pd[1]) + 3), (0,), (0,), viacost=0.8, tol=0.04)
            if not path: good = False; break
            path[0] = (start[0], start[1], F); path[-1] = (pd[0], pd[1], F)
            lengths[net] = 2.0 + emit(net, simplify(path), W)
        if good: soc_ok = True; break
        for o in made[n0:]: b.Remove(o); KEEP.append(o)
        ids = set(id(o) for o in made[n0:]); del made[n0:]
        g.remove(lambda r: r[3] == 'attempt'); [g.add_item(o, 'attempt') for o in made]
    if not soc_ok: return None, 'SoC side (both orders)'
    mid_r = ((R9['2'][0] + R8['2'][0])/2 - 0.9, (R9['2'][1] + R8['2'][1])/2)
    cu = ((U1DP[0] + U1DM[0])/2, U1DP[1])
    goals = [(cu[0], cu[1] - d) for d in (2.2, 3.0)] + [(cu[0] - dx, cu[1] - 0.9) for dx in (2.0, 2.8)] + [(cu[0] + dx, cu[1] - 0.9) for dx in (2.0, 2.8)] + [(cu[0], cu[1] + 2.0)]
    def fat_free(p, ex): return g.clear(('pt', p, HALF + 0.03), F, DP, extra_tracks=ex, ignore=ig_pair)
    n_before = len(made); done = None
    for mid_u1 in goals:
        if not fat_free(mid_u1, 0): print('     approach', tuple(round(v,2) for v in mid_u1), 'blocked', flush=True); continue
        cl = None
        for ex in (SPACE_EXTRA, 0.15):
            mid_r2 = (mid_r[0] - 1.0, mid_r[1])               # first leg straight west, in line with the resistors
            if not all(fat_free((mid_r[0] - 0.1*k, mid_r[1]), ex) for k in range(11)): cl = None; continue
            cl = astar(DP, mid_r2, mid_u1, 2*HALF, [F], 0.1, WIN, extra_tracks=ex, ignore=ig_pair, goal_tol=0.15)
            if cl: cl = [(mid_r[0], mid_r[1], F)] + cl; break
        if not cl: print('     approach', tuple(round(v,2) for v in mid_u1), 'no centreline', flush=True); continue
        cl = [(mid_r[0], mid_r[1], F)] + simplify(cl)[1:-1] + [(mid_u1[0], mid_u1[1], F)]
        c2 = [cl[0]]
        for p in cl[1:]:
            if math.dist(p[:2], c2[-1][:2]) > 0.05: c2.append(p)
        cl = [p[:2] for p in c2]
        if len(cl) < 2: continue
        o1, o2 = offset(cl, S/2), offset(cl, -S/2)
        odm, odp = (o1, o2) if math.dist(o1[-1], U1DM) < math.dist(o2[-1], U1DM) else (o2, o1)
        if ssd(R9['2'], odm[0], R8['2'], odp[0]) < S - W or ssd(odm[-1], U1DM, odp[-1], U1DP) < S - W:   # fan-ins would cross or touch
            print('     approach', tuple(round(v,2) for v in mid_u1), 'order crossed', flush=True); continue
        ok = True
        for net, line, rp, up in ((DM, odm, R9['2'], U1DM), (DP, odp, R8['2'], U1DP)):
            lengths[net] = emit(net, [(px, py, F) for px, py in line], W)
            for a0, b0 in ((rp, line[0]), (line[-1], up)):          # fan-ins at both ends: straight if it fits, else routed
                partner = DM if net == DP else DP          # the partner may come to the 0.127 mm pair gap (DRU rule), not closer
                sg = ('seg', a0, b0, W/2)
                if g.clear(sg, F, net, ignore=lambda r, pn=partner: r[0] == pn) and g.clear(sg, F, net, extra=-0.031, ignore=lambda r, pn=partner: r[0] != pn):
                    lengths[net] += emit(net, [(a0[0], a0[1], F), (b0[0], b0[1], F)], W); continue
                fp_ = astar(net, a0, b0, W, [F], 0.025, (min(a0[0], b0[0]) - 2, min(a0[1], b0[1]) - 2, max(a0[0], b0[0]) + 2, max(a0[1], b0[1]) + 2), start_li=(0,), goal_tol=0.03, ignore=lambda r, pn=partner: r[0] == pn, partner=partner)
                if not fp_: print('     approach', tuple(round(v,2) for v in mid_u1), 'fan-in failed', net[-6:], tuple(round(v,2) for v in a0), '->', tuple(round(v,2) for v in b0), flush=True); ok = False; break
                fp_[0] = (a0[0], a0[1], F); fp_[-1] = (b0[0], b0[1], F)
                lengths[net] += emit(net, simplify(fp_), W)
            if not ok: break
        if ok: done = (mid_u1, ex); break
        for o in made[n_before:]: b.Remove(o); KEEP.append(o)
        del made[n_before:]; g.remove(lambda r: r[3] == 'attempt'); [g.add_item(o, 'attempt') for o in made]
    if not done: return None, 'centreline/fan-in (no approach to U1 worked)'
    print('   pair to U1 via approach', tuple(round(v, 2) for v in done[0]), 'spacing extra', done[1], flush=True)
    # densify each line so a stub can leave from any point, then try the closest few
    def dense(line, step=0.25):
        out = []
        for a0, c0 in zip(line, line[1:]):
            n = max(1, int(math.dist(a0, c0)/step))
            out += [(a0[0] + (c0[0]-a0[0])*q/n, a0[1] + (c0[1]-a0[1])*q/n) for q in range(n)]
        return out + [line[-1]]
    for net, line, up in ((DM, odm, U2DM), (DP, odp, U2DP)):
        path = None
        for st in sorted(dense(line), key=lambda q: math.dist(q, up))[:6]:
            path = astar(net, st, up, W, [F, IN2, pcbnew.B_Cu], 0.05, (min(st[0], up[0]) - 4, min(st[1], up[1]) - 4, max(st[0], up[0]) + 4, max(st[1], up[1]) + 4), viacost=1.0, start_li=(0,), goal_tol=0.04)
            if path: break
        if not path: return None, 'U2 stub ' + net[-6:]
        path[0] = (st[0], st[1], F); path[-1] = (up[0], up[1], F)
        lengths[net] += emit(net, simplify(path), W)
    bad = [] if os.environ.get('USBPAIR_NO_YIELD') else [n for n in reroute_yield() if not n.startswith('/SoC/SD_')]   # the microSD bus is re-routed and tuned as a whole afterwards
    if bad: return None, 'nets that made room did not re-route: %s' % sorted(set(n[-18:] for n in bad))
    return lengths, (x, y, pitch, topref)

result = None
for k, cand in enumerate(cands[:40]):
    lengths, info = attempt(cand)
    if lengths: result = (lengths, info); print('attempt', k, 'OK', info, flush=True); break
    print('attempt', k, 'failed:', info, flush=True)
    if os.environ.get('USBPAIR_STOP_ON_YIELD') and 'did not re-route' in str(info):
        b.Save(BOARD); raise SystemExit('stopped at attempt %d for diagnosis' % k)
    undo()
if not result: raise SystemExit('no complete USB layout in the first 40 resistor spots')
lengths, (x, y, pitch, topref) = result
nv = {n: sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == n) for n in PAIR}
b.Save(BOARD)
print(json.dumps({'lengths_mm': {k: round(v, 2) for k, v in lengths.items()},
                  'skew_soc_side': round(abs(lengths[SDP] - lengths[SDM]), 2), 'skew_connector_side': round(abs(lengths[DP] - lengths[DM]), 2),
                  'vias': nv, 'stack_top': topref, 'at': [round(x, 2), round(y, 2), pitch]}, indent=1))
