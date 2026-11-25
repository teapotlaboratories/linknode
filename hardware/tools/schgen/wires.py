import sys,uuid,json,itertools
def segs(polys):
    out=[]
    for p in polys:
        for a,b in zip(p,p[1:]):
            if a!=b: out.append((tuple(map(lambda v:round(v,2),a)),tuple(map(lambda v:round(v,2),b))))
    return out
def on_seg(pt,s):
    (x1,y1),(x2,y2)=s; x,y=pt
    if x1==x2==x and min(y1,y2)<y<max(y1,y2): return True
    if y1==y2==y and min(x1,x2)<x<max(x1,x2): return True
    return False
def junctions(sg,pins=()):
    pts={}
    for s in sg:
        for e in s: pts[e]=pts.get(e,0)+1
    for p in pins: pts[p]=pts.get(p,0)+1
    J=set()
    for p,n in pts.items():
        mids=sum(1 for s in sg if on_seg(p,s))
        if n+2*mids>=3: J.add(p)
    return sorted(J)
def pinpoints(parts,powers):
    import symlib
    pts=[]; own=set()
    for p in parts:
        u=p.get('unit',1); m=p.get('mirror')
        for q in symlib.pins(p['symbol']):
            if q.get('unit',1) not in (0,u): continue
            x,y,_=symlib.endpoint((p['position']['x'],p['position']['y']),p['rotation'],q,(m if m in ('x','y') else ('y' if m else None))); own.add((round(x,2),round(y,2)))
        pts+=list(own); own=set()
    for p in powers: pts.append((round(p['position']['x'],2),round(p['position']['y'],2)))
    return pts
def write(path,polys,pins=(),extra_j=()):
    sg=segs(polys); J=sorted(set(junctions(sg,pins))|set(extra_j))
    s=open(path).read()
    txt=''
    for (a,b) in sg:
        txt+=f'\t(wire\n\t\t(pts\n\t\t\t(xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{uuid.uuid4()}")\n\t)\n'
    for (x,y) in J:
        txt+=f'\t(junction\n\t\t(at {x} {y})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{uuid.uuid4()}")\n\t)\n'
    i=s.rindex('(sheet_instances'); i=s.rindex('\n',0,i)+1
    s=s[:i]+txt+s[i:]
    open(path,'w').write(s)
    return len(sg),J
