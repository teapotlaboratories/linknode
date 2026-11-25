import pcbnew, sys
src, dst = sys.argv[1], sys.argv[2]
io = pcbnew.PCB_IO_MGR.FindPlugin(pcbnew.PCB_IO_MGR.ALTIUM_DESIGNER)
names = io.FootprintEnumerate(src)
print('footprints:', list(names))
kio = pcbnew.PCB_IO_MGR.FindPlugin(pcbnew.PCB_IO_MGR.KICAD_SEXP)
import os
os.makedirs(dst, exist_ok=True)
for n in names:
    fp = io.FootprintLoad(src, n)
    print(n, 'pads', len(fp.Pads()))
    for p in sorted(fp.Pads(), key=lambda p: (len(p.GetNumber()), p.GetNumber())):
        pos = p.GetPosition(); sz = p.GetSize()
        print('  pad', p.GetNumber(), round(pcbnew.ToMM(pos.x), 3), round(pcbnew.ToMM(pos.y), 3), 'size', round(pcbnew.ToMM(sz.x), 3), round(pcbnew.ToMM(sz.y), 3), p.GetShape(), p.GetAttribute())
    kio.FootprintSave(dst, fp)
