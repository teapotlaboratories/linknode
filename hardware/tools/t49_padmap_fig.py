"""Draw the expansion pogo-pad map (T49/T50) from the board: whole-board top view + close-up with pad numbers.
Usage: python3 t49_padmap_fig.py <board.kicad_pcb> <out.png>
Pad n = TP10nn; pad 1 = MH1 + (56.00, 27.20) mm; 7 per row, 2.54 mm pitch. Labels come from the pad nets."""
import sys, re, pcbnew, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyBboxPatch, Circle
from matplotlib.lines import Line2D
b = pcbnew.LoadBoard(sys.argv[1]); FP = {f.GetReference(): f for f in b.GetFootprints()}
MH1 = FP['MH1'].GetPosition(); MH1 = (MH1.x/1e6, MH1.y/1e6)
pads = sorted(((int(r[4:]), f) for r, f in FP.items() if re.fullmatch(r'TP10\d\d', r)), key=lambda t: t[0])
def label(net):
    n = net.split('/')[-1]
    if n.startswith('Net-(R100'): n = {'1': 'ETH_TX+', '2': 'ETH_TX−', '3': 'ETH_RX+', '4': 'ETH_RX−'}[n[9]]
    if n.startswith('Net-(U1006'): n = {'D1+': 'MIC0+', 'D1-': 'MIC0−', 'D2+': 'MIC1+', 'D2-': 'MIC1−'}[n[11:14]]
    return n.replace('EXP_', '').replace('VCC5V0_SYS', '5V').replace('VCC_3V3', '3V3').replace('SPI0_', '').replace('_SDA', ' SDA').replace('_SCL', ' SCL')
def col(n):
    return ('#e8590c' if n in ('5V', '3V3') else '#868e96' if n == 'GND' else '#f08c00' if n.startswith('ETH') else
            '#c2255c' if n.startswith(('MIC', 'LINE')) else '#1971c2' if ('I2C' in n or n in ('CS0', 'CLK', 'MOSI', 'MISO')) else '#2f9e44')
def T(ax, *a, **k): k['clip_on'] = True; return ax.text(*a, **k)
def draw(ax, zoom):
    for f in b.GetFootprints():
        r = f.GetReference()
        if f.IsFlipped() and not r.startswith('TP10'):
            cy = f.GetCourtyard(pcbnew.B_CrtYd)
            if cy.OutlineCount():
                ax.add_patch(Polygon([(cy.Outline(0).CPoint(i).x/1e6, cy.Outline(0).CPoint(i).y/1e6) for i in range(cy.Outline(0).PointCount())], fc='#f1f3f5', ec='#ced4da', lw=0.5))
        elif not f.IsFlipped() and r in ('U801', 'U20', 'U100', 'U701', 'J401', 'J1', 'J2'):
            cy = f.GetCourtyard(pcbnew.F_CrtYd)
            ax.add_patch(Polygon([(cy.Outline(0).CPoint(i).x/1e6, cy.Outline(0).CPoint(i).y/1e6) for i in range(cy.Outline(0).PointCount())], fill=False, ec='#adb5bd', lw=0.8, ls='--'))
            c = f.GetPosition(); T(ax, c.x/1e6, (c.y/1e6) if r != 'U801' else (148.5 if not zoom else 143.6), {'U801': 'ESP32-C5 (top)', 'U20': 'GPS (top)', 'U100': 'RV1106 (top)', 'U701': 'HaLow (top)', 'J401': 'microSD', 'J1': 'USB-C', 'J2': 'DC IN'}[r], ha='center', va='center', fontsize=8, color='#868e96')
        if r.startswith('MH'):
            c = f.GetPosition(); ax.add_patch(Circle((c.x/1e6, c.y/1e6), 1.6, fc='#dee2e6', ec='#495057', lw=1)); T(ax, c.x/1e6, c.y/1e6 + 3.6, r, ha='center', fontsize=8, color='#495057')
    eb = b.GetBoardEdgesBoundingBox()
    ax.add_patch(FancyBboxPatch((eb.GetLeft()/1e6, eb.GetTop()/1e6), eb.GetWidth()/1e6, eb.GetHeight()/1e6, boxstyle='round,pad=0,rounding_size=2', fill=False, ec='#f08c00', lw=1.8))
    for n, f in pads:
        p = list(f.Pads())[0]; x, y = p.GetPosition().x/1e6, p.GetPosition().y/1e6; lab = label(p.GetNetname())
        ax.add_patch(Circle((x, y), 0.75, fc=col(lab), ec='none'))
        if zoom:
            T(ax, x, y + 0.95, lab, ha='center', va='top', fontsize=6.0, color='#212529')
            T(ax, x, y, str(n), ha='center', va='center', fontsize=6.3, color='white', weight='bold')
fig, axs = plt.subplots(1, 2, figsize=(16, 7.6), gridspec_kw=dict(width_ratios=[1.3, 1]))
draw(axs[0], False); axs[0].set_xlim(98, 180); axs[0].set_ylim(162, 96); axs[0].set_aspect('equal')
p1 = list(pads[0][1].Pads())[0].GetPosition()
axs[0].annotate('', xy=(p1.x/1e6 - 0.9, p1.y/1e6 - 0.4), xytext=(MH1[0] + 1.8, MH1[1] + 0.9), arrowprops=dict(arrowstyle='->', color='#c2255c', lw=1.5))
T(axs[0], 128, 111.5, 'pad 1 = MH1 + (56.00, 27.20) mm', color='#c2255c', fontsize=9, rotation=-25)
T(axs[0], 139, 100.3, 'M3 hole pattern 70.05 × 54.05 mm; top view, pads on the bottom', fontsize=8, color='#495057', ha='center')
draw(axs[1], True); axs[1].set_xlim(156, 178.5); axs[1].set_ylim(143.5, 126); axs[1].set_aspect('equal')
for ax in axs: ax.tick_params(labelsize=7)
h = [Line2D([0], [0], marker='o', ls='', color=c, label=l, markersize=8) for c, l in (('#f08c00', 'Ethernet (raw PHY)'), ('#c2255c', 'audio (mic, line out)'), ('#1971c2', 'I2C2 / I2C0 / SPI0'), ('#2f9e44', 'GPIO, 3.3 V'), ('#e8590c', 'power, unswitched'), ('#868e96', 'GND'))]
fig.legend(handles=h, loc='lower center', ncol=6, fontsize=8.5, frameon=False)
plt.tight_layout(rect=(0, 0.05, 1, 1)); plt.savefig(sys.argv[2], dpi=150); print('written', sys.argv[2], len(pads), 'pads')
