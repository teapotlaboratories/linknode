"""T32: plot courtyards of a board (top and bottom side by side) with refs, coloured by sheet. Usage: t32_plot.py board out.png"""
import sys, pcbnew, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
b = pcbnew.LoadBoard(sys.argv[1]); eb = b.GetBoardEdgesBoundingBox()
x0, y0, x1, y1 = eb.GetLeft()/1e6, eb.GetTop()/1e6, eb.GetRight()/1e6, eb.GetBottom()/1e6
COL = {}; pal = plt.get_cmap('tab20').colors
fig, axs = plt.subplots(1, 2, figsize=(16, 7.6))
for ax, flipped, name in ((axs[0], False, 'top'), (axs[1], True, 'bottom (seen from top)')):
    ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, fill=False, lw=1.2, color='k'))
    for f in b.GetFootprints():
        if f.IsFlipped() != flipped: continue
        L = pcbnew.B_CrtYd if flipped else pcbnew.F_CrtYd; xs = []; ys = []
        for g in f.GraphicalItems():
            if g.GetLayer() == L: r = g.GetBoundingBox(); xs += [r.GetLeft(), r.GetRight()]; ys += [r.GetTop(), r.GetBottom()]
        if not xs: continue
        sh = f.GetSheetname() or 'root'; c = COL.setdefault(sh, pal[len(COL) % 20])
        l, t, r, bt = min(xs)/1e6, min(ys)/1e6, max(xs)/1e6, max(ys)/1e6
        ax.add_patch(Rectangle((l, t), r-l, bt-t, fc=c, ec='k', lw=0.3, alpha=0.75))
        ax.text((l+r)/2, (t+bt)/2, f.GetReference(), fontsize=3.2 if (r-l) < 4 else 5.5, ha='center', va='center')
    ax.set_xlim(x0-3, x1+12); ax.set_ylim(y1+3, y0-3); ax.set_aspect('equal'); ax.set_title(name)
axs[0].legend(handles=[Rectangle((0, 0), 1, 1, fc=c) for c in COL.values()], labels=list(COL), fontsize=6, loc='upper right', bbox_to_anchor=(1.0, -0.02), ncol=7)
plt.tight_layout(); plt.savefig(sys.argv[2], dpi=170)
