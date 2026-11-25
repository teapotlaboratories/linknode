"""Generate linknode:microSD_ShouHan_TF-PUSH (LCSC C393941, SHOU HAN "TF PUSH").
Source: C393941 datasheet p.1 "Recommended P.C.B hole layout, component side view (tol +/-0.05)"
(hardware/datasheets/ShouHan_TF-PUSH.pdf). Origin = midpoint of the two 1.00 mm locating holes (8.00 apart).
Read from the drawing: signal pads 0.70 x 1.60 (Cd 0.60 x 1.60) at 1.10 pitch, pad row centre 11.0 above the holes
(edges at 10.20 / ~11.8); shell pads 1.20 x 1.50 (top, bottom edge 9.25 above holes; right one 1.50 wide, 3.00 right of
the right hole) and 1.20 x 2.20 (bottom, bottom edge 0.70 below holes; left one 2.20 left of the left hole, right one
12.10 right of the left hole). Pad positions and sizes re-measured at T15 from the drawing's vector data (page rotated 270; hole pitch 66.0 pt = 8.00 mm,
8.25 pt/mm): Cd 0.70 wide at -5.60, pins 8..1 at -4.50..+3.20 (1.10 pitch), top-right shell 1.60 x 1.50 at +7.80; all within 0.01 mm."""
import sys
out = sys.argv[1]
f = lambda v: ('%.3f' % v).rstrip('0').rstrip('.') if abs(v) > 1e-9 else '0'
pads = []
def smd(num, x, y, w, h):
    pads.append('\t(pad "%s" smd rect (at %s %s) (size %s %s) (layers "F.Cu" "F.Paste" "F.Mask"))\n' % (num, f(x), f(y), f(w), f(h)))
smd('9', -5.60, -11.0, 0.70, 1.60)                       # Cd (card detect)
for k, num in enumerate(['8', '7', '6', '5', '4', '3', '2', '1']):
    smd(num, -4.50 + 1.10 * k, -11.0, 0.70, 1.60)
smd('SH', -6.80, -10.0, 1.20, 1.50); smd('SH', 7.80, -10.0, 1.60, 1.50)
smd('SH', -6.80, -0.40, 1.20, 2.20); smd('SH', 8.70, -0.40, 1.20, 2.20)
for x in (-4.0, 4.0):
    pads.append('\t(pad "" np_thru_hole circle (at %s 0) (size 1 1) (drill 1) (layers "*.Cu" "*.Mask"))\n' % f(x))
x0, x1, y0, y1 = -7.9, 9.8, -12.3, 3.6
s = '''(footprint "microSD_ShouHan_TF-PUSH"
\t(version 20241229)
\t(generator "linknode_gen_tfpush")
\t(layer "F.Cu")
\t(descr "microSD push-push socket SHOU HAN TF PUSH (LCSC C393941), card detect pad 9 (Cd), shell pads SH. Land pattern from the C393941 datasheet p.1; pads measured from the drawing's vector data (T15).")
\t(tags "microSD TF socket push-push C393941")
\t(property "Reference" "REF**" (at 0 -13.6 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
\t(property "Value" "TF PUSH" (at 0 4.8 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
\t(attr smd)
\t(fp_rect (start -6.425 -10.95) (end 8.325 3.55) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))
\t(fp_line (start -6.425 3.55) (end 8.325 3.55) (stroke (width 0.12) (type dash)) (layer "F.Fab"))
\t(fp_text user "card in" (at 0.95 2.5 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))
\t(fp_rect (start %s %s) (end %s %s) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
\t(fp_text user "${REFERENCE}" (at 0.95 -5 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
%s)
''' % (f(x0), f(y0), f(x1), f(y1), ''.join(pads))
open(out, 'w').write(s)
print('pads', s.count('(pad '))
