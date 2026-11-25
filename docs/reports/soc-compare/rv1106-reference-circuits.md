# RV1106G3 chip-down: reference-circuit extraction (Klepon Rev 1)

Extracted 2026-11-20. Read-only research. No project files were changed.

## Sources and citation keys

| Key | File (under `resources/resource/`) | Page convention |
|---|---|---|
| **REF** | `board_reference/RV1106G-AI-IPC-V13-20231110LX.pdf` (Rockchip RV1106G AI IPC V1.3, 2023-11-10) | PDF page = sheet number (e.g. REF p.7 = sheet "10.RV1106G Power/Codec/ETH/USB") |
| **HDG** | `Rockchip-RV1103G-RV1106G-Hardware-Design-Guide-en-V1-1-20221221.pdf` | PDF page; printed page = PDF page − 1 |
| **LPM** | `board_reference/Luckfox-Pico-Pro-Max-087b9515b5f90513ffea1e6ebe15848f.pdf` (one page) | cited by block name + refdes |
| **CORE** | `board_reference/Core1106-75c4bf40ace3640ddb05ede0677ad4ca.pdf` | PDF page |
| **IPC** | `board_reference/IPC-P01-Z02-sch-2022.pdf` (Rockchip IPC-P01-Z02 V1.1, 2023-02-27, secondary) | PDF page |
| **DS** | `rv1103_rv1106/Rockchip RV1106 Datasheet V1.3-20230522.pdf` | PDF page |
| **TRM** | `rv1103_rv1106/Rockchip_RV1106_TRM_V0.3-Part1-20220324.pdf` | PDF page |
| **EVB** | `rv1103_rv1106/RV1106_EN/ipc/Rockchip_RV1106_RV1103_User_Guide_Linux_EVB_EN.pdf` | PDF page |

The SoC refdes in REF is U1000 (parts A–D on pp.8, 9, 10, 7). In LPM it is U1, and in CORE it is U2.

**REF revision history (REF p.3), relevant lines:**
- V1.2 (2022-11-14): "Change R1110 to 1K and C1114 to 10nF; Add R1111/R1112; Add FB1001".
- V1.3 (2023-11-10): "Change R1106 / R1108 to 510R".

So HDG (Dec 2022) figures show the pre-V1.2 values in places. Where they differ, REF V1.3 is the newer Rockchip source.

Unless stated otherwise, all passives in REF are 0402. Every 100 nF is `C0402 X5R 16V`, every 1 µF is `C0402 X5R 6.3V`, and every 10 µF is `C0603 X5R 6.3V`. The text layer of REF p.7–p.11 gives the value, footprint and dielectric/voltage for each refdes.

---

## 1. Decoupling per supply pin or group

Pin numbers and names are from DS p.18–19 (Table 2-1).

