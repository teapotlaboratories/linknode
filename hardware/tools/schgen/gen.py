import json,sys,symlib
POWER_BASE={'power:GND':270,'power:VCC':90,'power:VBUS':90}
def build(spec, power_nets, hier):
    parts=[];pwr=[];labels={};lcsc={};nc=[];n=1
    seen=set()
    for c in spec:
        ref,lib,val,fp,pos,rot,nets,code=c
        parts.append(dict(symbol=lib,reference=ref,value=val,footprint=fp,position=dict(x=pos[0],y=pos[1]),rotation=rot))
        if code: lcsc[ref]=code
        pins=symlib.pins(lib)
        for key,net in nets.items():
            ps=[p for p in pins if p['num']==key] or [p for p in pins if p['name']==key]
            assert ps, (ref,key)
            if net is None:
                for p in ps: nc.append((ref,p['num'])); 
                continue
            if net in power_nets:
                for p in ps:
                    x,y,a=symlib.endpoint(pos,rot,p)
                    if (x,y) in seen: continue
                    seen.add((x,y))
                    plib=power_nets[net]; away=(a+180)%360
                    prot=(away-POWER_BASE[plib])%360
                    pwr.append(dict(symbol=plib,reference=f'#PWR{n:03d}',value=net,position=dict(x=x,y=y),rotation=prot)); n+=1
            else:
                x,y,a=symlib.endpoint(pos,rot,ps[0])
                if (x,y) in seen: continue
                seen.add((x,y)); labels.setdefault(ref,{})[ps[0]['num']]=net
    return parts,pwr,labels,lcsc,nc
