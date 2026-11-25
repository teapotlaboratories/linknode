"""microSD sheet (T11): boot card on SDMMC0 (SD 2.0, VCCIO4 3.3 V).
REF = RV1106G-AI-IPC-V13 p.19 "Card Power" / TF socket; LPM = Luckfox Pico Pro/Max (soc/reference.md §7):
 card VDD switched by a P-FET (Q8201 TCS1025 / LPM SI2301; here AO3401A C15127, already on the BOM), 100k gate-source
 pull-up + 100 nF, 10k from SDMMC0_PWREN (GPIO0_A1, internal pull-down => card ON at reset); output 100 nF + 10k bleeder,
 4.7 uF + 100 nF at the socket. AO3401A VGS(th) -0.5..-1.3 V (AOS datasheet p.2); gate sits at 0.7-1.1 V with the
 16-43k internal pull-down => VGS -2.2..-2.6 V, RDS(on) <= 85 mOhm at -2.5 V.
 DET: socket Cd -> 100R -> SDMMC_DET (REF R8205). No external CMD/DAT pull-ups (HDG Table 2-7: internal). CLK 22R on the
 SoC sheet. No SD ESD (as LPM; owner cost rule). R403 DNP: ties DET low if the Cd contact does not close to the shell."""
import sys, json; sys.path.insert(0, sys.argv[1])
from blocks import *
import wires
S = Sheet(); H = S.hier
def hl(name, x, y, rot, shape): H.append((name, x, y, rot, shape))
# --- card power switch
S.pwr('VCC_3V3', 86.36, 76.2); S.w((86.36, 76.2), (96.52, 76.2))
S.part('Q401', 'Transistor_FET:AO3401A', 'AO3401A', 'Package_TO_SOT_SMD:SOT-23', 101.6, 78.74, 90, 'C15127', mirror=True)   # S(96.52,76.2) D(106.68,76.2) G(101.6,83.82)
S.part('R404', 'Device:R_Small', '100k', R, 88.9, 78.74, 0, 'C25741'); S.w((88.9, 81.28), (88.9, 83.82))
S.part('C403', 'Device:C_Small', '100nF', C, 93.98, 78.74, 0, 'C1525'); S.w((93.98, 81.28), (93.98, 83.82))
S.part('R405', 'Device:R_Small', '10k', R, 81.28, 83.82, 90, 'C25744')
S.w((83.82, 83.82), (101.6, 83.82)); S.w((78.74, 83.82), (71.12, 83.82)); hl('SD_PWREN', 71.12, 83.82, 180, 'input')
# --- VCC3V3_SD rail to the socket
S.w((106.68, 76.2), (139.7, 76.2), (139.7, 106.68)); S.w((139.7, 76.2), (139.7, 73.66)); S.pwr('VCC3V3_SD', 139.7, 73.66)
S.pwr('FLAG', 109.22, 76.2, 0)
S.part('C404', 'Device:C_Small', '100nF', C, 114.3, 78.74, 0, 'C1525'); S.pwr('GND', 114.3, 81.28)
S.part('R406', 'Device:R_Small', '10k', R, 119.38, 78.74, 0, 'C25744'); S.pwr('GND', 119.38, 81.28)
S.part('C401', 'Device:C_Small', '4.7uF', C, 127.0, 78.74, 0, 'C23733'); S.pwr('GND', 127.0, 81.28)
S.part('C402', 'Device:C_Small', '100nF', C, 132.08, 78.74, 0, 'C1525'); S.pwr('GND', 132.08, 81.28)
# --- socket
S.part('J401', 'linknode:microSD_TF_PUSH', 'TF PUSH', 'linknode:microSD_ShouHan_TF-PUSH', 139.7, 119.38, 0, 'C393941')
for n, y, sh in (('SD_CLK', 111.76, 'input'), ('SD_CMD', 114.3, 'bidirectional'), ('SD_D0', 116.84, 'bidirectional'),
                 ('SD_D1', 119.38, 'bidirectional'), ('SD_D2', 121.92, 'bidirectional'), ('SD_D3', 124.46, 'bidirectional')):
    S.w((129.54, y), (101.6, y)); hl(n, 101.6, y, 180, sh)
S.w((129.54, 129.54), (121.92, 129.54)); S.part('R402', 'Device:R_Small', '100R', R, 119.38, 129.54, 90, 'C25076')
S.w((116.84, 129.54), (101.6, 129.54)); hl('SD_DET', 101.6, 129.54, 180, 'output')
S.part('R403', 'Device:R_Small', '10k DNP', R, 109.22, 132.08, 0, 'C25744'); S.pwr('GND', 109.22, 134.62)
S.pwr('GND', 137.16, 134.62); S.pwr('GND', 142.24, 134.62)
plain, mir = S.payload(1200)
json.dump(dict(plain=plain, mir=mir, hier=H, lcsc={r: {'properties': {'LCSC': c}} for r, c in S.lcsc.items()}, wires=S.wires,
               pins=wires.pinpoints(S.parts, S.pw) + [(x, y) for _, x, y, *r in H]), open(sys.argv[1] + '/microsd_w.json', 'w'))
print(len(plain), 'plain', len(mir), 'single', len(S.wires), 'polylines', len(H), 'hier')
