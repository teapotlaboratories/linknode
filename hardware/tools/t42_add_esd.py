"""T42: add the microSD ESD arrays U401/U402 (TPD4E05U06DQAR) to the board and place them at the socket (HDG §3.3.1).
Usage: python3 t42_add_esd.py <board.kicad_pcb>. Paths/fields/nets mirror microsd.kicad_sch (checked by DRC parity)."""
import sys, os, json, pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from placelib import place_moves
b = pcbnew.LoadBoard(sys.argv[1])
SHEET = '/48504eac-3d02-4d0d-9f40-71572c492bc9/'
DESC = ('4-channel ESD array for the microSD lines (HDG §3.3.1: < 1 pF at the connector). DOWO TPD4E05U06DQAR: '
        'C(I/O-GND) 0.5 pF max, VRWM 5.0 V (datasheet p.2); pin-compatible with TI TPD4E05U06 DQA.')
PARTS = {'U401': ('07cacadb-6d6a-43ec-8173-c142b5a29101', {'1': '/SoC/SD_CMD', '2': '/SoC/SD_CLK', '3': 'GND', '4': '/SoC/SD_D1',
                  '5': '/SoC/SD_D0', '8': 'GND', '6': 'unconnected-(U401-NC-Pad6)', '7': 'unconnected-(U401-NC-Pad7)',
                  '9': 'unconnected-(U401-NC-Pad9)', '10': 'unconnected-(U401-NC-Pad10)'}),
         'U402': ('ac93c24e-0e96-4d14-bb3e-82f9855b8ea5', {'1': '/SoC/SD_D2', '2': 'unconnected-(U402-D1--Pad2)', '3': 'GND',
                  '4': 'Net-(J401-DET)', '5': '/SoC/SD_D3', '8': 'GND', '6': 'unconnected-(U402-NC-Pad6)',
                  '7': 'unconnected-(U402-NC-Pad7)', '9': 'unconnected-(U402-NC-Pad9)', '10': 'unconnected-(U402-NC-Pad10)'})}
for ref, (uid, nets) in PARTS.items():
    assert b.FindFootprintByReference(ref) is None, ref
    f = pcbnew.FootprintLoad('/usr/share/kicad/footprints/Package_SON.pretty', 'USON-10_2.5x1.0mm_P0.5mm')
    f.SetReference(ref); f.SetValue('TPD4E05U06DQAR')
    f.SetFPIDAsString('Package_SON:USON-10_2.5x1.0mm_P0.5mm')
    f.SetPath(pcbnew.KIID_PATH(SHEET + uid)); f.SetSheetname('microSD'); f.SetSheetfile('microsd.kicad_sch')
    f.Reference().SetVisible(False)
    for k, v in (('Datasheet', 'hardware/datasheets/DOWO_TPD4E05U06DQAR.pdf'), ('Description', DESC), ('LCSC', 'C22390021')):
        f.SetField(k, v); fld = f.GetField(k); fld.SetVisible(False); fld.SetLayer(pcbnew.F_Fab)
    b.Add(f)
    for p in f.Pads():
        n = nets.get(p.GetNumber())
        if n is None: continue
        ni = b.FindNet(n)
        if ni is None: ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni)
        p.SetNet(ni)
# place on top behind the socket's signal pads, each pad next to the socket pin it protects
MOVES = [('U401', 'F', 6, [('J401', '5', 1.0), ('J401', '3', 1.0), ('J401', '7', 1.0), ('J401', '8', 1.0)]),
         ('U402', 'F', 6, [('J401', '1', 1.0), ('J401', '2', 1.0), ('J401', '9', 1.0)])]
rep = place_moves(b, MOVES)
b.Save(sys.argv[1]); print(json.dumps(rep))
