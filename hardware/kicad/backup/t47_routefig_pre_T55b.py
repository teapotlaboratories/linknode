"""T47 review figure: routed copper on a white background, top and bottom side by side, pads and tracks coloured by
net and every pad of a routed net labelled with its net name (KiCad's "net names on pads", drawn from the board).
Usage: python3 t47_routefig.py <board.kicad_pcb> <out.png> [x0,y0,x1,y1] [title] [NET|NET...]
The optional nets are highlighted too and their open connections drawn as dashed ratsnest lines (env ROUTEFIG_ONLY=1:
colour only those nets).
Exact copper shapes come from pcbnew (TransformShapeToPolygon), not redrawn by hand. Zones are not drawn."""
import sys, os, re, math, pcbnew, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Patch
BRD, OUT = sys.argv[1], sys.argv[2]
X0, Y0, X1, Y1 = [float(v) for v in (sys.argv[3] if len(sys.argv) > 3 else '134,120,153,139').split(',')]
TITLE = sys.argv[4] if len(sys.argv) > 4 else 'Routed copper'
HL = set(sys.argv[5].split('|')) if len(sys.argv) > 5 and sys.argv[5] else set()     # extra nets to highlight (+ ratsnest)
ONLY = os.environ.get('ROUTEFIG_ONLY') == '1'                                         # colour only the HL nets
b = pcbnew.LoadBoard(BRD)
F, B = b.GetLayerID('F.Cu'), b.GetLayerID('B.Cu')
routed = ({t.GetNetname() for t in b.GetTracks()} if not ONLY else set()) | HL
if os.environ.get('ROUTEFIG_ALL') == '1': routed |= {p.GetNetname() for fp in b.GetFootprints() for p in fp.Pads() if p.GetNetname()}
def alias(n):
    n0 = n.replace('{slash}', '/')
    fixed = {'VDD_0V9': '0V9', 'VDD_ARM': 'ARM', 'VCC_DDR': 'DDR', 'VCC_1V8': '1V8', 'VCC_3V3': '3V3', 'GND': 'GND'}
    if n0 in fixed: return fixed[n0]
    m = re.match(r'Net-\(.*?-(.*)\)$', n0); s = m.group(1) if m else n0.split('/')[-1]
    if s.startswith('HALOW_SDIO_'): return 'H_' + s[11:]          # T53: HaLow SDIO lines keep their own names
    if s.startswith('HALOW_'): return s[6:12]
    if s.startswith('C5_'): return {'C5_HANDSHAKE': 'HSHAKE', 'C5_DATA_READY': 'DRDY'}.get(s, s[3:])   # T54: ESP32-C5 lines keep their own names
    if s.startswith('GPS_'): return s
    if s.startswith('EXP_GPIO1_'): return s[10:]                                     # T55: FPC A lines keep their own names
    if s.startswith(('I2C0_', 'I2C2_')): return s[5:] + s[3]
    if s.startswith(('SPI0_', 'ETH_')): return s.split('_', 1)[1]
    m2 = re.match(r'Net-\(J1001-Pad(\d+)\)$', n0)
    if m2: return 'A' + m2.group(1)
    return {'DRAM_ZQ': 'ZQ', 'MIPI_AVDD1V8/VCCIO7': 'MIPI', 'OTP/ETH/TSADC_AVDD1V8': 'OTP', 'RTC_AVDD3V3': 'RTC',
            'SARADC_USB_AVDD1V8': 'ADC', 'nPOR': 'nPOR', 'CODEC_VCM': 'VCM', 'FEPHY_EXTR': 'EXTR', 'USB_DP': 'D+', 'USB_DM': 'D−',
            'D+-PadA6': 'D+', 'D--PadA7': 'D−'}.get(s, s[:6])
