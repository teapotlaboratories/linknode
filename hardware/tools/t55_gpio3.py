"""T55 (owner, 2026-11-24: "Switch to 1.8 V west pins"): FPC B's GPIOs move from the 3.3 V south pins (GPIO4_A6/A4/A3/A2/B0 on
39/41/42/44/47, GPIO0_A3/A4 on 62/63), which are boxed in by the microSD bus and the ESP32-C5 SPI, to the free 1.8 V VCCIO7 pins on the
west edge. GPS_PWR_EN moves from pin 4 to pin 2 (same 1.8 V group and reset pull-down), so the six GPIOs sit on contiguous pins 4-9
and don't cross the two enables. Minimal text edits.
Usage: python3 t55_gpio3.py <kicad dir>
soc.kicad_sch:       pins 39/41/42/44/47/62/63: wire + hierarchical label removed, no-connect back on the pin end
soc_power.kicad_sch: pin 4 label GPS_PWR_EN -> EXP_GPIO3_C6; pin 2 new stub GPS_PWR_EN; pins 5-9 new stubs EXP_GPIO3_C7/D1/D0/D2/D3
linknode.kicad_sch:  the 7 old sheet pins on SoC and Expansion and their wires removed; Expansion's top edge 2.54 mm higher and its
                     10 top pins (+ SoC bottom pins, wires) 17.78 mm right; 6 new pins SoC Power right edge -> Expansion left edge."""
import sys, os, re, uuid
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schgen'))
import symlib
K = sys.argv[1]
U = lambda: str(uuid.uuid4())
def g(v): return ('%.2f' % v).rstrip('0').rstrip('.')
def close(s, i):
    d = 0
    for j, ch in enumerate(s[i:]):
        if ch == '(': d += 1
        elif ch == ')':
            d -= 1
            if d == 0: return i + j + 1
PINS = {p['num']: p for p in symlib.pins('linknode:RV1106G3')}
def end(s, pin):
    for m in re.finditer(r'\(symbol\s+\(lib_id "linknode:RV1106G3"\)\s+\(at ([\d.\-]+) ([\d.\-]+) (\d+)\)(.*?)\(unit (\d+)\)', s, re.S):
        if int(m.group(5)) == PINS[pin]['unit']:
            return symlib.endpoint((float(m.group(1)), float(m.group(2))), int(m.group(3)), PINS[pin])[:2]
    raise SystemExit('unit not on sheet: ' + pin)
def near(a, b): return abs(a - b) < 0.01
def block(s, i):   # the top-level (...) item that starts at the line containing index i
    st = s.rindex('\n\t(', 0, i + 3) + 1; return st, close(s, st)
def unstub(s, pin, name):
    x, y = end(s, pin)
    m = re.search(r'\n\t\(hierarchical_label "' + re.escape(name) + r'"', s); assert m, name
    st, en = block(s, m.start() + 1); lab = s[st:en]
    lx, ly = map(float, re.search(r'\(at ([\d.\-]+) ([\d.\-]+)', lab).groups())
    wires = [w for w in re.finditer(r'\n\t\(wire\s+\(pts\s+\(xy ([\d.\-]+) ([\d.\-]+)\) \(xy ([\d.\-]+) ([\d.\-]+)\)', s)
             if {(round(float(w.group(1)), 2), round(float(w.group(2)), 2)), (round(float(w.group(3)), 2), round(float(w.group(4)), 2))}
             == {(round(x, 2), round(y, 2)), (round(lx, 2), round(ly, 2))}]
    assert len(wires) == 1, (pin, name, len(wires))
    ws, we = block(s, wires[0].start() + 1)
    for a, b in sorted([(st, en), (ws, we)], reverse=True): s = s[:a - 1] + s[b:]
    nc = f'\n\t(no_connect\n\t\t(at {g(x)} {g(y)})\n\t\t(uuid "{U()}")\n\t)'
    k = s.index('\n\t(wire'); return s[:k] + nc + s[k:]
def stub(s, pin, name, shape, lx):
    x, y = end(s, pin)
    hits = [m for m in re.finditer(r'\n\t\(no_connect\n\t\t\(at ([\d.\-]+) ([\d.\-]+)\)\n\t\t\(uuid "[^"]+"\)\n\t\)', s)
            if near(float(m.group(1)), x) and near(float(m.group(2)), y)]
    assert len(hits) == 1, (pin, x, y, len(hits))
    s = s[:hits[0].start()] + s[hits[0].end():]
    rot = 180 if lx < x else 0; just = 'right' if rot == 180 else 'left'
    add = (f'\n\t(wire\n\t\t(pts\n\t\t\t(xy {g(x)} {g(y)}) (xy {g(lx)} {g(y)})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)'
           f'\n\t(hierarchical_label "{name}"\n\t\t(shape {shape})\n\t\t(at {g(lx)} {g(y)} {rot})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{U()}")\n\t)')
    k = s.index('\n\t(wire'); return s[:k] + add + s[k:]
OLD = [('39', 'EXP_GPIO4_A6'), ('41', 'EXP_GPIO4_A4'), ('42', 'EXP_GPIO4_A3'), ('44', 'EXP_GPIO4_A2'), ('47', 'EXP_GPIO4_B0'),
       ('62', 'EXP_GPIO0_A3'), ('63', 'EXP_GPIO0_A4')]
NEW = [('4', 'EXP_GPIO3_C6'), ('5', 'EXP_GPIO3_C7'), ('6', 'EXP_GPIO3_D1'), ('7', 'EXP_GPIO3_D0'), ('8', 'EXP_GPIO3_D2'), ('9', 'EXP_GPIO3_D3')]

