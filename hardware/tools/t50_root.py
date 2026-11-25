"""T50 root sheet: 10 Ethernet + audio signals between SoC Power and Expansion, no crossing wires.
Usage: python3 t50_root.py <kicad dir>
  SoC Power (25.4, 129.54) 45.72 x 58.42 (left column under GPS): GPS_PWR_EN top edge (50.8) -> straight up to the GPS
            bottom pin; ETH x4 + MIC0P/N, MIC1P/N, MICBIAS, LINEOUT on its right edge (y 162.56..185.42); C5_PWR_EN bottom
            edge (68.58) -> y 193.04 -> x 170.18 -> y 142.24 -> x 279.4 -> y 71.12 -> Radio Power right edge.
  Expansion (101.6, 147.32) 63.5 x 40.64: the same 10 pins on its left edge, below the vertical top-pin names.
  Power (175.26, 147.32) and Hold-off (228.6, 147.32), 45.72 x 10.16 (no pins), in the space SoC Power left."""
import sys, re, uuid
K = sys.argv[1]; P = K + '/linknode.kicad_sch'; s = open(P).read()
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
def edit_sheet(s, name, at=None, size=None, remove=(), add=(), file_at=None):
    st, en = sheet_span(s, name); b = s[st:en]
    if at:
        b = re.sub(r'\(at [\d.\-]+ [\d.\-]+\)\n\t\t\(size [\d.\-]+ [\d.\-]+\)', f'(at {g(at[0])} {g(at[1])})\n\t\t(size {g(size[0])} {g(size[1])})', b, 1)
        b = re.sub(r'(\(property "Sheetname" "[^"]+"\n\t\t\t)\(at [\d.\-]+ [\d.\-]+ 0\)', lambda m: m.group(1) + f'(at {g(at[0] + 2.54)} {g(at[1] - 1.27)} 0)', b, 1)
        fa = file_at or (at[0] + 2.54, at[1] + size[1] + 1.27)
        b = re.sub(r'(\(property "Sheetfile" "[^"]+"\n\t\t\t)\(at [\d.\-]+ [\d.\-]+ 0\)', lambda m: m.group(1) + f'(at {g(fa[0])} {g(fa[1])} 0)', b, 1)
    elif file_at:
        b = re.sub(r'(\(property "Sheetfile" "[^"]+"\n\t\t\t)\(at [\d.\-]+ [\d.\-]+ 0\)', lambda m: m.group(1) + f'(at {g(file_at[0])} {g(file_at[1])} 0)', b, 1)
    for pn in remove:
        i = b.index(f'(pin "{pn}" '); st2 = b.rindex('\n', 0, i); b = b[:st2] + b[close(b, i):]
    if add:
        k = b.rstrip().rindex(')'); b = b[:k].rstrip('\n\t') + ''.join(pin_txt(*a) for a in add) + '\n\t)'
    return s[:st] + b + s[en:]
def wire_txt(a, c):
    return f'\n\t(wire\n\t\t(pts\n\t\t\t(xy {g(a[0])} {g(a[1])}) (xy {g(c[0])} {g(c[1])})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)'
def drop_wire(s, a, c):
    for m in re.finditer(r'\n\t\(wire\n\t\t\(pts\n\t\t\t\(xy ([\d.\-]+) ([\d.\-]+)\) \(xy ([\d.\-]+) ([\d.\-]+)\)\n\t\t\)(?:.|\n)*?\(uuid "[^"]+"\)\n\t\)', s):
        p = {(round(float(m.group(1)), 2), round(float(m.group(2)), 2)), (round(float(m.group(3)), 2), round(float(m.group(4)), 2))}
        if p == {a, c}: return s[:m.start()] + s[m.end():]
    raise KeyError((a, c))
ETH = [('ETH_TXP', 'output'), ('ETH_TXN', 'output'), ('ETH_RXP', 'input'), ('ETH_RXN', 'input')]
AUD = [('MIC0P', 'input'), ('MIC0N', 'input'), ('MIC1P', 'input'), ('MIC1N', 'input'), ('MICBIAS', 'output'), ('LINEOUT', 'output')]
ROWS = [(n, t, 162.56 + 2.54 * i) for i, (n, t) in enumerate(ETH + AUD)]
# --- T49 wires out
for a, c in [((165.1, y), (175.26, y)) for y in (149.86, 152.4, 154.94, 157.48)] + [
        ((50.8, 121.92), (50.8, 172.72)), ((50.8, 172.72), (170.18, 172.72)), ((170.18, 172.72), (170.18, 160.02)), ((170.18, 160.02), (175.26, 160.02)),
        ((220.98, 149.86), (246.38, 149.86)), ((246.38, 149.86), (246.38, 71.12)), ((246.38, 71.12), (236.22, 71.12))]:
    s = drop_wire(s, a, c)
# --- sheets
s = edit_sheet(s, 'SoC Power', at=(25.4, 129.54), size=(45.72, 58.42),
               remove=('ETH_TXP', 'ETH_TXN', 'ETH_RXP', 'ETH_RXN', 'GPS_PWR_EN', 'C5_PWR_EN'),
               add=[('GPS_PWR_EN', 'output', 50.8, 129.54, 90)] + [(n, t, 71.12, y, 0) for n, t, y in ROWS] + [('C5_PWR_EN', 'output', 68.58, 187.96, 270)])
s = edit_sheet(s, 'Expansion', remove=('ETH_TXP', 'ETH_TXN', 'ETH_RXP', 'ETH_RXN'),
               add=[(n, {'output': 'input', 'input': 'output'}[t], 101.6, y, 180) for n, t, y in ROWS], file_at=(104.14, 189.23))
st, en = sheet_span(s, 'Expansion')
s = s[:st] + s[st:en].replace('(size 63.5 20.32)', '(size 63.5 40.64)', 1) + s[en:]
s = edit_sheet(s, 'Power', at=(175.26, 147.32), size=(45.72, 10.16))
s = edit_sheet(s, 'Hold-off', at=(228.6, 147.32), size=(45.72, 10.16))
# --- wires in
W = [((50.8, 121.92), (50.8, 129.54))] + [((71.12, y), (101.6, y)) for _, _, y in ROWS]
W += [((68.58, 187.96), (68.58, 193.04)), ((68.58, 193.04), (170.18, 193.04)), ((170.18, 193.04), (170.18, 142.24)),
      ((170.18, 142.24), (279.4, 142.24)), ((279.4, 142.24), (279.4, 71.12)), ((279.4, 71.12), (236.22, 71.12))]
k = s.index('\n\t(wire'); s = s[:k] + ''.join(wire_txt(a, c) for a, c in W) + s[k:]
open(P, 'w').write(s); print('root: T50 layout, wires', len(W))
