"""Rebuild the walkthrough page with final decisions only (owner, 2026-11-23): no history, no before/after, no superseded
options. Keeps the page's <head>/style and the lightbox script; reuses the final-state reference figures; audit tables
from today's board (blk2/3/4_audit.py JSON)."""
import re, json, sys
P = '/home/argonite/Developments/klepon/docs/reports/t31-walkthrough/index.html'
A = 'scratch/audit'
old = open(P).read()
head = old[:old.index('<header>')]
tail = old[old.index('<footer>'):]
def grab(start, end, src=old):
    i = src.index(start); j = src.index(end, i) + len(end); return src[i:j]
def fig(start):
    """one <figure>…</figure> that contains `start`"""
    i = old.index(start); a = old.rindex('<figure>', 0, i); b = old.index('</figure>', i) + len('</figure>'); return old[a:b]

def audit(n, group_label):
    d = json.load(open('%s/blk%d.json' % (A, n)))
    rows = []
    for r in d['rows']:
        lim = ('≥ ' if r['more'] else '≤ ') + ('%g' % r['lim']) if r['kind'] == 'rule' else ''
        ver = ('<td class="good">pass</td>' if r['ok'] else '<td class="bad">fail</td>') if r['kind'] == 'rule' else '<td>info</td>'
        src = r['src'].replace('schematic has none', 'U401/U402 at the socket')
        dd = r['d']
        if r['what'].startswith('ESD on the TF card'): dd = 'fitted'
        rows.append('<tr><td>%s</td><td>%s</td><td class=n>%s (%s)</td><td class=n>%s</td><td class=n>%s</td>%s<td>%s</td></tr>' % (
            r['conv'], r['what'], r['ref'], 'top' if r['side'] == 'T' else 'bottom', dd, lim, ver, src))
    return ('<details><summary>All %d audit rows on today’s board (pad-centre distances, mm): %d of %d rule checks fail</summary>\n'
            '  <div class="tablewrap"><table>\n    <thead><tr><th>%s</th><th>Check</th><th>Part</th><th>mm</th><th>Limit</th><th>Result</th><th>Source</th></tr></thead>\n'
            '    <tbody>\n%s\n    </tbody></table></div>\n  <p style="color:var(--muted)">Tool: <code>hardware/tools/blk%d_audit.py</code>.</p>\n  </details>') % (
            len(d['rows']), d['fails'], d['total'], group_label, '\n'.join(rows), n)
a2, a3, a4 = (json.load(open('%s/blk%d.json' % (A, n))) for n in (2, 3, 4))

def sec(sid, status, num, h2, intro, tldr, body):
    pill = '<span class="badge">Current step · awaiting your approval</span>' if status == 'current' else '<span class="pill ok">approved</span>'
    cls = 'current' if status == 'current' else 'approved'
    tl = '<div class="tldr"><b>TL;DR</b><ul class="tight">\n' + '\n'.join('    <li>%s</li>' % t for t in tldr) + '\n  </ul></div>'
    return ('<section id="%s" class="%s">\n  <div class="shead">%s<span class="num">%s</span>\n  <h2>%s</h2>\n  <p>%s</p></div>\n  %s\n%s\n</section>\n'
            % (sid, cls, pill, num, h2, intro, tl, body))

