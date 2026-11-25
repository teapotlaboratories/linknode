import sys,json; sys.path.insert(0,sys.argv[1])
from blocks import *
import wires
S=Sheet(); S.labels=[]
X,Y=152.4,96.52   # U2 BQ25798
S.part('U2','Battery_Management:BQ25798','BQ25798RQMR','Package_DFN_QFN:Texas_RQM0029A_VQFN-29_4x4mm_P0.4mm',X,Y,0,'C2876593')
S.pwr('GND',X,Y+33.02)
# --- USB-C connector, CC, ESD ---
S.part('J1','Connector:USB_C_Receptacle_USB2.0_16P','TYPE-C-31-M-12','Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',25.4,76.2,0,'C165948')
S.pwr('GND',25.4,99.06); S.pwr('GND',17.78,99.06); S.pwr('FLAG',30.48,99.06,180)
S.w((25.4,99.06),(30.48,99.06))
S.w((40.64,60.96),(43.18,60.96),(43.18,53.34),(76.2,53.34)); S.pwr('VBUS',76.2,53.34)
S.part('TP1','Connector:TestPoint','VBUS',TP,50.8,53.34,0,None)
S.pwr('FLAG',58.42,53.34,0)
S.part('C1','Device:C_Small','100nF 50V',C,66.04,55.88,0,'C307331'); S.pwr('GND',66.04,58.42)
S.part('R1','Device:R_Small','5.1k',R,48.26,66.04,90,'C25905')   # pins 45.72 / 50.8
S.part('R2','Device:R_Small','5.1k',R,63.5,68.58,90,'C25905')    # pins 60.96 / 66.04
S.w((40.64,66.04),(45.72,66.04)); S.pwr('GND',50.8,66.04,90)
S.w((40.64,68.58),(60.96,68.58)); S.pwr('GND',66.04,68.58,90)
S.w((40.64,73.66),(43.18,73.66),(43.18,76.2)); S.w((40.64,76.2),(73.66,76.2))         # D-  (A7,B7) -> U1 I/O1
S.w((40.64,81.28),(45.72,81.28),(45.72,78.74)); S.w((40.64,78.74),(73.66,78.74))      # D+  (A6,B6) -> U1 I/O2
S.part('U1','Power_Protection:USBLC6-2SC6','USBLC6-2SC6','Package_TO_SOT_SMD:SOT-23-6',78.74,76.2,0,'C2827654')
S.pwr('VBUS',78.74,71.12); S.pwr('GND',78.74,83.82)
S.w((83.82,76.2),(91.44,76.2),(91.44,88.9),(142.24,88.9))      # D- flow-through -> BQ D-
S.w((83.82,78.74),(88.9,78.74),(88.9,91.44),(142.24,91.44))    # D+ flow-through -> BQ D+
S.w((101.6,88.9),(101.6,86.36),(104.14,86.36)); S.hier.append(('USB_DM',104.14,86.36,0,'bidirectional'))
S.w((99.06,91.44),(99.06,93.98),(101.6,93.98)); S.hier.append(('USB_DP',101.6,93.98,0,'bidirectional'))
# --- input FET pairs (Q1/Q2 USB, Q3/Q4 DC in: SI2318A 40 V for the 24 V input, P-12), common source; rot 90 + mirror y = rotate then flip X ---
S.part('Q1','Transistor_FET:AO3400A','AO3400A','Package_TO_SOT_SMD:SOT-23',96.52,48.26,90,'C20917')
S.part('Q2','Transistor_FET:AO3400A','AO3400A','Package_TO_SOT_SMD:SOT-23',114.3,48.26,90,'C20917',mirror=True)
S.part('Q3','Transistor_FET:AO3400A','SI2318A','Package_TO_SOT_SMD:SOT-23',96.52,66.04,90,'C2681218')
S.part('Q4','Transistor_FET:AO3400A','SI2318A','Package_TO_SOT_SMD:SOT-23',114.3,66.04,90,'C2681218',mirror=True)
for yc in (45.72,63.5): S.w((101.6,yc),(109.22,yc))
S.w((96.52,53.34),(96.52,55.88),(114.3,55.88),(114.3,53.34))
S.w((96.52,71.12),(96.52,73.66),(114.3,73.66),(114.3,71.12))
S.w((114.3,55.88),(127.0,55.88),(127.0,68.58)); S.w((127.0,73.66),(127.0,76.2),(142.24,76.2))       # ACDRV1 via R20
S.w((114.3,73.66),(121.92,73.66),(121.92,83.82),(124.46,83.82)); S.w((129.54,83.82),(142.24,83.82))   # ACDRV2 via R21
S.w((91.44,45.72),(86.36,45.72)); S.pwr('VBUS',86.36,45.72)
S.w((91.44,63.5),(86.36,63.5)); S.pwr('VDCIN',86.36,63.5)
S.w((119.38,45.72),(177.8,45.72)); S.w((139.7,45.72),(139.7,68.58),(142.24,68.58))   # CHG_VBUS
S.w((119.38,63.5),(139.7,63.5))
S.pwr('FLAG',134.62,45.72,0)
for ref,xx,val,lc,fp in (('C4',147.32,'10uF 25V','C15850',C8),('C5',162.56,'10uF 25V','C15850',C8),('C6',177.8,'100nF 50V','C307331',C)):
    S.part(ref,'Device:C_Small',val,fp,xx,48.26,0,lc); S.pwr('GND',xx,50.8)
