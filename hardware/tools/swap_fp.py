"""Swap footprints in place (T33, 2026-11-22). Keeps reference, value, fields, schematic path (parity), sheet,
position, orientation, side and pad nets (by pad number). Attributes (SMD/THT, BOM, position files) come from the new footprint. Refills zones and saves.
Usage: swap_fp.py board.kicad_pcb REF=Lib:Footprint [REF=Lib:Footprint ...]"""
import sys, os, traceback, pcbnew
sys.excepthook = lambda *e: (traceback.print_exception(*e), sys.stderr.flush(), os._exit(1))
SYS = '/usr/share/kicad/footprints'
b = pcbnew.LoadBoard(sys.argv[1]); keep = []
for arg in sys.argv[2:]:
    ref, fpid = arg.split('='); lib, name = fpid.split(':')
    old = b.FindFootprintByReference(ref)
    path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), 'library', 'linknode.pretty') if lib == 'linknode' else os.path.join(SYS, lib + '.pretty')
    new = pcbnew.FootprintLoad(path, name)
    assert new, fpid
    new.SetFPID(pcbnew.LIB_ID(lib, name))
    new.SetReference(old.GetReference()); new.SetValue(old.GetValue())
    for fld in old.GetFields():
        n = fld.GetName()
        if n in ('Reference', 'Value', 'Footprint'): continue
        new.SetField(n, fld.GetText())
        nf = new.GetField(n)
        if nf: nf.SetVisible(fld.IsVisible())
    new.SetPath(old.GetPath()); new.SetSheetname(old.GetSheetname()); new.SetSheetfile(old.GetSheetfile())
    b.Add(new)
    if old.IsFlipped(): new.Flip(new.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    new.SetOrientationDegrees(old.GetOrientationDegrees()); new.SetPosition(old.GetPosition())
    nets = {p.GetNumber(): p.GetNet() for p in old.Pads()}
    for p in new.Pads():
        if p.GetNumber() in nets: p.SetNet(nets[p.GetNumber()])
    print(ref, old.GetFPIDAsString(), '->', new.GetFPIDAsString(), [(p.GetNumber(), p.GetNetname()) for p in new.Pads()])
    keep.append(old); b.Remove(old)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1])
