"""Antenna sheet (T14): HaLow RF path. HALOW_ANT -> 100 pF DC block (Heltec SDIO reference C1) -> 5-pole LC low-pass
(2.7p / 8.2n / 5.6p / 8.2n / 2.7p) -> U.FL. Filter for the 3rd harmonic near 2.75 GHz (project rules); simulated with the
LQW15AN8N2 datasheet limits (Q >= 25 @ 250 MHz, SRF >= 5.5 GHz): 0.3-0.6 dB at 915 MHz, RL 31 dB, -20 dB at 2fo,
-44 dB at 3fo. The shunt pads double as matching positions. ESP32-C5: module U.FL (ANT1); GPS: U.FL on the GPS sheet."""
import sys, json; sys.path.insert(0, sys.argv[1])
from blocks import *
import wires
S = Sheet(); H = S.hier
Y = 101.6
H.append(('HALOW_ANT', 50.8, Y, 180, 'bidirectional'))
S.w((50.8, Y), (60.96, Y)); S.part('C901', 'Device:C_Small', '100pF C0G', C, 63.5, Y, 90, 'C1546')
S.w((66.04, Y), (83.82, Y))
S.part('C902', 'Device:C_Small', '2.7pF C0G', C, 76.2, Y + 2.54, 0, 'C1561'); S.pwr('GND', 76.2, Y + 5.08)
S.part('L901', 'Device:L_Small', '8.2nH', 'Inductor_SMD:L_0402_1005Metric', 86.36, Y, 90, 'C84404')
S.w((88.9, Y), (104.14, Y))
S.part('C903', 'Device:C_Small', '5.6pF C0G', C, 96.52, Y + 2.54, 0, 'C1574'); S.pwr('GND', 96.52, Y + 5.08)
S.part('L902', 'Device:L_Small', '8.2nH', 'Inductor_SMD:L_0402_1005Metric', 106.68, Y, 90, 'C84404')
S.w((109.22, Y), (121.92, Y))
S.part('C904', 'Device:C_Small', '2.7pF C0G', C, 116.84, Y + 2.54, 0, 'C1561'); S.pwr('GND', 116.84, Y + 5.08)
S.part('J901', 'Connector:Conn_Coaxial', 'U.FL HaLow', 'Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical', 127.0, Y, 0, 'C88374')
S.pwr('GND', 127.0, Y + 5.08)
plain, mir = S.payload(1500)
json.dump(dict(plain=plain, mir=mir, hier=H, lcsc={r: {'properties': {'LCSC': c}} for r, c in S.lcsc.items()}, wires=S.wires,
               pins=wires.pinpoints(S.parts, S.pw) + [(x, y) for _, x, y, *r in H]), open(sys.argv[1] + '/antenna_w.json', 'w'))
print(len(plain), 'plain', len(mir), 'single', len(S.wires), 'polylines', len(H), 'hier')
