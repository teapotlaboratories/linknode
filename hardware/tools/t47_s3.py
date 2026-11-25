"""T47 Section 3 (2026-11-23): RV1106 signal nets, by the T31 method, under the T47 rules.
Usage: python3 t47_s3.py <board.kicad_pcb> [KEY,KEY,... [--stub-exp]] [--extra NET,NET]   (keys: net-name substrings for a subset;
       --extra: full names of nets with no RV1106 pin to route as well)
1. Escape stubs (0.12 mm, top) straight out from every RV1106 signal pin that has no copper yet, the expansion pins
   included (only their stubs: those nets are routed last, owner), with a lane reserved around each stub so no route
   cuts across a neighbour's exit (netroute.add_escapes).
2. Every non-expansion RV1106 signal net routed end to end (netroute, top + bottom, 0.12 mm), 0.5 mm from the USB pair
   on the same layer (HDG 20 mil). SD/SDIO are routed here and length-matched in a later section.
Then bend45.py --pull on these nets (45-degree bends), refill, DRC. Prints the nets that failed."""
import sys, os, json, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import netroute as nr
from geomlib import Geo
B = sys.argv[1]; b = pcbnew.LoadBoard(B)
_eb = b.GetBoardEdgesBoundingBox(); EBOX = (_eb.GetLeft()/1e6 - 1, _eb.GetTop()/1e6 - 1, _eb.GetRight()/1e6 + 1, _eb.GetBottom()/1e6 + 1)
U = b.FindFootprintByReference('U100')
RAILS = {'GND', 'VCC_3V3', 'VCC_1V8', 'VDD_0V9', 'VDD_ARM', 'VCC_DDR', ''}
USB = ('/SoC/USB_DP', '/SoC/USB_DN')                       # HDG 20 mil rule on the long pair (as linknode.kicad_dru); the 3 mm pin-side segments are exempt
routed = {t.GetNetname() for t in b.GetTracks()}
def is_exp(n): return n.startswith('/Expansion/')
pins = [p for p in U.Pads() if p.GetNetname() not in RAILS and not p.GetNetname().startswith('unconnected')]
ESC = {p.GetNetname() for p in pins if p.GetNetname() not in routed}
SIG = {n for n in ESC if not is_exp(n)}
if len(sys.argv) > 2:                                       # subset: comma-separated net-name substrings (e.g. a 3a/3b/3c group)
    keys = sys.argv[2].split(',')                          # named nets are routed even if they have copper (fan-out stubs)
    SIG = {p.GetNetname() for p in pins if not is_exp(p.GetNetname()) and any(k in p.GetNetname() for k in keys)}
    ESC = (SIG & ESC) | {n for n in ESC if is_exp(n)} if '--stub-exp' in sys.argv else SIG & ESC
    print('subset', sorted(SIG), flush=True)
if '--extra' in sys.argv:                                   # nets with no RV1106 pin (e.g. a clock after its series resistor)
    EXTRA = set(sys.argv[sys.argv.index('--extra') + 1].split(','))
    SIG |= EXTRA; print('extra', sorted(EXTRA), flush=True)
g = Geo(b, EBOX)
made = []
n_esc = nr.add_escapes(b, g, ESC, made=made)
print('escape stubs', n_esc, 'of', len(ESC), flush=True)
MARGIN = float(sys.argv[sys.argv.index('--margin') + 1]) if '--margin' in sys.argv else 5.0   # search window around each connection
failed = nr.route_nets(b, B, g, SIG, keep_from=USB, keep=0.35, made=made, diag=True, margin=MARGIN)
# An escape stub can run straight past the pad it lands on (the route then starts at the pad): cut such a free end back
# to the point on the stub nearest the pad centre, so no copper dangles (DRC track_dangling).
import math
def _xy(v): return (v.x/1e6, v.y/1e6)
trimmed = 0
for t in [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in SIG]:
    n = t.GetNetname(); L = t.GetLayer(); tid = t.m_Uuid.AsString()       # SWIG wrappers differ per call: match by UUID
    for end in ('start', 'end'):
        q = _xy(t.GetStart() if end == 'start' else t.GetEnd()); o = _xy(t.GetEnd() if end == 'start' else t.GetStart())
        others = [u for u in b.GetTracks() if u.m_Uuid.AsString() != tid and u.GetNetname() == n and (
            (u.GetClass() == 'PCB_VIA' and math.dist(_xy(u.GetPosition()), q) < 0.01) or
            (u.GetClass() != 'PCB_VIA' and u.GetLayer() == L and min(math.dist(_xy(u.GetStart()), q), math.dist(_xy(u.GetEnd()), q)) < 0.01))]
        pads = [p for p in b.GetPads() if p.GetNetname() == n and p.IsOnLayer(L)]
        if others or any(p.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(q[0]), pcbnew.FromMM(q[1]))) for p in pads): continue
        for p in pads:
            c = _xy(p.GetPosition()); d = (q[0] - o[0], q[1] - o[1]); l2 = d[0]**2 + d[1]**2
            k = max(0.0, min(1.0, ((c[0] - o[0])*d[0] + (c[1] - o[1])*d[1])/l2)) if l2 else 0
            m = (o[0] + d[0]*k, o[1] + d[1]*k)
            if 0 < k < 1 and p.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(m[0]), pcbnew.FromMM(m[1]))):
                v = pcbnew.VECTOR2I(pcbnew.FromMM(m[0]), pcbnew.FromMM(m[1]))
                t.SetStart(v) if end == 'start' else t.SetEnd(v); trimmed += 1; break
print('dangling ends trimmed', trimmed, flush=True)
b.Save(B)
print(json.dumps(dict(signal_nets=len(SIG), expansion_stubbed=len(ESC - SIG), escapes=n_esc, failed=sorted(set(failed)),
                      unrouted=b.GetConnectivity().GetUnconnectedCount(False))))
