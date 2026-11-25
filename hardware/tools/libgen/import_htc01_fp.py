"""Import Heltec's Altium footprint for the HT-HC01 V2 into linknode.pretty.
Source: https://resource.heltec.cn/download/Heltec_Module_Footprint/HT-HC01_V2/HT-HC01_V2.PcbLib (linked from the
datasheet p.19), converted with pcbnew's Altium reader (PCB_IO_MGR.ALTIUM_DESIGNER) to conv.pretty/HT-HC01_V2.kicad_mod.
This script: drops the Altium mechanical-layer items (User.2), adds a courtyard and a body outline (18.5 x 14 mm,
datasheet p.19), sets the description. Pads are untouched: 38 castellated pads 1.5 mm pitch + two "0" GND pads."""
import re, sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()
def drop_layer(s, layer):
    out = []; i = 0
    while True:
        m = re.search(r'\n\t\((fp_\w+)\b', s[i:])
        if not m: out.append(s[i:]); break
        a = i + m.start(); d = 0
        for j in range(a + 1, len(s)):
            if s[j] == '(': d += 1
            elif s[j] == ')':
                d -= 1
                if d == 0: break
        blk = s[a:j + 1]
        out.append(s[i:a]); out.append('' if '(layer "%s")' % layer in blk else blk); i = j + 1
    return ''.join(out)
s = drop_layer(s, 'User.2')
s = re.sub(r'\(descr "[^"]*"\)', '', s)
extra = ('\t(descr "Heltec HT-HC01 V2 Wi-Fi HaLow module (MM6108 + FEM), 18.5 x 14 mm, 38 castellated pads 1.5 mm pitch + 2 bottom GND pads (pad 0). Converted from Heltec\'s HT-HC01_V2.PcbLib (datasheet p.19 link).")\n'
         '\t(tags "Heltec HaLow MM6108 module")\n'
         '\t(fp_rect (start -9.25 -7) (end 9.25 7) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))\n'
         '\t(fp_rect (start -10.2 -7.9) (end 10.2 7.9) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))\n')
i = s.index('\n', s.index('(layer "F.Cu")')) + 1
s = s[:i] + extra + s[i:]
open(dst, 'w').write(s)
print('pads', s.count('(pad '), 'User.2 left', s.count('User.2'))
