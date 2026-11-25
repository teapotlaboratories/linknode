"""Generate linknode:ESP32-C5-WROOM-1U. Pins from esp32-c5-wroom-1_wroom-1u_datasheet_en.pdf Table 3-2 (p.14-15).
Left: the pins LinkNode uses, spaced so EN and the IO28 strap can take their RC / pull-up with wires.
Right: unused GPIOs, NC pins and ANT2 (ANT1 is the module's U.FL)."""
import sys
L = {0: ('8', 'IO6/FSPICLK', 'bidirectional'), 1: ('9', 'IO7/FSPID', 'bidirectional'), 2: ('4', 'IO2/FSPIQ', 'bidirectional'),
     3: ('12', 'IO10/FSPICS0', 'bidirectional'), 5: ('21', 'IO23', 'bidirectional'), 6: ('23', 'IO24', 'bidirectional'),
     8: ('25', 'TXD0/IO11', 'bidirectional'), 9: ('24', 'RXD0/IO12', 'bidirectional'), 13: ('3', 'EN', 'input'), 20: ('15', 'IO28/BOOT', 'bidirectional')}
R = {0: ('6', 'IO0', 'bidirectional'), 1: ('7', 'IO1', 'bidirectional'), 2: ('5', 'IO3', 'bidirectional'), 3: ('17', 'IO4', 'bidirectional'),
     4: ('16', 'IO5', 'bidirectional'), 5: ('10', 'IO8', 'bidirectional'), 6: ('11', 'IO9', 'bidirectional'), 7: ('13', 'IO13/USB_D-', 'bidirectional'),
     8: ('14', 'IO14/USB_D+', 'bidirectional'), 9: ('19', 'NC/IO15', 'bidirectional'), 10: ('26', 'IO25', 'bidirectional'), 11: ('27', 'IO26', 'bidirectional'),
     12: ('18', 'IO27', 'bidirectional'), 14: ('20', 'NC', 'no_connect'), 15: ('22', 'NC', 'no_connect'), 17: ('31', 'ANT2', 'passive')}
TOP = 27.94; BOT = TOP - 2.54 * 22; HW = 15.24
def pin(t, x, y, a, name, num, hide=False):
    return ('      (pin %s line (at %g %g %d) (length 2.54)%s (name "%s" (effects (font (size 1.27 1.27)))) '
            '(number "%s" (effects (font (size 1.27 1.27)))))\n') % (t, x, round(y, 2), a, ' (hide yes)' if hide else '', name, num)
P = ''.join(pin(t, -HW - 2.54, TOP - 2.54 * (r + 1), 0, nm, n) for r, (n, nm, t) in L.items())
P += ''.join(pin(t, HW + 2.54, TOP - 2.54 * (r + 1), 180, nm, n) for r, (n, nm, t) in R.items())
P += pin('power_in', 0, TOP + 2.54, 270, '3V3', '2')
P += pin('power_in', 0, BOT - 2.54, 90, 'GND', '1')
for n in ('28', '29', '30', '32'): P += pin('passive', 0, BOT - 2.54, 90, 'GND', n, hide=True)
sym = '''  (symbol "ESP32-C5-WROOM-1U"
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    (property "Reference" "U" (at %g %g 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "ESP32-C5-WROOM-1U-N16R8" (at %g %g 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "linknode:ESP32-C5-WROOM-1U" (at 0 %g 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Datasheet" "hardware/datasheets/esp32-c5-wroom-1_wroom-1u_datasheet_en.pdf" (at 0 %g 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Description" "Espressif ESP32-C5-WROOM-1U dual-band Wi-Fi 6 module, U.FL (ANT1). Pins per datasheet Table 3-2. Pin 19 is SPICS1 for the in-package PSRAM on R8 variants: leave unconnected." (at 0 %g 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "LCSC" "C54951857" (at 0 %g 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (symbol "ESP32-C5-WROOM-1U_0_1"
      (rectangle (start %g %g) (end %g %g) (stroke (width 0.254) (type default)) (fill (type background)))
    )
    (symbol "ESP32-C5-WROOM-1U_1_1"
%s    )
  )
''' % (-HW, TOP + 7.62, -HW, TOP + 5.08, BOT - 10.16, BOT - 12.7, BOT - 15.24, BOT - 17.78, -HW, TOP, HW, BOT, P)
lib = sys.argv[1]; s = open(lib).read(); assert '"ESP32-C5-WROOM-1U"' not in s
i = s.rstrip().rfind(')'); open(lib, 'w').write(s[:i] + sym + ')\n'); print('added')
