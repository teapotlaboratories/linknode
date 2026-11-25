"""T45 silkscreen tidy. Usage: python3 t45_silk.py <board.kicad_pcb> [c6_dx_mm]
1. Edge connectors (J1-J4) overhang the board by design; their footprint silk lines run onto or past Edge.Cuts
   (DRC silk_edge_clearance). Each straight silk segment is clipped to the board outline shrunk by MARGIN; a segment
   wholly outside is deleted. Rect/arc/poly silk is left alone (none of it crosses the edge).
2. U2's pin-1 marker sits on C6 pad 1 (silk_over_copper): C6 moves left by c6_dx (default 0.3 mm), staying beside
   the VBUS pins (the Block 2 audit checks it stays <= 2.0 mm).
No other part moves; designators stay hidden."""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); dx = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3
mm = pcbnew.FromMM; MARGIN = 0.15
eb = b.GetBoardEdgesBoundingBox(); w = 0.05
X0, Y0, X1, Y1 = eb.GetLeft()/1e6 + w + MARGIN, eb.GetTop()/1e6 + w + MARGIN, eb.GetRight()/1e6 - w - MARGIN, eb.GetBottom()/1e6 - w - MARGIN
def clip(p, q):
    """Liang-Barsky clip of segment p-q to [X0,X1]x[Y0,Y1]; None if outside."""
    (x0, y0), (x1, y1) = p, q; dxs, dys = x1 - x0, y1 - y0; t0, t1 = 0.0, 1.0
    for pp, qq in ((-dxs, x0 - X0), (dxs, X1 - x0), (-dys, y0 - Y0), (dys, Y1 - y0)):
        if abs(pp) < 1e-12:
            if qq < 0: return None
            continue
        t = qq/pp
        if pp < 0: t0 = max(t0, t)
        else: t1 = min(t1, t)
        if t0 > t1: return None
    return (x0 + t0*dxs, y0 + t0*dys), (x0 + t1*dxs, y0 + t1*dys)
rep = {'trimmed': 0, 'deleted': 0}
FPS = {f.GetReference(): f for f in b.GetFootprints()}
for ref in ('J1', 'J2', 'J3', 'J4'):
    f = FPS[ref]; items = [g for g in f.GraphicalItems()]
    for g in items:
        if g.GetClass() != 'PCB_SHAPE' or g.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS) or g.GetShape() != pcbnew.SHAPE_T_SEGMENT: continue
        p = (g.GetStart().x/1e6, g.GetStart().y/1e6); q = (g.GetEnd().x/1e6, g.GetEnd().y/1e6)
        c = clip(p, q)
        if c is None or (abs(c[0][0] - c[1][0]) < 0.05 and abs(c[0][1] - c[1][1]) < 0.05):
            f.Delete(g); rep['deleted'] += 1; continue
        if max(abs(c[0][0] - p[0]), abs(c[0][1] - p[1]), abs(c[1][0] - q[0]), abs(c[1][1] - q[1])) > 1e-6:
            g.SetStart(pcbnew.VECTOR2I(mm(c[0][0]), mm(c[0][1]))); g.SetEnd(pcbnew.VECTOR2I(mm(c[1][0]), mm(c[1][1]))); rep['trimmed'] += 1
c6 = FPS['C6']; p = c6.GetPosition(); c6.SetPosition(pcbnew.VECTOR2I(p.x - mm(dx), p.y)); rep['C6_dx'] = -dx
b.Save(sys.argv[1]); print(rep)
