# Klepon Rev 1: symbol pin numbers vs LCSC datasheet pinouts (T15)

Date: 2026-11-20. Read-only check. No project files were edited.

## Method

- **Symbol pins:** from the `<libparts>` and `<nets>` sections of `t15/net.xml`, which come from the symbols embedded in each schematic.
- **Datasheet pins:** from the LCSC part's own datasheet. Short forms used below: `DS/` = `hardware/datasheets/`; `dl/` = `scratch/t15/ds/`, downloaded from the LCSC DB URL. Diagrams with no text were rendered to PNG and read by eye.
- **Footprint pads:** from `/usr/share/kicad/footprints/*.kicad_mod`.
  - SOT-23: pads 1 and 2 on the left side, pad 3 alone on the right.
  - SOT-23-5/6: counter-clockwise from pad 1 at top left.
  - D_SMA, D_SOD-123 and LED_0603: pad 1 at −x, inside the closed (cathode) end of the silkscreen.
- **Pin-1 marking:** AOS and Winsok draw no pin numbers. Pin 1 is the lead beside the marking dot (G), the other lead on that side is pin 2 (S), and the single lead is pin 3 (D). This is the JEDEC SOT-23 numbering, and the same numbering CJ prints for its 2N7002 and UMW prints for its SI2318A.

## Table

