import json, re, html
W = 'scratch/worklist'
items = json.load(open(W + '/items.json'))
crops = {int(k): v for k, v in json.load(open(W + '/crops.json')).items()}

def human(desc):
    m = re.match(r'Pad (\S+) \[[^\]]*\] of (\S+) on (\S+)', desc)
    if m: return '%s pad %s' % (m.group(2), m.group(1)), m.group(3)
    m = re.match(r'Track \[[^\]]*\] on (\S+), length (\S+)', desc)
    if m: return 'Track end', m.group(1)
    if desc.startswith('Via'): return 'Via', 'F.Cu–B.Cu'
    if desc.startswith('Zone'): return 'GND fill piece', 'F.Cu'
    return desc[:40], ''

H = {1: 'Drop a GND via right next to C6 pad 2, or move the track that cuts this pad off from the F.Cu GND fill.',
 2: 'Drop a GND via next to U7 pad 2 (the 1.8 V buck’s ground pin). Keep it short, because it carries the switching return current.',
 3: 'Two pieces of the top-layer GND fill have no via to the In1 plane. Find them in KiCad’s DRC “Unconnected items” list (they show as Zone ↔ Zone) and put one stitching via in each.',
 4: 'U100 pin 57 is a ground pin at 0.35 mm pitch. Run a 0.2 mm stub straight out of the pin and join the C611 GND track, or put a via just past the pin row.',
 5: 'Same as row 3: a second isolated top-layer GND piece that needs a stitching via.',
 6: 'VSYS between C16 and C19 next to the charger. A short F.Cu link, at least 0.3 mm wide; nudge C16 if it’s in the way.',
 7: 'U100 pins 71 and 67 are both VDD_0V9, 1.4 mm apart on the right side. Link them with a 0.2 mm track just outside the pin row.',
 8: 'From pin 71, a 0.2 mm stub out to a via that lands on the In2 VDD_0V9 island under the SoC.',
 9: 'A VCC5V0_SYS via about 0.3 mm left of U4 pin 3 blocks the only exit. Move that via (or reroute its short stub), then route FB to R15 pad 2. Keep FB away from the SW node.',
 10: 'U4 pin 8 (ILIM) down to R14 pad 1. Same tight spot as FB; do it right after row 9.',
 11: 'U100 pin 24 (SARADC/USB AVDD 1.8 V) to C602 pad 1. Nudge C602 closer to the pin if there’s no path.',
 12: 'R601 pad 1 to C602 pad 1: the filter path for the same AVDD rail.',
 13: 'VCC_3V3: join two track ends at the SoC’s left side. A 0.2 mm track, or a via to the 3V3 run on In2 nearby.',
 14: 'VCC_3V3: F.Cu track end to the In2 3V3 track. One via at the F.Cu end usually does it.',
 15: 'VCC_3V3 at C632 (SoC decoupling, bottom-right). Link C632 pad 1 to the 3V3 track just below it.',
 16: 'VCC_1V8 pin 53 (bottom side) to the In2 1.8 V track at (147.1, 151.0): a 0.2 mm stub and one via.',
 17: 'VCC_1V8 pins 53 and 70 on two different sides; joining them through the In2 1.8 V run is enough.',
 18: 'SD_D1: about 26 mm from U100’s left side to the microSD socket. Route it with the other SD lines; they get length-matched in the quality pass anyway.',
 19: 'SD_D3: about 27 mm, same path as SD_D1.',
 20: 'USB D+ from U100 pin 27 to the series resistor R508. If convenient, reroute D− with it as a coupled pair in the USB90 class (0.155 mm, 0.127 mm gap); otherwise it is done in the quality pass.',
 21: 'Two ILIM_HIZ tracks on different layers end at the same point with no via. Add one via at (128.04, 152.97).',
 22: 'Same net, second spot: add one via at (128.04, 153.70).',
 23: 'U2 pin 9 is VAC1, the USB VBUS sense input (low current). A 0.15–0.2 mm track up to the VBUS track at (125.2, 166.4).',
 24: 'Two PMID tracks on different layers meet with no via. Add one via at (119.5, 158.8).'}