| Supply pin(s) | Pin | Rail | REF (Rockchip V1.3) | LPM (Luckfox Pro/Max) | HDG requirement |
|---|---|---|---|---|---|
| CPU_DVDD | 115 | VDD_ARM | C1007 10µF 0603 6.3V, C1009 1µF, C1010 100nF ("For ARM", "Close to Power Pin"), REF p.7 | C15 10µF, C16 1µF, C17 100nF ("For ARM") | Fig 2-8 (HDG p.22): 10µF + 1µF + 100nF + 100nF **DNP**. "The capacitors in the … reference design schematic cannot be omitted", ripple ±5% (§2.2.3.1, HDG p.21) |
| DVDD_1..7 + OSC_PLL_DVDD (REF calls it PLL_DVDD0V9) | 10, 51, 54, 55, 82, 103, 116, 71 | VDD_0V9 | C1019, C1020 10µF 0603; C1021, C1022 1µF; C1023, C1024, C1025 100nF ("For LOGIC/NPU/VEPU"), REF p.7. 7 caps for 8 pins | C22, C23 10µF; C24, C25 1µF; C26–C28 100nF (same 7) | Fig 2-10 (HDG p.22): 2×10µF, 2×1µF, **5×100nF**. Text: "place 2 10uF capacitors on the near power supply side and the far power supply side … Each pin should have at least 1 100nF" (§2.2.3.2). Peak 1.6 A |
| DDR_VDDQ_1..3 | 49, 50, 56 | VCC_DDR (1.35 V) | C1012, C1013 10µF 0603; C1014 1µF; C1015 100nF ("For DDR"), REF p.7 | C18, C19 10µF; C20 1µF; C21 100nF | Fig 2-12 (HDG p.23): same 4 caps. Peak 400 mA, ±5% (§2.2.3.3) |
| DDR_PLL_AVDD1V8 | 53 | VCC_1V8 | C1027 1µF, C1028 100nF ("For AVDD18_DDR"), REF p.7 | C11 1µF, C12 100nF | Fig 2-12: same |
| PMU_DVDD0V9 (OSC_DVDD0V9) | 67 | VDD_0V9 | C1109 100nF, REF p.8 | C36 100nF | 100 nF per pin (§2.1.8.2, HDG p.19) |
| OSC_AVDD1V8 / PLL_AVDD1V8 | 70 | VCC_1V8 direct | C1115 100nF (on the VCC_1V8 node), REF p.8 | C32 100nF | Fig 2-1 (HDG p.14) same |
| OTP_AVDD1V8 / ETH_AVDD1V8 / TSADC_AVDD1V8 | 96 | VCC_1V8 **through FB1100 120R@100MHz (L0402)** | FB1100 + C1106 100nF after the bead, REF p.8 | FB3 UPZ1005D121-1R3TF (alt. BLM15PD121SN1) + C31 100nF | §2.3.4 (HDG p.29): "The AVDD18 power supply of FEPHY is susceptible to noise … magnetic beads need to be placed nearby". Fig 2-23 (HDG p.30) |
| SARADC_USB_AVDD1V8 (also the VCCIO2/SARADC IO supply) | 24 | VCC_1V8 **through R1005 1Ω 5%** → net AVDD1V8_USB | R1005 1R + C1006 100nF, REF p.7 | R8 1R + C10 100nF | §2.3.3 (HDG p.27): "The 1.8V power supply of the controller needs to be connected with a 1ohm resistor in series to avoid the damage caused by the surge" (Fig 2-19). Symbol note: "USB must always power supply" |
| USB_AVDD3V3 | 28 | VCC_3V3 | C1005 100nF, REF p.7 | C9 100nF | Fig 2-16/2-19: same |
| CODEC_AVDD1V8 | 31 | VCC_1V8 **through FB1000 120R@100MHz** → VCC1V8_CODEC | FB1000 + C1016 10µF **C0402 X5R 4V** + C1017 100nF, REF p.7 | FB2 UPZ1005D121-1R3TF + C13 10µF X5R 4V + C14 100nF | none stated |
| MIPI_AVDD1V8 / VCCIO7 (GPIO7_VCC1V8) | 1 | VCC_1V8 **through R1303 1Ω 5%** → MIPI_CSI_AVDD_1V8 | R1303 1R + C1300 100nF, REF p.10 | R31 1R + C45 100nF | §2.3.7.1 (HDG p.34–35): "needs to be connected in series with a 1ohm resistor to avoid the damage caused by the surge" (Fig 2-31 shows 1R + 100nF; the figure title says "magnetic beads") |
| FEPHY_AVDD3V3 (DS: ETH_AVDD3V3) | 101 | VCC_3V3 **through FB1001 120R@100MHz** (added in V1.2) | FB1001; C1004 100nF sits on the **VCC_3V3 side** of the bead (only a TP on the pin side), REF p.7 | FB1 UPZ1005D121-1R3TF + C8 100nF, also on the VCC_3V3 side | Fig 2-21 (HDG p.28, older): direct VCC_3V3 + C1004 100nF, no bead |
| PMU_VCC3V3 | 61 | VCC_3V3 | C1110 100nF, REF p.8 | C37 100nF | 100 nF per pin |
| RTC_AVDD3V3 | 19 | VCC3V3_RTC **through R1101 100Ω 5%** | R1101 100R + C1107 1µF X5R 6.3V, REF p.8 | R11 100R + C35 1µF | §2.1.1 (HDG p.14): "the RC parameters of the AVDD33_RTC power input … **must be 100ohm and 1uF**" |
| VCCIO1_VCC3V3 (GPIO1_VCC3V3) | 81 | VCC_3V3 | C1108 100nF, REF p.8 | C39 100nF | 100 nF per pin, ±5% (§2.1.8.2, HDG p.19; §2.2.3.4, HDG p.23) |
| VCCIO3_VCC (GPIO3_VCC) | 43 | VCCIO_FLASH | C1204 100nF at the pin. VCCIO_FLASH = VCC_3V3 via R1205 0R (R1204 0R from VCC_1V8 is DNP), plus C1211 10µF 0603 + C1212 100nF, REF p.9 | C40 100nF (VCCIO_FLASH) | same |
| VCCIO4_VCC (GPIO4_VCC, SDMMC0) | 13 | VCC_3V3 | C1205 100nF, REF p.9 | C41 100nF | "external 3.3V power supply (SD 2.0 mode)" (§2.3.1, HDG p.23) |
| VCCIO5_VCC (GPIO5_VCC) | 108 | VCC_3V3 | C1302 100nF, REF p.10 | **no cap drawn** | 100 nF per pin |
| VCCIO6_VCC (GPIO6_VCC) | 88 | VCC_3V3 | C1301 100nF, REF p.10 | **no cap drawn** | 100 nF per pin |
| ePAD (VSS) | 129 | GND | ePAD → GND, REF p.7 | same | — |

**Where Rockchip and Luckfox differ:**
- VDD_0V9 has 3×100 nF in both REF V1.3 and LPM. HDG Fig 2-10 shows 5×100 nF, and the HDG text asks for one per pin (8 pins). Neither board meets the text. The recommendation for us is to follow the text: 8×100 nF + 2×10 µF + 2×1 µF. This is a judgement call, not a reference value.
- LPM has no caps on VCCIO5 or VCCIO6. REF and HDG both want 100 nF on each.
- Values are otherwise identical. The bead parts differ: REF uses a generic "120R-100M L0402", LPM/CORE use UPZ1005D121-1R3TF or BLM15PD121SN1.
- CORE p.1 matches REF too. VDD_0V9 has C68–C74 (2×10µF, 2×1µF, 3×100nF), ARM has C61–C63, DDR has C64–C67, AVDD18_DDR has C75/C76, and the codec has FB4 BLM15PD121SN1 + C77 10µF 4V + C78 100nF. FEPHY uses FB3 + C51, and USB uses R30 1R + C52/C53.

