"""T55 FPC B, audio only (owner, 2026-11-24: "Audio only on FPC B"): parts and routing on a copy.
Usage: python3 t55_fpcb.py <in.kicad_pcb> <out.kicad_pcb>

Plan (lines 0.12 mm, 45-degree bends only):
- Top: LINEOUT (pin 29) and MICBIAS (pin 32) leave west, the four MIC lines (pins 33-36) leave south; all six turn south-west
  in one diagonal bundle (MIC starts staggered 0.02 mm so parallel diagonals keep 0.13 mm) and run south in the free top strip
  west of the microSD socket (x 134.3 / 134.9 / 135.5 / 136.2 / 136.9 / 137.6) to a row of vias at y 145.0.
- The 1 uF MIC series capacitors C1001-C1004 move to the top, in line on their lanes (two staggered rows).
- Bottom: nested L's east into FPC B (eastmost lane highest): MIC1P 146.16, MIC1N 146.41, MIC0P 146.66, MIC0N 146.91,
  MICBIAS 147.16, LINEOUT 147.41. Each line runs north->south through its ESD array (flow-through)
  into its contact.
- Arrays on the contact pitch: U1007 centred on contact 3 (pads 1 LINEOUT / 3 GND / 4 MICBIAS), U1006 centred on contact 10
  (pads 1 MIC0N / 2 MIC0P / 3 GND / 4 MIC1N / 5 MIC1P); 3.5 mm apart so the courtyards clear.
- microSD capacitors: C401 moves from under the lanes to east of C404 (146.95, 145.75); C402/C404 move 0.06 mm north (y 145.117),
  C402 0.02 mm west and C404 0.02 mm east, so the MIC lanes pass under them with the power-class clearance.
- J401-DET re-route (section 3b): the top hop R402 -> via (135.0, 140.14) -> bottom diagonal -> via (140.225, 144.4) crossed the
  audio lanes. Now: R402 via (138.225, 137.89) -> top south along x 138.225 -> diagonal to the socket DET pad; the old top
  segment, both bottom segments and the two vias go.
- FPC B power: GND contacts bridged in groups with a via under the connector body (y 151.35, as FPC A); mounting tabs to vias;
  5 V contacts 21-22 to one via (In2). The 3V3 contacts 14-15 are bridged; the 3V3 rail reaches them with the rails section."""
import sys, os, subprocess, pcbnew
IN, OUT = sys.argv[1:3]; PH2 = '--phase2' in sys.argv   # pcbnew SWIG gets unstable after removals: phase 2 runs in a fresh process
LAY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 't53_lay.py')
mm, MM = pcbnew.ToMM, pcbnew.FromMM

if not PH2:
  b = pcbnew.LoadBoard(IN)
  fp = {f.GetReference(): f for f in b.GetFootprints()}
  # ---- parts
  def place(ref, x, y, rot, top=None):
      f = fp[ref]
      if top is True and f.IsFlipped(): f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
      f.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y))); f.SetOrientationDegrees(rot)
  place('U1007', 141.25, 148.05, -90.0)
  place('U1006', 144.75, 148.05, -90.0)
  for ref, x in (('C402', 143.98), ('C404', 145.27)):   # the SD capacitor row 0.06 north, C402/C404 0.02 apart (SD_CLK via clearance)
      place(ref, x, 145.117, 90.0)
  place('C401', 146.95, 145.75, 0.0)                     # C401 east of C404 (R406 sits north of its old place)
  CAPS = {'C1001': (135.5, 140.3), 'C1003': (136.9, 140.3), 'C1002': (136.2, 142.5), 'C1004': (137.6, 142.5)}
  for ref, (x, y) in CAPS.items():
      place(ref, x, y, 90.0, top=True)
      f = fp[ref]; f.Reference().SetVisible(False)
      mic = [p for p in f.Pads() if '/Expansion/MIC' in p.GetNetname()][0]
      if mm(mic.GetPosition().y) > y: f.SetOrientationDegrees(270.0)   # RV1106 side (MIC net) north
  # ---- J401-DET: old hop out
  DEL_V = {(135.0, 140.143), (140.225, 144.4)}
  gone = 0
  for t in list(b.GetTracks()):
      if t.GetNetname() != 'Net-(J401-DET)': continue
      if t.Type() == pcbnew.PCB_VIA_T:
          q = t.GetPosition()
          if (round(mm(q.x), 3), round(mm(q.y), 3)) in DEL_V: b.Remove(t); gone += 1
          continue
      s, e = t.GetStart(), t.GetEnd(); pts = {(round(mm(s.x), 3), round(mm(s.y), 3)), (round(mm(e.x), 3), round(mm(e.y), 3))}
      old_top = t.GetLayer() == pcbnew.F_Cu and pts & {(135.0, 140.143), (137.253, 137.89)}
      old_bot = t.GetLayer() == pcbnew.B_Cu and pts & {(135.0, 140.143), (138.217, 143.36), (139.289, 143.36), (140.225, 144.296)}
      if old_top or old_bot: b.Remove(t); gone += 1
  b.Save(OUT); print('parts placed; J401-DET items removed:', gone); sys.stdout.flush()
  os.execv(sys.executable, [sys.executable, __file__, OUT, OUT, '--phase2'])
