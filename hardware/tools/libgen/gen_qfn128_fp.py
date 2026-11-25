"""Generate linknode:Rockchip_QFN-128-1EP_12.3x12.3mm_P0.35mm_EP7x7mm.

Source: Rockchip RV1106 Datasheet V1.3, Fig 2-3/2-4 (p.16) and Fig 2-5 (p.17):
D = E = 12.3 BSC, e = 0.35, b = 0.08/0.13/0.18, L = 0.3/0.4/0.5, D2 = E2 = 6.9/7.0/7.1, 32 pins per side,
pin 1 at the top of the left side (top view), counter-clockwise.
Land: pad width = b max (0.18, gap 0.17); pad from (D/2 - Lmax - 0.05) to (D/2 + 0.25) => 0.80 long, centre 6.00.
"""
import sys
out = sys.argv[1]
NAME = 'Rockchip_QFN-128-1EP_12.3x12.3mm_P0.35mm_EP7x7mm'
D, e, N = 12.3, 0.35, 32
PW, PL, PC = 0.18, 0.80, 6.00
EP = 7.0
f = lambda v: ('%.4f' % v).rstrip('0').rstrip('.') if abs(v) > 1e-9 else '0'

def pad(num, x, y, w, h):
    return ('\t(pad "%s" smd roundrect\n\t\t(at %s %s)\n\t\t(size %s %s)\n\t\t(layers "F.Cu" "F.Paste" "F.Mask")\n'
            '\t\t(roundrect_rratio 0.25)\n\t)\n') % (num, f(x), f(y), f(w), f(h))

pads = []
o = (N - 1) / 2 * e
TRIM = 0.05   # corner pads: inner end shortened so the diagonal gap to the next side's pad is >= 0.15 mm
for i in range(N):
    d = -o + i * e
    t = TRIM if i in (0, N - 1) else 0
    c, l = PC + t / 2, PL - t
    pads.append(pad(1 + i, -c, d, l, PW))              # left, top -> bottom
    pads.append(pad(33 + i, d, c, PW, l))              # bottom, left -> right
    pads.append(pad(65 + i, c, -d, l, PW))             # right, bottom -> top
    pads.append(pad(97 + i, -d, -c, PW, l))            # top, right -> left
# exposed pad: copper + mask, paste in 3x3 windows, 16 thermal vias in the gaps
pads.append('\t(pad "129" smd rect\n\t\t(at 0 0)\n\t\t(size %s %s)\n\t\t(layers "F.Cu" "F.Mask")\n\t\t(zone_connect 2)\n\t)\n' % (f(EP), f(EP)))
for cx in (-2.4, 0, 2.4):
    for cy in (-2.4, 0, 2.4):
        pads.append('\t(pad "" smd roundrect\n\t\t(at %s %s)\n\t\t(size 1.8 1.8)\n\t\t(layers "F.Paste")\n\t\t(roundrect_rratio 0.1)\n\t)\n' % (f(cx), f(cy)))
vias = set()
for g in (-1.2, 1.2):
    for t in (-2.4, -1.2, 0, 1.2, 2.4):
        vias.add((g, t)); vias.add((t, g))
for x, y in sorted(vias):
    pads.append('\t(pad "129" thru_hole circle\n\t\t(at %s %s)\n\t\t(size 0.5 0.5)\n\t\t(drill 0.3)\n\t\t(layers "*.Cu")\n\t\t(zone_connect 2)\n\t)\n' % (f(x), f(y)))
assert len(vias) == 16, len(vias)

h = D / 2
cy = PC + PL / 2 + 0.25            # courtyard
sk = h + 0.11                      # silk just outside the body
tick = 0.6
silk = ''
for sx in (-1, 1):
    for sy in (-1, 1):
        if sx == -1 and sy == -1:
            continue
        silk += '\t(fp_line (start %s %s) (end %s %s) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))\n' % (f(sx * sk), f(sy * sk), f(sx * (sk - tick)), f(sy * sk))
        silk += '\t(fp_line (start %s %s) (end %s %s) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))\n' % (f(sx * sk), f(sy * sk), f(sx * sk), f(sy * (sk - tick)))
silk += '\t(fp_circle (center %s %s) (end %s %s) (stroke (width 0.2) (type solid)) (fill solid) (layer "F.SilkS"))\n' % (f(-cy - 0.1), f(-o), f(-cy - 0.1 + 0.15), f(-o))
fab = ('\t(fp_poly (pts (xy %s %s) (xy %s %s) (xy %s %s) (xy %s %s) (xy %s %s)) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))\n'
       % (f(-h + 1), f(-h), f(h), f(-h), f(h), f(h), f(-h), f(h), f(-h), f(-h + 1)))
crt = '\t(fp_rect (start %s %s) (end %s %s) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))\n' % (f(-cy), f(-cy), f(cy), f(cy))
s = '''(footprint "%s"
\t(version 20241229)
\t(generator "linknode_gen_qfn128")
\t(layer "F.Cu")
\t(descr "Rockchip RV1106 QFN-128, 12.3x12.3 mm body, 0.35 mm pitch, 7x7 mm exposed pad. RV1106 Datasheet V1.3 Fig 2-3..2-5 p.16-17. Pads 0.18x0.80 mm at 6.00 mm (bmax; Lmax + 0.25 toe + 0.05 heel); EP paste 3x3 windows 1.8 mm (66 %%); 16 thermal vias 0.3/0.5 mm in the paste gaps. Corner pads 0.75 long (inner end trimmed 0.05) for 0.15 mm corner clearance.")
\t(tags "QFN-128 RV1106 Rockchip 0.35mm")
\t(property "Reference" "REF**" (at 0 %s 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
\t(property "Value" "%s" (at 0 %s 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
\t(property "Footprint" "" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1.27 1.27))))
\t(property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1.27 1.27))))
\t(property "Description" "" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1.27 1.27))))
\t(attr smd)
%s%s%s\t(fp_text user "${REFERENCE}" (at 0 0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
%s)
''' % (NAME, f(-cy - 1.2), NAME, f(cy + 1.2), silk, fab, crt, ''.join(pads))
open(out, 'w').write(s)
print('pads', s.count('(pad "') - 9, 'courtyard', 2 * cy)
