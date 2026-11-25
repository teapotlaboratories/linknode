"""Shortest copper path length of a net between two pads (tracks plus vias, via barrel counted as the board thickness
between the two layers it joins, as KiCad does roughly), so side stubs are excluded. T30, 2026-11-22.
Usage: python3 pathlen.py <board> NET REF.PAD REF.PAD"""
import sys, math, heapq, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); net = sys.argv[2]
def padpos(s):
    r, n = s.split('.'); fp = b.FindFootprintByReference(r)
    q = [p for p in fp.Pads() if p.GetNumber() == n][0]; return (q.GetPosition().x/1e6, q.GetPosition().y/1e6), q
A, pa = padpos(sys.argv[3]); B, pb = padpos(sys.argv[4])
key = lambda x, y, L: (round(x, 3), round(y, 3), L)
G = {}
def edge(u, v, w): G.setdefault(u, []).append((v, w)); G.setdefault(v, []).append((u, w))
LAY = {pcbnew.F_Cu: 0, pcbnew.In1_Cu: 1, pcbnew.In2_Cu: 2, pcbnew.B_Cu: 3}
nodes = []
for t in b.GetTracks():
    if t.GetNetname() != net: continue
    if t.GetClass() == 'PCB_VIA':
        x, y = t.GetPosition().x/1e6, t.GetPosition().y/1e6
        for L1 in range(4):
            for L2 in range(L1 + 1, 4): edge(key(x, y, L1), key(x, y, L2), 0.0)   # barrel: KiCad's own via length is separate
        nodes += [key(x, y, L) for L in range(4)]
    else:
        L = LAY[t.GetLayer()]; s = key(t.GetStart().x/1e6, t.GetStart().y/1e6, L); e = key(t.GetEnd().x/1e6, t.GetEnd().y/1e6, L)
        edge(s, e, t.GetLength()/1e6); nodes += [s, e]
def attach(P, pad, tag):
    L = 0 if pad.IsOnLayer(pcbnew.F_Cu) else 3
    for n in set(nodes):
        if n[2] == L and pad.HitTest(pcbnew.VECTOR2I(int(n[0]*1e6), int(n[1]*1e6))): edge(tag, n, 0.0)
attach(A, pa, 'A'); attach(B, pb, 'B')
dist = {'A': 0.0}; q = [(0.0, 'A')]
while q:
    d, u = heapq.heappop(q)
    if u == 'B': break
    if d > dist.get(u, 1e18): continue
    for v, w in G.get(u, []):
        if d + w < dist.get(v, 1e18): dist[v] = d + w; heapq.heappush(q, (d + w, v))
print('%s %s->%s path %.2f mm' % (net, sys.argv[3], sys.argv[4], dist.get('B', float('nan'))))
