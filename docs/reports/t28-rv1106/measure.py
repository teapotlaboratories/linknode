"""Measure U100 (RV1106G3) placement against the Rockchip HDG V1.1 rules, on the current board and on the pre-T28 backup.
Usage: python3 measure.py <board_now> <board_before> > data.json"""
import sys, json, math, pcbnew
GROUPS = [(['1'], ['C603']), (['10'], ['C610']), (['13'], ['C629']), (['19'], ['C604']), (['24'], ['C602']), (['28'], ['C630']),
 (['30'], ['C637']), (['31'], ['C625']), (['43'], ['C631']), (['49', '50'], ['C623']), (['51'], ['C611']),
 (['54', '55'], ['C612', 'C613', 'C619']), (['53'], ['C626', 'C628']), (['56'], ['C624']),
 (['61'], ['C632']), (['66'], ['C505', 'R503']), (['67'], ['C614']), (['70'], ['C627']), (['71'], ['C615', 'C620']),
 (['81'], ['C633']), (['82'], ['C616']), (['88'], ['C634']), (['96'], ['C601']), (['101'], ['C635']),
 (['102'], ['R605']), (['103'], ['C617']), (['108'], ['C636']), (['115'], ['C606', 'C607']), (['116'], ['C618']), (['52'], ['R604'])]
