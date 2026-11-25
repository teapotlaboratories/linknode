"""T47/T51 Section 2, final (owner, 2026-11-23): the USB pair as routed by KiCad's own diff-pair router (on a scratch copy,
scratch/xvfb/kicad_routed.kicad_pcb), length-matched with KiCad-style meander bumps (option D: 4 equal bumps), plus the
BC1.2 taps to U2. KiCad's skew tuner would not place a pattern under automation, so the bumps are drawn here in its
"chamfer, single-sided" style: straight legs at 90 degrees to the line, every corner cut at 45 degrees, equal amplitude,
equal spacing, all on the side away from the partner line.
Usage: python3 t47_usb_kicad.py <board.kicad_pcb> <kicad_routed.kicad_pcb> [--n 4 --s 0.45 --c 0.07] [--bump smooth|chamfer]
--bump smooth (default, owner 2026-11-23): the deskew bumps are rounded (quarter arcs, radius A/2), the one exception to
the 45-degree rule; chamfer = KiCad's "chamfer, single-sided" look.
  1. Replace the USB_DP/USB_DN/USB_SOC_DP/USB_SOC_DN copper on the board with KiCad's (same coordinates; the copy was
     made from this board, so everything else is identical). USB_CONN_* (connector side) is kept as it is.
  2. Skew target: the whole RV1106 -> U1 path (USB_SOC_* + USB_*), D- minus D+, from copper lengths (no taps yet).
     Bump (amplitude A, leg spacing s, chamfer c) adds 2A - (8 - 4*sqrt2)*c; A is solved so n equal bumps add the skew.
     The bumps go on D+'s long straight run, starting 0.45 mm past R508's pad, east (away from D-); class clearance +
     0.35 mm to other tracks (HDG 20 mil) checked with geomlib.
  3. BC1.2 taps (as t47_usb.py): a via just outside U2 for each line (D+ north-west, D- south-west of its pin) with a
     45-degree top stub into the pin's outer end; netroute A* (F/B) from a pair vertex outside the bump group.
Then run bend45.py --check, refill, DRC."""
import sys, os, math, json, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geomlib import Geo, CU, bbox, arc_points
from geomlib import dist as gdist
import netroute as nr
BRD, KRT = sys.argv[1], sys.argv[2]
opt = {sys.argv[i]: sys.argv[i + 1] for i in range(3, len(sys.argv) - 1) if sys.argv[i].startswith('--')}
NB, SP, CH = int(opt.get('--n', 4)), float(opt.get('--s', 0.45)), float(opt.get('--c', 0.07))
F, B_ = pcbnew.F_Cu, pcbnew.B_Cu
DP, DN, SDP, SDN = '/SoC/USB_DP', '/SoC/USB_DN', '/SoC/USB_SOC_DP', '/SoC/USB_SOC_DN'
PAIRN = (DP, DN, SDP, SDN)
W = 0.155; EXTRA = 0.35
def V(p): return pcbnew.VECTOR2I(pcbnew.FromMM(p[0]), pcbnew.FromMM(p[1]))
def P2(v): return (round(v.x/1e6, 4), round(v.y/1e6, 4))
# ---- 1. KiCad's copper in. The copy is read in a separate process (two boards in one pcbnew process confuse SWIG).
import subprocess
DUMP = r"""
import sys, json, pcbnew
k = pcbnew.LoadBoard(sys.argv[1]); N = set(sys.argv[2].split('|')); out = []
for t in k.GetTracks():
    n = t.GetNetname()
    if n not in N: continue
    if t.GetClass() == 'PCB_VIA': out.append(['via', n, [t.GetPosition().x, t.GetPosition().y], t.GetWidth(pcbnew.F_Cu), t.GetDrill()])
    elif t.GetClass() == 'PCB_TRACK': out.append(['trk', n, [t.GetStart().x, t.GetStart().y], [t.GetEnd().x, t.GetEnd().y], t.GetWidth(), t.GetLayer()])
    else: raise SystemExit('unexpected ' + t.GetClass())
print('JSON' + json.dumps(out))
"""
r = subprocess.run([sys.executable, '-c', DUMP, KRT, '|'.join(PAIRN)], capture_output=True, text=True)
KT = json.loads([l for l in r.stdout.splitlines() if l.startswith('JSON')][0][4:])
b = pcbnew.LoadBoard(BRD)
_eb = b.GetBoardEdgesBoundingBox()                      # read before any copper is added (SWIG wrapper goes stale)
EBOX = (_eb.GetLeft()/1e6 - 1, _eb.GetTop()/1e6 - 1, _eb.GetRight()/1e6 + 1, _eb.GetBottom()/1e6 + 1)
REMOVED = []                                             # keep removed items referenced: if Python frees them, pcbnew's SWIG state breaks
for t in list(b.GetTracks()):
    if t.GetNetname() in PAIRN: b.Remove(t); REMOVED.append(t)
