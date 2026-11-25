"""T30 checks on a saved board: kicad-cli DRC on the saved fills (no refill flag), unconnected split into RV1106 / rest,
vias inside SMD pads on RV1106 nets, tracks under Y501/Y502. Usage: python3 t30_check.py <board> <drc_out.json>"""
import sys, json, re, subprocess, collections, math, pcbnew
board, out = sys.argv[1], sys.argv[2]
subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-all', '--schematic-parity', '-o', out, board], capture_output=True)
d = json.load(open(out))
b = pcbnew.LoadBoard(board)
U = b.FindFootprintByReference('U100'); CX, CY = U.GetPosition().x/1e6, U.GetPosition().y/1e6
sat = re.compile(r'^(U100|R5\d\d|C5\d\d|Y5\d\d|TP5\d\d|J5\d\d|R6\d\d|C6\d\d|FB6\d\d)$')
RAILS = {'GND', 'VCC_3V3', 'VCC_1V8', 'VDD_0V9', 'VDD_ARM', 'VCC_DDR', 'VCC5V0_SYS', 'VBUS', 'VSYS', ''}
SIG = set()
for fp in b.GetFootprints():
    if sat.match(fp.GetReference()):
        for p in fp.Pads():
            n = p.GetNetname()
            if n not in RAILS and not n.startswith('unconnected'): SIG.add(n)
def soc_item(it):
    m = re.search(r' of (\S+) on ', it['description'])
    if m: return bool(sat.match(m.group(1)))
    return abs(it['pos']['x']-CX) < 13.5 and abs(it['pos']['y']-CY) < 13.5
rv, rest = [], 0
for u in d['unconnected_items']:
    a, c = u['items']; net = re.search(r'\[([^\]]*)\]', a['description']).group(1)
    netb = net if b.FindNet(net) else 'Net-(' + net[5:].replace('/', '{slash}') if net.startswith('Net-(') else net
    if netb in SIG or (net in RAILS and soc_item(a) and soc_item(c)): rv.append((net, a['description'][:48], c['description'][:48]))
    else: rest += 1
viol = collections.Counter(x['type'] for x in d['violations'])
smd = [(fp.GetReference(), q) for fp in b.GetFootprints() for q in fp.Pads() if q.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and not (fp.GetReference() == 'U100' and q.GetNumber() == '129')]
vip = []
for v in b.GetTracks():
    if v.GetClass() != 'PCB_VIA': continue
    if v.GetNetname() not in SIG and v.GetNetname() not in RAILS: continue
    for r, q in smd:
        if q.HitTest(v.GetPosition()): vip.append((r, q.GetNumber(), v.GetNetname())); break
under = {}
for ref in ('Y501', 'Y502'):
    fp = b.FindFootprintByReference(ref); bb = fp.GetBoundingBox(False, False); own = set(q.GetNetname() for q in fp.Pads())
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)          # exact: track copper against the crystal courtyard outline
    under[ref] = sorted(set((t.GetNetname(), b.GetLayerName(t.GetLayer())) for t in b.GetTracks()
                            if t.GetNetname() not in own and cy.Collide(t.GetEffectiveShape(t.GetLayer() if t.GetClass() != 'PCB_VIA' else pcbnew.F_Cu), 0)))
print(json.dumps({'unconnected_total': len(d['unconnected_items']), 'unconnected_rv1106': len(rv), 'unconnected_rest_of_board': rest,
                  'parity': len(d['schematic_parity']), 'violations': viol, 'vias_in_smd_pads': vip, 'tracks_under_crystals': under,
                  'rv1106_open': rv}, indent=1))
