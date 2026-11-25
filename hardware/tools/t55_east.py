"""T55 routing (2026-11-24, owner: "re-lay together"): the RV1106 east side as one planned set. The ESP32-C5 and GPS lines
(T54) are re-laid together with the FPC A expansion lines (SPI0, I2C0, I2C2, GPIO1_C7, GPIO1_B1) and the I2C pull-up taps.
Usage: python3 t55_east.py <board.kicad_pcb> [NET ...]     (lays every net in PLAN order, or only the named ones)

Plan (all lines 0.12 mm, 45-degree bends only):
- Tier 1 (pins 95..83): fanned on top at 0.42 mm pitch (SPI0 to 122.45..123.62, the rest to 125.38..128.30) so every via has
  0.38 mm (via 0.2 + 0.12 + 0.06) to the lanes that pass it.
- Tier 2 (pins 78..72): fanned on top to 0.40 mm pitch (129.90..132.30).
- Each line ends in its own via column: west slots 152.29/152.76/153.23/153.70 (SPI0 dive vias north, I2C columns going north),
  corridor slots 154.10/154.50/154.90/155.30/155.70 (UTX, HAN, URX, C7+DR, B1+EN: the GPIO lines go north from the via, the
  C5 lines go south from a via further south in the same column). The corridor clears the Y501 keep-out (x <= 153.55) and the
  T54 SPI dive via (153.65, 139.4).
- Bottom levels into FPC A (N->S = array pads W->E): SPI0 122.45/122.84/123.23/123.62, SDA0 124.01, SCL0 124.26, SDA2 124.51,
  SCL2 124.76, C7 125.01, B1 125.26 (all north of the HAN via 125.78).
- I2C pull-ups: a via at the corner of each I2C column (bottom lane) feeds a top trace to its pull-up (R1007, R1008, R1005,
  R1006 on top); their 3V3 pads are joined on top and dropped to the 3V3 contact 7.
- GPS: TXD and RXD hop to the bottom (vias 156.5/156.1) and come up under their pads; PPS stays on top and passes under pad 1.
- C5 lines end in a via beside their pad with a short top stub (as T54); BOOT via west of the module edge, bottom stub to R802."""
import sys, os, subprocess, json
B = sys.argv[1]; ONLY = set(sys.argv[2:])
LAY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 't53_lay.py')
P = 148.775; X1 = 149.45; X2 = 149.6          # pad centre, tier-1 / tier-2 fan start

T1 = [124.63, 124.98, 125.33, 125.68, 126.03, 126.38, 126.73, 127.08, 127.43, 127.78, 128.13, 128.48, 128.83]   # pins 95..83
T2 = [130.58, 130.93, 131.28, 131.63, 131.98, 132.33, 132.68]                                                   # pins 78..72
def fan(x0, tier, yp, yt, xv):   # pin -> east -> 45-degree fan -> east to via x. Each lane starts its diagonal 0.03 mm east of
    x = round(x0 + 0.03 * tier.index(yp), 3)      # the lane above it, so neighbouring diagonals keep >= 0.13 mm gap at 0.35 pitch
    return [(P, yp), (x, yp), (round(x + yp - yt, 3), yt), (xv, yt)]
def fan1(yp, yt, xv): return fan(X1, T1, yp, yt, xv)
def fan2(yp, yt, xv): return fan(X2, T2, yp, yt, xv)
def F(*pts): return 'F:' + '/'.join(f'{x:.3f},{y:.3f}' for x, y in pts)
def Bc(*pts): return 'B:' + '/'.join(f'{x:.3f},{y:.3f}' for x, y in pts)
def V(x, y): return f'V:{x:.3f},{y:.3f}'
def level(xc, yv, L, xpad, ypad, c=0.2):   # column up from the via, 45-degree corner, level east, corner, north to the array pad
    return [(xc, yv), (xc, L + c), (xc + c, L), (xpad - c, L), (xpad, L - c), (xpad, ypad)]