CAPS = {'C1001': (135.5, 140.3), 'C1003': (136.9, 140.3), 'C1002': (136.2, 142.5), 'C1004': (137.6, 142.5)}
b = pcbnew.LoadBoard(OUT); fp = {f.GetReference(): f for f in b.GetFootprints()}
for ref in ('U1007', 'U1006', 'C401', 'C402', 'C404', *CAPS):
    f = fp[ref]; print(' ', ref, round(mm(f.GetPosition().x), 3), round(mm(f.GetPosition().y), 3), f.GetOrientationDegrees(), 'B' if f.IsFlipped() else 'T',
                       [(p.GetNumber(), round(mm(p.GetPosition().y), 3), p.GetNetname()[-14:]) for p in f.Pads()] if ref.startswith('C10') else '')
pad_y = {ref: {p.GetNetname(): round(mm(p.GetPosition().y), 3) for p in fp[ref].Pads()} for ref in CAPS}
del b

def F(*pts): return 'F:' + '/'.join(f'{x:.3f},{y:.3f}' for x, y in pts)
def Bc(*pts): return 'B:' + '/'.join(f'{x:.3f},{y:.3f}' for x, y in pts)
def V(x, y): return f'V:{x:.3f},{y:.3f}'
YV = 145.0                                        # via row
def bus(xc, L, xpad, c=0.2):   # bottom: via south, 45 corner, east on level L, 45 corner, south through the array pad pair to the contact
    return [(xc, YV), (xc, L - c), (xc + c, L), (xpad - c, L), (xpad, L + c), (xpad, 150.2)]
def mic(px, yt, xc, cap, side_net):               # pin south to yt, SW diagonal to column xc, south to the cap; cap -> via
    yd = yt + (px - xc)
    ys = pad_y[cap]
    ymic = [v for k, v in ys.items() if '/Expansion/MIC' in k][0]; yarr = [v for k, v in ys.items() if '/Expansion/MIC' not in k][0]
    return ([F((px, 135.705), (px, yt), (xc, yd), (xc, ymic))], [F((xc, yarr), (xc, YV)), V(xc, YV)])
PLAN = []
PLAN.append(('/Expansion/LINEOUT', [F((136.775, 134.08), (136.2, 134.08), (134.3, 135.98), (134.3, YV)), V(134.3, YV),
                                    Bc(*bus(134.3, 147.41, 140.25))]))
PLAN.append(('/Expansion/MICBIAS', [F((136.75, 135.13), (136.2, 135.13), (134.9, 136.43), (134.9, YV)), V(134.9, YV),
                                    Bc(*bus(134.9, 147.16, 141.75))]))
MICS = [('MIC0N', 137.35, 136.25, 135.5, 'C1001', 146.91, 143.75), ('MIC0P', 137.7, 136.27, 136.2, 'C1002', 146.66, 144.25),
        ('MIC1N', 138.05, 136.29, 136.9, 'C1003', 146.41, 145.25), ('MIC1P', 138.4, 136.31, 137.6, 'C1004', 146.16, 145.75)]
for name, px, yt, xc, cap, L, xpad in MICS:
    a, rest = mic(px, yt, xc, cap, None)
    side = [k for k in pad_y[cap] if '/Expansion/MIC' not in k][0]
    PLAN.append(('/Expansion/' + name, a))
    PLAN.append((side, rest + [Bc(*bus(xc, L, xpad))]))
# J401-DET: R402 via -> top south -> diagonal into the remaining top junction at (140.225, 144.4)
PLAN.append(('Net-(J401-DET)', [F((138.225, 137.89), (138.225, 142.4), (140.225, 144.4))]))
# FPC B power and ground (contact pads at y 150.2, 149.55-150.85; vias under the connector body at y 151.35)
YG = 151.35
PLAN.append(('GND', [Bc((141.25, 147.665), (141.25, YG)), Bc((140.75, 150.2), (141.25, 150.2)), V(141.25, YG),
                     Bc((142.25, 150.2), (143.25, 150.2)), Bc((142.75, 150.2), (142.75, YG)), V(142.75, YG),
                     Bc((144.75, 147.665), (144.75, YG)), V(144.75, YG),
                     Bc((146.25, 150.2), (146.25, YG)), V(146.25, YG),
                     Bc((147.75, 150.2), (149.75, 150.2)), Bc((148.75, 150.2), (148.75, YG)), V(148.75, YG),
                     Bc((151.25, 150.2), (151.75, 150.2)), Bc((151.5, 150.2), (151.5, YG)), V(151.5, YG),
                     V(138.6, 152.55), V(153.4, 152.55)]))
PLAN.append(('VCC5V0_SYS', [Bc((150.25, 150.2), (150.75, 150.2)), Bc((150.5, 150.2), (150.5, YG)), V(150.5, YG)]))
PLAN.append(('VCC_3V3', [Bc((146.75, 150.2), (147.25, 150.2))]))
for net, steps in PLAN:
    r = subprocess.run([sys.executable, LAY, OUT, net] + steps, capture_output=True, text=True)
    out = [l for l in (r.stdout + r.stderr).strip().splitlines() if 'Debug' not in l and 'leak' not in l]
    print(net, '->', out[-1] if out else r.returncode)
    if r.returncode != 0: sys.exit(1)
