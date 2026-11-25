"""T57 (owner, 2026-11-24: "for the inner layer please also show the actual pcb from kicad"): KiCad's own plot of In1.Cu and
In2.Cu for board areas. A copy of the board is refilled (pcbnew ZONE_FILLER) and each inner layer is exported by kicad-cli
(SVG, the PCB editor's colour theme, zones filled, holes drawn at actual size) with Edge.Cuts, rendered on white at PX px/mm,
then cropped per area: In1 | In2 side by side.
Usage: python3 t57_kicadinner.py <board.kicad_pcb> <outdir> name=x0,y0,x1,y1[=title] [name=...]... [--px 30]
Writes <outdir>/<name>.png per area."""
import sys, os, subprocess, tempfile, shutil, pcbnew
from PIL import Image, ImageDraw, ImageFont
args = sys.argv[1:]; PX = 30
if '--px' in args: k = args.index('--px'); PX = float(args[k+1]); del args[k:k+2]
BRD, OUTD = args[0], args[1]; AREAS = []
for a in args[2:]:
    parts = a.split('=', 2); AREAS.append((parts[0], [float(v) for v in parts[1].split(',')], parts[2] if len(parts) > 2 else ''))
FONT = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', int(s))
FONTR = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', int(s))
tmp = tempfile.mkdtemp(prefix='kinner')
Image.MAX_IMAGE_PIXELS = None
try:
    src = os.path.dirname(os.path.abspath(BRD)); base = os.path.splitext(os.path.basename(BRD))[0]
    for ext in ('.kicad_pcb', '.kicad_pro', '.kicad_dru'):
        if os.path.exists(os.path.join(src, base + ext)): shutil.copy(os.path.join(src, base + ext), os.path.join(tmp, 'p' + ext))
    b = pcbnew.LoadBoard(os.path.join(tmp, 'p.kicad_pcb')); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(os.path.join(tmp, 'p.kicad_pcb'))
    eb = b.GetBoardEdgesBoundingBox(); ox, oy = eb.GetLeft()/1e6, eb.GetTop()/1e6
    full = {}
    for L in ('In1.Cu', 'In2.Cu'):
        svg = os.path.join(tmp, L + '.svg'); png = os.path.join(tmp, L + '.png')
        subprocess.run(['kicad-cli', 'pcb', 'export', 'svg', '--mode-single', '--layers', L + ',Edge.Cuts', '--page-size-mode', '2',
                        '--exclude-drawing-sheet', '--drill-shape-opt', '2', '-o', svg, os.path.join(tmp, 'p.kicad_pcb')], check=True, capture_output=True)
        subprocess.run(['rsvg-convert', '-z', str(PX), '--dpi-x', '25.4', '--dpi-y', '25.4', '-b', 'white', svg, '-o', png], check=True)
        full[L] = Image.open(png).convert('RGB')
    os.makedirs(OUTD, exist_ok=True)
    for name, (x0, y0, x1, y1), title in AREAS:
        box = (int((x0-ox)*PX), int((y0-oy)*PX), int((x1-ox)*PX), int((y1-oy)*PX))
        A, B = full['In1.Cu'].crop(box), full['In2.Cu'].crop(box); W, H = A.size
        G = 24; T = 60; TT = 64 if title else 0; FS = 28
        note = 'KiCad plot (kicad-cli SVG export, PCB editor colours), zones filled; holes at actual size. White = no copper.'
        LF = FONTR(max(14, min(24, (2*W + 3*G)/80)))
        out = Image.new('RGB', (2*W + 3*G, TT + T + H + 50), 'white'); d = ImageDraw.Draw(out)
        if title: d.text((G, 14), title, fill=(29, 35, 42), font=FONT(FS*1.15))
        for k, (im, t) in enumerate(((A, 'In1.Cu (GND plane), KiCad'), (B, 'In2.Cu (power planes), KiCad'))):
            x = G + k*(W + G); d.text((x, TT + 12), t, fill=(29, 35, 42), font=FONT(FS*0.85)); out.paste(im, (x, TT + T))
            d.rectangle((x-1, TT+T-1, x+W, TT+T+H), outline=(206, 212, 218), width=2)
        d.text((G, TT + T + H + 12), note, fill=(85, 85, 85), font=LF)
        out.save(os.path.join(OUTD, name + '.png')); print('written', name, out.size)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