PLAN = []
# ---- SPI0 (west dive vias, bottom levels straight into U1002's south row)
for net, yp, yt, xv, xpad in (('SPI0_CS0', 124.63, 122.45, 152.29, 158.75), ('SPI0_CLK', 124.98, 122.84, 152.76, 159.25),
                               ('SPI0_MOSI', 125.33, 123.23, 153.23, 160.25), ('SPI0_MISO', 125.68, 123.62, 153.70, 160.75)):
    PLAN.append((net, [F(*fan1(yp, yt, xv)), V(xv, yt), Bc((xv, yt), (xpad - 0.2, yt), (xpad, yt - 0.2), (xpad, 121.185))]))
# ---- I2C (tier 2 -> west columns -> levels -> U1003 south row), corner tap via -> top trace -> pull-up
I2C = (('I2C0_SDA', 131.28, 130.70, 152.29, 124.01, 161.25, [(154.25, 124.01), (154.45, 123.81), (154.45, 123.51)]),
       ('I2C0_SCL', 131.63, 131.10, 152.76, 124.26, 161.75, [(154.79, 124.26), (154.99, 124.06), (154.99, 121.30)]),
       ('I2C2_SDA', 132.33, 131.90, 153.23, 124.51, 162.75, [(155.32, 124.51), (155.52, 124.31), (155.52, 123.51)]),
       ('I2C2_SCL', 132.68, 132.30, 153.70, 124.76, 163.25, [(156.28, 124.76), (156.48, 124.56), (156.48, 123.51)]))
for net, yp, yt, xv, L, xpad, tail in I2C:
    PLAN.append((net, [F(*fan2(yp, yt, xv)), V(xv, yt), Bc(*level(xv, yt, L, xpad, 123.285)), V(xv, L + 0.2),
                       F((xv, L + 0.2), (xv + 0.2, L), *tail)]))
# ---- GPIO to FPC A (C7 tier 1, B1 tier 2; share the C5 columns, north of the C5 vias)
PLAN.append(('EXP_GPIO1_C7', [F(*fan1(128.48, 127.88, 155.30)), V(155.30, 127.88), Bc(*level(155.30, 127.88, 125.01, 163.75, 121.185))]))
PLAN.append(('EXP_GPIO1_B1', [F(*fan2(130.58, 129.90, 155.70)), V(155.70, 129.90), Bc(*level(155.70, 129.90, 125.26, 164.25, 121.185))]))
# ---- ESP32-C5 lines: corridor column down to a via beside the pad, top stub into the pad (x 156.89)
for net, yp, yt, xv, ypad in (('C5_UART_TX', 127.78, 127.04, 154.10, 144.26), ('C5_HANDSHAKE', 126.38, 125.78, 154.50, 139.18),
                              ('C5_UART_RX', 128.13, 127.46, 154.90, 142.99)):
    PLAN.append((net, [F(*fan1(yp, yt, xv)), V(xv, yt), Bc((xv, yt), (xv, ypad)), V(xv, ypad), F((xv, ypad), (156.89, ypad))]))
PLAN.append(('C5_DATA_READY', [F(*fan1(128.83, 128.28, 154.24)[:-1], (154.24, 128.28), (154.96, 129.0), (155.30, 129.0)), V(155.30, 129.0),
                               Bc((155.30, 129.0), (155.30, 141.72)), V(155.30, 141.72), F((155.30, 141.72), (156.89, 141.72))]))
PLAN.append(('C5_EN', [F(*fan2(131.98, 131.50, 155.70)), V(155.70, 131.50),
                       Bc((155.70, 131.50), (155.70, 147.25), (156.15, 147.7), (169.85, 147.7), (170.3, 147.25))]))
PLAN.append(('C5_BOOT', [F(*fan2(130.93, 130.30, 155.6), (155.9, 130.6)), V(155.9, 130.6), F((155.9, 130.6), (156.5, 131.2)),
                         Bc((155.9, 130.6), (156.9, 131.6), (156.99, 131.6))]))
# ---- GPS: RXD/TXD hop under the pads, PPS on top under pad 1
PLAN.append(('GPS_RXD', [F(*fan1(126.73, 126.20, 156.1)), V(156.1, 126.20), Bc((156.1, 126.20), (159.705, 126.20), (160.125, 126.62)),
                         V(160.125, 126.62), F((160.125, 126.62), (160.125, 125.475))]))