# validated reference categorical palette (dataviz palette.md, light), fixed order; GND neutral gray
PAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6']
GROUP = {'0V9': 0, '3V3': 1, '1V8': 2, 'DDR': 3, 'ZQ': 4, 'ARM': 6, 'D+': 7, 'D−': 8}
PAL += ['#e34948', '#2a78d6']
GROUP.update({k: 0 for k in ('CS0', 'CLK', 'MOSI', 'MISO')})                       # T55 east side / FPC A: one colour per function
GROUP.update({k: 7 for k in ('SDA0', 'SCL0', 'SDA2', 'SCL2')})
GROUP.update({k: 4 for k in ('C7', 'B1')})
GROUP.update({k: 6 for k in ('TXP', 'TXN', 'RXP', 'RXN', 'A1', 'A2', 'A4', 'A5')})
GROUP.update({k: 3 for k in ('GPS_TXD', 'GPS_RXD', 'GPS_PPS')})
GROUP.update({k: 2 for k in ('UART_TX', 'UART_RX', 'HSHAKE', 'DRDY', 'EN', 'BOOT')})
def col(a): return '#6c757d' if a == 'GND' else PAL[GROUP.get(a, 5)]
def tint(hexc, f=0.72):
    r, g, bb = (int(hexc[i:i + 2], 16) for i in (1, 3, 5)); return '#%02x%02x%02x' % tuple(int(c + (255 - c)*f) for c in (r, g, bb))
def polys(item, L):
    ps = pcbnew.SHAPE_POLY_SET(); item.TransformShapeToPolygon(ps, L, 0, pcbnew.FromMM(0.002), pcbnew.ERROR_INSIDE)
    return [[(ps.Outline(k).CPoint(i).x/1e6, ps.Outline(k).CPoint(i).y/1e6) for i in range(ps.Outline(k).PointCount())] for k in range(ps.OutlineCount())]
def inwin(pts, m=1.0): return any(X0 - m < x < X1 + m and Y0 - m < y < Y1 + m for x, y in pts)
DPI = 200; FIGW = 22.0
fig, axs = plt.subplots(1, 2, figsize=(FIGW, FIGW/2*(Y1 - Y0)/(X1 - X0) + 1.3), dpi=DPI)
pxmm = (FIGW/2*0.93*DPI)/(X1 - X0)                      # pixels per mm in one panel (approx.)
def fs_for(text, w, h):
    lng, sht = max(w, h), min(w, h)
    mmh = min(sht*0.72, lng*0.88/(0.62*max(len(text), 1)))
    return mmh*pxmm*72/DPI
