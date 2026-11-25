"""T58 (owner 2026-11-24: "we should follow Rockchip's guide"): make room for GND stitching vias beside the microSD escape
vias (HDG V1.1 §3.2 (16) p.42) and move the 32.768 kHz crystal away from the SD lanes (§3.2 (11) p.41).
Usage: python3 t58_escape.py <in.kicad_pcb> <out.kicad_pcb>
Phase 1 (parts + removals):
- Y502 and its two keep-out rule areas 1.8 mm west; C503 (XIN load cap) with it (XIN pad x 128.475);
  TP17 (VCC_1V8 test point) to (127.3, 126.2); TP501 (RECOVERY, bottom) to (126.75, 130.2), out of the moved bottom keep-out;
  C507 (SARADC_IN0 1 nF, bottom) 0.4 mm south (127.6, 132.25) so SARADC_IN0 passes between it and the keep-out.
- R601 (SARADC 1R, 0402) to the bottom at (134.5, 127.3): no room for it on top between C504 and R603.
- C608 (VDD_0V9 10 uF, bottom) to (131.9, 127.3) horizontal, GND pad east.
- Remove: the OSC_RTC_XIN / XOUT tracks; the bottom SARADC_IN0 tracks west of x 132 (the via at 131.84,132.35 stays); the
  D1/D0/CLK/CMD escape (fingers, vias, lane tops down to the bus columns); C608's old GND link and its via (133.945,127.96).
Phase 2 (t53_lay): RTC traces for the new crystal place; SARADC_IN0 round the west of the keep-out (45-degree bends); the four
escapes in pairs (D1+D0 0.5 mm, CLK+CMD 0.51 mm on their bus columns; D3+D2 unchanged) with ~0.9-1.2 mm gaps; every lane either
goes straight into its bus column or jogs >= 0.36 mm (no zig-zag, t47_jagged); GND vias in the gaps (133.47,129.8), (135.1,130.45)
and at the west end (131.95,128.65, also C608's GND link)."""
import sys, os, subprocess, math, pcbnew
IN, OUT = sys.argv[1:3]; PH2 = '--phase2' in sys.argv
LAY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 't53_lay.py')
mm, MM = pcbnew.ToMM, pcbnew.FromMM
SDCLK = 'Net-(U100SD and SPI1-SDMMC_CLK{slash}GPIO3_A4)'
SHIFT = 1.8
if not PH2:
    b = pcbnew.LoadBoard(IN); fp = {f.GetReference(): f for f in b.GetFootprints()}
    def mv(ref, x, y, rot=None):
        f = fp[ref]; f.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        if rot is not None: f.SetOrientationDegrees(rot)
    y5 = fp['Y502'].GetPosition(); mv('Y502', mm(y5.x) - SHIFT, mm(y5.y))
    for z in b.Zones():
        if z.GetIsRuleArea() and 'Y502' in z.GetZoneName(): z.Move(pcbnew.VECTOR2I(MM(-SHIFT), 0))
    mv('C503', 128.95, 128.455); mv('TP17', 127.3, 126.2); mv('TP501', 126.75, 130.2); mv('C507', 127.6, 132.25)
    r = fp['R601']
    if not r.IsFlipped(): r.Flip(r.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    mv('R601', 134.5, 127.3, 0.0)
    mv('C608', 131.9, 127.3, 0.0)
    gnd = [p for p in fp['C608'].Pads() if p.GetNetname() == 'GND'][0]
    if mm(gnd.GetPosition().x) < 131.9: mv('C608', 131.9, 127.3, 180.0)
    R = lambda v: round(mm(v), 3)
    gone = 0
    ESC = {'/SoC/SD_D1', '/SoC/SD_D0', SDCLK, '/SoC/SD_CMD'}
    LANE_TOP = {'/SoC/SD_D1': 132.368, '/SoC/SD_D0': 132.402, SDCLK: 132.437, '/SoC/SD_CMD': 132.471}
    for t in list(b.GetTracks()):
        n = t.GetNetname(); s, e = t.GetStart(), t.GetEnd(); ly = t.GetLayer()
        xs = [R(s.x), R(e.x)]; ys = [R(s.y), R(e.y)]
        kill = False
        if n in ('Net-(U100System-OSC_RTC_XIN)', 'Net-(U100System-OSC_RTC_XOUT)'): kill = True
        elif 'SARADC_IN0' in n and t.Type() != pcbnew.PCB_VIA_T and ly == pcbnew.B_Cu and max(xs) < 132: kill = True
        elif n in ESC:
            if t.Type() == pcbnew.PCB_VIA_T: kill = R(s.y) < 131
            elif ly == pcbnew.F_Cu: kill = min(xs) < 136.7
            elif ly == pcbnew.B_Cu: kill = max(ys) <= LANE_TOP[n] + 0.001
        elif n == 'GND':
            if t.Type() == pcbnew.PCB_VIA_T: kill = (R(s.x), R(s.y)) == (133.945, 127.96)
            elif ly == pcbnew.B_Cu: kill = set(zip(xs, ys)) <= {(132.4, 128.38), (132.82, 127.96), (133.945, 127.96)}
        if kill: b.Remove(t); gone += 1
    b.Save(OUT); print('phase 1: parts moved, items removed:', gone); sys.stdout.flush()
    os.execv(sys.executable, [sys.executable, __file__, OUT, OUT, '--phase2'])
def F(*p): return 'F:' + '/'.join(f'{x:.3f},{y:.3f}' for x, y in p)
def Bp(*p): return 'B:' + '/'.join(f'{x:.3f},{y:.3f}' for x, y in p)
def V(x, y): return f'V:{x:.3f},{y:.3f}'
PLAN = [
 ('Net-(U100System-OSC_RTC_XIN)', '0.12', [F((128.475, 128.455), (128.475, 130.205)),
     F((128.475, 130.205), (128.475, 131.005), (129.07, 131.6), (135.28, 131.6), (135.6, 131.28), (136.775, 131.28))]),
 ('Net-(U100System-OSC_RTC_XOUT)', '0.12', [F((131.755, 126.705), (130.975, 127.485), (130.975, 130.205)), F((130.975, 130.93), (136.775, 130.93))]),
 ('Net-(U100System-SARADC_IN0{slash}GPIO4_C0)', '0.12', [Bp((130.09, 128.5), (127.78, 128.5), (127.48, 128.8), (127.48, 130.2)),
     Bp((127.48, 130.2), (126.75, 130.2)), Bp((127.48, 130.2), (127.48, 131.5), (127.63, 131.65), (128.08, 131.65)),
     Bp((128.08, 131.65), (128.08, 132.25)), Bp((128.08, 131.65), (130.99, 131.65), (131.69, 132.35), (131.84, 132.35))]),
 ('/SoC/SD_D1', '0.17', [F((136.775, 128.13), (132.69, 128.13), (132.52, 128.30)), V(132.52, 128.30), Bp((132.52, 128.30), (132.52, 131.988), (132.9, 132.368))]),
 ('/SoC/SD_D0', '0.17', [F((136.775, 128.83), (133.19, 128.83), (133.02, 129.0)), V(133.02, 129.0), Bp((133.02, 129.0), (133.02, 131.768), (133.41, 132.158), (133.41, 132.402))]),
 (SDCLK, '0.17', [F((136.775, 129.18), (134.09, 129.18), (133.92, 129.35)), V(133.92, 129.35), Bp((133.92, 129.35), (133.92, 132.437))]),
 ('/SoC/SD_CMD', '0.17', [F((136.775, 129.53), (134.6, 129.53), (134.43, 129.70)), V(134.43, 129.70), Bp((134.43, 129.70), (134.43, 132.471))]),
 ('GND', '0.2', [V(133.47, 129.8), V(135.1, 130.45), V(131.95, 128.65), Bp((132.675, 127.3), (131.95, 128.025), (131.95, 128.65))]),
]
for net, w, steps in PLAN:
    r = subprocess.run([sys.executable, LAY, OUT, net, '--w', w] + steps, capture_output=True, text=True)
    out = [l for l in (r.stdout + r.stderr).strip().splitlines() if 'Debug' not in l and 'leak' not in l]
    print(net[-30:], '->', out[-1] if out else r.returncode)
    if r.returncode != 0: print('\n'.join(out[-8:])); sys.exit(1)
