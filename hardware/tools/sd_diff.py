"""sd_diff.py before.kicad_pcb after.kicad_pcb : list SD-sheet routing/part differences (nets touching refs 400-499 or SD names)"""
import sys, pcbnew, re, json
mm = pcbnew.ToMM
def load(p):
    b = pcbnew.LoadBoard(p)
    sdref = [f for f in b.GetFootprints() if re.match(r'[A-Z]+4\d\d$', f.GetReference())]
    nets = {pd.GetNetname() for f in sdref for pd in f.Pads()} | {n for n in b.GetNetsByName().keys() if 'SD' in str(n)}
    nets = {str(n) for n in nets} - {'GND', 'VCC_3V3', 'VCC5V0_SYS', ''}
    seg, via = {}, {}
    for t in b.GetTracks():
        n = t.GetNetname()
        if n not in nets: continue
        if t.Type() == pcbnew.PCB_VIA_T:
            q = t.GetPosition(); via[(round(mm(q.x),3), round(mm(q.y),3))] = n
        else:
            s, e = t.GetStart(), t.GetEnd()
            k = tuple(sorted([(round(mm(s.x),3), round(mm(s.y),3)), (round(mm(e.x),3), round(mm(e.y),3))]))
            seg[(b.GetLayerName(t.GetLayer()), k)] = (n, round(mm(t.GetWidth()),3))
    parts = {f.GetReference(): (round(mm(f.GetPosition().x),3), round(mm(f.GetPosition().y),3), f.GetOrientationDegrees(), 'B' if f.IsFlipped() else 'T') for f in sdref}
    return nets, seg, via, parts
nA, sA, vA, pA = load(sys.argv[1]); nB, sB, vB, pB = load(sys.argv[2])
print('nets', len(nA), len(nB), 'only before', nA - nB, 'only after', nB - nA)
rem = {k: v for k, v in sA.items() if k not in sB}; add = {k: v for k, v in sB.items() if k not in sA}
print('segments before', len(sA), 'after', len(sB), 'removed', len(rem), 'added', len(add))
for k, v in sorted(rem.items()): print('  -', k, v)
for k, v in sorted(add.items()): print('  +', k, v)
print('vias removed', {k: v for k, v in vA.items() if k not in vB}); print('vias added', {k: v for k, v in vB.items() if k not in vA})
for r in sorted(pA):
    if pA[r] != pB.get(r): print('  moved', r, pA[r], '->', pB.get(r))
json.dump({'rem': [[k[0], k[1], v[0]] for k, v in rem.items()], 'add': [[k[0], k[1], v[0]] for k, v in add.items()],
           'vrem': [[k, v] for k, v in vA.items() if k not in vB], 'vadd': [[k, v] for k, v in vB.items() if k not in vA],
           'moved': {r: [pA[r], pB[r]] for r in pA if pA[r] != pB.get(r)}}, open(sys.argv[3], 'w'))