p = os.path.join(K, 'soc.kicad_sch'); s = open(p).read()
for pin, name in OLD: s = unstub(s, pin, name)
open(p, 'w').write(s)

p = os.path.join(K, 'soc_power.kicad_sch'); s = open(p).read()
pat = re.compile(r'\(hierarchical_label "GPS_PWR_EN"\s+\(shape \w+\)'); assert len(pat.findall(s)) == 1
s = pat.sub('(hierarchical_label "EXP_GPIO3_C6"\n\t\t(shape bidirectional)', s)
s = stub(s, '2', 'GPS_PWR_EN', 'output', 182.88)
for pin, name in NEW[1:]: s = stub(s, pin, name, 'bidirectional', 182.88)
open(p, 'w').write(s)

p = os.path.join(K, 'linknode.kicad_sch'); s = open(p).read()
def sheet_span(s, name):
    i = s.index(f'(property "Sheetname" "{name}"'); st = s.rindex('\n\t(sheet\n', 0, i) + 1; return st, close(s, st)
def drop_pin(s, sheet, name):
    st, en = sheet_span(s, sheet); blk = s[st:en]
    m = re.search(r'\n\t\t\(pin "' + re.escape(name) + r'" \w+', blk); assert m, (sheet, name)
    b = close(blk, m.start() + 3)                       # m starts at '\n\t\t(pin'
    return s[:st] + blk[:m.start()] + blk[b:] + s[en:]
for _, name in OLD:
    st, en = sheet_span(s, 'SoC'); x = float(re.search(r'\(pin "' + name + r'" \w+\s+\(at ([\d.]+) ', s[st:en]).group(1))
    s = drop_pin(s, 'SoC', name); s = drop_pin(s, 'Expansion', name)
    w = [m for m in re.finditer(r'\n\t\(wire\s+\(pts\s+\(xy ([\d.]+) 139\.7\) \(xy ([\d.]+) 147\.32\)', s)
         if near(float(m.group(1)), x) and near(float(m.group(2)), x)]
    assert len(w) == 1, (name, x); ws, we = block(s, w[0].start() + 1); s = s[:ws - 1] + s[we:]
# Expansion's top edge moves up 2.54 (six free left-edge slots at 147.32..160.02); its 10 remaining top pins, the matching SoC
# bottom pins and their wires move 17.78 right into the freed slots, so their vertical text clears the new left-edge pin text
st, en = sheet_span(s, 'Expansion'); blk = s[st:en]
nb = re.sub(r'\(at 101\.6 147\.32\)(\s+\(size 63\.5 )40\.64\)', r'(at 101.6 144.78)\g<1>43.18)', blk, count=1); assert nb != blk
nb2 = re.sub(r'(\(property "Sheetname" "Expansion"\s+\(at 147\.32 )146\.05', r'\g<1>143.51', nb, count=1); assert nb2 != nb
s = s[:st] + nb2 + s[en:]
KEEP = ['I2C2_SDA', 'I2C2_SCL', 'I2C0_SDA', 'I2C0_SCL', 'SPI0_CS0', 'SPI0_CLK', 'SPI0_MOSI', 'SPI0_MISO', 'EXP_GPIO1_B1', 'EXP_GPIO1_C7']
for name in KEEP:
    for sheet in ('SoC', 'Expansion'):
        st, en = sheet_span(s, sheet); blk = s[st:en]
        m = re.search(r'(\(pin "' + re.escape(name) + r'" \w+\s+\(at )([\d.]+) ([\d.]+)', blk); assert m, (sheet, name)
        x, y = float(m.group(2)), float(m.group(3)); ny = 144.78 if sheet == 'Expansion' else y
        blk = blk[:m.start()] + m.group(1) + f'{g(x + 17.78)} {g(ny)}' + blk[m.end():]
        s = s[:st] + blk + s[en:]
    w = re.compile(r'\(xy ' + re.escape(g(x)) + r' 139\.7\) \(xy ' + re.escape(g(x)) + r' 147\.32\)'); assert len(w.findall(s)) == 1, name
    s = w.sub(f'(xy {g(x + 17.78)} 139.7) (xy {g(x + 17.78)} 144.78)', s)
def pin_txt(name, x, y, rot):
    just = 'right' if rot == 0 else 'left'
    return (f'\n\t\t(pin "{name}" bidirectional\n\t\t\t(at {g(x)} {g(y)} {rot})\n\t\t\t(uuid "{U()}")\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify {just})\n\t\t\t)\n\t\t)')
YS = [147.32, 149.86, 152.4, 154.94, 157.48, 160.02]
for sheet, x, rot in (('SoC Power', 71.12, 0), ('Expansion', 101.6, 180)):
    st, en = sheet_span(s, sheet); blk = s[st:en]
    k = blk.index('\n\t\t(pin '); blk = blk[:k] + ''.join(pin_txt(n, x, y, rot) for (_, n), y in zip(NEW, YS)) + blk[k:]
    s = s[:st] + blk + s[en:]
add = ''.join(f'\n\t(wire\n\t\t(pts\n\t\t\t(xy 71.12 {g(y)}) (xy 101.6 {g(y)})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)' for y in YS)
k = s.index('\n\t(wire'); s = s[:k] + add + s[k:]
open(p, 'w').write(s)
print('soc: 7 stubs removed; soc_power: 1 rename + 6 stubs; root: 7 pins x2 + 7 wires removed, Expansion top up 2.54, 10 pins x2 + wires 17.78 right, 6 pins x2 + 6 wires added')