PLAN.append(('GPS_TXD', [F(*fan1(127.43, 126.62, 156.5)), V(156.5, 126.62), Bc((156.5, 126.62), (159.025, 126.62)),
                         V(159.025, 126.62), F((159.025, 126.62), (159.025, 125.475))]))
PLAN.append(('GPS_PPS', [F(*fan1(126.03, 125.38, 156.05), (157.68, 127.01), (160.9, 127.01), (161.225, 126.685), (161.225, 125.475))]))
# ---- pull-up 3V3: R1007.1 north, over R1008, into R1008.2, on to R1006.2 and R1005.1; via at the corner down to contact 7
PLAN.append(('VCC_3V3', [F((154.45, 122.49), (154.45, 120.6), (155.81, 120.6), (156.01, 120.8), (156.01, 121.3), (156.48, 121.77), (156.48, 122.49), (155.52, 122.49)),
                         V(154.45, 120.6), Bc((154.45, 120.6), (157.5, 120.6), (157.75, 120.35), (157.75, 118.6))]))

# ---- FPC A: contact -> array north row -> flow-through to the south row (TI SLVSBO7O 6.3.9), straight or one 0.5 mm jog
def jog(x0, x1, ypad): return [(x0, 118.6), (x0, 119.4), (x1, 119.9), (x1, ypad)] if x1 != x0 else [(x0, 118.6), (x0, ypad)]
for net, xc, xp, ys in (('SPI0_CS0', 158.75, 158.75, 121.185), ('SPI0_CLK', 159.25, 159.25, 121.185), ('SPI0_MOSI', 159.75, 160.25, 121.185),
                        ('SPI0_MISO', 160.25, 160.75, 121.185), ('I2C0_SDA', 161.25, 161.25, 123.285), ('I2C0_SCL', 161.75, 161.75, 123.285),
                        ('I2C2_SDA', 162.25, 162.75, 123.285), ('I2C2_SCL', 162.75, 163.25, 123.285),
                        ('EXP_GPIO1_C7', 163.25, 163.75, 121.185), ('EXP_GPIO1_B1', 163.75, 164.25, 121.185)):
    PLAN.append((net, [Bc(*jog(xc, xp, ys))]))
# ---- FPC A power: array GND pads through to a via south; GND contacts 13 and 20-22 to vias north of the pads (under the
# connector body), the mounting tabs to vias; 5 V contacts 23-24 to a via south (In2); 3V3 contact 8 joined to contact 7
PLAN.append(('GND', [Bc((159.75, 120.415), (159.75, 121.85)), V(159.75, 121.85), Bc((162.25, 122.515), (162.25, 123.9)), V(162.25, 123.9),
                     Bc((164.75, 120.415), (164.75, 121.85)), V(164.75, 121.85), Bc((160.75, 118.6), (160.75, 117.35)), V(160.75, 117.35),
                     Bc((164.25, 118.6), (165.25, 118.6)), Bc((164.75, 118.6), (164.75, 117.35)), V(164.75, 117.35),
                     V(153.1, 116.25), V(167.9, 116.25)]))
PLAN.append(('VCC5V0_SYS', [Bc((165.75, 118.6), (166.25, 118.6)), Bc((166.25, 118.6), (166.25, 119.8)), V(166.25, 119.8)]))
PLAN.append(('VCC_3V3', [Bc((158.25, 118.6), (158.25, 119.65), (157.75, 120.15))]))

def full(b, short):   # the board's full net name for a short name
    import pcbnew
    for n in b.GetNetsByName().keys():
        s = str(n)
        if s == short or s.endswith('/' + short): return s
    raise SystemExit('no net ' + short)
import pcbnew
bb = pcbnew.LoadBoard(B); names = {k: full(bb, k) for k, _ in PLAN}; del bb
for net, steps in PLAN:
    if ONLY and net not in ONLY: continue
    r = subprocess.run([sys.executable, LAY, B, names[net]] + steps, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip().splitlines()
    msg = [l for l in out if 'Debug' not in l and 'leak' not in l]
    print(net, '->', msg[-1] if msg else r.returncode)
    if r.returncode != 0: sys.exit(1)
