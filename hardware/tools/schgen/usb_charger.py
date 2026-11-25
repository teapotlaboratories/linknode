import json,sys
sys.path.insert(0,'.')
from gen import build
R0402='Resistor_SMD:R_0402_1005Metric'; C0402='Capacitor_SMD:C_0402_1005Metric'; C0603='Capacitor_SMD:C_0603_1608Metric'; C0805='Capacitor_SMD:C_0805_2012Metric'
P={'GND':'power:GND','VBUS':'power:VBUS','VSOLAR':'power:VCC','VSYS':'power:VCC','VBAT':'power:VCC','VCC_3V3':'power:VCC'}
G='GND'
spec=[
('J1','Connector:USB_C_Receptacle_USB2.0_16P','TYPE-C-31-M-12','Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',(30.48,58.42),0,{'VBUS':'VBUS','A5':'CC1','B5':'CC2','A6':'USB_DP','B6':'USB_DP','A7':'USB_DM','B7':'USB_DM','A8':None,'B8':None,'GND':G,'SH':G},'C165948'),
('R1','Device:R_Small','5.1k',R0402,(60.96,50.8),0,{'1':'CC1','2':G},'C25905'),
('R2','Device:R_Small','5.1k',R0402,(68.58,50.8),0,{'1':'CC2','2':G},'C25905'),
('U1','Power_Protection:USBLC6-2SC6','USBLC6-2SC6','Package_TO_SOT_SMD:SOT-23-6',(68.58,78.74),0,{'1':'USB_DP','6':'USB_DP','3':'USB_DM','4':'USB_DM','5':'VBUS','2':G},'C2827654'),
('C1','Device:C_Small','100nF 50V',C0402,(55.88,30.48),0,{'1':'VBUS','2':G},'C307331'),
('J2','Connector_Generic:Conn_01x02','Solar','Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical',(20.32,134.62),0,{'1':'VSOLAR_RAW','2':G},'C20079'),
('D1','Device:D_Schottky_Small','SS34','Diode_SMD:D_SMA',(35.56,134.62),180,{'A':'VSOLAR_RAW','K':'VSOLAR'},'C8678'),
('R3','Device:R_Small','2R',('Resistor_SMD:R_0603_1608Metric'),(50.8,129.54),0,{'1':'VSOLAR','2':'SNUB'},'C22977'),
('C2','Device:C_Small','2.2uF 50V',C0805,(48.26,142.24),0,{'1':'SNUB','2':G},'C377773'),
('C3','Device:C_Small','100nF 50V',C0402,(58.42,137.16),0,{'1':'VSOLAR','2':G},'C307331'),
('Q1','Transistor_FET:AO3400A','AO3400A','Package_TO_SOT_SMD:SOT-23',(96.52,35.56),0,{'D':'VBUS','S':'ACS1','G':'ACDRV1'},'C20917'),
('Q2','Transistor_FET:AO3400A','AO3400A','Package_TO_SOT_SMD:SOT-23',(114.3,35.56),0,{'D':'CHG_VBUS','S':'ACS1','G':'ACDRV1'},'C20917'),
('Q3','Transistor_FET:AO3400A','AO3400A','Package_TO_SOT_SMD:SOT-23',(96.52,127.0),0,{'D':'VSOLAR','S':'ACS2','G':'ACDRV2'},'C20917'),
('Q4','Transistor_FET:AO3400A','AO3400A','Package_TO_SOT_SMD:SOT-23',(114.3,127.0),0,{'D':'CHG_VBUS','S':'ACS2','G':'ACDRV2'},'C20917'),
('U2','Battery_Management:BQ25798','BQ25798RQMR','Package_DFN_QFN:Texas_RQM0029A_VQFN-29_4x4mm_P0.4mm',(167.64,91.44),0,
  {'2':'CHG_VBUS','3':'CHG_VBUS','VAC1':'VBUS','VAC2':'VSOLAR','ACDRV1':'ACDRV1','ACDRV2':'ACDRV2','D+':'USB_DP','D-':'USB_DM','SCL':'I2C_SCL','SDA':'I2C_SDA','~{INT}':'CHG_INT','~{CE}':'CE','~{QON}':'QON','ILIM_HIZ':'REGN','PROG':'PROG','TS':'TS','GND':G,'PMID':'PMID','BTST1':'BTST1','SW1':'SW1','SW2':'SW2','BTST2':'BTST2','STAT':'STAT','REGN':'REGN','SYS':'VSYS','22':'VBAT','23':'VBAT','SDRV':'SDRV','BATP':'BATP'},'C2876593'),
('C4','Device:C_Small','10uF 25V',C0805,(121.92,30.48),0,{'1':'CHG_VBUS','2':G},'C15850'),
('C5','Device:C_Small','10uF 25V',C0805,(129.54,30.48),0,{'1':'CHG_VBUS','2':G},'C15850'),
('C6','Device:C_Small','100nF 50V',C0402,(137.16,30.48),0,{'1':'CHG_VBUS','2':G},'C307331'),
('C7','Device:C_Small','10uF 25V',C0805,(190.5,30.48),0,{'1':'PMID','2':G},'C15850'),
('C8','Device:C_Small','10uF 25V',C0805,(198.12,30.48),0,{'1':'PMID','2':G},'C15850'),
('C9','Device:C_Small','10uF 25V',C0805,(205.74,30.48),0,{'1':'PMID','2':G},'C15850'),
('C10','Device:C_Small','100nF 50V',C0402,(213.36,30.48),0,{'1':'PMID','2':G},'C307331'),
('C11','Device:C_Small','47nF 50V',C0402,(190.5,58.42),0,{'1':'BTST1','2':'SW1'},'C880605'),
('C12','Device:C_Small','47nF 50V',C0402,(198.12,58.42),0,{'1':'BTST2','2':'SW2'},'C880605'),
('L1','Device:L_Small','2.2uH 3.2A','Inductor_SMD:L_Changjiang_FNR4030S',(215.9,50.8),0,{'1':'SW1','2':'SW2'},'C167869'),
('C13','Device:C_Small','4.7uF 16V',C0603,(190.5,86.36),0,{'1':'REGN','2':G},'C19666'),
('C14','Device:C_Small','10uF 10V',C0603,(220.98,101.6),0,{'1':'VSYS','2':G},'C19702'),
('C15','Device:C_Small','10uF 10V',C0603,(228.6,101.6),0,{'1':'VSYS','2':G},'C19702'),
('C16','Device:C_Small','10uF 10V',C0603,(236.22,101.6),0,{'1':'VSYS','2':G},'C19702'),
('C17','Device:C_Small','10uF 10V',C0603,(243.84,101.6),0,{'1':'VSYS','2':G},'C19702'),
('C18','Device:C_Small','10uF 10V',C0603,(251.46,101.6),0,{'1':'VSYS','2':G},'C19702'),
('C19','Device:C_Small','100nF 16V',C0402,(259.08,101.6),0,{'1':'VSYS','2':G},'C1525'),
('C20','Device:C_Small','10uF 10V',C0603,(220.98,127.0),0,{'1':'VBAT','2':G},'C19702'),
('C21','Device:C_Small','10uF 10V',C0603,(228.6,127.0),0,{'1':'VBAT','2':G},'C19702'),
('R4','Device:R_Small','100R',R0402,(243.84,127.0),0,{'1':'VBAT','2':'BATP'},'C25076'),
('C22','Device:C_Small','1nF 50V',C0402,(198.12,121.92),0,{'1':'SDRV','2':G},'C1523'),
('R5','Device:R_Small','10k',R0402,(121.92,104.14),0,{'1':'CE','2':G},'C25744'),
('R6','Device:R_Small','4.7k',R0402,(129.54,124.46),0,{'1':'PROG','2':G},'C25900'),
('R7','Device:R_Small','5.23k',R0402,(121.92,137.16),0,{'1':'REGN','2':'TS'},'C11631'),
('R8','Device:R_Small','30.1k',R0402,(121.92,149.86),0,{'1':'TS','2':G},'C2076806'),
('R9','Device:R_Small','2.2k',R0402,(205.74,81.28),0,{'1':'REGN','2':'STAT_LED'},'C25879'),
('D2','Device:LED_Small','CHG',('LED_SMD:LED_0603_1608Metric'),(215.9,83.82),180,{'A':'STAT_LED','K':'STAT'},'C2286'),
('R10','Device:R_Small','10k',R0402,(121.92,76.2),0,{'1':'VCC_3V3','2':'CHG_INT'},'C25744'),
('SW1','Switch:SW_Push','PWR','Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A',(149.86,152.4),0,{'1':'QON','2':G},'C318884'),
('TP1','Connector:TestPoint','VBUS','TestPoint:TestPoint_Pad_D1.0mm',(50.8,20.32),0,{'1':'VBUS'},None),
('TP2','Connector:TestPoint','VSOLAR','TestPoint:TestPoint_Pad_D1.0mm',(76.2,127.0),0,{'1':'VSOLAR'},None),
('TP3','Connector:TestPoint','VSYS','TestPoint:TestPoint_Pad_D1.0mm',(266.7,96.52),0,{'1':'VSYS'},None),
('TP4','Connector:TestPoint','VBAT','TestPoint:TestPoint_Pad_D1.0mm',(228.6,121.92),0,{'1':'VBAT'},None),
('TP5','Connector:TestPoint','GND','TestPoint:TestPoint_Pad_D1.0mm',(254.0,121.92),180,{'1':'GND'},None),
]
POS={'J1':(30.48,58.42),'R1':(63.5,50.8),'R2':(76.2,50.8),'U1':(68.58,78.74),'C1':(63.5,25.4),'J2':(20.32,134.62),'D1':(35.56,134.62),'R3':(50.8,129.54),'C2':(50.8,142.24),'C3':(63.5,134.62),
'Q1':(96.52,35.56),'Q2':(114.3,35.56),'Q3':(96.52,127.0),'Q4':(114.3,127.0),'U2':(167.64,91.44),
'C4':(129.54,22.86),'C5':(142.24,22.86),'C6':(154.94,22.86),'C7':(190.5,22.86),'C8':(203.2,22.86),'C9':(215.9,22.86),'C10':(228.6,22.86),
'C11':(190.5,50.8),'C12':(203.2,50.8),'L1':(215.9,50.8),'C13':(190.5,76.2),'R9':(203.2,76.2),'D2':(215.9,83.82),
'C14':(190.5,101.6),'C15':(203.2,101.6),'C16':(215.9,101.6),'C17':(228.6,101.6),'C18':(241.3,101.6),'C19':(254.0,101.6),
'C20':(190.5,127.0),'C21':(203.2,127.0),'R4':(215.9,127.0),'C22':(241.3,127.0),'R5':(134.62,104.14),'R6':(134.62,121.92),'R7':(134.62,137.16),'R8':(134.62,149.86),'R10':(134.62,76.2),'SW1':(149.86,152.4),
'TP1':(50.8,20.32),'TP2':(76.2,127.0),'TP3':(266.7,96.52),'TP4':(228.6,121.92),'TP5':(254.0,121.92)}
spec=[(c[0],c[1],c[2],c[3],POS[c[0]],*c[5:]) for c in spec]
parts,pwr,labels,lcsc,nc=build(spec,P,None)
json.dump(dict(parts=parts,pwr=pwr,labels=labels,lcsc=lcsc,nc=nc),open('usb_charger.json','w'),indent=0)
print(len(parts),'parts',len(pwr),'power syms',sum(len(v) for v in labels.values()),'labels',len(nc),'nc')
