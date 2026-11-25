"""Single-net A* router on geomlib geometry (T30, 2026-11-22). Routes the unconnected pairs that kicad-cli DRC reports for
the given nets, on F.Cu / In2.Cu / B.Cu with through vias, and says why a pair fails (start blocked, goal blocked, no path).
Usage: python3 netroute.py <board.kicad_pcb> NET[,NET...] [--keep-from NET,NET --keep 0.35] [--layers F,B] [--diag]
--layers: routing layers (T47, owner 2026-11-23: signals on F/B, In2 = 5 V plane only for short escapes -> default F,B;
  pass F,In2,B to allow In2). Unconnected pairs come from pcbnew connectivity (the DRC JSON list stops at 499 entries).
--keep-from/--keep: extra spacing (mm, on top of class clearance) to the tracks of those nets on the same layer
(used for the HDG 20 mil rule around the USB pair). Saves the board; kicad-cli DRC is the final check."""
import sys, os, math, heapq, json, re, subprocess, tempfile, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(__file__))
from geomlib import Geo, CU

F, IN2, BC = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
LAYERS = [F, IN2, BC]; LMAP = {'F.Cu': 0, 'In2.Cu': 1, 'B.Cu': 2}
ALLOW = {0, 2}   # layer indices a route may use (T47 default: F, B)

def astar(g, net, start, goal, w, grid, window, start_li, goal_li, keep_from=(), keep=0.0, viacost=1.0, tol=None, max_it=2500000, diag=None):
    x0, y0, x1, y1 = window; nx, ny = int((x1-x0)/grid)+1, int((y1-y0)/grid)+1
    tol = tol if tol is not None else grid*0.8
    cache, vcache = {}, {}
    def free(li, i, j):
        k = (li, i, j)
        if k not in cache:
            pt = ('pt', (x0 + i*grid, y0 + j*grid), w/2 + 0.03)
            cache[k] = (li in ALLOW) and g.clear(pt, LAYERS[li], net)
        return cache[k]
    kcache = {}
    def kfree(li, i, j):                                   # spacing to the keep_from nets: enforced even at the route ends
        if not keep_from: return True
        k = (li, i, j)
        if k not in kcache:
            kcache[k] = g.clear(('pt', (x0 + i*grid, y0 + j*grid), w/2 + 0.03), LAYERS[li], net, extra=keep, ignore=lambda r: r[0] not in keep_from)
        return kcache[k]
    def vfree(i, j):
        k = (i, j)
        if k not in vcache:
            xx, yy = x0 + i*grid, y0 + j*grid
            vcache[k] = g.hole_ok(xx, yy, 0.2) and all(g.clear(('pt', (xx, yy), 0.23), L, net) for L in CU) and \
                g.clear(('pt', (xx, yy), 0.23), F, net, ignore=lambda r: r[4] != 'pad', same_net_ok=False) and g.clear(('pt', (xx, yy), 0.23), BC, net, ignore=lambda r: r[4] != 'pad', same_net_ok=False) and \
                (not keep_from or all(g.clear(('pt', (xx, yy), 0.23), L, net, extra=keep, ignore=lambda r: r[0] not in keep_from) for L in (F, IN2, BC)))
        return vcache[k]
    si, sj = int(round((start[0]-x0)/grid)), int(round((start[1]-y0)/grid))
    gx, gy = goal
    def near_start(i, j): return math.hypot(x0 + i*grid - start[0], y0 + j*grid - start[1]) <= 0.35
    def near_goal(i, j): return math.hypot(x0 + i*grid - gx, y0 + j*grid - gy) <= 0.35
    def h(i, j): return math.hypot(x0 + i*grid - gx, y0 + j*grid - gy)/grid
    openq, came, gs = [], {}, {}
    for li in start_li:
        s = (li, si, sj); gs[s] = 0; came[s] = None; heapq.heappush(openq, (h(si, sj), 0, s))
    D8 = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1), (-1, -1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (1, 1, 1.414)]
    it = 0
    while openq:
        f, gg, n = heapq.heappop(openq); it += 1
        li, i, j = n
        if math.hypot(x0 + i*grid - gx, y0 + j*grid - gy) <= tol and li in goal_li:
            path = []
            while n is not None: path.append(n); n = came[n]
            return [(x0 + i*grid, y0 + j*grid, LAYERS[li]) for li, i, j in reversed(path)]
        if it > max_it: break
        for di, dj, c in D8:
            m = (li, i+di, j+dj)
            if not (0 <= m[1] < nx and 0 <= m[2] < ny): continue
            if not free(*m) and not near_start(m[1], m[2]) and not near_goal(m[1], m[2]): continue
            if not kfree(*m): continue
            ng = gg + c
            if ng < gs.get(m, 1e18): gs[m] = ng; came[m] = n; heapq.heappush(openq, (ng + h(m[1], m[2]), ng, m))
        if vfree(i, j):
            for lj in range(3):
                if lj == li or not free(lj, i, j): continue
                m = (lj, i, j); ng = gg + viacost/grid
                if ng < gs.get(m, 1e18): gs[m] = ng; came[m] = n; heapq.heappush(openq, (ng + h(i, j), ng, m))
    if diag is not None:
        diag['iterations'] = it; diag['explored'] = len(gs)
        best = min(gs, key=lambda m: h(m[1], m[2])) if gs else None
        if best: diag['closest_mm'] = round(h(best[1], best[2])*grid, 2); diag['closest_at'] = (round(x0 + best[1]*grid, 2), round(y0 + best[2]*grid, 2), best[0])
    return None