def P(v): return (round(v.x/1e6, 3), round(v.y/1e6, 3))
def d(a, b): return round(math.hypot(a[0]-b[0], a[1]-b[1]), 2)
def measure(path, full):
    b = pcbnew.LoadBoard(path); U = b.FindFootprintByReference('U100'); C = P(U.GetPosition())
    pad = {p.GetNumber(): p for p in U.Pads() if p.GetNumber()}
    vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    smd = [(fp.GetReference(), q) for fp in b.GetFootprints() for q in fp.Pads() if q.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and not (fp.GetReference() == 'U100' and q.GetNumber() == '129')]
    vip = [(v, r, q) for v in vias for r, q in smd if q.HitTest(v.GetPosition())]
    vipset = set(id(v) for v, r, q in vip)
    out_vip = [{'ref': r, 'pad': q.GetNumber(), 'net': q.GetNetname(), 'pos': P(v.GetPosition()), 'side': 'B' if q.IsOnLayer(pcbnew.B_Cu) else 'F'} for v, r, q in vip]
    out = {'U100': C, 'groups': [], 'via_in_pad': out_vip}
    for pins, parts in GROUPS:
        net = pad[pins[0]].GetNetname(); pp = P(pad[pins[0]].GetPosition())
        ring = [P(v.GetPosition()) for v in vias if id(v) not in vipset and v.GetNetname() == net and 3.5 < max(abs(P(v.GetPosition())[0]-C[0]), abs(P(v.GetPosition())[1]-C[1])) < 5.7]
        via = min(ring, key=lambda q: d(q, pp)) if ring else None
        g = {'pins': pins, 'net': net, 'pin': pp, 'via': via, 'parts': []}
        for ref in parts:
            fp = b.FindFootprintByReference(ref)
            mine = [P(q.GetPosition()) for q in fp.Pads() if q.GetNetname() == net]
            other = [(P(q.GetPosition()), q.GetNetname()) for q in fp.Pads() if q.GetNetname() != net]
            cp = min(mine, key=lambda q: d(q, via or pp)) if mine else None
            e = {'ref': ref, 'val': fp.GetValue(), 'side': 'B' if fp.IsFlipped() else 'F', 'pos': P(fp.GetPosition()),
                 'rot': fp.GetOrientationDegrees(), 'pad': cp, 'other': other,
                 'pin_to_pad': d(pp, cp) if cp else None}
            if via and cp and e['side'] == 'B': e['path'] = round(d(pp, via) + d(via, cp), 2)
            g['parts'].append(e)
        out['groups'].append(g)
    if full:
        bulk = {}
        for ref in ('C608', 'C609', 'C605', 'C621', 'C622'):
            fp = b.FindFootprintByReference(ref); bulk[ref] = {'val': fp.GetValue(), 'side': 'B' if fp.IsFlipped() else 'F', 'pos': P(fp.GetPosition()),
                    'net': [q.GetNetname() for q in fp.Pads() if q.GetNetname() != 'GND'][0]}
        out['bulk'] = bulk
        # all pads of U100 for drawing
        out['pads'] = [{'n': p.GetNumber(), 'pos': P(p.GetPosition()), 'sz': (round(p.GetBoundingBox().GetWidth()/1e6, 3), round(p.GetBoundingBox().GetHeight()/1e6, 3)), 'net': p.GetNetname()} for p in U.Pads() if p.GetNumber()]
        out['ep_vias'] = sum(1 for v in vias if max(abs(P(v.GetPosition())[0]-C[0]), abs(P(v.GetPosition())[1]-C[1])) < 3.5 and v.GetNetname() == 'GND')
        out['bottom_parts'] = []
        for fp in b.GetFootprints():
            q = P(fp.GetPosition())
            if fp.IsFlipped() and abs(q[0]-C[0]) < 9 and abs(q[1]-C[1]) < 9:
                out['bottom_parts'].append({'ref': fp.GetReference(), 'pos': q, 'rot': fp.GetOrientationDegrees(),
                    'pads': [{'pos': P(x.GetPosition()), 'net': x.GetNetname(), 'sz': (round(x.GetBoundingBox().GetWidth()/1e6, 3), round(x.GetBoundingBox().GetHeight()/1e6, 3))} for x in fp.Pads()]})
        out['ring_vias'] = [{'pos': P(v.GetPosition()), 'net': v.GetNetname()} for v in vias if 3.5 < max(abs(P(v.GetPosition())[0]-C[0]), abs(P(v.GetPosition())[1]-C[1])) < 5.7]
        # crystals, series R, RTC RC, board
        bb = b.GetBoardEdgesBoundingBox(); out['board'] = [bb.GetLeft()/1e6, bb.GetTop()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6]
        misc = {}
        for fp in b.GetFootprints():
            nets = [q.GetNetname() for q in fp.Pads()]
            if any('OSC' in n for n in nets) or any('RTC' in n for n in nets) or any('SD_CLK' in n or 'SDMMC0_CLK' in n for n in nets) or fp.GetReference().startswith('Y'):
                misc[fp.GetReference()] = {'val': fp.GetValue(), 'side': 'B' if fp.IsFlipped() else 'F', 'pos': P(fp.GetPosition()), 'nets': nets,
                    'to_U100_mm': d(P(fp.GetPosition()), C)}
        out['misc'] = misc
        # nearest U100 pad for each misc part's signal pad
        for ref, m in misc.items():
            fp = b.FindFootprintByReference(ref); best = None
            for q in fp.Pads():
                for p in U.Pads():
                    if p.GetNumber() and p.GetNetname() == q.GetNetname() and q.GetNetname() not in ('GND', ''):
                        dd = d(P(q.GetPosition()), P(p.GetPosition()))
                        if best is None or dd < best[0]: best = (dd, p.GetNumber())
            m['to_pin'] = best
        # crystal GND pads: GND via within 1 mm?
        for ref, m in misc.items():
            if not ref.startswith('Y'): continue
            fp = b.FindFootprintByReference(ref); gp = [P(q.GetPosition()) for q in fp.Pads() if q.GetNetname() == 'GND']
            m['gnd_pads'] = len(gp); m['gnd_via_mm'] = [min([d(g, P(v.GetPosition())) for v in vias if v.GetNetname() == 'GND'] or [99]) for g in gp]
            # foreign tracks under the crystal on any layer
            box = fp.GetBoundingBox(False, False); under = set()
            for t in b.GetTracks():
                if t.GetClass() == 'PCB_VIA' or t.GetNetname() in [q.GetNetname() for q in fp.Pads()]: continue
                if box.Intersects(t.GetBoundingBox()): under.add((t.GetNetname(), b.GetLayerName(t.GetLayer())))
            m['tracks_under'] = sorted(under)
    return out
now = measure(sys.argv[1], True); before = measure(sys.argv[2], False)
print(json.dumps({'now': now, 'before': before}, indent=0))