**Regulator-side bulk caps in REF (not at the SoC), REF p.11:**

| Rail | Output caps |
|---|---|
| VDD_0V9 | C2007 22µF 0603 + C2008 100nF |
| VDD_ARM | C2013 22µF + C2014 100nF |
| VCC_DDR | C2030 10µF + C2031 100nF |
| VCC_1V8 | C2018 4.7µF + C2019 100nF |
| VCC_3V3 | C2025 4.7µF + C2026 100nF |

**Supply limits (DS p.20, Tables 3-1/3-2):**

| Pin | Recommended (min / typ / max) | Absolute max |
|---|---|---|
| CPU_DVDD | 0.85 / 0.90 / 1.05 V | 1.15 V |
| DVDD_i, PMU_DVDD0V9 | 0.81 / 0.90 / 0.95 V | 0.99 V |
| DDR_VDDQ | 1.283 / 1.35 / 1.45 V | — |
| RTC_AVDD3V3 | 1.6 / 3.3 / 3.6 V | — |
| ETH_AVDD3V3 | 2.97–3.63 V | — |
| USB_AVDD3V3 | 3.0–3.6 V | — |
| 1.8 V analog pins | 1.62–1.98 V | — |

---

## 2. 24 MHz crystal (OSC_SOC_XIN pin 68 / OSC_SOC_XOUT pin 69)

| Item | REF p.8 (Y1100) | LPM (Y1) | CORE p.1 (Y1) | IPC p.8 (Y1) |
|---|---|---|---|---|
| Crystal | 24 MHz, 4-pad `CRY4_3R20X2R50X0R80` (3.2×2.5 mm). Pins 2/4 GND. No CL/ESR given | 24 MHz passive ("无源"), 2016 size (2.0×1.6 mm). No CL/ESR given | 24 MHz passive, 2016 | **"24MHz-12p-10ppm-3225"** (CL 12 pF, ±10 ppm, 3.2×2.5 mm) |
| Load caps | C1100, C1102 **18 pF C0G 50V 0402** | C29, C30 18 pF C0G 50V | C17, C18 18 pF C0G 50V | 18 pF C0G 50V |
| Series R on XOUT | R1100 **22 Ω 5%** (between pin 69 and crystal X2) | R9 22R 5% | R7 22R | R9 22R |
| Feedback R | R1109 **1 MΩ 5%** across XOUT–XIN | R10 1M | R8 1M | R10 1M |

**HDG §2.1.1 (HDG p.14) requirements:**
- Load caps must match the crystal's load capacitance and should be NPO.
- Use a 4-pin chip crystal and connect both GND pins fully to ground, for ESD robustness.
- Frequency offset must be < 20 ppm. Table 2-1: 24.000000 MHz, ±20 ppm. Driving from an active oscillator into OSC_XIN is also allowed, at 1.8 V ±10% amplitude.

The oscillator sits in the 1.8 V OSC/PLL domain (pin 70).

**Crystal CL and ESR:**
- ESR is **UNVERIFIED**. No local Rockchip or Luckfox source gives a maximum ESR.
- The only local CL figure is IPC's 12 pF part with 18 pF caps. CL ≈ 18/2 + ~3 pF stray is consistent with that, but the stray value is an inference. Choose the LCSC part's CL first, then compute the caps.

---

## 3. 32.768 kHz RTC crystal (OSC_RTC_XIN pin 21 / OSC_RTC_XOUT pin 20)

**Reference values:**
- REF p.8: Y1101 32.768 kHz, `CRY2_3R20x1R50x0R90` (3.2×1.5 mm), with C1101 and C1103 **18 pF C0G 50V 0402** to GND.
- RTC supply: R1101 100 Ω + C1107 1 µF on RTC_AVDD3V3 (pin 19), from VCC3V3_RTC.
- IPC p.8: Y2 **"32.768KHz-12.5pF-20ppm-3215"** (FC-135 footprint), also with 18 pF caps.
- LPM: Y2 passive 32.768 kHz "2012" size, C33/C34 18 pF C0G 50V, R11 100R, C35 1 µF.
- CORE p.1: Y2 2012 size, C21/C22 18 pF, R14 100R, C26 1 µF.

**RTC power source:**
- REF p.11 "RTC Power": VCC_3V3 → D2000 **B5819WS** → VCC3V3_RTC, with coin cell J2000 MS614SE via R2022 1.1 kΩ for backup.
- LPM: D3 B5819WS from VCC_3V3, plus a battery header H2 through D2 B5819WS and R45 "NC/1.1K".
- CORE p.1: VCC_3V3 → D1 **RB521S-30** → VCC3V3_RTC, with no battery.

