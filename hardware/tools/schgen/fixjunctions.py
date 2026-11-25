"""Recompute junctions of a sheet from its wires and symbol pin endpoints (raw text edit)."""
import re,sys,math,uuid
sys.path.insert(0,__file__.rsplit('/',1)[0]); import symlib
from wires import on_seg
P=sys.argv[1]; S=open(P).read(); T=symlib.parse(S)
F=lambda n,k:[c for c in n if isinstance(c,list) and c and c[0]==k]
libs={s[1]:s for s in F(F(T,'lib_symbols')[0],'symbol')}
def xf(pt,at,rot,mir):
    # KiCad: rotate in symbol space, then mirror in sheet space (mirror y flips X, mirror x flips Y)
    x,y=pt
    r=math.radians(rot); rx=x*math.cos(r)-y*math.sin(r); ry=x*math.sin(r)+y*math.cos(r)
    if mir=='y': rx=-rx
    if mir=='x': ry=-ry
    return (round(at[0]+rx,2), round(at[1]-ry,2))
pins=[]
for s in F(T,'symbol'):
    lid=F(s,'lib_id')[0][1]; at=F(s,'at')[0]; pos=(float(at[1]),float(at[2])); rot=float(at[3]) if len(at)>3 else 0
    mir=F(s,'mirror')[0][1] if F(s,'mirror') else None; unit=int(F(s,'unit')[0][1]) if F(s,'unit') else 1
    own=set()
    for sub in F(libs[lid],'symbol'):
        u=int(re.search(r'_(\d+)_(\d+)$',sub[1]).group(1))
        if u not in (0,unit): continue
        for p in F(sub,'pin'):
            a=F(p,'at')[0]; own.add(xf((float(a[1]),float(a[2])),pos,rot,mir))
    pins+=list(own)
for k in ('label','hierarchical_label','global_label'):
    for l in F(T,k): a=F(l,'at')[0]; pins.append((round(float(a[1]),2),round(float(a[2]),2)))
sg=[]
for w in F(T,'wire'):
    a,b=[(round(float(xy[1]),2),round(float(xy[2]),2)) for xy in F(F(w,'pts')[0],'xy')]; sg.append((a,b))
cnt={}
for a,b in sg:
    for e in (a,b): cnt[e]=cnt.get(e,0)+1
for p in pins: cnt[p]=cnt.get(p,0)+1
J=[]
for p,n in cnt.items():
    mids=sum(1 for s in sg if on_seg(p,s))
    if n+2*mids>=3 and (mids or n>=3): J.append(p)
S=re.sub(r'\n\s*\(junction\s*\(at [^)]*\)\s*\(diameter [^)]*\)\s*\(color [^)]*\)\s*\(uuid "?[^)"]*"?\)\s*\)','',S)
txt=''.join(f'\t(junction\n\t\t(at {x} {y})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{uuid.uuid4()}")\n\t)\n' for x,y in sorted(J))
i=S.rindex('(sheet_instances'); i=S.rindex('\n',0,i)+1
S=S[:i]+txt+S[i:]; open(P,'w').write(S)
print('junctions',len(J), 'remaining old', len(re.findall(r'\(junction',S))-len(J))
