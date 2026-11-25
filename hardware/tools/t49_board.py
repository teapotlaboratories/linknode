"""T49/T50 board update: Expansion sheet parts onto the board + re-net from the schematic netlist (no tracks exist yet).
Usage: python3 t49_board.py <board.kicad_pcb> <netlist (kicadsexpr)>
1. Every component in the netlist that is missing on the board is added (footprint from the library, KIID path
   /<sheet tstamps>/<symbol tstamp>, Sheetname/Sheetfile, fields LCSC/Description/Datasheet hidden on F.Fab).
2. Every pad of every footprint takes its net from the netlist (new nets created). This also moves the three enables
   and connects the 27 newly used RV1106 pins.
3. TP10nn (pogo pad n) goes to the bottom at MH1 + (56.00 + 2.54*col, 27.20 + 2.54*row), row = (n-1)//7, col = (n-1)%7.
4. U1001-U1005, R1001-R1008 are placed on the bottom next to the pads they serve (placelib.place_moves); the area under
   the ESP32-C5 ground pad (vias go there) is kept out."""
import sys, os, re, json, pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from placelib import place_moves
BRD, NET = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(BRD); mm = pcbnew.FromMM
s = open(NET).read()
# --- components
comps = {}
for m in re.finditer(r'\n\t\t\(comp\n(.*?)\n\t\t\)(?=\n\t\t\(comp|\n\t\)\n)', s, re.S):
    blk = m.group(1)
    ref = re.search(r'\(ref "([^"]+)"\)', blk).group(1)
    d = dict(value=re.search(r'\(value "([^"]*)"\)', blk).group(1), fp=re.search(r'\(footprint "([^"]*)"\)', blk).group(1),
             sheet=re.search(r'\(sheetpath\s+\(names "([^"]*)"\)\s+\(tstamps "([^"]*)"\)', blk).groups(),
             uid=(re.search(r'\n\t\t\t\(tstamps "([^"]+)"', blk) or re.search(r'^\t\t\t\(tstamps "([^"]+)"', blk, re.M)).group(1),   # multi-unit parts list several
             fields={k: v for k, v in re.findall(r'\(field\s+\(name "([^"]+)"\) "([^"]*)"\)', blk)},
             sheetfile=re.search(r'\(name "Sheetfile"\)\s+\(value "([^"]*)"\)', blk).group(1))
    comps[ref] = d
pinnet = {}
body = s[s.index('\n\t(nets'):]
for blk in re.split(r'\n\t\t\(net\b', body)[1:]:
    name = re.search(r'\(name "([^"]*)"\)', blk).group(1)
    for r, n in re.findall(r'\(ref "([^"]+)"\)\s+\(pin "([^"]+)"\)', blk): pinnet[(r, n)] = name
FP = {f.GetReference(): f for f in b.GetFootprints()}
added = []
for ref, d in sorted(comps.items()):
    if ref in FP: continue
    lib, name = d['fp'].split(':')
    path = os.path.join(os.path.dirname(os.path.abspath(BRD)), 'library', 'linknode.pretty') if lib == 'linknode' else f'/usr/share/kicad/footprints/{lib}.pretty'
    f = pcbnew.FootprintLoad(path, name); assert f, d['fp']
    f.SetReference(ref); f.SetValue(d['value']); f.SetFPIDAsString(d['fp'])
    f.SetPath(pcbnew.KIID_PATH(d['sheet'][1] + d['uid']))
    f.SetSheetname(d['sheet'][0].strip('/')); f.SetSheetfile(d['sheetfile'])
    f.Reference().SetVisible(False)
    for k in ('Datasheet', 'Description', 'LCSC'):
        if d['fields'].get(k):
            f.SetField(k, d['fields'][k]); fld = f.GetField(k); fld.SetVisible(False); fld.SetLayer(pcbnew.F_Fab)
    b.Add(f); FP[ref] = f; added.append(ref)
# --- nets for every pad
newnets = 0; changed = 0
for ref, f in FP.items():
    for p in f.Pads():
        n = pinnet.get((ref, p.GetNumber()))
        if n is None or p.GetNumber() == '': continue
        if p.GetNetname() == n: continue
        ni = b.FindNet(n)
        if ni is None: ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); newnets += 1
        p.SetNet(ni); changed += 1
# --- pogo pads
MH1 = FP['MH1'].GetPosition()
NPADS = sum(1 for r in FP if re.fullmatch(r'TP10\d\d', r))   # 28 (T49), 35 with the audio row (T50)
for n in range(1, NPADS + 1):
    f = FP[f'TP10{n:02d}']; row, col = (n - 1) // 7, (n - 1) % 7
    f.SetPosition(pcbnew.VECTOR2I(MH1.x + mm(56.0 + 2.54 * col), MH1.y + mm(27.2 + 2.54 * row)))
    if not f.IsFlipped(): f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    f.SetOrientationDegrees(0)
# --- ESD, 0R, pull-ups on the bottom next to their pads
T = lambda *ns: [(f'TP10{n:02d}', '1', 1.0) for n in ns]
MOVES = [('U1001', 'B', 8, T(9, 10, 11, 12)), ('U1002', 'B', 8, T(15, 16, 17, 18)), ('U1003', 'B', 8, T(19, 20, 21, 22)),
         ('U1004', 'B', 8, T(23, 24, 25, 26)), ('U1005', 'B', 8, T(27)),
         ('R1001', 'B', 8, T(1)), ('R1002', 'B', 8, T(2)), ('R1003', 'B', 8, T(4)), ('R1004', 'B', 8, T(5)),
         ('R1005', 'B', 8, T(9)), ('R1006', 'B', 8, T(10)), ('R1007', 'B', 8, T(11)), ('R1008', 'B', 8, T(12))]
if 'U1006' in FP:   # T50 audio row: mic ESD + 1 uF series caps (HDG Table 2-12) next to pads 29-33
    MOVES += [('U1006', 'B', 8, T(29, 30, 32, 33)), ('C1001', 'B', 8, T(29)), ('C1002', 'B', 8, T(30)), ('C1003', 'B', 8, T(32)), ('C1004', 'B', 8, T(33))]
KEEP = [('B', (161.9, 137.6, 167.7, 142.0))]   # ESP32-C5 ground-pad vias (U801 pad 29 at y 137.78..141.18, top)
rep = place_moves(b, MOVES, keepout=KEEP)
b.Save(BRD)
print(json.dumps(dict(added=len(added), new_nets=newnets, pads_renetted=changed, placed=rep)))
