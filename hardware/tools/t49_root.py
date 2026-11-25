"""T49 root sheet: add the Expansion sheet and re-wire the moved enables. Minimal text edit; no crossing wires.
Usage: python3 t49_root.py <kicad dir> <expansion sheet uuid>
Layout (mm):
  SoC box extended to y 139.7 (17 new bottom-edge pins x 104.14..144.78; their text clears the side-pin text)
  Expansion (101.6, 147.32) 63.5 x 20.32: 17 top pins (straight wires up to SoC), ETH x4 on its right edge
  SoC Power (175.26, 147.32) 45.72 x 15.24: ETH x4 on its left edge (straight wires), GPS_PWR_EN left edge y 160.02,
            C5_PWR_EN right edge y 149.86
  GPS_PWR_EN: GPS pin moves to the GPS bottom edge (66.04, 121.92); wire runs below Expansion (y 172.72)
  C5_PWR_EN: Radio Power pin moves to its right edge (236.22, 71.12); wire runs up the right margin (x 246.38)
  Antenna (1 pin) moves to the top-right corner (243.84, 22.86) 38.1 x 12.7, so the HaLow-Antenna wire is short and no
            longer fences in the right margin. Power and Hold-off (no pins) move to the bottom row (y 177.8)."""
import sys, re, uuid
K, SU = sys.argv[1], sys.argv[2]
P = K + '/linknode.kicad_sch'; s = open(P).read()
U = lambda: str(uuid.uuid4())
def g(v): return ('%.2f' % v).rstrip('0').rstrip('.')
def close(s, i):
    d = 0
    for j, ch in enumerate(s[i:]):
        if ch == '(': d += 1
        elif ch == ')':
            d -= 1
            if d == 0: return i + j + 1
def sheet_span(s, name):
    i = s.index(f'(property "Sheetname" "{name}"'); st = s.rindex('\n\t(sheet\n', 0, i) + 1; return st, close(s, st)
JUST = {0: 'right', 180: 'left', 90: 'right', 270: 'left'}
def pin_txt(name, typ, x, y, rot):
    return (f'\n\t\t(pin "{name}" {typ}\n\t\t\t(at {g(x)} {g(y)} {rot})\n\t\t\t(uuid "{U()}")\n\t\t\t(effects\n\t\t\t\t(font\n'
            f'\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify {JUST[rot]})\n\t\t\t)\n\t\t)')
def edit_sheet(s, name, at=None, size=None, remove=(), move=None, add=()):
    st, en = sheet_span(s, name); b = s[st:en]
    if at:
        b = re.sub(r'\(at [\d.\-]+ [\d.\-]+\)\n\t\t\(size [\d.\-]+ [\d.\-]+\)', f'(at {g(at[0])} {g(at[1])})\n\t\t(size {g(size[0])} {g(size[1])})', b, 1)
        b = re.sub(r'(\(property "Sheetname" "[^"]+"\n\t\t\t)\(at [\d.\-]+ [\d.\-]+ 0\)', lambda m: m.group(1) + f'(at {g(at[0] + 2.54)} {g(at[1] - 1.27)} 0)', b, 1)
        b = re.sub(r'(\(property "Sheetfile" "[^"]+"\n\t\t\t)\(at [\d.\-]+ [\d.\-]+ 0\)', lambda m: m.group(1) + f'(at {g(at[0] + 2.54)} {g(at[1] + size[1] + 1.27)} 0)', b, 1)
    for pn in remove:
        i = b.index(f'(pin "{pn}" '); st2 = b.rindex('\n', 0, i); b = b[:st2] + b[close(b, i):]
    for pn, (x, y, rot) in (move or {}).items():
        i = b.index(f'(pin "{pn}" '); e = close(b, i); blk = b[i:e]
        blk = re.sub(r'\(at [\d.\-]+ [\d.\-]+ \d+\)', f'(at {g(x)} {g(y)} {rot})', blk, 1)
        blk = re.sub(r'\(justify \w+\)', f'(justify {JUST[rot]})', blk, 1)
        b = b[:i] + blk + b[e:]
    if add:
        k = b.rstrip().rindex(')'); b = b[:k].rstrip('\n\t') + ''.join(pin_txt(*a) for a in add) + '\n\t)'
    return s[:st] + b + s[en:]
def wire_txt(a, c):
    return f'\n\t(wire\n\t\t(pts\n\t\t\t(xy {g(a[0])} {g(a[1])}) (xy {g(c[0])} {g(c[1])})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)'
def wires(s):
    for m in re.finditer(r'\n\t\(wire\n\t\t\(pts\n\t\t\t\(xy ([\d.\-]+) ([\d.\-]+)\) \(xy ([\d.\-]+) ([\d.\-]+)\)\n\t\t\)(?:.|\n)*?\(uuid "[^"]+"\)\n\t\)', s):
        yield m, (float(m.group(1)), float(m.group(2))), (float(m.group(3)), float(m.group(4)))
def drop_wires(s, pred):
    n = 0
    for m, a, c in sorted(wires(s), key=lambda t: -t[0].start()):
        if pred(a, c): s = s[:m.start()] + s[m.end():]; n += 1
    return s, n