def simplify(pts):
    out = [pts[0]]
    for q in range(1, len(pts)-1):
        a, c, d = out[-1], pts[q], pts[q+1]
        if c[2] != a[2] or d[2] != c[2]: out.append(c); continue
        if abs((c[0]-a[0])*(d[1]-c[1]) - (c[1]-a[1])*(d[0]-c[0])) > 1e-9: out.append(c)
    out.append(pts[-1]); return out

# linknode.kicad_dru "USB2 spacing to other signals > 20 mil (HDG p.48)": every other-net track keeps 0.5 mm from the USB_DP/DN
# copper (pads included). Class clearance 0.15 + USB_EXTRA 0.35. Enforced in pull() so straightening never breaks it.
USB_KEEP = ('/SoC/USB_DP', '/SoC/USB_DN')
USB_FAMILY = USB_KEEP + ('/SoC/USB_SOC_DP', '/SoC/USB_SOC_DN', '/USB and Charger/CHG_DP', '/USB and Charger/CHG_DN')
USB_EXTRA = 0.35
def usb_ok(g, shape, L, net):
    return net in USB_FAMILY or g.clear(shape, L, net, extra=USB_EXTRA, ignore=lambda r: r[0] not in USB_KEEP)
def pull(g, net, pts, w):
    """T47 string-pulling: on each same-layer run, jump from a point to the farthest later point of the run whose direct
    segment is 0/45/90 degrees, or which one straight + one diagonal reaches (45-degree style, owner 2026-11-23), and
    keeps clearance (geomlib). Removes the A* staircase without changing layers or vias. No long any-angle jumps: only the
    tiny grid-snap step at an off-grid end stays off-angle, and bend45.py turns it into a 45-degree dogleg."""
    out = [pts[0]]; i = 0; n = len(pts)
    while i < n - 1:
        j_best = i + 1
        for j in range(n - 1, i + 1, -1):
            a, c = pts[i], pts[j]
            if any(pts[k][2] != a[2] for k in range(i, j + 1)): continue
            dx, dy = c[0] - a[0], c[1] - a[1]
            octo = abs(dx) < 1e-6 or abs(dy) < 1e-6 or abs(abs(dx) - abs(dy)) < 1e-6
            if octo:
                if g.clear(('seg', a[:2], c[:2], w/2 + 0.03), a[2], net) and usb_ok(g, ('seg', a[:2], c[:2], w/2 + 0.03), a[2], net): j_best = j; break
            if not octo and (j - i >= 3 or i == 0 or j == n - 1):   # T47 (45-degree style): one straight + one diagonal
                m = min(abs(dx), abs(dy)); dg = (math.copysign(m, dx), math.copysign(m, dy))
                for mid in ((a[0] + dg[0], a[1] + dg[1]), (c[0] - dg[0], c[1] - dg[1])):
                    if all(g.clear(sg, a[2], net) and usb_ok(g, sg, a[2], net) for sg in (('seg', a[:2], mid, w/2 + 0.03), ('seg', mid, c[:2], w/2 + 0.03))):
                        j_best = (j, (mid[0], mid[1], a[2])); break
                if isinstance(j_best, tuple): break
        if isinstance(j_best, tuple): out.extend([j_best[1], pts[j_best[0]]]); i = j_best[0]
        else: out.append(pts[j_best]); i = j_best
    return out