g = Geo(b, EBOX)                                         # built before KiCad's copper is added (see above)
for it in KT:
    if it[0] == 'via': g.add_via(it[2][0]/1e6, it[2][1]/1e6, it[1], d=it[3]/1e6, h=it[4]/1e6, tag='kicad')
    else: g.add_track((it[2][0]/1e6, it[2][1]/1e6), (it[3][0]/1e6, it[3][1]/1e6), it[4]/1e6, it[5], it[1], tag='kicad')
ncopy = len(KT)
def netlen(n): return sum(t.GetLength()/1e6 for t in b.GetTracks() if t.GetNetname() == n and t.GetClass() == 'PCB_TRACK')
need = (netlen(SDN) + netlen(DN)) - (netlen(SDP) + netlen(DP))
# ---- 2. KiCad-style meander on D+
def pad(ref, num): return [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
r8b = pad('R508', '2'); r8bot = r8b.GetBoundingBox().GetBottom()/1e6
segs = [t for t in b.GetTracks() if t.GetNetname() == DP and t.GetClass() == 'PCB_TRACK' and t.GetLayer() == F]
run = max(segs, key=lambda t: t.GetLength())
A0, C0 = P2(run.GetStart()), P2(run.GetEnd())
if A0[1] > C0[1]: A0, C0 = C0, A0                                     # top to bottom
ln = math.dist(A0, C0); u = ((C0[0] - A0[0])/ln, (C0[1] - A0[1])/ln)
# outward = away from D-: the D- copper is on the other side
dn_pts = [P2(t.GetStart()) for t in b.GetTracks() if t.GetNetname() == DN and t.GetClass() == 'PCB_TRACK']
mid = ((A0[0] + C0[0])/2, (A0[1] + C0[1])/2)
o = (-u[1], u[0])
if min(math.dist((mid[0] + o[0]*0.3, mid[1] + o[1]*0.3), q) for q in dn_pts) < min(math.dist((mid[0] - o[0]*0.3, mid[1] - o[1]*0.3), q) for q in dn_pts):
    o = (-o[0], -o[1])
STYLE = opt.get('--bump', 'smooth')
K8 = 8 - 4*math.sqrt(2)
R2 = math.sqrt(0.5)
if STYLE == 'smooth':
    # owner 2026-11-23: deskew bumps smooth (the one exception to the 45-degree rule): every corner a quarter arc of
    # radius r = A/2 (capped at s/2), so each bump is legs-free: arc, arc, short top, arc, arc. Extra per bump =
    # 2A - (8 - 2*pi)*r; with r = A/2 that is (2 - (4 - pi))*A = 1.1416*A.
    A = need/NB/(2 - (4 - math.pi))
    RR = min(A/2, SP/2)
    if RR < A/2: A = (need/NB + (8 - 2*math.pi)*RR)/2
    PER = SP + 2*RR
else:
    A = (need/NB + K8*CH)/2                                           # chamfer style: per-bump extra = 2A - K8*c
    if A < 2*CH + 0.05: raise SystemExit('amplitude %.3f too small for chamfer %.3f' % (A, CH))
    PER = SP + 2*CH
total = NB*PER + (NB - 1)*SP
def bump_items(x0):
    """one bump from baseline point x0, as ('L', a, c) and ('A', start, mid, end) items in board mm"""
    def at(a, h): return (round(x0[0] + u[0]*a + o[0]*h, 4), round(x0[1] + u[1]*a + o[1]*h, 4))
    if STYLE != 'smooth':
        q = [at(0, 0), at(CH, CH), at(CH, A - CH), at(2*CH, A), at(SP, A), at(SP + CH, A - CH), at(SP + CH, CH), at(SP + 2*CH, 0)]
        return [('L', a, c) for a, c in zip(q, q[1:])]
    r = RR
    it = [('A', at(0, 0), at(r*R2, r - r*R2), at(r, r))]
    if A - 2*r > 1e-4: it.append(('L', at(r, r), at(r, A - r)))
    it.append(('A', at(r, A - r), at(2*r - r*R2, A - r + r*R2), at(2*r, A)))
    if SP - 2*r > 1e-4: it.append(('L', at(2*r, A), at(SP, A)))
    it.append(('A', at(SP, A), at(SP + r*R2, A - r + r*R2), at(SP + r, A - r)))
    if A - 2*r > 1e-4: it.append(('L', at(SP + r, A - r), at(SP + r, r)))
    it.append(('A', at(SP + r, r), at(SP + 2*r - r*R2, r - r*R2), at(SP + 2*r, 0)))
    return it
def item_segs(it):
    if it[0] == 'L': return [(it[1], it[2])]
    q = arc_points(it[1], it[2], it[3], 12); return list(zip(q, q[1:]))
start0 = max(0.45 + (r8bot - A0[1]) if abs(u[1]) > 0.9 else 0.45, 0.45)
best = None
for i in range(int((ln - total - start0 - 0.3)/0.05) + 1):
    s0 = start0 + 0.05*i
    items = []; cur = A0
    for j in range(NB):
        x0 = (round(A0[0] + u[0]*(s0 + j*(PER + SP)), 4), round(A0[1] + u[1]*(s0 + j*(PER + SP)), 4))
        items.append(('L', cur, x0)); bi = bump_items(x0); items += bi; cur = bi[-1][-1]
    items.append(('L', cur, C0))
    ok = True
    for it in items:
        for a, c in item_segs(it):
            if math.dist(a, c) < 1e-6: continue
            if not (g.clear(('seg', a, c, W/2), F, DP, ignore=lambda r: r[0] == DN) and
                    g.clear(('seg', a, c, W/2), F, DP, extra_tracks=EXTRA, ignore=lambda r: r[0] in PAIRN or r[4] != 'track')):
                ok = False; break
        if not ok: break
    if ok: best = (s0, items); break
MEANDER = best
if best is None: raise SystemExit('no room for the meander')
b.Remove(run); REMOVED.append(run)
bump_set = set()
for it in best[1]:
    if it[0] == 'L':
        if math.dist(it[1], it[2]) < 1e-6: continue
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(it[1])); t.SetEnd(V(it[2]))
    else:
        t = pcbnew.PCB_ARC(b); t.SetStart(V(it[1])); t.SetMid(V(it[2])); t.SetEnd(V(it[3]))
    t.SetWidth(pcbnew.FromMM(W)); t.SetLayer(F); t.SetNet(b.FindNet(DP)); b.Add(t); g.add_item(t, 'meander')
