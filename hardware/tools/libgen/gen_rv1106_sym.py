"""Generate the linknode:RV1106G3 multi-unit symbol from the Rockchip pin-out workbook (sheet 06, extracted to pins.json).

Usage: gen_rv1106_sym.py pins.json out.kicad_sym_fragment
Units: 1 Power, 2 System (clocks/reset/PMU GPIO0/USB/SARADC), 3 SD card + EMMC/SPI1 (VCCIO3/4),
       4 VCCIO5 (SDIO_M0 / GPIO2), 5 VCCIO1 + VCCIO6 (GPIO1), 6 unused blocks (VCCIO7 camera, FEPHY, CODEC).
Pin name = GPIO + the function LinkNode uses (or function 0); every mux function is kept as a KiCad alternate.
"""
import json, re, sys, math

pins = json.load(open(sys.argv[1]))
out = sys.argv[2]
assert len(pins) == 129, len(pins)
assert sorted(p['pin'] for p in pins) == list(range(1, 130))

USE = {38: 'SPI1_CLK_M0', 40: 'SPI1_CS0_M0', 45: 'SPI1_MOSI_M0', 46: 'SPI1_MISO_M0',
       79: 'UART2_TX_M1', 80: 'UART2_RX_M1', 87: 'UART3_RX_M1', 89: 'UART3_TX_M1',
       85: 'UART5_TX_M1', 86: 'UART5_RX_M1', 22: 'SARADC_IN1'}
TYPE = {'PI': 'power_in', 'API': 'power_in', 'G': 'power_in', 'I/O': 'bidirectional', 'I': 'input',
        'CI': 'input', 'CO': 'output', 'AI': 'input', 'AO': 'output', 'AI/O': 'bidirectional',
        'A': 'passive', 'APO': 'power_out', 'AG': 'power_in'}

def parse(p):
    raw = p['name'].strip()
    segs = [s for s in raw.split('/') if s]
    gpio = [s for s in segs if re.match(r'GPIO\d_[A-D]\d_[udz]$', s)]
    p['funcs'] = [s for s in segs if s not in gpio]
    if gpio:
        g = gpio[0][:-2]
        f = USE.get(p['pin'], p['funcs'][0] if p['funcs'] else None)
        p['label'] = f + '/' + g if f else g
        p['gpio'] = g
        p['etype'] = 'bidirectional'          # every GPIO-capable pin, MIPI/SARADC included
    else:
        p['gpio'] = None
        SHORT = {'DVDDD_3': 'DVDD_3',   # xlsx typo
                 'OTP_AVDD1V8/ETH_AVDD1V8/TSADC_AVDD1V8': 'OTP/ETH/TSADC_AVDD1V8',
                 'MIPI_AVDD1V8/VCCIO7_VCC1V8': 'MIPI_AVDD1V8/VCCIO7',
                 'OSC_AVDD1V8/PLL_AVDD1V8': 'OSC/PLL_AVDD1V8'}
        p['label'] = SHORT.get(raw, raw)
        p['etype'] = TYPE[p['type']]
    if p['pin'] == 129:
        p['label'] = 'VSS_EP'
    return p

pins = [parse(p) for p in pins]
by = {p['pin']: p for p in pins}

def gkey(p):
    m = re.match(r'GPIO(\d)_([A-D])(\d)', p['gpio']); return (int(m[1]), m[2], int(m[3]))

def grp(cond):
    return sorted([p for p in pins if cond(p)], key=gkey)

dom = lambda p: p['part'] or ''
# ---- unit 1: power. Rails grouped (gap = None) in the order the decoupling is drawn.
r09 = [115, 10, 51, 54, 55, 82, 103, 116, 71, 67]
r135 = [49, 50, 56]
r18 = [70, 96, 24, 31, 53, 1]
r33 = [61, 19, 28, 101, 81, 43, 13, 108, 88]
# grouped by rail; gaps leave room for the per-pin filters (bead / 1R / 100R + cap) drawn beside the pin
U1L = [115, None, None, 10, 51, 54, 55, 82, 103, 116, 71, 67, None, None, 49, 50, 56]
U1R = [70, 31, 53, None, None, 96, None, None, None, 24, None, None, None, 1, None, None, None, 19,
       None, None, None, None, 61, 28, 101, 81, 43, 13, 108, 88]