**Is the crystal required?**
- Every local RV1106 board fits it (REF, IPC, LPM, CORE, and Luckfox Pico Zero and Ultra-W). No local source states it may be omitted.
- The TRM shows the SoC does not depend on it for its own 32 kHz clock. The PMU slow clock mux `clk_deepslow_sel` selects 2'b00 xin_osc0_div (24 MHz divided), 2'b01 xin_osc1_32k, or 2'b10 clk_pvtm_32k (TRM p.101). PMU_GRF has a PVTM divider "to generate 32KHz clock" (TRM p.163). The RV1103 has no RTC and runs without it (HDG p.15 note "RV1103G does not support RTC").
- GPIO0_A0 (pin 58) can be CLK_32K / RTC_CLKO (DS p.19, TRM p.191). In REF it is used as LCD_RST, not as a 32 kHz input.
- The RTC block itself is specified "based on a 32.768 kHz crystal oscillator", with a supply of 1.6–3.3 V, typ 2.5 µA, and "32.768 kHz clock self-detect" (TRM p.762). It also has an internal analog 32 kHz generator that is "affected by temperature, voltage" and can be calibrated against 24 MHz (TRM p.762–763).
- **Conclusion: likely omittable if the on-chip RTC is not used (GPS supplies UTC). UNVERIFIED.** No source says how to terminate OSC_RTC_XIN/XOUT when the crystal is absent, or whether RTC_AVDD3V3 may be unpowered. The low-risk choice is to keep RTC_AVDD3V3 = 100 Ω + 1 µF from VCC_3V3 (HDG says "must"), and either fit the crystal (about one cheap part plus 2 caps) or leave pads DNP.

---

## 4. nPOR (pin 66)

**REF V1.3 (REF p.8):**
- R1110 **1 kΩ 5% 0402** pull-up to VCC_3V3 (= PMU_VCC3V3 rail).
- C1114 **10 nF X5R 25V 0402** to GND.
- R1111 and R1112 (both DNP, 0402) form an optional divider from VCC5V0_SYS into the same node ("Option" box).
- There is no supervisor IC and no reset button on REF.

**Older values:**
- HDG Fig 2-3 (HDG p.15) shows R1110 **10 kΩ** + C1114 **100 nF**. IPC p.8 uses R13 10K + C36 100nF.
- REF V1.2 changed them to 1K / 10nF (REF p.3).

**Luckfox:**
- LPM: R12 1K + C38 10nF X5R 25V, the same as REF V1.3.
- LPM also has a reset key: Key1 to GND → R22 100R → NPOR, with ED1 "NC/ESD5451N" ("Power Reset" block).
- CORE takes NPOR to the board-to-board connector, so its RC is on the carrier (CORE p.1).

**How it works:**
- HDG §2.1.2 (HDG p.15): the chip has an internal POR. Pin 66 pulled up to PMU_VCC3V3 "is used as the input reference of the voltage comparator of the internal NPOR. The capacitor C1114 is used to eliminate jitter … place the resistor and capacitor close to the RV1106G."
- The RC is a deglitch, not a delay generator. 1 kΩ × 10 nF = 10 µs, versus 1 ms for the old 10 kΩ × 100 nF.

**Timing (REF p.5, "Power-on Sequence" table and timing diagram):**
- Slot 1 = VDD_0V9 and VDD_ARM, slot 2 = VCC_1V8 and VCC_DDR, slot 3 = VCC_3V3.
- "Finally, nPOR RESET 10ms after VCC_3V3 is ready".
- Notes: "T0, T1 > 1ms; **T2 = 10ms (Internal)**; Trise > 100us". The 10 ms is generated inside the chip after PMU_VCC3V3 rises.
- HDG §2.2.1 (HDG p.20): low voltage first, the same voltage at the same time, intervals > 1 ms, soft-start > 100 µs. Sequence: VDD_0V9 & VDD_ARM → VCC_1V8 & VCC_DDR → VCC_3V3.
- Power-off: "no strict requirement … all power sources can be powered off at the same time" (§2.2.2, HDG p.21).

Since NPOR references VCC_3V3, which is the last rail up, sequencing by rail order is sufficient. A reset button is optional (LPM fits one).

---

## 5. TVSS, DRAM_ZQ, FEPHY_EXTR, CODEC_VCM / MICBIAS

