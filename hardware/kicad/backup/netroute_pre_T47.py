"""Single-net A* router on geomlib geometry (T30, 2026-11-22). Routes the unconnected pairs that kicad-cli DRC reports for
the given nets, on F.Cu / In2.Cu / B.Cu with through vias, and says why a pair fails (start blocked, goal blocked, no path).
Usage: python3 netroute.py <board.kicad_pcb> NET[,NET...] [--keep-from NET,NET --keep 0.35] [--diag]
--keep-from/--keep: extra spacing (mm, on top of class clearance) to the tracks of those nets on the same layer
(used for the HDG 20 mil rule around the USB pair). Saves the board; kicad-cli DRC is the final check."""
import sys, os, math, heapq, json, re, subprocess, tempfile, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(__file__))
from geomlib import Geo, CU

F, IN2, BC = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
LAYERS = [F, IN2, BC]; LMAP = {'F.Cu': 0, 'In2.Cu': 1, 'B.Cu': 2}

def astar(g, net, start, goal, w, grid, window, start_li, goal_li, keep_from=(), keep=0.0, viacost=1.0, tol=None, max_it=2500000, diag=None):
    x0, y0, x1, y1 = window; nx, ny = int((x1-x0)/grid)+1, int((y1-y0)/grid)+1
    tol = tol if tol is not None else grid*0.8
    cache, vcache = {}, {}
    def free(li, i, j):
        k = (li, i, j)
        if k not in cache:
            pt = ('pt', (x0 + i*grid, y0 + j*grid), w/2 + 0.03)
            cache[k] = g.clear(pt, LAYERS[li], net)
        return cache[k]
    kcache = {}
    def kfree(li, i, j):                                   # spacing to the keep_from nets: enforced even at the route ends
        if not keep_from: return True
        k = (li, i, j)
        if k not in kcache:
            kcache[k] = g.clear(('pt', (x0 + i*grid, y0 + j*grid), w/2 + 0.03), LAYERS[li], net, extra_tracks=keep, ignore=lambda r: r[0] not in keep_from)
        return kcache[k]
    def vfree(i, j):
        k = (i, j)
        if k not in vcache:
            xx, yy = x0 + i*grid, y0 + j*grid
            vcache[k] = g.hole_ok(xx, yy, 0.2) and all(g.clear(('pt', (xx, yy), 0.23), L, net) for L in CU) and \
                g.clear(('pt', (xx, yy), 0.23), F, net, ignore=lambda r: r[4] != 'pad', same_net_ok=False) and g.clear(('pt', (xx, yy), 0.23), BC, net, ignore=lambda r: r[4] != 'pad', same_net_ok=False) and \
                (not keep_from or all(g.clear(('pt', (xx, yy), 0.23), L, net, extra_tracks=keep, ignore=lambda r: r[0] not in keep_from) for L in (F, IN2, BC)))
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

def route_nets(b, board_path, g, nets, keep_from=(), keep=0.0, width=0.12, made=None, diag=False, rounds=3, pair_filter=None, widths=None):
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
            win = (min(pa[0], pc[0]) - 5, min(pa[1], pc[1]) - 5, max(pa[0], pc[0]) + 5, max(pa[1], pc[1]) + 5)
            d = {} if diag else None
            wn = (widths or {}).get(net, width)
            path = astar(g, net, pa, pc, wn, 0.1 if far else 0.05, win, la, lc, keep_from, keep, tol=0.08 if far else 0.04, diag=d)
            if not path:
                failed.append(net)
                if diag: print('  round %d FAIL %-28s %s -> %s  %s' % (rnd, net[-28:], tuple(round(v, 2) for v in pa), tuple(round(v, 2) for v in pc), d), flush=True)
                continue
            path[0] = (pa[0], pa[1], path[0][2]); path[-1] = (pc[0], pc[1], path[-1][2])
            emit(g, net, simplify(path), wn, mine)
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
    b = pcbnew.LoadBoard(BOARD)
    g = Geo(b, (100, 100, 190, 180))
    if '--escape' in opt: print('escape stubs', add_escapes(b, g, NETS, opt['--escape']), flush=True)
    failed = route_nets(b, BOARD, g, NETS, kf, float(opt.get('--keep', 0)), diag=True)
    b.Save(BOARD)
    print('failed', sorted(set(failed)))
