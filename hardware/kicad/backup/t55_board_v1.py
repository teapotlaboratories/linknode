"""T55 (owner, 2026-11-24, plan approved, page section exp3): expansion v3 on the board. Two 24-pin 0.5 mm FPC connectors
(JUSHUO AFC07-S24ECC-00, LCSC C11092) on the bottom replace the 35 pogo pads TP1001..TP1035.
Usage: python3 t55_board.py <in.kicad_pcb> <out.kicad_pcb> <netlist.xml>   (netlist exported from the new schematic)
- removes TP1001..TP1035;
- adds J1001 (FPC A, under the GPS: flipped, 0 deg, pads south, pin 1 west, opening north), J1002 (FPC B, under the microSD
  socket: flipped, 180 deg, pads north, pin 1 east, opening south to the bottom edge) and U1007 (TPD4E05U06DQAR), linked to their symbols;
- sets the net of every pad of the expansion parts from the netlist (new and renamed nets included);
- moves the ESD arrays, 0R links, I2C pull-ups and mic capacitors next to their connector (PLACE below).
Prints each part's final position and pad 1; DRC (courtyards, clearances) is the check afterwards."""
import sys, os, pcbnew, xml.etree.ElementTree as ET
IN, OUT, NETL = sys.argv[1:4]
LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kicad', 'library', 'linknode.pretty')
SON = '/usr/share/kicad/footprints/Package_SON.pretty'
SHEET = '/d95cb237-0177-4440-a7e6-29dc79faada9/3a2925e3-54eb-4721-b2a4-d259e048c5a9'   # root / expansion sheet
b = pcbnew.LoadBoard(IN); KEEP = []
r = ET.parse(NETL).getroot()
comp = {c.get('ref'): c for c in r.iter('comp')}
pin_net = {}
for n in r.iter('net'):
    for x in n.iter('node'): pin_net[(x.get('ref'), x.get('pin'))] = n.get('name')
# 1. pogo pads out
gone = [f for f in b.GetFootprints() if f.GetReference().startswith('TP10') and len(f.GetReference()) == 6]
for f in gone: b.Remove(f); KEEP.append(f)
# 2. new footprints
NEW = {'J1001': (LIB, 'Jushuo_AFC07-S24ECC-00_1x24-1MP_P0.50_Horizontal'), 'J1002': (LIB, 'Jushuo_AFC07-S24ECC-00_1x24-1MP_P0.50_Horizontal'),
       'U1007': (SON, 'USON-10_2.5x1.0mm_P0.5mm')}
for ref, (lib, name) in NEW.items():
    if any(f.GetReference() == ref for f in b.GetFootprints()): continue
    fp = pcbnew.FootprintLoad(lib, name); c = comp[ref]
    fp.SetReference(ref); fp.SetValue(c.findtext('value'))
    if ref.startswith('J'): fp.SetFPID(pcbnew.LIB_ID('linknode', name))
    else: fp.SetFPID(pcbnew.LIB_ID('Package_SON', name))
    for fl in c.iter('field'):
        if fl.get('name') in ('LCSC', 'Description', 'Datasheet'): fp.SetField(fl.get('name'), fl.text or '')
    uid = (c.find('tstamps').text or '').split()[0]                      # multi-unit: the first unit's UUID
    fp.SetPath(pcbnew.KIID_PATH(SHEET + '/' + uid))
    b.Add(fp)
FP = {f.GetReference(): f for f in b.GetFootprints()}
# 3. placement (bottom side). (x, y, rot): rot is the orientation after flipping, as KiCad stores it.
PLACE = {
    'J1001': (164.0, 117.0, 0), 'J1002': (146.0, 151.8, 180),   # flipped: 0 deg = pads south, pin 1 west; J1002 1.2 mm north of the
                                                                 # microSD peg holes (141.82/149.82, 156.6)
    # FPC A side: ESD arrays (rot 90 = long axis east-west) in a row under the pad row, Ethernet 0R links upright west of them,
    # I2C pull-ups in a column east of the connector (x <= 175.55, the 2.5 mm right-edge rule)
    'U1002': (161.0, 120.8, 270), 'U1003': (164.2, 120.8, 270), 'U1001': (167.4, 120.8, 270),   # 270: pin 1 west = contact order
    'R1001': (155.4, 121.6, 90), 'R1002': (156.45, 121.6, 90), 'R1003': (157.5, 121.6, 90), 'R1004': (158.55, 121.6, 90),
    'R1005': (174.4, 115.5, 0), 'R1006': (174.4, 116.6, 0), 'R1007': (174.4, 117.7, 0), 'R1008': (174.4, 118.8, 0),
    # FPC B side: ESD arrays in a row north of the pad row, mic capacitors upright north of them (clear of C401)
    'U1007': (140.4, 148.05, 270), 'U1006': (144.0, 148.05, 270), 'U1004': (147.15, 148.05, 270), 'U1005': (150.3, 148.05, 270),
    'C1001': (137.9, 146.0, 90), 'C1002': (139.0, 146.0, 90), 'C1003': (140.1, 146.0, 90), 'C1004': (141.2, 146.0, 90),
}
for ref, (x, y, rot) in PLACE.items():
    f = FP[ref]
    if not f.IsFlipped(): f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))); f.SetOrientationDegrees(rot)
# silkscreen: the bottom branding group (LOGO1, "Teapotlabs", "LinkNode", T46) 1.5 mm north, keeping its offsets, off J1001;
# the bottom "REVISION 1" text from under J1001 to the free area below the ESP32-C5. Designators of the new parts hidden (T45).
UP = pcbnew.VECTOR2I(0, pcbnew.FromMM(-1.5))
FP['LOGO1'].SetPosition(FP['LOGO1'].GetPosition() + UP)
for d in b.GetDrawings():
    if d.GetClass() == 'PCB_TEXT' and d.GetLayer() == pcbnew.B_SilkS:
        if d.GetText() in ('Teapotlabs', 'LinkNode'): d.SetPosition(d.GetPosition() + UP)
        if d.GetText() == 'REVISION 1': d.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(164.0), pcbnew.FromMM(153.3)))
for ref in NEW:
    FP[ref].Reference().SetVisible(False)
    for fl in FP[ref].GetFields():                     # added fields (LCSC, Description, Datasheet) must not print on silk
        if fl.GetName() not in ('Reference', 'Value', 'Footprint'): fl.SetVisible(False)
# 4. nets from the netlist
NI = b.GetNetInfo()
def net(name):
    n = b.FindNet(name)
    if n is None: n = pcbnew.NETINFO_ITEM(b, name); b.Add(n)
    return n
touched = 0
for ref in [f.GetReference() for f in b.GetFootprints()]:
    if not (ref in NEW or (ref[:3] in ('U10', 'R10', 'C10') and len(ref) == 5 and ref[3] == '0')): continue
    for p in FP[ref].Pads():
        name = pin_net.get((ref, p.GetNumber()))
        if name is None: continue
        if p.GetNetname() != name: p.SetNet(net(name)); touched += 1
b.Save(OUT)
print('removed', len(gone), 'pads; nets set on', touched, 'pads')
for ref in ('J1001', 'J1002', 'U1007'):
    f = FP[ref]; p1 = [p for p in f.Pads() if p.GetNumber() == '1'][0]
    print(ref, 'at', round(f.GetPosition().x/1e6, 3), round(f.GetPosition().y/1e6, 3), 'rot', f.GetOrientationDegrees(), 'flipped', f.IsFlipped(),
          'pad1', round(p1.GetPosition().x/1e6, 3), round(p1.GetPosition().y/1e6, 3), p1.GetNetname())
