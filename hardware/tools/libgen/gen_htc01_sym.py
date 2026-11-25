"""Generate linknode:HT-HC01_V2. Pins from Heltec_HT-HC01_V2.pdf p.7-9 (checked against Heltec's HT-HC01_V2.SchLib,
pad 0 = GND). SDIO pins are 4 rows apart so each pull-up can be drawn with wires; pull-down pins are grouped in fours
for 4x0402 resistor arrays."""
import sys
L, R = {}, {}
for r, (num, name, t) in {0: ('18', 'SDIO_CLK', 'input'), 4: ('21', 'SDIO_CMD', 'bidirectional'), 8: ('17', 'SDIO_D0', 'bidirectional'),
                          12: ('16', 'SDIO_D1', 'bidirectional'), 16: ('23', 'SDIO_D2', 'bidirectional'), 20: ('22', 'SDIO_D3', 'bidirectional'),
                          24: ('35', 'RESET_N', 'input'), 25: ('36', 'WAKE', 'input'), 26: ('34', 'BUSY/GPIO_0', 'output')}.items():
    L[r] = (num, name, t)
for r, (num, name, t) in {0: ('38', 'ANT', 'passive'),
                          2: ('4', 'JTAG_TCK', 'input'), 3: ('5', 'JTAG_TDI', 'input'), 4: ('7', 'JTAG_TMS', 'input'), 5: ('8', 'JTAG_TRST_N', 'input'),
                          7: ('9', 'JTAG_TDO', 'output'), 8: ('33', 'GPIO_1', 'bidirectional'), 9: ('30', 'GPIO_2', 'bidirectional'), 10: ('29', 'GPIO_3', 'bidirectional'),
                          12: ('28', 'GPIO_4', 'bidirectional'), 13: ('27', 'GPIO_5', 'bidirectional'), 14: ('24', 'GPIO_6', 'bidirectional'), 15: ('15', 'GPIO_7', 'bidirectional'),
                          17: ('14', 'GPIO_8', 'bidirectional'), 18: ('13', 'GPIO_9', 'bidirectional'),
                          20: ('6', 'NC', 'no_connect'), 21: ('10', 'NC', 'no_connect'), 22: ('11', 'NC', 'no_connect')}.items():
    R[r] = (num, name, t)
TOP = 35.56; BOT = TOP - 2.54 * 28; HW = 17.78
def pin(t, x, y, a, name, num, hide=False):
    return ('      (pin %s line (at %g %g %d) (length 2.54)%s (name "%s" (effects (font (size 1.27 1.27)))) '
            '(number "%s" (effects (font (size 1.27 1.27)))))\n') % (t, x, y, a, ' (hide yes)' if hide else '', name, num)
P = ''
for r, (n, nm, t) in L.items(): P += pin(t, -HW - 2.54, TOP - 2.54 * (r + 1), 0, nm, n)
for r, (n, nm, t) in R.items(): P += pin(t, HW + 2.54, TOP - 2.54 * (r + 1), 180, nm, n)
for x, n, nm in ((-5.08, '25', 'VBAT'), (0, '19', 'VDD_IO'), (5.08, '32', 'VDD_FEM')): P += pin('power_in', x, TOP + 2.54, 270, nm, n)
P += pin('power_in', 0, BOT - 2.54, 90, 'GND', '0')
for n in ('1', '2', '3', '12', '20', '26', '31', '37'): P += pin('passive', 0, BOT - 2.54, 90, 'GND', n, hide=True)
sym = '''  (symbol "HT-HC01_V2"
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    (property "Reference" "U" (at %g %g 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "HT-HC01_V2" (at %g %g 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "linknode:HT-HC01_V2" (at 0 %g 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Datasheet" "hardware/datasheets/Heltec_HT-HC01_V2.pdf" (at 0 %g 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Description" "Heltec HT-HC01 V2 Wi-Fi HaLow module, Morse Micro MM6108 + FEM, 902-928 MHz 27 dBm, SDIO 2.0. Pins per datasheet p.7-9; pad 0 (two bottom pads) = GND per Heltec's SchLib. Not stocked by LCSC: buy from heltec.org." (at 0 %g 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "ki_keywords" "HaLow 802.11ah MM6108 Heltec" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (symbol "HT-HC01_V2_0_1"
      (rectangle (start %g %g) (end %g %g) (stroke (width 0.254) (type default)) (fill (type background)))
    )
    (symbol "HT-HC01_V2_1_1"
%s    )
  )
''' % (-HW, TOP + 7.62, -HW, TOP + 5.08, BOT - 10.16, BOT - 12.7, BOT - 15.24, -HW, TOP, HW, BOT, P)
lib = sys.argv[1]; s = open(lib).read()
assert '"HT-HC01_V2"' not in s
i = s.rstrip().rfind(')'); open(lib, 'w').write(s[:i] + sym + ')\n'); print('added')
