"""T49 (owner, 2026-11-23): Expansion sheet, pogo-pad breakout (proposal v2, approved).
Usage: python3 build_expansion.py <kicad dir> <sheet uuid on root>   -> writes <kicad dir>/expansion.kicad_sch
- TP1001..TP1028: one Connector:TestPoint per pogo pad (footprint linknode:PogoPad_D1.5, placed on B.Cu in a 7 x 4 grid,
  pad n = TP10nn; pad 1 = MH1 + (56.00, 27.20) mm). Pads are copper only: excluded from BOM and position files.
- U1001..U1005: DOWO TPD4E05U06DQAR (LCSC C22390021, already used on microSD) on the 17 signal pads. Each chip takes
  two nets from the left and two from the right, so every tap is a straight row (no crossings).
- R1001..R1004: 0R in series on ETH TX+/TX-/RX+/RX- (HDG Table 2-11: "cannot be omitted"); placed at the pads,
  as drawn in HDG Fig 2-22. The long run keeps the ETH_TXP/TXN/RXP/RXN names for the diff-pair router.
- R1005..R1008: 4.7k pull-ups to VCC_3V3 on I2C2 and I2C0.
- Power pads: VCC_3V3 (TP1014) and VCC5V0_SYS (TP1007), unswitched (owner); GND pads TP1003/06/08/13/28.
Library symbols are copied from soc.kicad_sch (R_Small, TestPoint, GND, VCC) and microsd.kicad_sch (TPD4E05U06DQA)."""
import sys, os, re, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import symlib
K, SHEET_UUID = sys.argv[1], sys.argv[2]
ROOT = 'd95cb237-0177-4440-a7e6-29dc79faada9'
PATH = f'/{ROOT}/{SHEET_UUID}'
U = lambda: str(uuid.uuid4())
def g(v): return ('%.2f' % v).rstrip('0').rstrip('.')

def blk_at(s, i):
    d = 0
    for j, ch in enumerate(s[i:]):
        if ch == '(': d += 1
        elif ch == ')':
            d -= 1
            if d == 0: return s[i:i + j + 1]
def libsym(path, name):
    s = open(path).read(); i = s.index('(lib_symbols'); body = s[i:]
    k = body.index(f'(symbol "{name}"'); return blk_at(body, k)
soc = os.path.join(K, 'soc.kicad_sch'); msd = os.path.join(K, 'microsd.kicad_sch')
LIB = [libsym(soc, n) for n in ('Device:R_Small', 'Connector:TestPoint', 'power:GND', 'power:VCC')] + [libsym(msd, 'Power_Protection:TPD4E05U06DQA'), libsym(soc, 'Device:C_Small')]

items = []; syms = []; pwr_n = [0]
OLD_UUID = {}   # keep the symbol UUIDs of an existing sheet, so board footprints stay linked when the sheet is regenerated
_op = os.path.join(K, 'expansion.kicad_sch')
if os.path.exists(_op):
    _os = open(_op).read()
    for _m in re.finditer(r'\n\t\(symbol\n\t\t\(lib_id "[^"]+"\)(?:.|\n)*?\n\t\t\(uuid "([^"]+)"\)(?:.|\n)*?\(property "Reference" "([^"]+)"', _os):
        OLD_UUID.setdefault(_m.group(2), _m.group(1))
def field(name, val, x, y, ang=0, hide=False, just=None):
    h = '\n\t\t\t(hide yes)' if hide else ''
    j = f'\n\t\t\t\t(justify {just})' if just else ''
    return f'''
		(property "{name}" "{val}"
			(at {g(x)} {g(y)} {ang}){h}
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				){j}
			)
		)'''
