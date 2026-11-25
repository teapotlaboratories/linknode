"""T53 (2026-11-24): 2W spacing audit for the SD/SDIO buses (HDG V1.1 Table 3-1: spacing >= 2 x width). Samples each bus
track every 0.05 mm, takes the edge gap to the nearest copper of another bus net (tracks + vias) on the same layer, and
reports the length below 2W by gap band and by place. Also lists any bus track that is not 0.17 mm.
Usage: python3 t53_spacing.py <board.kicad_pcb> NET1,NET2,...  [2W gap, default 0.34]"""
import sys, math, collections, pcbnew
sys.path.insert(0, '/home/argonite/Developments/klepon/hardware/tools')
from geomlib import dist
b = pcbnew.LoadBoard(sys.argv[1]); NETS = set(sys.argv[2].split(',')); W2 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.34
segs = []; vias = []
for t in b.GetTracks():
    n = t.GetNetname()
    if n not in NETS: continue
    if t.GetClass() == 'PCB_VIA': vias.append((n, (t.GetPosition().x/1e6, t.GetPosition().y/1e6), 0.2)); continue
    segs.append((n, t.GetLayer(), (t.GetStart().x/1e6, t.GetStart().y/1e6), (t.GetEnd().x/1e6, t.GetEnd().y/1e6), t.GetWidth()/2e6))
widths = collections.Counter((round(s[4]*2, 3)) for s in segs)
print('widths', dict(widths))
for s in segs:
    if abs(s[4]*2 - 0.17) > 1e-3: print('  width', round(s[4]*2, 3), s[0].split('/')[-1][-12:], 'F' if s[1] == pcbnew.F_Cu else 'B', tuple(round(v, 2) for v in s[2]), tuple(round(v, 2) for v in s[3]))
band = collections.Counter(); spots = collections.defaultdict(float)
for n, L, a, c, r in segs:
    l = math.dist(a, c); k = max(1, int(l/0.05))
    for i in range(k):
        t_ = (i + 0.5)/k; p = (a[0] + (c[0]-a[0])*t_, a[1] + (c[1]-a[1])*t_)
        best = 9
        for n2, L2, a2, c2, r2 in segs:
            if n2 == n or L2 != L: continue
            best = min(best, dist(('pt', p, r), ('seg', a2, c2, r2)))
        for n2, v, rv in vias:
            if n2 != n: best = min(best, dist(('pt', p, r), ('pt', v, rv)))
        if best < W2 - 1e-3:
            bd = '<0.20' if best < 0.2 else ('0.20-0.30' if best < 0.3 else '0.30-0.34')
            band[bd] += l/k; spots[('F' if L == pcbnew.F_Cu else 'B', round(p[0]), round(p[1]))] += l/k
tot = sum(math.dist(s[2], s[3]) for s in segs)
print('bus length (sum over nets) %.1f mm; below 2W: %.1f mm' % (tot, sum(band.values())), {k: round(v, 1) for k, v in band.items()})
for k, v in sorted(spots.items(), key=lambda kv: -kv[1])[:25]: print('  ', k, round(v, 2))
