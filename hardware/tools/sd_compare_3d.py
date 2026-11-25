"""sd_compare_3d.py DIR diff.json out.jpg
DIR holds cal/, before/, after/ from the render script: q_<side>.png (basic renders; cal/ has filled silkscreen dots at
(133,136) and (155,158) on both sides) and hq_<side>.png (high-quality renders, before/ and after/).
The dots give the board-mm -> pixel map (orthographic, so linear; bottom is mirrored in x). The changes from sd_diff.py
are drawn over the high-quality renders: top layer changes on the top views, bottom layer changes on the bottom views."""
import sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
DIR, DJ, OUT = sys.argv[1:4]; D = json.load(open(DJ))
FONT = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', s)
M = ((133.0, 136.0), (155.0, 158.0))
def calib(side):
    a = np.asarray(Image.open(f'{DIR}/cal/q_{side}.png').convert('RGB')).astype(int)
    b = np.asarray(Image.open(f'{DIR}/before/q_{side}.png').convert('RGB')).astype(int)
    m = np.abs(a - b).sum(2) > 60
    ys, xs = np.nonzero(m)
    # two blobs: split on the y midpoint
    mid = (ys.min() + ys.max()) / 2
    c1 = (xs[ys < mid].mean(), ys[ys < mid].mean()); c2 = (xs[ys >= mid].mean(), ys[ys >= mid].mean())
    ax = (c2[0] - c1[0]) / (M[1][0] - M[0][0]); bx = c1[0] - ax*M[0][0]
    ay = (c2[1] - c1[1]) / (M[1][1] - M[0][1]); by = c1[1] - ay*M[0][1]
    print(side, 'px/mm x', round(ax, 2), 'y', round(ay, 2))
    return lambda x, y: (ax*x + bx, ay*y + by), abs(ay)
def ring(d, c, r, col, dash=False, w=6):
    cx, cy = c
    if not dash: d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=col, width=w); return
    for a in range(0, 360, 24): d.arc((cx-r, cy-r, cx+r, cy+r), a, a+13, fill=col, width=w)
def tag(d, c, n, col):
    cx, cy = c; r = 30; d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=col, outline='white', width=4)
    d.text((cx, cy), str(n), fill='white', font=FONT(34), anchor='mm')
TAGS = {('top', False): [(1, 135.6, 138.0, (230, 110, 0)), (2, 133.6, 139.2, (220, 40, 20)), (2, 140.9, 143.4, (220, 40, 20))],
        ('top', True): [(3, 137.3, 140.4, (30, 150, 50))],
        ('bottom', False): [(1, 136.2, 142.0, (230, 110, 0)), (2, 133.6, 139.2, (220, 40, 20)), (2, 140.9, 143.4, (220, 40, 20)),
                            (4, 141.4, 147.6, (200, 0, 120)), (5, 144.6, 143.6, (200, 0, 120))],
        ('bottom', True): [(4, 148.4, 146.9, (200, 0, 120)), (5, 144.6, 143.6, (200, 0, 120))]}
def panel(side, after):
    P, s = calib(side)
    im = Image.open(f"{DIR}/{'after' if after else 'before'}/hq_{side}.png").convert('RGBA')
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    halo = (60, 230, 80, 125) if after else (255, 150, 0, 140); lay = 'F.Cu' if side == 'top' else 'B.Cu'
    for l, (p, q), n in (D['add'] if after else D['rem']):
        if l != lay: continue
        d.line([P(*p), P(*q)], fill=halo, width=int(0.9*s))
        for e in (p, q): cx, cy = P(*e); r = 0.45*s; d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=halo)
    im = Image.alpha_composite(im, ov); d = ImageDraw.Draw(im)
    if not after:
        for (x, y), n in D['vrem']: ring(d, P(x, y), 0.7*s, (255, 60, 30, 255), dash=True)
    if side == 'bottom':
        for r, (pa, pb) in D['moved'].items():
            if not after: ring(d, P(pa[0], pa[1]), 1.05*s, (255, 40, 170, 255), dash=True); continue
            ring(d, P(pb[0], pb[1]), 1.05*s, (255, 40, 170, 255))
            if math.hypot(pa[0]-pb[0], pa[1]-pb[1]) > 0.5:
                ring(d, P(pa[0], pa[1]), 1.05*s, (255, 40, 170, 200), dash=True, w=4)
                (ax, ay), (bx, by) = P(pa[0], pa[1]), P(pb[0], pb[1]); L = math.hypot(bx-ax, by-ay); ux, uy = (bx-ax)/L, (by-ay)/L
                sx, sy, ex, ey = ax+ux*1.15*s, ay+uy*1.15*s, bx-ux*1.15*s, by-uy*1.15*s
                d.line([(sx, sy), (ex, ey)], fill=(255, 40, 170, 255), width=6)
                d.polygon([(ex+ux*4, ey+uy*4), (ex-ux*26-uy*14, ey-uy*26+ux*14), (ex-ux*26+uy*14, ey-uy*26-ux*14)], fill=(255, 40, 170, 255))
    for n, x, y, col in TAGS[(side, after)]: tag(d, P(x, y), n, col)
    return im.convert('RGB')
ims = {(s, a): panel(s, a) for s in ('top', 'bottom') for a in (False, True)}
W, H = ims[('top', False)].size; G = 30; T = 70
out = Image.new('RGB', (2*W + 3*G, 2*(H + T) + G + 300), 'white'); dd = ImageDraw.Draw(out)
for r, s in enumerate(('top', 'bottom')):
    for c, a in enumerate((False, True)):
        x = G + c*(W + G); y = r*(H + T) + T
        dd.text((x, y - 52), f"{'AFTER — FPC B routed (copy)' if a else 'BEFORE — main board'}  ·  {'top' if s == 'top' else 'bottom (seen from below, mirrored)'}",
                fill='#1d232a', font=FONT(34))
        out.paste(ims[(s, a)], (x, y))
legend = ['1  Card detect (J401-DET): the hop under the audio lanes is removed (top stub + bottom diagonal)',
          '2  Its two vias are removed',
          '3  New card-detect route: straight south on the top, one 45° diagonal into the socket pad',
          '4  C401 moved from under the audio lanes to east of C404 (bottom)',
          '5  C402 / C404 moved 0.06 mm north, 0.02 mm apart (bottom)',
          'Orange halo = copper removed, green halo = copper added, pink rings = moved parts (dashed = old place).']
y0 = 2*(H + T) + G
for k, l in enumerate(legend): dd.text((G, y0 + k*44), l, fill='#1d232a' if k < 5 else '#555', font=FONT(30))
out.save(OUT, quality=88); print('written', OUT, out.size)
