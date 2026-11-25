"""Grid maze router for the last unrouted connections (T26e).

Usage: python3 mazeroute.py <board.kicad_pcb> <project.kicad_pro> <drc.json> [--nets N1,N2] [--margin 4] [--grid 0.05]

Reads KiCad's DRC report (kicad-cli pcb drc --format json) and, for each unconnected pair, runs an A* search on a grid
inside a window around the two endpoints (plus --margin mm) on F.Cu, In2.Cu and B.Cu. In1.Cu is the solid GND plane:
vias pass through it, tracks don't go on it.
Obstacles: every pad, track and via of another net, inflated by the net class clearance + half the track width (KiCad's
own TransformShapeToPolygon outlines), on each layer; vias are checked on all four copper layers. Copper zones are ignored
because they refill around new copper. Widths and clearances come from the net classes in the .kicad_pro.
Each routed path is simplified into straight segments and written with pcbnew. This is a pre-check only: run kicad-cli DRC
afterwards and revert anything it rejects.
"""
import sys, json, math, heapq, re
import numpy as np
import pcbnew

args = sys.argv[1:]
BOARD, PRO, DRC = args[0], args[1], args[2]
opt = dict(zip(args[3::2], args[4::2]))
NETS = set(opt['--nets'].split(',')) if '--nets' in opt else None
MARGIN = float(opt.get('--margin', 4)); G = float(opt.get('--grid', 0.05))
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(BOARD)
pro = json.load(open(PRO))
classes = {c['name']: c for c in pro['net_settings']['classes']}
RULES = pro['board']['design_settings']['rules']
EDGE = RULES.get('min_copper_edge_clearance', 0.3)
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]            # routing layers (index 0..2)
ALLCU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]

def cls(net):
    n = b.FindNet(net).GetNetClassName()
    return classes.get(n, classes.get(n.split(',')[-1], classes['Default']))

eb = b.GetBoardEdgesBoundingBox()
BX0, BY0, BX1, BY1 = eb.GetLeft()/1e6, eb.GetTop()/1e6, eb.GetRight()/1e6, eb.GetBottom()/1e6

def items_on(layer):
    out = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.IsOnLayer(layer): out.append(p)
    for t in b.GetTracks():
        if t.IsOnLayer(layer): out.append(t)
    return out

def raster(mask, item, layer, infl, x0, y0):
    ps = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(ps, layer, mm(infl), mm(0.005), pcbnew.ERROR_OUTSIDE)
    bb = ps.BBox()
    i0 = max(0, int((bb.GetLeft()/1e6 - x0)/G)); i1 = min(mask.shape[1]-1, int((bb.GetRight()/1e6 - x0)/G)+1)
    j0 = max(0, int((bb.GetTop()/1e6 - y0)/G)); j1 = min(mask.shape[0]-1, int((bb.GetBottom()/1e6 - y0)/G)+1)
    for j in range(j0, j1+1):
        y = mm(y0 + j*G)
        for i in range(i0, i1+1):
            if not mask[j, i] and ps.Contains(pcbnew.VECTOR2I(mm(x0 + i*G), y)):
                mask[j, i] = True

SAFE = 0.04                                       # covers grid rounding (G/sqrt(2)) and polygon approximation
_oc = {}
def oclr(it):                                     # KiCad uses the larger of the two nets' clearances
    n = it.GetNetname()
    if n not in _oc: _oc[n] = cls(n)['clearance'] if n else classes['Default']['clearance']
    return _oc[n]

