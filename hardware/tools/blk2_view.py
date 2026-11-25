"""T41 Block 2: pad-level view of a board region, pads coloured by role (SW, GND, input, output, FB, other).
Usage: python3 blk2_view.py <board> <out.png> x0 y0 x1 y1 [title] [groups.json]
groups.json: a list of groups, or {"groups": [...], "arrows": [{"from": [ref, pad] | [x, y], "to": ..., "label", "color", "rad", "at"}]};
groups: [{"label": "...", "refs": [...], "color": "#hex", "each": bool, "at": [x, y]}, ...]: one outline around the group
(or, with each, one per part) and its label.
Top-side parts are drawn solid, bottom-side parts hatched (seen from the top)."""
import sys, re, pcbnew, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
b = pcbnew.LoadBoard(sys.argv[1]); out = sys.argv[2]; x0, y0, x1, y1 = map(float, sys.argv[3:7]); title = sys.argv[7] if len(sys.argv) > 7 else ''
def role(n):
    if n == 'GND': return '#8a8f98'
    if re.search(r'-SW\d?\)|SW1\)|SW2\)', n): return '#e0453a'
    if re.search(r'-FB\)|COMP', n): return '#2f9e44'
    if n in ('VCC5V0_SYS', 'VSYS', 'VSYS_SW', 'VBUS', 'VDCIN', 'VBAT') or 'PMID' in n or 'Q2-D' in n: return '#f08c00'
    if n.startswith('VDD') or n.startswith('VCC'): return '#1c7ed6'
    return '#c5cad3'
fig, ax = plt.subplots(figsize=((x1 - x0)/3.2, (y1 - y0)/3.2))
for f in b.GetFootprints():
    p0 = f.GetPosition()
    if not (x0 - 3 < p0.x/1e6 < x1 + 3 and y0 - 3 < p0.y/1e6 < y1 + 3): continue
    bot = f.IsFlipped(); L = pcbnew.B_CrtYd if bot else pcbnew.F_CrtYd
    for g in f.GraphicalItems():
        if g.GetLayer() == L:
            r = g.GetBoundingBox(); ax.add_patch(Rectangle((r.GetLeft()/1e6, r.GetTop()/1e6), r.GetWidth()/1e6, r.GetHeight()/1e6, fill=False,
                                                          ec='#5c7cfa' if bot else '#212529', lw=0.5, ls='--' if bot else '-'))
    for p in f.Pads():
        poly = p.GetEffectivePolygon(pcbnew.F_Cu if not bot else pcbnew.B_Cu) if hasattr(p, 'GetEffectivePolygon') else None
        bb = p.GetBoundingBox(); c = role(p.GetNetname())
        if p.GetDrillSizeX() > 0: c = '#adb5bd'
        ax.add_patch(Rectangle((bb.GetLeft()/1e6, bb.GetTop()/1e6), bb.GetWidth()/1e6, bb.GetHeight()/1e6, fc=c, ec='none',
                               alpha=0.45 if bot else 0.95, hatch='////' if bot else None))
    ax.text(p0.x/1e6, p0.y/1e6, f.GetReference(), fontsize=4.2 if not bot else 3.6, ha='center', va='center',
            clip_on=True, color='#1c1c1c' if not bot else '#364fc7', fontweight='bold' if f.GetReference()[0] in 'UQL' else 'normal')
eb = b.GetBoardEdgesBoundingBox()
ax.add_patch(Rectangle((eb.GetLeft()/1e6, eb.GetTop()/1e6), eb.GetWidth()/1e6, eb.GetHeight()/1e6, fill=False, ec='#f59f00', lw=1.2))
ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect('equal'); ax.set_title(title, fontsize=8)
ax.tick_params(labelsize=5)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(fc=c, label=l) for c, l in (('#e0453a', 'SW node'), ('#f08c00', 'input / PMID / SYS'), ('#1c7ed6', 'output rail'),
          ('#8a8f98', 'GND'), ('#2f9e44', 'FB / COMP'), ('#c5cad3', 'other'))] + [Patch(fc='w', ec='#5c7cfa', ls='--', label='bottom side')],
          fontsize=5, loc='upper left', bbox_to_anchor=(1.01, 1))
if len(sys.argv) > 8:
    import json
    from matplotlib.patches import FancyBboxPatch
    def cbox(r):
        f = b.FindFootprintByReference(r); L = pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd; xs, ys = [], []
        for it in f.GraphicalItems():
            if it.GetLayer() == L: q = it.GetBoundingBox(); xs += [q.GetLeft()/1e6, q.GetRight()/1e6]; ys += [q.GetTop()/1e6, q.GetBottom()/1e6]
        return min(xs) - 0.12, min(ys) - 0.12, max(xs) + 0.12, max(ys) + 0.12
    spec = json.load(open(sys.argv[8]))
    groups, arrows = (spec, []) if isinstance(spec, list) else (spec.get('groups', []), spec.get('arrows', []))
    from matplotlib.patches import FancyArrowPatch
    def pt(v):
        if isinstance(v[0], (int, float)): return tuple(v)
        p = [q for q in b.FindFootprintByReference(v[0]).Pads() if q.GetNumber() == v[1]][0]
        return (p.GetPosition().x/1e6, p.GetPosition().y/1e6)
    for a in arrows:
        p0, p1 = pt(a['from']), pt(a['to'])
        ax.add_patch(FancyArrowPatch(p0, p1, connectionstyle=f"arc3,rad={a.get('rad', 0.2)}", arrowstyle='-|>,head_length=2.2,head_width=1.2',
                                     color=a['color'], lw=a.get('lw', 2.2), zorder=7, alpha=0.95, shrinkA=0, shrinkB=1.5))
        for q in (p0,): ax.add_patch(matplotlib.patches.Circle(q, 0.28, color=a['color'], zorder=7))
        if a.get('label'):
            lx, ly = a.get('at', ((p0[0] + p1[0])/2, (p0[1] + p1[1])/2))
            ax.text(lx, ly, a['label'], fontsize=a.get('size', 5.0), color='white', fontweight='bold', ha='center', va='center', zorder=8,
                    clip_on=True, bbox=dict(boxstyle='round,pad=0.3', fc=a['color'], ec='white', lw=0.6))
    for g in groups:
        boxes = [cbox(r) for r in g['refs']] if g.get('each') else \
                [tuple(f(v) for f, v in zip((min, min, max, max), zip(*[cbox(r) for r in g['refs']])))]
        for (l, t, r_, bt) in boxes:
            ax.add_patch(FancyBboxPatch((l, t), r_ - l, bt - t, boxstyle='round,pad=0,rounding_size=0.4', fill=False, ec=g['color'], lw=2.0, zorder=5))
        l, t, r_, bt = boxes[0]
        if g.get('each'): lx, ly, va = tuple(g.get('at', (l, t - 0.1))) + ('bottom',)
        else: lx, ly, va = l + 0.25, t + 0.25, 'top'
        ax.text(lx, ly, g['label'], fontsize=g.get('size', 5.2), color='white', fontweight='bold', ha='left', va=va, zorder=6, clip_on=True,
                bbox=dict(boxstyle='round,pad=0.25', fc=g['color'], ec='none', alpha=0.95))
plt.tight_layout(); plt.savefig(out, dpi=int(__import__('os').environ.get('BLK2_DPI', 220)))
