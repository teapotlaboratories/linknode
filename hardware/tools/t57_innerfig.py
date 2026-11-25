"""T57 (owner, 2026-11-24: "show the inner layer pcb in the report as well ... for all blocks"): inner-layer figure of a board area.
Usage: python3 t57_innerfig.py <board.kicad_pcb> <out.png> x0,y0,x1,y1 [title] [--px 40] [--refs]
Two panels side by side: In1.Cu with the F.Cu tracks drawn over it (top signals reference In1), and In2.Cu with the
B.Cu tracks over it (bottom signals reference In2). Plane copper is KiCad's own zone fill (the board is refilled with
pcbnew's ZONE_FILLER first), coloured by net and labelled; white = no copper (splits, antipads, gaps). Inner-layer
tracks are drawn in their net colour, darker. Through vias and through-hole pads are the small dark dots.
Board mm -> px at --px px/mm. --refs labels ICs and connectors (footprints with 6+ pads). --only In1|In2 draws one panel."""
import sys, math, pcbnew
from PIL import Image, ImageDraw, ImageFont
a = sys.argv[1:]; opt = {}
pos = []
i = 0
while i < len(a):
    if a[i] == '--px': opt['px'] = float(a[i+1]); i += 2
    elif a[i] == '--refs': opt['refs'] = True; i += 1
    elif a[i] == '--only': opt['only'] = a[i+1]; i += 2
    else: pos.append(a[i]); i += 1
BRD, OUT, BOX = pos[0], pos[1], [float(v) for v in pos[2].split(',')]
TITLE = pos[3] if len(pos) > 3 else ''
PX = opt.get('px', 40); X0, Y0, X1, Y1 = BOX
FONT = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', int(s))
FONTR = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', int(s))
NETC = {'GND': (178, 208, 170), 'VCC5V0_SYS': (166, 199, 236), 'VDD_0V9': (243, 196, 124), 'VCC_3V3': (214, 178, 230),
        'VCC_1V8': (245, 170, 170), 'VCC_DDR': (160, 214, 214), 'VSYS': (236, 220, 140), 'VBAT': (205, 190, 160)}
PAL = [(190, 160, 220), (240, 160, 190), (150, 200, 200), (220, 200, 150), (170, 190, 240), (200, 220, 160)]
def ncol(n):
    if n in NETC: return NETC[n]
    return PAL[sum(map(ord, n)) % len(PAL)]
b = pcbnew.LoadBoard(BRD); pcbnew.ZONE_FILLER(b).Fill(b.Zones())
P = lambda x, y: ((x/1e6 - X0)*PX, (y/1e6 - Y0)*PX)
W, H = int((X1-X0)*PX), int((Y1-Y0)*PX)
def short(n):
    n = n.replace('{slash}', '/'); return n.split('/')[-1]
