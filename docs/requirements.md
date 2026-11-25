# LinkNode product requirements

(Renamed from Klepon, owner 2026-11-23, T48.)

Owner: Teapot Laboratories. Status: draft, 2026-11-20. Each requirement has an ID so that design notes, TODOs
and reviews can refer to it. **Source** says where the requirement came from. Anything not yet settled is listed
under [Open questions](#open-questions) and is not a requirement yet.

## 1. Product summary

LinkNode is an off-the-grid mesh network node. Nodes form one mesh across sub-GHz (Wi-Fi HaLow) and 2.4 GHz (ESP32-C5)
links, and each node knows its position and the time from a GPS receiver. Each node runs from a battery charged by
solar from a handheld-size panel, and it can be plugged into a laptop over USB-C, which gives the laptop network access to the mesh and also
charges the node.

## 2. Product goals

| ID | Requirement | Source |
|---|---|---|
| G-1 | One layer-2 mesh spanning sub-GHz (HaLow) and 2.4 GHz (ESP32-C5) links. | Owner, 2026-11-20; amended 2026-11-20 (ESP32 removed; C5 mesh on 2.4 GHz, Q-10) |
| G-2 | Works off the grid: no mains power, wired backhaul or internet needed. | Owner, 2026-11-20 |
| G-3 | **As cheap as possible.** Judge each part by unit cost first, then by power draw, because power drives the battery and panel cost. | Owner, 2026-11-20 |

## 3. Functional requirements

### Networking

| ID | Requirement | Source |
|---|---|---|
| N-1 | A HaLow (802.11ah) mesh link using 802.11s. | Owner, 2026-11-20 |
| N-2 | ~~A 2.4 GHz mesh link using 802.11s, on an original ESP32 running Ferris-on-Air (FoA).~~ **Removed**: the original ESP32 is replaced by a GPS receiver (N-8). | Owner, 2026-11-20; removed by owner 2026-11-20 |
| N-3 | A 2.4 GHz link on the ESP32-C5. The link protocol is ESP-NOW, because ESP-IDF has no 802.11s. (Was 5 GHz; owner chose 2.4 GHz, answer to Q-10.) | Owner, 2026-11-20; band changed by owner 2026-11-20 |
| N-4 | batman-adv on the main processor joins all links into one mesh (`bat0`) and picks the best link per hop. | Design decision, 2026-11-20 |
| N-5 | A laptop on USB-C sees a network interface (CDC-NCM, with RNDIS for Windows) bridged into the mesh. | Owner, 2026-11-20 |
| N-6 | The ESP32-C5 provides a hotspot that phones can join. | Design proposal, 2026-11-20 (owner has not confirmed) |
| N-7 | The main processor can reflash the ESP32-C5 in the field (UART, EN and boot pins wired to it). | Design decision, 2026-11-20 |
| N-8 | A GPS receiver gives the RV1106 the node's position and UTC time (NMEA over UART). It replaces the original ESP32. | Owner, 2026-11-20 |
| N-9 | The GPS time-pulse (1PPS) output goes to an RV1106 GPIO, so an off-grid node can keep accurate time with no internet (log timestamps, mesh time sync). Applies if the chosen module has a PPS pin. | Design proposal, 2026-11-20 (owner has not confirmed) |

### Power

| ID | Requirement | Source |
|---|---|---|
| P-1 | Runs from 1S Li-ion 18650 cells connected in parallel. | Owner, 2026-11-20 |
| P-2 | An on-board 1S battery protection IC with protection FETs. | Owner, 2026-11-20 |
| P-3 | Charges from a solar panel, with maximum-power-point tracking. | Owner, 2026-11-20 |
| P-4 | Charges from USB-C, including from a laptop's USB port. | Owner, 2026-11-20 |
| P-5 | Solar and USB-C can both be connected. The node selects between them without user action. | Design decision, 2026-11-20 |
| P-6 | Each radio (ESP32-C5, HaLow module, HaLow front-end) and the GPS can be powered off by software, to duty-cycle and save energy. | Design decision, 2026-11-20; GPS replaces the ESP32 2026-11-20 |
| P-7 | Supplies the worst-case peak with every radio transmitting at once. That was about 1.8 A on the 5 V bus with the ESP32 (see `docs/power-budget.md`); it must be recomputed without the ESP32 and with the GPS. | Design decision, 2026-11-20 |
| P-8 | **Cold start from solar.** With the node switched off and the battery at 0 %, sunlight on the panel alone makes the node start charging its battery. No user action, no USB and no running firmware are needed. | Owner, 2026-11-20 |
| P-9 | During a cold start (P-8) the system load stays off until the battery is charged enough, so the panel's power goes into the battery first and the RV1106 doesn't boot and brown out on a weak panel. **The node turns on at VBAT ≈ 3.6 V and off at ≈ 3.3 V** (owner, 2026-11-20). The 0.3 V gap covers the battery sag under TX peaks; the off threshold is also the low-battery cut-off that the BQ25798 lacks. Built as the Hold-off sheet: an LM2903 comparator with hysteresis switching VSYS → VSYS_SW (the boost input) through an AO3401A. Designed values: on 3.63 V, off 3.32 V, about ±2 % (TL432 ±0.5 % plus 1 % resistors). | Derived from P-8, 2026-11-20; thresholds by owner 2026-11-20 |
| P-11 | **The solar panel is external and the user's choice.** The node is not designed around one panel size. The amount of energy it gets only changes how long the radios can stay on (F-6). Handheld 6 V panels (about 1–3 W) are one supported option; options and prices are in `docs/solar-panels.md`. | Owner, 2026-11-20 (Q-5 answer, revised the same day: "the panel is external, it depends on the user") |
| P-13 | **USB bypass:** with USB-C power present (VBUS), the node switches on straight away even with a flat battery, so it always comes up on a laptop. The hold-off (P-9) applies only when USB is absent. USB supplies at least 2.5 W (a 500 mA SDP port) and the charger feeds the system before the battery. | Owner, 2026-11-20 (answer to Q-14) |
| P-12 | **The external DC input takes any DC source** (a solar panel of any size, a bench supply, a 12 V vehicle battery, a 24 V adapter) **up to the charger's maximum voltage: 3.6–24 V** (BQ25798 VBUS operating range, `TI_BQ25798.pdf` p.10). Input current is limited to **3.3 A** by firmware (IINDPM range 0.1–3.3 A, p.13; p.63), the charger's maximum. Was 2.4 A while the input was a 2.5 A barrel jack; since T38 (2026-11-23) the connector is an 8 A terminal block, and the path parts allow it (Q11 WST2319 6 A at 25 °C / 4.5 A at 100 °C, `Winsok_WST2319.pdf` p.1; Q3/Q4 SI2318A 4.3 A at 25 °C / 3.5 A at 70 °C, `UMW_SI2318A.pdf` p.1). The input survives transients up to the charger's 30 V absolute maximum on VAC2 (p.8), reverse polarity and hot plugging. MPPT applies only to solar sources. | Owner, 2026-11-20; limit raised with the T38 connector, owner 2026-11-23 |
| P-10 | Every charger default that a cold start relies on is checked against the BQ25798 datasheet and then measured on a board: input overvoltage limit, safety timers, input voltage regulation without MPPT. (Details under section 7.) | Derived from P-8, 2026-11-20 |

## 4. Hardware requirements

| ID | Requirement | Source |
|---|---|---|
| H-1 | Main processor: Rockchip **RV1106G3** (256 MB DDR3L), soldered directly to the board (no module). The owner confirmed the G3 over the cheaper G2. | Owner, 2026-11-20 |
| H-2 | HaLow radio: Heltec HT-HC01 V2 (Morse Micro MM6108), on the RV1106 SDIO bus. | Owner, 2026-11-20 |
| H-3 | Radio: one ESP32-C5 as an Espressif **module**, ESP32-C5-WROOM-1U, with a U.FL connector for an external antenna. The original ESP32 (ESP32-WROOM-32UE) is removed. | Owner, 2026-11-20; ESP32 removed by owner 2026-11-20 |
| H-13 | **External DC input:** the user plugs in from outside the enclosure through a board-edge **2-pin pluggable terminal block**: header Kefa KF2EDGR-3.81-2P (C441182, 3.81 mm, right angle, 300 V 8 A UL; `Kefa_KF2EDGR-3.81.pdf`) and screw plug KF2EDGK-3.81-2P (C440858, 300 V 8 A, AWG 28–16; `Kefa_KF2EDGK-3.81.pdf`) shipped loose with the board. Pin 1 = +, pin 2 = GND. Bare wires or a pigtail to a 5.5 × 2.1 plug (owner, 2026-11-23, T38; was a DC-005G-2.5A-2.0 barrel jack, C692446). Protection follows TI Fig 10-1 (`TI_BQ25798.pdf` p.130): a WST2319 −40 V P-FET for reverse polarity (BZT52C12 gate clamp, 100k), an SMAJ24A TVS (standoff 24 V, breakdown 26.7 V min, clamp 38.9 V at 10.3 A), and a 2R + 2.2 µF hot-plug snubber. SI2318A 40 V input FETs. A 294 Ω ACDRV resistor and a BZT52C10 gate–source zener on each input FET pair. Not sealed: outdoors it needs a cap or a sheltered face (Q-4). | Owner, 2026-11-20 (jack); rating from P-12 |
| H-12 | GPS: **ATGM336H-5NR32-G** (C49233943, $1.98; GPS + BDS + GLONASS, <26 mA at 3.3 V, 1PPS; `ZHONGKEWEI_ATGM336H-5NR32-G.pdf` p.2-9), u-blox MAX pad layout (KiCad `RF_GPS:ublox_MAX`). The ATGM336H-5N31 (C90770, $3.26, 9,518 in stock) has the same pinout and is the second source (`ZHONGKEWEI_ATGM336H-5N.pdf` p.10). It is powered by its own ME6211 3.3 V LDO from VSYS, switched by GPS_PWR_EN, with a 100k pull-down so it is off at boot. An XC6206 3.3 V LDO (1 µA quiescent) from the cell keeps the module's backup supply alive for ≤1 s hot starts (p.8-9). The **external active antenna** goes on a U.FL (Hirose C88374) and is fed from VCC_RF through 47 nH (p.10; owner, Q-11). | Owner ("a cheap GPS"), 2026-11-20; part chosen 2026-11-20 |
| H-9 | Charger: TI **BQ25798**, solar on VAC2 and USB-C on VAC1. The owner chose it over the cheaper CN3791 + TP4056 pair for dual-input switching, power path and telemetry. | Owner, 2026-11-20 |
| H-10 | Boot and storage: **boot from the microSD card only**. No on-board boot flash (no SPI NAND/NOR, no eMMC). The RV1106 BootRom supports SD/MMC boot (datasheet §1.2.2 p.8). The SD card sits on SDMMC0 (4-bit, SD 3.0), and the FSPI/eMMC pins stay free for other uses. | Owner, 2026-11-20 |
| H-11 | Interface allocation: HaLow on the single SDIO controller (SDMMC1); ESP32-C5 on SPI1; GPS on a UART, with 1PPS on a GPIO. SPI0 is no longer used, which also removes the SPI0_M0 / SDIO_M1 pin overlap on GPIO1_C. The RV1106 has 1 SD/MMC, 1 SDIO, 1 eMMC/FSPI and 2 SPI controllers (datasheet §1.2.2, §1.2.13). | Design decision, 2026-11-20; updated for the GPS 2026-11-20 |
| H-4 | HaLow band 902–928 MHz (27 dBm, 1/2/4/8 MHz channels). | Owner, 2026-11-20 |
| H-5 | A 4-layer PCB. | Owner, 2026-11-20 |
| H-6 | One USB-C port for both data and charging. | Owner, 2026-11-20 |
| H-7 | Source parts from LCSC (lcsc.com) wherever possible. Each BOM line has an LCSC part number; a non-LCSC part needs a stated reason. | Owner, 2026-11-20 |
| H-8 | Rail sequencing and ratings follow Rockchip's RV1106 hardware design guide and the Luckfox reference designs. Each regulator runs within its datasheet rating. | Owner, 2026-11-20 |
| H-14 | **SD/SDIO length matching is best effort** (owner, 2026-11-22). The microSD bus runs in SD 2.0 mode (VCCIO4 at 3.3 V, Rockchip HDG p.23) and the HaLow SDIO bus is SDIO 2.0 up to 50 MHz (`Heltec_HT-HC01_V2.pdf` p.17). At 50 MHz a 15 mm mismatch is ~0.1 ns of a 20 ns period, so the HDG’s 120 mil data-to-clock limit (HDG p.46, aimed at SD 3.0 UHS) is relaxed to a 12 mm spread per bus in `linknode.kicad_dru`. A future 1.8 V UHS microSD mode would need it tightened again. USB keeps the full HDG pair rules. | Owner, 2026-11-22 (T30) |
| H-15 | **USB-C CC sense:** R23/R24 (100k) from J1 CC1/CC2 to a node, R25 (100k) to GND, net `USB_CC_SENSE` to RV1106 pin 22 SARADC_IN1 (the only free ADC; SARADC_IN0 is the recovery input; RV1106G3 has 2 channels, 0–1.8 V 10-bit, HDG §2.3.8 p.36), with C508 100 nF at the pin. Node = (V_CC1+V_CC2)/3 ≤ 0.68 V for a 2.04 V CC; one CC faulted to 5.5 V gives 1.83 V through 100k (µA). Each Rd sees 5.1k ∥ 150k = 4.93k, inside 4.59–5.61k. | Owner, 2026-11-23 (T39) |
| H-16 | **microSD ESD protection** (owner, 2026-11-23; overrides the earlier no-ESD choice that followed the Luckfox Pico and the cost rule): 2× TPD4E05U06DQAR (DOWO, LCSC C22390021, $0.029; `DOWO_TPD4E05U06DQAR.pdf` p.2: C(I/O–GND) 0.5 pF max, VRWM 5.0 V; pin-compatible with TI TPD4E05U06 DQA) on SD_CLK, CMD, D0–D3 and the card-detect line (socket side of R402), one channel spare. Rockchip HDG §3.3.1 p.46: TF-card ESD under 1 pF, close to the connector. Cost +$0.058 per board plus one extended-part setup fee | Owner, 2026-11-23 (T42) |
| H-17 | **Expansion breakout on two 24-pin 0.5 mm FPC connectors** (owner, 2026-11-24, T55; replaces the T49/T50 pogo pads; JUSHUO AFC07-S24ECC-00, LCSC C11092, ×2, both on the bottom). **FPC A** (J1001, under the GPS, opening north), pin 1 west: 1 ETH TX+ · 2 TX− · 3 GND · 4 RX+ · 5 RX− · 6 GND · 7–8 3V3 · 9–12 SPI0 CS/CLK/MOSI/MISO · 13 GND · 14–15 I2C0 SDA/SCL · 16–17 I2C2 SDA/SCL · 18 GPIO1_C7 (84) · 19 GPIO1_B1 (78) · 20–22 GND · 23–24 VCC5V0_SYS; tabs GND. Ethernet raw from the FEPHY through 0R ×4 (HDG Table 2-11), 100 Ω diff, pin-to-contact skew 0 (HDG §3.3.2 < 30 mil); I2C 4.7k pull-ups to VCC_3V3. **FPC B** (J1002, under the microSD socket, opening south) **carries audio only** (owner, 2026-11-24: "Audio only on FPC B"; its GPIOs and arrays U1004/U1005 were dropped, so the board has 2 expansion GPIOs, both on FPC A). Pin 1 east: 1–2 GND · 3–4 VCC5V0_SYS · 5–9 GND · 10–11 VCC_3V3 · 12 GND · 13 MIC1+ · 14 MIC1− · 15 GND · 16 MIC0+ · 17 MIC0− · 18–20 GND · 21 MICBIAS · 22–23 GND · 24 LINEOUT; tabs GND. MIC lines through 1 µF series caps C1001–C1004 (HDG Table 2-12). ESD: 5× TPD4E05U06DQAR, flow-through (3 on FPC A, U1006/U1007 on FPC B). Recommend ≤ 0.5 A total on 3V3 + 5V. Users' cable: 24-pin 0.5 mm FFC (e.g. LCSC C20060). **Routing these nets is the lowest priority** (owner); FPC A and FPC B routed and installed 2026-11-24 (T55). | Owner, 2026-11-23/24 |

## 5. Regulatory

| ID | Requirement | Source |
|---|---|---|
| R-1 | The HaLow band and TX power must be legal in the deployment region. 902–928 MHz is the chosen band (H-4). The region still has to be confirmed. | Design note, 2026-11-20 |
| R-2 | The HaLow module must use its `bcf_mf08551.bin` board config file. Heltec warns that other files can cause abnormal RF output. | Heltec HT-HC01 V2 page |

## 6. Firmware requirements that come from the hardware

| ID | Requirement | Source |
|---|---|---|
| F-1 | Turn on the charger's solar MPPT at boot over I²C (BQ25798 `EN_MPPT`, which is off at power-up). | `TI_BQ25798.pdf` §9.3.6.3 |
| F-2 | Keep the battery charge voltage at or below 4.2 V, below the DW01A overcharge trip (4.25 V minimum). | `docs/power-budget.md` |
| F-3 | Service or disable the charger watchdog, otherwise it resets the charger's settings. | `TI_BQ25798.pdf` §9.3.2 |
| F-6 | Firmware adapts the radio and GPS duty cycle to the energy available: battery charge and input power from the BQ25798 ADC. With a large panel or a DC supply the node stays on; with a small panel it sleeps more. Wake windows use GPS time so neighbouring nodes wake together. | Owner, 2026-11-20 (panel is the user's choice; replaces Q-13) |
| F-7 | At boot, firmware checks VAC_OVP = 26 V (the POR default per Rev C p.72; written again in case a board shows the EVM guide's 7 V) and keeps IINDPM at or below 3.3 A, the charger's maximum (P-12; the input connector is rated 8 A since T38, H-13). | Derived from P-12, 2026-11-20; T17a |
| F-8 | Once booted, firmware owns the charger: it sets the charge timers (or disables them while it monitors the charge itself) and the charge current for the source. The no-firmware defaults (§7) only have to carry a cold start up to the 3.63 V boot threshold. | T17c, 2026-11-20 |
| F-5 | Firmware shuts the node down cleanly (sync the SD card, then ship mode) before VBAT reaches the 3.3 V hardware cut-off, for example at 3.4 V read from the BQ25798 ADC. The hardware cut-off is only a backstop. | Derived from P-9, 2026-11-20 |
| F-4 | Switching the node off uses the charger's ship mode: firmware sets SFET_PRESENT = 1 (REG14, POR 0; Rev C p.78) once at boot, then SDRV_CTRL = 10 to switch off. The ship FET Q13 (T25) isolates the cell from VBAT. A newly connected input (sun, USB, DC jack) or the PWR button (QON) ends it (Rev C §7.3.12.2 p.50). Never switch off by clearing EN_CHG or setting HIZ: a watchdog expiry keeps the EN_CHG setting (STOP_WD_CHG = 0 at POR, p.65), so the node could stay unable to charge (P-8). | Derived from P-8, 2026-11-20; restored with the ship FET (owner, Q-16, 2026-11-21) |
| F-9 | Firmware never sets the charge current (ICHG) above **2.5 A**: the battery connector J3 is a side-entry JST XH header (S2B-XH-A, C157931) rated 3 A with AWG 22 wire (`hardware/datasheets/JST_XH.pdf` p.1; owner chose XH for the battery and PH for the NTC, 2026-11-22, T33). The pack lead must be AWG 22. |
| F-10 | **USB-C current from CC:** with USB present, firmware reads `USB_CC_SENSE` on RV1106 SARADC_IN1 (H-15). The node is (V_CC1 + V_CC2)/3, so the active CC voltage is 3× the reading. If BC1.2 found only an SDP/unknown port, firmware raises IINDPM to 1.5 A when CC > 0.66 V and to 3.0 A when CC > 1.23 V (node 0.22 V / 0.41 V), and back to 500 mA below 0.66 V. Thresholds from TI TPS25751 (SLVSH93A) sink detection; the official Type-C spec tables are still to be checked. Never above the 3.3 A IINDPM limit. **Since T52 the charger's D+/D− reach the USB lines only through the 0 Ω links R26/R27, not fitted by default:** firmware then sets AUTO_INDET_EN = 0 (REG0x15 bit 6; POR is 1, `TI_BQ25798_RevC_2026.pdf` p.73) and takes the current limit from CC alone; the first plug-in before firmware runs does one detection on the open lines (TI states no behaviour for unconnected D+/D−; expected SDP 500 mA, unverified). If R26/R27 are fitted, BC1.2/HVDCP detection works as before and the RV1106 enables its USB only after BC1.2_DONE. | Owner, 2026-11-23 (T39; T52) |

F-1 to F-4 and F-7 come from the BQ25798 charger (H-9); F-5 from the hold-off (P-9); F-6 from P-11.

## 7. Known constraints and risks

- **ESP32-C5 has one radio**, so it can work on only one band at a time. It runs on 2.4 GHz (Q-10). The phone hotspot
  (N-6, if kept) shares that radio and channel with the mesh link.
- **The ESP32 and FoA are gone** (owner, 2026-11-20). LinkNode no longer depends on the experimental FoA 802.11s stack.
  The mesh now has two bands: HaLow and the C5's 2.4 GHz link.
- **Cold start (P-8 to P-10).** What the BQ25798 does on its own with no firmware (`TI_BQ25798.pdf`):
  - It charges without a host in "default mode" (§9.3.9.1 p.41, §9.4.1 p.55). Below 2.06–2.25 V it trickle-charges
    at 100 mA, then pre-charges at 120 mA up to 71.4 % of VREG, which is 3.0 V (p.12, Table 9-9 p.41, REG08 p.64).
  - The DW01A allows charging a cell from 0 V and keeps the discharge FET off until the cell reaches 2.9 V
    (`PUOLOP_DW01A.pdf` p.2 and p.4; the p.4 table text is partly garbled, so recheck it).
  - **Input overvoltage limit: resolved (T17a): the POR default is 26 V.** Rev B (`TI_BQ25798.pdf`, Jan 2023) contradicted
    itself: the REG10 field table said 7 V, but the register reset value 85h decodes to 26 V (p.72). Rev C
    (`TI_BQ25798_RevC_2026.pdf`, SLUSDV2C, Jun 2026, p.72) corrects the field table: VAC_OVP reset 0h = **26 V (default)**,
    consistent with 85h, and changes setting 1h from 22 V to 18 V (revision history p.142). Only a stale "POR: 11b" note
    remains. A TI engineer on E2E gives the same answer for the BQ25790, the sister part ("another datasheet typo... the
    default is 26V"). The EVM user's guide (SLUUCB5) still says 7 V, so T17d confirms it on a board. With 26 V, every P-12
    source (3.6–24 V) is accepted at power-up with no firmware.
  - **The system turns on at once.** With input present, SYS is held at VSYSMIN = 3.5 V even with a flat cell
    (p.25, p.39), and the VSYSMIN loop cuts the charge current to zero to keep SYS up under load (p.40). The
    TPS61089's EN is pulled up to its input (R18), so the 5 V rail and the RV1106 start straight away. P-9 needs a
    hardware hold-off.
  - **No MPPT without firmware.** MPPT is off at POR, and it can't be turned on while VBAT < VSYSMIN (p.34). The
    charger regulates the panel at its default VINDPM instead: VBUS0 − 0.7 V below 7 V, or VBUS0 − 1.4 V from 7 V up
    (p.27). For the handheld 6 V panel (P-11) that is about 6.3 V against a Vmp of about 6.0 V, close to the
    maximum power point even with no firmware.
  - **VAC_OVP and P-12 (resolved):** with the 26 V default, a 12 V panel, a 12 V battery or a 24 V adapter works from power-up, and a flat node can start from them (P-8).
  - **VAC_OVP and the 6 V panel (resolved):** a 6 V panel (Voc 7.0–8.5 V, about 8.5 V+ in the cold) is far below 26 V.
  - **Safety timers in default mode (T17c, analysis):** trickle 1 h (fixed, only below VBAT_SHORTZ 2.5 V), pre-charge 2 h at
    120 mA, fast charge 12 h at 1 A (Rev C Table 7-9 p.41, §7.3.9.2 p.42). All count at half rate while input current,
    input voltage or thermal regulation is active (TMR2X_EN = 1 at POR, p.44). That is normal on a weak panel, so they become
    2 h / 4 h / 24 h. When one expires, charging stops. The timers reset on a CE or EN_CHG toggle, a recharge, a change of
    charge phase, or a CHG_TMR write (p.44).
    - **Fast charge cannot be cut short in practice.** A day of sun is shorter than 24 h, and the node boots at 3.63 V
      (hold-off) and firmware then owns the timers (F-8).
    - **Pre-charge is the only risk.** It covers cells resting below VBAT_LOWV (3.0 V): only cells that have self-discharged
      for months, since a DW01A cut-off at 2.4–2.5 V relaxes back to about 3 V. Two 3.5 Ah cells may need roughly
      140–350 mAh to get from 2.5 V to 3.0 V (**EST**, 2–5 % of capacity). That is 1.2–2.9 h at 120 mA, so a 2 h timer can
      expire in good sun.
    - **What restarts it:** a full POR. Overnight a flat bank cannot keep the charger alive, so it restarts each dawn. That
      gives at least 2–4 h of pre-charge (240–480 mAh) per day, and the bank still reaches 3.0 V within one or two days. Not
      fatal for P-8, but slower.
    - **Unconfirmed:** whether a dawn re-plug restarts the timers while the battery still powers the charger. The datasheet
      doesn't say (T17d bench test).
  - **Poor-source qualification:** after REGN starts, the charger checks the source can deliver current without sagging
    below VPOORSRC. A weak dawn panel that fails is retried every 7 minutes (Rev C §7.3.4.2 p.26–27). This only delays a
    cold start.
  - **Ship mode needs an external ship FET (T17, found 2026-11-20).** Rev B said ship mode turns off "BATFET and external
    ship FET" (p.50). Rev C deleted the BATFET (revision history p.142; §7.3.12.2 p.50 now says only "the external ship
    FET"). LinkNode has none: SDRV has only C22 1 nF to GND, which is what the pin table calls for when no ship FET is used
    (Rev C p.5).
    - Consequences: ship mode, shutdown mode and the QON "system power reset" do nothing on this board. F-4 does not work
      as written, and SW1 (PWR, on QON) has nothing to switch.
    - Decision Q-16: add the ship FET (owner, 2026-11-21). Drawn as Q13 (T25).
- **Energy from a handheld panel (P-11).** Using the budget's own assumptions (4 peak-sun hours, 75 % harvest,
  **EST**): a 1.3 W panel gives about 3.9 Wh a day (**0.16 W** average); the 3 W 145 × 145 mm panel gives about 9 Wh
  (**0.375 W**); a 5 W panel about 15 Wh (**0.62 W**). The always-listening node needs about 1.8 W (next bullet). So a handheld panel
  can sustain the node only if it sleeps most of the time, roughly 10–20 % awake, or if it runs down the battery
  on cloudy days. Owner decision needed: Q-13.
- **Power budget:** with every radio always listening, the node drew about 2.1 W, roughly 50 Wh a day. That means
  about four 18650 cells for one day without sun and a panel of about 17 W. Swapping the ESP32 (0.37 W in RX) for
  the GPS (about 26 mA at 3.3 V, 0.09 W, from the LCSC catalog listing, unverified) brings this down to about
  1.8 W before conversion losses are recomputed. Duty-cycling the radios and the GPS (P-6) is the main lever for
  reducing both. All figures are estimates until measured (`docs/power-budget.md`, to be updated).
- **RV1106 availability and price** (LCSC product API, 2026-11-20 04:40 UTC):
  - RV1106G3 (C5328706): 1,933 in stock, $23.87 at qty 1, $21.14 at qty 30.
  - RV1106G2 (C5272606): 582 in stock, $13.68 at qty 1, $10.90 at qty 100.

  The G3 is the most expensive part on the board.

## Open questions

| ID | Question |
|---|---|
| Q-4 | ~~Board size and enclosure~~ answered (owner, 2026-11-21): the **smallest single-sided board**, about 80 × 90 mm, all parts on the top side, 4 mounting holes. USB-C, DC jack, microSD and PWR button on one edge; the U.FL feeds go to the enclosure on pigtails. The enclosure and its weather rating are still to choose. **Amended (owner, 2026-11-21):** bottom-side assembly is allowed, so the RV1106 decoupling can sit under the chip (HDG “close to the chip pins”). **Amended again (owner, 2026-11-22):** re-pack the whole board as tight as possible while staying routable, shrink the outline to the smallest that passes, and allow 0402/0603 passives on the bottom side everywhere (modules, connectors, inductors, crystals and ICs stay on top). Connector edge, 4 mounting holes and U.FL pigtails unchanged. **Floorplan approved (owner, 2026-11-23, T40, layout B6):** 76 × 60 mm, power **Edge margin (owner, 2026-11-23, T44):** grown to 78 × 62 mm (top and right edges +2.0 mm) so parts sit ≥ 2.5 mm from those edges (ESP32-C5 2.5 mm, top parts ≥ 2.85 mm); corner holes moved with the edges. | RV1106 | radios from left to right; HaLow (rot 180) above the RV1106 with its RF filter running up to the U.FL; GPS (rot 90) and ESP32-C5 (rot 180) centred in the right column; DC in, PWR, USB-C, microSD on the bottom edge; battery/NTC on the left edge; holes in the corners. |
| Q-5 | Panel: the user's choice (P-11). Still open: how many 18650 cells the enclosure and battery connector (J3, JST XH 2-pin side entry, 3 A; T33/T34) are designed for (the cells are also user-fitted). Power budget (T19, 2026-11-20): at 25 % listening duty the node uses about 7.2 Wh/day, so three sunless days need about 21.5 Wh: **two 3.5 Ah 18650 cells** (80 % usable). Owner to confirm. **Cells are off-board on wires through J3** (owner, 2026-11-21), so the count is a build choice; two 3.5 Ah cells meet the 3-day target. **Battery NTC at the pack** (owner, 2026-11-21, T27): a leaded MF52A103F3435 (C84036) taped to the cells, wired to J4 (TS, GND). The pack wiring is J3 (VCELL, CELL_N) plus J4 (NTC); the NTC returns to board GND, never CELL_N. |
| Q-6 | Which external antennas (and connectors at the enclosure) for HaLow (900 MHz), the ESP32-C5 (2.4 GHz) and the GPS (active, L1)? All three are external on U.FL. |
| Q-7 | Deployment region (affects R-1). |
| Q-8 | Phone hotspot on the ESP32-C5 (N-6): confirm or drop. It would share the C5's 2.4 GHz radio and channel with the mesh link, and it costs power (Q-13). |
| Q-9 | DW01A pin 4 (TD, "test pin for reduce delay time", `PUOLOP_DW01A.pdf` p.2): leave unconnected (current design, as KiCad's library marks it) or tie to GND? The app circuit (p.3) shows no external connection. |
| Q-10 | ~~ESP32-C5 band~~ answered: **2.4 GHz** (owner, 2026-11-20). See N-3 and Q-12. |
| Q-11 | ~~GPS antenna~~ answered: **external** active antenna on U.FL (owner, 2026-11-20). See H-12. |
| Q-12 | ~~ESP32-C5 or a cheaper 2.4 GHz module?~~ Answered: **keep the ESP32-C5-WROOM-1U** (owner, 2026-11-20). The C6-MINI-1U was $1.24 cheaper at qty 1. |
| Q-14 | ~~Should USB power bypass the hold-off?~~ Answered: **yes** (owner, 2026-11-20); see P-13. |
| Q-15 | **Operating temperature range** for an outdoor node? The RV1106 is rated −20 to 85 °C ambient (`Rockchip_RV1106_Datasheet_V2.2-20260602.pdf` p.27; V1.3 said 0 to 80 °C). Li-ion cells must not charge below 0 °C (the charger's TS input handles this). Freezing climates need a check of the enclosure and the cells. | Open (raised 2026-11-20, T11) |
| Q-16 | ~~Add an external ship FET on SDRV?~~ Answered: **yes, add it** (owner, 2026-11-21). F-4 is restored once it's drawn (T25). |
| Q-13 | ~~Answered~~ by the owner: the panel is the user's choice, so firmware adapts (F-6). Original question: a handheld panel supports only about 0.16–0.4 W on average, against about 1.8 W always listening. Is a node that sleeps most of the time and wakes on a schedule acceptable, or should the panel be bigger? This decides the power-management design, the firmware and the cell count (Q-5). |