S = []
# ---------------------------------------------------------------- board today
S.append('''<section id="board" class="approved">
  <div class="shead"><span class="pill ok">current board</span><span class="num">LinkNode Rev 1 · 78 × 62 mm · 4 layers</span>
  <h2>The board today</h2>
  <p>3D renders and KiCad’s own plot of the board as it stands, with every decision below applied. Top: modules, connectors, inductors, crystals and ICs. Bottom: 0402/0603 passives, the RV1106 decoupling ring, the expansion pogo pads and the Teapotlabs branding.</p></div>
  <div class="pair">
    <figure><img src="img/final/3d_top.jpg" alt="3D render, top" width="1568" height="1232" loading="lazy"><figcaption><b>Top</b>: power column left, RV1106 centre, HaLow top, GPS and ESP32-C5 right; DC IN, PWR, USB-C and microSD on the bottom edge.</figcaption></figure>
    <figure><img src="img/final/3d_bottom.jpg" alt="3D render, bottom" width="1568" height="1232" loading="lazy"><figcaption><b>Bottom</b>, seen from below (mirrored): logo and REVISION 1, the 7 × 5 expansion pads, the RV1106 decoupling ring.</figcaption></figure>
    <figure><img src="img/final/3d_iso_front.jpg" alt="3D render, front angle" width="1568" height="1064" loading="lazy"><figcaption><b>Front angle</b>: the connector edge.</figcaption></figure>
    <figure><img src="img/final/3d_iso_back.jpg" alt="3D render, back angle" width="1568" height="1064" loading="lazy"><figcaption><b>Back angle</b>: battery and NTC headers, the U.FL antenna connectors.</figcaption></figure>
  </div>
  <figure><img src="img/route/all_kicad.png" alt="KiCad plot of the whole board with all routing so far" width="4681" height="3811" loading="lazy"><figcaption><b>KiCad plot, whole board</b> (zone fills hidden; top copper red, bottom blue, silkscreen yellow): routing Sections 1 and 2.</figcaption></figure>
</section>
''')
# ---------------------------------------------------------------- block 1
S.append(sec('blk1', 'ok', 'Placement · Block 1', 'Connector edge and mounting holes',
  'All user connectors sit flush on the bottom edge, the battery and NTC headers on the left edge, and one M3 hole in each corner.',
  ['Bottom edge, left to right: DC IN (J2), PWR button (SW1), USB-C (J1), microSD (J401). Left edge: battery (J3) and NTC (J4).',
   'Four M3 holes (Ø3.2 mm, non-plated), centres 3.975 mm from both edges: hole pattern <b>70.05 × 54.05 mm</b> for the enclosure.',
   'USB-C plug to microSD socket: 2.7 mm, room for an enclosure wall between the two openings.'],
  '''  <figure><img src="img/final/edge_bottom.png" alt="KiCad plot of the connector edge" width="4684" height="1100" loading="lazy"><figcaption><b>Connector edge</b>, KiCad plot (top view).</figcaption></figure>
  <figure><img src="img/final/3d_front.jpg" alt="3D render of the connector edge, straight on" width="1800" height="500" loading="lazy"><figcaption><b>Straight on</b>, as the enclosure wall sees it.</figcaption></figure>
  <div class="tablewrap"><table>
    <thead><tr><th>Item</th><th>Value</th></tr></thead>
    <tbody>
      <tr><td>Mounting holes</td><td>4 × Ø3.2 mm, non-plated, no copper; 3.975 mm from both edges; pattern 70.05 × 54.05 mm. Nearest part ≥ 1.1 mm outside the M3 head (Ø5.5 mm).</td></tr>
      <tr><td>DC IN, USB-C, microSD fronts</td><td>Within ±0.2 mm of the bottom edge; the microSD lip 0.5 mm past it.</td></tr>
      <tr><td>Battery and NTC header mouths</td><td>0.05 mm from the left edge.</td></tr>
      <tr><td>PWR button</td><td>0.45 mm inside the edge, pressed from the top (needs a hole or plunger in the lid).</td></tr>
      <tr><td>Clearances between openings</td><td>DC plug ↔ PWR button 1.3 mm; USB-C plug (≤ 12.35 mm wide) ↔ microSD socket 2.7 mm.</td></tr>
    </tbody>
  </table></div>'''))
# ---------------------------------------------------------------- edge margin
S.append(sec('edge', 'ok', 'Board outline · edge margin', 'Board 78 × 62 mm, with room at the top and right edges',
  'Parts keep at least 2.5 mm from the top and right edges; the connector edges (bottom, left) are flush by design.',
  ['Board outline 78 × 62 mm, four corner holes as in Block 1.',
   'Closest to the top edge: R102/R112 (bottom) 2.9 mm. Closest to the right edge: the ESP32-C5 module 2.5 mm.',
   'The expansion pogo pads (bare copper, column 7) are 2.0 mm from the right edge.',
   'Copper pours (GND on top, In1, bottom; 5 V on In2) follow the outline.'],
  '''  <div class="tablewrap"><table>
    <thead><tr><th>Edge</th><th>Closest parts</th><th>Distance</th></tr></thead>
    <tbody>
      <tr><td>Top</td><td>R102 / R112 (radio rail FB resistors, bottom); C702 (HaLow 10 µF, bottom)</td><td class=n>2.9 / 3.0 mm</td></tr>
      <tr><td>Right</td><td>U801 (ESP32-C5 module); U1005 (expansion ESD, bottom); R801, C803 (bottom)</td><td class=n>2.5 / 2.6 / 3.0 / 3.2 mm</td></tr>
      <tr><td>Right</td><td>Expansion pads TP1007…TP1035 (column 7, pad edge)</td><td class=n>2.0 mm</td></tr>
      <tr><td>Left, bottom</td><td>Connectors on the edge, by design</td><td class=n>0</td></tr>
    </tbody>
  </table></div>'''))