| Pin | Function used (reference) | Our case (block unused) |
|---|---|---|
| **TVSS (57)** | Tied directly to GND (REF p.8; LPM Part A; CORE p.1; IPC p.8). DS p.19 lists it only by name | Tie to GND, as all references do. Not optional |
| **DRAM_ZQ (52)** | R1002 **240 Ω 1% 0402** to GND (REF p.7). LPM R1 240R 1%, CORE R24 240R 1%. The SiP DDR3L needs it | Always required (the DDR is in the package) |
| **FEPHY_EXTR / ETH_EXTR (102)** | R1001 **6.04 kΩ 1% 0402** to GND (REF p.7). HDG Table 2-11 (HDG p.29): "Connect 6.04K precision resistor in series to ground", "placed close to the chip". LPM R7 6.04K ±1%, CORE R28 6.04K 1% | **UNVERIFIED** whether it may be left open. Every local RV1106 board fits it, Ethernet or not. Recommend fitting it (one cheap 1% 0402) |
| **FEPHY_RXP/RXN/TXP/TXN (98/97/100/99)** | 0 Ω series resistors "cannot be omitted" (HDG Table 2-11, p.29) | Dedicated analog pins, not GPIO (DS p.18). No source covers the unused case. **UNVERIFIED**: leave NC |
| **CODEC_VCM (30)** | C1026 **4.7 µF X5R 6.3V 0402** to GND (REF p.7). HDG Table 2-12 (HDG p.31): "Connect a 4.7uF capacitor to ground". VCM cap "placed close to the chip" (§3.3.4, HDG p.48). LPM C3 4.7µF, CORE C42 4.7µF | **UNVERIFIED**. Recommend keeping the 4.7 µF (cheap, keeps the internal reference defined) |
| **CODEC_MICBIAS (32)** | Output that feeds net VCC1V8_MICBIAS → R1003 100R → C1000 4.7µF → R1000/R1004 1.1K bias for the mic connector J1000 (REF p.7). DS p.23: VMICB 0.8–0.975×AVDD, ≤ 3 mA | NC when the mic is unused. LPM brings it to a pad, P9 "BIAS" |
| **CODEC_MIC0P/N (34/33)** | 1 µF series caps C1001/C1002 (REF p.7; HDG Table 2-12) | NC |
| **CODEC_MIC1P/N (36/35)** | NC (✕) in REF p.7 | NC |
| **CODEC_LINEOUT (29)** | Net LINEOUT to the audio page (REF p.7) | NC |
| **CODEC_AVSS (37)** | R1006 **0 Ω** to GND, note "Place R1001 close to Pin37" (REF p.7; the note names R1001 but the part at pin 37 is R1006, a source typo). LPM R4 0R, CORE R26 0R | Tie to GND (keep the 0 Ω or connect directly) |
| **CODEC_AVDD1V8 (31)** | Via FB1000 + 10 µF + 100 nF (§1) | See §8 |

---

## 6. USB

**USB_VBUSDET (pin 25):**
- REF p.7: only test point TP1002. REF uses the USB as a host to an on-board USB Wi-Fi module (REF p.16), so VBUS detect is not needed there.
- HDG Fig 2-18 (HDG p.27), "RV1106G USB insert detection": VCC5V0_USB → R2503 **10 kΩ 5%** → USB_DET, R2504 **18 kΩ 5%** to GND, C2502 **100 nF** X5R 16V.
- HDG text (HDG p.26): "USB interface is Device mode by default. Since the USB_VBUS (USB_DET) is used as the USB device insertion detection, **the input detection voltage must be less than 3.3V, and the high level must be detected to be recognized by the computer.**"
- LPM ("Type-C"): VBUS → R2 10K / R5 18K → USB_DET_IN, with C7 100 nF. This is the same divider.
- Arithmetic: 5.00 V × 18/28 = 3.21 V, and 5.25 V × 18/28 = 3.375 V. The latter is above the HDG's "< 3.3 V" at the top of the USB VBUS range.
- **UNVERIFIED**: DS gives no VBUSDET threshold or absolute max. A designer may prefer 10k/15k (3.0 V at 5.0 V, 3.15 V at 5.25 V). That is not a reference value.
- **For gadget mode this pin must be wired. It is not optional.**

**USB_DP/DM (27/26):**
- HDG Table 2-10 (HDG p.28): "Connect a 2.2ohm resistor in series".
- HDG Fig 2-20 (HDG p.28): R2501/R2502 **2.2 Ω 5% 0402**, plus an optional common-mode choke FB2500 90R@100MHz (RP2_0405) marked **DNP**, bypassed by R2505/R2506 0 Ω 0402. "consider reserving a common mode choke … choose the resistor or common mode choke according to the actual situation" (HDG p.27).
- REF p.7 and REF p.16 have **no** series resistors (direct to the Wi-Fi module).
- LPM goes direct from the SoC to the Type-C (USB_P/USB_N) with **no** series R and no ESD drawn. CC1/CC2 have R3/R6 5.1 kΩ to GND, and VBUS feeds the system through D1 MBR230LSFT1G.

**ESD and layout:**
- HDG Fig 2-17 (HDG p.26) USB socket: ESD2500 **ESD5302F** (SOT-23) on D+/D−, ED2500 **ESD5451N** on VBUS, C2500 10 µF + C2501 100 nF on VBUS.
- §3.3.3 (HDG p.48): ESD parasitic capacitance < 1 pF, 90 Ω ±10% differential, < 6 in, ≤ 6 vias (recommend < 4), intra-pair skew < 30 mil.
- HDG p.26: "If the UART/SD is not used for programming, there need to reserve interface since the USB is used as firmware programming port."

**Supplies:** SARADC_USB_AVDD1V8 is fed through the 1 Ω (R1005), and USB_AVDD3V3 direct, each with 100 nF (see §1). "USB must always power supply" (REF p.7 symbol text; also LPM, CORE).

---

## 7. microSD on SDMMC0 (VCCIO4 = 3.3 V, SD 2.0)

**Pins (DS p.18–19, REF p.9):**

