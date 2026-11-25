R='Resistor_SMD:R_0402_1005Metric'; C='Capacitor_SMD:C_0402_1005Metric'; C6='Capacitor_SMD:C_0603_1608Metric'; C8='Capacitor_SMD:C_0805_2012Metric'
TP='TestPoint:TestPoint_Pad_D1.0mm'
class Sheet:
    def __init__(s): s.parts=[]; s.pw=[]; s.wires=[]; s.pinpts=[]; s.hier=[]; s.lcsc={}; s.n=0
    def part(s,ref,lib,val,fp,x,y,rot=0,lcsc=None,mirror=False,unit=1,mirror_axis='y'):
        s.parts.append(dict(symbol=lib,reference=ref,value=val,footprint=fp,position=dict(x=round(x,2),y=round(y,2)),rotation=rot,mirror=(mirror_axis if mirror else False),unit=unit))
        if lcsc: s.lcsc[ref]=lcsc
    def pwr(s,net,x,y,rot=None):
        lib='power:GND' if net=='GND' else ('power:PWR_FLAG' if net=='FLAG' else 'power:VCC')
        if rot is None: rot=0
        s.pw.append(dict(symbol=lib,net=net,position=dict(x=round(x,2),y=round(y,2)),rotation=rot))
    def w(s,*pts): s.wires.append([(round(a,2),round(b,2)) for a,b in pts])
    def payload(s,base):
        out=[];i=f=0
        for p in s.pw:
            if p['net']=='FLAG': f+=1; ref=f'#FLG{base+f:03d}'; val='PWR_FLAG'
            else: i+=1; ref=f'#PWR{base+i:03d}'; val=p['net']
            out.append(dict(symbol=p['symbol'],reference=ref,value=val,position=p['position'],rotation=p['rotation']))
        plain=[{k:v for k,v in p.items() if k not in ('mirror','unit')} for p in s.parts if not p['mirror'] and p.get('unit',1)==1]
        mirrored=[p for p in s.parts if p['mirror'] or p.get('unit',1)!=1]   # placed one by one (mirror and/or unit)
        return plain+out, mirrored

def tlv(S,x,y,n,out,rtop,rtop_c,en_mode,en_net=None,ren=None,ren_c=None,cen=None,cen_c=None,cout2=False,tp=None):
    """TLV62569DBV buck. en_mode 'rc' (R from 5V, C to GND) or 'gpio' (hier label + 100k pull-down)."""
    i=n*10; yt=y-12.7
    S.part(f'U{n}','Regulator_Switching:TLV62569DBV','TLV62569DBVR','Package_TO_SOT_SMD:SOT-23-5',x,y,0,'C141836')
    S.pwr('GND',x,y+7.62)
    # input
    S.pwr('VCC5V0_SYS',x-25.4,yt)
    S.w((x-25.4,yt),(x-12.7,yt),(x-12.7,y-2.54),(x-7.62,y-2.54))
    S.part(f'C{i}','Device:C_Small','4.7uF 16V',C6,x-17.78,yt+2.54,0,'C19666'); S.pwr('GND',x-17.78,yt+5.08)
    if en_mode=='rc':
        S.part(f'R{i}','Device:R_Small',ren,R,x-25.4,y-2.54,0,ren_c)
        S.w((x-25.4,y-5.08),(x-25.4,yt))
        S.w((x-25.4,y),(x-7.62,y))
        S.part(f'C{i+1}','Device:C_Small',cen,C,x-20.32,y+2.54,0,cen_c); S.pwr('GND',x-20.32,y+5.08)
    else:
        S.w((x-27.94,y),(x-7.62,y))
        S.hier.append((en_net,x-27.94,y,180,'input'))
        S.part(f'R{i}','Device:R_Small','100k',R,x-20.32,y+2.54,0,'C25741'); S.pwr('GND',x-20.32,y+5.08)
    # output
    S.part(f'L{n}','Device:L_Small','2.2uH 3A','Inductor_SMD:L_1008_2520Metric',x+12.7,y-2.54,90,'C22471111')
    S.w((x+7.62,y-2.54),(x+10.16,y-2.54))
    xe=x+60.96 if cout2 else x+53.34
    S.w((x+15.24,y-2.54),(xe,y-2.54))
    S.part(f'R{i+1}','Device:R_Small',rtop,R,x+22.86,y,0,rtop_c)
    S.part(f'R{i+2}','Device:R_Small','100k',R,x+22.86,y+7.62,0,'C25741'); S.pwr('GND',x+22.86,y+10.16); S.w((x+22.86,y+2.54),(x+22.86,y+5.08))
    S.w((x+7.62,y),(x+17.78,y),(x+17.78,y+2.54),(x+22.86,y+2.54))
    cff=f'C{i+2}' if en_mode=='rc' else f'C{i+1}'
    S.part(cff,'Device:C_Small','6.8pF',C,x+33.02,y,0,'C1576')
    S.w((x+22.86,y+2.54),(x+33.02,y+2.54))
    co=f'C{i+3}' if en_mode=='rc' else f'C{i+2}'
    S.part(co,'Device:C_Small','10uF 10V',C6,x+43.18,y,0,'C19702'); S.pwr('GND',x+43.18,y+2.54)
    if cout2:
        co2=f'C{i+3}'
        S.part(co2,'Device:C_Small','10uF 10V',C6,x+53.34,y,0,'C19702'); S.pwr('GND',x+53.34,y+2.54)
    S.pwr(out,xe,y-2.54)
    if tp: S.part(tp,'Connector:TestPoint',out,TP,xe-2.54,y-2.54,0,None)
    S.pwr('FLAG',x+27.94,y-2.54,0)

