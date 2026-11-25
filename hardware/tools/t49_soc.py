"""T49 (owner, 2026-11-23): RV1106 pin changes for the expansion pogo pads (proposal v2). Minimal text edits.
Usage: python3 t49_soc.py <kicad dir>
soc.kicad_sch:
  - renames (label already wired to the pin): pin 72 HALOW_FEM_EN -> I2C2_SCL, pin 73 GPS_PWR_EN -> I2C2_SDA,
    pin 75 C5_PWR_EN -> I2C0_SCL (all bidirectional)
  - new stubs replacing the no-connect: 58 HALOW_FEM_EN (3.3 V, resets Hi-Z, R122 100k holds it low), 62/63 GPIO0_A3/A4,
    76 I2C0_SDA, 78 GPIO1_B1, 84 GPIO1_C7, 92-95 SPI0, 39/41/42/44/47 GPIO4 (eMMC/FSPI pins)
soc_power.kicad_sch (U100 unit 6):
  - 97-100 FEPHY -> ETH_RXN/RXP/TXP/TXN; pin 3 (GPIO3_C5, 1.8 V) C5_PWR_EN; pin 4 (GPIO3_C6, 1.8 V) GPS_PWR_EN
  - R605 Reference/Value moved below the ETH rows
Pin ends come from the symbol (hardware/tools/schgen/symlib.py), and each must carry a no-connect (or the renamed label's wire)."""
import sys, os, re, uuid
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schgen'))
import symlib
K = sys.argv[1]
U = lambda: str(uuid.uuid4())
def g(v): return ('%.2f' % v).rstrip('0').rstrip('.')
PINS = {p['num']: p for p in symlib.pins('linknode:RV1106G3')}
def units(s):
    out = {}
    for m in re.finditer(r'\(symbol\s+\(lib_id "linknode:RV1106G3"\)\s+\(at ([\d.\-]+) ([\d.\-]+) (\d+)\)(.*?)\(unit (\d+)\)', s, re.S):
        out[int(m.group(5))] = (float(m.group(1)), float(m.group(2)), int(m.group(3)))
    return out
def end(s, pin):
    u = units(s)[PINS[pin]['unit']]; x, y, a = symlib.endpoint((u[0], u[1]), u[2], PINS[pin]); return x, y, a
def rename(s, old, new, shape='bidirectional'):
    pat = re.compile(r'\(hierarchical_label "' + re.escape(old) + r'"\s+\(shape \w+\)')
    assert len(pat.findall(s)) == 1, old
    return pat.sub(f'(hierarchical_label "{new}"\n\t\t(shape {shape})', s)
def stub(s, pin, name, shape, lx):
    x, y, a = end(s, pin)
    hits = [m for m in re.finditer(r'\n\t\(no_connect\n\t\t\(at ([\d.\-]+) ([\d.\-]+)\)\n\t\t\(uuid "[^"]+"\)\n\t\)', s)
            if abs(float(m.group(1)) - x) < 0.01 and abs(float(m.group(2)) - y) < 0.01]   # coordinates carry float noise
    assert len(hits) == 1, (pin, x, y, len(hits))
    s = s[:hits[0].start()] + s[hits[0].end():]
    rot = 180 if lx < x else 0; just = 'right' if rot == 180 else 'left'
    add = (f'\n\t(wire\n\t\t(pts\n\t\t\t(xy {g(x)} {g(y)}) (xy {g(lx)} {g(y)})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)'
           f'\n\t(hierarchical_label "{name}"\n\t\t(shape {shape})\n\t\t(at {g(lx)} {g(y)} {rot})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{U()}")\n\t)')
    k = s.index('\n\t(wire'); return s[:k] + add + s[k:]

p = os.path.join(K, 'soc.kicad_sch'); s = open(p).read()
s = rename(s, 'HALOW_FEM_EN', 'I2C2_SCL'); s = rename(s, 'GPS_PWR_EN', 'I2C2_SDA'); s = rename(s, 'C5_PWR_EN', 'I2C0_SCL')
for pin, name, shape, lx in (('58', 'HALOW_FEM_EN', 'output', 144.78), ('62', 'EXP_GPIO0_A3', 'bidirectional', 144.78), ('63', 'EXP_GPIO0_A4', 'bidirectional', 144.78),
                             ('76', 'I2C0_SDA', 'bidirectional', 35.56), ('78', 'EXP_GPIO1_B1', 'bidirectional', 35.56),
                             ('95', 'SPI0_CS0', 'output', 132.08), ('94', 'SPI0_CLK', 'output', 132.08), ('93', 'SPI0_MOSI', 'output', 132.08), ('92', 'SPI0_MISO', 'input', 132.08),
                             ('84', 'EXP_GPIO1_C7', 'bidirectional', 132.08),
                             ('44', 'EXP_GPIO4_A2', 'bidirectional', 266.7), ('42', 'EXP_GPIO4_A3', 'bidirectional', 266.7), ('41', 'EXP_GPIO4_A4', 'bidirectional', 266.7),
                             ('39', 'EXP_GPIO4_A6', 'bidirectional', 266.7), ('47', 'EXP_GPIO4_B0', 'bidirectional', 266.7)):
    s = stub(s, pin, name, shape, lx)
open(p, 'w').write(s)

p = os.path.join(K, 'soc_power.kicad_sch'); s = open(p).read()
for pin, name, shape, lx in (('98', 'ETH_RXP', 'input', 259.08), ('97', 'ETH_RXN', 'input', 259.08), ('100', 'ETH_TXP', 'output', 259.08), ('99', 'ETH_TXN', 'output', 259.08),
                             ('3', 'C5_PWR_EN', 'output', 182.88), ('4', 'GPS_PWR_EN', 'output', 182.88)):
    s = stub(s, pin, name, shape, lx)
i = s.index('(reference "R605")'); st = s.rindex('\n\t(symbol', 0, i); blk = s[st:i]
nb = blk.replace('(at 255.76 80.39 0)', '(at 255.78 88.27 0)', 1).replace('(at 255.76 82.17 0)', '(at 255.78 90.17 0)', 1)
assert nb != blk; s = s[:st] + nb + s[i:]
open(p, 'w').write(s)
print('done: soc 3 renames + 15 stubs; soc_power 6 stubs + R605 fields')
