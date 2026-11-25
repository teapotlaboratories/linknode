"""GPS sheet (T18): ATGM336H-5NR32-G, ME6211 3.3 V switched LDO from VSYS, XC6206 backup LDO from VBAT, U.FL + 47 nH antenna bias.
Values per ATGM336H-5NR32-G manual p.7-11, ME6211 datasheet p.2/p.4/p.6, XC6206 datasheet p.1-2."""
import sys,json; sys.path.insert(0,sys.argv[1])
from blocks import *
import wires
S=Sheet()
# GNSS module
S.part('U20','linknode:ATGM336H','ATGM336H-5NR32-G','RF_GPS:ublox_MAX',152.4,88.9,0,'C49233943')
S.w((149.86,106.68),(154.94,106.68)); S.pwr('GND',152.4,106.68)
# Main LDO: VSYS -> VCC3V3_GPS, CE from GPS_PWR_EN (100k pull-down: GPS off at boot)
S.part('U21','Regulator_Linear:ME6211C33M5','ME6211C33M5G-N','Package_TO_SOT_SMD:SOT-23-5',76.2,76.2,0,'C82942')
S.pwr('GND',76.2,83.82)
S.pwr('VSYS',55.88,73.66); S.w((55.88,73.66),(68.58,73.66))
S.part('C200','Device:C_Small','1uF 25V',C,63.5,76.2,0,'C52923'); S.pwr('GND',63.5,78.74)
S.w((68.58,76.2),(66.04,76.2),(66.04,88.9),(50.8,88.9)); S.hier.append(('GPS_PWR_EN',50.8,88.9,180,'input'))
S.part('R200','Device:R_Small','100k',R,60.96,91.44,0,'C25741'); S.pwr('GND',60.96,93.98)
S.w((83.82,73.66),(86.36,73.66),(86.36,66.04),(134.62,66.04),(134.62,78.74),(139.7,78.74))   # VCC3V3_GPS rail
S.part('C201','Device:C_Small','1uF 25V',C,91.44,68.58,0,'C52923'); S.pwr('GND',91.44,71.12)
S.part('TP23','Connector:TestPoint','VCC3V3_GPS',TP,99.06,66.04,0,None)
S.pwr('VCC3V3_GPS',106.68,66.04)
S.part('C202','Device:C_Small','10uF 10V',C6,127.0,68.58,0,'C19702'); S.pwr('GND',127.0,71.12)
# Backup LDO: VBAT (cell side, always on) -> GPS VBAT (1.5-3.6 V) for hot start
S.part('U22','Regulator_Linear:XC6206PxxxMR','XC6206P332MR','Package_TO_SOT_SMD:SOT-23',76.2,106.68,0,'C5446')
S.pwr('GND',76.2,114.3)
S.pwr('VBAT',55.88,106.68); S.w((55.88,106.68),(68.58,106.68))
S.part('C203','Device:C_Small','1uF 25V',C,63.5,109.22,0,'C52923'); S.pwr('GND',63.5,111.76)
S.w((83.82,106.68),(96.52,106.68),(96.52,81.28),(139.7,81.28))
S.part('C204','Device:C_Small','1uF 25V',C,88.9,109.22,0,'C52923'); S.pwr('GND',88.9,111.76)
# Active antenna: VCC_RF -> 47 nH -> RF_IN, U.FL to the external antenna
S.part('L20','Device:L_Small','47nH','Inductor_SMD:L_0402_1005Metric',134.62,96.52,0,'C395068')
S.w((139.7,93.98),(134.62,93.98))
S.w((139.7,96.52),(137.16,96.52),(137.16,101.6),(132.08,101.6))
S.w((134.62,99.06),(134.62,101.6))
S.part('J20','Connector:Conn_Coaxial','U.FL GPS','Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical',127.0,101.6,0,'C88374',mirror=True)
S.pwr('GND',127.0,106.68)
# UART + PPS to the RV1106
S.w((165.1,78.74),(175.26,78.74)); S.hier.append(('GPS_TXD',175.26,78.74,0,'output'))
S.w((165.1,81.28),(175.26,81.28)); S.hier.append(('GPS_RXD',175.26,81.28,0,'input'))
S.w((165.1,83.82),(175.26,83.82)); S.hier.append(('GPS_PPS',175.26,83.82,0,'output'))
plain,mir=S.payload(400)
nc=[['U20','5'],['U20','9'],['U20','16'],['U20','17'],['U21','4']]
json.dump(dict(plain=plain,mir=mir,hier=S.hier,nc=nc,lcsc={r:{'properties':{'LCSC':c}} for r,c in S.lcsc.items()},wires=S.wires,pins=wires.pinpoints(S.parts,S.pw)+[(x,y) for _,x,y,*r in S.hier]),open(sys.argv[1]+'/gps_w.json','w'))
print(len(plain),'plain',len(mir),'mir',len(S.wires),'polylines')