def emit(g, net, pts, w, made=None):
    for a, c in zip(pts, pts[1:]):
        if a[2] != c[2]:
            v = g.add_via(a[0], a[1], net); made is not None and made.append(v); continue
        if math.dist(a[:2], c[:2]) < 1e-6: continue
        t = g.add_track(a[:2], c[:2], w, a[2], net); made is not None and made.append(t)

def ends(it, b=None, net=None):
    d = it['description']; m_ = re.search(r' on (\S+)', d); lay = m_.group(1) if m_ else 'F.Cu'
    p = (it['pos']['x'], it['pos']['y'])
    if d.startswith('Track') and b is not None:          # DRC reports a track by its start: use its free end instead
        L = b.GetLayerID(lay)
        pads = [(q.GetPosition().x/1e6, q.GetPosition().y/1e6, max(q.GetSizeX(), q.GetSizeY())/2e6) for fp in b.GetFootprints() for q in fp.Pads() if q.GetNetname() == net]
        others = [t for t in b.GetTracks() if t.GetNetname() == net]
        for t in b.GetTracks():
            if t.GetClass() == 'PCB_VIA' or t.GetNetname() != net or t.GetLayer() != L: continue
            s0 = (t.GetStart().x/1e6, t.GetStart().y/1e6); e0 = (t.GetEnd().x/1e6, t.GetEnd().y/1e6)
            if math.dist(s0, p) > 0.01 and math.dist(e0, p) > 0.01: continue
            def free_end(q):
                if any(math.dist(q, (x, y)) < r for x, y, r in pads): return False
                n = sum(1 for o in others if o is not t and (math.dist(q, (o.GetStart().x/1e6, o.GetStart().y/1e6)) < 0.01 or math.dist(q, (o.GetEnd().x/1e6, o.GetEnd().y/1e6)) < 0.01 or (o.GetClass() == 'PCB_VIA' and math.dist(q, (o.GetPosition().x/1e6, o.GetPosition().y/1e6)) < 0.01)))
                return n == 0
            for q in (e0, s0):
                if free_end(q): return q, (LMAP.get(lay, 0),)
    if d.startswith('Pad') and lay in ('F.Cu', 'B.Cu'): return p, (LMAP[lay],)
    if d.startswith('Pad') or d.startswith('Via'): return p, (0, 1, 2)
    return p, (LMAP.get(lay, 0),)