# ---------------------------------------------------------------- block 2
b2 = old[old.index('<div class="flow"><b>Power flow</b>'):old.index('  <div class="pair">\n    <figure><img src="img/blk2/before_iso.jpg"')]
b2 = b2.replace('img/blk2/sch_u2.png" alt="Charger schematic, USB and Charger sheet" width="1500" height="1138"', 'img/blk2/sch_u2_v2.png" alt="Charger schematic, USB and Charger sheet" width="1960" height="1560"')
b2 = b2.replace('img/blk2/sch_input.png" alt="Input path schematic" width="1245" height="1011"', 'img/blk2/sch_input_v2.png" alt="Input path schematic" width="1560" height="1250"')
b2 = b2.replace(' The FEM switch Q7 with C120–C122 and R120–R122 went with the loose parts, beside U11 (see the overview).', ' The FEM switch Q7 with C120–C122 and R120–R122 sits beside U11.')
b2 = b2.replace('(the arrows in the layout images point from each section’s power source to its input)', '(the arrows in the layout image point from each section’s power source to its input)')
S.append(sec('blk2', 'ok', 'Placement · Block 2', 'Power: every converter laid out the way TI’s own layout example does it',
  'Each converter is one fixed tile copied from the TI layout example in its datasheet; the six identical bucks share one tile and sit on a grid. Radio rails run along the top, the SoC rails in a 2 × 2 grid, the 5 V boost below them, and the charger between the DC and USB inputs.',
  ['Charger, 5 V boost and six bucks each follow their TI example layout: hot-loop caps at the pins, short SW nodes beside the inductors, FB parts on the bottom away from SW.',
   'TI layout checks on today’s board: <b>%d of %d fail</b> (%d info rows).' % (a2['fails'], a2['total'], a2['info']),
   'Buck inductors stay ≥ 5.5 mm from the HaLow module (closest 5.53 mm).',
   '15 test points (1 mm pads) on the top side.',
   'Routing notes: SW1/SW2 of the charger drop through vias under U2 to an inner layer (TI item 2); every GND cap pad gets its own via to In1.'],
  '''  <figure><img src="img/blk2/v_after.png" alt="Pad-level view of the power column" width="1500" height="2376" loading="lazy"><figcaption><b>Power column</b>, pad level. Pads coloured by role: red SW node, orange input/PMID/SYS, blue output rail, grey GND, green FB; hatched = bottom side. Each converter is outlined and labelled with the rail it makes; arrows ①–⑥ show the power flow (list below).</figcaption></figure>
  <p style="color:var(--muted)">Each limit is set from TI’s own example layout with the same package sizes. Where TI’s example itself has a long distance, the row is <i>info</i> only (for example the TLV62569 GND pin is on the far side of the package from VIN, so Cin returns through the ground pour).</p>
''' + b2 + '  ' + audit(2, 'Converter')))
# ---------------------------------------------------------------- block 3
b3 = old[old.index('  <h3 class="sub">HaLow (U701, HT-HC01 V2)</h3>'):old.index('  <h3 class="sub">3D views after Block 3</h3>')]
b3 = b3.replace(' Moved: C701 (was 20 mm away), C704 (10 mm), C705/C706 (22 mm).', '')
b3 = b3.replace('3V3 (pin 2) pair C802/C803 moved from the power column (66–71 mm away) to the bottom under pin 2. The EN RC and the BOOT pull-up were already at their pins. The module’s right edge is 0.6 mm from the board edge, so these parts go underneath.',
                '3V3 (pin 2) pair C802/C803 on the bottom under pin 2; the EN RC and the BOOT pull-up at their pins. These parts sit under the module edge, on the bottom.')
b3 = b3.replace('U21 now sits beside the module’s VCC pin, with its caps C200/C201 and the 10 µF C202 under the pins on the bottom. The backup LDO U22 moved up, with C204 under the module’s VBAT pin. The U.FL moved down to the RF input.',
                'U21 sits beside the module’s VCC pin, with its caps C200/C201 and the 10 µF C202 under the pins on the bottom. The backup LDO U22 is above it, with C204 under the module’s VBAT pin. The U.FL sits at the RF input.')
