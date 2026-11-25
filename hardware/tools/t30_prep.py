"""T30 prep: rip up every U100 signal net board-wide, then lock all remaining tracks and vias so the autorouter keeps them.
Signal nets = nets on U100 and on the SoC-sheet satellites (R5xx, C5xx, Y5xx, TP5xx, J5xx, R6xx, C6xx, FB6xx),
minus GND and the rails (VCC_3V3, VCC_1V8, VDD_0V9, VDD_ARM, VCC_DDR, VCC5V0_SYS, VBUS, VSYS): those keep their routing
outside the SoC window (already cleared inside by T29, apart from the fan-out). Refills zones and saves.
Usage: python3 t30_prep.py <board.kicad_pcb>"""
import sys, re, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
RAILS = {'GND', 'VCC_3V3', 'VCC_1V8', 'VDD_0V9', 'VDD_ARM', 'VCC_DDR', 'VCC5V0_SYS', 'VBUS', 'VSYS', ''}
sat = re.compile(r'^(U100|R5\d\d|C5\d\d|Y5\d\d|TP5\d\d|J5\d\d|R6\d\d|C6\d\d|FB6\d\d)$')
nets = set()
for fp in b.GetFootprints():
    if sat.match(fp.GetReference()):
        for p in fp.Pads():
            n = p.GetNetname()
            if n not in RAILS and not n.startswith('unconnected'): nets.add(n)
KEEP = []; rip = 0
for t in list(b.GetTracks()):
    if t.GetNetname() in nets: b.Remove(t); KEEP.append(t); rip += 1
locked = 0
for t in b.GetTracks(): t.SetLocked(True); locked += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
print('signal nets', len(nets), 'ripped', rip, 'locked', locked)
print(sorted(nets))