def unconnected(b, board_path, nets):
    """T47: unconnected pairs from pcbnew connectivity (no 499 cap). For each net: group its pads/tracks/vias/zones into
    connected clusters (GetConnectedItems), then join the clusters by a minimum spanning set of shortest anchor links.
    Anchors: SMD pad -> its layer; THT pad / via -> any layer; track -> its two ends on its layer."""
    b.BuildConnectivity(); c = b.GetConnectivity(); out = []
    for net in sorted(nets):
        ni = b.FindNet(net)
        if ni is None: continue
        code = ni.GetNetCode()
        items = [p for fp in b.GetFootprints() for p in fp.Pads() if p.GetNetCode() == code]
        items += [t for t in b.GetTracks() if t.GetNetCode() == code] + [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetCode() == code]
        key = lambda it: it.m_Uuid.AsString()
        byk = {key(it): it for it in items}; seen = set(); clusters = []
        for it in items:
            if key(it) in seen: continue
            stack = [it]; cl = []; seen.add(key(it))
            while stack:
                x = stack.pop(); cl.append(x)
                for y in c.GetConnectedItems(x):
                    k = key(y)
                    if k in byk and k not in seen: seen.add(k); stack.append(byk[k])
            clusters.append(cl)
        def anchors(cl):
            a = []
            for x in cl:
                if x.GetClass() == 'PAD':
                    q = (x.GetPosition().x/1e6, x.GetPosition().y/1e6)
                    if x.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH,): a.append((q, (0, 1, 2)))
                    elif x.IsOnLayer(pcbnew.F_Cu): a.append((q, (0,)))
                    elif x.IsOnLayer(pcbnew.B_Cu): a.append((q, (2,)))
                elif x.GetClass() == 'PCB_VIA': a.append(((x.GetPosition().x/1e6, x.GetPosition().y/1e6), (0, 1, 2)))
                elif x.GetClass() in ('PCB_TRACK', 'PCB_ARC'):
                    li = LMAP.get(b.GetLayerName(x.GetLayer()), 0)
                    a.append(((x.GetStart().x/1e6, x.GetStart().y/1e6), (li,))); a.append(((x.GetEnd().x/1e6, x.GetEnd().y/1e6), (li,)))
            return a
        A = [anchors(cl) for cl in clusters]
        A = [a for a in A if a]
        if len(A) < 2: continue
        inT = {0}
        while len(inT) < len(A):                                    # Prim: shortest link from the tree to a new cluster
            best = None
            for i in inT:
                for j in range(len(A)):
                    if j in inT: continue
                    for pa, la in A[i]:
                        for pc, lc in A[j]:
                            d = math.dist(pa, pc) + (0 if set(la) & set(lc) else 2.0)   # a layer change costs a via
                            if best is None or d < best[0]: best = (d, j, (pa, la), (pc, lc))
            inT.add(best[1]); out.append((net, best[2], best[3]))
    return out

def unconnected_drc(b, board_path, nets):
    b.Save(board_path)
    tmp = tempfile.mktemp(suffix='.json')
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '-o', tmp, board_path], capture_output=True)
    out = []
    for u in json.load(open(tmp))['unconnected_items']:
        a_, c_ = u['items']; net = re.search(r'\[([^\]]*)\]', a_['description']).group(1)
        if b.FindNet(net) is None and net.startswith('Net-('): net = 'Net-(' + net[5:].replace('/', '{slash}')
        if net in nets and not a_['description'].startswith('Zone') and not c_['description'].startswith('Zone'):
            out.append((net, ends(a_, b, net), ends(c_, b, net)))
    return out

def route_nets(b, board_path, g, nets, keep_from=(), keep=0.0, width=0.12, made=None, diag=False, rounds=3, pair_filter=None, widths=None, margin=5.0):
    """route the unconnected pairs of `nets`, shortest first; if some fail, undo this call's routes and retry with the
    failed ones first (up to `rounds` times). Returns the nets still failing."""
    base = sorted(unconnected(b, board_path, nets), key=lambda j: math.dist(j[1][0], j[2][0]))
    if pair_filter: base = [j for j in base if pair_filter(j)]
    first = []
    for rnd in range(rounds):
        mine = []; failed = []
        order = [j for j in base if j[0] in first] + [j for j in base if j[0] not in first]
        for net, (pa, la), (pc, lc) in order:
            pa = REMAP.get((round(pa[0], 2), round(pa[1], 2)), pa); pc = REMAP.get((round(pc[0], 2), round(pc[1], 2)), pc)
            if pa in REMAP.values(): la = (0,)
            if pc in REMAP.values(): lc = (0,)
            far = math.dist(pa, pc) > 10
            win = (min(pa[0], pc[0]) - margin, min(pa[1], pc[1]) - margin, max(pa[0], pc[0]) + margin, max(pa[1], pc[1]) + margin)
            d = {} if diag else None
            wn = (widths or {}).get(net, width)
            path = astar(g, net, pa, pc, wn, 0.1 if far else 0.05, win, la, lc, keep_from, keep, tol=0.08 if far else 0.04, diag=d)
            if not path:
                failed.append(net)
                if diag: print('  round %d FAIL %-28s %s -> %s  %s' % (rnd, net[-28:], tuple(round(v, 2) for v in pa), tuple(round(v, 2) for v in pc), d), flush=True)
                continue
            path[0] = (pa[0], pa[1], path[0][2]); path[-1] = (pc[0], pc[1], path[-1][2])
            emit(g, net, simplify(path if keep_from else pull(g, net, simplify(path), wn)), wn, mine)
        if not failed or rnd == rounds - 1: break
        for o in mine: b.Remove(o); _KEEP.append(o)                      # undo this round, failed nets go first next time
        ids = set(id(o) for o in mine)
        g.remove(lambda r: r[3] == 'new'); [g.add_item(o, 'new') for o in (made or []) if id(o) not in ids and o.GetBoard() is not None]
        first = list(dict.fromkeys(failed + first))
    if made is not None: made.extend(mine)
    return failed
