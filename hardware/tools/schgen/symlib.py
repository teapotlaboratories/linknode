import re,math,os,functools
LIBDIRS=['/usr/share/kicad/symbols','/home/argonite/Developments/klepon/hardware/kicad/library']
def tok(s):
    for m in re.finditer(r'"((?:[^"\\]|\\.)*)"|([()])|([^\s()"]+)',s):
        if m.group(1) is not None: yield ('s',m.group(1))
        elif m.group(2): yield (m.group(2),None)
        else: yield ('a',m.group(3))
def parse(s):
    st=[[]]
    for t,v in tok(s):
        if t=='(': st.append([])
        elif t==')': x=st.pop(); st[-1].append(x)
        else: st[-1].append(v)
    return st[0][0]
@functools.lru_cache(None)
def lib(name):
    for d in LIBDIRS:
        p=os.path.join(d,name+'.kicad_sym')
        if os.path.exists(p): return parse(open(p).read())
    raise FileNotFoundError(name)
def find(node,key): return [c for c in node if isinstance(c,list) and c and c[0]==key]
def symbol(libid):
    ln,sn=libid.split(':'); L=lib(ln)
    for s in find(L,'symbol'):
        if s[1]==sn:
            ext=find(s,'extends')
            if ext: return symbol(ln+':'+ext[0][1])
            return s
    raise KeyError(libid)
def pins(libid):
    s=symbol(libid); out=[]
    for sub in find(s,'symbol'):
        m=re.search(r'_(\d+)_(\d+)$',sub[1]); unit=int(m.group(1))
        for p in find(sub,'pin'):
            at=find(p,'at')[0]; name=find(p,'name')[0][1]; num=find(p,'number')[0][1]
            out.append(dict(unit=unit,name=name,num=num,x=float(at[1]),y=float(at[2]),a=float(at[3]) if len(at)>3 else 0.0,type=p[1]))
    return out
def endpoint(pos,rot,p,mirror=None):
    # KiCad rotates first, then mirrors in sheet space ('y' flips X, 'x' flips Y)
    r=math.radians(rot); px,py=p['x'],p['y']
    rx=px*math.cos(r)-py*math.sin(r); ry=px*math.sin(r)+py*math.cos(r)
    if mirror=='y': rx=-rx
    if mirror=='x': ry=-ry
    return (round(pos[0]+rx,2), round(pos[1]-ry,2), (p['a']+rot)%360)
