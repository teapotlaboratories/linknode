import sys; sys.path.insert(0,'.')
from sheet import run
R='Resistor_SMD:R_0402_1005Metric'; C='Capacitor_SMD:C_0402_1005Metric'
P={'GND':'power:GND','VBAT':'power:VCC'}
spec=[
('J3','Connector_Generic:Conn_01x02','Battery 1S','TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal',(38.1,88.9),180,{'1':'VCELL','2':'CELL_N'},'C474881'),
# T25 (2026-11-21): ship FET Q13 AO3400A (D VCELL, S VBAT, G SDRV) and the VCELL/VBAT symbols were added by scripting server + applywires
# on the drawn sheet. T27 (2026-11-21): TH1 removed, J4 KF301-5.0-2P (pin 1 TS, pin 2 GND) for the pack NTC; (see docs/worklog/2026-11-21-pcb-kickoff-cont.md); this older generator is kept for reference only.
('R11','Device:R_Small','100R',R,(78.74,63.5),90,{'1':'DW_VCC','2':'VCELL'},'C25076'),
('C23','Device:C_Small','100nF',C,(88.9,76.2),0,{'1':'DW_VCC','2':'CELL_N'},'C1525'),
('U3','Battery_Management:DW01A','DW01A','Package_TO_SOT_SMD:SOT-23-6',(114.3,78.74),0,{'VCC':'DW_VCC','GND':'CELL_N','TD':'CELL_N','OD':'DW_OD','OC':'DW_OC','CS':'DW_CS'},'C351410'),
('R12','Device:R_Small','1k',R,(139.7,76.2),90,{'1':'DW_CS','2':'GND'},'C11702'),
('Q5','linknode:FS8205A','FS8205A','Package_TO_SOT_SMD:SOT-23-6',(114.3,111.76),0,{'S1':'CELL_N','S2':'GND','2':'PROT_D','G1':'DW_OD','G2':'DW_OC'},'C908265'),
('Q6','linknode:FS8205A','FS8205A','Package_TO_SOT_SMD:SOT-23-6',(114.3,134.62),0,{'S1':'CELL_N','S2':'GND','2':'PROT_D','G1':'DW_OD','G2':'DW_OC'},'C908265'),
('TH1','Device:Thermistor_NTC','10k B3435','Resistor_SMD:R_0603_1608Metric',(190.5,88.9),0,{'1':'TS','2':'GND'},'C2889048'),
('TP6','Connector:TestPoint','CELL_N','TestPoint:TestPoint_Pad_D1.0mm',(63.5,101.6),0,{'1':'CELL_N'},None),
]
run('battery',spec,P,flags=[('J3','2',180)],hier=[('TH1','1','TS')],base=100)
