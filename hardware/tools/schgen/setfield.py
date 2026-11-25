"""Override field placement: setfield.py sheet.kicad_sch 'REF:Field:x:y:angle:justify' ...
justify in {left,right,center}. Whitespace-agnostic (paren matching)."""
import sys,re,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from sexpblk import *
p=sys.argv[1]; s=open(p).read()
for spec in sys.argv[2:]:
    ref,field,x,y,ang,just=spec.split(':')
    a,b=find_symbol(s,ref); blk=s[a:b]
    ps,pe=prop_span(blk,field); prop=blk[ps:pe]
    prop=re.sub(r'\s*\(justify[^)]*\)','',prop)
    prop=re.sub(r'\(at [^)]*\)','(at %s %s %s)'%(x,y,ang),prop,count=1)
    prop=re.sub(r'\s*\(hide yes\)','',prop)
    if just=='hide':
        prop=re.sub(r'(\(at [^)]*\))',r'\1 (hide yes)',prop,count=1); just='center'
    if just!='center':
        k=prop.index('(font'); f=close(prop,k); prop=prop[:f]+' (justify %s)'%just+prop[f:]
    blk=blk[:ps]+prop+blk[pe:]; s=s[:a]+blk+s[b:]
open(p,'w').write(s); print('set',len(sys.argv)-2)
