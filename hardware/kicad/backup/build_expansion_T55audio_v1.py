"""T49 (owner, 2026-11-23) expansion breakout; T55 (owner, 2026-11-24): two 24-pin 0.5 mm FPC connectors instead of the
35 pogo pads (approved plan, page section exp3).
Usage: python3 build_expansion.py <kicad dir> <sheet uuid on root>   -> writes <kicad dir>/expansion.kicad_sch
- J1001 (FPC A, bottom under the GPS) and J1002 (FPC B, bottom under the microSD socket): JUSHUO AFC07-S24ECC-00 (LCSC C11092,
  0.4 A per contact, hardware/datasheets/JUSHUO_AFC07-S24ECC-00.pdf p.1). Symbol linknode:FPC_24P_MP has one unit per contact
  (units 1-24 = pins 1-24, unit 25 = the two mounting tabs, tied to GND), so each contact sits on its own signal row where a
  pogo pad used to be. J1001 is placed flipped at 0 deg (pin 1 at the west end), J1002 flipped at 180 deg (pin 1 at the east
  end), so both read in RV1106-pin order west to east (see A_MAP / B_MAP).
- U1001..U1003, U1006, U1007: DOWO TPD4E05U06DQAR (LCSC C22390021): FPC A U1001-U1003, FPC B U1006 (mics), U1007 (MICBIAS, LINEOUT);
  flow-through: each used channel's NC pin is tied to its IO pin (TI SLVSBO7O Table 4-2 p.4), channel order = contact order.
- R1001..R1004: 0R in series on ETH TX+/TX-/RX+/RX- (HDG Table 2-11: "cannot be omitted"), placed at the chip.
- R1005..R1008: 4.7k pull-ups to VCC_3V3 on I2C2 and I2C0. C1001..C1004: 1 uF in series on the mic lines (HDG Table 2-12).
- Power on each connector: VCC_3V3 x2 and VCC5V0_SYS x2 (unswitched), GND between groups.
Library symbols are copied from soc.kicad_sch (R_Small, GND, VCC, C_Small), microsd.kicad_sch (TPD4E05U06DQA) and
library/linknode.kicad_sym (FPC_24P_MP)."""
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
LIB = [libsym(soc, n) for n in ('Device:R_Small', 'power:GND', 'power:VCC')] + [libsym(msd, 'Power_Protection:TPD4E05U06DQA'), libsym(soc, 'Device:C_Small')]
_ls = open(os.path.join(K, 'library', 'linknode.kicad_sym')).read(); _k = _ls.index('(symbol "FPC_24P_MP"')
LIB.append(blk_at(_ls, _k).replace('(symbol "FPC_24P_MP"', '(symbol "linknode:FPC_24P_MP"', 1))

