"""Collision-aware Reference/Value placement for a KiCad 10 schematic sheet (raw text edit)."""
import re,sys,math
sys.path.insert(0,__file__.rsplit('/',1)[0]); import symlib
P=sys.argv[1]; S=open(P).read(); T=symlib.parse(S)
F=lambda n,k:[c for c in n if isinstance(c,list) and c and c[0]==k]
libs={s[1]:s for s in F(F(T,'lib_symbols')[0],'symbol')}
CH=1.27; CW=1.27   # text height, char advance (mm) for 1.27 font
def xf(pt,at,rot,mir):
    # KiCad: rotate in symbol space, then mirror in sheet space (mirror y flips X, mirror x flips Y)
    x,y=pt
    r=math.radians(rot); rx=x*math.cos(r)-y*math.sin(r); ry=x*math.sin(r)+y*math.cos(r)
    if mir=='y': rx=-rx
    if mir=='x': ry=-ry
    return (at[0]+rx, at[1]-ry)
def libgeom(lid,unit):
    s=libs[lid]; pts=[]; pins=[]
    for sub in F(s,'symbol'):
        m=re.search(r'_(\d+)_(\d+)$',sub[1]); u=int(m.group(1))
        if u not in (0,unit): continue
        for g in sub[2:]:
            if not isinstance(g,list): continue
            if g[0]=='rectangle': pts+= [tuple(map(float,F(g,'start')[0][1:3])),tuple(map(float,F(g,'end')[0][1:3]))]
            elif g[0]=='polyline': pts+= [tuple(map(float,xy[1:3])) for xy in F(F(g,'pts')[0],'xy')]
            elif g[0]=='circle':
                c=tuple(map(float,F(g,'center')[0][1:3])); r=float(F(g,'radius')[0][1]); pts+=[(c[0]-r,c[1]-r),(c[0]+r,c[1]+r)]
            elif g[0]=='arc': pts+=[tuple(map(float,F(g,k)[0][1:3])) for k in ('start','mid','end')]
            elif g[0]=='pin':
                at=F(g,'at')[0]; L=float(F(g,'length')[0][1]) if F(g,'length') else 2.54
                hid=any(isinstance(c,list) and c[0]=='hide' for c in g)
                a=math.radians(float(at[3]) if len(at)>3 else 0); p0=(float(at[1]),float(at[2])); p1=(p0[0]+L*math.cos(a),p0[1]+L*math.sin(a))
                if not hid: pins.append((p0,p1))
    return pts,pins
def bbox(pts):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; return (min(xs),min(ys),max(xs),max(ys))
def inter(a,b,m=0.15): return not (a[2]+m<=b[0] or b[2]+m<=a[0] or a[3]+m<=b[1] or b[3]+m<=a[1])
obst=[]   # (box, owner)
syms=[]
for s in F(T,'symbol'):
    lid=F(s,'lib_id')[0][1]; at=F(s,'at')[0]; pos=(float(at[1]),float(at[2])); rot=float(at[3]) if len(at)>3 else 0
    mir=F(s,'mirror')[0][1] if F(s,'mirror') else None; unit=int(F(s,'unit')[0][1]) if F(s,'unit') else 1
    props={p[1]:p for p in F(s,'property')}
    ref=props['Reference'][2]; val=props['Value'][2]
    pts,pins=libgeom(lid,unit)
    body=bbox([xf(p,pos,rot,mir) for p in pts]) if pts else (pos[0]-0.5,pos[1]-0.5,pos[0]+0.5,pos[1]+0.5)
    obst.append((body,ref))
    for p0,p1 in pins:
        a,b=xf(p0,pos,rot,mir),xf(p1,pos,rot,mir); obst.append(((min(a[0],b[0])-1.7,min(a[1],b[1])-1.7,max(a[0],b[0])+1.7,max(a[1],b[1])+1.7),ref))
    syms.append(dict(ref=ref,val=val,lid=lid,pos=pos,rot=rot,body=body,power=lid.startswith('power:'),tp=lid=='Connector:TestPoint',
                     refhid=any(isinstance(c,list) and c[0]=='hide' for c in props['Reference'])))
for w in F(T,'wire'):
    (x1,y1),(x2,y2)=[tuple(map(float,xy[1:3])) for xy in F(F(w,'pts')[0],'xy')]
    obst.append(((min(x1,x2)-0.3,min(y1,y2)-0.3,max(x1,x2)+0.3,max(y1,y2)+0.3),'wire'))
for k in ('label','hierarchical_label','global_label'):
    for l in F(T,k):
        at=F(l,'at')[0]; x,y,r=float(at[1]),float(at[2]),float(at[3]); w=len(l[1])*CW+(2.5 if k!='label' else 0.5)
        if r==0: b=(x,y-CH,x+w,y+CH*0.6)
        elif r==180: b=(x-w,y-CH,x,y+CH*0.6)
        elif r==90: b=(x-CH,y-w,x+CH*0.6,y)
        else: b=(x-CH,y,x+CH*0.6,y+w)
        obst.append((b,'label'))
def tbox(x,y,txt,just):
    w=len(txt)*CW
    if just=='left': return (x,y-CH/2,x+w,y+CH/2)
    if just=='right': return (x-w,y-CH/2,x,y+CH/2)
    return (x-w/2,y-CH/2,x+w/2,y+CH/2)
def free(boxes,own):
    for b in boxes:
        if b[0]<12 or b[2]>285 or b[1]<12 or b[3]>198: return False
        for ob,who in obst:
            if inter(b,ob): return False
    return True