def panel(inner, outer, oname):
    L = b.GetLayerID(inner); LO = b.GetLayerID(outer)
    im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im)
    labels = []
    for z in sorted([z for z in b.Zones() if z.IsOnLayer(L) and z.GetNetname()], key=lambda z: z.GetAssignedPriority()):
        fp = z.GetFilledPolysList(L); c = ncol(z.GetNetname())
        for k in range(fp.OutlineCount()):
            o = fp.Outline(k); pts = [P(o.CPoint(j).x, o.CPoint(j).y) for j in range(o.PointCount())]
            if len(pts) > 2: d.polygon(pts, fill=c)
            for h in range(fp.HoleCount(k)):
                hh = fp.Hole(k, h); hp = [P(hh.CPoint(j).x, hh.CPoint(j).y) for j in range(hh.PointCount())]
                if len(hp) > 2: d.polygon(hp, fill='white')
            area = fp.Outline(k).Area()/1e12
            labels.append((area, z.GetNetname(), (fp, k)))
    # inner-layer tracks
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T or t.GetLayer() != L: continue
        c = tuple(int(v*0.55) for v in ncol(t.GetNetname()))
        d.line([P(t.GetStart().x, t.GetStart().y), P(t.GetEnd().x, t.GetEnd().y)], fill=c, width=max(1, int(t.GetWidth()/1e6*PX)))
    # outer-layer tracks over the plane (semi-transparent)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    oc = (200, 16, 46, 170) if outer == 'F.Cu' else (31, 79, 191, 170)
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T or t.GetLayer() != LO: continue
        w = max(1, int(t.GetWidth()/1e6*PX)); p1, p2 = P(t.GetStart().x, t.GetStart().y), P(t.GetEnd().x, t.GetEnd().y)
        od.line([p1, p2], fill=oc, width=w)
        for q in (p1, p2): od.ellipse((q[0]-w/2, q[1]-w/2, q[0]+w/2, q[1]+w/2), fill=oc)
    im = Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB'); d = ImageDraw.Draw(im)
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            x, y = P(t.GetPosition().x, t.GetPosition().y); r = max(1.5, 0.1*PX)
            d.ellipse((x-r, y-r, x+r, y+r), fill=(40, 40, 40))
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                x, y = P(p.GetPosition().x, p.GetPosition().y); r = max(2, p.GetDrillSize().x/2e6*PX)
                d.ellipse((x-r, y-r, x+r, y+r), outline=(40, 40, 40), width=2)
        if opt.get('refs') and len(f.Pads()) >= 6:
            x, y = P(f.GetPosition().x, f.GetPosition().y)
            if 0 < x < W and 0 < y < H: d.text((x, y), f.GetReference(), fill=(90, 90, 90), font=FONTR(max(11, PX*0.45)), anchor='mm')
    # plane labels: one per net, at the visible point of its largest piece farthest from any edge of that piece
    done = set()
    for area, n, (fp, k) in sorted(labels, key=lambda v: -v[0]):
        if n in done or area < 4: continue
        chains = [fp.Outline(k)] + [fp.Hole(k, h) for h in range(fp.HoleCount(k))]
        best = None; st = max(0.5, (X1 - X0)/40)
        y = Y0 + st
        while y < Y1:
            x = X0 + st
            while x < X1:
                q = pcbnew.VECTOR2I(int(x*1e6), int(y*1e6))
                if fp.Outline(k).PointInside(q) and not any(fp.Hole(k, h).PointInside(q) for h in range(fp.HoleCount(k))):
                    dm = min(math.sqrt(c.SquaredDistance(q, True)) for c in chains)/1e6
                    dm = min(dm, x - X0, X1 - x, y - Y0, Y1 - y)
                    if best is None or dm > best[0]: best = (dm, x, y)
                x += st
            y += st
        if not best or best[0] < 0.6: continue
        done.add(n); fs = max(14, PX*0.55); px_, py_ = (best[1] - X0)*PX, (best[2] - Y0)*PX
        d.text((px_, py_), short(n), fill=(30, 30, 30), font=FONT(fs), anchor='mm', stroke_width=3, stroke_fill='white')
    return im
PANELS = [('In1.Cu', 'F.Cu', 'In1 (GND plane)  ·  top-layer tracks over it'), ('In2.Cu', 'B.Cu', 'In2 (power planes)  ·  bottom-layer tracks over it')]
if opt.get('only'): PANELS = [p for p in PANELS if p[0].startswith(opt['only'])]
ims = [(panel(i, o, ''), t) for i, o, t in PANELS]
G = 24; T = 64; FS = 30
legend = 'Planes: KiCad zone fill, coloured by net (white = no copper: splits, gaps, antipads). Red = top-layer tracks over In1; blue = bottom-layer tracks over In2. Dots = vias / through-holes.'
n = len(ims); OW = n*W + (n+1)*G; LF = FONTR(max(14, min(26, OW/75)))
cur = ''
words = legend.split(' '); lines = []
for w_ in words:
    if LF.getlength(cur + ' ' + w_) > OW - 2*G and cur: lines.append(cur); cur = w_
    else: cur = (cur + ' ' + w_).strip()
lines.append(cur)
out = Image.new('RGB', (OW, H + T + (T if TITLE else 0) + 24 + int(LF.size*1.4)*len(lines)), 'white'); d = ImageDraw.Draw(out)
y0 = (T if TITLE else 0) + T
if TITLE: d.text((G, 14), TITLE, fill=(29, 35, 42), font=FONT(FS*1.15))
for k, (im, t) in enumerate(ims):
    x = G + k*(W + G); d.text((x, y0 - 44), t, fill=(29, 35, 42), font=FONT(FS*0.85)); out.paste(im, (x, y0))
    d.rectangle((x-1, y0-1, x+W, y0+H), outline=(206, 212, 218), width=2)
for k, l in enumerate(lines): d.text((G, y0 + H + 12 + k*int(LF.size*1.4)), l, fill=(85, 85, 85), font=LF)
out.save(OUT); print('written', OUT, out.size)
