"""T60 (owner 2026-11-25: "lets try it"): ESP32-C5 module U801 from 180° to 0°, body in the same place.
Usage: python3 t60_c5rot.py <in.kicad_pcb> <out.kicad_pcb>
The footprint anchor is not the pad centre, so the module is turned 180° about its anchor and then moved 0.5 mm west: the body
keeps its old outline (right-edge margin 2.5 mm). Its bottom parts (C801/R801 EN RC, C802/C803 3V3 decoupling, R802 BOOT
pull-up) get the same transform (+180°), so each stays at its pin. All tracks and vias of the ten C5 signal nets are removed
(FPC A and everything else stay) for re-routing."""
import sys, pcbnew
IN, OUT = sys.argv[1:3]; MM = pcbnew.FromMM
b = pcbnew.LoadBoard(IN)
u = b.FindFootprintByReference('U801'); a = u.GetPosition(); ax, ay = a.x, a.y
DX = MM(-0.5)
def T(x, y): return (2*ax - x + DX, 2*ay - y)
before = u.GetCourtyard(pcbnew.F_CrtYd).BBox()
for ref in ('U801', 'C801', 'C802', 'C803', 'R801', 'R802'):
    f = b.FindFootprintByReference(ref); p = f.GetPosition(); nx, ny = T(p.x, p.y)
    f.SetPosition(pcbnew.VECTOR2I(int(nx), int(ny))); f.SetOrientationDegrees((f.GetOrientationDegrees() + 180) % 360)
after = u.GetCourtyard(pcbnew.F_CrtYd).BBox()
print('U801 courtyard before', [round(v/1e6, 3) for v in (before.GetLeft(), before.GetTop(), before.GetRight(), before.GetBottom())],
      'after', [round(v/1e6, 3) for v in (after.GetLeft(), after.GetTop(), after.GetRight(), after.GetBottom())], 'orientation', u.GetOrientationDegrees())
NETS = {'/ESP32-C5/C5_' + n for n in ('SPI_CLK', 'SPI_CS', 'SPI_MOSI', 'SPI_MISO', 'EN', 'BOOT', 'DATA_READY', 'HANDSHAKE', 'UART_RX', 'UART_TX')}
gone = 0
for t in list(b.GetTracks()):
    if t.GetNetname() in NETS: b.Remove(t); gone += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(OUT); print('C5 tracks/vias removed:', gone)
for p in sorted(u.Pads(), key=lambda p: (round(p.GetPosition().x/1e6), p.GetPosition().y)):
    n = p.GetNetname().split('/')[-1]
    if n.startswith('C5_') or n in ('VCC3V3_C5',): print('  pin', p.GetNumber(), n, round(p.GetPosition().x/1e6, 3), round(p.GetPosition().y/1e6, 3))
