"""T47 tidy routing (owner, 2026-11-23: no jagged routes): route the unconnected pairs of the given nets with
netroute.astar_turn (heading in the state, 45-degree turns only, a cost per turn, a straight run after each turn), so the
paths come out as few long 45-degree runs instead of grid staircases.
Usage: python3 t47_tidy.py <board.kicad_pcb> NET[,NET...] [--rip] [--bend 0.6] [--minrun 3] [--grid 0.05] [--margin 4] [--w 0.12] [--box x0,y0,x1,y1]
  --box: only the pairs with both ends inside the box (T67: keeps a power net's far links, e.g. VSYS to the GPS LDO, for their own section).
  --rip: remove the nets' existing tracks and vias first (pads and parts stay); otherwise only the missing links are routed.
Pairs are routed shortest first, each with a window of the two ends +- margin; a failed pair is retried at the end with
twice the margin. Afterwards run bend45.py (no --pull) for the off-grid pad ends, refill and DRC."""
import sys, os, math, json, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import netroute as nr
from geomlib import Geo
B = sys.argv[1]; NETS = set(sys.argv[2].split(','))
opt = {sys.argv[i]: sys.argv[i + 1] for i in range(3, len(sys.argv) - 1) if sys.argv[i].startswith('--') and sys.argv[i] != '--rip'}
BEND = float(opt.get('--bend', 0.6)); MINRUN = int(opt.get('--minrun', 3)); GRID = float(opt.get('--grid', 0.05)); MARGIN = float(opt.get('--margin', 4))
b = pcbnew.LoadBoard(B); KEEP = []
if '--rip' in sys.argv:
    for t in list(b.GetTracks()):
        if t.GetNetname() in NETS: b.Remove(t); KEEP.append(t)
_eb = b.GetBoardEdgesBoundingBox(); g = Geo(b, (_eb.GetLeft()/1e6 - 1, _eb.GetTop()/1e6 - 1, _eb.GetRight()/1e6 + 1, _eb.GetBottom()/1e6 + 1))
USB = nr.USB_KEEP
# --no-top x0,y0,x1,y1[;...]: no top copper inside (e.g. under a module, inside its edge pads)
for bx in (opt['--no-top'].split(';') if '--no-top' in opt else []):
    x0_, y0_, x1_, y1_ = (float(v) for v in bx.split(','))
    g.add('__keepout__', pcbnew.F_Cu, ('poly', [(x0_, y0_), (x1_, y0_), (x1_, y1_), (x0_, y1_)]), 'no-top', 'keepout')
# --no-via x0,y0,x1,y1[;...]: no vias inside (e.g. under a module body)
nr.VIA_NO = [tuple(float(v) for v in bx.split(',')) for bx in opt['--no-via'].split(';')] if '--no-via' in opt else []
VIACOST = float(opt.get('--viacost', 1.5)); WID = float(opt.get('--w', 0.12))   # --w: track width (T53: 0.17 for the 50-ohm SD/SDIO taps)
pairs = sorted(nr.unconnected(b, B, NETS), key=lambda j: math.dist(j[1][0], j[2][0]))
NOTOP = [tuple(float(v) for v in bx.split(',')) for bx in opt['--no-top'].split(';')] if '--no-top' in opt else []
def fix_anchor(net, p, la):
    # a top-only anchor inside a no-top zone (e.g. a module pad) is reached through the net's nearest via instead
    if la != (0,) or not any(b0 <= p[0] <= b2 and b1 <= p[1] <= b3 for b0, b1, b2, b3 in NOTOP): return p, la
    vs = [(t.GetPosition().x/1e6, t.GetPosition().y/1e6) for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == net]
    return (min(vs, key=lambda v: math.dist(v, p)), (0, 2)) if vs else (p, la)
pairs = [(n_, fix_anchor(n_, *a_), fix_anchor(n_, *c_)) for n_, a_, c_ in pairs]
if '--box' in opt:
    _bx = [float(v) for v in opt['--box'].split(',')]
    _in = lambda p: _bx[0] <= p[0] <= _bx[2] and _bx[1] <= p[1] <= _bx[3]
    pairs = [q for q in pairs if _in(q[1][0]) and _in(q[2][0])]
done, failed = [], []
def go(net, pa, la, pc, lc, margin):
    win = (min(pa[0], pc[0]) - margin, min(pa[1], pc[1]) - margin, max(pa[0], pc[0]) + margin, max(pa[1], pc[1]) + margin)
    d = {}
    path = nr.astar_turn(g, net, pa, pc, WID, GRID, win, la, lc, () if net in nr.USB_FAMILY else USB, nr.USB_EXTRA,
                         bend=BEND, minrun=MINRUN, viacost=VIACOST, tol=GRID*0.8, diag=d)
    if not path: return None, d
    path[0] = (pa[0], pa[1], path[0][2]); path[-1] = (pc[0], pc[1], path[-1][2])
    path = nr.simplify(path); nr.emit(g, net, path, WID)
    return path, d
for net, (pa, la), (pc, lc) in pairs:
    path, d = go(net, pa, la, pc, lc, MARGIN)
    if path: done.append((net[-20:], round(sum(math.dist(p[:2], q[:2]) for p, q in zip(path, path[1:])), 2), sum(1 for p, q in zip(path, path[1:]) if p[2] != q[2])))
    else: failed.append((net, pa, la, pc, lc))
still = []
for net, pa, la, pc, lc in failed:
    path, d = go(net, pa, la, pc, lc, MARGIN*2)
    if path: done.append((net[-20:], round(sum(math.dist(p[:2], q[:2]) for p, q in zip(path, path[1:])), 2), 'retry'))
    else: still.append((net[-20:], pa, pc, d))
b.Save(B)
print(json.dumps(dict(routed=done, failed=still, unrouted=b.GetConnectivity().GetUnconnectedCount(False))))