S.append(sec('blk3', 'ok', 'Placement · Block 3', 'Radios: every supply pin decoupled at the pin, GPS power and antenna at the module',
  'HaLow (top), GPS and ESP32-C5 (right column) with their decoupling at each supply pin, the GPS LDO at the module and the GPS U.FL at its RF input.',
  ['HaLow and ESP32-C5: each supply pin has its 100 nF + 10/22 µF pair right at the pin (bottom, under the module edge), as the Heltec and Espressif reference schematics show.',
   'GPS: the 3.3 V LDO beside the module’s VCC pin, the backup LDO above it, the U.FL 2.4 mm from RF_IN.',
   'Radio checks on today’s board: <b>%d of %d fail</b>: L20, the GPS antenna bias choke, 3.2 mm from the RF line (limit 2.5), <b>accepted by you</b>. A 3 mm stub is about λ/33 at 1575 MHz; the U.FL body covers the line, so there is no closer spot on top.' % (a3['fails'], a3['total']),
   'Limits: 100 nF ≤ 2.0 mm from its pin, bulk ≤ 3.5 mm (Heltec and the LDO makers give no layout distances); GPS antenna connector ≤ 3.0 mm from RF_IN.'],
  b3 + '  ' + audit(3, 'Module')))
# ---------------------------------------------------------------- block 4
refs4 = old[old.index('  <h3 class="sub">Rockchip references for each rule</h3>'):old.index('  <h3 class="sub">Your review: three fixes</h3>')]
refs4 = refs4.replace(' This is why R511 moved to the RV1106 pin it drives.', ' R511 sits at the RV1106 pin it drives.').replace(' Ours is R506/R507 + C506; C506 now sits next to the pin.', ' Ours is R506/R507 + C506, at the pin.').replace(' Already placed in T29; unchanged.', '')
sch4 = fig('img/blk4/sch_soc.png')
esd_fig = old[old.index('  <div class="sbs">\n    <figure><img src="img/blk4/sch_sd_esd.png"'):old.index('  <h3 class="sub">3D views after Block 4</h3>')]
esd_fig = esd_fig.replace(' ERC 0; the netlist changed only by the ESD pins on 17 nets; no overlaps, no wires through symbols. R403 (DNP) moved left on the DET line to keep its text clear.', '')
S.append(sec('blk4', 'ok', 'Placement · Block 4', 'RV1106 surroundings: series resistors, filter caps and the microSD',
  'Around the RV1106: the decoupling ring, both crystals, the NPOR RC, the USB series resistors and the RTC corner, plus the parts checked against the Rockchip design guide (HDG): series resistors at the transmitter, the ADC and detect filter caps at their pins, and the microSD with ESD.',
  ['R511, the SD clock’s 22 Ω series resistor, 1.6 mm from the RV1106 pin it drives (HDG: series resistors at the transmitter).',
   'C506 (VBUS detect) and C508 (USB-C CC sense) next to their RV1106 input pins: 3.3 and 2.6 mm.',
   'microSD ESD: two DOWO TPD4E05U06DQAR arrays (0.5 pF max, LCSC C22390021) behind the socket, 2.1–5.2 mm from the data pins (card-detect 8.6 mm).',
   'Socket 3D model aligned to the ShouHan drawing; bottom test-pad labels GND / RX / TX on the free side; designators hidden.',
   'Checks on today’s board: <b>%d of %d fail</b> (limits: series R ≤ 3 mm, filter caps ≤ 3.5 mm, the closest spots just outside the RV1106 body).' % (a4['fails'], a4['total'])],
  '''  <div class="sbs">
    ''' + sch4 + '''
    <figure><img src="img/final/blk4_parts.png" alt="RV1106 left side with R511, C506 and C508 marked" width="724" height="1140" loading="lazy"><figcaption><span class="tag us">Layout</span> KiCad plot of the RV1106’s left side: ① R511, ② C506, ③ C508 (bottom). C507 (recovery input) sits at pin 23.</figcaption></figure>
  </div>
''' + refs4 + '''  <h3 class="sub">microSD socket and ESD</h3>
  <p>The socket footprint and 3D model match the ShouHan drawing: pin tails on the pads, side tabs on the side pads, the lip 0.5 mm past the board edge; Q401 (SD power switch) has about 2 mm of clearance. U401 protects CLK, CMD, D0 and D1; U402 protects D2, D3 and card-detect (one channel spare). Each ESD GND pad gets its own via at routing (Rockchip §3.2 item 13).</p>
  <div class="pair">
    ''' + fig('img/blk4/fix_sd_after.png').replace('<b>After</b>: tails on the pads, the front at the board edge, Q401 clear. The two new ESD arrays are visible behind the socket.', '<b>Socket</b>, 3D: tails on the pads, the front at the board edge, Q401 clear, the two ESD arrays behind the socket.') + '''
    ''' + fig('img/blk4/fix_sd_overlay.png') + '''
  </div>
  <div class="tiref">''' + fig('img/blk4/ref_shouhan_layout.png') + '''</div>
''' + esd_fig + '''  <div class="pair">
    ''' + fig('img/blk4/fix_j501_after.png').replace('<b>After</b>: GND / RX / TX on the free side, no designator.', '<b>Debug test pads J501</b> (bottom, mirrored): GND / RX / TX on the free side, no designator.') + '''
  </div>
  ''' + audit(4, 'Group')))
