"""Plot the U100 window of a board as SVG (mm units): tracks/vias/pads per copper layer, part outlines and refs.
Zones are left out so the copper that matters shows. Usage: python3 plot_svg.py <board> <out.svg> [x0 y0 x1 y1]"""
import sys, math, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); out = sys.argv[2]
X0, Y0, X1, Y1 = map(float, sys.argv[3:7]) if len(sys.argv) > 6 else (134.0, 128.0, 162.0, 156.0)
LN = {pcbnew.F_Cu: 'fcu', pcbnew.In1_Cu: 'in1', pcbnew.In2_Cu: 'in2', pcbnew.B_Cu: 'bcu'}
def inw(x, y, m=1.0): return X0-m < x < X1+m and Y0-m < y < Y1+m
g = {k: [] for k in ('in2', 'bcu', 'fcu', 'via', 'bfab', 'ffab', 'txt')}
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        x, y = t.GetPosition().x/1e6, t.GetPosition().y/1e6
        if inw(x, y): g['via'].append('<circle class="v" data-net="%s" cx="%.3f" cy="%.3f" r="%.3f"/><circle class="vh" cx="%.3f" cy="%.3f" r="%.3f"/>' % (t.GetNetname(), x, y, t.GetWidth(pcbnew.F_Cu)/2e6, x, y, t.GetDrill()/2e6))
        continue
    a, c = t.GetStart(), t.GetEnd(); L = LN.get(t.GetLayer())
    if L in g and (inw(a.x/1e6, a.y/1e6) or inw(c.x/1e6, c.y/1e6)):
        g[L].append('<line data-net="%s" x1="%.3f" y1="%.3f" x2="%.3f" y2="%.3f" stroke-width="%.3f"/>' % (t.GetNetname(), a.x/1e6, a.y/1e6, c.x/1e6, c.y/1e6, t.GetWidth()/1e6))
for fp in b.GetFootprints():
    x, y = fp.GetPosition().x/1e6, fp.GetPosition().y/1e6
    if not inw(x, y, 2): continue
    side = 'bcu' if fp.IsFlipped() else 'fcu'
    for p in fp.Pads():
        px, py = p.GetPosition().x/1e6, p.GetPosition().y/1e6
        if not inw(px, py): continue
        sx, sy = p.GetSizeX()/1e6, p.GetSizeY()/1e6; ang = -p.GetOrientationDegrees()
        if p.GetDrillSizeX() > 0:
            g['via'].append('<circle class="v pth" cx="%.3f" cy="%.3f" r="%.3f"/><circle class="vh" cx="%.3f" cy="%.3f" r="%.3f"/>' % (px, py, sx/2, px, py, p.GetDrillSizeX()/2e6)); continue
        g[side].append('<rect class="pad" data-net="%s" data-ref="%s" x="%.3f" y="%.3f" width="%.3f" height="%.3f" rx="%.3f" transform="rotate(%.1f %.3f %.3f)"/>' % (p.GetNetname(), fp.GetReference(), px-sx/2, py-sy/2, sx, sy, min(sx, sy)*0.2, ang, px, py))
    if fp.GetReference() == 'U100':
        g['ffab'].append('<rect class="body" x="%.3f" y="%.3f" width="12.3" height="12.3"/>' % (x-6.15, y-6.15)); continue
    bb = fp.GetBoundingBox(False, False)
    fab = 'bfab' if fp.IsFlipped() else 'ffab'
    g[fab].append('<rect class="out" data-ref="%s" x="%.3f" y="%.3f" width="%.3f" height="%.3f"/>' % (fp.GetReference(), bb.GetLeft()/1e6, bb.GetTop()/1e6, bb.GetWidth()/1e6, bb.GetHeight()/1e6))
    if fp.GetReference()[0] in 'CRYL':
        g['txt'].append('<text class="ref %s" x="%.3f" y="%.3f">%s</text>' % ('rb' if fp.IsFlipped() else 'rf', x, y+0.12, fp.GetReference()))
svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="%g %g %g %g">' % (X0, Y0, X1-X0, Y1-Y0)]
for k, cls in (('in2', 'L in2'), ('bcu', 'L bcu'), ('bfab', 'fab bfab'), ('fcu', 'L fcu'), ('ffab', 'fab ffab'), ('via', 'vias'), ('txt', 'txt')):
    svg.append('<g class="%s">%s</g>' % (cls, ''.join(g[k])))
svg.append('</svg>'); open(out, 'w').write(''.join(svg)); print(out, {k: len(v) for k, v in g.items()})
