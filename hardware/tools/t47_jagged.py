"""T47 (owner, 2026-11-23: "make sure no jagged route"): find jagged copper. A chain is followed through its track ends on
one layer (vias and pads end it). Reported per net:
  - short: a segment shorter than SHORT (default 0.2 mm) whose both ends are bends (a staircase step), not a pad entry;
  - zigzag: two consecutive bends that turn opposite ways with less than ZZ (default 0.5 mm) between them.
Arcs (the USB deskew bumps) are skipped. Usage: python3 t47_jagged.py <board.kicad_pcb> [--short 0.2] [--zz 0.5] [--nets A,B]"""
import sys, math, json, collections, pcbnew
B = sys.argv[1]
opt = {sys.argv[i]: sys.argv[i + 1] for i in range(2, len(sys.argv) - 1) if sys.argv[i].startswith('--')}
SHORT = float(opt.get('--short', 0.2)); ZZ = float(opt.get('--zz', 0.5))
ONLY = set(opt['--nets'].split(',')) if '--nets' in opt else None
b = pcbnew.LoadBoard(B)
def k(p): return (round(p[0], 3), round(p[1], 3))
segs = collections.defaultdict(list)            # (net, layer) -> [(a, c)]
for t in b.GetTracks():
    if t.GetClass() != 'PCB_TRACK': continue
    n = t.GetNetname()
    if ONLY and n not in ONLY: continue
    a = k((t.GetStart().x/1e6, t.GetStart().y/1e6)); c = k((t.GetEnd().x/1e6, t.GetEnd().y/1e6))
    if a != c: segs[(n, t.GetLayer())].append((a, c))
stops = set()
for t in b.GetTracks():
    if t.GetClass() in ('PCB_VIA', 'PCB_ARC'):
        for q in ([t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()]): stops.add(k((q.x/1e6, q.y/1e6)))
for p in b.GetPads(): stops.add(k((p.GetPosition().x/1e6, p.GetPosition().y/1e6)))
def ang(a, c): return math.degrees(math.atan2(c[1] - a[1], c[0] - a[0]))
def turn(a, m, c):
    d = (ang(m, c) - ang(a, m) + 540) % 360 - 180; return d
rep = collections.defaultdict(lambda: {'short': [], 'zigzag': []})
for (n, L), ss in segs.items():
    deg = collections.Counter(); adj = collections.defaultdict(list)
    for a, c in ss: deg[a] += 1; deg[c] += 1; adj[a].append(c); adj[c].append(a)
    # bends: a point joining exactly two segments, not a pad/via, with a direction change
    bend = {}
    for p, nb in adj.items():
        if len(nb) == 2 and p not in stops:
            t_ = turn(nb[0], p, nb[1])
            if abs(t_) > 1: bend[p] = t_
    for a, c in ss:
        l = math.dist(a, c)
        if l < SHORT and a in bend and c in bend: rep[n]['short'].append((a, round(l, 3)))
        if a in bend and c in bend and l < ZZ:
            # opposite turns seen along a -> c
            nb_a = [q for q in adj[a] if q != c][0]; nb_c = [q for q in adj[c] if q != a][0]
            if turn(nb_a, a, c) * turn(a, c, nb_c) < 0: rep[n]['zigzag'].append((a, round(l, 3)))
out = {n[-28:]: {'short': len(v['short']), 'zigzag': len(v['zigzag']), 'at': [p for p, _ in (v['short'] + v['zigzag'])][:4]}
       for n, v in sorted(rep.items()) if v['short'] or v['zigzag']}
print(json.dumps(dict(nets=len(out), total_short=sum(v['short'] for v in out.values()), total_zigzag=sum(v['zigzag'] for v in out.values()), detail=out), indent=0))
