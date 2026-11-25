"""Move schematic symbols to the positions in a builder JSON plan (fields shift by the same delta),
then strip all wires and junctions so the plan's wires can be re-applied.
Usage: movesyms.py plan.json sheet.kicad_sch. Aborts without writing if any plan symbol is missing."""
import sys,json,re,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from sexpblk import *
d=json.load(open(sys.argv[1])); p=sys.argv[2]; s=open(p).read()
want={(q['reference']+('@%d'%q.get('unit',1) if q.get('unit',1)!=1 or sum(1 for z in d['plain']+d['mir'] if z['reference']==q['reference'])>1 else '')):q for q in d['plain']+d['mir']}
have={r for _,_,r in symbols(s)}
miss=sorted(k for k in want if k.split('@')[0] not in have)
if miss: sys.exit('ABORT, not on sheet: %s'%miss)
moved=0
for ref,q in want.items():
    a,b=find_symbol(s,ref); blk=s[a:b]
    m=re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)',blk)
    x0,y0,r0=float(m.group(1)),float(m.group(2)),float(m.group(3) or 0)
    x1,y1,r1=q['position']['x'],q['position']['y'],float(q['rotation'])
    if (round(x0,2),round(y0,2),r0)==(round(x1,2),round(y1,2),r1): continue
    dx,dy=x1-x0,y1-y0
    blk=blk[:m.start()]+'(at %g %g %g)'%(x1,y1,r1)+blk[m.end():]
    def shift(pm):
        pr=pm.group(0); return re.sub(r'\(at ([-\d.]+) ([-\d.]+)( [-\d.]+)?\)',lambda t:'(at %g %g%s)'%(round(float(t.group(1))+dx,2),round(float(t.group(2))+dy,2),t.group(3) or ''),pr,count=1)
    blk=re.sub(r'\(property\s+"[^"]*"\s+"[^"]*"\s*\(at [^)]*\)',shift,blk)
    s=s[:a]+blk+s[b:]; moved+=1; print('moved',ref,(x0,y0,r0),'->',(x1,y1,r1))
s=strip_top(s,'wire'); s=strip_top(s,'junction')
open(p,'w').write(s); print(moved,'moved; wires/junctions stripped')