_KEEP = []

REMAP = {}      # pad centre -> escape stub free end (DRC may report the pad even when a stub is attached)
def add_escapes(b, g, nets, ref='U100', lengths=(2.0, 1.5, 1.0, 0.6), made=None):
    """fan-out first: a straight stub outward from every pad of `ref` on `nets` (perpendicular to its side), as long as fits,
    and a lane one pitch wide around each stub reserved on all layers, so no route cuts across a neighbour's exit"""
    U = b.FindFootprintByReference(ref); cx, cy = U.GetPosition().x/1e6, U.GetPosition().y/1e6
    n_ok = 0
    for q in U.Pads():
        n = q.GetNetname()
        if n not in nets or not q.GetNumber(): continue
        x, y = q.GetPosition().x/1e6, q.GetPosition().y/1e6; dx, dy = x - cx, y - cy
        u = ((1 if dx > 0 else -1), 0) if abs(dx) > abs(dy) else (0, (1 if dy > 0 else -1))
        half = max(q.GetBoundingBox().GetWidth(), q.GetBoundingBox().GetHeight())/2e6
        a0 = (x + u[0]*half, y + u[1]*half)
        for ln in lengths:
            c0 = (a0[0] + u[0]*ln, a0[1] + u[1]*ln)
            if g.clear(('seg', a0, c0, 0.06), F, n): break
        else: continue
        t = g.add_track((x, y), c0, 0.12, F, n); made is not None and made.append(t); n_ok += 1
        REMAP[(round(x, 2), round(y, 2))] = c0
        p0 = (a0[0] + u[0]*0.05, a0[1] + u[1]*0.05); p1 = (c0[0] - u[0]*0.08, c0[1] - u[1]*0.08); h = 0.175
        lane = [(p0[0] - u[1]*h, p0[1] - u[0]*h), (p1[0] - u[1]*h, p1[1] - u[0]*h), (p1[0] + u[1]*h, p1[1] + u[0]*h), (p0[0] + u[1]*h, p0[1] + u[0]*h)]
        for L in CU: g.add('__fanout__', L, ('poly', lane), 'fanout', 'keepout')
    return n_ok

if __name__ == '__main__':
    BOARD = sys.argv[1]; NETS = set(sys.argv[2].split(','))
    opt = dict(zip(sys.argv[3::2], sys.argv[4::2]))
    kf = tuple(opt['--keep-from'].split(',')) if '--keep-from' in opt else ()
    if '--layers' in opt: ALLOW.clear(); ALLOW.update({'F': 0, 'In2': 1, 'B': 2}[l] for l in opt['--layers'].split(','))
    b = pcbnew.LoadBoard(BOARD)
    eb = b.GetBoardEdgesBoundingBox()
    g = Geo(b, (eb.GetLeft()/1e6 - 1, eb.GetTop()/1e6 - 1, eb.GetRight()/1e6 + 1, eb.GetBottom()/1e6 + 1))
    if '--escape' in opt: print('escape stubs', add_escapes(b, g, NETS, opt['--escape']), flush=True)
    failed = route_nets(b, BOARD, g, NETS, kf, float(opt.get('--keep', 0)), diag=True)
    b.Save(BOARD)
    print('failed', sorted(set(failed)))

