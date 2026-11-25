"""T42: add microSD ESD protection (2x TPD4E05U06DQAR, DOWO, LCSC C22390021) to microsd.kicad_sch by a minimal text edit.
Usage: python3 add_sd_esd.py <microsd.kicad_sch> <TPD4EUSB30 lib block file>
HDG §3.3.1 (p.46): TF-card ESD devices with junction capacitance < 1 pF, close to the connector.
DOWO datasheet (hardware/datasheets/DOWO_TPD4E05U06DQAR.pdf p.2): C(I/O-GND) 0.4 typ / 0.5 max pF, VRWM 5.0 V,
I/O pins 1, 2, 4, 5; GND 3, 8; pins 6, 7, 9, 10 not connected (same as TI TPD4E05U06 DQA, SLVSBO7O Table 4-2).
U401 (rot 0): CLK, CMD, D0, D1. U402 (rot 90): D2, D3, DET (socket side of R402); one channel spare (no-connect).
The seven SD hierarchical labels move from x 101.6 to 73.66 to make room; their nets do not change."""
import sys, re, uuid
P, LIB = sys.argv[1], sys.argv[2]
s = open(P).read()
U = lambda: str(uuid.uuid4())
ROOT = '/d95cb237-0177-4440-a7e6-29dc79faada9/48504eac-3d02-4d0d-9f40-71572c492bc9'
assert ROOT in s

# 1. move the hierarchical labels and their wire ends
for y in ('111.76', '114.3', '116.84', '119.38', '121.92', '124.46', '129.54'):
    n0 = s.count(f'(at 101.6 {y} 180)'); assert n0 == 1, (y, n0)
    s = s.replace(f'(at 101.6 {y} 180)', f'(at 73.66 {y} 180)')
    n1 = s.count(f'(xy 101.6 {y})'); assert n1 == 1, (y, n1)
    s = s.replace(f'(xy 101.6 {y})', f'(xy 73.66 {y})')

# 1b. R403 (10k DNP DET pull-down) + its GND move from x 109.22 to 91.44 on the same DET line (clear of the new taps)
import re as _re
def shift_block(s, marker, dx):
    i = s.index(marker); st = s.rindex('(symbol (lib_id', 0, i); d = 0
    for j, ch in enumerate(s[st:]):
        if ch == '(': d += 1
        elif ch == ')':
            d -= 1
            if d == 0: break
    blk = s[st:st + j + 1]
    nb = _re.sub(r'\(at ([\d.\-]+) ([\d.\-]+)', lambda m: '(at %s %s' % (('%.2f' % (float(m.group(1)) + dx)).rstrip('0').rstrip('.'), m.group(2)), blk)
    return s[:st] + nb + s[st + j + 1:]
s = shift_block(s, '(reference "R403")', -17.78)
s = shift_block(s, '(reference "#PWR1207")', -17.78)
assert s.count('(at 109.22 129.54)') == 1; s = s.replace('(at 109.22 129.54)', '(at 91.44 129.54)')

# 2. library symbol, flattened from Power_Protection:TPD4EUSB30 (TPD4E05U06DQA extends it)
lib = open(LIB).read().strip()
lib = lib.replace('(symbol "TPD4EUSB30"', '(symbol "Power_Protection:TPD4E05U06DQA"', 1)
lib = re.sub(r'\(symbol "TPD4EUSB30_(\d_\d)"', r'(symbol "TPD4E05U06DQA_\1"', lib)
lib = lib.replace('(property "Value" "TPD4EUSB30"', '(property "Value" "TPD4E05U06DQA"')
lib = lib.replace('"http://www.ti.com/lit/ds/symlink/tpd2eusb30a.pdf"', '"https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf"')
assert 'TPD4EUSB30' not in lib
i = s.index('(lib_symbols'); s = s[:i + len('(lib_symbols')] + '\n' + lib + s[i + len('(lib_symbols'):]

# 3. instances
def esd(ref, x, y, rot, refat, valat, fang=0):
    pins = ''.join(f'\n    (pin "{n}" (uuid "{U()}"))' for n in range(1, 11))
    desc = ('4-channel ESD array for the microSD lines (HDG §3.3.1: < 1 pF at the connector). DOWO TPD4E05U06DQAR: '
            'C(I/O-GND) 0.5 pF max, VRWM 5.0 V (datasheet p.2); pin-compatible with TI TPD4E05U06 DQA.')
    return f'''
  (symbol (lib_id "Power_Protection:TPD4E05U06DQA") (at {x} {y} {rot}) (unit 1)
    (body_style 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (in_pos_files yes) (dnp no)
    (uuid "{U()}")
    (property "Reference" "{ref}"
      (at {refat[0]} {refat[1]} {fang})
      (show_name no)
      (do_not_autoplace no)
      (effects (font (size 1.27 1.27)) (justify {refat[2]}))
    )
    (property "Value" "TPD4E05U06DQAR"
      (at {valat[0]} {valat[1]} {fang})
      (show_name no)
      (do_not_autoplace no)
      (effects (font (size 1.27 1.27)) (justify {valat[2]}))
    )
    (property "Footprint" "Package_SON:USON-10_2.5x1.0mm_P0.5mm"
      (at {x} {y} 0)
      (hide yes)
      (show_name no)
      (do_not_autoplace no)
      (effects (font (size 1.27 1.27)))
    )
    (property "Datasheet" "hardware/datasheets/DOWO_TPD4E05U06DQAR.pdf"
      (at {x} {y} 0)
      (hide yes)
      (show_name no)
      (do_not_autoplace no)
      (effects (font (size 1.27 1.27)))
    )
    (property "Description" "{desc}"
      (at {x} {y} 0)
      (hide yes)
      (show_name no)
      (do_not_autoplace no)
      (effects (font (size 1.27 1.27)))
    )
    (property "LCSC" "C22390021" (at {x} {y} 0)
      (effects (font (size 1.27 1.27)) (hide yes))
    ){pins}
    (instances
      (project "linknode"
        (path "{ROOT}"
          (reference "{ref}")
          (unit 1)
        )
      )
    )
  )'''
