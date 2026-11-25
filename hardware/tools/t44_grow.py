"""T44 (owner, 2026-11-23): grow the board on the top and right for edge margin: 76 x 60 -> 78 x 62 mm.
Usage: python3 t44_grow.py <board.kicad_pcb>. No part moves except the three corner holes that sit on a moved edge.
- Edge.Cuts: rounded rectangle r = 2 mm, x 100..178, y 98..160 (the right edge +2.0, the top edge -2.0; left/bottom unchanged).
- MH1 (top-left) and MH2 (top-right) move up 2.0; MH2 and MH4 (bottom-right) move right 2.0 (still 3.975 mm from both edges).
- The board-wide pours (GND on F/In1/B, VCC5V0_SYS on In2) take the new outline; local zones and keepouts are untouched.
Refill and DRC are separate steps."""
import sys, math, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.FromMM
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))
OLD = (100.0, 100.0, 176.0, 160.0); X0, Y0, X1, Y1 = 100.0, 98.0, 178.0, 160.0; R = 2.0
keep = []
for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts: keep.append(d); b.Remove(d)
def seg(a, c):
    s = pcbnew.PCB_SHAPE(b); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*a)); s.SetEnd(V(*c)); b.Add(s)
def arc(a, m, c):
    s = pcbnew.PCB_SHAPE(b); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetArcGeometry(V(*a), V(*m), V(*c)); b.Add(s)
k = R*(1 - math.sqrt(0.5))
seg((X0 + R, Y0), (X1 - R, Y0)); seg((X1, Y0 + R), (X1, Y1 - R)); seg((X1 - R, Y1), (X0 + R, Y1)); seg((X0, Y1 - R), (X0, Y0 + R))
arc((X0, Y0 + R), (X0 + k, Y0 + k), (X0 + R, Y0)); arc((X1 - R, Y0), (X1 - k, Y0 + k), (X1, Y0 + R))
arc((X1, Y1 - R), (X1 - k, Y1 - k), (X1 - R, Y1)); arc((X0 + R, Y1), (X0 + k, Y1 - k), (X0, Y1 - R))
for ref, dx, dy in (('MH1', 0, -2.0), ('MH2', 2.0, -2.0), ('MH4', 2.0, 0)):
    f = b.FindFootprintByReference(ref); p = f.GetPosition(); f.SetPosition(pcbnew.VECTOR2I(p.x + mm(dx), p.y + mm(dy)))
n = 0
for z in b.Zones():
    if z.GetIsRuleArea(): continue
    bb = z.GetBoundingBox()
    if (round(bb.GetLeft()/1e6, 2), round(bb.GetTop()/1e6, 2), round(bb.GetRight()/1e6, 2), round(bb.GetBottom()/1e6, 2)) != OLD: continue
    o = z.Outline(); o.RemoveAllContours(); o.NewOutline()
    for px, py in ((X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)): o.Append(mm(px), mm(py))
    n += 1
b.Save(sys.argv[1])
print('outline 78 x 62 (x 100..178, y 98..160); holes moved MH1 MH2 MH4; board-wide pours reshaped:', n)
