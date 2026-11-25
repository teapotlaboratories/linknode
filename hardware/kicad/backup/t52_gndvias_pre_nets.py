"""T52 (owner, 2026-11-23): a GND via beside every USB signal via (Rockchip HDG V1.1 §3.3.3 p.48: "A GND via needs to be
placed near the USB signal via for better signal quality"). The GND via ties the top pour, In1 (GND plane) and the bottom
pour together right where the signal changes layer, so its return current has a short path.
Usage: python3 t52_gndvias.py <board.kicad_pcb> [--rmax 1.2]
For each via on a USB net (USB_DP/DN, USB_SOC_*, USB_CONN_*): the nearest legal 0.4/0.2 mm GND via within rmax (0.05 mm
grid): class clearance to every other net on all layers, hole spacing, and >= 0.09 mm from any pad edge. Skips a USB via
that already has a GND via within rmax. Saves the board; refill and DRC afterwards."""
import sys, os, math, json, pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geomlib import Geo, CU, bbox
from geomlib import dist as gdist
B = sys.argv[1]; opt = {sys.argv[i]: sys.argv[i + 1] for i in range(2, len(sys.argv) - 1) if sys.argv[i].startswith('--')}
RMAX = float(opt.get('--rmax', 1.2))
b = pcbnew.LoadBoard(B)
_eb = b.GetBoardEdgesBoundingBox(); g = Geo(b, (_eb.GetLeft()/1e6 - 1, _eb.GetTop()/1e6 - 1, _eb.GetRight()/1e6 + 1, _eb.GetBottom()/1e6 + 1))
USB = ('/SoC/USB_DP', '/SoC/USB_DN', '/SoC/USB_SOC_DP', '/SoC/USB_SOC_DN', '/USB and Charger/USB_CONN_DP', '/USB and Charger/USB_CONN_DN')
def V2(v): return (v.GetPosition().x/1e6, v.GetPosition().y/1e6)
vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
sig = [V2(v) for v in vias if v.GetNetname() in USB]
gnd = [V2(v) for v in vias if v.GetNetname() == 'GND']
def ok(x, y):
    if not (g.hole_ok(x, y, 0.2) and all(g.clear(('pt', (x, y), 0.2), L, 'GND') for L in CU)): return False
    G = ('pt', (x, y), 0.2)
    for L in (pcbnew.F_Cu, pcbnew.B_Cu):
        for r in g.near(L, bbox(G), 0.6):
            if r[4] == 'pad' and r[0] == 'GND' and gdist(G, r[1]) < 0.09: return False
    return True
added = []
for s in sig:
    if any(math.dist(s, q) <= RMAX for q in gnd + [a for a, _ in added]): continue
    best = None
    n = int(RMAX/0.05)
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = round(s[0] + i*0.05, 3), round(s[1] + j*0.05, 3); d = math.dist((x, y), s)
            if d > RMAX or (best and d >= best[0]): continue
            if ok(x, y): best = (d, (x, y))
    if best:
        g.add_via(best[1][0], best[1][1], 'GND', d=0.4, h=0.2, tag='gndvia'); added.append((best[1], round(best[0], 2)))
    else: print('no GND via spot near', s)
b.Save(B)
print(json.dumps(dict(usb_vias=len(sig), gnd_vias_added=added)))
