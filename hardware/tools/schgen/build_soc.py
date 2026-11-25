"""SoC sheet (T11): RV1106G3 U10 units 2 (System), 3 (SD + SPI1), 4 (SDIO, VCCIO5), 5 (GPIO1, VCCIO1/6).
Units 1 (Power) and 6 (unused blocks) are on the SoC Power sheet.
Reference circuits: scratch soc/reference.md (REF = RV1106G-AI-IPC-V13, HDG = Hardware Design Guide V1.1, LPM = Luckfox Pico Pro/Max).
Pins: docs/rv1106-pinmap.md (C5 handshake/data-ready moved to GPIO1_C5/C6, off the FSPI pads, 2026-11-20)."""
import sys, json; sys.path.insert(0, sys.argv[1])
from blocks import *
import wires
S = Sheet()
SOC = 'linknode:RV1106G3'; FP = 'linknode:Rockchip_QFN-128-1EP_12.3x12.3mm_P0.35mm_EP7x7mm'
XT24 = 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm'; XT32 = 'Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm'
H = S.hier
def hl(name, x, y, rot, shape): H.append((name, x, y, rot, shape))

# ===================== unit 2: System at (88.9, 66.04) ; left pins x=63.5, right x=114.3
S.part('U100', SOC, 'RV1106G3', FP, 88.9, 66.04, 0, 'C5328706', unit=2)
# --- 24 MHz: HDG §2.1.1 / REF p.8 Y1100: 4-pad crystal, 18 pF C0G, 22R in XOUT, 1M feedback. KYX K3A240001210 CL 12 pF, ±10 ppm
S.part('Y501', 'Device:Crystal_GND24_Small', '24MHz', XT24, 43.18, 25.4, 0, 'C368741')   # 1 (40.64,25.4) 3 (45.72,25.4) G (43.18,27.94)
S.pwr('GND', 43.18, 27.94)
S.part('R501', 'Device:R_Small', '22R', R, 55.88, 40.64, 90, 'C25092')        # XOUT series
S.w((63.5, 40.64), (58.42, 40.64)); S.w((53.34, 40.64), (38.1, 40.64), (38.1, 17.78), (40.64, 17.78))   # XOUT node x=38.1
S.w((63.5, 38.1), (48.26, 38.1), (48.26, 17.78), (45.72, 17.78))                                        # XIN node x=48.26
S.w((38.1, 25.4), (40.64, 25.4)); S.w((45.72, 25.4), (48.26, 25.4))
S.part('R502', 'Device:R_Small', '1M', R, 43.18, 17.78, 90, 'C26083')         # feedback
S.w((38.1, 22.86), (33.02, 22.86)); S.part('C501', 'Device:C_Small', '18pF C0G', C, 33.02, 25.4, 0, 'C1549'); S.pwr('GND', 33.02, 27.94)
S.w((48.26, 22.86), (53.34, 22.86)); S.part('C502', 'Device:C_Small', '18pF C0G', C, 53.34, 25.4, 0, 'C1549'); S.pwr('GND', 53.34, 27.94)
# --- 32.768 kHz: REF p.8 Y1101, 18 pF C0G. Epson FC-135 12.5 pF
S.w((63.5, 50.8), (35.56, 50.8), (35.56, 58.42), (40.64, 58.42))             # RTC_XIN
S.w((63.5, 53.34), (50.8, 53.34), (50.8, 58.42), (45.72, 58.42))              # RTC_XOUT
S.part('Y502', 'Device:Crystal_Small', '32.768kHz', XT32, 43.18, 58.42, 0, 'C32346')
S.part('C503', 'Device:C_Small', '18pF C0G', C, 35.56, 60.96, 0, 'C1549'); S.pwr('GND', 35.56, 63.5)
S.part('C504', 'Device:C_Small', '18pF C0G', C, 50.8, 60.96, 0, 'C1549'); S.pwr('GND', 50.8, 63.5)
# --- nPOR: REF V1.3 R1110 1k to VCC_3V3, C1114 10 nF (HDG §2.1.2: internal POR, RC is the deglitch)
S.w((63.5, 71.12), (48.26, 71.12))
S.part('R503', 'Device:R_Small', '1k', R, 60.96, 68.58, 0, 'C11702'); S.pwr('VCC_3V3', 60.96, 66.04)
S.part('C505', 'Device:C_Small', '10nF', C, 48.26, 73.66, 0, 'C15195'); S.pwr('GND', 48.26, 76.2)
# --- TVSS to GND (REF p.8, LPM, CORE)
S.w((63.5, 81.28), (60.96, 81.28)); S.pwr('GND', 60.96, 81.28)
# --- I2C1 to the charger, 10k pull-ups to VCC_3V3 (PMU domain is 3.3 V)
S.w((114.3, 38.1), (144.78, 38.1)); hl('I2C_SCL', 144.78, 38.1, 0, 'bidirectional')
S.part('R504', 'Device:R_Small', '10k', R, 124.46, 35.56, 0, 'C25744'); S.pwr('VCC_3V3', 124.46, 33.02)
S.w((114.3, 40.64), (144.78, 40.64)); hl('I2C_SDA', 144.78, 40.64, 0, 'bidirectional')
S.part('R505', 'Device:R_Small', '10k', R, 129.54, 43.18, 0, 'C25744'); S.pwr('VCC_3V3', 129.54, 45.72, 180)
S.w((114.3, 50.8), (144.78, 50.8)); hl('CHG_INT', 144.78, 50.8, 0, 'input')
S.w((114.3, 53.34), (144.78, 53.34)); hl('SD_PWREN', 144.78, 53.34, 0, 'output')
# --- USB_VBUSDET: HDG Fig 2-18 divider, 10k/15k instead of 10k/18k so 5.25 V VBUS gives 3.15 V (< 3.3 V, HDG p.26)
S.w((114.3, 66.04), (134.62, 66.04))
S.part('R506', 'Device:R_Small', '10k', R, 137.16, 66.04, 90, 'C25744'); S.w((139.7, 66.04), (142.24, 66.04)); S.pwr('VBUS', 142.24, 66.04)
S.part('R507', 'Device:R_Small', '15k', R, 129.54, 68.58, 0, 'C25756'); S.pwr('GND', 129.54, 71.12)
S.part('C506', 'Device:C_Small', '100nF', C, 119.38, 68.58, 0, 'C1525'); S.pwr('GND', 119.38, 71.12)
# --- USB D+/D-: HDG Table 2-10 / Fig 2-20: 2.2R series
S.w((114.3, 76.2), (134.62, 76.2)); S.part('R508', 'Device:R_Small', '2.2R', R, 137.16, 76.2, 90, 'C2906903'); S.w((139.7, 76.2), (144.78, 76.2)); hl('USB_DP', 144.78, 76.2, 0, 'bidirectional')
S.w((114.3, 78.74), (134.62, 78.74)); S.part('R509', 'Device:R_Small', '2.2R', R, 137.16, 78.74, 90, 'C2906903'); S.w((139.7, 78.74), (144.78, 78.74)); hl('USB_DM', 144.78, 78.74, 0, 'bidirectional')
# --- SARADC_IN0: "must always be pulled-up" (REF p.9): 10k to VCC_1V8 + 1 nF; test pad to GND = recovery (Rockusb)
S.w((114.3, 83.82), (127.0, 83.82))
S.part('R510', 'Device:R_Small', '10k', R, 129.54, 83.82, 90, 'C25744'); S.w((132.08, 83.82), (134.62, 83.82)); S.pwr('VCC_1V8', 134.62, 83.82, 270)
S.part('C507', 'Device:C_Small', '1nF', C, 124.46, 86.36, 0, 'C1523'); S.pwr('GND', 124.46, 88.9)
S.part('TP501', 'Connector:TestPoint', 'RECOVERY', TP, 116.84, 83.82, 180, None)