# ---------------------------------------------------------------- silkscreen + labels
S.append(sec('silk', 'ok', 'Silkscreen', 'Silkscreen: nothing printed off the board or on a pad',
  'Designators are hidden (decided 2026-11-21); pin-1 and polarity marks are kept.',
  ['Edge connectors (USB-C, DC IN, battery, NTC): outline lines stop 0.15 mm inside the board edge.',
   'U2’s pin-1 mark clear of C6’s pad (C6 1.54 mm from the VBUS pins, limit 2.0).',
   'DRC: 0 silkscreen items. The 4 “footprint differs from library” notes (J1–J4, their trimmed silk) are accepted.'],
  ''))
lab = old[old.index('<div class="tablewrap"><table>\n    <thead><tr><th>Item</th><th>BWLC1A (tracker-c0)</th>'):]
lab = lab[:lab.index('</table></div>') + len('</table></div>')]
crops = '\n'.join('    ' + fig(x) for x in ('img/labels/crop_left.jpg', 'img/labels/crop_bottom.jpg', 'img/labels/crop_ant.jpg', 'img/labels/crop_c5.jpg'))
S.append(sec('labels', 'ok', 'Labels and branding', 'Wiring labels on top, Teapotlabs branding on the bottom, in the BWLC1A style',
  'Small labels at every user-facing part, and the Teapotlabs logo with “Teapotlabs / LinkNode” and a separate “REVISION 1”, styled exactly like the BWLC1A board (tracker-c0). The project is named <b>LinkNode</b> (<code>hardware/kicad/linknode.kicad_pro</code>, library nickname <code>linknode</code>).',
  ['<b>Top</b>: BAT + −, NTC, DC IN + −, PWR, USB, SD, and the antennas <b>WiFi HaLow</b>, <b>GPS</b> and <b>WiFi 2.4GHz 5GHz</b> (the ESP32-C5 is dual-band on one antenna port). Bold 1 mm knockout text, plain + and − at the pins; polarity from the netlist (J2 pin 1 = DC +, J3 pin 1 = battery +).',
   '<b>Bottom</b>: the Teapotlabs cup logo with “Teapotlabs / LinkNode” in Really Free 3 mm (embedded in the board file), and “REVISION 1” in 2 mm bold knockout under the logo.',
   'No “CHG” label at the charge LED: no room for the 0.8 mm minimum text height.',
   'Checks: 0 label conflicts with pads, holes, bodies, silkscreen, edge or screw heads; no silkscreen DRC items.'],
  '  <div class="pair">\n' + crops + '\n  </div>\n  <h3 class="sub">Style, copied from BWLC1A</h3>\n  ' + lab))
