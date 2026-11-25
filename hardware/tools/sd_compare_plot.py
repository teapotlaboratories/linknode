"""sd_compare_plot.py before.kicad_pcb after.kicad_pcb diff.json out.png [x0,y0,x1,y1]
KiCad's own plot (kicad-cli SVG, zone fills removed; top copper red, bottom blue) of the microSD area, before | after,
with the changes from sd_diff.py drawn over it: removed copper haloed orange (before), added copper haloed green (after),
removed vias dashed rings, moved parts ringed with an arrow for long moves. Board mm -> px at 60 px/mm."""
import sys, os, json, math, subprocess, tempfile, shutil, pcbnew
from PIL import Image, ImageDraw, ImageFont
BEF, AFT, DJ, OUT = sys.argv[1:5]
X0, Y0, X1, Y1 = map(float, (sys.argv[5] if len(sys.argv) > 5 else '131,133,157,160').split(','))
PX = 60; D = json.load(open(DJ))
FONT = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', s)
def plot(brd):
    tmp = tempfile.mkdtemp(prefix='sdplot')
    try:
        src = os.path.dirname(os.path.abspath(brd)); base = os.path.splitext(os.path.basename(brd))[0]
        for ext in ('.kicad_pcb', '.kicad_pro', '.kicad_dru'):
            if os.path.exists(os.path.join(src, base + ext)): shutil.copy(os.path.join(src, base + ext), os.path.join(tmp, 'p' + ext))
        b = pcbnew.LoadBoard(os.path.join(tmp, 'p.kicad_pcb'))
        for z in b.Zones(): z.UnFill()
        b.Save(os.path.join(tmp, 'p.kicad_pcb'))
        eb = b.GetBoardEdgesBoundingBox(); ox, oy = eb.GetLeft()/1e6, eb.GetTop()/1e6
        subprocess.run(['kicad-cli', 'pcb', 'export', 'svg', '--mode-single', '--layers', 'F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,Edge.Cuts',
                        '--page-size-mode', '2', '--exclude-drawing-sheet', '-o', os.path.join(tmp, 'p.svg'), os.path.join(tmp, 'p.kicad_pcb')],
                       check=True, capture_output=True)
        subprocess.run(['rsvg-convert', '-z', str(PX), '--dpi-x', '25.4', '--dpi-y', '25.4', '-b', 'white', os.path.join(tmp, 'p.svg'),
                        '-o', os.path.join(tmp, 'p.png')], check=True)
        im = Image.open(os.path.join(tmp, 'p.png')).convert('RGBA')
        return im.crop((int((X0-ox)*PX), int((Y0-oy)*PX), int((X1-ox)*PX), int((Y1-oy)*PX)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
P = lambda x, y: ((x - X0)*PX, (y - Y0)*PX)
def tag(d, x, y, n, col):
    cx, cy = P(x, y); r = 30
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=col, outline='white', width=4)
    d.text((cx, cy), str(n), fill='white', font=FONT(34), anchor='mm')
def ring(d, x, y, r, col, dash=False, w=6):
    cx, cy = P(x, y); r *= PX
    if not dash: d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=col, width=w); return
    for a in range(0, 360, 24): d.arc((cx-r, cy-r, cx+r, cy+r), a, a+13, fill=col, width=w)
def panel(brd, after):
    im = plot(brd); ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    halo = (40, 200, 60, 120) if after else (255, 140, 0, 135)
    for lay, (p, q), n in (D['add'] if after else D['rem']):
        d.line([P(*p), P(*q)], fill=halo, width=int(0.9*PX)); 
        for e in (p, q): cx, cy = P(*e); r = 0.45*PX; d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=halo)
    im = Image.alpha_composite(im, ov); d = ImageDraw.Draw(im)
    if not after:
        for (x, y), n in D['vrem']: ring(d, x, y, 0.7, (220, 40, 20, 255), dash=True)
    for r, (pa, pb) in D['moved'].items():
        if after:
            ring(d, pb[0], pb[1], 1.05, (200, 0, 120, 255))
            if math.hypot(pa[0]-pb[0], pa[1]-pb[1]) > 0.5:
                ring(d, pa[0], pa[1], 1.05, (200, 0, 120, 160), dash=True, w=4)
                (ax, ay), (bx, by) = P(pa[0], pa[1]), P(pb[0], pb[1]); L = math.hypot(bx-ax, by-ay); ux, uy = (bx-ax)/L, (by-ay)/L
                sx, sy, ex, ey = ax+ux*66, ay+uy*66, bx-ux*66, by-uy*66
                d.line([(sx, sy), (ex, ey)], fill=(200, 0, 120, 255), width=6)
                d.polygon([(ex+ux*4, ey+uy*4), (ex-ux*26-uy*14, ey-uy*26+ux*14), (ex-ux*26+uy*14, ey-uy*26-ux*14)], fill=(200, 0, 120, 255))
        else: ring(d, pa[0], pa[1], 1.05, (200, 0, 120, 255), dash=True)
    # numbered tags (same numbers both sides)
    if not after:
        tag(d, 136.2, 142.0, 1, (230, 110, 0)); tag(d, 133.6, 139.2, 2, (220, 40, 20)); tag(d, 140.9, 143.4, 2, (220, 40, 20))
        tag(d, 141.4, 147.6, 4, (200, 0, 120)); tag(d, 144.6, 143.6, 5, (200, 0, 120))
    else:
        tag(d, 137.3, 140.4, 3, (30, 150, 50)); tag(d, 148.4, 146.9, 4, (200, 0, 120)); tag(d, 144.6, 143.6, 5, (200, 0, 120))
    return im
A, B = panel(BEF, False), panel(AFT, True)
W, H = A.size; G = 40; TOP = 90
legend = ['1  Card detect (J401-DET): bottom-layer hop under the audio lanes removed (4 bottom + 2 top segments)',
          '2  Its two vias removed: (135.0, 140.1) and (140.2, 144.4)',
          '3  New card-detect route: straight south on the top from R402\'s via (x 138.2), one 45° diagonal into the socket pad',
          '4  C401 (1 µF, card supply) moved from under the audio lanes to east of C404 (bottom side)',
          '5  C402 / C404 moved 0.06 mm north and 0.02 mm apart (bottom side)',
          'All other microSD copper (CLK, CMD, D0–D3, power switch, pull-ups) is identical: 233 of 237 segments unchanged.']
LH = 40; out = Image.new('RGB', (2*W + 3*G, TOP + H + 30 + LH*len(legend) + 30), 'white'); dd = ImageDraw.Draw(out)
for i, (im, t) in enumerate(((A, 'BEFORE  —  main board'), (B, 'AFTER  —  FPC B routed (copy)'))):
    x = G + i*(W + G); out.paste(im.convert('RGB'), (x, TOP)); dd.rectangle((x-2, TOP-2, x+W+1, TOP+H+1), outline='#ced4da', width=2)
    dd.text((x, 28), t, fill='#1d232a', font=FONT(44))
y = TOP + H + 30
for k, l in enumerate(legend): dd.text((G, y + k*LH), l, fill='#1d232a' if k < 5 else '#555', font=FONT(28))
out.save(OUT); print('written', OUT, out.size)