| ref | part | symbol pin → name | datasheet pin → function (file, page) | footprint pad assumption | verdict |
|---|---|---|---|---|---|
| Q1, Q2 | AO3400A, AOS, C20917 (`Transistor_FET:AO3400A`) | 1 G, 2 S, 3 D | 1 G (pin by dot), 2 S, 3 D (single lead). N-ch, VGS ±12 V. `DS/AOS_AO3400A.pdf` p.1 pin diagram | SOT-23 pad n = pin n | OK |
| Q3, Q4 | SI2318A, UMW, C2681218 (drawn with the AO3400A symbol) | 1 G, 2 S, 3 D | 1 G, 2 S, 3 D (pinning table). N-ch 40 V, VGS ±20 V. `DS/UMW_SI2318A.pdf` p.1 §3 and §4 | SOT-23 pad n = pin n | OK |
| Q11 | WST2319, Winsok, C2906299 (drawn with the AO3401A symbol) | 1 G, 2 S, 3 D | 1 G (pin by dot), 2 S, 3 D (single lead). P-ch −40 V, VGS ±20 V. `DS/Winsok_WST2319.pdf` p.1 "SOT-23-3L Pin Configuration" | SOT-23 pad n = pin n | OK |
| Q7, Q9, Q401 | AO3401A, AOS, C15127 | 1 G, 2 S, 3 D | 1 G (pin by dot), 2 S, 3 D. P-ch. `DS/AOS_AO3401A.pdf` p.1 pin diagram | SOT-23 pad n = pin n | OK |
| Q8, Q10, Q12 | 2N7002, CJ/JCET, C8545 | 1 G, 2 S, 3 D | 1 GATE, 2 SOURCE, 3 DRAIN. `dl/C8545.pdf` p.1 SOT-23 box | SOT-23 pad n = pin n | OK |
| U31 | TL432 0.5 %, UMW, C545558 (`Reference_Voltage:TL432DBZ`) | 1 REF, 2 K, 3 A | 1 R (reference), 2 K (cathode), 3 A (anode). `DS/UMW_TL432.pdf` p.1 §4 | SOT-23 pad n = pin n | OK (see note 1) |
| U22 | XC6206P332MR, Torex, C5446 (`Regulator_Linear:XC6206PxxxMR`) | 1 GND, 2 VO, 3 VI | SOT-23: 1 VSS, 2 VOUT, 3 VIN. `DS/Torex_XC6206.pdf` p.2 pin assignment | SOT-23 pad n = pin n | OK |
| U5–U8, U10, U11 | TLV62569DBVR, TI, C141836 (`Regulator_Switching:TLV62569DBV`) | 1 EN, 2 GND, 3 SW, 4 VIN, 5 FB | SOT23-5: 1 EN, 2 GND, 3 SW, 4 VIN, 5 FB. `DS/TI_TLV62569.pdf` p.3 §5 Pin Functions | SOT-23-5, counter-clockwise | OK |
| U21 | ME6211C33M5G-N, Microne, C82942 (`Regulator_Linear:ME6211C33M5`) | 1 VIN, 2 VSS, 3 CE, 4 NC, 5 VOUT | ME6211CxxG SOT23-5: 1 VIN, 2 VSS, 3 CE, 4 NC, 5 VOUT. `DS/Microne_ME6211.pdf` p.4 pin table | SOT-23-5, counter-clockwise | OK |
| U3 | DW01A, PUOLOP, C351410 (`klepon:DW01A`) | 1 OD, 2 CS, 3 OC, 4 TD, 5 VCC, 6 GND | 1 OD, 2 VM (current sense; the symbol calls it CS), 3 OC, 4 TD, 5 VCC, 6 GND. `DS/PUOLOP_DW01A.pdf` p.2 Pin Configuration (top view 1-2-3 bottom, 6-5-4 top) | SOT-23-6, counter-clockwise | OK (see note 2) |
| Q5, Q6 | FS8205A, Fuxinsemi, C908265 (`klepon:FS8205A`) | 1 S1, 2 D, 3 S2, 4 G2, 5 D, 6 G1 | Marking view, dot at bottom left = pin 1. Bottom row 1 S1, 2 D1/D2, 3 S2; top row 4 G2, 5 D1/D2, 6 G1. `DS/FUXINSEMI_FS8205A.pdf` p.1 "Marking" | SOT-23-6, counter-clockwise | OK |
| U1 | USBLC6-2SC6, TECH PUBLIC, C2827654 (`Power_Protection:USBLC6-2SC6`) | 1 I/O1, 2 GND, 3 I/O2, 4 I/O2, 5 VBUS, 6 I/O1 | 1 I/O1, 2 GND, 3 I/O2, 4 I/O2, 5 VBUS, 6 I/O1. Same as ST. `DS/TECHPUBLIC_USBLC6-2SC6.pdf` p.1 (image-only PDF, rendered) | SOT-23-6, counter-clockwise | OK |
| D1 | SMAJ24A, Hongjiacheng, C19077541 (`Device:D_Zener_Small` on `D_SMA`) | 1 K, 2 A | No pin numbers. The band marks the cathode (unidirectional). `dl/C19077541.pdf` (identical to `DS/SMAJ_series.pdf`) p.2 note 1, p.1 symbol | D_SMA pad 1 (−x, closed silk end) = K | OK |
| D3 | BZT52C12, YONGYUTAI, C2891780 (`D_Zener_Small` on `D_SOD-123`) | 1 K, 2 A | "Polarity: Color band denotes cathode end". `dl/C2891780.pdf` p.1 | D_SOD-123 pad 1 = K | OK |
| D4, D5 | BZT52C10, MDD, C173431 (`D_Zener_Small` on `D_SOD-123`) | 1 K, 2 A | "Cathode bar" on the body. `DS/MDD_BZT52.pdf` p.1 outline | D_SOD-123 pad 1 = K | OK |
| D2 | KT-0603R, KENTO, C2286 (`Device:LED_Small` on `LED_0603_1608Metric`) | 1 K, 2 A | Vendor drawing: ① = "+" (anode), ② = "−" (cathode, green corner mark, T-mark bar end). `dl/C2286.pdf` p.2 §2 | LED_0603 pad 1 = K, so the vendor's ② lands on KiCad pad 1 | OK (see note 3) |

## FET orientation in the circuit (body diodes)

Nets come from `t15/net.xml`. A P-channel body diode conducts from D to S; an N-channel body diode conducts from S to D.