def sym(lib, ref, val, fp, x, y, rot, fields, pins, lcsc=None, bom=True, pos=True, desc='', dsheet=''):
    lc = field('LCSC', lcsc, x, y, 0, True) if lcsc else ''
    pin_s = ''.join(f'\n\t\t(pin "{p}"\n\t\t\t(uuid "{U()}")\n\t\t)' for p in pins)
    syms.append(f'''
	(symbol
		(lib_id "{lib}")
		(at {g(x)} {g(y)} {rot})
		(unit 1)
		(body_style 1)
		(exclude_from_sim no)
		(in_bom {'yes' if bom else 'no'})
		(on_board yes)
		(in_pos_files {'yes' if pos else 'no'})
		(dnp no)
		(uuid "{OLD_UUID.get(ref) or U()}"){fields}{field('Footprint', fp, x, y, 0, True)}{field('Datasheet', dsheet, x, y, 0, True)}{field('Description', desc, x, y, 0, True)}{lc}{pin_s}
		(instances
			(project "linknode"
				(path "{PATH}"
					(reference "{ref}")
					(unit 1)
				)
			)
		)
	)''')
def power(net, x, y, rot=0):
    pwr_n[0] += 1; ref = f'#PWR{1300 + pwr_n[0]}'
    lib = 'power:GND' if net == 'GND' else 'power:VCC'
    vy = y + 3.81 if net == 'GND' or rot == 180 else y - 3.81
    if net != 'GND' and rot == 180: vy = y + 3.81
    syms.append(f'''
	(symbol
		(lib_id "{lib}")
		(at {g(x)} {g(y)} {rot})
		(unit 1)
		(body_style 1)
		(exclude_from_sim no)
		(in_bom no)
		(on_board no)
		(in_pos_files yes)
		(dnp no)
		(uuid "{U()}"){field('Reference', ref, x, y, 0, True)}{field('Value', net, x, vy, 0)}{field('Footprint', '', x, y, 0, True)}{field('Datasheet', '', x, y, 0, True)}{field('Description', '', x, y, 0, True)}
		(pin "1"
			(uuid "{U()}")
		)
		(instances
			(project "linknode"
				(path "{PATH}"
					(reference "{ref}")
					(unit 1)
				)
			)
		)
	)''')
def wire(*pts):
    for a, b in zip(pts, pts[1:]):
        items.append(f'\n\t(wire\n\t\t(pts\n\t\t\t(xy {g(a[0])} {g(a[1])}) (xy {g(b[0])} {g(b[1])})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')
def junction(x, y):
    items.append(f'\n\t(junction\n\t\t(at {g(x)} {g(y)})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{U()}")\n\t)')
def nc(x, y):
    items.append(f'\n\t(no_connect\n\t\t(at {g(x)} {g(y)})\n\t\t(uuid "{U()}")\n\t)')
HL = []
def hlabel(name, x, y, rot, shape):
    just = 'right' if rot == 180 else 'left'
    HL.append((name, shape))
    items.append(f'''
	(hierarchical_label "{name}"
		(shape {shape})
		(at {g(x)} {g(y)} {rot})
		(effects
			(font
				(size 1.27 1.27)
			)
			(justify {just})
		)
		(uuid "{U()}")
	)''')

TPFP = 'linknode:PogoPad_D1.5'
def tp(n, x, y, up=True):
    ref = f'TP10{n:02d}'
    rot = 0 if up else 180
    ry = y - 5.59 if up else y + 5.59
    sym('Connector:TestPoint', ref, f'PAD{n}', TPFP, x, y, rot,
        field('Reference', ref, x, ry, 0) + field('Value', f'PAD{n}', x, y, 0, True), ['1'], bom=False, pos=False,
        desc=f'Expansion pogo pad {n} (bottom, D1.5 mm)')
def res(ref, val, x, y, rot, lcsc):
    if rot == 90: fl = field('Reference', ref, x, y - 2.54, 90) + field('Value', val, x, y + 2.54, 90)   # angle 90 on a 90-deg symbol renders horizontal (footgun, project rules)
    else: fl = field('Reference', ref, x + 1.27, y - 1.27, 0, just='left') + field('Value', val, x + 1.27, y + 1.27, 0, just='left')
    sym('Device:R_Small', ref, val, 'Resistor_SMD:R_0402_1005Metric', x, y, rot, fl, ['1', '2'], lcsc=lcsc)