| Signal | Pin | GPIO | Internal pull |
|---|---|---|---|
| SDMMC_DET | 11 | GPIO3_A1 | pull-up |
| D0 | 14 | GPIO3_A3 | pull-up |
| D1 | 12 | GPIO3_A2 | pull-up |
| D2 | 18 | GPIO3_A7 | pull-up |
| D3 | 17 | GPIO3_A6 | pull-up |
| CLK | 15 | GPIO3_A4 | pull-down |
| CMD | 16 | GPIO3_A5 | pull-up |
| VCCIO4_VCC | 13 | — | — |

**Series resistors:**
- CLK: R1201 **22 Ω 5% 0402** at the SoC (REF p.9). HDG Table 2-7 (HDG p.24): "SDMMC_CLK … Connect a 22ohm resistor in series". LPM R16 22R. CORE has R29 22R in the same block (CORE p.1 text layer).
- DAT/CMD: direct connection (Table 2-7).
- DET: R8205 **100 Ω 5%** between the socket CD pin and SDMMC_DET (REF p.19). LPM R54 100R.

**Pull-ups on CMD/DAT:** none external in REF p.9/p.19 or LPM. Table 2-7 relies on the internal pull-ups (DS p.21: Rpu 16/25/43 kΩ min/typ/max).

**SDMMC_DET wiring:**
- REF p.19: socket J8202 pin 9 "CD" → R8205 → SDMMC_DET. Inserting the card pulls it to ground; the internal pull-up keeps it high when no card is present.
- LPM: TF1 CD1 (pin 9) to GND, CD2 (pin 10) → R54 100R → SDMMC_DET.
- CORE p.1: SDMMC0 is used for an SDIO Wi-Fi module, so SDMMC_DET is tied to GND through **R53 10 kΩ** (forces SDMMC mode permanently).

**HDG Table 2-2 (§2.1.4, HDG p.16), SDMMC0_DET (internal pull-up):**
- "0: Recognized as SD card insertion, SDMMC/JTAG/UART pins are multiplexed as SDMMC output."
- "1: Recognized as SD card not inserted, SDMMC/JTAG/UART pins are multiplexed as JTAG/UART output (Default)."
- §2.1.5: DET must be high before connecting a JTAG emulator.
- So for SD boot, DET must be low when the card is present. Either use a socket with a CD switch to GND, or tie DET to GND (CORE style, 10 kΩ). Tying it low gives up JTAG/UART2_M0 on the card pins, which our design does not need.

**Card power switch: yes, REF switches the card VDD (REF p.19 "Card Power"):**
- Q8201 **TCS1025/TCS1012** P-MOSFET, SOT-23. Source on VCC_3V3, drain on VCC3V3_SD.
- R8204 **100 kΩ** gate-source pull-up and C8202 **100 nF** gate-source (slow turn-on).
- R8206 **10 kΩ** gate ← SDMMC_PWREN = GPIO0_A1_d (pin 59, REF p.8).
- R8209 0 Ω 0603 bypass, **DNP**.
- Output: C8203 100 nF, R4218 **10 kΩ** bleeder, and at the connector C8204 **4.7 µF X5R 6.3V 0402** + C8205 100 nF.
- Note: "SDMMC0_PWREN=L VCC3V3_SD=3.3V (Default); SDMMC0_PWREN=H VCC3V3_SD=0V".
- LPM is the same topology: Q1 **SI2301CDS-T1-E3**, R51 100K, C69 100nF, R55 10K, R50 bypass (value not shown), C70 100nF, R52 10K, C71 **10 µF** X5R 6.3V, C72 100nF.
- Footgun: "Default ON" depends on GPIO0_A1's internal pull-down (DS p.21: 16–43 kΩ) beating the 100k+10k path. Gate ≈ 3.3 × Rpd/(Rpd+110k) ≈ 0.43–0.93 V, so VGS ≈ −2.4 to −2.9 V. Whether that turns the FET fully on depends on its VGS(th), which has **not been checked against the FET datasheet**. Keep PWREN on a pin whose reset state is pull-down (GPIO0_A1 is "_d").

**ESD:**
- REF p.19: one TVS per line, 8 in total: ED8200–ED8206 + D8200, on DET, D0–D3, CLK, CMD and VDD. Six are **ESD5341N** and two **ESD5451N** (ESD0402). Which two lines get the ESD5451N is not readable from the drawing (**UNVERIFIED**; VDD and DET are likely).
- LPM: no SD ESD drawn.
- HDG §3.3.1 (HDG p.46): "For ESD devices, select devices with a junction capacitance of less than 1pF, and … place them close to the connector".
- Layout (Table 3-1, HDG p.47): 50 Ω ±10% single-ended, data-to-clock matching < 120 mil, < 4 in, spacing ≥ 2W. Ground-shield DAT/CMD as a group and CLK separately.

**Socket:** REF J8202 **TFP09-2-12B** (9 signal pins + 4 shell lugs G1–G4 to GND). LPM TF1 (part number not given; it has CD1/CD2/SHELL).

---

## 8. Unused pins and blocks

**What the sources say:**
- HDG has **no explicit unused-pin rules**. A search of the full English HDG and the Chinese V1.1 HDG for 悬空/不用/unused/floating found nothing relevant.
- REF and LPM mark unused GPIO pins **NC (✕)**, for example:
  - REF p.9: pins 38, 40, 45, 46 (SPI1_M0 / EMMC_D4–D7). These are the pins we plan to use for SPI1 to the ESP32-C5.
  - REF p.10: pins 104, 105, 8, 9.
  - REF p.7: CODEC_MIC1P/N pins 36/35.
  - The GPIO suffix "_d/_u/_z" is the reset pull (DS p.18–19).
