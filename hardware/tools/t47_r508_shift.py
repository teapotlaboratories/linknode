"""T47 Section 3b (owner, 2026-11-23, option 1): move the USB series resistors R508/R509 (stacked, top) south by DY so a
via row fits under the 32 kHz XIN line for the three 3a nets that cross the microSD bus (USB_CC_SENSE, SARADC_IN0,
USB_VBUSDET). The USB pair's copper is kept, not re-routed:
  - USB_DP / USB_DN (R508/R509 pad 2 -> U1): every segment and arc above the first long vertical run moves with the
    resistors; that long run (D-: x 132.183 down to y 142.6; D+: x 132.465 after the deskew bumps) keeps its lower end
    and gets DY shorter. Both lines lose DY, so the pair skew is unchanged.
  - USB_SOC_DP / USB_SOC_DN (RV1106 pins 27/26 -> R508/R509 pad 1): the coupled run from the pins is kept up to where the
    lines split; from there each line goes to its moved pad by the shortest 45-degree path.
Usage: python3 t47_r508_shift.py <board.kicad_pcb> [DY=0.5]     Prints both lines' lengths before and after."""
import sys, os, math, json, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
B = sys.argv[1]; DY = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
b = pcbnew.LoadBoard(B); mm = pcbnew.FromMM; KEEP = []
def V(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))
def xy(v): return (v.x/1e6, v.y/1e6)
def tlen(t):
    return t.GetLength()/1e6
def netlen(n): return sum(tlen(t) for t in b.GetTracks() if t.GetNetname() == n and t.GetClass() != 'PCB_VIA')
NETS = ('/SoC/USB_SOC_DN', '/SoC/USB_SOC_DP', '/SoC/USB_DN', '/SoC/USB_DP')
before = {n: round(netlen(n), 3) for n in NETS}
# 1. the resistors
for r in ('R508', 'R509'):
    f = b.FindFootprintByReference(r); p = f.GetPosition(); f.SetPosition(pcbnew.VECTOR2I(p.x, p.y + mm(DY)))
# 2. the pair side: translate everything above the long run, stretch the long run's top end
CUT = {'/SoC/USB_DN': (132.183, 134.6), '/SoC/USB_DP': (132.465, 138.95)}     # (x of the long run, y above which copper moves)
for n, (xl, yc) in CUT.items():
    for t in list(b.GetTracks()):
        if t.GetNetname() != n or t.GetClass() == 'PCB_VIA': continue
        s, e = xy(t.GetStart()), xy(t.GetEnd())
        if max(s[1], e[1]) <= yc:
            t.Move(V(0, DY))
        elif min(s[1], e[1]) <= yc < max(s[1], e[1]) and t.GetClass() == 'PCB_TRACK':
            assert abs(s[0] - xl) < 0.01 and abs(e[0] - xl) < 0.01, (n, s, e)       # the long vertical run
            if s[1] < e[1]: t.SetStart(V(s[0], s[1] + DY))
            else: t.SetEnd(V(e[0], e[1] + DY))
# 3. the SoC side: keep the pin-side start (segments east of XS), then each line runs straight west (D+ and D- stay
#    coupled) and turns 45 degrees into its moved pad; D+ turns earlier, which keeps the pair skew at ~0
XS = 134.75
def pad(ref, num): return [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
for n, ref in (('/SoC/USB_SOC_DN', 'R509'), ('/SoC/USB_SOC_DP', 'R508')):
    segs = [t for t in b.GetTracks() if t.GetNetname() == n and t.GetClass() == 'PCB_TRACK']
    keep = [t for t in segs if min(xy(t.GetStart())[0], xy(t.GetEnd())[0]) >= XS - 1e-6]
    for t in segs:
        if t not in keep: b.Remove(t); KEEP.append(t)
    ends = [xy(t.GetStart()) for t in keep] + [xy(t.GetEnd()) for t in keep]
    a = min(ends, key=lambda q: q[0])                                   # west end of the kept coupled run
    c = xy(pad(ref, '1').GetPosition())
    dx, dy = c[0] - a[0], c[1] - a[1]; m = min(abs(dx), abs(dy))
    mid = (c[0] - math.copysign(m, dx), c[1] - math.copysign(m, dy))  # straight (still coupled) first, then 45 degrees into the pad
    w = keep[0].GetWidth()
    for p_, q_ in ((a, mid), (mid, c)):
        if math.dist(p_, q_) < 1e-6: continue
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(*p_)); t.SetEnd(V(*q_)); t.SetWidth(w); t.SetLayer(pcbnew.F_Cu); t.SetNet(b.FindNet(n)); b.Add(t)
after = {n: round(netlen(n), 3) for n in NETS}
tot = lambda d: {'D-': round(d['/SoC/USB_SOC_DN'] + d['/SoC/USB_DN'], 3), 'D+': round(d['/SoC/USB_SOC_DP'] + d['/SoC/USB_DP'], 3)}
b.Save(B)
print(json.dumps(dict(dy=DY, before=before, after=after, total_before=tot(before), total_after=tot(after))))
