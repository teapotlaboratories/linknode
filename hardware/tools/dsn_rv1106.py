"""Prepare a KiCad-exported Specctra DSN so Freerouting routes only the RV1106 (T30, 2026-11-22).
Usage: python3 dsn_rv1106.py <raw.dsn> <out.dsn> [--usb-clearance 500]
- planes: only GND on In1.Cu kept (In1 as power layer); the other pours refill around the routes in KiCad;
- SoCPower class 200/120 with the 400/200 via (the scripting server exporter labels it "Power,SoCPower" at 300/150);
- (control (via_at_smd off)): no vias inside SMD pads;
- network: RV1106 signal nets (on U100 and the 5xx/6xx parts) keep all pins; GND and the rails keep only the pins of
  U100 and its parts; every other pin becomes a one-pin net in its original class (keeps its clearance, nothing to route);
- --usb-clearance: clearance (um) of the USB90 class, e.g. 500 for the HDG 20 mil spacing (the pair itself is locked).
Locked board items arrive as (type fix) and stay."""
import re, sys
src, dst = sys.argv[1], sys.argv[2]
opt = dict(zip(sys.argv[3::2], sys.argv[4::2]))
s = open(src).read()
RAIL = {'GND', 'VCC_3V3', 'VCC_1V8', 'VDD_0V9', 'VDD_ARM', 'VCC_DDR'}
NOT_SIG = RAIL | {'VCC5V0_SYS', 'VBUS', 'VSYS'}
sat = re.compile(r'^(U100|R5\d\d|C5\d\d|Y5\d\d|TP5\d\d|J5\d\d|R6\d\d|C6\d\d|FB6\d\d)-')
def drop(m): return m.group(0) if (m.group(1) == 'GND' and m.group(2) == 'In1.Cu') else ''
s = re.sub(r'\s*\(plane (\S+) \(polygon (\S+)[^)]*\)\)', drop, s)
s = re.sub(r'(\(layer In1\.Cu\s*\(type )signal\)', r'\1power)', s, count=1)
m = re.search(r'\(class (Power,SoCPower|SoCPower)( [^\n]*)\n\s*\(circuit\s*\(use_via "[^"]+"\)\s*\)\s*\(rule\s*\(width \d+\)\s*\(clearance \d+\)\s*\)', s)
if m: s = s[:m.start()] + '(class SoCPower' + m.group(2) + '\n      (circuit\n        (use_via "Via[0-3]_400:200_um")\n      )\n      (rule\n        (width 200)\n        (clearance 120)\n      )' + s[m.end():]
i = s.index('(structure'); s = s[:i+len('(structure')] + '\n    (control (via_at_smd off))' + s[i+len('(structure'):]
ni = s.index('  (network'); ci = s.index('    (class ', ni)
def q(n): return '"%s"' % n if re.search(r'[\s/()"{}:,]', n) else n
out = []; rename = {}; SIG = set(); stats = {'signal': 0, 'rail_soc': 0, 'singletons': 0}
for m in re.finditer(r'    \(net ("[^"]*"|\S+)\n      \(pins ([^)]*)\)\n    \)\n', s[ni:ci]):
    name = m.group(1).strip('"'); pins = m.group(2).split()
    soc = [p for p in pins if sat.match(p)]
    if name not in NOT_SIG and soc:
        out.append(m.group(0)); SIG.add(name); stats['signal'] += 1; continue
    keep = soc if name in RAIL else []
    if len(keep) > 1:
        out.append('    (net %s\n      (pins %s)\n    )\n' % (m.group(1), ' '.join(keep))); SIG.add(name); stats['rail_soc'] += 1
        rest = [p for p in pins if p not in keep]
    else: rest = pins
    new = []
    for k, p in enumerate(rest):
        nn = '%s__pin%d' % (name, k); new.append(nn); out.append('    (net %s\n      (pins %s)\n    )\n' % (q(nn), p)); stats['singletons'] += 1
    if new: rename[name] = new
s = s[:ni] + '  (network\n' + ''.join(out) + s[ci:]
def repl(mm_):
    toks = re.findall(r'"[^"]*"|[^\s"]+', mm_.group(2)); res = []
    for t in toks:
        n = t.strip('"')
        if n in SIG: res.append(t)
        if n in rename: res += [q(x) for x in rename[n]]
    return '    (class %s %s\n      (circuit' % (mm_.group(1), ' '.join(dict.fromkeys(res)))
s = re.sub(r'    \(class (\S+)((?:.|\n)*?)\n      \(circuit', repl, s)
s = re.sub(r'    \(class (\S+) \n      \(circuit(?:.|\n)*?\n    \)\n', '', s)
if '--usb-clearance' in opt:
    s, n = re.subn(r'(\(class USB90 [^\n]*\n(?:.|\n)*?\(clearance )\d+(\))', r'\g<1>%s\2' % opt['--usb-clearance'], s, count=1)
    stats['usb_clearance_set'] = bool(n)
open(dst, 'w').write(s)
print(stats, re.findall(r'\(class (\S+)', s))