| ref | circuit role | D | S | G | body-diode check |
|---|---|---|---|---|---|
| Q1 + Q2 (AO3400A) | ACFET/RBFET pair for USB VBUS (TI BQ25798 Fig 10-1) | Q1: VBUS (USB). Q2: Net-(Q2-D) = U2 VBUS | common Net-(D4-A) | common Net-(D4-K), R20; D4 10 V zener K→G, A→S | Common source, diodes point outwards, so the pair blocks both ways. OK. The 10 V clamp is below VGS ±12 V. |
| Q3 + Q4 (SI2318A) | ACFET/RBFET pair for VDCIN | Q3: VDCIN. Q4: Net-(Q2-D) | common Net-(D5-A) | common Net-(D5-K), R21; D5 10 V | Same as Q1/Q2. OK. VGS ±20 V. |
| Q11 (WST2319, P) | Reverse-polarity FET on the barrel jack | Net-(Q11-D) = J2 pin 1 (jack centre) | VDCIN | Net-(D3-A): R22 100k to GND, D3 12 V K→VDCIN (S) | The body diode conducts jack → VDCIN, so correct polarity starts it and a reversed input is blocked. OK. VSG clamp 12 V < 20 V. |
| Q7 (AO3401A, P) | High-side switch, 5 V → VDD_FEM | VDD_FEM | VCC5V0_SYS | Net-(Q7-G), R120/R121 → Q8 | Body diode VDD_FEM → 5 V, blocks when off. OK. |
| Q9 (AO3401A, P) | Hold-off switch VSYS → VSYS_SW | VSYS_SW | VSYS | Net-(Q9-G), R307/R308 → Q10/Q12 | Body diode VSYS_SW → VSYS, so VSYS does not leak forward when off. OK. |
| Q401 (AO3401A, P) | SD-card power switch | VCC3V3_SD | VCC_3V3 | Net-(Q401-G) | OK |
| Q8, Q10, Q12 (2N7002) | Low-side level shifters that pull P-FET gates low | Q8: Net-(Q8-D). Q10/Q12: Net-(Q10-D) (wired-OR) | GND | Q8: HALOW_FEM_EN. Q10/Q12: comparator side | OK |
| Q5 + Q6 (FS8205A ×2, paralleled) | DW01A cell-protection FETs | D1/D2 common Net-(Q5-D-Pad2) | S1: Net-(J3-Pin_2) (B−, also DW01A GND). S2: GND (P−) | G1 = DW01A OD (pin 1). G2 = DW01A OC (pin 3) | Common drain, back-to-back. OD drives the FET whose source is on B− and OC the FET whose source is on P−, matching `DS/PUOLOP_DW01A.pdf` p.3 Typical Application (M1 = OD at BATT−cell side, M2 = OC at BATT−). VM via R12 1k to P− matches R2 1k. OK. |

## Notes

1. **U31 (UMW TL432) is a 1.25 V reference, not TI's 2.495 V TL432.** The stock `TL432DBZ` symbol was drawn for TI's part (`DS/UMW_TL432.pdf` p.1 "1.25V band gap", p.3 Vref 1.25 V typ). The pin order 1 REF, 2 K, 3 A is the same as TI's TL432 DBZ, so the pins are fine. The design already uses the 1.25 V value (worklog `docs/worklog/2026-11-20-pcb-kickoff.md:327`). Check that no symbol description or field text says 2.5 V. In this circuit REF is tied to K, so even a REF/K swap would have no effect. Only A on pin 3 matters, and it is correct.
2. **U3 pin 4 (TD) is left open (no-connect),** which matches the vendor application circuit (`DS/PUOLOP_DW01A.pdf` p.3, where TD sits on the chip outline with no wire). Pin 2 is called CS in the klepon symbol and VM in the datasheet: same function.
3. **D2 assembly note:** KENTO numbers the LED's anode ① and cathode ②, the reverse of KiCad's pad 1 = K. Electrically this is fine: the K net is on pad 1 and the cathode mark has to land on pad 1. Check the polarity in the JLCPCB placement preview, because a CPL rotation built from the vendor's numbering could fit the part backwards. The circuit: K → U2 STAT (open drain), A → R9. Correct.
4. **Package names:** Winsok calls its package "SOT-23-3L" and Torex calls the XC6206's "SOT-23-3L"; both use the standard SOT-23 footprint. The pad count was checked earlier.

## Result

- **MISMATCH:** none.
- **UNVERIFIED:** none for pin mapping.
- The AOS (AO3400A, AO3401A) and Winsok (WST2319) datasheets give no pin numbers. Their mapping is inferred from the pin-1 dot plus the standard SOT-23 numbering, which is consistent with the CJ and UMW SOT-23 FETs.
