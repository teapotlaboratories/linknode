import sys
def load(p):
    d={}
    for l in open(p):
        if ':' not in l: continue
        n,pins=l.rsplit(': ',1) if ': ' in l else (l.strip(),'')
        d[n.strip()]=frozenset(pins.split())
    return d
a,b=load(sys.argv[1]),load(sys.argv[2])
refs=set(sys.argv[3].split(',')) if len(sys.argv)>3 else None
def keep(ps): return refs is None or any(p.split('/')[0] in refs for p in ps)
A={v for v in a.values() if keep(v)}; B={v for v in b.values() if keep(v)}
# restrict pins to refs for comparison of globals (GND etc.) 
def restrict(S): return {frozenset(p for p in v if refs is None or p.split('/')[0] in refs) for v in S}
A,B=restrict(A),restrict(B)
print('only in baseline:',sorted(map(sorted,A-B))); print('only in new:',sorted(map(sorted,B-A)))
print('MATCH' if A==B else 'DIFF')
