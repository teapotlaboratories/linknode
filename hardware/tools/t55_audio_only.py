"""T55 (owner, 2026-11-24: "Audio only on FPC B"): the 7 FPC B GPIOs (GPIO4_A6/A4/A3/A2/B0 on 39/41/42/44/47, GPIO0_A3/A4 on
62/63) are dropped: they are walled in by the microSD bus and the ESP32-C5 SPI (south) and the free 1.8 V pins are walled in
by the SD/RTC/USB escapes (west). Minimal text edits; the expansion sheet itself comes from schgen/build_expansion.py.
Usage: python3 t55_audio_only.py <kicad dir>
soc.kicad_sch:      pins 39/41/42/44/47/62/63: wire + hierarchical label removed, no-connect back on the pin end
linknode.kicad_sch: the 7 sheet pins on SoC (bottom edge) and Expansion (top edge) and the wires between them removed"""
import sys, os, re, importlib.util
K = sys.argv[1]
spec = importlib.util.spec_from_file_location('g3', os.path.join(os.path.dirname(os.path.abspath(__file__)), 't55_gpio3.py'))
src = open(spec.origin).read(); src = src[:src.index("p = os.path.join(K, 'soc.kicad_sch')")]   # helpers only
ns = {'__file__': spec.origin}; sys.argv = [spec.origin, K]; exec(compile(src, spec.origin, 'exec'), ns)
p = os.path.join(K, 'soc.kicad_sch'); s = open(p).read()
for pin, name in ns['OLD']: s = ns['unstub'](s, pin, name)
open(p, 'w').write(s)
p = os.path.join(K, 'linknode.kicad_sch'); s = open(p).read()
def sheet_span(s, name):
    i = s.index(f'(property "Sheetname" "{name}"'); st = s.rindex('\n\t(sheet\n', 0, i) + 1; return st, ns['close'](s, st)
def drop_pin(s, sheet, name):
    st, en = sheet_span(s, sheet); blk = s[st:en]
    m = re.search(r'\n\t\t\(pin "' + re.escape(name) + r'" \w+', blk); assert m, (sheet, name)
    b = ns['close'](blk, m.start() + 3)
    return s[:st] + blk[:m.start()] + blk[b:] + s[en:]
for _, name in ns['OLD']:
    st, en = sheet_span(s, 'SoC'); x = float(re.search(r'\(pin "' + name + r'" \w+\s+\(at ([\d.]+) ', s[st:en]).group(1))
    s = drop_pin(s, 'SoC', name); s = drop_pin(s, 'Expansion', name)
    w = [m for m in re.finditer(r'\n\t\(wire\s+\(pts\s+\(xy ([\d.]+) 139\.7\) \(xy ([\d.]+) 147\.32\)', s)
         if abs(float(m.group(1)) - x) < 0.01 and abs(float(m.group(2)) - x) < 0.01]
    assert len(w) == 1, (name, x); ws, we = ns['block'](s, w[0].start() + 1); s = s[:ws - 1] + s[we:]
open(p, 'w').write(s)
print('soc: 7 stubs removed; root: 7 pins x2 + 7 wires removed')