S.w((142.24,73.66),(139.7,73.66)); S.pwr('VBUS',139.7,73.66,90)      # VAC1
S.w((142.24,81.28),(139.7,81.28)); S.pwr('VDCIN',139.7,81.28,90)    # VAC2
# --- left-side control pins: one column per part, upper pins further left ---
S.w((142.24,96.52),(91.44,96.52)); S.hier.append(('I2C_SCL',91.44,96.52,180,'bidirectional'))
S.w((142.24,99.06),(91.44,99.06)); S.hier.append(('I2C_SDA',91.44,99.06,180,'bidirectional'))
S.w((142.24,104.14),(91.44,104.14)); S.hier.append(('CHG_INT',91.44,104.14,180,'output'))
S.part('R10','Device:R_Small','10k',R,96.52,106.68,0,'C25744'); S.pwr('VCC_3V3',96.52,109.22,180)
S.w((142.24,106.68),(104.14,106.68))
S.part('R5','Device:R_Small','10k',R,104.14,109.22,0,'C25744'); S.pwr('GND',104.14,111.76)
S.w((142.24,111.76),(114.3,111.76))
S.part('SW1','Switch:SW_Push','PWR','Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A',114.3,116.84,90,'C318884'); S.pwr('GND',114.3,121.92)
S.w((142.24,116.84),(124.46,116.84),(124.46,147.32),(182.88,147.32),(182.88,104.14))   # ILIM_HIZ -> REGN loop
S.part('C13','Device:C_Small','4.7uF 16V',C6,129.54,149.86,0,'C19666'); S.pwr('GND',129.54,152.4)
S.w((142.24,119.38),(132.08,119.38))
S.part('R6','Device:R_Small','4.7k',R,132.08,121.92,0,'C25900'); S.pwr('GND',132.08,124.46)
S.w((142.24,124.46),(139.7,124.46),(139.7,134.62))                    # TS node
S.part('R7','Device:R_Small','5.23k',R,132.08,134.62,90,'C11631'); S.w((124.46,134.62),(129.54,134.62)); S.w((134.62,134.62),(139.7,134.62))
S.part('R8','Device:R_Small','30.1k',R,139.7,137.16,0,'C2076806'); S.pwr('GND',139.7,139.7)
S.w((139.7,134.62),(144.78,134.62)); S.hier.append(('TS',144.78,134.62,0,'bidirectional'))
# --- right-side power pins ---
S.w((162.56,68.58),(167.64,68.58),(167.64,58.42),(228.6,58.42))      # PMID
for ref,xx,val,lc,fp in (('C7',182.88,'10uF 25V','C15850',C8),('C8',198.12,'10uF 25V','C15850',C8),('C9',213.36,'10uF 25V','C15850',C8),('C10',228.6,'100nF 50V','C307331',C)):
    S.part(ref,'Device:C_Small',val,fp,xx,60.96,0,lc); S.pwr('GND',xx,63.5)
S.part('C11','Device:C_Small','47nF 50V',C,170.18,76.2,0,'C880605'); S.w((162.56,73.66),(170.18,73.66))
S.w((162.56,78.74),(182.88,78.74),(182.88,81.28))                       # SW1 -> L1
S.part('L1','Device:L_Small','2.2uH 3.2A','Inductor_SMD:L_Changjiang_FNR4030S',182.88,83.82,0,'C167869')
S.w((162.56,88.9),(182.88,88.9),(182.88,86.36))                         # SW2 -> L1
S.part('C12','Device:C_Small','47nF 50V',C,170.18,91.44,0,'C880605'); S.w((162.56,93.98),(170.18,93.98))
S.part('D2','Device:LED_Small','CHG','LED_SMD:LED_0603_1608Metric',167.64,99.06,0,'C2286'); S.w((162.56,99.06),(165.1,99.06))
S.part('R9','Device:R_Small','2.2k',R,175.26,99.06,90,'C25879'); S.w((170.18,99.06),(172.72,99.06)); S.w((177.8,99.06),(180.34,99.06),(180.34,104.14))
S.w((162.56,104.14),(182.88,104.14))
S.w((162.56,109.22),(167.64,109.22)); S.pwr('VSYS',167.64,109.22,270)
S.w((162.56,114.3),(167.64,114.3)); S.pwr('VBAT',167.64,114.3,270)
S.w((162.56,119.38),(165.1,119.38)); S.hier.append(('SDRV',165.1,119.38,0,'output'))   # ship FET Q13 gate on the Battery sheet (T25, BQ25798 Rev C Fig 7-15)
S.part('R4','Device:R_Small','100R',R,167.64,124.46,90,'C25076'); S.w((162.56,124.46),(165.1,124.46)); S.pwr('VCELL',170.18,124.46,270)   # BATP senses the cell side of the ship FET
# --- VSYS / VBAT decoupling rows ---
S.w((187.96,137.16),(279.4,137.16)); S.pwr('VSYS',187.96,137.16)
for i,xx in enumerate((193.04,208.28,223.52,238.76,254.0)):
    S.part(f'C{14+i}','Device:C_Small','10uF 10V',C6,xx,139.7,0,'C19702'); S.pwr('GND',xx,142.24)