def route(net, A, B):
    c = cls(net); w = c['track_width']; clr = max(c['clearance'], 0.12)
    vd, vh = c['via_diameter'], c['via_drill']
    x0 = max(BX0, min(A[0], B[0]) - MARGIN); x1 = min(BX1, max(A[0], B[0]) + MARGIN)
    y0 = max(BY0, min(A[1], B[1]) - MARGIN); y1 = min(BY1, max(A[1], B[1]) + MARGIN)
    nx, ny = int((x1-x0)/G)+1, int((y1-y0)/G)+1
    block = np.zeros((3, ny, nx), bool); vblock = np.zeros((ny, nx), bool)
    win = pcbnew.BOX2I(pcbnew.VECTOR2I(mm(x0-1), mm(y0-1)), pcbnew.VECTOR2L(mm(x1-x0+2), mm(y1-y0+2)))
    for li, L in enumerate(LAYERS):
        for it in items_on(L):
            if it.GetNetname() == net or not it.GetBoundingBox().Intersects(win): continue
            raster(block[li], it, L, max(clr, oclr(it)) + w/2 + SAFE, x0, y0)
    for L in ALLCU:
        for it in items_on(L):
            if it.GetNetname() == net or not it.GetBoundingBox().Intersects(win): continue
            if L == pcbnew.In1_Cu and it.GetNetname() == 'GND': continue      # GND plane: vias of other nets get antipads
            raster(vblock, it, L, max(clr, oclr(it)) + vd/2 + SAFE, x0, y0)
    # hole-to-hole spacing applies to every drilled hole, whatever its net
    H2H = RULES.get('min_hole_to_hole', 0.25)
    holes = [(t.GetPosition(), t.GetDrill()/1e6) for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    holes += [(p.GetPosition(), p.GetDrillSizeX()/1e6) for fp in b.GetFootprints() for p in fp.Pads() if p.GetDrillSizeX() > 0]
    for pos, dr in holes:
        hx, hy = pos.x/1e6, pos.y/1e6
        r = dr/2 + H2H + vh/2 + SAFE
        if hx < x0 - r or hx > x1 + r or hy < y0 - r or hy > y1 + r: continue
        i0, i1 = max(0, int((hx - r - x0)/G)), min(nx-1, int((hx + r - x0)/G)+1)
        j0, j1 = max(0, int((hy - r - y0)/G)), min(ny-1, int((hy + r - y0)/G)+1)
        for j in range(j0, j1+1):
            for i in range(i0, i1+1):
                if (x0 + i*G - hx)**2 + (y0 + j*G - hy)**2 < r*r: vblock[j, i] = True
    # board-edge keep-out
    yy, xx = np.mgrid[0:ny, 0:nx]
    gx, gy = x0 + xx*G, y0 + yy*G
    edge_bad = (gx < BX0 + EDGE + w/2) | (gx > BX1 - EDGE - w/2) | (gy < BY0 + EDGE + w/2) | (gy > BY1 - EDGE - w/2)
    block |= edge_bad[None]
    vblock |= (gx < BX0 + EDGE + vd/2) | (gx > BX1 - EDGE - vd/2) | (gy < BY0 + EDGE + vd/2) | (gy > BY1 - EDGE - vd/2)

    def cells_for(P):
        (px, py, layers) = P
        i, j = int(round((px - x0)/G)), int(round((py - y0)/G))
        return [(li, j, i) for li in layers]
    S = cells_for(A); T = set(cells_for(B))
    for (li, j, i) in S + list(T): block[li, j, i] = False
    viacost = 30
    def h(n): return min(abs(n[1]-t[1]) + abs(n[2]-t[2]) for t in T)
    openq = [(h(s), 0, s) for s in S]; heapq.heapify(openq)
    came = {s: None for s in S}; gsc = {s: 0 for s in S}
    D8 = [(-1,0,1),(1,0,1),(0,-1,1),(0,1,1),(-1,-1,1.414),(1,-1,1.414),(-1,1,1.414),(1,1,1.414)]
    end = None; it = 0
    while openq:
        f, g, n = heapq.heappop(openq); it += 1
        if n in T: end = n; break
        if it > 3_000_000: break
        li, j, i = n
        for dj, di, cst in D8:
            m = (li, j+dj, i+di)
            if not (0 <= m[1] < ny and 0 <= m[2] < nx) or block[li, m[1], m[2]]: continue
            ng = g + cst
            if ng < gsc.get(m, 1e18): gsc[m] = ng; came[m] = n; heapq.heappush(openq, (ng + h(m), ng, m))
        if not vblock[j, i]:
            for lj in range(3):
                if lj == li or block[lj, j, i]: continue
                m = (lj, j, i); ng = g + viacost
                if ng < gsc.get(m, 1e18): gsc[m] = ng; came[m] = n; heapq.heappush(openq, (ng + h(m), ng, m))
    if end is None: return None
    path = []; n = end
    while n is not None: path.append(n); n = came[n]
    path.reverse()
    return path, (x0, y0), w, vd, vh

def emit(net, res, A, B):
    path, (x0, y0), w, vd, vh = res
    ni = b.FindNet(net); made = 0
    pts = [(x0 + i*G, y0 + j*G, li) for (li, j, i) in path]
    # exact endpoints
    pts[0] = (A[0], A[1], pts[0][2]); pts[-1] = (B[0], B[1], pts[-1][2])
    # merge short middle runs between two layer changes into the next layer (one via instead of two close ones)
    runs = []
    for p in pts:
        if runs and runs[-1][0] == p[2]: runs[-1][1].append(p)
        else: runs.append([p[2], [p]])
    changed = True
    while changed:
        changed = False
        for r in range(1, len(runs) - 1):
            seg = runs[r][1]
            L = sum(math.hypot(seg[q+1][0]-seg[q][0], seg[q+1][1]-seg[q][1]) for q in range(len(seg)-1))
            if L < 0.5:
                runs[r+1][1] = [(x, y, runs[r+1][0]) for (x, y, _) in seg] + runs[r+1][1]
                del runs[r]; changed = True; break
    pts = [p for _, ps in runs for p in ps]
    # split into runs on one layer, simplify collinear points
    k = 0
    while k < len(pts) - 1:
        if pts[k+1][2] != pts[k][2]:
            v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(pts[k][0]), mm(pts[k][1])))
            v.SetWidth(mm(vd)); v.SetDrill(mm(vh)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(ni); b.Add(v); made += 1
            k += 1; continue
        s = k
        while k + 1 < len(pts) and pts[k+1][2] == pts[s][2]:
            k += 1
        run = pts[s:k+1]
        simp = [run[0]]
        for q in range(1, len(run) - 1):
            ax, ay = run[q][0] - simp[-1][0], run[q][1] - simp[-1][1]
            bx, by = run[q+1][0] - run[q][0], run[q+1][1] - run[q][1]
            if abs(ax*by - ay*bx) > 1e-9: simp.append(run[q])
        simp.append(run[-1])
        for a, c in zip(simp, simp[1:]):
            if abs(a[0]-c[0]) < 1e-6 and abs(a[1]-c[1]) < 1e-6: continue
            t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1]))); t.SetEnd(pcbnew.VECTOR2I(mm(c[0]), mm(c[1])))
            t.SetWidth(mm(w)); t.SetLayer(LAYERS[a[2]]); t.SetNet(ni); b.Add(t); made += 1
    return made