items = []; syms = []; pwr_n = [0]
OLD_UUID = {}   # keep the symbol UUIDs of an existing sheet, so board footprints stay linked when the sheet is regenerated
_op = os.path.join(K, 'expansion.kicad_sch')
if os.path.exists(_op):
    _os = open(_op).read()
    for _m in re.finditer(r'\n\t\(symbol\n\t\t\(lib_id "[^"]+"\)\n\t\t\(at [^)]*\)\n\t\t\(unit (\d+)\)(?:.|\n)*?\n\t\t\(uuid "([^"]+)"\)(?:.|\n)*?\(property "Reference" "([^"]+)"', _os):
        OLD_UUID.setdefault((_m.group(3), int(_m.group(1))), _m.group(2))   # T55: keyed by (reference, unit)
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
def sym(lib, ref, val, fp, x, y, rot, fields, pins, lcsc=None, bom=True, pos=True, desc='', dsheet='', unit=1):
    lc = field('LCSC', lcsc, x, y, 0, True) if lcsc else ''
    pin_s = ''.join(f'\n\t\t(pin "{p}"\n\t\t\t(uuid "{U()}")\n\t\t)' for p in pins)
    syms.append(f'''
	(symbol
		(lib_id "{lib}")
		(at {g(x)} {g(y)} {rot})
		(unit {unit})
		(body_style 1)
		(exclude_from_sim no)
		(in_bom {'yes' if bom else 'no'})
		(on_board yes)
		(in_pos_files {'yes' if pos else 'no'})
		(dnp no)
		(uuid "{OLD_UUID.get((ref, unit)) or U()}"){fields}{field('Footprint', fp, x, y, 0, True)}{field('Datasheet', dsheet, x, y, 0, True)}{field('Description', desc, x, y, 0, True)}{lc}{pin_s}
		(instances
			(project "linknode"
				(path "{PATH}"
					(reference "{ref}")
					(unit {unit})
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

FPCFP = 'linknode:Jushuo_AFC07-S24ECC-00_1x24-1MP_P0.50_Horizontal'
FPCVAL = {'J1001': 'FPC A 24P', 'J1002': 'FPC B 24P'}
def conn(jp, x, y, up=True):   # one contact of J1001/J1002 (jp = (ref, pin)); unit = pin, 25 = mounting tabs
    ref, pin = jp; unit = 25 if pin == 'MP' else int(pin)
    rot = 0 if up else 180; ry = y - 5.59 if up else y + 5.59
    show_val = unit == 25
    vy = y - 7.62 if up else y + 7.62
    sym('linknode:FPC_24P_MP', ref, FPCVAL[ref], FPCFP, x, y, rot,
        field('Reference', ref, x, ry, 0) + field('Value', FPCVAL[ref], x, vy, 0, not show_val), ['MP' if unit == 25 else str(unit)],
        lcsc='C11092', dsheet='hardware/datasheets/JUSHUO_AFC07-S24ECC-00.pdf', unit=unit,
        desc='Expansion FPC connector, 24 pins 0.5 mm (JUSHUO AFC07-S24ECC-00), bottom side')
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
# T55 pin maps, west to east as seen from the top. J1001: pin n at position n. J1002 (flipped, 0 deg): pin = 25 - position.
A = lambda n: ('J1001', n)
B = lambda pos: ('J1002', 25 - pos)
GROUPS = [
    # FPC A v3 pin map (T55 routing, 2026-11-24): contacts follow the board's lane order (I2C inner, GPIO outer)
    ('U1001', 'A', 35.56, [('EXP_GPIO1_C7', A(18), 'L', -1, 'bidirectional', False), ('EXP_GPIO1_B1', A(19), 'L', 1, 'bidirectional', False)]),
    ('U1002', 'A', 66.04, [('SPI0_CS0', A(9), 'L', -1, 'output', False), ('SPI0_CLK', A(10), 'L', 1, 'output', False),
                           ('SPI0_MOSI', A(11), 'R', -1, 'output', False), ('SPI0_MISO', A(12), 'R', 1, 'input', False)]),
    ('U1003', 'A', 96.52, [('I2C0_SDA', A(14), 'L', -1, 'bidirectional', True), ('I2C0_SCL', A(15), 'L', 1, 'bidirectional', True),
                           ('I2C2_SDA', A(16), 'R', -1, 'bidirectional', True), ('I2C2_SCL', A(17), 'R', 1, 'bidirectional', True)]),
    # FPC B audio only (T55, owner 2026-11-24): the 7 GPIOs and their arrays U1004/U1005 dropped
    ('U1006', 'A', 157.48, [('MIC0N', B(5), 'L', -1, 'output', 'C1001'), ('MIC0P', B(6), 'L', 1, 'output', 'C1002'),
                            ('MIC1N', B(8), 'R', -1, 'output', 'C1003'), ('MIC1P', B(9), 'R', 1, 'output', 'C1004')]),
    ('U1007', 'B', 20.32, [('LINEOUT', B(2), 'L', -1, 'input', False), ('MICBIAS', B(4), 'L', 1, 'input', False)]),
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
            pin = (xc - 12.7, y); hlabel(lab, xL, y, 180, shape); conn(pad, xTL, y, up=(row < 0))
            if series: cap(series, '1uF', xL + 10.16, y, 'C52923', up=(row < 0)); wire((xL, y), (xL + 7.62, y)); wire((xL + 12.7, y), (xTL, y), pin)
            else: wire((xL, y), (xTL, y), pin)
            xp = xPL
        else:
            pin = (xc + 12.7, y); hlabel(lab, xR, y, 0, shape); conn(pad, xTR, y, up=(row < 0))
            if series: cap(series, '1uF', xR - 10.16, y, 'C52923', up=(row < 0)); wire(pin, (xTR, y), (xR - 12.7, y)); wire((xR - 7.62, y), (xR, y))
            else: wire(pin, (xTR, y), (xR, y))
            xp = xPR
        used.add((side, row))
        if pull:   # 4.7k to VCC_3V3: above the row for row -1, below for row +1
            r = {'I2C2_SDA': 'R1005', 'I2C2_SCL': 'R1006', 'I2C0_SDA': 'R1007', 'I2C0_SCL': 'R1008'}[lab]   # refs stay with their nets
            if row < 0: res(r, '4.7k', xp, y - 2.54, 0, 'C25900'); power('VCC_3V3', xp, y - 5.08)
            else: res(r, '4.7k', xp, y + 2.54, 0, 'C25900'); power('VCC_3V3', xp, y + 5.08, 180)
            junction(xp, y)
    for side in ('L', 'R'):   # T55: TI SLVSBO7O Table 4-2 p.4 / 6.3.9 p.12: NC pins 10/9/7/6 sit straight across from IO 1/2/4/5,
        x = xc - 12.7 if side == 'L' else xc + 12.7   # "used for optional straight-through routing": tied to the IO net so the
        for row in (-1, 1):                            # board track can run through both pads (flow-through)
            ync = yc + 7.62 * row
            if (side, row) not in used: nc(x, yc + 2.54 * row); nc(x, ync)
            else: wire((x, ync), (x, yc + 2.54 * row)); junction(x, yc + 2.54 * row)

# ---------------- Ethernet: label -> 0R -> pad (rows 10.16 apart, pads point up)
ETH = [('ETH_TXP', A(1), 'output'), ('ETH_TXN', A(2), 'output'), ('ETH_RXP', A(4), 'input'), ('ETH_RXN', A(5), 'input')]
for i, (lab, pad, shape) in enumerate(ETH):
    y = 111.76 + i * 10.16; xr = 200.66   # T55: block 10.16 right so the FPC A power row clears it
    hlabel(lab, 177.8, y, 180, shape)
    res(f'R10{i + 1:02d}', '0R', xr, y, 90, 'C17168')
    wire((177.8, y), (xr - 2.54, y)); wire((xr + 2.54, y), (220.98, y)); conn(pad, 220.98, y, up=True)

# ---------------- power and GND contacts: contact up, wire down 2.54 to the power symbol; one row per connector
PWR_A = [A(3), A(6), A(13), A(20), A(21), A(22), ('J1001', 'MP')]   # v3: 5 V on the end contacts, its via away from the GPS RF pad
PWR_A = [(p, 'GND') for p in PWR_A] + [(A(7), 'VCC_3V3'), (A(8), 'VCC_3V3'), (A(23), 'VCC5V0_SYS'), (A(24), 'VCC5V0_SYS')]
PWR_B = [B(1), B(3), B(7), B(10), B(13), B(14), B(15), B(16), B(17), B(18), B(19), B(20), B(23), B(24), ('J1002', 'MP')]   # audio only: former GPIO contacts 13-19 are GND
PWR_B = [(p, 'GND') for p in PWR_B] + [(B(11), 'VCC_3V3'), (B(12), 'VCC_3V3'), (B(21), 'VCC5V0_SYS'), (B(22), 'VCC5V0_SYS')]
for row_y, lst in ((132.08, PWR_A), (187.96, PWR_B)):
    for i, (jp, net) in enumerate(lst):
        x, y = 30.48 + i * 12.7, row_y
        conn(jp, x, y, up=True); wire((x, y), (x, y + 2.54))
        power(net, x, y + 2.54, 0 if net == 'GND' else 180)

for _r in ('J1001', 'J1002'):
    _u = sorted(int(m) for m in re.findall(r'\(reference "%s"\)\n\t+\(unit (\d+)\)' % _r, ''.join(syms)))
    assert _u == list(range(1, 26)), (_r, _u)
head = f'''(kicad_sch
	(version 20260101)
	(generator "eeschema")
	(generator_version "10.0")
	(uuid {SHEET_UUID})
	(paper "A4")
	(title_block
		(title "Expansion")
		(date "2026-11-24")
		(rev "1")
		(company "Teapot Laboratories")
		(comment 1 "FPC A = J1001 (under the GPS), FPC B = J1002 (under the microSD), bottom side")
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
