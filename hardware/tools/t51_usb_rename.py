"""T51 (owner, 2026-11-23): USB nets renamed so KiCad sees them as differential pairs (net names ending P/N).
Usage: python3 t51_usb_rename.py <kicad dir>          (schematics, project, rules; minimal text edits)
       python3 t51_usb_rename.py <kicad dir> --board  (board nets: pads and tracks, after the schematic edit)
  /SoC/USB_DM                       -> /SoC/USB_DN            hierarchical labels (SoC, USB and Charger) + root sheet pins
  Net-(U100System-USB_DP / _DM)     -> /SoC/USB_SOC_DP / _DN  local labels on the existing U100 -> R508/R509 wires
  Net-(J1-D+-PadA6) / Net-(J1-D--PadA7) -> /USB and Charger/USB_CONN_DP / _DN  local labels on the J1 -> U1 wires
Labels only name wires that already connect (no connection made by a label)."""
import sys, os, re, uuid, json
K = sys.argv[1]
MAP = {'/SoC/USB_DM': '/SoC/USB_DN', 'Net-(U100System-USB_DP)': '/SoC/USB_SOC_DP', 'Net-(U100System-USB_DM)': '/SoC/USB_SOC_DN',
       'Net-(J1-D+-PadA6)': '/USB and Charger/USB_CONN_DP', 'Net-(J1-D--PadA7)': '/USB and Charger/USB_CONN_DN'}
if '--board' in sys.argv:
    import pcbnew
    P = os.path.join(K, 'linknode.kicad_pcb'); b = pcbnew.LoadBoard(P)
    for old, new in MAP.items():
        o = b.FindNet(old)
        if o is None: raise SystemExit('no net ' + old)
        n = b.FindNet(new)
        if n is None: n = pcbnew.NETINFO_ITEM(b, new); b.Add(n)
        k = 0
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.GetNetname() == old: p.SetNet(n); k += 1
        for t in b.GetTracks():
            if t.GetNetname() == old: t.SetNet(n); k += 1
        for z in b.Zones():
            if z.GetNetname() == old: z.SetNet(n); k += 1
        print('%-28s -> %-32s %d items' % (old, new, k))
    b.RemoveUnusedNets(None) if hasattr(b, 'RemoveUnusedNets') else None
    b.Save(P); raise SystemExit(0)
U = lambda: str(uuid.uuid4())
def label(name, x, y):
    return (f'\n\t(label "{name}"\n\t\t(at {x:g} {y:g} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            f'\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')
def on_wire(s, x, y):
    for m in re.finditer(r'\(wire\s*\(pts\s*\(xy ([\d.\-]+) ([\d.\-]+)\) \(xy ([\d.\-]+) ([\d.\-]+)\)', s):
        x1, y1, x2, y2 = map(float, m.groups())
        if abs(y1 - y) < 1e-6 and abs(y2 - y) < 1e-6 and min(x1, x2) < x < max(x1, x2): return True
    return False
def edit(fn, f):
    p = os.path.join(K, fn); s = open(p).read(); s2 = f(s); open(p, 'w').write(s2); print('edited', fn)
def soc(s):
    assert s.count('(hierarchical_label "USB_DM"') == 1
    s = s.replace('(hierarchical_label "USB_DM"', '(hierarchical_label "USB_DN"')
    add = ''
    for name, y in (("USB_SOC_DP", 76.2), ("USB_SOC_DN", 78.74)):          # wires U100 (x 114.3) -> R508/R509 pin 1 (134.62); clear of the GND text under R507
        assert on_wire(s, 115.57, y), name                 # label anchored at the wire's U100 end (114.3)
        add += label(name, 114.3, y)
    k = s.index('\n\t(wire'); return s[:k] + add + s[k:]
def usbchg(s):
    assert s.count('(hierarchical_label "USB_DM"') == 1
    s = s.replace('(hierarchical_label "USB_DM"', '(hierarchical_label "USB_DN"')
    add = ''
    for name, y in (('USB_CONN_DN', 76.2), ('USB_CONN_DP', 78.74)):       # wires J1 D-/D+ (x 40.64) -> U1 pins 1/3 (73.66)
        assert on_wire(s, 55.88, y), name
        add += label(name, 55.88, y)
    k = s.index('\n\t(wire'); return s[:k] + add + s[k:]
def root(s):
    assert s.count('(pin "USB_DM" bidirectional') == 2
    return s.replace('(pin "USB_DM" bidirectional', '(pin "USB_DN" bidirectional')
def pro(s):
    for old, new in MAP.items():
        assert s.count(f'"pattern": "{old}"') == 1, old
        s = s.replace(f'"pattern": "{old}"', f'"pattern": "{new}"')
    return s
def dru(s):
    for old, new in MAP.items(): s = s.replace(f"'{old}'", f"'{new}'")
    return s
edit('soc.kicad_sch', soc); edit('usb_and_charger.kicad_sch', usbchg); edit('linknode.kicad_sch', root)
edit('linknode.kicad_pro', pro); edit('linknode.kicad_dru', dru)