# ===================== unit 3: SD + SPI1 at (223.52, 55.88); left x=193.04, right x=254
S.part('U100', SOC, 'RV1106G3', FP, 223.52, 55.88, 0, None, unit=3)
S.w((193.04, 43.18), (185.42, 43.18)); S.part('R511', 'Device:R_Small', '22R', R, 182.88, 43.18, 90, 'C25092'); S.w((180.34, 43.18), (172.72, 43.18)); hl('SD_CLK', 172.72, 43.18, 180, 'output')   # HDG Table 2-7
for n, y, sh in (('SD_DET', 45.72, 'input'), ('SD_CMD', 48.26, 'bidirectional'), ('SD_D0', 50.8, 'bidirectional'),
                 ('SD_D1', 53.34, 'bidirectional'), ('SD_D2', 55.88, 'bidirectional'), ('SD_D3', 58.42, 'bidirectional')):
    S.w((193.04, y), (172.72, y)); hl(n, 172.72, y, 180, sh)
S.w((254.0, 43.18), (259.08, 43.18)); S.part('R512', 'Device:R_Small', '22R', R, 261.62, 43.18, 90, 'C25092'); S.w((264.16, 43.18), (266.7, 43.18)); hl('C5_SPI_CLK', 266.7, 43.18, 0, 'output')
for n, y, sh in (('C5_SPI_MISO', 45.72, 'input'), ('C5_SPI_MOSI', 48.26, 'output'), ('C5_SPI_CS', 50.8, 'output')):
    S.w((254.0, y), (266.7, y)); hl(n, 266.7, y, 0, sh)

