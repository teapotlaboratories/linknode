"""Drop a via next to a pad and connect it with a short F.Cu stub (T26e clean-up).
Usage: python3 viadrop.py <board.kicad_pcb> REF:PAD [REF:PAD ...] | --islands NET
--islands NET: refill the zones, then put one via inside every F.Cu fill piece of NET that has no via or PTH pad of NET.
For each pad, search a spiral of candidate via positions (0.45-3 mm from the pad centre). A candidate is accepted when the
via (0.4/0.2 mm) clears every copper item of another net on every copper layer, and the straight stub (0.2 mm, F.Cu) from
the pad centre clears every other-net item on F.Cu, both by CLR, and the via keeps EDGE from the board outline.
The via takes the pad's net. Prints what it placed; KiCad DRC must be run afterwards (this is a pre-check, not a DRC)."""
import sys, math, pcbnew
CLR, EDGE, VD, VH, TW = 0.15, 0.4, 0.4, 0.2, 0.2
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
eb = b.GetBoardEdgesBoundingBox()
X0, Y0, X1, Y1 = eb.GetLeft()/1e6 + EDGE, eb.GetTop()/1e6 + EDGE, eb.GetRight()/1e6 - EDGE, eb.GetBottom()/1e6 - EDGE
items = []                                         # (net, layer, shape)
for fp in b.GetFootprints():
    for p in fp.Pads():
        for L in CU:
            if p.IsOnLayer(L): items.append((p.GetNetname(), L, p.GetEffectiveShape(L)))
for t in b.GetTracks():
    for L in CU:
        if t.IsOnLayer(L): items.append((t.GetNetname(), L, t.GetEffectiveShape(L)))
def clear(shape_by_layer, net):
    for n, L, s in items:
        if n == net or L not in shape_by_layer: continue
        if s.Collide(shape_by_layer[L], mm(CLR)): return False
    return True
def try_via(x, y, net):
    if not (X0 <= x <= X1 and Y0 <= y <= Y1): return None
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(VD)); v.SetDrill(mm(VH))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    return v if clear({L: v.GetEffectiveShape(L) for L in CU}, net) else None
def edge_d2(chains, pt):
    best = None
    for ch in chains:
        for i in range(ch.SegmentCount()):
            d = ch.CSegment(i).SquaredDistance(pt)
            best = d if best is None or d < best else best
    return best
if sys.argv[2] == '--islands':
    net = sys.argv[3]; ni = b.FindNet(net)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    anchors = [t.GetPosition() for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == net]
    anchors += [p.GetPosition() for fp in b.GetFootprints() for p in fp.Pads() if p.GetNetname() == net and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    added = 0
    for z in b.Zones():
        if z.GetNetname() != net or z.GetLayer() != pcbnew.F_Cu: continue
        polys = z.GetFilledPolysList(pcbnew.F_Cu)
        for k in range(polys.OutlineCount()):
            one = pcbnew.SHAPE_POLY_SET(); one.AddOutline(polys.Outline(k))
            for h in range(polys.HoleCount(k)): one.AddHole(polys.Hole(k, h))
            if any(one.Contains(a) for a in anchors): continue
            chains = [polys.Outline(k)] + [polys.Hole(k, h) for h in range(polys.HoleCount(k))]
            bb = one.BBox(); placed = None
            for gy in range(int(bb.GetTop()), int(bb.GetBottom()), mm(0.1)):
                for gx in range(int(bb.GetLeft()), int(bb.GetRight()), mm(0.1)):
                    pt = pcbnew.VECTOR2I(gx, gy)
                    if not one.Contains(pt) or edge_d2(chains, pt) < mm(VD/2 + 0.05)**2: continue
                    v = try_via(gx/1e6, gy/1e6, net)
                    if v: placed = v; break
                if placed: break
            if placed:
                placed.SetNet(ni); b.Add(placed); anchors.append(placed.GetPosition()); added += 1
                for L in CU: items.append((net, L, placed.GetEffectiveShape(L)))
                print('island %d: via (%.2f, %.2f)' % (k, placed.GetPosition().x/1e6, placed.GetPosition().y/1e6))
            else:
                print('island %d: no legal via spot (area %.2f mm2)' % (k, one.Area()/1e12))
    print('added', added); b.Save(sys.argv[1]); sys.exit(0)
for arg in sys.argv[2:]:
    ref, num = arg.split(':')
    pad = [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
    net = pad.GetNetname(); c = pad.GetPosition(); cx, cy = c.x/1e6, c.y/1e6
    done = False
    for R in [0.45 + 0.05*i for i in range(52)]:
        for k in range(int(2*math.pi*R/0.1)):
            a = 2*math.pi*k/max(1, int(2*math.pi*R/0.1)); x, y = cx + R*math.cos(a), cy + R*math.sin(a)
            if not (X0 <= x <= X1 and Y0 <= y <= Y1): continue
            v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(VD)); v.SetDrill(mm(VH))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            if not clear({L: v.GetEffectiveShape(L) for L in CU}, net): continue
            t = pcbnew.PCB_TRACK(b); t.SetStart(c); t.SetEnd(pcbnew.VECTOR2I(mm(x), mm(y))); t.SetWidth(mm(TW)); t.SetLayer(pcbnew.F_Cu)
            if not clear({pcbnew.F_Cu: t.GetEffectiveShape(pcbnew.F_Cu)}, net): continue
            ni = b.FindNet(net); v.SetNet(ni); t.SetNet(ni); b.Add(v); b.Add(t)
            items.append((net, None, None))
            for L in CU: items.append((net, L, v.GetEffectiveShape(L)))
            items.append((net, pcbnew.F_Cu, t.GetEffectiveShape(pcbnew.F_Cu)))
            print('%-8s %-14s via (%.2f, %.2f), stub %.2f mm' % (arg, net[-14:], x, y, R)); done = True; break
        if done: break
    if not done: print('%-8s no spot within 3 mm' % arg)
items[:] = [i for i in items if i[1] is not None]
b.Save(sys.argv[1])
