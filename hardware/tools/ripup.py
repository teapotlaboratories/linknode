"""Rip up other-net tracks and vias around failed endpoints so mazeroute.py can retry (T26e).
Usage: python3 ripup.py <board.kicad_pcb> <drc.json> <radius_mm> NET [NET ...]
For every unconnected pair of the listed nets in the DRC report, delete tracks and vias of OTHER nets that come within
radius of either endpoint. Pads are never touched; nets matching PROTECT (hand-routed RF) are never ripped.
The ripped nets become unconnected and are re-routed by the next mazeroute.py pass."""
import sys, json, re, pcbnew
BOARD, DRC, R = sys.argv[1], sys.argv[2], float(sys.argv[3]); NETS = set(sys.argv[4:])
PROTECT = ('HALOW_ANT', 'Net-(C901-Pad2)', 'Net-(C903-Pad1)', 'Net-(J901-In)', 'Net-(J20-In)')
b = pcbnew.LoadBoard(BOARD); mm = pcbnew.FromMM
rep = json.load(open(DRC)); pts = []
for u in rep['unconnected_items']:
    a, c = u['items']; net = re.search(r'\[([^\]]+)\]', a['description']).group(1)
    if net in NETS:
        for i in (a, c):
            if not i['description'].startswith('Zone'): pts.append((net, i['pos']['x'], i['pos']['y']))
gone = {}
for t in list(b.GetTracks()):
    n = t.GetNetname()
    if any(p in n for p in PROTECT): continue
    for net, x, y in pts:
        if n == net: continue
        c = pcbnew.VECTOR2I(mm(x), mm(y))
        if t.GetEffectiveShape(t.GetLayer() if t.GetClass() != 'PCB_VIA' else pcbnew.F_Cu).Collide(c, mm(R)):
            gone[n] = gone.get(n, 0) + 1; b.Remove(t); break
print('ripped', sum(gone.values()), 'items from', len(gone), 'nets:', ', '.join(sorted(gone))[:300])
b.Save(BOARD)
