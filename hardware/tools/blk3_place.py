"""T41 Block 3: move the radio parts that blk3_audit.py found away from their pins.
Usage: python3 blk3_place.py <board.kicad_pcb>   (edits in place; back the board up first)

Each part in MOVES is lifted, then put at the pose (0.1 mm grid, 4 rotations, given side, within RADIUS of its first
target) with the least weighted pad-centre distance to its targets [(ref, pin, weight)], 0.1 mm courtyard gap, nothing
else moves. Order matters: the GPS U.FL first, then L20 between it and the module, then the GPS LDO next to the module's
VCC pin with its caps, then the HaLow and ESP32-C5 decoupling (100 nF before the bulk cap). Sources: see blk3_audit.py."""
import sys, os, json, traceback
import numpy as np, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from placelib import Raster, best_pose, crt, side_of, set_side, pos, ppos, V
BOARD = sys.argv[1]; b = pcbnew.LoadBoard(BOARD)
FP = {f.GetReference(): f for f in b.GetFootprints()}
eb = b.GetBoardEdgesBoundingBox(); X0, Y0, X1, Y1 = eb.GetLeft()/1e6, eb.GetTop()/1e6, eb.GetRight()/1e6, eb.GetBottom()/1e6
MOVES = [  # (ref, side, radius mm, [(target ref, target pin, weight)])
    ('J20', 'F', 4, [('U20', '11', 1.0)]),                       # ATGM336H §2.8: antenna connector close to RF_IN
    ('L20', 'F', 4, [('U20', '14', 1.0), ('U20', '11', 1.0)]),   # VCC_RF bias feed onto the RF line
    ('U21', 'F', 8, [('U20', '8', 1.0)]),                        # LDO next to the GPS VCC pin (low ripple at the load)
    ('U22', 'F', 10, [('U20', '6', 0.3), ('U21', '1', 0.0)]),     # backup LDO (uA load): anywhere close, after U21
    ('C201', 'B', 4, [('U21', '5', 1.0), ('U21', '2', 0.4)]),    # LDO output cap (bottom, under the pin)
    ('C200', 'B', 4, [('U21', '1', 1.0), ('U21', '2', 0.4)]),    # LDO input cap (bottom, under the pin)
    ('R200', 'B', 4, [('U21', '3', 1.0)]),                       # EN pull-down
    ('C203', 'B', 4, [('U22', '3', 1.0), ('U22', '1', 0.4)]),    # backup LDO input cap (bottom)
    ('C202', 'B', 4, [('U20', '8', 1.0)]),                       # 10 uF under the GPS VCC pin (bottom, via)
    ('C204', 'B', 4, [('U20', '6', 1.0)]),                       # backup LDO output under the GPS VBAT pin
    ('TP23', 'F', 8, [('U21', '5', 1.0)]),                       # VCC3V3_GPS test point
    ('C701', 'B', 5, [('U701', '25', 1.0)]),                     # HaLow 100 nF VBAT
    ('C704', 'B', 5, [('U701', '19', 1.0)]),                     # HaLow 10 uF VDD_IO
    ('C705', 'B', 5, [('U701', '32', 1.0)]),                     # HaLow 100 nF VDD_FEM
    ('C706', 'B', 5, [('U701', '32', 1.0)]),                     # HaLow 10 uF VDD_FEM
    ('C803', 'B', 5, [('U801', '2', 1.0)]),                      # ESP32-C5 0.1 uF 3V3
    ('C802', 'B', 5, [('U801', '2', 1.0)]),                      # ESP32-C5 22 uF 3V3
]
MOV = {m[0] for m in MOVES}
report = {'moved': {}, 'failed': []}
R = Raster(X0, Y0, X1, Y1)
for ref in MOV: FP[ref].SetPosition(V(X1 + 30, Y0))
for f in b.GetFootprints():
    if f.GetReference() not in MOV: R.mark_fp(f)
for z in b.Zones():
    if z.GetIsRuleArea() and z.IsOnLayer(pcbnew.B_Cu):
        q = z.GetBoundingBox(); R.mark('B', (q.GetLeft()/1e6, q.GetTop()/1e6, q.GetRight()/1e6, q.GetBottom()/1e6))
def tpad(ref, num): return [p for p in FP[ref].Pads() if p.GetNumber() == num][0]
for ref, side, rad, targets in MOVES:
    f = FP[ref]; set_side(f, side)
    T = [(tpad(t, n).GetNetname(), np.array(ppos(tpad(t, n))), w) for t, n, w in targets]
    def cost(rot, pads, ox, oy, T=T):
        c = np.zeros(ox.shape)
        for net, tp, w in T:
            mine = [(dx, dy) for n, _, dx, dy in pads if n == net]
            if not mine: continue
            c = c + w*np.min([np.hypot(ox + dx - tp[0], oy + dy - tp[1]) for dx, dy in mine], axis=0)
        return c
    cx, cy = T[0][1]
    r = best_pose(f, R, cx, cy, rad, 0.1, cost, 0.1)
    if r is None: report['failed'].append(ref); continue
    report['moved'][ref] = [round(pos(f)[0], 2), round(pos(f)[1], 2), f.GetOrientationDegrees(), side_of(f), round(r[0], 2)]
b.Save(BOARD)
print(json.dumps(report))
