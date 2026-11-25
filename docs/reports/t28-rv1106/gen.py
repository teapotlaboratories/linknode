"""Build the T28 RV1106 placement report (index.html) from data.json, the plotted SVGs and the netlist pin names.
Run measure.py and plot_svg.py first. Usage: python3 gen.py <netlist.xml>"""
import json, sys, math, html, xml.etree.ElementTree as ET
D = json.load(open('data.json')); N, B = D['now'], D['before']
root = ET.parse(sys.argv[1]).getroot()
pinfn = {}
for n in root.iter('net'):
    for x in n.findall('node'):
        if x.get('ref') == 'U100': pinfn[x.get('pin')] = (x.get('pinfunction') or '').rsplit('_', 1)[0]
def dist(a, b): return math.hypot(a[0]-b[0], a[1]-b[1])
def short(net):
    s = net.replace('{slash}', '/')
    if s.startswith('Net-('): s = s.split('-', 2)[-1].rstrip(')')
    return s
rows = []
for g, gb in zip(N['groups'], B['groups']):
    first, fb = g['parts'][0], gb['parts'][0]
    after = first.get('path'); before = fb['pin_to_pad']
    v2c = round(dist(g['via'], first['pad']), 2) if g['via'] and first['side'] == 'B' else None
    p2v = round(dist(g['pin'], g['via']), 2) if g['via'] else None
    rows.append(dict(pins='/'.join(g['pins']), fn=' / '.join(sorted(set(pinfn.get(p, '') for p in g['pins']))), net=g['net'], netshort=short(g['net']),
                     parts=[(e['ref'], e['val'], e['side'], e.get('path') or e['pin_to_pad']) for e in g['parts']],
                     before=before, after=after, p2v=p2v, v2c=v2c, side=first['side']))
supply = [r for r in rows if r['after'] is not None]
p2v = [r['p2v'] for r in supply]; v2c = [r['v2c'] for r in supply]; aft = [r['after'] for r in supply]; bef = [r['before'] for r in supply]
nbottom = sum(1 for r in rows for p in r['parts'] if p[2] == 'B') + sum(1 for k, v in N['bulk'].items() if v['side'] == 'B')
board = N['board']; bc = ((board[0]+board[2])/2, (board[1]+board[3])/2); soc_off = dist(N['U100'], bc)
M = N['misc']
T30 = json.load(open('t30.json'))
WHY = {'Y502': 'RTC crystal above the USB channel, ~5 mm from pins 20/21', 'C503': 'load cap with Y502', 'C504': 'load cap with Y502',
       'R510': 'SARADC pull-up beside its pin group', 'C507': 'SARADC filter beside its pin group', 'TP501': 'recovery test point beside SARADC',
       'R506': 'VBUSDET divider, VBUS end below the channel', 'R507': 'VBUSDET divider beside pin 25', 'C506': 'VBUSDET filter beside pin 25',
       'R508': 'USB D+ series R, stacked with R509 just past the fan-out', 'R509': 'USB D− series R, stacked with R508', 'R511': 'SD clock series R, moved past the pin fan-out'}
import collections
UNCON = len(json.load(open(sys.argv[2]))['unconnected_items']) if len(sys.argv) > 2 else '?'
def f2(x): return '%.2f' % x

# ---------- dumbbell chart (before: hollow ring, after: filled dot), one row per supply-pin group, sorted by pin
ch = sorted(supply, key=lambda r: int(r['pins'].split('/')[0]))
W, LM, RM, TM, RH = 640, 150, 24, 30, 19
H = TM + RH*len(ch) + 34; XMAX = 7.0
def X(v): return LM + (W-LM-RM)*v/XMAX
cs = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-labelledby="chart-title chart-desc">' % (W, H),
      '<desc id="chart-desc">For each RV1106 supply pin, distance from the pin to its decoupling capacitor before T28 (top side, straight line) and after (pin to via to bottom-side capacitor pad).</desc>']
for t in range(0, 8):
    cs.append('<line class="grid" x1="%.1f" x2="%.1f" y1="%d" y2="%d"/>' % (X(t), X(t), TM-6, TM+RH*len(ch)))
    cs.append('<text class="tick" x="%.1f" y="%d">%d</text>' % (X(t), TM+RH*len(ch)+16, t))
cs.append('<text class="axis" x="%.1f" y="%d">mm from pin to capacitor pad</text>' % ((LM+W-RM)/2, H-2))
cs.append('<rect class="target" x="%.1f" y="%d" width="%.1f" height="%d"/>' % (X(0), TM-6, X(1.5)-X(0), RH*len(ch)+6))
cs.append('<text class="tlabel" x="%.1f" y="%d">1.5 mm (T28 target)</text>' % (X(1.5)+4, TM-10))
for i, r in enumerate(ch):
    y = TM + RH*i + RH/2
    lab = 'pin %s · %s' % (r['pins'], r['parts'][0][0])
    tip = 'Pin %s (%s): %s %s. Before %s mm on top, after %s mm (pin→via %s, via→pad %s).' % (r['pins'], r['fn'], r['parts'][0][0], r['parts'][0][1], f2(r['before']), f2(r['after']), f2(r['p2v']), f2(r['v2c']))
    cs.append('<g class="row" tabindex="0" data-tip="%s"><rect class="hit" x="0" y="%.1f" width="%d" height="%d"/>' % (html.escape(tip), y-RH/2, W, RH))
    cs.append('<text class="rl" x="%d" y="%.1f">%s</text>' % (LM-10, y+4, html.escape(lab)))
    cs.append('<line class="link" x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f"/>' % (X(r['after']), X(r['before']), y, y))
    cs.append('<circle class="bef" cx="%.1f" cy="%.1f" r="4.5"/><circle class="aft" cx="%.1f" cy="%.1f" r="4.5"/></g>' % (X(r['before']), y, X(r['after']), y))