for it in best[1][1:-1]:
    for q in it[1:]: bump_set.add(q)
# ---- 3. BC1.2 taps
def P(p): return (p.GetPosition().x/1e6, p.GetPosition().y/1e6)
def seg_ok(a, c, net): return g.clear(('seg', a, c, W/2), F, net)
def via_ok(x, y, net, r=0.225, drill=0.25, own_gap=0.09):
    if not (g.hole_ok(x, y, drill) and all(g.clear(('pt', (x, y), r), Lc, net) for Lc in CU)): return False
    G = ('pt', (x, y), r)
    for Lc in (F, B_):
        for rec in g.near(Lc, bbox(G), 0.6):
            if rec[4] == 'pad' and rec[0] == net and gdist(G, rec[1]) < own_gap: return False
    return True
def keepout(L, box, tag):
    x0, y0, x1, y1 = box; g.add('__keepout__', L, ('poly', [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]), tag, 'keepout')
U2 = b.FindFootprintByReference('U2'); cu = U2.GetCourtyard(F).BBox()
U2BOX = (cu.GetLeft()/1e6, cu.GetTop()/1e6, cu.GetRight()/1e6, cu.GetBottom()/1e6)
p6, p7 = P(pad('U2', '6')), P(pad('U2', '7'))
def dogleg_paths(a, c):
    dx, dy = c[0] - a[0], c[1] - a[1]; m = min(abs(dx), abs(dy)); dg = (math.copysign(m, dx), math.copysign(m, dy))
    yield [a, (a[0] + dg[0], a[1] + dg[1]), c]; yield [a, (c[0] - dg[0], c[1] - dg[1]), c]
    for d in (0.15, 0.2, 0.25, 0.3, 0.4, 0.5):
        if c[0] - a[0] > d: yield [a, (a[0], c[1] + math.copysign(d, a[1] - c[1])), (a[0] + d, c[1]), c]
def tap_via(net, pin, box):
    best = None
    for ix in range(int((box[2] - box[0])/0.05) + 1):
        for iy in range(int((box[3] - box[1])/0.05) + 1):
            x, y = box[0] + ix*0.05, box[1] + iy*0.05
            if not via_ok(x, y, net): continue
            for pth in dogleg_paths((x, y), pin):
                if pth[-2][0] > pin[0] - 0.25 + 1e-6 and abs(pth[-2][1] - pin[1]) > 1e-6: continue
                if all(seg_ok(a, c, net) for a, c in zip(pth, pth[1:]) if math.dist(a, c) > 1e-6):
                    l = sum(math.dist(a, c) for a, c in zip(pth, pth[1:]))
                    if best is None or l < best[0]: best = (l, (x, y), pth)
    return best
