"""T50 (owner, 2026-11-23): codec pins to the expansion pads. soc_power.kicad_sch, U100 unit 6. Minimal text edit.
Usage: python3 t50_soc.py <kicad dir>
- R605 (FEPHY EXTR, + #PWR1127) and C637 (CODEC VCM, + #PWR1128) move right 17.78 mm (x 254 -> 271.78), their feed wires
  from pins 102 and 30 lengthen to match: they sat on the MIC0P and MICBIAS rows. Connections unchanged.
- Stubs + hierarchical labels (x 256.54) replace the no-connects on pins 34 MIC0P, 33 MIC0N, 36 MIC1P, 35 MIC1N,
  29 LINEOUT, 32 MICBIAS (HDG Table 2-12 p.31: MIC lines get 1 uF in series, which sit on the Expansion sheet)."""
import sys, os, re, uuid
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schgen'))
import symlib
K = sys.argv[1]; P = os.path.join(K, 'soc_power.kicad_sch'); s = open(P).read()
U = lambda: str(uuid.uuid4())
def g(v): return ('%.2f' % v).rstrip('0').rstrip('.')
def close(s, i):
    d = 0
    for j, ch in enumerate(s[i:]):
        if ch == '(': d += 1
        elif ch == ')':
            d -= 1
            if d == 0: return i + j + 1
def shift(s, ref, dx):
    i = s.index(f'(reference "{ref}")'); st = s.rindex('\n\t(symbol', 0, i) + 1; en = close(s, st); b = s[st:en]
    nb = re.sub(r'\(at ([\d.\-]+) ([\d.\-]+)', lambda m: f'(at {g(float(m.group(1)) + dx)} {m.group(2)}', b)
    return s[:st] + nb + s[en:]
DX = 17.78
for r in ('R605', '#PWR1127', 'C637', '#PWR1128'): s = shift(s, r, DX)
for y in ('86.36', '104.14'):
    pat = re.compile(r'\(xy 248\.92 ' + re.escape(y) + r'\) \(xy 254(?:\.0+)? ' + re.escape(y) + r'\)')
    assert len(pat.findall(s)) == 1, y
    s = pat.sub(f'(xy 248.92 {y}) (xy {g(254 + DX)} {y})', s)
PINS = {p['num']: p for p in symlib.pins('linknode:RV1106G3')}
u6 = [m for m in re.finditer(r'\(symbol\s+\(lib_id "linknode:RV1106G3"\)\s+\(at ([\d.\-]+) ([\d.\-]+) (\d+)\)(.*?)\(unit (\d+)\)', s, re.S) if m.group(5) == '6'][0]
UX, UY, UR = float(u6.group(1)), float(u6.group(2)), int(u6.group(3))
def stub(s, pin, name, shape, lx):
    x, y, a = symlib.endpoint((UX, UY), UR, PINS[pin])
    hits = [m for m in re.finditer(r'\n\t\(no_connect\n\t\t\(at ([\d.\-]+) ([\d.\-]+)\)\n\t\t\(uuid "[^"]+"\)\n\t\)', s)
            if abs(float(m.group(1)) - x) < 0.01 and abs(float(m.group(2)) - y) < 0.01]
    assert len(hits) == 1, (pin, x, y, len(hits))
    s = s[:hits[0].start()] + s[hits[0].end():]
    add = (f'\n\t(wire\n\t\t(pts\n\t\t\t(xy {g(x)} {g(y)}) (xy {g(lx)} {g(y)})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)'
           f'\n\t(hierarchical_label "{name}"\n\t\t(shape {shape})\n\t\t(at {g(lx)} {g(y)} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')
    k = s.index('\n\t(wire'); return s[:k] + add + s[k:]
for pin, name, shape in (('34', 'MIC0P', 'input'), ('33', 'MIC0N', 'input'), ('36', 'MIC1P', 'input'), ('35', 'MIC1N', 'input'),
                         ('29', 'LINEOUT', 'output'), ('32', 'MICBIAS', 'output')):
    s = stub(s, pin, name, shape, 256.54)
open(P, 'w').write(s); print('done: R605/C637 moved +17.78, 6 codec stubs')
