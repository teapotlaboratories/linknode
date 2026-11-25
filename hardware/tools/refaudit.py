"""Reference-plane audit for a bus (T56/T59, HDG V1.1 §3.3.1 / §3.2 (3)(5)(16)(25)).
Usage: python3 refaudit.py <board.kicad_pcb> NET[,NET...]   (a NET may end in * as a prefix match)
Refills zones in memory, then per net: length of bottom-layer track over each In2 net (top-layer tracks reference In1) and the
"void" length not within 0.45 mm of a via/through-hole (true gaps, not antipads); per bus via: distance to the nearest GND via;
the minimum gap from bus tracks to a same-layer GND pour on F.Cu/B.Cu."""
import sys, math, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pats = sys.argv[2].split(',')
allnets = [str(n) for n in b.GetNetsByName().keys()]
NETS = sorted({n for n in allnets for p in pats if (n.startswith(p[:-1]) if p.endswith('*') else n == p)})
In2, B, F = b.GetLayerID('In2.Cu'), b.GetLayerID('B.Cu'), b.GetLayerID('F.Cu')
zs2 = [z for z in b.Zones() if z.IsOnLayer(In2) and z.GetNetname()]
holes = [(t.GetPosition().x/1e6, t.GetPosition().y/1e6) for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
holes += [(p.GetPosition().x/1e6, p.GetPosition().y/1e6) for f in b.GetFootprints() for p in f.Pads() if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)]
gvia = [(t.GetPosition().x/1e6, t.GetPosition().y/1e6) for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == 'GND']
gz = [z for z in b.Zones() if z.GetNetname() == 'GND']
gap = {}
for n in NETS:
    tot = {}; vias = []
    for t in b.GetTracks():
        if t.GetNetname() != n: continue
        if t.Type() == pcbnew.PCB_VIA_T:
            q = (t.GetPosition().x/1e6, t.GetPosition().y/1e6); vias.append((q, round(min(math.dist(q, g) for g in gvia), 2))); continue
        L = t.GetLength()/1e6; k = max(1, int(L/0.05)); s, e = t.GetStart(), t.GetEnd(); ly = t.GetLayer()
        for i in range(k + 1):
            x = s.x + (e.x - s.x)*i/k; y = s.y + (e.y - s.y)*i/k; P = pcbnew.VECTOR2I(int(x), int(y)); xm, ym = x/1e6, y/1e6
            if ly == B and i < k:
                h = sorted({z.GetNetname() for z in zs2 if z.GetFilledPolysList(In2).Contains(P)})
                key = '+'.join(h) if h else ('void(antipad)' if min(math.dist((xm, ym), v) for v in holes) <= 0.45 else 'VOID')
                tot[key] = tot.get(key, 0) + L/k
            if ly in (F, B):
                for z in gz:
                    if not z.IsOnLayer(ly): continue
                    fp = z.GetFilledPolysList(ly)
                    if fp.OutlineCount() == 0: continue
                    d = -1 if fp.Contains(P) else math.sqrt(fp.SquaredDistance(P, False))/1e6 - t.GetWidth()/2e6
                    nm = b.GetLayerName(ly); gap[nm] = min(gap.get(nm, (9, None)), (round(d, 3), (round(xm, 2), round(ym, 2))))
    print(n, {k: round(v, 2) for k, v in sorted(tot.items())})
    for q, d in vias: print(f'    via ({q[0]:.2f},{q[1]:.2f}) nearest GND via {d} mm')
print('min bus track edge -> same-layer GND pour:', gap)