used = set()
for ax, L, name in ((axs[0], F, 'Top copper (F.Cu)'), (axs[1], B, 'Bottom copper (B.Cu), seen from the top')):
    ax.set_facecolor('white')
    # pads
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if not p.IsOnLayer(L): continue
            for pts in polys(p, L):
                if not inwin(pts): continue
                n = p.GetNetname(); hot = n in routed
                if hot:
                    a = alias(n); c = col(a); used.add(n)
                    ax.add_patch(Polygon(pts, closed=True, fc=tint(c), ec=c, lw=0.8, zorder=2))
                else:
                    ax.add_patch(Polygon(pts, closed=True, fc='#eef0f2', ec='#c9ced4', lw=0.5, zorder=1))
    # tracks (exact outlines) then vias
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            x, y = t.GetPosition().x/1e6, t.GetPosition().y/1e6
            if not (X0 - 1 < x < X1 + 1 and Y0 - 1 < y < Y1 + 1): continue
            c = col(alias(t.GetNetname()))
            ax.add_patch(Circle((x, y), t.GetWidth(pcbnew.F_Cu)/2e6, fc=c, ec='white', lw=0.6, zorder=5))
            ax.add_patch(Circle((x, y), t.GetDrill()/2e6, fc='white', ec='none', zorder=6))
            continue
        if t.GetLayer() != L: continue
        for pts in polys(t, L):
            if inwin(pts): ax.add_patch(Polygon(pts, closed=True, fc=col(alias(t.GetNetname())), ec='none', alpha=0.92, zorder=4))
    # net names on pads (above the tracks, dark ink with a light halo)
    import matplotlib.patheffects as pe
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if not p.IsOnLayer(L) or p.GetNetname() not in routed: continue
            bb = p.GetBoundingBox(); w, h = bb.GetWidth()/1e6, bb.GetHeight()/1e6
            x, y = p.GetPosition().x/1e6, p.GetPosition().y/1e6
            if not (X0 < x < X1 and Y0 < y < Y1): continue
            a = alias(p.GetNetname()); fs = fs_for(a, w, h)
            if fs < 2.2: continue
            ax.text(x, y, a, ha='center', va='center', fontsize=min(fs, 16), rotation=90 if h > w*1.15 else 0, color='#1d232a',
                    weight='bold', zorder=7, path_effects=[pe.withStroke(linewidth=1.6, foreground='white')])
    # footprint references for parts that have a routed pad on this layer (small, muted, beside the part)
    for fp in b.GetFootprints():
        if not any(p.IsOnLayer(L) and p.GetNetname() in routed for p in fp.Pads()): continue
        r = fp.GetReference()
        if r.startswith(('U100', 'MH')): continue
        bb = fp.GetBoundingBox(False, False); cx, cy = bb.GetCenter().x/1e6, bb.GetCenter().y/1e6
        if not (X0 < cx < X1 and Y0 < cy < Y1): continue
        horiz = bb.GetWidth() >= bb.GetHeight()
        ty = cy - bb.GetHeight()/2e6 - 0.06 if horiz else cy
        ax.text(cx if horiz else cx + bb.GetWidth()/2e6 + 0.05, ty, r, ha='center' if horiz else 'left', va='bottom' if horiz else 'center',
                fontsize=6, color='#6c757d', zorder=8, path_effects=[pe.withStroke(linewidth=1.4, foreground='white')])
    if HL:      # open connections: minimum spanning tree over each highlighted net's copper clusters (pcbnew connectivity)
        conn = b.GetConnectivity()
        for net in HL:
            n = b.FindNet(net)
            if n is None: continue
            items = [p for fp in b.GetFootprints() for p in fp.Pads() if p.GetNetname() == net]
            clusters = []
            for p in items:
                if any(p.m_Uuid.AsString() in c[0] for c in clusters): continue
                ids = {p.m_Uuid.AsString()} | {o.m_Uuid.AsString() for o in conn.GetConnectedItems(p)}
                clusters.append((ids, [(q.GetPosition().x/1e6, q.GetPosition().y/1e6) for q in items if q.m_Uuid.AsString() in ids]))
            if len(clusters) < 2: continue
            inT = {0}
            while len(inT) < len(clusters):
                best = None
                for a in inT:
                    for k in range(len(clusters)):
                        if k in inT: continue
                        for pa in clusters[a][1]:
                            for pb in clusters[k][1]:
                                d = math.dist(pa, pb)
                                if best is None or d < best[0]: best = (d, k, pa, pb)
                inT.add(best[1]); pa, pb = best[2], best[3]
                ax.plot([pa[0], pb[0]], [pa[1], pb[1]], ls=(0, (3, 2)), lw=0.9, color=col(alias(net)), zorder=9)
    ax.set_xlim(X0, X1); ax.set_ylim(Y1, Y0); ax.set_aspect('equal'); ax.set_title(name, fontsize=12, color='#1d232a')
    ax.tick_params(labelsize=7, colors='#6c757d')
    for s in ax.spines.values(): s.set_color('#ced4da')
# legend: colour groups, then alias = full net name
full = {}
for n in sorted(used | routed): full.setdefault(alias(n), n.replace('{slash}', '/'))
order = sorted(full, key=lambda a: (a == 'GND', GROUP.get(a, 5), a))
def nice(n):
    m = re.match(r'Net-\((\w+?)(?:Power|System|Unused.*?)?-(.*)\)$', n)
    return f'{m.group(2)} ({m.group(1)} pin net)' if m else n
h = [Patch(fc=tint(col(a)), ec=col(a), label=f'{a} = {nice(full[a])}') for a in order]
fig.legend(handles=h, loc='lower center', ncol=5, fontsize=8, frameon=False)
fig.suptitle(TITLE, fontsize=13, color='#1d232a')
plt.tight_layout(rect=(0, 0.07, 1, 0.97)); plt.savefig(OUT, dpi=DPI, facecolor='white'); print('written', OUT, len(order), 'nets')