def gnd(ref, x, y):
    return f'''
  (symbol (lib_id "power:GND") (at {x} {y} 0) (unit 1)
    (body_style 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (in_pos_files yes) (dnp no)
    (uuid "{U()}")
    (property "Reference" "{ref}"
      (at {x} {y + 6.35} 0)
      (hide yes)
      (show_name no)
      (do_not_autoplace no)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "GND"
      (at {x} {y + 3.81} 0)
      (show_name no)
      (do_not_autoplace no)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {x} {y} 0) (hide yes) (show_name no) (do_not_autoplace no) (effects (font (size 1.27 1.27))))
    (property "Datasheet" "" (at {x} {y} 0) (hide yes) (show_name no) (do_not_autoplace no) (effects (font (size 1.27 1.27))))
    (property "Description" "" (at {x} {y} 0) (hide yes) (show_name no) (do_not_autoplace no) (effects (font (size 1.27 1.27))))
    (pin "1" (uuid "{U()}"))
    (instances
      (project "linknode"
        (path "{ROOT}"
          (reference "{ref}")
          (unit 1)
        )
      )
    )
  )'''
syms = (esd('U401', 96.52, 149.86, 0, (96.52, 140.97, 'left'), (99.06, 167.64, 'left'))
        + esd('U402', 125.73, 149.86, 90, (135.89, 146.05, 'right'), (135.89, 156.21, 'right'), fang=90)  # 90 on a 90-deg symbol renders at 180: 'right' runs away from the body
        + gnd('#PWR1210', 96.52, 162.56) + gnd('#PWR1211', 140.97, 149.86))

# 4. wires, junctions, no-connects
W = [[(76.2, 111.76), (76.2, 152.4), (83.82, 152.4)],         # CLK  -> U401 D1-
     [(78.74, 114.3), (78.74, 147.32), (83.82, 147.32)],       # CMD  -> U401 D1+
     [(114.3, 116.84), (114.3, 152.4), (109.22, 152.4)],       # D0   -> U401 D2-
     [(111.76, 119.38), (111.76, 147.32), (109.22, 147.32)],   # D1   -> U401 D2+
     [(115.57, 121.92), (115.57, 165.1), (123.19, 165.1), (123.19, 162.56)],  # D2 -> U402 D1+
     [(128.27, 124.46), (128.27, 137.16)],                     # D3   -> U402 D2-
     [(123.19, 129.54), (123.19, 137.16)],                     # DET  -> U402 D2+ (socket side of R402)
     [(138.43, 149.86), (140.97, 149.86)]]                     # U402 GND
J = [(76.2, 111.76), (78.74, 114.3), (114.3, 116.84), (111.76, 119.38), (115.57, 121.92), (128.27, 124.46), (123.19, 129.54)]
NC = [(83.82, 142.24), (83.82, 157.48), (109.22, 142.24), (109.22, 157.48),
      (118.11, 137.16), (133.35, 137.16), (118.11, 162.56), (133.35, 162.56), (128.27, 162.56)]
def g(v): return ('%.2f' % v).rstrip('0').rstrip('.')
items = ''
for w in W:
    for a, b in zip(w, w[1:]):
        items += f'\n\t(wire\n\t\t(pts\n\t\t\t(xy {g(a[0])} {g(a[1])}) (xy {g(b[0])} {g(b[1])})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)'
for x, y in J:
    items += f'\n\t(junction\n\t\t(at {g(x)} {g(y)})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{U()}")\n\t)'
for x, y in NC:
    items += f'\n\t(no_connect\n\t\t(at {g(x)} {g(y)})\n\t\t(uuid "{U()}")\n\t)'
k = s.index('\n\t(junction'); s = s[:k] + items + s[k:]
k = s.index('(sheet_instances') if '(sheet_instances' in s else s.rstrip().rindex(')')
k = s.rindex('\n', 0, k)
s = s[:k] + syms + s[k:]
open(P, 'w').write(s)
print('ok: 2 ESD, 2 GND, %d wire segments, %d junctions, %d no-connects' % (sum(len(w) - 1 for w in W), len(J), len(NC)))