S.part('C19','Device:C_Small','100nF 16V',C,269.24,139.7,0,'C1525'); S.pwr('GND',269.24,142.24)
S.part('TP3','Connector:TestPoint','VSYS',TP,279.4,137.16,0,None)
S.w((187.96,154.94),(223.52,154.94)); S.pwr('VBAT',187.96,154.94)
S.part('C20','Device:C_Small','10uF 10V',C6,193.04,157.48,0,'C19702'); S.pwr('GND',193.04,160.02)
S.part('C21','Device:C_Small','10uF 10V',C6,208.28,157.48,0,'C19702'); S.pwr('GND',208.28,160.02)
S.part('TP4','Connector:TestPoint','VBAT',TP,223.52,154.94,0,None)
S.part('TP5','Connector:TestPoint','GND',TP,238.76,160.02,0,None); S.pwr('GND',238.76,160.02)
# --- solar input ---
# External DC input (H-13, P-12): DC-005G board-edge jack (24 V 2.5 A), centre +; reverse P-FET Q11, TVS D1, 2R+2.2uF snubber (TI Fig 10-1 note 1)
S.part('J2','Connector:Barrel_Jack_Switch','DC-005G DC IN','linknode:DC-005G_Horizontal',22.86,121.92,0,'C692446')   # pins 1 (30.48,119.38) 3 (30.48,121.92) 2 (30.48,124.46)
S.w((30.48,119.38),(33.02,119.38))
S.w((30.48,121.92),(30.48,124.46),(30.48,127)); S.pwr('GND',30.48,127)
S.part('Q11','Transistor_FET:AO3401A','WST2319','Package_TO_SOT_SMD:SOT-23',38.1,121.92,90,'C2906299')   # reverse-polarity P-FET: D(33.02,119.38) S(43.18,119.38) G(38.1,127)
S.part('D3','Device:D_Zener_Small','BZT52C12','Diode_SMD:D_SOD-123',45.72,121.92,270,'C2891780')        # gate clamp: K at source
S.w((45.72,124.46),(45.72,127),(38.1,127))
S.part('R22','Device:R_Small','100k',R,38.1,129.54,0,'C25741')
S.part('D1','Device:D_Zener_Small','SMAJ24A','Diode_SMD:D_SMA',58.42,121.92,270,'C19077541')           # TVS, unidirectional
S.w((43.18,119.38),(99.06,119.38)); S.pwr('VDCIN',99.06,119.38,180); S.pwr('FLAG',50.8,119.38,0)
S.part('R3','Device:R_Small','2R','Resistor_SMD:R_0603_1608Metric',71.12,121.92,0,'C22977')
S.part('C2','Device:C_Small','2.2uF 50V',C8,71.12,129.54,0,'C377773'); S.w((71.12,124.46),(71.12,127)); S.pwr('GND',71.12,132.08)
S.part('C3','Device:C_Small','100nF 50V',C,81.28,121.92,0,'C307331'); S.pwr('GND',81.28,124.46)
S.part('TP2','Connector:TestPoint','VDCIN',TP,86.36,119.38,0,None)
S.part('R20','Device:R_Small','294R',R,127.0,71.12,0,'C477682')    # ACDRV1 gate resistor (TI Fig 10-1)
S.part('R21','Device:R_Small','294R',R,127.0,83.82,90,'C477682')   # ACDRV2 gate resistor
S.part('D4','Device:D_Zener_Small','BZT52C10','Diode_SMD:D_SOD-123',106.68,50.8,90,'C173431')   # Q1/Q2 gate clamp, K at gates
S.w((106.68,48.26),(106.68,45.72)); S.w((106.68,53.34),(106.68,55.88))
S.part('D5','Device:D_Zener_Small','BZT52C10','Diode_SMD:D_SOD-123',106.68,68.58,90,'C173431')   # Q3/Q4 gate clamp
S.w((106.68,66.04),(106.68,63.5)); S.w((106.68,71.12),(106.68,73.66))
S.pwr('GND',38.1,132.08); S.pwr('GND',58.42,124.46)   # appended last so existing #PWR numbers stay
plain,mir=S.payload(1)
json.dump(dict(plain=plain,mir=mir,hier=S.hier,labels=S.labels,nc=[['J1','A8'],['J1','B8']],lcsc={r:{'properties':{'LCSC':c}} for r,c in S.lcsc.items()},wires=S.wires,pins=wires.pinpoints(S.parts,S.pw)+[(x,y) for _,x,y,*r in S.hier]+[(x,y) for _,x,y,_ in S.labels]),open(sys.argv[1]+'/usb_w2.json','w'))
print(len(plain),'plain',len(mir),'mirrored',len(S.wires),'polylines')