def cap(ref, val, x, y, lcsc, up=True):   # horizontal (rot 90), fields angle 90 so they render level; both on the outer side
    d = -1 if up else 1
    fl = field('Reference', ref, x, y + d * (4.06 if up else 2.29), 90) + field('Value', val, x, y + d * (2.29 if up else 4.06), 90)
    sym('Device:C_Small', ref, val, 'Capacitor_SMD:C_0402_1005Metric', x, y, 90, fl, ['1', '2'], lcsc=lcsc,
        desc='MIC input series capacitor, 1 uF X5R (HDG Table 2-12 p.31, Fig 2-24)')
def esd(ref, xc, yc):
    fl = field('Reference', ref, xc, yc - 8.89, 0, just='left') + field('Value', 'TPD4E05U06DQAR', xc + 2.54, yc + 17.78, 0, just='left')
    sym('Power_Protection:TPD4E05U06DQA', ref, 'TPD4E05U06DQAR', 'Package_SON:USON-10_2.5x1.0mm_P0.5mm', xc, yc, 0, fl,
        [str(i) for i in range(1, 11)], lcsc='C22390021', dsheet='hardware/datasheets/DOWO_TPD4E05U06DQAR.pdf',
        desc='4-channel ESD array, 0.5 pF max, VRWM 5.0 V (DOWO datasheet p.2): expansion pogo pads')
    power('GND', xc, yc + 12.7)

# ---------------- ESD groups: (ref, xc, yc, [(label, pad, side, row, shape, pullup)])  row: -1 = yc-2.54, +1 = yc+2.54
COLS = {'A': (96.52, 40.64, 63.5, 127.0, 149.86, 48.26, 137.16), 'B': (217.17, 160.02, 182.88, 247.65, 269.24, 168.91, 257.81)}
GROUPS = [
    ('U1001', 'A', 35.56, [('I2C2_SDA', 9, 'L', -1, 'bidirectional', True), ('I2C2_SCL', 10, 'L', 1, 'bidirectional', True),
                           ('I2C0_SDA', 11, 'R', -1, 'bidirectional', True), ('I2C0_SCL', 12, 'R', 1, 'bidirectional', True)]),
    ('U1002', 'A', 66.04, [('SPI0_CS0', 15, 'L', -1, 'output', False), ('SPI0_CLK', 16, 'L', 1, 'output', False),
                           ('SPI0_MOSI', 17, 'R', -1, 'output', False), ('SPI0_MISO', 18, 'R', 1, 'input', False)]),
    ('U1003', 'A', 96.52, [('EXP_GPIO1_B1', 19, 'L', -1, 'bidirectional', False), ('EXP_GPIO1_C7', 20, 'L', 1, 'bidirectional', False),
                           ('EXP_GPIO0_A4', 21, 'R', -1, 'bidirectional', False), ('EXP_GPIO0_A3', 22, 'R', 1, 'bidirectional', False)]),
    ('U1004', 'B', 50.8, [('EXP_GPIO4_A6', 23, 'L', -1, 'bidirectional', False), ('EXP_GPIO4_A4', 24, 'L', 1, 'bidirectional', False),
                           ('EXP_GPIO4_A3', 25, 'R', -1, 'bidirectional', False), ('EXP_GPIO4_A2', 26, 'R', 1, 'bidirectional', False)]),
    ('U1005', 'B', 81.28, [('EXP_GPIO4_B0', 27, 'L', -1, 'bidirectional', False), ('MICBIAS', 34, 'L', 1, 'input', False),
                           ('LINEOUT', 35, 'R', -1, 'input', False)]),
    ('U1006', 'A', 157.48, [('MIC0P', 29, 'L', -1, 'output', 'C1001'), ('MIC0N', 30, 'L', 1, 'output', 'C1002'),
                            ('MIC1P', 32, 'R', -1, 'output', 'C1003'), ('MIC1N', 33, 'R', 1, 'output', 'C1004')]),
]
pu = [5]
for ref, col, yc, nets in GROUPS:
    xc, xL, xTL, xTR, xR, xPL, xPR = COLS[col]
    esd(ref, xc, yc)
    used = set()
    for lab, pad, side, row, shape, pull in nets:
        y = yc + 2.54 * row
        series = pull if isinstance(pull, str) else None   # a reference = a series cap between label and pad
        if series: pull = False
        if side == 'L':
            pin = (xc - 12.7, y); hlabel(lab, xL, y, 180, shape); tp(pad, xTL, y, up=(row < 0))
            if series: cap(series, '1uF', xL + 10.16, y, 'C52923', up=(row < 0)); wire((xL, y), (xL + 7.62, y)); wire((xL + 12.7, y), (xTL, y), pin)
            else: wire((xL, y), (xTL, y), pin)
            xp = xPL
        else:
            pin = (xc + 12.7, y); hlabel(lab, xR, y, 0, shape); tp(pad, xTR, y, up=(row < 0))
            if series: cap(series, '1uF', xR - 10.16, y, 'C52923', up=(row < 0)); wire(pin, (xTR, y), (xR - 12.7, y)); wire((xR - 7.62, y), (xR, y))
            else: wire(pin, (xTR, y), (xR, y))
            xp = xPR
        used.add((side, row))
        if pull:   # 4.7k to VCC_3V3: above the row for row -1, below for row +1
            r = f'R10{pu[0]:02d}'; pu[0] += 1
            if row < 0: res(r, '4.7k', xp, y - 2.54, 0, 'C25900'); power('VCC_3V3', xp, y - 5.08)
            else: res(r, '4.7k', xp, y + 2.54, 0, 'C25900'); power('VCC_3V3', xp, y + 5.08, 180)
            junction(xp, y)
    for side in ('L', 'R'):
        x = xc - 12.7 if side == 'L' else xc + 12.7
        for row in (-1, 1):
            if (side, row) not in used: nc(x, yc + 2.54 * row)
        nc(x, yc - 7.62); nc(x, yc + 7.62)

