"""T30 (owner 2026-11-22: clear all routing, route only the RV1106 for now).
Removes every track on the board, and every via, except:
  - everything inside the SoC window (the T29 fan-out: pin stubs, ring vias, bottom links, GND stubs, Y501 GND vias);
  - standalone GND vias outside it (stitching between the GND pours, no track attached).
Zones stay. What's kept is locked. Zones refilled, board saved.
Usage: python3 t30_clear.py <board.kicad_pcb>"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
U = b.FindFootprintByReference('U100'); CX, CY = U.GetPosition().x/1e6, U.GetPosition().y/1e6
W = (CX-13.5, CY-13.5, CX+13.5, CY+13.5)
inw = lambda p: W[0] < p.x/1e6 < W[2] and W[1] < p.y/1e6 < W[3]
KEEP = []; tr = vi = 0
for t in list(b.GetTracks()):
    if t.GetClass() != 'PCB_VIA' and not (inw(t.GetStart()) and inw(t.GetEnd())):
        b.Remove(t); KEEP.append(t); tr += 1
ends = set()
for t in b.GetTracks():
    if t.GetClass() != 'PCB_VIA':
        for e in (t.GetStart(), t.GetEnd()): ends.add((e.x//1000, e.y//1000))
kept_stitch = 0
for v in list(b.GetTracks()):
    if v.GetClass() != 'PCB_VIA' or inw(v.GetPosition()): continue
    p = v.GetPosition()
    if v.GetNetname() == 'GND' and (p.x//1000, p.y//1000) not in ends: kept_stitch += 1; continue
    b.Remove(v); KEEP.append(v); vi += 1
for t in b.GetTracks(): t.SetLocked(True)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
left = sum(1 for _ in b.GetTracks())
print('removed tracks', tr, 'vias', vi, '| kept GND stitching vias', kept_stitch, '| items left (fan-out + stitching)', left)
