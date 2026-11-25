"""Length matching by serpentines (T30, 2026-11-22): Rockchip HDG 3.3.1 p.46 (SDMMC/SDIO data and command within 120 mil
of the clock) and 3.3.3 p.48 (USB intra-pair skew < 30 mil).
Usage: python3 tune.py <board.kicad_pcb> <group> [--tol 0.5]
groups: sd | sdio | usb. Each net shorter than the longest net of the group by more than --tol gets serpentines so that
it ends within --tol of it. A serpentine replaces part of one straight track segment with N rectangular bumps of
amplitude A (each bump adds 2A), legs 0.35 mm apart; amplitude 0.15-1.2 mm, either side; the first variant that keeps
class clearance to every other net (geomlib) is used, and the last bump is sized to hit the target.
Lengths are copper lengths per net, as KiCad's skew rule measures them. kicad-cli DRC is the final check."""
import sys, os, math, json, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(__file__))
from geomlib import Geo, mm
CU_IDS = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
BOARD, GROUP = sys.argv[1], sys.argv[2]
opt = dict(zip(sys.argv[3::2], sys.argv[4::2])); TOL = float(opt.get('--tol', 0.5))
GROUPS = {
    'sd': ['/SoC/SD_CLK', '/SoC/SD_CMD', '/SoC/SD_D0', '/SoC/SD_D1', '/SoC/SD_D2', '/SoC/SD_D3'],
    'sdio': ['/HaLow/HALOW_SDIO_CLK', '/HaLow/HALOW_SDIO_CMD', '/HaLow/HALOW_SDIO_D0', '/HaLow/HALOW_SDIO_D1', '/HaLow/HALOW_SDIO_D2', '/HaLow/HALOW_SDIO_D3'],
    'usb': ['/SoC/USB_DP', '/SoC/USB_DM'],
}
if GROUP == 'add':                      # tune.py <board> add NET=mm REF.PAD,REF.PAD : add exactly mm on that pad-to-pad path
    _n, _mm = sys.argv[3].split('='); ADD = {_n: float(_mm)}; PATH = sys.argv[4].split(',')
    sys.argv = sys.argv[:3]; opt = {}; NETS = [_n]
else:
    ADD = None; NETS = GROUPS[GROUP]
b = pcbnew.LoadBoard(BOARD)
OFFS = json.load(open(opt['--offsets'])) if '--offsets' in opt else {}   # per-net via allowance so lengths match KiCad's DRC (kicad_lengths.py)
def netlen(n): return OFFS.get(n, 0.0) + sum(t.GetLength()/1e6 for t in b.GetTracks() if t.GetClass() != 'PCB_VIA' and t.GetNetname() == n)
L = {n: netlen(n) for n in NETS}; target = max(L.values())
ON_PATH = None
if ADD:
    import heapq
    net = NETS[0]; target = L[net] + ADD[net] + TOL/2
    def padobj(sp):
        r, n = sp.split('.'); return [q for q in b.FindFootprintByReference(r).Pads() if q.GetNumber() == n][0]
    pa, pb = padobj(PATH[0]), padobj(PATH[1])
    key = lambda x, y, Ly: (round(x, 3), round(y, 3), Ly)
    G = {}; trk = {}
    def edge(u, v, w, t=None):
        G.setdefault(u, []).append((v, w, t)); G.setdefault(v, []).append((u, w, t))
    for t in b.GetTracks():
        if t.GetNetname() != net: continue
        if t.GetClass() == 'PCB_VIA':
            x, y = t.GetPosition().x/1e6, t.GetPosition().y/1e6
            for L1 in CU_IDS:
                for L2 in CU_IDS:
                    if L1 < L2: edge(key(x, y, L1), key(x, y, L2), 0.0)
        else:
            edge(key(t.GetStart().x/1e6, t.GetStart().y/1e6, t.GetLayer()), key(t.GetEnd().x/1e6, t.GetEnd().y/1e6, t.GetLayer()), t.GetLength()/1e6, t)
    def attach(pad, tag):
        for n in list(G):
            if isinstance(n, tuple) and n[2] in (pcbnew.F_Cu, pcbnew.B_Cu) and pad.IsOnLayer(n[2]) and pad.HitTest(pcbnew.VECTOR2I(int(n[0]*1e6), int(n[1]*1e6))): edge(tag, n, 0.0)
    attach(pa, 'A'); attach(pb, 'B')
    dist_ = {'A': 0.0}; prev = {}; q = [(0.0, 'A')]
    while q:
        d, u = heapq.heappop(q)
        if u == 'B': break
        if d > dist_.get(u, 1e18): continue
        for v, w, t in G.get(u, []):
            if d + w < dist_.get(v, 1e18): dist_[v] = d + w; prev[v] = (u, t); heapq.heappush(q, (d + w, v))
    ON_PATH = set(); u = 'B'
    while u in prev: u, t = prev[u]; t is not None and ON_PATH.add(t.m_Uuid.AsString())   # SWIG wrappers are new objects each call: match by UUID
    print('path tracks', len(ON_PATH), 'path length %.2f' % dist_.get('B', -1), flush=True)