U1B = [129, 37, 52]
# ---- unit 2: system
# gaps leave room to draw the crystal, reset, pull-up and divider parts with wires only
U2L = [68, 69, None, None, None, 21, 20, None, None, None, None, None, None, 66, None, None, None, 57]
U2R = [64, 65, None, None, None, 60, 59, 58, 62, 63, None, 25, None, None, None, 27, 26, None, 23, None, None, None, 22]
# ---- unit 3: SD (VCCIO4) left, EMMC/FSPI/SPI1 (VCCIO3) right
# clock pins on the top row so the 22 ohm series resistor has room for its text
U3L = [15, 11, 16, 14, 12, 18, 17]
U3R = [38, 46, 45, 40, None, 44, 42, 41, 39, 47, 48]
# ---- unit 4: VCCIO5, SDIO_M0 first
U4L = [111, 112, 110, 109, 114, 113]
U4R = [107, 106, 105, 104]
# ---- unit 5: VCCIO1 left, VCCIO6 right
U5L = [p['pin'] for p in grp(lambda p: dom(p).startswith('VCCIO1') and p['gpio'])]
U5R = [p['pin'] for p in grp(lambda p: dom(p).startswith('VCCIO6') and p['gpio'])]
# ---- unit 6: unused blocks
U6L = [p['pin'] for p in grp(lambda p: dom(p).startswith('VCCIO7') and p['gpio'])]
U6R = [98, 97, 100, 99, 102, None, 34, 33, 36, 35, 29, 30, 32]
UNITS = [('Power', U1L, U1R, U1B), ('System', U2L, U2R, []), ('SD and SPI1', U3L, U3R, []),
         ('SDIO (VCCIO5)', U4L, U4R, []), ('GPIO1 (VCCIO1, VCCIO6)', U5L, U5R, []),
         ('Unused: camera, Ethernet, audio', U6L, U6R, [])]
used = [n for _, l, r, b in UNITS for n in l + r + b if n]
assert sorted(used) == list(range(1, 130)), (set(range(1, 130)) - set(used), [n for n in used if used.count(n) > 1])

G = 2.54
CW = 1.22   # approx stroke-font advance per char at 1.27 mm (KiCad default font)
def snap_up(v): return math.ceil(v / G - 1e-9) * G
def fmt(v): return ('%.2f' % v).rstrip('0').rstrip('.') if abs(v) > 1e-9 else '0'

def pin_s(p, x, y, ang):
    alts = ''.join('\n        (alternate "%s" %s line)' % (f, 'bidirectional') for f in p['funcs']
                   if p['gpio'] and f + '/' + p['gpio'] != p['label']) if p['gpio'] else ''
    return ('      (pin %s line\n        (at %s %s %d)\n        (length 2.54)\n'
            '        (name "%s" (effects (font (size 1.27 1.27))))\n'
            '        (number "%d" (effects (font (size 1.27 1.27))))%s\n      )\n') % (
        p['etype'], fmt(x), fmt(y), ang, p['label'], p['pin'], alts)

body = []
for ui, (uname, L, R, B) in enumerate(UNITS, 1):
    wl = max([len(by[n]['label']) for n in L if n] + [0]) * CW
    wr = max([len(by[n]['label']) for n in R if n] + [0]) * CW
    half = snap_up((wl + wr + 5.08) / 2)
    rows = max(len(L), len(R))
    top = snap_up(rows * G / 2)
    bot_extra = G * 2 if B else 0
    ytop, ybot = top, top - (rows + 1) * G - bot_extra
    s = '    (symbol "RV1106G3_%d_1"\n      (unit_name "%s")\n' % (ui, uname)
    s += ('      (rectangle (start %s %s) (end %s %s)\n        (stroke (width 0.254) (type default))\n'
          '        (fill (type background))\n      )\n') % (fmt(-half), fmt(ytop), fmt(half), fmt(ybot))
    for col, xs, ang in ((L, -half - G, 0), (R, half + G, 180)):
        y = ytop - G
        for n in col:
            if n: s += pin_s(by[n], xs, y, ang)
            y -= G
    if B:
        x = -G * (len(B) - 1)
        for n in B:
            s += pin_s(by[n], x, ybot - G, 90); x += 2 * G
    s += '    )\n'
    body.append(s)
    print('unit', ui, uname, 'half-width', half, 'rows', rows, 'pins', len([n for n in L + R + B if n]))

head = '''  (symbol "RV1106G3"
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    (property "Reference" "U" (at 0 TOPREF 0) (effects (font (size 1.27 1.27))))
    (property "Value" "RV1106G3" (at 0 TOPVAL 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "linknode:Rockchip_QFN-128-1EP_12.3x12.3mm_P0.35mm_EP7x7mm" (at 0 -2.54 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Datasheet" "hardware/datasheets/Rockchip_RV1106_Datasheet_V1.3.pdf" (at 0 -5.08 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Description" "Rockchip RV1106G3 Cortex-A7 SoC with 2 Gb DDR3L in package, QFN-128 12.3x12.3 mm 0.35 mm pitch. Pins from Rockchip RV1106G_PinOut_V1.1_20220507.xlsx sheet 06; package from RV1106 Datasheet V1.3 Fig 2-3..2-5 p.16-17. Pin 129 is the exposed pad (VSS). Every mux function is a pin alternate." (at 0 -7.62 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "LCSC" "C5328706" (at 0 -10.16 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "ki_keywords" "Rockchip RV1106 SoC Cortex-A7 DDR3L QFN-128" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
'''
TOP = max(snap_up(max(len(l), len(r)) * G / 2) for _, l, r, _ in UNITS)
head = head.replace('TOPREF', fmt(TOP + 5.08)).replace('TOPVAL', fmt(TOP + 2.54))
open(out, 'w').write(head + ''.join(body) + '  )\n')
