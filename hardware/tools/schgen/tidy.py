import re,sys,math
p=sys.argv[1]; s=open(p).read()
def blocks(s):
    out=[];i=0
    for m in re.finditer(r'\n\t\(symbol\n',s):
        st=m.start()+1; d=0
        for j in range(st,len(s)):
            if s[j]=='(':d+=1
            elif s[j]==')':
                d-=1
                if d==0: out.append((st,j+1));break
    return out
def setprop(b,name,x,y,justify=None,hide=None):
    m=re.search(r'\(property "'+name+r'" "[^"]*"\n(\t+)\(at [\d.\-]+ [\d.\-]+ [\d.\-]+\)',b)
    if not m: return b
    b=b[:m.start()]+re.sub(r'\(at [\d.\-]+ [\d.\-]+ [\d.\-]+\)',f'(at {x:.2f} {y:.2f} 0)',b[m.start():m.end()])+b[m.end():]
    # property block bounds
    st=b.index(f'(property "{name}"'); d=0
    for j in range(st,len(b)):
        if b[j]=='(':d+=1
        elif b[j]==')':
            d-=1
            if d==0: en=j+1;break
    pb=b[st:en]
    pb=re.sub(r'\n\t+\(hide yes\)','',pb)
    if hide: pb=re.sub(r'(\(at [^)]*\))',r'\1\n\t\t\t(hide yes)',pb,1)
    pb=re.sub(r'\n\t+\(justify [a-z ]+\)','',pb)
    if justify: pb=re.sub(r'(\(font\n\t+\(size [\d.]+ [\d.]+\)\n\t+\))',r'\1\n\t\t\t\t(justify '+justify+')',pb,1)
    return b[:st]+pb+b[en:]
res=[];pos=0
for st,en in blocks(s):
    b=s[st:en]
    lib=re.search(r'\(lib_id "([^"]+)"\)',b).group(1)
    at=re.search(r'\(at ([\d.\-]+) ([\d.\-]+) ([\d.\-]+)\)',b); x,y,r=map(float,at.groups())
    if lib.startswith('power:'):
        b=b.replace('(in_bom yes)','(in_bom no)').replace('(on_board yes)','(on_board no)')
        base={'power:GND':270,'power:PWR_FLAG':90}.get(lib,90)
        ang=math.radians((base+r)%360); d=4.6 if lib!='power:PWR_FLAG' else 4.0
        vx=x+d*math.cos(ang); vy=y-d*math.sin(ang)
        just=None
        if abs(math.cos(ang))>0.5: just='left' if math.cos(ang)>0 else 'right'; vx=x+2.2*math.copysign(1,math.cos(ang)); vy=y
        b=setprop(b,'Reference',x,y,hide=True)
        b=setprop(b,'Value',vx,vy,justify=just)
    elif lib in ('Device:R_Small','Device:C_Small','Device:L_Small','Device:Thermistor_NTC'):
        if int(r)%180==0:
            b=setprop(b,'Reference',x+2.03,y-1.27,justify='left'); b=setprop(b,'Value',x+2.03,y+1.27,justify='left')
        else:
            b=setprop(b,'Reference',x,y-2.54); b=setprop(b,'Value',x,y+2.54)
    elif lib in ('Device:LED_Small','Device:D_Schottky_Small','Device:D_Small'):
        b=setprop(b,'Reference',x,y-2.54); b=setprop(b,'Value',x,y+2.79)
    elif lib=='Connector:TestPoint':
        up=int(r)%360==0
        b=setprop(b,'Reference',x+1.27,y-5.08 if up else y+5.08,justify='left',hide=True); b=setprop(b,'Value',x+1.27,y-4.32 if up else y+4.32,justify='left')
    res.append(s[pos:st]+b); pos=en
res.append(s[pos:])
open(p,'w').write(''.join(res))
print('ok')