D8 = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
VIA_NO = []      # boxes (x0, y0, x1, y1) where astar_turn places no via (e.g. under a module body)
def astar_turn(g, net, start, goal, w, grid, window, start_li, goal_li, keep_from=(), keep=0.0, bend=0.6, viacost=1.5,
               tol=None, max_it=4000000, minrun=3, layers=None, diag=None):
    """T47 tidy routing (owner, 2026-11-23: no jagged routes): A* whose state carries the heading, so only 45-degree turns
    exist and each one costs `bend` (mm); after a turn the path must run `minrun` grid steps straight before turning again,
    so no staircases or zigzags. Vias cost `viacost` (mm) and keep the heading. Same clearance model as astar()."""
    x0, y0, x1, y1 = window; nx, ny = int((x1 - x0)/grid) + 1, int((y1 - y0)/grid) + 1
    tol = tol if tol is not None else grid*0.8
    allow = set(layers) if layers is not None else ALLOW
    cache, vcache, kcache = {}, {}, {}
    def free(li, i, j):
        k = (li, i, j)
        if k not in cache:
            pt = ('pt', (x0 + i*grid, y0 + j*grid), w/2 + 0.03)
            cache[k] = (li in allow) and g.clear(pt, LAYERS[li], net) and (not keep_from or g.clear(pt, LAYERS[li], net, extra=keep, ignore=lambda r: r[0] not in keep_from))
        return cache[k]
    def vfree(i, j):
        k = (i, j)
        if k not in vcache:
            xx, yy = x0 + i*grid, y0 + j*grid
            vcache[k] = g.hole_ok(xx, yy, 0.2) and all(g.clear(('pt', (xx, yy), 0.23), L, net) for L in CU) and \
                g.clear(('pt', (xx, yy), 0.23), F, net, ignore=lambda r: r[4] != 'pad', same_net_ok=False) and \
                g.clear(('pt', (xx, yy), 0.23), BC, net, ignore=lambda r: r[4] != 'pad', same_net_ok=False) and \
                not any(b0 - 0.25 <= xx <= b2 + 0.25 and b1 - 0.25 <= yy <= b3 + 0.25 for b0, b1, b2, b3 in VIA_NO)
        return vcache[k]
    si, sj = int(round((start[0] - x0)/grid)), int(round((start[1] - y0)/grid))
    gx, gy = goal
    def near(i, j, p): return math.hypot(x0 + i*grid - p[0], y0 + j*grid - p[1]) <= 0.3
    def h(i, j): return math.hypot(x0 + i*grid - gx, y0 + j*grid - gy)
    openq, came, gs = [], {}, {}
    for li in start_li:
        for d in range(8):
            s = (li, si, sj, d, minrun); gs[s] = 0.0; came[s] = None; heapq.heappush(openq, (h(si, sj), 0.0, s))
    it = 0
    while openq:
        f, gg, n = heapq.heappop(openq); it += 1
        if gg > gs.get(n, 1e18) + 1e-9: continue
        li, i, j, d, run = n
        if math.hypot(x0 + i*grid - gx, y0 + j*grid - gy) <= tol and li in goal_li:
            path = []
            while n is not None: path.append(n); n = came[n]
            return [(x0 + i*grid, y0 + j*grid, LAYERS[li]) for li, i, j, d, run in reversed(path)]
        if it > max_it: break
        for dd in (0, -1, 1):
            if dd and run < minrun: continue
            d2 = (d + dd) % 8; di, dj = D8[d2]; m = (li, i + di, j + dj)
            if not (0 <= m[1] < nx and 0 <= m[2] < ny): continue
            if not free(*m) and not near(m[1], m[2], start) and not near(m[1], m[2], goal): continue
            ng = gg + grid*math.hypot(di, dj) + (bend if dd else 0.0)
            ms = (li, m[1], m[2], d2, 1 if dd else min(run + 1, minrun))
            if ng < gs.get(ms, 1e18) - 1e-9: gs[ms] = ng; came[ms] = n; heapq.heappush(openq, (ng + h(m[1], m[2]), ng, ms))
        if run >= minrun and vfree(i, j):
            for lj in (0, 1, 2):
                if lj == li or lj not in allow or not free(lj, i, j): continue
                ms = (lj, i, j, d, 0); ng = gg + viacost
                if ng < gs.get(ms, 1e18) - 1e-9: gs[ms] = ng; came[ms] = n; heapq.heappush(openq, (ng + h(i, j), ng, ms))
    if diag is not None:
        diag['iterations'] = it; diag['explored'] = len(gs)
    return None