- TRM p.443: "Unused Module Pin is tied to zero!" (internal mux note, not a board rule).

**MIPI CSI pins (117–128):** these are muxed GPIO3_B0..C3 ("_d", pull-down by default, DS p.19). Leave NC like other unused GPIO. VCCIO7/MIPI_AVDD1V8 (pin 1) is also the IO supply for GPIO3_B/C/D, so it must stay powered (1 Ω + 100 nF, §1).

**FEPHY pins (97–100):** dedicated analog pins. No source covers the unused case. **UNVERIFIED**: NC. ETH_EXTR: see §5.

**CODEC pins:** see §5. **UNVERIFIED**: MIC/LINEOUT/MICBIAS NC, VCM cap kept, AVSS to GND.

**Must the supplies stay powered when the block is unused? UNVERIFIED.**
- No local source shows a board with FEPHY, CODEC or MIPI supplies left unpowered. Every local RV1106 board (REF, IPC, LPM, CORE, Pico Zero, Pico Ultra-W) powers all of them. LPM and the Zero/Ultra-W boards also use Ethernet.
- Explicit statements:
  - "USB must always power supply" (REF p.7 symbol).
  - The capacitors "cannot be omitted" (HDG §2.2.3.1/§2.2.3.3).
  - RTC RC "must be 100ohm and 1uF" (HDG p.14).
- Several "analog" pins are shared and cannot be turned off without losing something:
  - Pin 96 also supplies OTP and TSADC.
  - Pin 24 also supplies VCCIO2/SARADC (REF p.9 note "VCCIO2_VCC1V8 supply from USB_AVDD1V8").
  - Pin 1 is also VCCIO7.
  - Pin 101 ETH_AVDD3V3 has no shared role documented.
- **Recommendation:** power every supply pin as REF does. The cost is one 100 nF plus a bead/0 Ω/1 Ω per pin. The beads FB1000 (codec) and FB1001 (FEPHY 3V3) could become 0 Ω if their blocks are unused (a design judgement, not a reference value). Keep FB1100 on pin 96 because it also feeds OTP/TSADC.

---

## 9. Maskrom and recovery

**Boot order (HDG §2.1.3, HDG p.16):** SFC/SPI flash → eMMC → SDMMC card.

**Fallback (TRM §1.2, TRM p.14):** "When boot code is not ready in these devices, also provide system code download into them by USB OTG or UART interface." DS p.6 lists the BootROM download interfaces as "USB interface, UART interface". So **with no flash or eMMC and no bootable card, the BootROM falls through to USB download (maskrom)** without any button. Pulling the card is our maskrom method. The exact BootROM behaviour is not further documented locally.

**Recovery key on SARADC_IN0:**
- REF p.9 "RECOVERY Key": SARADC_IN0 (pin 23, GPIO4_C0_z, high-Z with no internal pull) ← R1206 **10 kΩ 5%** pull-up to VCC_1V8, C1213 **1 nF C0G 50V**, R1207 **100 Ω** series to RECOVERY_KEY, ED1200 **ESD5451N**, SW1200 2-pin key to GND.
- Red note: "**SARADC_IN0 must always be pulled-up.**"
- HDG §2.3.8 (HDG p.36): ADC_IN0 is "multiplexed as a RECOVER mode trigger … On the premise that the system has already programmed the firmware, pull down ADCIN0 when the system starts … then RV1103G/RV1106G enters the Rockusb programming mode". This is the loader's Rockusb mode, not the BootROM maskrom. Release the key to return to 1.8 V.
- HDG Fig 2-35 (HDG p.37) shows the pull-up to **VCC1V8_USB** (10 kΩ 1% + 1 nF C0G 25V). REF uses VCC_1V8.
- LPM "System RECOVERY Key": Key2 on SARADC_IN0 with R21 10K to VCC_1V8, C44 1nF C0G 50V, R23 100R, ED2 NC/ESD5451N. This is Luckfox's "BOOT" key. The silk name "BOOT" is not in the schematic (**UNVERIFIED** naming).
- EVB p.7: "press and hold the Update button on the board, then power on or press the RESET button to enter maskrom mode" (EVB board; the pin is not stated).

**Our case (SD-only):**
- The key is optional, because removing the card forces USB download.
- **The 10 kΩ pull-up (+1 nF) on SARADC_IN0 is mandatory** per REF. Without it the high-Z pin could read low at boot and drop the loader into Rockusb.
- If SARADC_IN0 is wanted as a battery-sense ADC instead, that conflicts with the recovery function. Use SARADC_IN1 (pin 22) for battery sense:
  - REF uses IN1 for a light sensor: 10 kΩ to VCC_1V8 + 1 nF (REF p.19 R8200/C8206). LPM uses R57 10K + C73 1 nF.
  - HDG Fig 2-35 shows a 10k/10k divider + 1 nF on ADCIN1.
  - ADC range is 0–1.8 V, 10 bit (HDG §2.3.8; DS p.24: VREFP 1.8 V, CIN 8 pF).