# ===================== unit 4: SDIO (VCCIO5) at (223.52, 129.54); left x=193.04, right x=254
S.part('U100', SOC, 'RV1106G3', FP, 223.52, 129.54, 0, None, unit=4)
S.w((193.04, 124.46), (185.42, 124.46)); S.part('R513', 'Device:R_Small', '22R', R, 182.88, 124.46, 90, 'C25092'); S.w((180.34, 124.46), (172.72, 124.46)); hl('HALOW_SDIO_CLK', 172.72, 124.46, 180, 'output')   # HDG Table 2-8
for n, y in (('HALOW_SDIO_CMD', 127.0), ('HALOW_SDIO_D0', 129.54), ('HALOW_SDIO_D1', 132.08), ('HALOW_SDIO_D2', 134.62), ('HALOW_SDIO_D3', 137.16)):
    S.w((193.04, y), (172.72, y)); hl(n, 172.72, y, 180, 'bidirectional')
for n, y, sh in (('HALOW_RESET_N', 124.46, 'output'), ('HALOW_WAKE', 127.0, 'output'), ('HALOW_BUSY', 129.54, 'input'), ('HALOW_PWR_EN', 132.08, 'output')):
    S.w((254.0, y), (266.7, y)); hl(n, 266.7, y, 0, sh)

# ===================== unit 5: GPIO1 (VCCIO1/6) at (88.9, 134.62); left x=58.42, right x=119.38
S.part('U100', SOC, 'RV1106G3', FP, 88.9, 134.62, 0, None, unit=5)
for n, y, sh in (('HALOW_FEM_EN', 121.92, 'output'), ('GPS_PWR_EN', 124.46, 'output'), ('C5_EN', 127.0, 'output'),
                 ('C5_PWR_EN', 129.54, 'output'), ('C5_BOOT', 134.62, 'output')):
    S.w((58.42, y), (35.56, y)); hl(n, 35.56, y, 180, sh)
# debug console UART2_M1 (HDG §2.3.9), direct like LPM; 3-pin header, not fitted
S.part('J501', 'Connector_Generic:Conn_01x03', 'DEBUG UART', 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical', 40.64, 142.24, 0, None, mirror=True)
S.w((45.72, 139.7), (58.42, 139.7)); S.w((45.72, 142.24), (58.42, 142.24)); S.w((45.72, 144.78), (50.8, 144.78)); S.pwr('GND', 50.8, 144.78)
for n, y, sh in (('GPS_PPS', 132.08, 'input'), ('C5_HANDSHAKE', 134.62, 'input'), ('C5_DATA_READY', 137.16, 'input'),
                 ('GPS_RXD', 142.24, 'output'), ('GPS_TXD', 144.78, 'input'), ('C5_UART_TX', 147.32, 'input'), ('C5_UART_RX', 149.86, 'output')):
    S.w((119.38, y), (132.08, y)); hl(n, 132.08, y, 0, sh)

NC = ['58', '62', '63', '22',                     # GPIO0_A0, A3, A4, SARADC_IN1
      '44', '42', '41', '39', '47', '48',         # GPIO4_A2, A3, A4, A6, B0, B1 (FSPI pads, left free for the boot ROM)
      '76', '78', '95', '94', '93', '92', '84']   # GPIO1_A4, B1, C0..C3, C7
plain, mir = S.payload(1000)
json.dump(dict(plain=plain, mir=mir, hier=H, nc=[['U100', n] for n in NC],
               lcsc={r: {'properties': {'LCSC': c}} for r, c in S.lcsc.items()}, wires=S.wires,
               pins=wires.pinpoints(S.parts, S.pw) + [(x, y) for _, x, y, *r in H]),
          open(sys.argv[1] + '/soc_w.json', 'w'))
print(len(plain), 'plain', len(mir), 'single', len(S.wires), 'polylines', len(H), 'hier')
