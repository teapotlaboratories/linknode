"""Set every footprint pad's net from a KiCad XML netlist (the netlist writes '/' where the board stores '{slash}' in generated
Net-(...) / unconnected-(...) names). Optional --drop REF,REF removes footprints that left the schematic.
Usage: python3 padsync.py <in.kicad_pcb> <out.kicad_pcb> <netlist.xml> [--drop U1004,U1005]"""
import sys, pcbnew, xml.etree.ElementTree as ET
IN, OUT, NL = sys.argv[1:4]; DROP = set(sys.argv[sys.argv.index('--drop') + 1].split(',')) if '--drop' in sys.argv else set()
b = pcbnew.LoadBoard(IN); r = ET.parse(NL).getroot()
pin_net = {(x.get('ref'), x.get('pin')): n.get('name') for n in r.iter('net') for x in n.iter('node')}
def net(name):
    n = b.FindNet(name)
    if n is None: n = pcbnew.NETINFO_ITEM(b, name); b.Add(n)
    return n
def bn(nm): return nm.replace('/', '{slash}') if nm.startswith(('Net-(', 'unconnected-(')) else nm
ch = []; rm = []
for f in b.GetFootprints():
    if f.GetReference() in DROP: rm.append(f); continue
    for p in f.Pads():
        nm = pin_net.get((f.GetReference(), p.GetNumber()))
        if nm is None: continue
        if p.GetNetname() != bn(nm): ch.append((f.GetReference(), p.GetNumber(), p.GetNetname(), bn(nm))); p.SetNet(net(bn(nm)))
for f in rm: b.Remove(f)
b.Save(OUT)
print(len(ch), 'pads re-netted, removed', len(rm))
for c in ch: print('  %s.%s %s -> %s' % c)