# ---------------------------------------------------------------- expansion
ex = old[old.index('<section id="expansion"'):old.index('</section>', old.index('<section id="expansion"'))]
pad_fig = fig('img/exp/pogo_field.png')
padmap = ex[ex.index('  <h3 class="sub">Pad map'):ex.index('  <h3 class="sub">Ethernet')]
i0 = padmap.index('  <h3 class="sub">Signals that move</h3>')
padmap = padmap[:i0] + '''  <h3 class="sub">RV1106 enable signals on other pins (so I2C0 and I2C2 are free)</h3>
  <div class="tablewrap"><table>
    <thead><tr><th>Signal</th><th>RV1106 pin</th><th>Why it is safe</th></tr></thead>
    <tbody>
      <tr><td>C5_PWR_EN (ESP32-C5 buck U10)</td><td>pin 3 (1.8 V camera-group pin)</td><td>TLV62569 EN high threshold 1.2 V max (<code>TI_TLV62569.pdf</code> p.4). The pin resets pulled down, and the 100k pull-down R100 holds it off.</td></tr>
      <tr><td>GPS_PWR_EN (GPS LDO U21)</td><td>pin 4 (1.8 V camera-group pin)</td><td>ME6211 CE start-up 1.0 V min (<code>Microne_ME6211.pdf</code> p.6). Resets pulled down; R200 holds it off.</td></tr>
      <tr><td>HALOW_FEM_EN (2N7002 Q8)</td><td>pin 58 (3.3 V, PMU)</td><td>A 2N7002 needs more than 1.8 V, so this one is on a 3.3 V pin. Pin 58 resets high-impedance and R122 (100k) holds it low.</td></tr>
    </tbody></table></div>
'''
eth = ex[ex.index('  <h3 class="sub">Ethernet'):ex.index('  <h3 class="sub">Parts (no new part types)</h3>')]
eth = eth.replace(' (added 2026-11-23)', '').replace(' (new U1006 on the mic lines; MICBIAS and LINEOUT use spare channels of U1005)', ' (U1006 on the mic lines; MICBIAS and LINEOUT on spare channels of U1005)')
parts = ex[ex.index('  <h3 class="sub">Parts (no new part types)</h3>'):ex.index('  <p style="color:var(--muted)">Superseded:')]
parts = parts.replace(' U1006 was added for audio.', '')
schs = '''  <h3 class="sub">Schematic and board</h3>
  <p>Schematic sheet “Expansion” (<code>expansion.kicad_sch</code>, refs 10xx): the 35 pad test points TP1001–TP1035 (pad n = TP10nn), 6 ESD arrays, the four 0 Ω Ethernet resistors, the four 4.7 kΩ I2C pull-ups and the four 1 µF mic capacitors. On the root sheet every connection is a straight wire with no crossings. On the board the pads sit at pad 1 = MH1 + (56.00, 27.20) mm, with the ESD arrays, resistors and mic capacitors beside them.</p>
  <div class="pair">
    ''' + fig('img/exp/sch_expansion.png') + '''
    <figure><img src="img/exp/sch_root_v2.png" alt="Root sheet" width="2425" height="1715" loading="lazy"><figcaption><b>Root sheet</b>: Expansion below SoC (17 straight wires); SoC Power in the left column feeds it 10 straight wires (Ethernet + audio).</figcaption></figure>
    ''' + fig('img/exp/board_bottom.jpg') + '''
  </div>
'''
pogo = ex[ex.index('  <h3 class="sub">Recommended pogo pin'):ex.index('  <p class="done">')]
S.append(sec('expansion', 'ok', 'Expansion breakout · pogo pads', 'Expansion as pogo-pin pads on the bottom: Ethernet, audio, two I2C, SPI, GPIO and power',
  'Bare test pads on the bottom (no header, no power switches, for cost): users make a small pogo-pin board that bolts to the four corner holes. ESD on every signal pad. These nets are routed last.',
  ['<b>35 pads</b> (Ø1.5 mm, 2.54 mm pitch, 7 × 5) under the ESP32-C5 on the bottom: Ethernet TX± / RX± (raw), audio (two differential mic inputs, mic bias, line out), I2C2 and I2C0, SPI0, 9 GPIOs at 3.3 V (3 with PWM), 3.3 V, 5 V, GND.',
   'Position: <b>pad 1 = MH1 + (56.00, 27.20) mm</b>, rows and columns 2.54 mm apart, M3 hole pattern 70.05 × 54.05 mm.',
   'About $0.20 in parts, no new part types. C5_PWR_EN, GPS_PWR_EN and HALOW_FEM_EN use other RV1106 pins (pins 3, 4, 58) to free the buses.',
   'Power pads are unswitched (your choice): a short on a user’s board pulls down the node’s 3.3 V or 5 V; recommended load ≤ 0.5 A (5 V equivalent) with a fuse or limited switch on the user’s board. Ethernet needs magnetics and a TVS on the user’s board. 6 GPIOs toggle at boot.',
   'Recommended pogo pin: BAT WIRELESS BWCD-L5.0W2.0H2.5 (LCSC C2826549).'],
  '  ' + pad_fig + '\n' + padmap + eth + parts + schs + pogo))
