"""Restore missing layer-change vias: find every point where track ends of one net on two or more different copper layers
meet (within 1 um) with no via or through-hole pad there, and add a 0.4/0.2 through via. Seen after Freerouting SES
import plus mazeroute on the T28 board (2026-11-21): tracks on F.Cu, In2.Cu and B.Cu ending at one point, unjoined.
Usage: python3 gapvia.py <board.kicad_pcb> [--remove "x,y;x,y"]
Clearance is left to kicad-cli DRC: run it afterwards and remove any added via it flags with --remove."""
import sys, math, collections, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.FromMM; KEEP = []
if len(sys.argv) > 2 and sys.argv[2] == '--remove':
    pts = [tuple(map(float, p.split(','))) for p in sys.argv[3].split(';') if p]; n = 0
    for t in list(b.GetTracks()):
        if t.GetClass() == 'PCB_VIA' and any(math.hypot(t.GetPosition().x/1e6-px, t.GetPosition().y/1e6-py) < 0.002 for px, py in pts):
            b.Remove(t); KEEP.append(t); n += 1
    b.Save(sys.argv[1]); print('removed', n); sys.exit(0)
ends = collections.defaultdict(set); joined = set()
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        joined.add((t.GetNetname(), t.GetPosition().x//1000, t.GetPosition().y//1000)); continue
    for e in (t.GetStart(), t.GetEnd()): ends[(t.GetNetname(), e.x//1000, e.y//1000)].add(t.GetLayer())
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetDrillSizeX() > 0: joined.add((p.GetNetname(), p.GetPosition().x//1000, p.GetPosition().y//1000))
added = []
for (net, x, y), layers in ends.items():
    if len(layers) < 2 or (net, x, y) in joined: continue
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(int(x*1000), int(y*1000))); v.SetWidth(mm(0.4)); v.SetDrill(mm(0.2))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet(net)); b.Add(v)
    added.append((x/1000, y/1000, net, sorted(b.GetLayerName(L) for L in layers)))
b.Save(sys.argv[1]); print('added', len(added))
for a in added: print('  via %.3f,%.3f %s %s' % a)
