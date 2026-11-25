"""T31 driver: route every RV1106 net with netroute (no Freerouting). Usage: python3 t31_route.py <board.kicad_pcb>
1. escape stubs at U100 for its signal pins (lanes reserved);
2. signal nets end to end (0.12 mm), 0.5 mm from the USB pair on the same layer;
3. local rails (0.2 mm, SoCPower) only between U100's own parts (both ends within 15 mm of U100);
Saves the board; refill and DRC afterwards."""
import sys, os, re, math, json, pcbnew
sys.path.insert(0, os.path.dirname(__file__))
import netroute as nr
from geomlib import Geo
B = sys.argv[1]; b = pcbnew.LoadBoard(B)
U = b.FindFootprintByReference('U100'); CX, CY = U.GetPosition().x/1e6, U.GetPosition().y/1e6
RAILS = {'VCC_3V3', 'VCC_1V8', 'VDD_0V9', 'VDD_ARM', 'VCC_DDR'}
NOT = RAILS | {'GND', 'VCC5V0_SYS', 'VBUS', 'VSYS', ''}
sat = re.compile(r'^(U100|R5\d\d|C5\d\d|Y5\d\d|TP5\d\d|J5\d\d|R6\d\d|C6\d\d|FB6\d\d)$')
USB = {'/SoC/USB_DP', '/SoC/USB_DM', 'Net-(U100System-USB_DP)', 'Net-(U100System-USB_DM)'}
SIG = set()
for fp in b.GetFootprints():
    if sat.match(fp.GetReference()):
        for p in fp.Pads():
            n = p.GetNetname()
            if n not in NOT and not n.startswith('unconnected') and n not in USB: SIG.add(n)
g = Geo(b, (100, 100, 190, 180))
print('escape stubs', nr.add_escapes(b, g, SIG), flush=True)
f1 = nr.route_nets(b, B, g, SIG, keep_from=('/SoC/USB_DP', '/SoC/USB_DM'), keep=0.35, diag=True)
print('signals failed', sorted(set(f1)), flush=True)
near = lambda p: abs(p[0] - CX) < 15 and abs(p[1] - CY) < 15
f2 = nr.route_nets(b, B, g, RAILS, keep_from=('/SoC/USB_DP', '/SoC/USB_DM'), keep=0.35, width=0.2, diag=True,
                   pair_filter=lambda j: near(j[1][0]) and near(j[2][0]))
print('rails failed', sorted(set(f2)), flush=True)
b.Save(B)
print(json.dumps({'signals_failed': sorted(set(f1)), 'rails_failed': sorted(set(f2))}))