# ---------------------------------------------------------------- routing 1
S.append(sec('route1', 'ok', 'Routing · rules and Section 1', 'Routing rules, and Section 1: the RV1106’s supply pins fanned out to their decoupling capacitors',
  'Each RV1106 supply pin has a short top stub to a via in the ring between the pin rows and the exposed pad; the via drops to the bottom, where a short link reaches that pin’s decoupling capacitor.',
  ['<b>Routing rules</b>: every track at 0/45/90°, every bend exactly 45° (a right-angle turn is two 45° bends); the only exception is the <b>smooth deskew bumps</b> on length-matched pairs. Signals on top and bottom; the 5 V plane (In2) only for short escapes; In1 stays solid GND. Expansion nets last.',
   '<b>Tools</b>: my own scripts (no Freerouting); differential pairs use <b>KiCad’s own diff-pair router</b>. Every section gets a net-coloured figure and a KiCad plot.',
   'Section 1: 29 ring vias, 32 bottom links, 2 GND stubs into the exposed pad, GND vias for the 24 MHz crystal (outside its keep-out), and DDR ZQ (pin 52) through its own via to R604. 99 tracks, 32 vias.',
   'C619, C628 and R503 are linked in the rail-routing section (a straight link would not keep clearance).',
   'Checks: DRC adds nothing; schematic parity 0; every bend 45°.'],
  '''  <figure><img src="img/route/s1_45_nets.png" alt="Section 1 copper coloured by net with net names on pads" width="4400" height="2460" loading="lazy"><figcaption><b>Section 1 by net</b> (click to zoom). Top copper left, bottom copper (seen from the top) right. Pads and tracks of each routed net share a colour, and every pad of a routed net carries its net name; grey pads are not routed yet; small grey text is the part reference.</figcaption></figure>
  <figure><img src="img/final/s1_kicad.png" alt="Section 1, KiCad plot" width="1144" height="1172" loading="lazy" style="max-width:640px"><figcaption><b>Section 1, KiCad plot</b> (zone fills hidden; top copper red, bottom blue).</figcaption></figure>'''))
# ---------------------------------------------------------------- routing 2
S.append(sec('route2', 'current', 'Routing · Section 2 · USB 2.0', 'USB pair: KiCad’s diff-pair route with smooth deskew bumps',
  'USB D+/D− from the RV1106 (pins 27/26) through the series resistors R508/R509 (2.2 Ω, at the transmitter) and the USBLC6 ESD chip (U1) to the USB-C connector (J1), with the charger’s USB-type (BC1.2) taps to the BQ25798 (U2, pins 6/7). Rockchip’s rules (HDG V1.1 §3.3.3 p.48): 90 Ω differential, skew under 30 mil (0.76 mm), at most 6 vias per line, other signals more than 20 mil (0.5 mm) away.',
  ['Routed with <b>KiCad’s own diff-pair router</b>: one coupled pair on the top layer over solid GND, 0.155 mm lines with a 0.127 mm gap (USB90 class), 45° bends.',
   '<b>Skew 0.00 mm</b> from the RV1106 to U1 (19.13 mm both lines), from <b>4 smooth deskew bumps</b> on D+ right after R508 (0.23 mm high, rounded). To the USB-C pins: 0.26 mm (B row) and 0.02 mm (A row).',
   'Net names: <code>USB_SOC_DP/DN</code> (RV1106 → R508/R509), <code>USB_DP/DN</code> (→ U1 and the charger), <code>USB_CONN_DP/DN</code> (USB-C → U1).',
   'USB-C: its pads alternate D−/D+/D−/D+, so D+ reaches pad A6 through 2 vias and a 1 mm bottom link (no copper under the shell). For the A-row plug orientation that adds about 3 mm of via barrel to D+, about 20 ps.',
   'Charger taps: D+ 13.9 mm and D− 11.8 mm, 2 vias each, on the bottom, entering U2’s pins from outside the chip.',
   'Checks: DRC adds nothing (USB skew, via-count and spacing rules included); ERC 0; schematic parity 0; every bend 45° apart from the bumps.'],
  '''  <figure><img src="img/route/s2_usb_v3.png" alt="USB routing coloured by net with net names on pads" width="4400" height="2660" loading="lazy"><figcaption><b>Section 2 by net</b> (click to zoom). Left, top copper: the coupled pair from R508/R509 (top right) down to U1 (bottom centre), the deskew bumps on D+ near the top, the connector side fanning into the USB-C pads. Right, bottom copper (seen from the top): the two charger taps to U2 and the short D+ link at the connector. Red D+, blue D−.</figcaption></figure>
  <div class="pair">
    <figure><img src="img/route/s2_usb_kicad_v3.png" alt="KiCad plot of the USB routing with three numbered notes" width="1324" height="1620" loading="lazy"><figcaption><b>KiCad plot</b> (zone fills hidden; top copper red, bottom blue, silkscreen yellow): ① the deskew bumps, ② the D+ vias to USB-C pad A6, ③ the charger taps arriving just outside U2.</figcaption></figure>
    <figure><img src="img/route/s2_bumps_smooth.png" alt="Close-up of the four smooth deskew bumps" width="510" height="728" loading="lazy"><figcaption><b>Deskew bumps</b>, KiCad plot: 4 bumps, 0.23 mm high, rounded with 0.12 mm radius quarter arcs, 0.45 mm apart. They add the 1.06 mm by which D− is longer: R509 (D−) sits 1.05 mm north of R508, so D− runs further to join the pair.</figcaption></figure>
  </div>
  <div class="tablewrap"><table>
    <thead><tr><th>Path (pad to pad, copper)</th><th>D−</th><th>D+</th><th>Skew</th></tr></thead>
    <tbody>
      <tr><td>RV1106 → R509/R508</td><td class=n>3.33 mm</td><td class=n>3.60 mm</td><td></td></tr>
      <tr><td>R509/R508 → U1 (D+ with the bumps)</td><td class=n>15.80 mm</td><td class=n>15.53 mm</td><td></td></tr>
      <tr><td><b>RV1106 → U1</b></td><td class=n>19.13 mm</td><td class=n>19.13 mm</td><td class=n><b>0.00 mm</b></td></tr>
      <tr><td>U1 → USB-C B row (B7/B6), no vias</td><td class=n>2.36 mm</td><td class=n>2.10 mm</td><td class=n>0.26 mm (10 mil)</td></tr>
      <tr><td>U1 → USB-C A row (A7/A6)</td><td class=n>3.08 mm</td><td class=n>3.10 mm + 2 vias</td><td class=n>0.02 mm + ≈3 mm via barrel on D+</td></tr>
      <tr><td>Charger tap (to U2)</td><td class=n>11.8 mm, 2 vias</td><td class=n>13.9 mm, 2 vias</td><td></td></tr>
    </tbody></table></div>
  <div class="approve"><b>Your call</b><p>Approve the USB pair. Optional, if you want them: R508/R509 side by side (removes the need for deskew bumps; a placement change), or the USB-C crossover under the connector shell (removes the connector vias, puts copper under the grounded shell). The next section is the RV1106 signal nets (escapes and the short local links), then its local rails and ground, then SD/SDIO length matching.</p></div>'''))

