import json,sys,symlib
from gen import build
def run(name,spec,P,flags=(),hier=(),base=100):
    parts,pwr,labels,lcsc,nc=build(spec,P,None)
    byref={p['reference']:p for p in parts}
    fl=[]
    for i,(ref,pin,rot) in enumerate(flags,1):
        p=byref[ref]; ps=[q for q in symlib.pins(p['symbol']) if q['num']==pin or q['name']==pin][0]
        x,y,_=symlib.endpoint((p['position']['x'],p['position']['y']),p['rotation'],ps)
        fl.append(dict(symbol='power:PWR_FLAG',reference=f'#FLG{base+i:03d}',value='PWR_FLAG',position=dict(x=x,y=y),rotation=rot))
    for i,p in enumerate(pwr,1): p['reference']=f'#PWR{base+i:03d}'
    json.dump(dict(all=parts+pwr+fl,labels=labels,lcsc={r:{'properties':{'LCSC':c}} for r,c in lcsc.items()},nc=[{'componentRef':r,'pinName':p} for r,p in nc],hier=list(hier)),open(name+'.json','w'))
    print(name,len(parts),'parts',len(pwr),'pwr',len(fl),'flags',sum(len(v) for v in labels.values()),'labels',len(nc),'nc')
