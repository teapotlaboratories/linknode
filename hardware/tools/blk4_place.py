"""T41 Block 4: move the RV1106-side parts that blk4_audit.py found away from their pins.
Usage: python3 blk4_place.py <board.kicad_pcb>   (edits in place; back the board up first). Uses placelib.place_moves.
- R511 SD_CLK 22R series resistor to the RV1106 pin (HDG §3.2 item 9: series resistors near the transmitter).
- C506 / C508 filter caps on USB_DET (pin 25) and SARADC_IN1 (pin 22) to their pins (C507 on SARADC_IN0 is already
  at the closest spot outside the RV1106 body, 3.0 mm).
The bottom under the RV1106 body stays free (its fan-out vias)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from placelib import place_moves
b = pcbnew.LoadBoard(sys.argv[1])
MOVES = [('R511', 'B', 5, [('U100', '15', 1.0)]),
         ('C508', 'B', 5, [('U100', '22', 1.0)]),
         ('C506', 'B', 6, [('U100', '25', 1.0)])]
# The bottom under the RV1106 body is kept for its fan-out vias (T31 method): nothing new goes there.
from placelib import crt
U = b.FindFootprintByReference('U100'); ub = crt(U)
rep = place_moves(b, MOVES, keepout=[('B', ub)])
b.Save(sys.argv[1]); print(json.dumps(rep))
