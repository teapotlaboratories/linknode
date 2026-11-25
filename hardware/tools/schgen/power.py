import sys; sys.path.insert(0,'.')
from sheet import run
R='Resistor_SMD:R_0402_1005Metric'; C='Capacitor_SMD:C_0402_1005Metric'; C6='Capacitor_SMD:C_0603_1608Metric'; C8='Capacitor_SMD:C_0805_2012Metric'
G='GND'
P={'GND':'power:GND','VSYS':'power:VCC','VCC5V0_SYS':'power:VCC','VDD_0V9':'power:VCC','VDD_ARM':'power:VCC','VCC_DDR':'power:VCC','VCC_1V8':'power:VCC','VCC_3V3':'power:VCC'}
spec=[
('U4','Regulator_Switching:TPS61089','TPS61089RNRR','Package_DFN_QFN:Texas_VQFN-RNR0011A-11',(63.5,63.5),0,{'SW':'B_SW','BOOT':'B_BOOT','FSW':'B_FSW','VIN':'VSYS','EN':'B_EN','VOUT':'VCC5V0_SYS','FB':'B_FB','COMP':'B_COMP','ILIM':'B_ILIM','VCC':'B_VCC','GND':G},'C165129'),
('L2','Device:L_Small','2.2uH 7.5A','Inductor_SMD:L_Changjiang_FNR4020S',(30.48,38.1),90,{'1':'VSYS','2':'B_SW'},'C602029'),
('C24','Device:C_Small','10uF 25V',C8,(17.78,63.5),0,{'1':'VSYS','2':G},'C15850'),
('C25','Device:C_Small','100nF',C,(27.94,63.5),0,{'1':'VSYS','2':G},'C1525'),
('C26','Device:C_Small','100nF',C,(38.1,63.5),0,{'1':'B_BOOT','2':'B_SW'},'C1525'),
('R13','Device:R_Small','316k',R,(17.78,86.36),0,{'1':'B_FSW','2':'B_SW'},'C25777'),
('R18','Device:R_Small','100k',R,(30.48,86.36),0,{'1':'VSYS','2':'B_EN'},'C25741'),
('C27','Device:C_Small','2.2uF',C6,(93.98,88.9),0,{'1':'B_VCC','2':G},'C23630'),
('R14','Device:R_Small','180k',R,(104.14,88.9),0,{'1':'B_ILIM','2':G},'C25760'),
('R15','Device:R_Small','316k',R,(93.98,30.48),0,{'1':'VCC5V0_SYS','2':'B_FB'},'C25777'),
('R16','Device:R_Small','100k',R,(93.98,43.18),0,{'1':'B_FB','2':G},'C25741'),
('R17','Device:R_Small','8.06k',R,(116.84,73.66),0,{'1':'B_COMP','2':'B_COMPRC'},'C276278'),
('C28','Device:C_Small','6.8nF',C,(116.84,86.36),0,{'1':'B_COMPRC','2':G},'C1542'),
('C29','Device:C_Small','22pF',C,(127.0,80.01),0,{'1':'B_COMP','2':G},'C1555'),
('C30','Device:C_Small','22uF 25V',C8,(17.78,124.46),0,{'1':'VCC5V0_SYS','2':G},'C45783'),
('C31','Device:C_Small','22uF 25V',C8,(30.48,124.46),0,{'1':'VCC5V0_SYS','2':G},'C45783'),
('C32','Device:C_Small','22uF 25V',C8,(43.18,124.46),0,{'1':'VCC5V0_SYS','2':G},'C45783'),
('C33','Device:C_Small','100nF',C,(55.88,124.46),0,{'1':'VCC5V0_SYS','2':G},'C1525'),
('TP7','Connector:TestPoint','5V0','TestPoint:TestPoint_Pad_D1.0mm',(68.58,119.38),0,{'1':'VCC5V0_SYS'},None),
]
def rail(tag,x,y,out,rtop,rtop_c,ren,ren_c,cen,cen_c,n):
    U=f'U{n}'; i=n*10
    return [
    (U,'Regulator_Switching:TLV62569DBV','TLV62569DBVR','Package_TO_SOT_SMD:SOT-23-5',(x,y),0,{'EN':f'{tag}_EN','VIN':'VCC5V0_SYS','SW':f'{tag}_SW','FB':f'{tag}_FB','GND':G},'C141836'),
    (f'C{i}','Device:C_Small','4.7uF 16V',C6,(x-17.78,y+7.62),0,{'1':'VCC5V0_SYS','2':G},'C19666'),
    (f'R{i}','Device:R_Small',ren,R,(x-27.94,y-5.08),0,{'1':'VCC5V0_SYS','2':f'{tag}_EN'},ren_c),
    (f'C{i+1}','Device:C_Small',cen,C,(x-27.94,y+10.16),0,{'1':f'{tag}_EN','2':G},cen_c),
    (f'L{n}','Device:L_Small','2.2uH 3A','Inductor_SMD:L_1008_2520Metric',(x+17.78,y-7.62),90,{'1':f'{tag}_SW','2':out},'C22471111'),
    (f'R{i+1}','Device:R_Small',rtop,R,(x+27.94,y+2.54),0,{'1':out,'2':f'{tag}_FB'},rtop_c),
    (f'R{i+2}','Device:R_Small','100k',R,(x+27.94,y+15.24),0,{'1':f'{tag}_FB','2':G},'C25741'),
    (f'C{i+2}','Device:C_Small','6.8pF',C,(x+38.1,y+2.54),0,{'1':out,'2':f'{tag}_FB'},'C1576'),
    (f'C{i+3}','Device:C_Small','10uF 10V',C6,(x+48.26,y+7.62),0,{'1':out,'2':G},'C19702'),
    (f'TP{n+10}','Connector:TestPoint',out,'TestPoint:TestPoint_Pad_D1.0mm',(x+58.42,y+2.54),0,{'1':out},None),
    ]
spec+=rail('R09',165.1,40.64,'VDD_0V9','47k','C25792','100k','C25741','10nF','C15195',5)
spec+=rail('RDDR',165.1,93.98,'VCC_DDR','124k','C36777','100k','C25741','100nF','C1525',6)
spec+=rail('R18V',165.1,144.78,'VCC_1V8','200k','C25764','100k','C25741','100nF','C1525',7)
spec+=rail('R33',83.82,144.78,'VCC_3V3','453k','C27009','200k','C25764','100nF','C1525',8)
spec+=[('R19','Device:R_Small','0R',R,(254.0,40.64),90,{'1':'VDD_0V9','2':'VDD_ARM'},'C17168')]
flags=[('C30','1',0),('C53','1',0),('R19','2',0),('C63','1',0),('C73','1',0),('C83','1',0)]
run('power',spec,P,flags=flags,base=200)