---

## 10. Debug UART2_M1 (pins 79 TX = GPIO1_B2_d, 80 RX = GPIO1_B3_u)

| Source | Series resistors | Connector |
|---|---|---|
| REF p.8 | R1108 (TX) and R1106 (RX), **510 Ω 5% 0402**. Changed to 510R in V1.3 (REF p.3). Both are **marked DNP**, as is J1100 | J1100 3-pin, 1.25 mm |
| IPC p.8 | R14/R15 **100 Ω** | test points TP4–TP6 |
| LPM | **none**: UART2_TX/RX go straight to header U3 pins 1/2 | header |

HDG §2.3.9 (HDG p.36–37):
- UART2_M1 is the debug port.
- UART2_M0 is muxed on the SD pins (TF-to-serial adapter, usable only when DET is high).
- 115200 baud, no flow control (HDG p.38).

---

## 11. Other parts at the SoC

- **ePAD (129):** GND (REF p.7). HDG §3.2 (HDG p.41): a GND via per GND pad.
- **Test points in REF:**
  - TP1002 on USB_VBUSDET (p.7).
  - A TP on FEPHY_AVDD3V3 (p.7).
  - TP1202/TP1203 on SDMMC_D0/D1 (p.9; the V1.3 history says they were deleted but they are still drawn).
  - TP1200/TP1201 on the SPI flash.
- **VDD_ARM tied to VDD_0V9:** REF p.11 provides it as R2008 **0 Ω 0603 DNP** between VDD_0V9 and VDD_ARM.
  - Red note (Chinese, REF p.11): "需要用到高算力的RV1106G3产品，VDD_0V9需要定频0.95V。此时不建议VDD_ARM与VDD_0V9合并供电，易造成功耗增加。" = *"For RV1106G3 products that need high compute, VDD_0V9 must be fixed at 0.95 V; in that case merging VDD_ARM with VDD_0V9 is not recommended, as it tends to increase power consumption."*
  - Green "Option" box: (1) dual-camera fusion/AI-ISP needs an adjustable, independent VDD_ARM; (2) general IPC with low CPU demand "VDD_ARM可以与VDD_0V9合并供电，降低成本" (*may share VDD_0V9 to cut cost*).
  - REF defaults: VDD_0V9 = 0.882 V (R2005 47k / R2006 100k, FB 0.6 V), VDD_ARM range 0.805–1.006 V, default 0.905 V (PWM AVS on AVS_ARM = GPIO1_A2, pin 74).
  - Peak currents (REF p.5 table): VDD_0V9 1.6 A, VDD_ARM 0.5 A, VCC_DDR 0.5 A, VCC_1V8 0.1 A, VCC_3V3 0.2 A.
- **VCCIO3 domain (pins 38–48: EMMC/FSPI/SPI1_M0):** VCCIO_FLASH selected by 0 Ω (R1205 3V3 fitted, R1204 1V8 DNP, REF p.9). FSPI_CLK pin 48 has R1200 22R (HDG Table 2-4/2-5: 22 Ω on FSPI_CLK/eMMC_CLK).
  - Our SPI1_M0 uses pins 40 (CS0), 38 (CLK), 45 (MOSI), 46 (MISO). These are EMMC_D4–D7 (DS p.18), the same pads the BootROM's 8-bit eMMC probe would use.
  - **UNVERIFIED** whether the BootROM drives them during its eMMC probe. Consider holding the ESP32-C5 in reset (EN low) until Linux is up.
- **Operating temperature:** DS p.21 Table 3-2 gives TA **0 to 80 °C**. This matters for an outdoor solar node.

---

## Decisions for the schematic designer

1. VDD_0V9 decoupling: REF/LPM (7 caps) or the HDG text (≥1×100 nF per each of 8 pins + 2×10 µF + 2×1 µF)?
2. 32.768 kHz crystal: fit (all references do) or DNP, given the GPS. Keep RTC_AVDD3V3 = 100 Ω + 1 µF either way. Decide whether to keep a Schottky (B5819WS/RB521S-30) when there is no backup cell.
3. VBUSDET divider: REF/LPM 10k/18k + 100 nF (3.375 V at 5.25 V) or a lower ratio.
4. USB D+/D−: HDG 2.2 Ω series + DNP CMC footprint, or direct (LPM).
5. SDMMC_DET: socket CD switch (REF/LPM) or a hard 10 kΩ to GND (CORE).
6. Card-power P-FET (REF/LPM) or not. If fitted, check the FET's VGS(th) against the pull-down analysis in §7.
7. SD ESD (REF fits 8, LPM none). HDG wants < 1 pF parts.
8. Unused FEPHY/CODEC: keep the supplies and passives (recommended), and decide bead vs 0 Ω.
9. Recovery key on SARADC_IN0: optional. The pull-up is mandatory. Use IN1 for battery sense.
10. VDD_ARM tied to VDD_0V9: REF allows it for low-CPU products but warns against it for high-compute RV1106G3 at 0.95 V. Confirm this is acceptable (owner decision already taken, flagged here).
11. Reset button on NPOR (LPM) or none (REF).
