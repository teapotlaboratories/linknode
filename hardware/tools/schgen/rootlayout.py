"""Re-lay the root sheet: set each sheet's (at)/(size), move its Sheetname/Sheetfile fields, and place its existing
sheet pins at planned positions. Minimal text edit (the KiCad scripting server has no tool to move or resize a sheet).
Usage: rootlayout.py root.kicad_sch"""
import re, sys
p = sys.argv[1]; s = open(p).read()
SIDE = {0: 'right', 180: 'left', 90: 'right', 270: 'left'}   # keeps the pin text inside the box (checked in render)   # text justify per pin orientation (as KiCad writes them)
PLAN = {
 'USB and Charger': ((25.4, 22.86), (45.72, 22.86), {'USB_DP': (71.12, 27.94, 0), 'USB_DM': (71.12, 30.48, 0), 'I2C_SCL': (71.12, 33.02, 0),
                     'I2C_SDA': (71.12, 35.56, 0), 'CHG_INT': (71.12, 38.1, 0), 'TS': (48.26, 45.72, 270),
                     'SDRV': (58.42, 45.72, 270)}),
 'Battery':         ((25.4, 53.34), (45.72, 10.16), {'TS': (48.26, 53.34, 90), 'SDRV': (58.42, 53.34, 90)}),
 'microSD':         ((25.4, 71.12), (45.72, 25.4), {}),
 'GPS':             ((25.4, 104.14), (45.72, 17.78), {'GPS_PWR_EN': (71.12, 106.68, 0), 'GPS_TXD': (71.12, 109.22, 0),
                     'GPS_RXD': (71.12, 111.76, 0), 'GPS_PPS': (71.12, 114.3, 0)}),
 'SoC':             ((101.6, 22.86), (50.8, 101.6), {}),
 'HaLow':           ((190.5, 22.86), (45.72, 30.48), {}),
 'Radio Power':     ((190.5, 60.96), (45.72, 15.24), {'HALOW_PWR_EN': (190.5, 66.04, 180), 'HALOW_FEM_EN': (190.5, 68.58, 180),
                     'C5_PWR_EN': (190.5, 71.12, 180)}),
 'ESP32-C5':        ((190.5, 86.36), (45.72, 33.02), {}),
 'Antenna':         ((190.5, 127.0), (45.72, 12.7), {}),
 'Power':           ((25.4, 137.16), (45.72, 17.78), {}),
 'Hold-off':        ((76.2, 137.16), (45.72, 17.78), {}),
 'SoC Power':       ((127.0, 137.16), (45.72, 17.78), {}),
}
def blocks(s):
    out = []; i = 0
    while True:
        m = re.search(r'\(sheet\s', s[i:])
        if not m: break
        a = i + m.start(); d = 0
        for j in range(a, len(s)):
            if s[j] == '(': d += 1
            elif s[j] == ')':
                d -= 1
                if d == 0: break
        out.append((a, j + 1)); i = j + 1
    return out
f = lambda v: ('%.2f' % v).rstrip('0').rstrip('.')
done = set()
for a, b in reversed(blocks(s)):
    blk = s[a:b]
    name = re.search(r'"Sheetname" "([^"]*)"', blk)[1]
    if name not in PLAN: print('not in plan:', name); continue
    (x, y), (w, h), pins = PLAN[name]
    blk = re.sub(r'\(at [\d.\-]+ [\d.\-]+\)(\s*)\(size [\d.\-]+ [\d.\-]+\)', '(at %s %s)\\1(size %s %s)' % (f(x), f(y), f(w), f(h)), blk, 1)
    blk = re.sub(r'(\(property "Sheetname" "[^"]*"\s*\(at )[\d.\-]+ [\d.\-]+', lambda m: m.group(1) + '%s %s' % (f(x + 2.54), f(y - 1.27)), blk, 1)
    blk = re.sub(r'(\(property "Sheetfile" "[^"]*"\s*\(at )[\d.\-]+ [\d.\-]+', lambda m: m.group(1) + '%s %s' % (f(x + 2.54), f(y + h + 1.27)), blk, 1)
    for pn, (px, py, po) in pins.items():
        m = re.search(r'\(pin "%s" \w+\s*\(at [\d.\-]+ [\d.\-]+ \d+\)' % re.escape(pn), blk)
        assert m, (name, pn)
        seg = re.sub(r'\(at [\d.\-]+ [\d.\-]+ \d+\)', '(at %s %s %d)' % (f(px), f(py), po), m.group(0))
        blk = blk[:m.start()] + seg + blk[m.end():]
        k = blk.index(seg); e = blk.index('(justify', k); e2 = blk.index(')', e)
        blk = blk[:e] + '(justify %s' % SIDE[po] + blk[e2:]
    s = s[:a] + blk + s[b:]; done.add(name)
# every sheet pin: justify so its text sits inside the box (scripting server add_sheet_pin writes the opposite)
def fixjust(m):
    o = int(m.group(2)); return m.group(1) + '(justify %s' % SIDE[o]
s = re.sub(r'(\(pin "[^"]*" \w+\s*\(at [\d.\-]+ [\d.\-]+ (\d+)\)[\s\S]*?)\(justify \w+', fixjust, s)
# drop the old root wires (only the USB TS -> Battery TS wire existed); they are redrawn
n = 0
while '--keep-wires' not in sys.argv:
    m = re.search(r'\n\t\(wire\s*\(pts[\s\S]*?\n\t\)', s)
    if not m: break
    s = s[:m.start()] + s[m.end():]; n += 1
open(p, 'w').write(s)
print('laid out', sorted(done), 'missing', sorted(set(PLAN) - done), 'wires removed', n)
