"""Greedy near-pin placer for T26 (positions only; moves are applied through the KiCad scripting server).
Usage: python3 placer.py <board.kicad_pcb> <plan.json> <out.json>
plan: list of entries (or {"margin", "keepouts": [[x1,y1,x2,y2]], "parts": [...]};
keepouts are escape lanes no part may cover unless its entry has "lanes_ok": true)
entries {"ref": R, "to": [IC, pad] | [x, y], "rot": [angles] (optional), "fixed": [x, y, rot] (optional)}.
Each part is placed at the free grid spot nearest the target, in the rotation that brings its pad on the
target's net (or its nearest pad) closest to the target. Obstacles: courtyards of every footprint already inside
or overlapping the board outline (plus `margin`), placed parts, and a 0.5 mm edge band."""
import sys, json, math, pcbnew
BOARD, PLAN, OUT = sys.argv[1:4]
b = pcbnew.LoadBoard(BOARD)
eb = b.GetBoardEdgesBoundingBox()
X0, Y0, X1, Y1 = eb.GetLeft() / 1e6 + 0.5, eb.GetTop() / 1e6 + 0.5, eb.GetRight() / 1e6 - 0.5, eb.GetBottom() / 1e6 - 0.5
MARGIN, GRID = 0.15, 0.25
def crt(fp):
    cy = fp.GetCourtyard(pcbnew.F_Cu)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False, False)
    return [bb.GetLeft() / 1e6, bb.GetTop() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6]
def inside(r): return r[0] >= X0 and r[1] >= Y0 and r[2] <= X1 and r[3] <= Y1
def onboard(r): return r[0] < X1 and r[2] > X0 and r[1] < Y1 and r[3] > Y0
plan = json.load(open(PLAN))
KEEPOUT = []
if isinstance(plan, dict):                     # {"margin": m, "keepouts": [[x1,y1,x2,y2],...], "parts": [...]}
    MARGIN = plan.get('margin', MARGIN); KEEPOUT = plan.get('keepouts', []); plan = plan['parts']
moving = {e['ref'] for e in plan}
obst = [crt(fp) for fp in b.GetFootprints() if fp.GetReference() not in moving and onboard(crt(fp))]
def hits(r, o, m): return not (r[2] + m <= o[0] or o[2] + m <= r[0] or r[3] + m <= o[1] or o[3] + m <= r[1])
def free(r, lanes=True, m=None):
    m = MARGIN if m is None else m
    return inside(r) and not (lanes and any(hits(r, k, 0) for k in KEEPOUT)) and not any(hits(r, o, m) for o in obst)
out = {}
for e in plan:
    fp = b.FindFootprintByReference(e['ref'])
    if 'fixed' in e:
        x, y, rot = e['fixed']; fp.SetOrientationDegrees(rot); fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        obst.append(crt(fp)); out[e['ref']] = [x, y, rot]; continue
    if isinstance(e['to'][0], str):
        ic = b.FindFootprintByReference(e['to'][0]); tp = [p for p in ic.Pads() if p.GetNumber() == str(e['to'][1])][0]
        tx, ty, net = tp.GetPosition().x / 1e6, tp.GetPosition().y / 1e6, tp.GetNetname()
    else:
        tx, ty = e['to']; net = e.get('net')
    best = None
    for rot in e.get('rot', [0, 90, 180, 270]):
        fp.SetOrientationDegrees(rot); fp.SetPosition(pcbnew.VECTOR2I(0, 0))
        rel = crt(fp)
        pads = [p for p in fp.Pads() if p.GetNumber()]
        mp = [p for p in pads if net and p.GetNetname() == net] or pads
        # offset of the anchoring pad from the footprint origin
        for R in [i * GRID for i in range(0, 120)]:
            found = None
            n = max(1, int(2 * math.pi * R / GRID))
            for k in range(n):
                a = 2 * math.pi * k / n
                for p in mp:
                    px, py = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
                    cx = round((tx + R * math.cos(a) - px) / GRID) * GRID; cy = round((ty + R * math.sin(a) - py) / GRID) * GRID
                    r = [rel[0] + cx, rel[1] + cy, rel[2] + cx, rel[3] + cy]
                    if free(r, not e.get('lanes_ok'), e.get('margin')):
                        d = math.hypot(cx + px - tx, cy + py - ty)
                        if found is None or d < found[0]: found = (d, cx, cy, rot, r)
            if found: break
        if found and (best is None or found[0] < best[0] - 1e-6): best = found
    if not best: print('NO SPOT', e['ref']); continue
    d, cx, cy, rot, r = best
    fp.SetOrientationDegrees(rot); fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy)))
    obst.append(r); out[e['ref']] = [round(cx, 3), round(cy, 3), rot]
    print('%-6s (%.2f, %.2f) rot %3d  pad-to-target %.2f mm' % (e['ref'], cx, cy, rot, d))
json.dump({k: {'x': v[0], 'y': v[1], 'rotation': v[2]} for k, v in out.items()}, open(OUT, 'w'))