segs = [t for t in b.GetTracks() if t.GetClass() != 'PCB_VIA' and t.GetNetname() in NETS]
xs = [p for t in segs for p in (t.GetStart().x/1e6, t.GetEnd().x/1e6)]; ys = [p for t in segs for p in (t.GetStart().y/1e6, t.GetEnd().y/1e6)]
g = Geo(b, (min(xs) - 2, min(ys) - 2, max(xs) + 2, max(ys) + 2))
PITCH = 0.30
KEEP = []
def meander(a, c, start, n, A, side, last_A):
    """points along a->c: straight to `start`, n bumps of amplitude A (last one last_A) on `side`, then on to c"""
    ux, uy = (c[0]-a[0])/math.dist(a, c), (c[1]-a[1])/math.dist(a, c); nx, ny = -uy*side, ux*side
    P = lambda s, h: (a[0] + ux*s + nx*h, a[1] + uy*s + ny*h)
    pts = [a, P(start, 0)]; s = start
    for k in range(n):
        h = last_A if k == n - 1 else A
        pts += [P(s, h), P(s + PITCH, h), P(s + PITCH, 0), P(s + 2*PITCH, 0)]; s += 2*PITCH
    pts.append(c); return pts, s
report = {}
for _pass in range(1 if ADD else 4):
  L = {n: netlen(n) for n in NETS}
  for net in sorted(NETS, key=lambda n: L[n]):
      need = target - L[net] - TOL/2
      if need <= 0: report.setdefault(net, {'len_before': round(L[net], 2), 'added': 0.0, 'len_after': round(L[net], 2)}); continue
      done = False
      cands = sorted([t for t in b.GetTracks() if t.GetClass() != 'PCB_VIA' and t.GetNetname() == net and (ON_PATH is None or t.m_Uuid.AsString() in ON_PATH)], key=lambda t: -t.GetLength())
      added_total = 0.0
      for t in cands:
          if need - added_total <= 0.05: break
          a = (t.GetStart().x/1e6, t.GetStart().y/1e6); c = (t.GetEnd().x/1e6, t.GetEnd().y/1e6); seglen = math.dist(a, c)
          w = t.GetWidth()/1e6; Ly = t.GetLayer()
          if seglen < 0.9: continue
          best = None
          for A in (0.15, 0.25, 0.35, 0.5, 0.7, 0.9, 1.2, 1.5):
              rem = need - added_total
              n = max(1, math.ceil(rem/(2*A)))
              if n*2*PITCH + 0.6 > seglen:                    # not enough room along this segment: use as many bumps as fit
                  n = int((seglen - 0.6)/(2*PITCH))
                  if n < 1: continue
              gain = min(rem, n*2*A); last = gain/2 - (n-1)*A
              if last < 0.05: n -= 1; last = A
              if n < 1: continue
              for side in (1, -1):
                  for start in [0.3 + 0.1*k for k in range(int((seglen - n*2*PITCH - 0.6)/0.1) + 1)]:
                      pts, _ = meander(a, c, start, n, A, side, last)
                      PARTNER = {'/SoC/USB_DP': '/SoC/USB_DM', '/SoC/USB_DM': '/SoC/USB_DP'}.get(net)
                      def ok(p, q):
                          sg = ('seg', p, q, w/2)
                          if PARTNER is None: return g.clear(sg, Ly, net)
                          return g.clear(sg, Ly, net, ignore=lambda r: r[0] == PARTNER) and g.clear(sg, Ly, net, extra=-0.031, ignore=lambda r: r[0] != PARTNER)
                      if all(ok(p, q) for p, q in zip(pts, pts[1:])):
                          best = (pts, n*0 + 2*((n-1)*A + last), A, side); break
                  if best: break
              if best: break
          if not best: continue
          pts, gain, A, side = best
          b.Remove(t); KEEP.append(t); g.remove(lambda r, tt=t: r[0] == net and r[1][0] == 'seg' and abs(r[1][1][0]-a[0]) < 1e-6 and abs(r[1][1][1]-a[1]) < 1e-6)
          for p, q in zip(pts, pts[1:]):
              if math.dist(p, q) > 1e-6: g.add_track(p, q, w, Ly, net)
          added_total += gain
      report.setdefault(net, {'len_before': round(L[net], 2), 'added': 0.0}); report[net]['added'] = round(report[net]['added'] + added_total, 2); report[net]['len_after'] = round(netlen(net), 2)
b.Save(BOARD)
after = {n: netlen(n) for n in NETS}
print(json.dumps({'group': GROUP, 'target': round(target, 2), 'tol': TOL, 'nets': report,
                  'spread_after': round(max(after.values()) - min(after.values()), 2)}, indent=1))