cs.append('</svg>')
chart = ''.join(cs)

# ---------- table
tr = []
for r in sorted(rows, key=lambda r: int(r['pins'].split('/')[0])):
    parts = '<br>'.join('%s <span class="mut">%s</span>%s' % (p[0], html.escape(p[1]), '' if p[2] == 'B' else ' <span class="pill warn">top</span>') for p in r['parts'])
    if r['after'] is None: st = '<span class="pill note">route</span>'
    else: st = '<span class="pill ok">linked</span>'
    tr.append('<tr data-net="%s"><td class="num">%s</td><td>%s</td><td>%s</td><td>%s</td><td class="num">%s</td><td class="num">%s</td><td class="num">%s</td><td>%s</td></tr>' % (
        html.escape(r['net']), r['pins'], html.escape(r['fn']), html.escape(r['netshort']), parts, f2(r['before']),
        '–' if r['p2v'] is None else f2(r['p2v']), '–' if r['after'] is None else f2(r['after']), st))
table = ''.join(tr)

y501, y502 = M['Y501'], M['Y502']
ctx = dict(
    NSUP=len(supply), NBOT=nbottom, AMIN=f2(min(aft)), AMAX=f2(max(aft)), BMIN=f2(min(bef)), BMAX=f2(max(bef)),
    P2VMIN=f2(min(p2v)), P2VMAX=f2(max(p2v)), V2CMIN=f2(min(v2c)), V2CMAX=f2(max(v2c)),
    NWITHIN=sum(1 for a in aft if a <= 1.5), NOVER=sum(1 for a in aft if a > 1.5),
    SOCOFF='%.1f' % soc_off, C505=f2([p for r in rows for p in r['parts'] if p[0] == 'C505'][0][3]),
    R503=f2([p for r in rows for p in r['parts'] if p[0] == 'R503'][0][3]),
    Y501UNDER=len(y501['tracks_under']), Y502UNDER=len(y502['tracks_under']),
    Y501LIST=', '.join('%s (%s)' % (short(n), l) for n, l in y501['tracks_under']),
    Y502LIST=', '.join('%s (%s)' % (short(n), l) for n, l in y502['tracks_under']),
    Y501GV=' and '.join(f2(v) for v in y501['gnd_via_mm']),
    C505S=f2([e for gg in N['groups'] for e in gg['parts'] if e['ref'] == 'C505'][0]['pin_to_pad']),
    R503S=f2([e for gg in N['groups'] for e in gg['parts'] if e['ref'] == 'R503'][0]['pin_to_pad']),
    VIPSOC=', '.join(sorted(set(v['ref'] for v in N['via_in_pad'] if v['side'] == 'B' and dist(v['pos'], N['U100']) < 9))),
    NVIPSOC=len(set(v['ref'] for v in N['via_in_pad'] if v['side'] == 'B' and dist(v['pos'], N['U100']) < 9)),
    NVIP=len(N['via_in_pad']), NVIPSIG=len([v for v in N['via_in_pad'] if v['net'] not in ('GND', '')]),
    R604S=f2([e for gg in N['groups'] for e in gg['parts'] if e['ref'] == 'R604'][0]['pin_to_pad']),
    UNCON=UNCON,
    USBDP=f2(T30['usb']['/SoC/USB_DP'] + T30['usb']['Net-(U100System-USB_DP)']), USBDM=f2(T30['usb']['/SoC/USB_DM'] + T30['usb']['Net-(U100System-USB_DM)']),
    USBSKEW=f2(abs(T30['usb']['/SoC/USB_DP'] + T30['usb']['Net-(U100System-USB_DP)'] - T30['usb']['/SoC/USB_DM'] - T30['usb']['Net-(U100System-USB_DM)'])),
    SDSPREAD=f2(max(T30['sd'].values()) - min(T30['sd'].values())), SDIOSPREAD=f2(max(T30['sdio'].values()) - min(T30['sdio'].values())),
    T30MOVES=''.join('<tr><td>%s</td><td>%s</td><td class="num">%.2f, %.2f</td><td class="num">%.2f, %.2f</td><td>%s</td></tr>' % (r, html.escape(v['val']), v['from'][0], v['from'][1], v['to'][0], v['to'][1], WHY.get(r, ''))
                     for r, v in T30['moved'].items() if v['from'] != v['to']),
    R511=f2(T30['r511_to_pin15']), R501=f2(M['R501']['to_pin'][0]), C604=f2(M['C604']['to_pin'][0]),
    CHART=chart, TABLE=table, AFTER=open('img/after.svg').read(), BEFORE=open('img/before.svg').read())
page = open('template.html').read()
for k, v in ctx.items(): page = page.replace('{{%s}}' % k, str(v))
open('index.html', 'w').write(page)
missing = [s for s in page.split('{{')[1:]]
print('wrote index.html', len(page)//1024, 'KB', 'unfilled:', [m.split('}}')[0] for m in missing][:5])
print({k: v for k, v in ctx.items() if k not in ('CHART', 'TABLE', 'AFTER', 'BEFORE')})