# ---------------- Ethernet: label -> 0R -> pad (rows 10.16 apart, pads point up)
ETH = [('ETH_TXP', 1, 'output'), ('ETH_TXN', 2, 'output'), ('ETH_RXP', 4, 'input'), ('ETH_RXN', 5, 'input')]
for i, (lab, pad, shape) in enumerate(ETH):
    y = 111.76 + i * 10.16; xr = 190.5
    hlabel(lab, 167.64, y, 180, shape)
    res(f'R10{i + 1:02d}', '0R', xr, y, 90, 'C17168')
    wire((167.64, y), (xr - 2.54, y)); wire((xr + 2.54, y), (210.82, y)); tp(pad, 210.82, y, up=True)

# ---------------- power and GND pads: pad up, wire down 2.54 to the power symbol
PWRP = [(3, 'GND'), (6, 'GND'), (8, 'GND'), (13, 'GND'), (28, 'GND'), (7, 'VCC5V0_SYS'), (14, 'VCC_3V3'), (31, 'GND')]
for i, (pad, net) in enumerate(PWRP):
    x, y = (50.8 + i * 15.24, 132.08) if i < 7 else (35.56, 142.24)   # pad 31: audio GND (T50)
    tp(pad, x, y, up=True); wire((x, y), (x, y + 2.54))
    power(net, x, y + 2.54, 0 if net == 'GND' else 180)

assert len([s for s in syms if 'Connector:TestPoint' in s]) == 35
head = f'''(kicad_sch
	(version 20260101)
	(generator "eeschema")
	(generator_version "10.0")
	(uuid {SHEET_UUID})
	(paper "A4")
	(title_block
		(title "Expansion")
		(date "2026-11-23")
		(rev "1")
		(company "Teapot Laboratories")
		(comment 1 "Pogo pads on the bottom: pad n = TP10nn, pad 1 = MH1 + (56.00, 27.20) mm, 7 x 5 at 2.54 mm pitch")
	)
	(lib_symbols
''' + '\n'.join('\t\t' + l.replace('\n', '\n') for l in LIB) + '\n\t)'
body = ''.join(items) + ''.join(syms)
tail = f'''
	(sheet_instances
		(path "/"
			(page "14")
		)
	)
	(embedded_fonts no)
)
'''
out = os.path.join(K, 'expansion.kicad_sch')
open(out, 'w').write(head + body + tail)
print('written', out, '| symbols', len(syms), '| items', len(items), '| hier labels', len(HL))
print('HIER', [h[0] for h in HL])
