import sys; sys.path.insert(0,'.')
from sheet import run
R='Resistor_SMD:R_0402_1005Metric'; C='Capacitor_SMD:C_0402_1005Metric'; C6='Capacitor_SMD:C_0603_1608Metric'; C8='Capacitor_SMD:C_0805_2012Metric'
G='GND'
P={'GND':'power:GND','VCC5V0_SYS':'power:VCC','VCC3V3_ESP32':'power:VCC','VCC3V3_C5':'power:VCC','VCC3V3_HALOW':'power:VCC','VDD_FEM':'power:VCC'}
def rail(tag,x,y,out,en,n):
    i=n*10
    return [
    (f'U{n}','Regulator_Switching:TLV62569DBV','TLV62569DBVR','Package_TO_SOT_SMD:SOT-23-5',(x,y),0,{'EN':en,'VIN':'VCC5V0_SYS','SW':f'{tag}_SW','FB':f'{tag}_FB','GND':G},'C141836'),
    (f'C{i}','Device:C_Small','4.7uF 16V',C6,(x-17.78,y+7.62),0,{'1':'VCC5V0_SYS','2':G},'C19666'),
    (f'R{i}','Device:R_Small','100k',R,(x-27.94,y+7.62),0,{'1':en,'2':G},'C25741'),
    (f'L{n}','Device:L_Small','2.2uH 3A','Inductor_SMD:L_1008_2520Metric',(x+17.78,y-7.62),90,{'1':f'{tag}_SW','2':out},'C22471111'),
    (f'R{i+1}','Device:R_Small','453k',R,(x+27.94,y+2.54),0,{'1':out,'2':f'{tag}_FB'},'C27009'),
    (f'R{i+2}','Device:R_Small','100k',R,(x+27.94,y+15.24),0,{'1':f'{tag}_FB','2':G},'C25741'),
    (f'C{i+1}','Device:C_Small','6.8pF',C,(x+38.1,y+2.54),0,{'1':out,'2':f'{tag}_FB'},'C1576'),
    (f'C{i+2}','Device:C_Small','10uF 10V',C6,(x+48.26,y+7.62),0,{'1':out,'2':G},'C19702'),
    (f'C{i+3}','Device:C_Small','10uF 10V',C6,(x+58.42,y+7.62),0,{'1':out,'2':G},'C19702'),
    (f'TP{n+10}','Connector:TestPoint',out,'TestPoint:TestPoint_Pad_D1.0mm',(x+68.58,y+2.54),0,{'1':out},None),
    ]
spec=[]
spec+=rail('RESP',165.1,40.64,'VCC3V3_ESP32','ESP32_PWR_EN',9)
spec+=rail('RC5',165.1,93.98,'VCC3V3_C5','C5_PWR_EN',10)
spec+=rail('RHL',165.1,144.78,'VCC3V3_HALOW','HALOW_PWR_EN',11)
spec+=[
('Q7','Transistor_FET:AO3401A','AO3401A','Package_TO_SOT_SMD:SOT-23',(68.58,60.96),0,{'S':'VCC5V0_SYS','D':'VDD_FEM','G':'FEM_G'},'C15127'),
('R120','Device:R_Small','100k',R,(50.8,48.26),0,{'1':'VCC5V0_SYS','2':'FEM_G'},'C25741'),
('C120','Device:C_Small','10nF',C,(40.64,48.26),0,{'1':'VCC5V0_SYS','2':'FEM_G'},'C15195'),
('R121','Device:R_Small','10k',R,(50.8,73.66),0,{'1':'FEM_G','2':'FEM_PD'},'C25744'),
('Q8','Transistor_FET:2N7002','2N7002','Package_TO_SOT_SMD:SOT-23',(48.26,93.98),0,{'D':'FEM_PD','S':G,'G':'HALOW_FEM_EN'},'C8545'),
('R122','Device:R_Small','100k',R,(33.02,101.6),0,{'1':'HALOW_FEM_EN','2':G},'C25741'),
('C121','Device:C_Small','22uF 25V',C8,(88.9,73.66),0,{'1':'VDD_FEM','2':G},'C45783'),
('C122','Device:C_Small','100nF',C,(99.06,73.66),0,{'1':'VDD_FEM','2':G},'C1525'),
('TP22','Connector:TestPoint','VDD_FEM','TestPoint:TestPoint_Pad_D1.0mm',(109.22,68.58),0,{'1':'VDD_FEM'},None),
]
flags=[('C92','1',0),('C102','1',0),('C112','1',0),('C121','1',0),('C90','1',0)]
run('radio_power',spec,P,flags=flags,base=300)