groups = [('quick', 'Quick: missing vias', 'Tracks already meet; they just need a via. A minute each.', [21, 22, 24]),
 ('gnd', 'Ground', 'Pads or fill pieces with no path to the In1 ground plane.', [1, 2, 4, 3, 5]),
 ('boost', 'Boost converter (U4)', 'One blocking via boxes in two feedback-side pins.', [9, 10]),
 ('soc', 'Processor supplies (U100)', 'Short 0.2 mm stubs out of 0.35 mm-pitch pins. SoCPower class: 0.2 mm track, 0.12 mm clearance.', [7, 8, 11, 12, 13, 14, 15, 16, 17]),
 ('chg', 'Charger area', 'Short low-current links near U2.', [6, 23]),
 ('sig', 'Signals', 'USB D+ and the two long SD data lines.', [20, 18, 19])]
assert sorted(sum((g[3] for g in groups), [])) == list(range(1, 25))
by = {it['k']: it for it in items}

def card(k):
    it = by[k]; a = human(it['a']); b = human(it['b']); c = crops.get(k); pts = [tuple(p) for p in it['pts']]
    coords = ' → '.join('(%.2f, %.2f)' % p for p in pts) if pts else 'no single location (fill pieces)'
    if c:
        marks = ''.join('<circle cx="%.2f" cy="%.2f" r="2.6"/><text x="%.2f" y="%.2f">%s</text>' % (
            (p[0]-c['x'])/c['s']*100, (p[1]-c['y'])/c['s']*100, (p[0]-c['x'])/c['s']*100 + 3.4, (p[1]-c['y'])/c['s']*100 - 2.6, 'AB'[i]) for i, p in enumerate(pts))
        img = ('<figure class="crop"><img src="img/u%02d.png" alt="Board area around gap %d, about %.0f mm across" loading="lazy" width="381" height="381">'
               '<svg viewBox="0 0 100 100" aria-hidden="true">%s</svg><figcaption>%.0f × %.0f mm window</figcaption></figure>') % (k, k, c['s'], marks, c['s'], c['s'])
    else:
        img = '<div class="crop nocrop"><p>No single spot to show: KiCad reports this one as two pieces of top-layer fill. Find it in the DRC “Unconnected items” list.</p></div>'
    return ('<article class="card" id="gap-%d">%s<div class="body"><div class="head"><span class="k">%d</span><code class="net">%s</code>'
            '<label class="done"><input type="checkbox" id="done-%d"> Done</label></div>'
            '<dl><dt>A</dt><dd>%s <span class="lay">%s</span></dd><dt>B</dt><dd>%s <span class="lay">%s</span></dd><dt>at</dt><dd class="xy">%s</dd></dl>'
            '<p class="hint">%s</p></div></article>') % (k, img, k, html.escape(it['net']), k, html.escape(a[0]), a[1], html.escape(b[0]), b[1], coords, html.escape(H[k]))

ov = []
for it in items:
    if not it['pts']: continue
    x = sum(p[0] for p in it['pts'])/len(it['pts']); y = sum(p[1] for p in it['pts'])/len(it['pts'])
    ov.append('<a href="#gap-%d" aria-label="Gap %d"><circle cx="%.2f" cy="%.2f" r="1.5"/><text x="%.2f" y="%.2f">%d</text></a>' % (it['k'], it['k'], x, y, x, y + 0.5, it['k']))
secs = ''.join('<section class="group" id="%s"><div class="ghead"><h2>%s</h2><p>%s</p></div><div class="cards">%s</div></section>' % (gid, t, dsc, ''.join(card(k) for k in ks)) for gid, t, dsc, ks in groups)
toc = ''.join('<a href="#%s">%s <span>%d</span></a>' % (gid, t.split(':')[0], len(ks)) for gid, t, dsc, ks in groups)
page = open(W + '/template.html').read().replace('MARKERS', ''.join(ov)).replace('SECTIONS', secs).replace('TOCLINKS', toc)
open(W + '/index.html', 'w').write(page)
print(len(page), 'bytes')
