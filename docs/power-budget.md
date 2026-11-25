# LinkNode power budget (Rev 1)

Status: refreshed for the drawn schematic on 2026-11-20 (T19). GPS replaces the original ESP32; the C5 is on 2.4 GHz;
the external panel is a handheld 2–3.5 W one (P-11). Every figure comes from the cited source. **EST** marks an
estimate and **MEASURE** marks a figure that must be measured on the first board. The numbers are computed by
[`docs/calc/power_budget.py`](calc/power_budget.py); change an input there and rerun it.

## Power tree (as drawn)

```
USB-C VBUS ─(Q1/Q2)─ VAC1 ┐
DC jack 3.6–24 V ─(Q11, Q3/Q4)─ VAC2 ┴─ BQ25798 ─ VSYS (3.0–4.2 V) ─┬─ 18650 1S cells (DW01A + 2× FS8205A)
                                                                    ├─ ME6211 LDO (GPS_PWR_EN) → VCC3V3_GPS → ATGM336H
                                                                    ├─ XC6206 (from VBAT) → GPS backup
                                                                    └─ Hold-off (LM2903, on 3.63 V / off 3.32 V; USB bypass)
                                                                         └─ VSYS_SW → TPS61089 boost → VCC5V0_SYS (5.04 V)
                                                                               ├─ TLV62569 → VDD_0V9 0.88 V (+VDD_ARM via 0R)
                                                                               ├─ TLV62569 → VCC_DDR 1.35 V
                                                                               ├─ TLV62569 → VCC_1V8
                                                                               ├─ TLV62569 → VCC_3V3 (SoC IO, microSD switch)
                                                                               ├─ TLV62569 (C5_PWR_EN)    → VCC3V3_C5    → ESP32-C5
                                                                               ├─ TLV62569 (HALOW_PWR_EN) → VCC3V3_HALOW → HT-HC01 VBAT/VDD_IO
                                                                               └─ AO3401A (HALOW_FEM_EN)  → VDD_FEM 5 V  → HT-HC01 PA/LNA
```

## Sources

| Load | Figure | Source |
|---|---|---|
| RV1106 SoC, heavy IPC (2K camera, NPU, encoder) | 731.7 mW at the rails, 25 °C: VDD_0V9 478.5 mA at 0.88 V, VDD_ARM 40.1 mA, VCC_DDR 92.5 mA at 1.376 V, VCC_1V8 20 mA, VCC_3V3 34.6 mA | Rockchip RV1106G Power Consumption Test Report V1.2, sheet "场景+SC530AI" |
| RV1106 peaks (same scenario) | VDD_0V9 1085 mA, VCC_DDR 242.5 mA, VCC_1V8 38.9 mA, VCC_3V3 94.4 mA | same report, sheet "峰值电流" |
| RV1106 SoC, LinkNode idle (no camera, NPU, encoder) | VDD_0V9 190 mA, VCC_DDR 60 mA, VCC_1V8 20 mA, VCC_3V3 20 mA ≈ 0.35 W at the rails | **EST**, scaled down from the heavy case. **MEASURE** |
| ESP32-C5, 2.4 GHz | RX 87 mA; TX 313 mA peak (802.11b 19 dBm); deep sleep 12 µA | `esp32-c5-wroom-1_wroom-1u_datasheet_en.pdf` Table 6-4 p.33, Table 6-9 p.35 |
| HT-HC01 V2, listen 4 MHz | VBAT 32 mA + VDD_FEM 17 mA (LNA) | `Heltec_HT-HC01_V2.pdf` Table 3.2.4.2 p.13 |
| HT-HC01 V2, TX MCS0 27 dBm 1 MHz | VBAT 51 mA max + VDD_FEM 400 mA max | same, Table 3.2.4.1 p.12 |
| HT-HC01 V2, deep sleep | VBAT 1 µA typ | same, Table 3.2.4.3 p.14 |
| ATGM336H GPS | 26 mA at 3.3 V; peak 100 mA; backup 10 µA | `ZHONGKEWEI_ATGM336H-5NR32-G.pdf` p.8; peak from `ZHONGKEWEI_ATGM336H-5N.pdf` p.11 |
| Active GPS antenna | 10 mA | **EST** (depends on the antenna; the module limits it to 50 mA, p.11) |
| BQ25798, battery only | 17 µA typ, 24 µA max | `TI_BQ25798.pdf` IQ_BAT_ON p.9 |
| LM2903 (hold-off) | 0.4 mA typ, 1.0 mA max | `onsemi_LM393_LM2903.pdf` p.3 |
| TL432 bias (hold-off) | (VSYS − 1.25 V) / 10k ≈ 0.2 mA | R303 on the Hold-off sheet |
| TPS61089 | 100 µA into VOUT, 1 µA into VIN, no load | `TI_TPS61089.pdf` p.6 |
| TLV62569 | 35 µA not switching; 0.1 µA shut down | `TI_TLV62569.pdf` p.4 |
| Conversion | boost 90 %; bucks from 5 V: 78 % (0.88 V), 85 % (1.35/1.8 V), 90 % (3.3 V); GPS LDO 3.3/3.7 = 89 % | **EST** from the TPS61089/TLV62569 efficiency curves. **MEASURE** |

