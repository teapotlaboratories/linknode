"""Hold-off sheet (T17b, P-8/P-9): VBAT comparator with hysteresis switches VSYS -> VSYS_SW (TPS61089 input).
On at VBAT ~3.63 V, off at ~3.32 V (owner, 2026-11-20). Values: Vref = TL432 1.25 V / 2 = 0.625 V (UMW TL432 p.3);
Voff = 0.625 x (1 + 432k/100k) = 3.32 V; Von = 0.625 x (1 + 432k/(100k||887k)) = 3.63 V.
LM2903 input common mode 0..VCC-2.0 V over temperature (onsemi LM393/D p.3) holds down to VSYS ~2.6 V.
A switch on the boost INPUT is needed: with only EN low, VIN reaches VOUT through the rectifier body diode (TPS61089 sec. 8.3.2)."""
import sys,json; sys.path.insert(0,sys.argv[1])
from blocks import *
import wires
S=Sheet()
LM='Comparator:LM2903'; SO8='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'
# --- VBAT sense divider + filter -> SNS bus (x=58.42)
S.pwr('VBAT',40.64,60.96); S.w((40.64,60.96),(40.64,63.5))
S.part('R301','Device:R_Small','432k',R,40.64,66.04,0,'C25787')
S.w((40.64,68.58),(40.64,73.66)); S.w((40.64,73.66),(40.64,76.2))
S.part('R302','Device:R_Small','100k',R,40.64,78.74,0,'C25741'); S.pwr('GND',40.64,81.28)
S.part('C301','Device:C_Small','100nF',C,33.02,76.2,0,'C1525'); S.pwr('GND',33.02,78.74)
S.w((33.02,73.66),(58.42,73.66))
S.w((58.42,68.58),(58.42,109.22))
S.w((58.42,68.58),(73.66,68.58))             # +A
S.w((58.42,101.6),(73.66,101.6))             # +B (unit B mirrored about x)
# --- comparators
S.part('U30','Comparator:LM2903','LM2903DR2G',SO8,81.28,71.12,0,'C57474',unit=1)
S.part('U30','Comparator:LM2903','LM2903DR2G',SO8,81.28,99.06,0,None,mirror=True,unit=2,mirror_axis='x')
S.part('U30','Comparator:LM2903','LM2903DR2G',SO8,134.62,104.14,0,None,unit=3)   # V+(132.08,96.52) V-(132.08,111.76)
S.pwr('VSYS',132.08,96.52); S.pwr('GND',132.08,111.76)
S.part('C304','Device:C_Small','100nF',C,124.46,104.14,0,'C1525')
S.w((124.46,101.6),(124.46,96.52),(132.08,96.52)); S.w((124.46,106.68),(124.46,111.76),(132.08,111.76))
# --- reference: TL432 1.25 V, 100k/100k -> VREF 0.625 V on the REF bus (x=66.04)
S.pwr('VSYS',111.76,78.74)
S.part('R303','Device:R_Small','10k',R,111.76,81.28,0,'C25744')
S.w((111.76,83.82),(111.76,86.36))
S.part('U31','Reference_Voltage:TL432DBZ','TL432 0.5%','Package_TO_SOT_SMD:SOT-23',111.76,88.9,90,'C545558')   # K(111.76,86.36) A(111.76,91.44) REF(109.22,88.9)
S.pwr('GND',111.76,91.44)
S.w((109.22,88.9),(109.22,86.36),(111.76,86.36))      # REF tied to K
S.w((111.76,83.82),(99.06,83.82))
S.part('R304','Device:R_Small','100k',R,99.06,86.36,0,'C25741')
S.w((99.06,88.9),(99.06,91.44))
S.part('R305','Device:R_Small','100k',R,99.06,93.98,0,'C25741'); S.pwr('GND',99.06,96.52)
S.w((99.06,88.9),(66.04,88.9))
S.w((66.04,73.66),(66.04,96.52)); S.w((66.04,73.66),(73.66,73.66)); S.w((66.04,96.52),(73.66,96.52))   # -A, -B
# --- hysteresis: OUTB pulls 887k from SNS to GND while the node is held off
S.w((88.9,99.06),(88.9,109.22),(78.74,109.22))
S.part('R309','Device:R_Small','887k',R,76.2,109.22,90,'C423127')
S.w((73.66,109.22),(58.42,109.22))
# --- OUTA -> CTRL (pull-up to VSYS) -> 2N7002 -> AO3401A gate
S.w((88.9,71.12),(121.92,71.12))
S.part('R306','Device:R_Small','100k',R,114.3,68.58,0,'C25741'); S.pwr('VSYS',114.3,66.04)
S.part('Q10','Transistor_FET:2N7002','2N7002','Package_TO_SOT_SMD:SOT-23',127.0,71.12,0,'C8545')   # G(121.92,71.12) S(129.54,76.2) D(129.54,66.04)
S.pwr('GND',129.54,76.2)
S.part('R307','Device:R_Small','10k',R,129.54,60.96,0,'C25744'); S.w((129.54,63.5),(129.54,66.04))   # Q10 D / Q12 D node
S.w((129.54,58.42),(129.54,55.88),(147.32,55.88))     # gate node
S.part('Q9','Transistor_FET:AO3401A','AO3401A','Package_TO_SOT_SMD:SOT-23',147.32,50.8,90,'C15127',mirror=True)   # S(142.24,48.26) D(152.4,48.26) G(147.32,55.88)
S.pwr('VSYS',129.54,48.26)
S.w((129.54,48.26),(142.24,48.26))
S.part('C302','Device:C_Small','10nF',C,134.62,50.8,0,'C15195'); S.w((134.62,53.34),(134.62,55.88))
S.part('R308','Device:R_Small','100k',R,139.7,50.8,0,'C25741'); S.w((139.7,53.34),(139.7,55.88))
S.w((152.4,48.26),(167.64,48.26)); S.pwr('VSYS_SW',167.64,48.26)
S.part('TP31','Connector:TestPoint','VSYS_SW',TP,160.02,48.26,0,None)
S.pwr('FLAG',157.48,48.26,0)
# --- USB bypass (P-13): VBUS present -> Q12 pulls the Q9 gate network low in parallel with Q10
S.part('Q12','Transistor_FET:2N7002','2N7002','Package_TO_SOT_SMD:SOT-23',147.32,86.36,0,'C8545')   # G(142.24,86.36) S(149.86,91.44) D(149.86,81.28)
S.w((149.86,81.28),(149.86,63.5),(129.54,63.5))
S.part('R310','Device:R_Small','10k',R,139.7,86.36,90,'C25744')
S.part('R311','Device:R_Small','100k',R,142.24,91.44,0,'C25741'); S.w((142.24,86.36),(142.24,88.9))
S.pwr('VBUS',137.16,86.36); S.pwr('GND',142.24,93.98); S.pwr('GND',149.86,91.44)
plain,mir=S.payload(600)
json.dump(dict(plain=plain,mir=mir,hier=S.hier,lcsc={r:{'properties':{'LCSC':c}} for r,c in S.lcsc.items()},wires=S.wires,pins=wires.pinpoints(S.parts,S.pw)),open(sys.argv[1]+'/holdoff_w.json','w'))
print(len(plain),'plain',len(mir),'single',len(S.wires),'polylines')
# check thresholds
vr=1.25/2; rb=100e3; ra=432e3; rh=887e3; par=1/(1/rb+1/rh)
print('Voff %.3f V  Von %.3f V'%(vr*(1+ra/rb),vr*(1+ra/par)))
