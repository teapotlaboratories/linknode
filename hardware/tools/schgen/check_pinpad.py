"""T15: every part's symbol pin numbers vs its footprint's pad numbers (kicadxml netlist + .kicad_mod files).
Usage: check_pinpad.py net.xml"""
import sys, re, os, xml.etree.ElementTree as ET, collections
LIBS = {'linknode': '/home/argonite/Developments/klepon/hardware/kicad/library/linknode.pretty'}
STOCK = '/usr/share/kicad/footprints'
t = ET.parse(sys.argv[1]).getroot()
libpins = {}
for lp in t.iter('libpart'):
    key = (lp.get('lib'), lp.get('part'))
    libpins[key] = {p.get('num') for p in lp.iter('pin')}
pads_cache = {}
def pads(fp):
    if fp in pads_cache: return pads_cache[fp]
    lib, name = fp.split(':', 1)
    d = LIBS.get(lib, os.path.join(STOCK, lib + '.pretty'))
    f = os.path.join(d, name + '.kicad_mod')
    if not os.path.exists(f): pads_cache[fp] = None; return None
    s = open(f).read()
    P = {m for m in re.findall(r'\(pad "([^"]*)"', s) if m != ''}
    pads_cache[fp] = P; return P
bad = 0; seen = set()
for c in t.iter('comp'):
    ref = c.get('ref'); fp = (c.findtext('footprint') or '').strip()
    ls = c.find('libsource'); key = (ls.get('lib'), ls.get('part'))
    if ref.startswith('#') or (ref, fp) in seen: continue
    seen.add((ref, fp))
    if not fp: print(ref, key, 'NO FOOTPRINT'); bad += 1; continue
    P = pads(fp)
    if P is None: print(ref, fp, 'FOOTPRINT FILE NOT FOUND'); bad += 1; continue
    pins = libpins.get(key, set())
    miss = pins - P; extra = P - pins
    if miss or extra:
        bad += 1; print(ref, key[1], fp, 'pins w/o pad:', sorted(miss), 'pads w/o pin:', sorted(extra))
print('components checked:', len(seen), 'problems:', bad)