def boost(S,x,y):
    """TPS61089 VSYS -> VCC5V0_SYS. Values per TPS61089 eq. 3-19 (see worklog)."""
    S.part('U4','Regulator_Switching:TPS61089','TPS61089RNRR','Package_DFN_QFN:Texas_VQFN-RNR0011A-11',x,y,0,'C165129')
    S.pwr('GND',x,y+12.7)
    # switch node, inductor, boot, fsw
    S.w((x-10.16,y-7.62),(x-27.94,y-7.62))
    S.part('L2','Device:L_Small','2.2uH 7.5A','Inductor_SMD:L_Changjiang_FNR4020S',x-30.48,y-7.62,90,'C602029')
    S.w((x-33.02,y-7.62),(x-35.56,y-7.62),(x-35.56,y+5.08))
    S.part('C26','Device:C_Small','100nF',C,x-15.24,y-5.08,0,'C1525')
    S.w((x-15.24,y-2.54),(x-15.24,y),(x-10.16,y))
    S.part('R13','Device:R_Small','316k',R,x-22.86,y-5.08,0,'C25777')
    S.w((x-22.86,y-2.54),(x-22.86,y+2.54),(x-10.16,y+2.54))
    # input
    S.w((x-10.16,y+5.08),(x-45.72,y+5.08)); S.pwr('VSYS_SW',x-45.72,y+5.08)   # switched by the Hold-off sheet (T17b)
    S.part('C24','Device:C_Small','10uF 25V',C8,x-43.18,y+7.62,0,'C15850'); S.pwr('GND',x-43.18,y+10.16)
    S.part('C25','Device:C_Small','100nF',C,x-27.94,y+7.62,0,'C1525'); S.pwr('GND',x-27.94,y+10.16)
    S.part('R18','Device:R_Small','100k',R,x-17.78,y+7.62,0,'C25741')
    S.w((x-17.78,y+10.16),(x-12.7,y+10.16),(x-12.7,y+7.62),(x-10.16,y+7.62))
    # output rail, feedback
    S.w((x+10.16,y-7.62),(x+106.68,y-7.62)); S.pwr('VCC5V0_SYS',x+106.68,y-7.62)
    S.part('R15','Device:R_Small','316k',R,x+45.72,y-5.08,0,'C25777')
    S.w((x+10.16,y-2.54),(x+45.72,y-2.54))
    S.part('R16','Device:R_Small','100k',R,x+45.72,y+2.54,0,'C25741'); S.w((x+45.72,y-2.54),(x+45.72,y)); S.pwr('GND',x+45.72,y+5.08)
    # compensation
    S.w((x+10.16,y+2.54),(x+35.56,y+2.54))
    S.part('R17','Device:R_Small','8.06k',R,x+27.94,y+5.08,0,'C276278')
    S.part('C28','Device:C_Small','6.8nF',C,x+27.94,y+12.7,0,'C1542'); S.w((x+27.94,y+7.62),(x+27.94,y+10.16)); S.pwr('GND',x+27.94,y+15.24)
    S.part('C29','Device:C_Small','22pF',C,x+35.56,y+5.08,0,'C1555'); S.pwr('GND',x+35.56,y+7.62)
    # ILIM, VCC
    S.w((x+10.16,y+5.08),(x+20.32,y+5.08))
    S.part('R14','Device:R_Small','180k',R,x+20.32,y+7.62,0,'C25760'); S.pwr('GND',x+20.32,y+10.16)
    S.w((x+10.16,y+7.62),(x+12.7,y+7.62))
    S.part('C27','Device:C_Small','2.2uF',C6,x+12.7,y+10.16,0,'C23630'); S.pwr('GND',x+12.7,y+12.7)
    # output caps
    for ref,xo,val,lc,fp in (('C30',53.34,'22uF 25V','C45783',C8),('C31',68.58,'22uF 25V','C45783',C8),('C32',83.82,'22uF 25V','C45783',C8),('C33',99.06,'100nF','C1525',C)):
        S.part(ref,'Device:C_Small',val,fp,x+xo,y-5.08,0,lc); S.pwr('GND',x+xo,y-2.54)
    S.part('TP7','Connector:TestPoint','5V0',TP,x+50.8,y-7.62,0,None)
