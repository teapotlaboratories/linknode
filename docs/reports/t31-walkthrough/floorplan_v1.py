"""T32 first-cut floorplan, drawn to scale as an inline SVG (mm). Blocks are sized from the measured top-side courtyard
area per sheet at ~70 % coverage; modules and connectors at their real courtyard sizes. Prints the <svg> and checks overlaps."""
W, H = 70.0, 64.0
B = [  # name, x, y, w, h, kind
 ('MH1', 0, 0, 7, 7, 'mh'), ('MH2', 63, 0, 7, 7, 'mh'), ('MH3', 0, 41, 7, 7, 'mh'), ('MH4', 63, 57, 7, 7, 'mh'),
 ('J2 DC jack', 1, 48, 11.6, 16, 'conn'), ('J1 USB-C', 14, 54.5, 10.7, 9.5, 'conn'), ('SW1 PWR', 26, 58.3, 7.6, 5.7, 'conn'), ('J401 microSD', 44, 48, 17.8, 16, 'conn'),
 ('J3 battery', 0, 8, 10.9, 11.1, 'conn'), ('J4 NTC', 0, 20, 10.9, 11.1, 'conn'),
 ('U701 HaLow', 12, 0, 20.5, 15.9, 'module'), ('J901', 33, 0, 4.8, 4.7, 'conn'),
 ('U801 ESP32-C5', 42, 0, 19.8, 23, 'module'),
 ('U20 GPS', 58, 25, 11.9, 10.7, 'module'), ('J20', 64, 37, 5, 4.7, 'conn'),
 ('U100 RV1106 + crystals', 33, 25, 22, 21, 'soc'),
 ('Charger, input, ESD', 13, 34, 19, 19.5, 'power'),
 ('Battery protect, hold-off', 12, 17, 11, 16, 'power'),
 ('Bucks, boost', 24, 17, 8.5, 16, 'power'), ('Radio power', 33.5, 5.5, 8, 18.5, 'power'),
 ('GPS LDOs', 58, 42, 6, 5, 'power'),
 ('Bucks (2)', 34, 47, 9.5, 11, 'power'), ('Hold-off (2)', 7, 32, 5, 9, 'power'),
]
COL = {'mh': '#9aa29b', 'conn': '#b4692c', 'module': '#3b6fc0', 'soc': '#1d6a46', 'power': '#8a5cb8'}
def overlaps():
    bad = []
    for i, a in enumerate(B):
        for b in B[i+1:]:
            if a[1] < b[1]+b[3] and b[1] < a[1]+a[3] and a[2] < b[2]+b[4] and b[2] < a[2]+a[4]: bad.append((a[0], b[0]))
        if a[1] < 0 or a[2] < 0 or a[1]+a[3] > W+0.01 or a[2]+a[4] > H+0.01: bad.append((a[0], 'outline'))
    return bad
s = ['<svg class="fp" viewBox="-2 -2 %g %g" role="img" aria-label="First-cut floorplan, %g by %g mm">' % (W+4, H+6, W, H),
     '<rect x="0" y="0" width="%g" height="%g" fill="none" stroke="currentColor" stroke-width="0.35"/>' % (W, H)]
for n, x, y, w, h, k in B:
    s.append('<rect x="%g" y="%g" width="%g" height="%g" rx="0.6" fill="%s" fill-opacity="0.22" stroke="%s" stroke-width="0.25"/>' % (x, y, w, h, COL[k], COL[k]))
    fs = 1.5 if w > 9 else 1.1
    s.append('<text x="%g" y="%g" font-size="%g" text-anchor="middle" fill="currentColor">%s</text>' % (x+w/2, y+h/2+0.5, fs, n if w > 6 else n.split()[0]))
s.append('<text x="%g" y="%g" font-size="1.6" text-anchor="middle" fill="currentColor">connector edge (USB-C, DC jack, PWR, microSD)</text>' % (W/2, H+3.2))
s.append('</svg>')
print('\n'.join(s)); import sys; print('overlaps:', overlaps(), file=sys.stderr)
