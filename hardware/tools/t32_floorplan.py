"""T32: floorplan drawing (inline SVG, mm units, theme-aware text) from a placed board: every top part's courtyard filled
by functional group, a dashed outline around each group, sheet labels at each sheet's centre, board dimensions.
Usage: t32_floorplan.py board.kicad_pcb [bottom] > floorplan.svg   (bottom: the underside, seen from the top)"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); eb = b.GetBoardEdgesBoundingBox()
BOTTOM = len(sys.argv) > 2 and sys.argv[2] == 'bottom'
X0, Y0, X1, Y1 = eb.GetLeft()/1e6, eb.GetTop()/1e6, eb.GetRight()/1e6, eb.GetBottom()/1e6
GROUP = {'HaLow': 'Radios', 'Antenna': 'Radios', 'ESP32-C5': 'Radios', 'GPS': 'Radios',
         'Power': 'Power', 'Radio Power': 'Power', 'USB and Charger': 'Power', 'Battery': 'Power', 'Hold-off': 'Power',
         'SoC': 'RV1106', 'SoC Power': 'RV1106', 'microSD': 'RV1106'}
CONN = {'J1', 'J2', 'J3', 'J4', 'J401', 'SW1', 'J501', 'J901', 'J20'}
COL = {'Radios': '#3b6fc0', 'Power': '#8a5cb8', 'RV1106': '#1d6a46', 'Connectors': '#b4692c', 'Holes': '#8f978f'}
LABEL = {'SoC Power': 'RV1106 decoupling', 'HaLow': 'HaLow', 'ESP32-C5': 'ESP32-C5', 'GPS': 'GPS', 'Antenna': 'RF filter', 'Power': 'bucks + boost',
         'Radio Power': 'radio power', 'USB and Charger': 'charger + input', 'Battery': 'battery protect', 'Hold-off': 'hold-off',
         'SoC': 'RV1106', 'microSD': 'SD switch'}
CONN_LABEL = {'J1': 'USB-C', 'J2': 'DC in', 'J3': 'BAT', 'J4': 'NTC', 'J401': 'microSD', 'SW1': 'PWR', 'J501': 'debug', 'J901': 'U.FL', 'J20': 'U.FL'}
def crt(f):
    xs = []; ys = []
    for g in f.GraphicalItems():
        if g.GetLayer() == (pcbnew.B_CrtYd if BOTTOM else pcbnew.F_CrtYd): r = g.GetBoundingBox(); xs += [r.GetLeft(), r.GetRight()]; ys += [r.GetTop(), r.GetBottom()]
    return (min(xs)/1e6, min(ys)/1e6, max(xs)/1e6, max(ys)/1e6) if xs else None
parts = []
for f in b.GetFootprints():
    r = f.GetReference()
    if f.IsFlipped() != BOTTOM and not (BOTTOM and f.GetReference().startswith('MH')): continue
    c = crt(f) if not (BOTTOM and f.GetReference().startswith('MH')) else None
    if BOTTOM and f.GetReference().startswith('MH'):
        bb = f.GetBoundingBox(False, False); c = (bb.GetLeft()/1e6, bb.GetTop()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6)
    if not c: continue
    g = 'Holes' if r.startswith('MH') else 'Connectors' if r in CONN else 'RV1106' if r == 'R19' else GROUP.get(f.GetSheetname(), 'Power')
    parts.append((r, f.GetSheetname(), g, c))
s = ['<svg class="fp" viewBox="%g %g %g %g" role="img" aria-label="Floorplan of the trial placement, %.0f by %.0f mm">' % (X0 - 6, Y0 - 6, X1 - X0 + 12, Y1 - Y0 + 13, X1 - X0, Y1 - Y0),
     '<rect x="%g" y="%g" width="%g" height="%g" rx="2" fill="none" stroke="currentColor" stroke-width="0.35"/>' % (X0, Y0, X1 - X0, Y1 - Y0)]
for r, sh, g, (l, t, rr, bt) in parts:
    s.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="0.3" fill="%s" fill-opacity="%s" stroke="%s" stroke-width="0.12"/>'
             % (l, t, rr - l, bt - t, COL[g], '0.55' if g in ('Connectors', 'Holes') else '0.3', COL[g]))
    if g == 'Connectors': s.append('<text x="%.2f" y="%.2f" font-size="1.7" text-anchor="middle" fill="currentColor">%s</text>' % ((l + rr)/2, (t + bt)/2 + 0.6, CONN_LABEL[r]))
# group regions: union of the group's courtyards grown by 0.8 mm, on a 0.25 mm raster; filled as row runs, edged by
# the raster boundary (test points left out so a stray one doesn't stretch the region)
import numpy as np
RES, GROW = 0.25, 0.8
NX, NY = int((X1 - X0)/RES) + 1, int((Y1 - Y0)/RES) + 1
def region(g):
    m = np.zeros((NY, NX), bool)
    for r, sh, gg, (l, t, rr, bt) in parts:
        if gg != g or r.startswith('TP'): continue
        i0, j0 = max(0, int((l - GROW - X0)/RES)), max(0, int((t - GROW - Y0)/RES))
        i1, j1 = min(NX, int((rr + GROW - X0)/RES) + 1), min(NY, int((bt + GROW - Y0)/RES) + 1)
        m[j0:j1, i0:i1] = True
    k = 4                               # 1 mm closing (grow then shrink) fills the small holes between parts
    def grow(a, inv=False):
        a = ~a if inv else a; o = a.copy()
        for dj in range(-k, k + 1):
            for di in range(-k, k + 1):
                o |= np.roll(np.roll(a, dj, 0), di, 1)
        return ~o if inv else o
    return grow(grow(m), inv=True) & (np.ones_like(m))
for g in ('Radios', 'Power', 'RV1106'):
    m = region(g); runs = []; edges = []
    for j in range(NY):
        i = 0
        while i < NX:
            if m[j, i]:
                k = i
                while k < NX and m[j, k]: k += 1
                runs.append('M%.2f %.2fh%.2fv%.2fh%.2fz' % (X0 + i*RES, Y0 + j*RES, (k - i)*RES, RES, -(k - i)*RES)); i = k
            else: i += 1
    P = np.pad(m, 1)
    for j in range(NY + 1):            # horizontal boundary segments between row j-1 and j
        diff = P[j, 1:-1] != P[j + 1, 1:-1]; i = 0
        while i < NX:
            if diff[i]:
                k = i
                while k < NX and diff[k]: k += 1
                edges.append('M%.2f %.2fH%.2f' % (X0 + i*RES, Y0 + j*RES, X0 + k*RES)); i = k
            else: i += 1
    for i in range(NX + 1):            # vertical boundary segments between column i-1 and i
        diff = P[1:-1, i] != P[1:-1, i + 1]; j = 0
        while j < NY:
            if diff[j]:
                k = j
                while k < NY and diff[k]: k += 1
                edges.append('M%.2f %.2fV%.2f' % (X0 + i*RES, Y0 + j*RES, Y0 + k*RES)); j = k
            else: j += 1
    s.insert(2, '<path d="%s" fill="%s" fill-opacity="0.10" stroke="none"/>' % (''.join(runs), COL[g]))
    s.append('<path d="%s" fill="none" stroke="%s" stroke-width="0.4"/>' % (''.join(edges), COL[g]))
# sheet labels at each sheet's centre (modules labelled by their own name)
for sh, lab in LABEL.items():
    if sh == 'SoC Power' and not BOTTOM: continue
    cs = [c for r, s2, g, c in parts if s2 == sh and g not in ('Connectors', 'Holes') and not r.startswith('TP') and r != 'R19']
    if sh == 'SoC' and not BOTTOM: cs = [c for r, s2, g, c in parts if r == 'U100']
    if not cs: continue
    cx = sum((c[0] + c[2])/2 for c in cs)/len(cs); cy = sum((c[1] + c[3])/2 for c in cs)/len(cs)
    big = sh in ('HaLow', 'ESP32-C5', 'GPS', 'SoC')
    s.append('<text x="%.2f" y="%.2f" font-size="%s" font-weight="%s" text-anchor="middle" fill="currentColor" style="paint-order:stroke;stroke:var(--paper);stroke-width:0.6px">%s</text>'
             % (cx, cy + 0.7, '2.4' if big else '1.8', '600' if big else '500', lab))
# dimensions
s.append('<path d="M%g %g H%g M%g %g v1.6 M%g %g v1.6" stroke="currentColor" stroke-width="0.2" fill="none"/>' % (X0, Y1 + 3.5, X1, X0, Y1 + 2.7, X1, Y1 + 2.7))
s.append('<text x="%g" y="%g" font-size="2" text-anchor="middle" fill="currentColor">%.0f mm · connector edge</text>' % ((X0 + X1)/2, Y1 + 6.2, X1 - X0))
s.append('<path d="M%g %g V%g M%g %g h1.6 M%g %g h1.6" stroke="currentColor" stroke-width="0.2" fill="none"/>' % (X0 - 3.5, Y0, Y1, X0 - 4.3, Y0, X0 - 4.3, Y1))
s.append('<text x="%g" y="%g" font-size="2" text-anchor="middle" fill="currentColor" transform="rotate(-90 %g %g)">%.0f mm</text>' % (X0 - 4.4, (Y0 + Y1)/2, X0 - 4.4, (Y0 + Y1)/2, Y1 - Y0))
s.append('</svg>')
print('\n'.join(s))