NETS = ['I2C2_SDA', 'I2C2_SCL', 'I2C0_SDA', 'I2C0_SCL', 'SPI0_CS0', 'SPI0_CLK', 'SPI0_MOSI', 'SPI0_MISO', 'EXP_GPIO1_B1', 'EXP_GPIO1_C7',
        'EXP_GPIO0_A4', 'EXP_GPIO0_A3', 'EXP_GPIO4_A6', 'EXP_GPIO4_A4', 'EXP_GPIO4_A3', 'EXP_GPIO4_A2', 'EXP_GPIO4_B0']
TYP = {'SPI0_CS0': 'output', 'SPI0_CLK': 'output', 'SPI0_MOSI': 'output', 'SPI0_MISO': 'input'}
XS = [104.14 + 2.54 * i for i in range(17)]
ETH = [('ETH_TXP', 'output', 149.86), ('ETH_TXN', 'output', 152.4), ('ETH_RXP', 'input', 154.94), ('ETH_RXN', 'input', 157.48)]

# --- wires out: GPS_PWR_EN (GPS-SoC), C5_PWR_EN (SoC-Radio Power), HALOW_ANT chain (all points x >= 236.22)
s, n1 = drop_wires(s, lambda a, c: {a, c} == {(71.12, 106.68), (101.6, 106.68)})
s, n2 = drop_wires(s, lambda a, c: {a, c} == {(152.4, 71.12), (190.5, 71.12)})
s, n3 = drop_wires(s, lambda a, c: min(a[0], c[0]) >= 236.2 and max(a[0], c[0]) > 236.3 or (a[0] > 236.3 and c[0] > 236.3))
assert (n1, n2) == (1, 1) and n3 >= 2, (n1, n2, n3)

# --- sheets
s = edit_sheet(s, 'SoC', at=(101.6, 22.86), size=(50.8, 116.84), remove=('GPS_PWR_EN', 'C5_PWR_EN'),
               add=[(n, TYP.get(n, 'bidirectional'), x, 139.7, 270) for n, x in zip(NETS, XS)])
s = edit_sheet(s, 'GPS', move={'GPS_PWR_EN': (66.04, 121.92, 270)})
s = edit_sheet(s, 'Radio Power', move={'C5_PWR_EN': (236.22, 71.12, 0)})
s = edit_sheet(s, 'Antenna', at=(243.84, 22.86), size=(38.1, 12.7), move={'HALOW_ANT': (243.84, 27.94, 180)})
s = edit_sheet(s, 'Power', at=(25.4, 177.8), size=(45.72, 10.16))
s = edit_sheet(s, 'Hold-off', at=(76.2, 177.8), size=(45.72, 10.16))
s = edit_sheet(s, 'SoC Power', at=(175.26, 147.32), size=(45.72, 15.24),
               add=[(n, t, 175.26, y, 180) for n, t, y in ETH] + [('GPS_PWR_EN', 'output', 175.26, 160.02, 180), ('C5_PWR_EN', 'output', 220.98, 149.86, 0)])
# --- new Expansion sheet block (copied format of the existing blocks)
exp_pins = ''.join(pin_txt(n, TYP.get(n, 'bidirectional'), x, 147.32, 90) for n, x in zip(NETS, XS)) + ''.join(pin_txt(n, t, 165.1, y, 0) for n, t, y in ETH)
blk = f'''
	(sheet
		(at 101.6 147.32)
		(size 63.5 20.32)
		(fields_autoplaced no)
		(stroke
			(width 0.0006)
			(type default)
		)
		(fill
			(color 0 0 0 0.0)
		)
		(uuid "{SU}")
		(property "Sheetname" "Expansion"
			(at 147.32 146.05 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left bottom)
			)
		)
		(property "Sheetfile" "expansion.kicad_sch"
			(at 104.14 168.91 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left top)
			)
		)
		(instances
			(project "linknode"
				(path "/d95cb237-0177-4440-a7e6-29dc79faada9"
					(page "14")
				)
			)
		)''' + exp_pins + '\n\t)'
k = s.index('\n\t(sheet\n'); s = s[:k] + blk + s[k:]
# --- wires in
W = [((x, 139.7), (x, 147.32)) for x in XS]
W += [((165.1, y), (175.26, y)) for _, _, y in ETH]
W += [((66.04, 121.92), (66.04, 172.72)), ((66.04, 172.72), (170.18, 172.72)), ((170.18, 172.72), (170.18, 160.02)), ((170.18, 160.02), (175.26, 160.02))]
W += [((220.98, 149.86), (246.38, 149.86)), ((246.38, 149.86), (246.38, 71.12)), ((246.38, 71.12), (236.22, 71.12))]
W += [((236.22, 27.94), (243.84, 27.94))]
k = s.index('\n\t(wire'); s = s[:k] + ''.join(wire_txt(a, c) for a, c in W) + s[k:]
open(P, 'w').write(s)
print('root: removed wires', n1, n2, n3, '| added', len(W), '| Expansion sheet + 21 pins; SoC +17 -2; SoC Power +6; moved GPS, Radio Power, Antenna pins')