status = ('floorplan B6 <span class="pill ok">approved</span> ' + ' '.join('<a href="#%s">%s</a> <span class="pill ok">approved</span>' % x for x in (
    ('blk1', 'Connector edge and holes'), ('edge', 'Edge margin'), ('blk2', 'Power'), ('blk3', 'Radios'), ('blk4', 'RV1106 surroundings'),
    ('silk', 'Silkscreen'), ('labels', 'Labels'), ('expansion', 'Expansion'), ('route1', 'Routing rules + Section 1'))) +
    ' <a href="#route2">Routing 2: USB</a> <span class="pill wait">awaiting you</span>')
header = '''<header><div class="wrap">
  <div class="eyebrow">LinkNode Rev 1 · layout and routing · updated 2026-11-23</div>
  <h1>LinkNode Rev 1: board decisions</h1>
  <p class="lede">The final decision for every block of the board, as it stands today, with the step under review last. Click any image to enlarge it; zoom with the wheel, pinch or +/−, drag to pan, Esc to close. How each decision was reached is in the worklog (<code>docs/worklog/2026-11-23-t41-placement.md</code>).</p>
  <div class="status">''' + status + '''</div>
</div></header>
<main class="wrap">

'''
out = head + header + '\n'.join(S) + '\n' + tail
from PIL import Image
import os
base = os.path.dirname(P)
def fixsize(m):
    src = m.group(1); fn = os.path.join(base, src)
    if not os.path.exists(fn): return m.group(0)
    w, h = Image.open(fn).size
    tag = re.sub(r'width="\d+"', 'width="%d"' % w, m.group(0)); tag = re.sub(r'height="\d+"', 'height="%d"' % h, tag); return tag
out = re.sub(r'<img src="(img/[^"]+)"[^>]*>', fixsize, out)
missing = [x for x in re.findall(r'<img src="(img/[^"]+)"', out) if not os.path.exists(os.path.join(base, x))]
if missing: raise SystemExit('missing images: %s' % missing)
out = out.replace('<footer>Sources: TI datasheets in <code>hardware/datasheets/</code> (pages as cited). Worklog: <code>docs/worklog/2026-11-23-t41-placement.md</code>.</footer>',
                  '<footer>Sources: datasheets in <code>hardware/datasheets/</code> and the Rockchip HDG in <code>resources/resource/</code> (pages as cited). Worklog: <code>docs/worklog/2026-11-23-t41-placement.md</code>.</footer>')
open(P, 'w').write(out)
imgs = sorted(set(re.findall(r'<img src="(img/[^"]+)"', out)))
print(len(out), 'bytes', len(imgs), 'images'); print('\n'.join(imgs))