def endpoint(item):
    x, y = item['pos']['x'], item['pos']['y']; d = item['description']
    if d.startswith('Pad'):
        m = re.search(r'of (\S+) on (\S+)', d); lay = m.group(2)
        layers = [0] if lay == 'F.Cu' else ([2] if lay == 'B.Cu' else [0, 1, 2])
    elif d.startswith('Via'): layers = [0, 1, 2]
    else:
        lay = re.search(r'on (\S+)', d).group(1); layers = [{'F.Cu': 0, 'In2.Cu': 1, 'B.Cu': 2}.get(lay, 0)]
    return (x, y, layers)

rep = json.load(open(DRC))
done = fail = 0
for u in rep['unconnected_items']:
    a, c = u['items']
    net = re.search(r'\[([^\]]+)\]', a['description']).group(1)
    if b.FindNet(net) is None and net.startswith('Net-('): net = 'Net-(' + net[5:].replace('/', '{slash}')   # DRC text shows '/', the board stores '{slash}'
    if NETS and net not in NETS: continue
    if a['description'].startswith('Zone') or c['description'].startswith('Zone'): continue
    A, B = endpoint(a), endpoint(c)
    res = route(net, A, B)
    if res:
        n = emit(net, res, A, B); done += 1
        print('routed %-32s (%.2f,%.2f)->(%.2f,%.2f): %d items' % (net[-32:], A[0], A[1], B[0], B[1], n))
    else:
        fail += 1; print('FAILED %-32s (%.2f,%.2f)->(%.2f,%.2f)' % (net[-32:], A[0], A[1], B[0], B[1]))
print('routed', done, 'failed', fail)
b.Save(BOARD)