fail = []; made = []
PAIR_IDS = {t.m_Uuid.AsString() for t in b.GetTracks() if t.GetNetname() in (DP, DN)}   # pair copper before the taps
taps = {}
for net, pin, box in ((DP, p6, (U2BOX[0] - 1.2, p6[1] - 2.0, p6[0] - 0.35, p6[1] - 0.45)),
                      (DN, p7, (U2BOX[0] - 1.2, p7[1] + 0.45, p7[0] - 0.35, p7[1] + 2.0))):
    tv = tap_via(net, pin, box)
    if tv is None: raise SystemExit('no tap via for %s' % net)
    taps[net] = tv
    made.append(g.add_via(tv[1][0], tv[1][1], net, d=0.45, h=0.25))
    for a, c in zip(tv[2], tv[2][1:]):
        if math.dist(a, c) > 1e-6: made.append(g.add_track(a, c, W, F, net))
keepout(F, U2BOX, 'tmpU2')
u1 = [P(pad('U1', n)) for n in ('4', '6')]
def plen(pth): return sum(math.dist(a[:2], c[:2]) + (1.0 if a[2] != c[2] else 0.0) for a, c in zip(pth, pth[1:]))
for net in (DN, DP):
    vx, vy = taps[net][1]
    # candidate tap points: anywhere on the pair line's top-layer straight runs, every 0.25 mm (not on the bumps, not
    # near U1 or R508/R509, not near U2); the tap joins at a track end, so the run is split there
    segs = [t for t in b.GetTracks() if t.GetNetname() == net and t.GetClass() == 'PCB_TRACK' and t.GetLayer() == F and t.m_Uuid.AsString() in PAIR_IDS]
    cands = []
    for t in segs:
        a, c = P2(t.GetStart()), P2(t.GetEnd())
        if a in bump_set or c in bump_set: continue
        L = math.dist(a, c); n = int(L/0.25)
        for kk in range(n + 1):
            q = (round(a[0] + (c[0] - a[0])*kk/max(n, 1), 4), round(a[1] + (c[1] - a[1])*kk/max(n, 1), 4))
            if any(math.dist(q, x) < 0.8 for x in u1) or any(math.dist(q, bq) < 0.5 for bq in bump_set): continue
            if any(math.dist(q, P(pad(r, '2'))) < 0.8 for r in ('R508', 'R509')): continue
            cands.append((math.dist(q, (vx, vy)), q, t))
    cands.sort(key=lambda z: z[0])
    tb = None
    print('tap', net, 'candidates', len(cands), flush=True)
    for _, v, t in cands[:12]:
        gx0 = math.ceil((v[0] - min(v[0], vx) + 4)/0.05); gy0 = math.ceil((v[1] - min(v[1], vy) + 4)/0.05)
        win = (v[0] - gx0*0.05, v[1] - gy0*0.05, max(v[0], vx) + 4, max(v[1], vy) + 4)
        pth = nr.astar(g, net, v, (vx, vy), W, 0.05, win, (0,), (0, 1, 2), viacost=1.5, tol=0.04)
        if not pth: continue
        pth[0] = (v[0], v[1], pth[0][2]); pth[-1] = (vx, vy, pth[-1][2])
        pth = nr.pull(g, net, nr.simplify(pth), W)
        if tb is None or plen(pth) < tb[0]: tb = (plen(pth), v, t, pth)
    if tb is None: fail.append(net + ' tap'); continue
    _, v, t, pth = tb
    a, c = P2(t.GetStart()), P2(t.GetEnd())
    if min(math.dist(v, a), math.dist(v, c)) > 1e-3:                    # split the run at the tap point
        b.Remove(t); REMOVED.append(t)
        for p0, p1 in ((a, v), (v, c)):
            nt = pcbnew.PCB_TRACK(b); nt.SetStart(V(p0)); nt.SetEnd(V(p1)); nt.SetWidth(pcbnew.FromMM(W)); nt.SetLayer(F); nt.SetNet(b.FindNet(net)); b.Add(nt)
    nr.emit(g, net, pth, W, made); taps[net] = taps[net] + (round(tb[0], 2),)
b.Save(BRD)
print(json.dumps(dict(style=STYLE, radius=round(RR, 4) if STYLE == 'smooth' else None, tap_len={n: taps[n][-1] for n in taps}, copied=ncopy, skew_before=round(need, 4), bumps=NB, amplitude=round(A, 4), spacing=SP, chamfer=CH,
                      meander_start=round(MEANDER[0], 2), failed=fail, unrouted=b.GetConnectivity().GetUnconnectedCount(False))))
