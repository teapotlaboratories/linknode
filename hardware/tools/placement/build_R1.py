import json, pcbnew
S='scratch'
b=pcbnew.LoadBoard('/home/argonite/Developments/klepon/hardware/kicad/linknode.kicad_pcb')
U=b.FindFootprintByReference('U100'); P={p.GetNumber():(p.GetPosition().x/1e6,p.GetPosition().y/1e6) for p in U.Pads() if p.GetNumber()}
cx,cy=148,142; L=2.5
def lane(a,z):
    xs=[P[str(k)][0] for k in range(a,z+1)]; ys=[P[str(k)][1] for k in range(a,z+1)]
    x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys)
    if x1<cx-5: return [x0-0.5-L, y0-0.25, x0-0.4, y1+0.25]
    if x0>cx+5: return [x1+0.4, y0-0.25, x1+0.5+L, y1+0.25]
    if y1<cy-5: return [x0-0.25, y0-0.5-L, x1+0.25, y0-0.4]
    return [x0-0.25, y1+0.4, x1+0.25, y1+0.5+L]
K=[lane(11,18),lane(25,27),lane(38,46),lane(59,64),lane(65,66),lane(72,80),lane(83,91),lane(104,114)]
parts=[]
def t(r,ic,p,**k): parts.append(dict(ref=r,to=[ic,str(p)],**k))
def at(r,x,y,**k): parts.append(dict(ref=r,to=[x,y],**k))
parts.append(dict(ref='U30',fixed=[178,108,0]))
for r,p in (('C304',8),('C301',8),('U31',3),('R301',3),('R302',3),('R303',2),('R304',2),('R305',5),('R306',5),('R309',6),('Q10',1),('Q12',7),('R310',7),('R311',7)): t(r,'U30',p)
t('Q13','J3',1); at('U3',106,112); t('C23','U3',5); t('R12','U3',2); t('R11','U3',5); t('Q5','U3',1); t('Q6','U3',3); t('TP6','J3',2)
t('Y501','U100',68,lanes_ok=True); t('C502','U100',68,lanes_ok=True); t('R501','U100',69,lanes_ok=True); t('R502','Y501',1); t('C501','Y501',1)
t('Y502','U100',21); t('C503','Y502',1); t('C504','Y502',2)
small=(('C606',115),('C607',115),('C610',10),('C611',51),('C612',54),('C613',55),('C614',67),('C615',71),('C616',82),('C617',103),('C618',116),('C619',55),('C620',71),
 ('C623',50),('C624',56),('C625',31),('C626',53),('C627',70),('C628',53),('C629',13),('C630',28),('C631',43),('C632',61),('C633',81),('C634',88),('C635',101),('C636',108),
 ('C601',96),('C602',24),('C603',1),('C604',19),('C637',30))
for r,p in small: t(r,'U100',p,margin=0.15)
for r,p in (('C605',115),('C608',54),('C609',103),('C621',49),('C622',56)): t(r,'U100',p,margin=0.15)
for r,p in (('R511',15),('R508',27),('R509',26),('R512',38),('R513',111)): t(r,'U100',p,lanes_ok=True)
for r,p in (('FB601',96),('R601',24),('R602',1),('R603',19),('R604',52),('R605',102),('R19',115),('C505',66),('R503',66),('C506',25),('R506',25),('R507',25),
            ('C507',23),('R510',23),('TP501',23),('R504',64),('R505',65),('R403',11)): t(r,'U100',p)
for r,p in (('C33',6),('C30',6),('C32',6),('C31',6),('C24',9),('C25',9),('C26',10),('C27',2),('R13',1),('R14',8),('R15',3),('R16',3),('R17',4),('C29',4),('C28',4),('R18',7),('TP7',6)): t(r,'U4',p,margin=0.15)
for u,xy in (('U5',(124,133)),('U6',(124,145)),('U7',(141,158)),('U8',(146,159))):
    n=u[1]; at(u,*xy); t('C%s0'%n,u,4); t('L'+n,u,3); t('C%s3'%n,'L'+n,2)
    for r in ('C%s2'%n,'R%s1'%n,'R%s2'%n): t(r,u,5,margin=0.15)
    for r in ('C%s1'%n,'R%s0'%n): t(r,u,1)
    t('TP1%s'%n,'L'+n,2)
t('Q9','L2',1); t('C302','Q9',1); t('R308','Q9',1); t('R307','Q9',1); t('TP31','Q9',3)
json.dump(dict(margin=0.3,keepouts=K,parts=parts),open(S+'/place/R1.json','w'))
print(len(parts),'parts')
