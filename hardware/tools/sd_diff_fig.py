"""sd_diff_fig.py before after diff.json out.png : 2x2 (before/after x top/bottom) of the microSD area; SD nets coloured, changes highlighted"""
import sys, json, re, pcbnew, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
mm = pcbnew.ToMM; D = json.load(open(sys.argv[3]))
X0, Y0, X1, Y1 = 131.5, 133.0, 154.5, 153.5
AUD = ('LINEOUT', 'MICBIAS', '/Expansion/MIC', 'U1006-D')
MOVED = set(D['moved'])
def kind(n, ref=None):
    if n == 'Net-(J401-DET)': return 'det'
    if any(a in n for a in AUD): return 'aud'
    if ref and re.match(r'[A-Z]+4\d\d$', ref) and n not in ('GND',): return 'sd'
    if 'SD' in n or 'J401' in n or 'U40' in n or 'R40' in n or 'Q401' in n: return 'sd'
    return 'other'
COL = {'det': '#d4380d', 'aud': '#2f6fdb', 'sd': '#2e8b57', 'other': '#b8b8b8'}
def draw(ax, path, layer, after):
    b = pcbnew.LoadBoard(path); L = b.GetLayerID(layer)
    def poly(item, c, z, a=1.0, ec='none', lw=0):
        sp = pcbnew.SHAPE_POLY_SET(); item.TransformShapeToPolygon(sp, L, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE)
        for i in range(sp.OutlineCount()):
            o = sp.Outline(i); pts = [(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())]
            if any(X0-1 < x < X1+1 and Y0-1 < y < Y1+1 for x, y in pts): ax.add_patch(Polygon(pts, closed=True, fc=c, ec=ec, lw=lw, zorder=z, alpha=a))
    for t in b.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T and t.GetLayer() != L: continue
        k = kind(t.GetNetname()); poly(t, COL[k], 4 if k != 'other' else 2, 1.0 if k != 'other' else 0.7)
    for f in b.GetFootprints():
        ref = f.GetReference()
        for p in f.Pads():
            if not p.IsOnLayer(L): continue
            k = kind(p.GetNetname(), ref); poly(p, COL[k], 3, 0.55 if k != 'other' else 0.45)
        if f.IsFlipped() == (layer == 'B.Cu'):
            bb = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd).BBox() if False else None
            q = f.GetPosition(); x, y = mm(q.x), mm(q.y)
            if X0 < x < X1 and Y0 < y < Y1 and (re.match(r'[A-Z]+4\d\d$', ref) or ref in ('J1002', 'U1006', 'U1007') or ref.startswith('C100')):
                hot = ref in MOVED
                ax.text(x, y - (1.25 if hot else 0), ref, fontsize=6.5 if hot else 5, color='#b00' if hot else '#334', weight='bold' if hot else 'normal',
                        ha='center', va='center', zorder=8, bbox=dict(fc='white', ec='#b00' if hot else 'none', lw=0.6, alpha=0.8, pad=0.6))
    # change markers
    seg = D['add'] if after else D['rem']; vias = D['vadd'] if after else D['vrem']
    lay = 'F.Cu' if layer == 'F.Cu' else 'B.Cu'
    for l, (p, q), n in seg:
        if l == lay: ax.plot([p[0], q[0]], [p[1], q[1]], color='#ffd400', lw=6, alpha=0.55, zorder=3.5, solid_capstyle='round')
    for (x, y), n in vias: ax.add_patch(plt.Circle((x, y), 0.45, fc='none', ec='#d4380d', lw=1.4, ls='--', zorder=9))
    for r, (pa, pb) in D['moved'].items():
        if (pa[3] == 'B') == (layer == 'B.Cu'):
            if not after: ax.add_patch(plt.Circle((pa[0], pa[1]), 0.85, fc='none', ec='#b00', lw=1.1, ls=':', zorder=9))
            else:
                ax.add_patch(plt.Circle((pb[0], pb[1]), 0.85, fc='none', ec='#b00', lw=1.1, zorder=9))
                if abs(pa[0]-pb[0]) + abs(pa[1]-pb[1]) > 0.5:
                    ax.annotate('', xy=(pb[0], pb[1]), xytext=(pa[0], pa[1]), arrowprops=dict(arrowstyle='->', color='#b00', lw=1.2, shrinkA=10, shrinkB=12), zorder=9)
    ax.set_xlim(X0, X1); ax.set_ylim(Y1, Y0); ax.set_aspect('equal'); ax.tick_params(labelsize=6)
    ax.set_facecolor('white'); ax.grid(True, lw=0.2, color='#ddd')
fig, axs = plt.subplots(2, 2, figsize=(15, 13.6))
for i, (path, after) in enumerate(((sys.argv[1], False), (sys.argv[2], True))):
    for j, layer in enumerate(('F.Cu', 'B.Cu')):
        draw(axs[j][i], path, layer, after)
        axs[j][i].set_title(f"{'AFTER (FPC B routed, copy)' if after else 'BEFORE (main board)'}  ·  {'top' if layer=='F.Cu' else 'bottom (seen from top)'}", fontsize=10)
from matplotlib.lines import Line2D
h = [Line2D([], [], color=COL['sd'], lw=4, label='microSD nets'), Line2D([], [], color=COL['det'], lw=4, label='J401-DET (card detect)'),
     Line2D([], [], color=COL['aud'], lw=4, label='FPC B audio'), Line2D([], [], color=COL['other'], lw=4, label='other nets'),
     Line2D([], [], color='#ffd400', lw=8, alpha=0.55, label='segment removed (before) / added (after)'),
     Line2D([], [], marker='o', ls='', mfc='none', mec='#d4380d', ms=10, label='via removed'),
     Line2D([], [], marker='o', ls='', mfc='none', mec='#b00', ms=10, label='capacitor moved')]
fig.legend(handles=h, loc='lower center', ncol=4, fontsize=9, frameon=False)
fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(sys.argv[4], dpi=130)
