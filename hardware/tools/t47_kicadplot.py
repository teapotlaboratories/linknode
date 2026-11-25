"""KiCad's own plot of a board area, for routing reviews (owner 2026-11-23: show the KiCad PCB routing for every section).
Usage: python3 t47_kicadplot.py <board.kicad_pcb> <out.png> x0,y0,x1,y1 [title] [--layers F.Cu,B.Cu,F.Silkscreen,Edge.Cuts]
       [--note "x,y,text"]...
A copy of the board with its zone fills removed (so the tracks show) is plotted by kicad-cli (SVG, the PCB editor's
colour theme: top copper red, bottom copper blue), rendered on white at 60 px/mm and cropped to the area (board mm).
--note draws a numbered marker at board point (x, y) with its text listed under the title. Scratch files go to a temp dir."""
import sys, os, subprocess, tempfile, shutil, pcbnew
args = sys.argv[1:]; notes = []; layers = 'F.Cu,B.Cu,F.Silkscreen,Edge.Cuts'; pos = []
i = 0
while i < len(args):
    if args[i] == '--note': notes.append(args[i + 1]); i += 2
    elif args[i] == '--layers': layers = args[i + 1]; i += 2
    else: pos.append(args[i]); i += 1
BRD, OUT, BOX = pos[0], pos[1], [float(v) for v in pos[2].split(',')]
TITLE = pos[3] if len(pos) > 3 else ''
PX = 60
tmp = tempfile.mkdtemp(prefix='kplot')
try:
    src = os.path.dirname(os.path.abspath(BRD)); base = os.path.splitext(os.path.basename(BRD))[0]
    for ext in ('.kicad_pcb', '.kicad_pro', '.kicad_dru'):
        if os.path.exists(os.path.join(src, base + ext)): shutil.copy(os.path.join(src, base + ext), os.path.join(tmp, 'p' + ext))
    b = pcbnew.LoadBoard(os.path.join(tmp, 'p.kicad_pcb'))
    for z in b.Zones(): z.UnFill()
    b.Save(os.path.join(tmp, 'p.kicad_pcb'))
    eb = b.GetBoardEdgesBoundingBox(); ox, oy = eb.GetLeft()/1e6, eb.GetTop()/1e6
    subprocess.run(['kicad-cli', 'pcb', 'export', 'svg', '--mode-single', '--layers', layers, '--page-size-mode', '2',
                    '--exclude-drawing-sheet', '-o', os.path.join(tmp, 'p.svg'), os.path.join(tmp, 'p.kicad_pcb')], check=True, capture_output=True)
    subprocess.run(['rsvg-convert', '-z', str(PX), '--dpi-x', '25.4', '--dpi-y', '25.4', '-b', 'white', os.path.join(tmp, 'p.svg'),
                    '-o', os.path.join(tmp, 'p.png')], check=True)
    x0, y0, x1, y1 = BOX
    FS = max(28, int((x1 - x0)*PX/90))                  # title size follows the crop width
    crop = '%dx%d+%d+%d' % ((x1 - x0)*PX, (y1 - y0)*PX, (x0 - ox)*PX, (y0 - oy)*PX)
    cmd = ['convert', os.path.join(tmp, 'p.png'), '-crop', crop, '+repage']
    for k, n in enumerate(notes, 1):
        x, y, _ = n.split(',', 2); px, py = (float(x) - x0)*PX, (float(y) - y0)*PX
        cmd += ['-fill', 'none', '-stroke', '#7048e8', '-strokewidth', '5', '-draw', 'circle %d,%d %d,%d' % (px, py, px + 46, py),
                '-fill', '#7048e8', '-stroke', 'none', '-draw', 'circle %d,%d %d,%d' % (px + 52, py - 52, px + 74, py - 52),
                '-fill', 'white', '-pointsize', '28', '-annotate', '+%d+%d' % (px + 44, py - 42), str(k)]
    head = TITLE + ('\n' + '\n'.join('%d  %s' % (k, n.split(',', 2)[2]) for k, n in enumerate(notes, 1)) if notes else '')
    lines = head.count('\n') + 1 if head else 0
    if head:
        cmd += ['-gravity', 'northwest', '-background', 'white', '-splice', '0x%d' % (16 + int(FS*1.43)*lines), '-fill', '#1d232a',
                '-pointsize', str(FS), '-annotate', '+20+10', head]
    cmd += ['-bordercolor', '#ced4da', '-border', '2', OUT]
    subprocess.run(cmd, check=True); print('written', OUT)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
