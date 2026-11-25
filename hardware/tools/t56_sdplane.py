"""T56 (owner approved, 2026-11-24): GND reference for the bottom-layer microSD bus (Rockchip RV1103G/RV1106G HDG V1.1
§3.3.1 p.46 "The signal takes GND as the reference plane"; §3.2 (3)/(6)/(25) p.39-46: no split, no change of reference plane).
Adds an In2.Cu GND zone (priority 3, above VDD_0V9 = 1 and VCC5V0_SYS = 0) whose outline is the union of every bottom-layer
SD bus track and SD via grown by MARGIN (track centre to corridor edge), so the bus no longer runs over the VDD_0V9 island
and no longer crosses the 0V9 / 5 V split. Zone settings copy the In1 GND plane. GND through-vias inside it tie it to In1.
Usage: python3 t56_sdplane.py <in.kicad_pcb> <out.kicad_pcb> [margin_mm, default 1.1] [--nets N1,N2,...] [--name ZONE] [--prio 3]
T59 (2026-11-24): --nets/--name reuse it for the HaLow SDIO bus (zone SDIO_GND_REF)."""
import sys, pcbnew
a = sys.argv[1:]; opt = {}
for k in ('--nets', '--name', '--prio'):
    if k in a: i = a.index(k); opt[k] = a[i+1]; del a[i:i+2]
IN, OUT = a[0:2]; MARGIN = float(a[2]) if len(a) > 2 else 1.1
SD = ['/SoC/SD_CLK', '/SoC/SD_CMD', '/SoC/SD_D0', '/SoC/SD_D1', '/SoC/SD_D2', '/SoC/SD_D3', 'Net-(U100SD and SPI1-SDMMC_CLK{slash}GPIO3_A4)']
if '--nets' in opt: SD = opt['--nets'].split(',')
ZNAME = opt.get('--name', 'SD_GND_REF'); PRIO = int(opt.get('--prio', 3))
b = pcbnew.LoadBoard(IN); FM = pcbnew.FromMM
In1, In2, Bc = b.GetLayerID('In1.Cu'), b.GetLayerID('In2.Cu'), b.GetLayerID('B.Cu')
sp = pcbnew.SHAPE_POLY_SET(); n = 0
for t in b.GetTracks():
    if t.GetNetname() not in SD: continue
    if t.Type() == pcbnew.PCB_VIA_T:
        r = FM(MARGIN); c = t.GetPosition()
        circ = pcbnew.SHAPE_POLY_SET(); circ.NewOutline()
        import math
        for k in range(32): circ.Append(int(c.x + r*math.cos(2*math.pi*k/32)), int(c.y + r*math.sin(2*math.pi*k/32)))
        sp.BooleanAdd(circ); n += 1
    elif t.GetLayer() == Bc:
        one = pcbnew.SHAPE_POLY_SET()
        t.TransformShapeToPolygon(one, Bc, FM(MARGIN) - t.GetWidth()//2, FM(0.01), pcbnew.ERROR_OUTSIDE)
        sp.BooleanAdd(one); n += 1
sp.Simplify()
print('items', n, 'outlines', sp.OutlineCount(), 'holes', [sp.HoleCount(i) for i in range(sp.OutlineCount())])
ref = [z for z in b.Zones() if z.GetNetname() == 'GND' and z.IsOnLayer(In1)][0]
zones = []
for i in range(sp.OutlineCount()):          # one zone per outline: a zone saves only its first outline (found T59)
    z = pcbnew.ZONE(b); z.SetLayer(In2); z.SetNet(b.FindNet('GND')); z.SetAssignedPriority(PRIO)
    z.SetZoneName(ZNAME if sp.OutlineCount() == 1 else f'{ZNAME}_{i+1}')
    z.SetLocalClearance(ref.GetLocalClearance()); z.SetMinThickness(ref.GetMinThickness()); z.SetPadConnection(ref.GetPadConnection())
    z.SetThermalReliefGap(ref.GetThermalReliefGap()); z.SetThermalReliefSpokeWidth(ref.GetThermalReliefSpokeWidth())
    z.SetIslandRemovalMode(ref.GetIslandRemovalMode()); z.SetFillMode(ref.GetFillMode())
    ol = z.Outline(); ol.RemoveAllContours()
    o = sp.Outline(i); ol.NewOutline()
    for j in range(o.PointCount()): ol.Append(o.CPoint(j).x, o.CPoint(j).y)
    for h in range(sp.HoleCount(i)):
        hh = sp.Hole(i, h); ol.NewHole()
        for j in range(hh.PointCount()): ol.Append(hh.CPoint(j).x, hh.CPoint(j).y, -1, h)
    b.Add(z); zones.append(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(OUT)
for z in zones:
    fp = z.GetFilledPolysList(In2); print(z.GetZoneName(), 'area mm2', round(fp.Area()/1e12, 1), 'fill pieces', fp.OutlineCount())