## Peaks and sizing checks

- **5 V bus worst case: 1.07 A.** That's HaLow TX (400 mA on VDD_FEM), C5 TX and HaLow VBAT through their bucks, plus Rockchip's heavy-IPC SoC peaks through theirs. The boost was sized for 1.8 A out at 3.0 V, with an R_ILIM of 180k giving a switch limit of at least 4.92 A (worklog, T6). Margin is fine.
- **Battery at 3.0 V: 2.0 A** (+0.1 A GPS peak).
  - BQ25798 BATFET: 6 A RMS (`TI_BQ25798.pdf` §8.3 p.8).
  - DW01A overcurrent trip: 4–9 A with 2× FS8205A (130–170 mV, `PUOLOP_DW01A.pdf` p.4; 18–32 mΩ path).
  - Both are above the peak.
- **VCC3V3_C5:** 313 mA peak on a 2 A TLV62569. **VCC3V3_HALOW:** 62 mA peak.
- **VDD_0V9:** 1.085 A measured peak (heavy IPC) on a 2 A TLV62569. Soft start 800 µs (`TI_TLV62569.pdf` tSS p.4), above the 100 µs minimum.

## Average power

| State | Power from the battery | Per day |
|---|---|---|
| SoC idle only (EST) | 0.47 W | 11.3 Wh |
| + HaLow listening (4 MHz) | +0.23 W | |
| + ESP32-C5 receiving (2.4 GHz) | +0.35 W | |
| + GPS tracking | +0.13 W | |
| **Everything listening** | **1.19 W** | **28.6 Wh** |
| Everything listening, GPS off | 1.06 W | 25.4 Wh |
| Node off (hold-off open) | 0.64 mA ≈ 2.4 mW | 0.06 Wh |

TX bursts come on top of these figures: HaLow TX costs about 2.2 W from the 5 V bus while it lasts. Count them per traffic pattern once firmware exists.

## What a handheld panel sustains

With 4 peak-sun hours, a 0.75 derate and 90 % charger efficiency (**EST**, location dependent):

| Panel | Harvest per day | Listening duty it can sustain |
|---|---|---|
| 2.0 W | 5.4 Wh | ≤ 19 % (4.5 h a day) |
| 3.5 W | 9.5 Wh | ≤ 33 % (7.9 h a day) |
| Listening 24 h a day | needs about 10.6 W | |

**Battery:** at 25 % duty the node uses about 7.2 Wh/day. Three days without sun needs about 21.5 Wh: **two 3.5 Ah 18650 cells** at 80 % usable (Q-5).

## Findings

1. **The node must duty-cycle hard (P-11, F-6).** Even the estimated SoC idle alone (0.47 W) is more than a 2 W panel delivers on average. Mesh nodes must share wake windows. The GPS supplies UTC to every node (N-8), so the windows can be scheduled on time without a radio handshake.
2. **The SoC idle figure is the biggest unknown.** Rockchip publishes only the heavy camera/NPU case. Measure VDD_0V9 and VCC_DDR on the first board, and test RV1106 suspend-to-RAM. A low-power SoC state between windows would move the duty limits more than anything else here.
3. **The ESP32-C5 receiver (0.35 W) is the largest radio listening load.** Keep it off outside the windows (C5_PWR_EN), or use its power-save modes.
4. **Power the GPS off between fixes** (GPS_PWR_EN). The XC6206 keeps its backup alive (10 µA), so it hot-starts.
5. **Two conversion stages** (boost to 5 V, then buck) cost about 20–28 % on the SoC rails. That's about 0.1 W against bucks running straight from VSYS. The 5 V bus was the owner's choice (2026-11-20); this is listed only as a power option if the budget gets tight.
6. **Off-state drain is negligible** (0.06 Wh/day). The LM2903 is most of it (0.4 mA); a micropower comparator would save little.

## Firmware requirements from the power design

- At boot: VAC_OVP = 26 V and IINDPM ≤ 3.3 A, the charger maximum (F-7; was 2.4 A with the barrel jack, raised with the T38 terminal block). Enable MPPT only for solar sources (`EN_MPPT = 0` at power-up; it can't be enabled while VBAT < VSYSMIN, `TI_BQ25798.pdf` §9.3.6.3 p.34).
- Service or disable the BQ25798 watchdog; it resets the registers when it expires (p.25).
- Keep VREG ≤ 4.2 V, below the DW01A overcharge trip of 4.25 V minimum.
- Turn the BQ25798 ADC off when it isn't needed, to keep IQ_BAT at 17 µA.
- Shut down cleanly at about 3.4 V (F-5), before the hold-off cuts at 3.32 V.
- Duty-cycle with GPS-timed wake windows (F-6), and switch each radio's rail off outside its window.