placed={}
order=sorted(syms,key=lambda s:(s['power'] or s['tp'], -(s['body'][2]-s['body'][0])*(s['body'][3]-s['body'][1])))
for s in order:
    x0,y0,x1,y1=s['body']; cx,cy=(x0+x1)/2,(y0+y1)/2; m=1.0; mv=1.5
    if s['lid']=='power:PWR_FLAG':
        placed[s['ref']]=[('Value',cx,cy,'center')]; s['hideval']=True; continue
    if s['tp']:
        txt=s['ref']; cands=[]
        for d in (0,1.27,2.54):
            cands+= [[('Reference',x1+m+d,cy,'left')],[('Reference',x0-m-d,cy,'right')],[('Reference',cx,y0-m-CH/2-d,'center')],[('Reference',cx,y1+m+CH/2+d,'center')]]
    elif s['power']:
        txt=s['val']; cands=[]
        for d in (0,1.27,2.54):
            cands+= [[('Value',cx,y0-m-CH/2-d,'center')],[('Value',cx,y1+m+CH/2+d,'center')],[('Value',x1+m+d,cy,'left')],[('Value',x0-m-d,cy,'right')]]
    else:
        cands=[]
        for d in (0,1.27,2.54,3.81,5.08,7.62):
            cands+=[[('Reference',x1+m,cy-CH*0.7-d,'left'),('Value',x1+m,cy+CH*0.7-d,'left')],
                    [('Reference',x1+m,cy-CH*0.7+d,'left'),('Value',x1+m,cy+CH*0.7+d,'left')],
                    [('Reference',x0-m,cy-CH*0.7-d,'right'),('Value',x0-m,cy+CH*0.7-d,'right')],
                    [('Reference',x0-m,cy-CH*0.7+d,'right'),('Value',x0-m,cy+CH*0.7+d,'right')],
                    [('Reference',cx+d,y0-mv-CH*1.9,'center'),('Value',cx+d,y0-mv-CH*0.6,'center')],
                    [('Reference',cx+d,y1+mv+CH*0.6,'center'),('Value',cx+d,y1+mv+CH*1.9,'center')],
                    [('Reference',cx-d,y0-mv-CH*1.9,'center'),('Value',cx-d,y0-mv-CH*0.6,'center')],
                    [('Reference',cx-d,y1+mv+CH*0.6,'center'),('Value',cx-d,y1+mv+CH*1.9,'center')]]
    choice=None
    for c in cands:
        bx=[tbox(x,y,s['ref'] if f=='Reference' else s['val'],j) for f,x,y,j in c]
        if free(bx,s['ref']): choice=(c,bx); break
    if not choice: print('NO SPACE for',s['ref']); continue
    for b in choice[1]: obst.append((b,'text'))
    placed[s['ref']]=choice[0]
# write back
def edit_prop(block,name,x,y,just,hide=None,ang=0):
    i=block.find(f'(property "{name}"'); d=0
    for j in range(i,len(block)):
        if block[j]=='(':d+=1
        elif block[j]==')':
            d-=1
            if d==0: e=j+1;break
    pb=block[i:e]
    pb=re.sub(r'\(at [\d.\-]+ [\d.\-]+ [\d.\-]+\)',f'(at {x:.2f} {y:.2f} {ang})',pb,1)
    pb=re.sub(r'\s*\(justify [a-z ]+\)','',pb)
    if just!='center': pb=re.sub(r'(\(font\s*\(size [\d.]+ [\d.]+\)\s*\))',r'\1 (justify '+just+')',pb,1)
    if hide is not None:
        pb=re.sub(r'\s*\(hide yes\)','',pb)
        if hide: pb=re.sub(r'(\(at [^)]*\))',r'\1 (hide yes)',pb,1)
    return block[:i]+pb+block[e:]
out=[];pos=0
for m in re.finditer(r'\n(\s*)\(symbol\s*\n?\s*\(lib_id',S):
    st=m.start()+1; d=0
    for j in range(st,len(S)):
        if S[j]=='(':d+=1
        elif S[j]==')':
            d-=1
            if d==0: en=j+1;break
    blk=S[st:en]
    ref=re.search(r'\(property "Reference" "([^"]+)"',blk).group(1)
    lid=re.search(r'\(lib_id "([^"]+)"',blk).group(1)
    rot=float(re.search(r'\(lib_id "[^"]+"\)\s*\(at [\d.\-]+ [\d.\-]+ ([\d.\-]+)\)',blk).group(1))
    ang=90 if int(rot)%180==90 else 0
    if ref in placed:
        for f,x,y,j in placed[ref]:
            jj=j
            mir=re.search(r'\(mirror ([xy])\)',blk); mir=mir.group(1) if mir else None
            flip=(int(rot)%360 in (180,270))
            if mir=='y': flip=not flip
            if mir=='x' and int(rot)%180==90: flip=not flip
            if flip and j in ('left','right'): jj={'left':'right','right':'left'}[j]
            blk=edit_prop(blk,f,x,y,jj,hide=False,ang=ang)
        if lid=='power:PWR_FLAG':
            blk=edit_prop(blk,'Value',*placed[ref][0][1:3],'center',hide=True,ang=ang)
            blk=edit_prop(blk,'Reference',*placed[ref][0][1:3],'center',hide=True,ang=ang)
        elif lid.startswith('power:'):
            blk=edit_prop(blk,'Reference',*placed[ref][0][1:3],'center',hide=True,ang=ang)
        elif lid=='Connector:TestPoint':
            blk=edit_prop(blk,'Value',*placed[ref][0][1:3],'center',hide=True,ang=ang)
    out.append(S[pos:st]+blk); pos=en
out.append(S[pos:]); open(P,'w').write(''.join(out))
print('placed',len(placed),'of',len(syms))
