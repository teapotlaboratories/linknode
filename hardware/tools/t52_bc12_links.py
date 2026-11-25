"""T52 (owner, 2026-11-23): 0 ohm links R26 (D-) / R27 (D+), DNP by default, between the USB lines and the BQ25798's
D-/D+ pins (U2 pins 7/6), so the USB pair has no branch unless BC1.2 detection is wanted (Rockchip HDG V1.1 §3.2 item 24:
keep stubs as short as possible). Part: 0402 0 ohm, LCSC C17168 (already in the BOM).
Usage: python3 t52_bc12_links.py <kicad dir>
usb_and_charger.kicad_sch, minimal text edit: the two straight wires from the USB-line junctions to U2 pins 7/6 are cut
around each resistor; local labels CHG_DN / CHG_DP name the U2 side (labels name wires that already connect)."""
import sys, os, re, uuid
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schgen'))
import symlib
K = sys.argv[1]; P = os.path.join(K, 'usb_and_charger.kicad_sch'); s = open(P).read()
U = lambda: str(uuid.uuid4())
def g(v): return ('%.2f' % v).rstrip('0').rstrip('.')
PATH = '/d95cb237-0177-4440-a7e6-29dc79faada9/b9181568-4658-40dd-8a1e-e88baa671b8a'   # this sheet's instance path (as R25)
PINS = {p['num']: p for p in symlib.pins('Device:R_Small')}
def resistor(ref, x, y, fields_below):
    e1, e2 = symlib.endpoint((x, y), 90, PINS['1']), symlib.endpoint((x, y), 90, PINS['2'])
    ry, vy = (y + 1.6, y + 3.1) if fields_below else (y - 4.67, y - 3.02)
    blk = f'''	(symbol
		(lib_id "Device:R_Small")
		(at {g(x)} {g(y)} 90)
		(unit 1)
		(body_style 1)
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(in_pos_files yes)
		(dnp yes)
		(uuid "{U()}")
		(property "Reference" "{ref}"
			(at {g(x)} {g(ry)} 90)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.016 1.016)
				)
			)
		)
		(property "Value" "0R"
			(at {g(x)} {g(vy)} 90)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Footprint" "Resistor_SMD:R_0402_1005Metric"
			(at {g(x)} {g(y)} 0)
			(hide yes)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Datasheet" ""
			(at {g(x)} {g(y)} 0)
			(hide yes)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Description" "BC1.2 link to the charger, not fitted by default (T52)"
			(at {g(x)} {g(y)} 0)
			(hide yes)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "LCSC" "C17168"
			(at {g(x)} {g(y)} 0)
			(hide yes)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(pin "1"
			(uuid "{U()}")
		)
		(pin "2"
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
	)
'''
    return blk, (e1[0], e1[1]), (e2[0], e2[1])
def wire(a, c):
    return f'\n\t(wire\n\t\t(pts\n\t\t\t(xy {g(a[0])} {g(a[1])}) (xy {g(c[0])} {g(c[1])})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)'
def label(name, x, y):
    return (f'\n\t(label "{name}"\n\t\t(at {g(x)} {g(y)} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            f'\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')
def drop_wire(s, a, c):
    pat = re.compile(r'\n\t\(wire\n\t\t\(pts\n\t\t\t\(xy ' + re.escape(g(a[0])) + ' ' + re.escape(g(a[1])) + r'\) \(xy ' +
                     re.escape(g(c[0])) + ' ' + re.escape(g(c[1])) + r'\)\n\t\t\)\n\t\t\(stroke\n\t\t\t\(width 0\)\n\t\t\t\(type default\)\n\t\t\)\n\t\t\(uuid "[^"]+"\)\n\t\)')
    assert len(pat.findall(s)) == 1, (a, c)
    return pat.sub('', s)
assert '(reference "R26")' not in s and '(reference "R27")' not in s
add_w = ''; add_s = ''
for ref, x, y, left_end, below, lab in (('R26', 116.84, 88.9, 91.44, False, 'CHG_DN'), ('R27', 129.54, 91.44, 88.9, True, 'CHG_DP')):
    s = drop_wire(s, (left_end, y), (142.24, y))
    blk, e1, e2 = resistor(ref, x, y, below)
    lo, hi = sorted((e1, e2))
    add_s += blk
    add_w += wire((left_end, y), lo) + wire(hi, (142.24, y)) + label(lab, 133.35, y)
k = s.index('\n\t(wire'); s = s[:k] + add_w + s[k:]
k = s.index('\n\t(symbol\n') + 1; s = s[:k] + add_s + s[k:]
open(P, 'w').write(s); print('R26/R27 inserted (DNP), labels CHG_DN / CHG_DP')
