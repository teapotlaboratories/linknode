# 2026-11-20 — PCB kickoff

## Decisions
- Architecture: RV1106 + HT-HC01 V2 (HaLow, 802.11s on SDIO) + original ESP32 (FoA 802.11s, 2.4 GHz) + ESP32-C5 (ESP-NOW, 5 GHz), joined by batman-adv. See project rules.
- Start from the PCB design (owner).
- Project rules adapted from the BWLC1A project rules.

## Findings
- HT-HC01 V2 (https://heltec.org/project/ht-hc01-v2-wifi-halow-module): MM6108 + FEM, SDIO 2.0 / SPI, VDD 3.0–3.6 V, VDDIO 1.62–3.6 V, VFEM 5 V, 27 dBm @ 915 MHz, 38-pin 1.27 mm stamp hole, 18.5 × 14 × 2.6 mm. No current figures and no datasheet linked.
- FoA (https://github.com/esp32-open-mac/FoA): only esp32/esp32s2 chip features. `foa_mesh` branch is 11 commits ahead of main and does WIP mesh peering (MPM).
- KiCad 10.0.8 stock libraries contain BQ25798, BQ27441, ESP32-WROOM-32E/UE and USBLC6, but not the ESP32-C5, the RV1106 or the HT-HC01.
- Luckfox Core1106 SoM: RV1106G2 (128 MB) or G3 (256 MB), 30 × 30 mm, 112 castellated pins, exposes USB, SDIO, SPI, UART, I2C and Ethernet (https://www.cnx-software.com/2025/01/21/solderable-rockchip-rv1106-system-on-module-features-112-castellated-pins-offers-wifi-6-and-bluetooth-5-2-connectivity/). Not verified against the official pinout yet.

## Next
- T1: get the owner's board-level decisions.

## Owner decisions (T1)
- RV1106 chip-down, not the Core1106 SoM.
- Battery: 1S Li-ion 18650 cells in parallel.
- HaLow: 902–928 MHz.
- 4-layer board.
- Still open: board size and enclosure, number of cells.

## Next
- T2: collect the RV1106 datasheet and hardware guide, plus the Luckfox Pico (RV1106) schematics, as the chip-down reference.

## T2 progress: RV1106 chip-down references
- Downloaded into `hardware/datasheets/`:
  - `Rockchip_RV1106_Datasheet_V2.2-20260602.pdf`
  - `Luckfox-Pico-Pro-Max.pdf`
  - `Core1106.pdf`
  - `Rockchip_RV1106_User_Manual_GPIO.pdf`

  Source: github.com/LuckfoxTECH/Luckfox-Pico-docs.
- RV1106G2/G3 is QFN128, with DDR3L in the package (1Gb on G2, 2Gb on G3), MSL3 (datasheet §2.1, §2.4, p.16/21).
- Recommended operating conditions (datasheet Table 3-2, p.26–27):

  | Rail | Min | Typ | Max |
  |---|---|---|---|
  | CPU_DVDD | 0.85 V | 0.90 V | 1.05 V |
  | DVDD and PMU_DVDD0V9 | 0.81 V | 0.90 V | 0.95 V |
  | DDR3L VDDQ | 1.283 V | 1.35 V | 1.45 V |
  | 1.8 V analog | 1.62 V | 1.8 V | 1.98 V |
  | GPIO1/PMU 3.3 V | 3.0 V | 3.3 V | 3.465 V |
  | RTC_AVDD3V3 | 1.6 V | — | 3.6 V |

  Ambient temperature range: −20 to 85 °C.
- Core1106 power tree (`Core1106.pdf` p.1, power block). All of it runs from VCC5V0_SYS:
  - EA3036C (U1) triple buck:
    - LX1 → VCC_3V3: 40.2k/9.1k, FB 0.6 V
    - LX2 → VDD_0V9: 47k/100k, noted "max 1.6A Ip". VDD_ARM is tied to it through R10 (0R).
    - LX3 → VCC_1V8: 200k/100k
  - MP1605GTF-Z (U5) → VCC_DDR: 127k/100k, FB 0.6 V, so about 1.36 V.
  - Sequencing uses RC delays on EN1/EN2/EN3 (200K/100nF, 10K/NC, 100K/100nF). EN3 also drives the DDR regulator's EN (`VCC_DDR_1V8_EN`).
- Luckfox Pico Max (`Luckfox-Pico-Pro-Max.pdf`) has the same rails, built from discrete bucks (U4 0V9, U5 1V8, U7 VCC_DDR, U6 3V3 with PWR_EN).
- EA3036C: search results say VIN is 2.7–5.5 V with three 1 A bucks (unverified). The xonlink PDF download was broken (XML, not PDF), so the official datasheet is still needed.
- Problem: on a 1S battery (3.0–4.2 V), a buck can't hold 3.3 V once the cell drops below about 3.4 V. Either the 3V3 rail needs a buck-boost, or the system runs from a 5 V boosted bus as the reference does.

## Owner decision: power tree
- 5 V system bus (charger SYS → boost → VCC5V0_SYS → Core1106 tree unchanged; the same 5 V feeds the HaLow VFEM). Added as T6.
- Still missing datasheets: BQ25798, 5 V boost candidate, EA3036C (official), MP1605GTF-Z, ESP32-WROOM-32E, ESP32-C5 module, HT-HC01 V2 pin map.

## Owner resources
- The owner supplied `resource.zip`. It is extracted to `resources/resource/` without `__MACOSX`, and the zip was deleted at the owner's request.
- Removed at the owner's request:
  - `.DS_Store` and `._*` files
  - `OSD62-PM-BRK-3.zip`
  - `v3s_documentation/`
  - `projects/` (all five projects were Allwinner V3s based)
- Key files for the PCB work:
  - `Rockchip-RV1103G-RV1106G-Hardware-Design-Guide-en-V1-1-20221221.pdf`
  - `images/rv1106_power_sequence.png`
  - `rv1103_rv1106/Rockchip_RV1106G_Power_Consumption_Test_Report_V1.2_20220622.xlsx`
  - `bq25798.pdf`
  - `board_reference/RV1106G-AI-IPC-V13-20231110LX.pdf`
  - `6979051.pdf`: Quectel FGH100M (a HaLow module) hardware design guide, useful as HaLow layout reference

## T6/T3: power design, solar + USB-C (owner: "also support solar charger")
- BQ25798 typical application, Fig 10-1 p.130:
  - Adapter on VAC1 with D+/D−; PV panel on VAC2. Each sits behind back-to-back ACFET/RBFET pairs driven by ACDRV1/2 (§9.3.5.4 p.31–33).
  - VAC1 has priority when both inputs appear at once.
  - PROG pin: 3.0 kΩ selects 1s at 1.5 MHz (use a 1 µH inductor); 4.7 kΩ selects 1s at 750 kHz (2.2 µH) (Table 9-1 p.25).
  - ILIM_HIZ divider 127k/100k from REGN; TS divider 5.24k/30.31k with a 103AT 10k NTC; BATP through 100 Ω (Fig 10-1).
- MPPT is off at POR and must be enabled by a host (§9.3.6.3 p.34). This is a firmware requirement.
- 5 V bus: TPS61230A, 2.5–4.5 V in, 5 V at 2.4 A (§8.1 p.12). SYS ≤ VREG 4.2 V, so it stays in range.
- New radio rail VCC3V3_RF: TLV62569 (2 A), feeding per-radio TPS22918 load switches (2 A, 1–5.5 V). A further switch gates HT-HC01 VDD_FEM.
- HT-HC01 V2 datasheet downloaded (`Heltec_HT-HC01_V2.pdf`, Dec 2025):
  - VDD_FEM 3.0–5.25 V; 400 mA max at 27 dBm (Table 3.2.4.1 p.12).
  - VBAT abs max 4.3 V.
  - Pin table p.7–9; SPI/SDIO reference designs p.15–16.
- EA3036 Ver 1.1 datasheet (non-C) in hand: 2 A continuous per channel, 6 W total. The EA3036C datasheet is still missing; the LCSC and xonlink links are dead.
- The power budget (`docs/power-budget.md`) estimates about 2.1 W average while always listening, which is about 50 Wh/day. That means roughly four 18650 cells and a panel of about 17 W. The earlier 1.2–1.5 W estimate was too low.

## Owner decision: 0V9 rail
- EA3036C Ver 1.4 (`hardware/datasheets/Everanalog_EA3036C.pdf`, from the KiCad library's datasheet link): 1 A continuous per channel (p.1). PMOS current limit 1.8–2.2 A (p.5). Peak load 1.5 A at ≤ 1.8 V and 1.2 A at 3.3 V, for Vin = 5 V and L = 1.5 µH (p.11).
- Core1106 puts VDD_0V9 and VDD_ARM on one EA3036C channel, which is over its rating against Rockchip's 1.6 A + 0.5 A peaks.
- Owner chose a separate 2 A TLV62569 for VDD_0V9/VDD_ARM. EA3036C: CH1 VCC_3V3, CH2 VCC_DDR, CH3 VCC_1V8. The MP1605 is dropped.
- Boost: TPS61230A (2.4 A, needs a custom symbol) rather than the stock-library TPS61230 (VSON-10, 2.1 A at 3.3 V input, `TI_TPS6123x.pdf` p.1), for headroom over the 1.8 A worst case.
- Load switches: TPS22917DBV (stock symbol; 2 A, 1–5.5 V, reverse-current blocking; `TI_TPS22917.pdf` p.1) in place of the TPS22918.
- T4 done: the KiCad project `hardware/kicad/klepon.kicad_pro` has six sub-sheets (power, soc, halow, esp32, esp32c5, usb_io). kicad-cli ERC: 0 violations.

## KiCad setup mirrors BWLC1A (owner request)
- Read `~/Developments/bwlc1a/bwlc1a/hardware/kicad`. It uses A4 sheets, one function each, with a title block per sheet. Cross-sheet links are hierarchical labels; rails are power symbols; passives are R_Small/C_Small; test points are used freely. It has a single project library (`.kicad_sym` + `.pretty` + `3dmodels`), Default/Power net classes and relaxed ERC severities.
- Klepon rebuilt to match (all sub-sheets were still empty, so I checked them and deleted them):
  - Root has 9 A4 sheets: SoC, USB and Charger, Battery, Power, Radio Power, HaLow, ESP32, ESP32-C5, Antenna.
  - Title blocks added. `fp-lib-table` and `library/klepon.pretty`, `library/3dmodels` and `production/` created.
  - `net_settings` (patterns adapted to Klepon rails), board `design_settings` and ERC severities copied from `tracker-c0.kicad_pro`.
- Tools: the sheets were created with the scripting server (`create_hierarchical_subsheet`). After `close_project`, the root reset, title blocks, sheet-box shift and `.kicad_pro` merge were done with Python text and JSON edits. `kicad-cli sch erc`: 0 violations.
- Custom symbols so far, in `library/klepon.kicad_sym`: TPS61230A (SLVSCZ5B p.3) and CSD87503Q3E (SLPS661 p.1). Footprints for both are still to make (T5).
- Open: the title-block company field. BWLC1A uses "Teapot Laboratories"; I left it blank for Klepon pending the owner.

## Owner answers
- Title-block company is "Teapot Laboratories". Added to all 10 sheets with a Python text edit; ERC re-run.
- Add an on-board 1S battery protection IC.
- Use LCSC parts where possible. Each BOM line gets an LCSC `Cxxxxx` number. Rule added to project rules.

## Requirements doc
- Owner asked for a requirements doc. Wrote `docs/requirements.md`: goals, networking, power, hardware, regulatory and firmware requirements, plus open questions Q-1 to Q-8. New owner requirement G-3: as cheap as possible.
- Cost check (LCSC in-stock snapshot 2026-11-19):
  - BQ25798 C2876593 $2.91. TPS61230A only 5 in stock; TPS61089 C165129 $0.72 (10.5k); SY7088 C178240 $0.40.
  - CSD87503Q3E only 10 in stock; AO3400A C20917 is a Basic part.
  - TLV62569DBV C141836 $0.07. TPS22917 $0.37. EA3036C $0.29.
  - DW01A C351410 $0.05; FS8205A C2830320 $0.05.
  - CN3791 C154992 $0.50; TP4056 C725790 $0.085.
  - ESP32-WROOM-32UE-N4 C701344 $4.01; ESP32-C5-WROOM-1U-N8R8 C54951858 $5.58. These are the only C5 module variants in stock, both U.FL.
  - RV1106G2 and G3 are not in the in-stock snapshot. The LCSC product pages (C5272606, C5328706) load but don't render stock.
  - Prices are qty-1 from the catalog snapshot.

## Cost and LCSC pass (G-3)
- Owner decisions:
  - Keep the BQ25798 (not CN3791 + TP4056).
  - Processor is the RV1106G3.
  - ESP modules: ESP32-WROOM-32UE-N4 (C701344) and ESP32-C5-WROOM-1U-N8R8 (C54951858), both U.FL.
- Boost changed from TPS61230A (5 in stock) to TPS61089RNRR (C165129, $0.72, 10.5k in stock, stock KiCad symbol). Its 7 A switch carries the 1.8 A at 5 V peak.
- SY7088 ($0.40) rejected: 3 A peak switch limit, efficiency curve only to 1.6 A at 3.3 V input (`Silergy_SY7088.pdf` p.1, scanned app note).
- BQ25798 input FETs: 4× AO3400A (C20917, LCSC Basic, 30 V), two back-to-back common-source per input. They replace the CSD87503Q3E (10 in stock).
- The TPS61230A and CSD87503Q3E custom symbols were deleted from `library/klepon.kicad_sym` with the scripting server `delete_symbol`.
- Battery protection: DW01A + 2× FS8205A in parallel. Trip-point maths is in `docs/power-budget.md`.
- Proposal awaiting the owner: replace the EA3036C and TPS22917 switches with one TLV62569 per rail and per radio. About $1.3 saved per board.

## RV1106 stock (owner: use the LCSC website)
- LCSC product API `wmsc.lcsc.com/ftps/wm/product/detail?productCode=` (the web page renders stock with JavaScript, so the JSON endpoint was queried directly), 2026-11-20 04:40 UTC:
  - RV1106G3 C5328706: 1,933 in stock, $23.87 at qty 1, $21.14 at qty 30, QFN-128 tray of 152.
  - RV1106G2 C5272606: 582 in stock, $13.68 at qty 1, $13.03 at 10, $11.89 at 30, $10.90 at 100.
- The local JLCPCB in-stock snapshot left both out, so it is not reliable for every LCSC part. For key parts, check the LCSC API.

## T7: USB and Charger sheet drawn
- Owner approved the TLV62569 consolidation, which drops the EA3036C and the TPS22917 switches. Still pending: the owner's "yes" did not say whether to keep the RV1106G3 or switch to the G2 to save about $10.
- How it was built: scripting server `batch_add_components` placed 49 parts, 58 power symbols and 4 PWR_FLAGs; `batch_connect` placed 71 local labels; `add_schematic_net_label` placed 6 hierarchical labels; `batch_add_no_connects` handled SBU1/SBU2; `batch_edit_schematic_components` set 44 LCSC fields; `add_sheet_pin` added 6 root sheet pins.
- Power-symbol and label positions come from a script (`symlib.py` + `gen.py` in the scratch) that computes pin endpoints from the KiCad libraries; spot-checked against scripting server `get_schematic_pin_locations`.
- Fallback (Python text edit, scripting server has no tool for it): `tidy.py` hides #PWR references, sets power symbols to in_bom/on_board no, and places Ref/Value fields beside each passive. The first build had 7.62 mm spacing with overlapping values; the sheet was reset (backup in the scratch) and rebuilt at 12.7 mm.
- Verified:
  - Netlist exported by kicad-cli has 36 nets and is identical before and after the LCSC edit. Every BQ25798 connection matches Fig 10-1, plus ILIM_HIZ tied to REGN (pin description: "Connect ILIM_HIZ to REGN to set the maximum input current limit"), PROG 4.7 kΩ (1s at 750 kHz, Table 9-1), SDRV 1 nF to GND (no ship FET).
  - All 15 footprints exist in the KiCad 10 libraries.
- ERC: 10 left, all cross-sheet: sheet pins not yet wired on the root, VCC_3V3 not driven until the Power sheet exists, I2C not yet driven.
- Design notes:
  - D1 SS34 adds solar reverse-polarity protection, at the cost of about 0.4–0.55 V loss.
  - The 2R + 2.2 µF snubber on VSOLAR follows Fig 10-1 note 1 (hot plug above 15 V).
  - TS divider 5.23k/30.1k is the nearest E96 pair to 5.24k/30.31k. The 103AT NTC goes on the Battery sheet through hierarchical label TS.

## Design report
- Published HTML report `docs/reports/rev1-design/`. Contents: architecture and power-tree diagrams (mermaid), planned power-up timing, power budget chart, sheet status, the USB and Charger sheet SVG, cost so far, open questions. Source copied to `docs/reports/rev1-design/`.

## Owner decision: boot from SD card only
- No on-board boot flash (no SPI NAND/NOR, no eMMC). The RV1106 boots from microSD on SDMMC0. Recorded as H-10 in requirements and in project rules.
- Interface check (datasheet V2.2 §1.2.2 p.8, §1.2.13 p.14): 1× SD/MMC, 1× SDIO (M0/M1 are pin options for one controller), 1× eMMC sharing pins with FSPI, 2× SPI with 2 CS each. HaLow → SDIO; ESP32 → SPI0/SPI1; SD → SDMMC0. Recorded as H-11.
- With no flash, the FSPI/eMMC pins on GPIO4 are free. SPI1_M0 (on the EMMC_D4–D7 pins) can be used without conflict. The SDIO_M1 / SPI0_M0 overlap on GPIO1_C still has to be resolved on the SoC sheet.

## RV1106 pin map (draft)
- `docs/rv1106-pinmap.md` is generated from the Rockchip pin-out xlsx (sheet 06).
- Key finding: SPI0 exists only as _M0 (GPIO1_C0–C3), on the same pins as SDIO_M1. So HaLow uses SDIO_M0 (GPIO2_A, VCCIO5), the ESP32 uses SPI0_M0 (GPIO1_C, VCCIO6), and the C5 uses SPI1_M0 (GPIO4_A, on the EMMC_D4–D7 pins, free because there is no flash).
- The SD card is on SDMMC (GPIO3_A, VCCIO4 fixed at 3.3 V). DET low selects SD mode (guide §2.1.4). Boot order is SFC, then eMMC, then SDMMC (§2.1.3).
- Per the guide (Tables 2-7 and 2-8): 22 Ω series on SDMMC_CLK and SDIO_CLK. The RV1106's internal SDIO pulls are pull-downs, so the Heltec-required SDIO pull-ups are external.
- ESP strapping: ESP32 GPIO0 low = download (Table 6). C5 GPIO28 low with GPIO27 high = download (Table 4-3). BOOT and EN are open drain with 10k pull-ups.
- ESP32 VSPI IO_MUX: CS0 GPIO5, CLK 18, MOSI (D) 23, MISO (Q) 19 (`esp32_datasheet_en.pdf` p.15).
- Report v3 has a connections section with a diagram and the pin table.

## T8–T10: Battery, Power and Radio Power sheets drawn
- **Battery:** J3 KF301-5.0-2P; U3 DW01A with R11 100 Ω, C23 100 nF, R12 1 kΩ (PUOLOP typical app p.3); Q5/Q6 FS8205A in parallel; TH1 CMFA 103F3435 NTC on TS.
  - New custom symbol `klepon:FS8205A` (pins from the FUXINSEMI marking drawing p.1).
  - ERC warning: the KiCad DW01A symbol marks TD as no-connect, but PUOLOP's app circuit ties TD to cell negative. Kept as drawn; warning accepted.
- **Power:** U4 TPS61089. Calculations (TPS61089 SLVSD38C):
  - R_FSW = 4·(1/f − 86 ns·Vout/Vin)/24 pF = 313k at 500 kHz, Vin 3.6 V → 316k.
  - Inductor peak 4.1 A (eq. 6–8, L −30 %, Vin 3.0 V, 1.8 A out). R_ILIM 180k gives 5.72 A typical, 4.92 A minimum (eq. 4, −0.8 A worst case).
  - FB 316k/100k with VREF 1.212 V → 5.04 V.
  - Compensation (eq. 17–19, fc 10 kHz, Co 40 µF effective, RHPZ 58.6 kHz): R5 8.06k, C5 6.8 nF, C6 22 pF.
  - L2 FHD4020S-2R2MT (4.8 A rated / 7.5 A saturation) on the FNR4020S footprint, pads still to check (T15).
  - TLV62569 ×4 values follow eq. 2 p.9: 6.8 pF feed-forward with a 100k lower resistor, 2.2 µH + 10 µF (Table 4), 4.7 µF input (Table 3).
- **Radio Power:** three TLV62569 at 3.32 V with GPIO enables and 100k pull-downs. VDD_FEM switch: AO3401A, 100k/10 nF gate RC, 2N7002 driver, 22 µF + 100 nF on VDD_FEM.
- BOM cost of the four drawn sheets: $7.98 (LCSC qty 1).
- The generator scripts are now kept in `hardware/tools/schgen/` (pin maths, labels, tidy, netlist dump, LCSC lookup).
- Design report published as v4 with the power sheets added.
- Next: T11 SoC sheet, which needs a 128-pin RV1106 symbol and QFN-128 footprint generated from the Rockchip pin-out xlsx.

## T16: sheets converted from net labels to wires (owner: "wire it, make it tidy, no overlapping text")
- **Battery, Power, Radio Power** rebuilt with wires from the generator plans (`hardware/tools/schgen/`). **USB and Charger** was rebuilt last, from `build_usb2.py`, with a new layout:
  - VBUS is raised above the CC resistors, and R1/R2 are staggered.
  - USBLC6 (U1) is drawn flow-through.
  - The solar FET row is moved down so the FET texts clear the ACDRV wires.
  - The left control pins each get their own column, with upper pins further left, so no part sits across another pin's wire.
  - The TS divider sits under the chip, and REGN loops under the chip to ILIM_HIZ, C13 and R7.
  - Cap rows are at 15.24 mm pitch.
- **Tools.** Scripting server: part placement, hierarchical labels, LCSC fields, no-connects, the DW01A lib_id swap and cache refresh, Battery TD wire deletion. Scripts, as the fallback: wires and junctions (`applywires.py`, `fixjunctions.py`), field placement (`fieldplace.py`, `setfield.py`), moving symbols for re-spacing (`movesyms.py`; the scripting server has no batch move for schematics, and its single move drops junctions).
- **R10 was missed in the first USB plan.** It is the 10k pull-up from VCC_3V3 to ~INT/CHG_INT and was caught by the netlist comparison. It is now on the sheet (C25744).
- **USBLC6 flow-through.** D+ and D− now enter on I/O pins 3 and 1 and leave on pins 4 and 6, so each line is two nets joined inside the part. Both datasheets show pins 1–6 and 3–4 joined internally: ST `ST_USBLC6-2.pdf` p.1 Fig 1 and p.5 Fig 7 ("optimized layout" passes the track straight through); TechPublic `TECHPUBLIC_USBLC6-2SC6.pdf` p.1, which is the part on the BOM (C2827654). This is the only intended netlist change.
- **Mirrored-symbol footgun.** KiCad rotates a symbol first and then mirrors it in sheet space. The helpers mirrored first, which gives the same result at rotation 180 but not at 90/270. Q2/Q4 came out floating until it was fixed. `symlib.endpoint`, `fixjunctions.xf` and `fieldplace.xf` now rotate, then mirror.
- **Field-text footgun.** A field angle is relative to the symbol. For a power symbol at rotation 90, field angle 90 with `justify right` draws the text to the right. At rotation 270, `justify left` does. KiCad uses the last `(justify)` it reads, so `setfield.py` strips every old `justify` before writing.
- **The Power sheet file uses a different whitespace layout** (written by the scripting server swig backend). The first `movesyms.py` failed on it, and `applywires.py` then stacked duplicate wires. The sheet was restored from backup. `movesyms.py` and `setfield.py` now find blocks by paren matching (`sexpblk.py`), and `movesyms.py` aborts before writing if any symbol is missing.
- **DW01A TD (U3 pin 4).** The stock KiCad symbol marks TD as `no_connect`, so the wire drawn to CELL_N was never in a net (`unconnected-(U3-TD-Pad4)`). The PUOLOP app circuit (p.3) shows no external connection on TD; the earlier note "tied per app circuit" was a misreading. Fix:
  - New symbol `klepon:DW01A` with TD as a visible passive pin.
  - The TD wire is removed and a no-connect flag added, so the netlist is unchanged.
  - The CELL_N rail is trimmed to Q6.
  - Owner question Q-9: leave TD floating or tie it to GND.
- **Radio Power:** the VCC5V0_SYS symbol for the VDD_FEM switch moved right of the Q7 source, pointing down, so its text no longer sits under C120.
- **Power:**
  - Boost output caps C30–C33 moved to 15.24 mm pitch, with TP7 between R15 and C30.
  - C24/C25 spaced out.
  - R14/R17/R18 texts placed explicitly.
- **Verification** (`kicad-cli`, 2026-11-20):
  - Netlist partition equals the label baseline, except for the intended USBLC6 change.
  - ERC: 9 root sheet pins unconnected, I2C_SCL not driven, 2 isolated hierarchical labels. All of these wait on the SoC sheet. The DW01A warning is gone.
  - Scripting server `find_wires_crossing_symbols`: 0 on all four sheets.
  - Scripting server `find_overlapping_elements`: only power symbols sitting on a pin (C3, R6, R10, U1, R100, C27, C29, C61, R62).
  - All four sheets were inspected in the `kicad-cli` SVG render for text overlaps.
- Next: re-export the PDF and SVGs, refresh the design report, then T11 (SoC sheet).
- SVG export: the scripting server `export_schematic_svg` wrote only the root sheet (klepon.svg), so the per-sheet SVGs were exported with `kicad-cli sch export svg`.
- Design report published as v5 (`docs/reports/rev1-design/`): new section 7 'Redraw' with outlined before/after crops, USBLC6 flow-through and DW01A TD diagrams, check table; refreshed sheet SVGs; Q-9 added. Source synced to `docs/reports/rev1-design/`.

## Owner: cold start from solar (P-8) and a GPS instead of the ESP32 (N-8)
- **New requirements:**
  - P-8 (owner): with the node off and the battery at 0 %, solar alone starts charging, with no user, USB or firmware.
  - P-9, P-10, F-4: derived from P-8.
  - N-8 and H-12 (owner): a cheap GPS replaces the original ESP32.
  - N-9: 1PPS to a GPIO, a design proposal.
  - Removed or amended: G-1 (2.4 GHz dropped), N-2 (removed), N-7, P-6, H-3, H-11.
  - New questions: Q-10 (C5 band), Q-11 (GPS antenna).
- **Cold-start findings (`TI_BQ25798.pdf`):**
  - Host-less default mode charges by itself (§9.3.9.1 p.41, §9.4.1 p.55): trickle 100 mA below 2.25 V, then pre-charge 120 mA up to 3.0 V (p.12, p.41, REG08 p.64).
  - The DW01A allows 0 V charging and releases overdischarge at 2.9 V (p.2, p.4).
  - **VAC_OVP POR default contradicts itself:**
    - The REG10 field table says 11b = 7 V.
    - The register reset value 85h decodes to VAC_OVP = 00b = 26 V (p.72).
    - If 7 V is right, a 12 V panel never reaches the charger until firmware runs, and P-8 fails. This blocks the panel choice (Q-5). To resolve: TI E2E or a bench test (T17a).
  - **Load hold-off:**
    - SYS is regulated to VSYSMIN 3.5 V even with a flat cell (p.25, p.39), and the VSYSMIN loop starves charging under load (p.40).
    - U4's EN is pulled to VIN (R18), so the RV1106 boots as soon as solar arrives.
    - Needs a VBAT-threshold hold-off on the boost enable (T17b).
  - **No MPPT before firmware:** MPPT is off at POR and can't be enabled while VBAT < VSYSMIN (p.34). Default VINDPM is VBUS0 − 1.4 V (p.27). Slow, but enough for the trickle and pre-charge currents.
  - **Default-mode timers:** trickle 1 h, pre-charge 2 h, fast 12 h, half rate during DPM (p.55, p.69). Charging stops when one expires. They reset on CE/EN_CHG toggles and phase changes (p.44). Whether the nightly loss of input power (a fresh POR) resets them must be measured (T17c).
  - **Power-off must use ship mode,** which a new input ends (§9.3.12.2 p.50), never EN_CHG = 0: STOP_WD_CHG = 0 keeps EN_CHG across a watchdog expiry (p.65). Recorded as F-4.
- **GPS candidates** (local LCSC catalog snapshot 2026-11-19, qty 1; datasheets not yet read):
  - ATGM336H-5NR32-G C49233943, $1.98, 462 in stock.
  - ATGM336H-5N31 C90770, $3.26, 9,518 in stock.
  - The bare AT6558R chip (C500608, $0.73) is rejected: it needs its own LNA, SAW filter and TCXO.
  - The ESP32-WROOM-32UE ($4.01) is removed. Its TLV62569 rail on Radio Power is oversized for a ~26 mA GPS (T18).
- **Bonus:** SPI0 is no longer used, which removes the SPI0_M0 / SDIO_M1 overlap on GPIO1_C.
- **Not done yet:** the schematic still has the ESP32 sheet, the ESP32 rail and its root sheet pins. The power budget still includes the ESP32. Tracked as T17–T19.

## Owner answers: Q-10, Q-11, Q-5
- **Q-10:** the ESP32-C5 meshes on **2.4 GHz**. G-1 is now sub-GHz + 2.4 GHz, and N-3 is updated. 5 GHz is unused, so a cheaper 2.4 GHz module is raised as Q-12: ESP32-C6-MINI-1U-H4, C20627095, $4.34 vs $5.58 for the C5, LCSC snapshot 2026-11-19. No ESP32-C3 U.FL module was in stock in the snapshot.
- **Q-11:** the GPS gets an **external active antenna on U.FL** (H-12). The board must supply the antenna bias.
- **Q-5:** a **handheld-size solar panel** (P-11). Cell count is still open.
  - Seller figures: 2 W 110×136 mm, Voc 7.2 V, Isc 366 mA (https://temperosystems.com.au/?p=34756); 3.5 W 210×113 mm, Voc 7.0 V, Vmp 6.0 V, Imp 615 mA (https://sparkfun.com/products/13782).
  - LCSC has no solar panels (catalog search: only PV connectors), so the panel is a stated non-LCSC item.
  - **Energy:** 2–3.5 W × 4 h × 0.75 (budget EST) is 6–10.5 Wh/day, i.e. a 0.25–0.44 W average, against about 1.8 W always listening. The node must sleep most of the time: Q-13 for the owner.
  - **Good side effects:**
    - Default VINDPM below 7 V is VBUS0 − 0.7 V (p.27), about 6.3 V, near the panel's Vmp of 6.0 V, so the cold start is nearly at the maximum power point without firmware.
    - VAC2 at about 6.5–6.8 V is under the possible 7 V VAC_OVP default at room temperature, but marginal in the cold (p.10). T17 still has to settle the default.
    - The >15 V hot-plug snubber is no longer needed.
- New tasks: T20 (solar input for a 6 V panel). T19 is extended to cover the panel and duty cycle.

## Solar panel search (owner: "check aliexpress or digikey, use web browser")
- Used a headless browser: Playwright 1.65.2 in the scratch venv, driving the Chromium build already in `~/.cache/ms-playwright`. Nothing new was installed under `~/`. Scripts are kept in `hardware/tools/web/`.
- **AliExpress** works headless. The search page shows a $1.09 new-shopper price on everything, so `skus.py` clicks each variant and records the regular price.
- **DigiKey** works headless: 10 solar cells, mostly Voltaic Systems. The P105 drawing was downloaded to `hardware/datasheets/Voltaic_P105_dwg.pdf`.
- Results and design notes are in `docs/solar-panels.md`, and P-11 is updated.
- **Key point:** "6 V" panels have a Voc of 7.0–8.5 V, at or above the possible 7 V VAC_OVP default. T17a (settle VAC_OVP) now decides between a 5 V and a 6 V panel.
- **Energy:** a 3 W handheld panel gives about 0.375 W average (EST). Q-13 still open.
- Solar panel report published: `docs/reports/solar-panels/` (photos, to-scale sizes, sustainable power, Voc against the 7 V VAC_OVP band). Source in `docs/reports/solar-panels/`. AliExpress started showing a reCAPTCHA robot check after repeated headless visits; I stopped there and did not try to get around it, so per-size photos weren't collected.

## T21: external solar jack (owner: "an external connector where the user can plug it in")
- **Options offered:** board-edge DC barrel, panel-mount DC barrel, GX12 aviation, IP68 circular. The owner picked the **board-edge DC barrel** (H-13).
- **Part:** XKB DC-005 2.0, C16214, $0.0566, 73,944 in stock (LCSC catalog snapshot).
  - Datasheet `hardware/datasheets/XKB_DC-005.pdf`: DC 12 V 1 A, −25…85 °C, ≤50 mΩ, 2.0 mm pin (takes a 5.5 × 2.1 mm plug).
  - PCB layout: rear (centre-pin) slot 13.8 mm from the front face, middle slot 7.5 mm, side slot 10.8 mm and 4.6 mm off-axis; 3.0 × 1.0 slots.
- **Footprint `klepon:DC-005_Horizontal`:** a copy of KiCad's `BarrelJack_Horizontal` (pads 1 rear, 2 middle, 3 side) with pad 2 moved to −6.3 mm and pad 3 to (−3.0, 4.6) to match the datasheet. Done as a text edit, because the scripting server has no footprint editor; checked with `kicad-cli fp export svg`.
- **Schematic:** J2 replaced by `Connector:Barrel_Jack_Switch` through the scripting server (delete, add, LCSC field).
  - Pin 1 (centre) goes to the D1 anode; pins 2 (sleeve) and 3 (switch) go to GND. Which of the DC-005's pins 2 and 3 is sleeve and which is switch doesn't matter, since both are grounded.
  - Wires regenerated from `build_usb2.py`; fields re-placed.
- **Verification:**
  - Netlist vs before: the only change is J2/3 joining GND.
  - ERC unchanged: 13 items, all waiting on the SoC sheet.
  - Layout lint: 0 wires crossing symbols; overlaps are only power symbols on pins.
  - KiCad render checked.
- **Still to do:**
  - The jack's front face goes on the board edge at layout.
  - ESD/TVS at the jack, sized once the panel voltage and VAC_OVP are settled (T17, T20).
  - The design report's BOM line still says XH-2A.

## T18: GPS replaces the ESP32 (schematic)
- **Module: ATGM336H-5NR32-G** (C49233943, $1.98, 462 in stock). From `ZHONGKEWEI_ATGM336H-5NR32-G.pdf`:
  - GPS + BDS + GLONASS; VCC 2.7–3.6 V (abs max 3.6 V), 26 mA (p.7-8).
  - VBAT backup 1.5–3.6 V at 10 µA. Hot start ≤1 s, cold start ≤32 s (p.8-9).
  - VCC_RF 3.3 V feeds the active antenna, with 50 mA short-circuit protection (p.8, p.11).
  - ON/OFF and nRESET may float; the reference circuit leaves them open (p.7, p.10). The manual asks for an LDO with ripple under 50 mVpp (p.11).
  - Second source: ATGM336H-5N31 (C90770). Same pinout; its pins 16/17 are I2C, unused here (`ZHONGKEWEI_ATGM336H-5N.pdf` p.10-11).
- **Package:** the pad layout matches u-blox MAX: 1.1 mm pitch, 0.65 mm edge, 9.7 × 10.1 mm (p.5-6). The pin order matches when rotated, so it uses KiCad `RF_GPS:ublox_MAX`. New symbol `klepon:ATGM336H` (scripting server create_symbol).
- **Power:**
  - ME6211C33M5G-N (C82942) from VSYS, CE driven by GPS_PWR_EN with R200 100k pull-down. Pins 1 VIN, 2 VSS, 3 CE, 4 NC, 5 VOUT; CE high ≥1.0 V, low ≤0.5 V; Iq 30 µA; 1 µF in and out (`Microne_ME6211.pdf` p.2, p.4, p.6).
  - Backup: XC6206P332MR (C5446, Basic) from VBAT. SOT-23 pins 1 VSS, 3 VIN, 2 VOUT; 1.0 µA Iq; 1 µF in and out (`Torex_XC6206.pdf` p.1-2).
  - 10 µF at the module's VCC, as in the reference circuit.
- **RF:** U.FL Hirose U.FL-R-SMT-1(80) (C88374). L20 47 nH 0402 (C395068) from VCC_RF to RF_IN, as in the reference circuit. Its SRF is not checked.
- **Sheet:** `esp32.kicad_sch` (still empty) became `gps.kicad_sch`, titled "GPS", by editing the root sheet's name and file fields; the scripting server has no tool to rename a sheet. Root sheet pins GPS_PWR_EN, GPS_TXD, GPS_RXD and GPS_PPS added through the scripting server.
- **Radio Power:** rebuilt without the ESP32 TLV62569 block (U9, L9, R90–R92, C90–C93, TP19). The C5 block moved to y = 45.72 and the HaLow block to y = 96.52. The root ESP32_PWR_EN pin was removed by text edit.
- **Verification:**
  - Netlist: no change besides the ESP32 removal and the GPS addition. GPS nets as designed: VCC3V3_GPS, U20-VBAT from U22, VCC_RF→L20→RF_IN/J20, and the hierarchical labels.
  - ERC: only cross-sheet items, all waiting on the SoC sheet.
  - Layout lint: 0 wires crossing symbols on GPS and Radio Power; overlap flags are only power symbols on pins.
- **Cost:** GPS sheet $2.37. Removed: ESP32-WROOM-32UE $4.01 and the rail $0.20. Net **−$1.84 per board**.
- **Next:** T17b load hold-off, then T11 SoC (UART + PPS + GPS_PWR_EN pins on a 3.3 V bank; SPI0 is now free).
- Design report v6 published (`docs/reports/rev1-design/`): architecture and power tree for HaLow + C5 on 2.4 GHz + GPS; budget without the ESP32; proposed GPS pins in the connection diagram; GPS sheet section; costs for five sheets $10.20; Q-9, Q-12 and Q-13 listed. `docs/rv1106-pinmap.md` has the proposed GPS pins.

## T17b: battery hold-off (owner: on ≈ 3.6 V, off ≈ 3.3 V)
- **Why the boost input is switched, not its EN:** the TPS61089 passes VIN to VOUT through the rectifier body diode in shutdown (§8.3.2, p.10). The TLV62569s run down to UVLO 2.3–2.45 V falling (Electrical Characteristics). So with EN low, VSYS 3.5 V − 0.7 V ≈ 2.8 V on VCC5V0_SYS would still start the SoC rails. A P-FET disconnects the boost input instead: VSYS → VSYS_SW.
- **Circuit (new sheet `holdoff.kicad_sch`, "Hold-off"):**
  - **Sense:** VBAT → R301 432k / R302 100k → SNS, with C301 100 nF filter (τ ≈ 8 ms).
  - **Reference:** U31 TL432 (UMW 0.5 %, C545558: Vref 1.243–1.256 V, IKA(min) 0.1 mA, pins 1 REF, 2 K, 3 A; `UMW_TL432.pdf` p.1, p.3), biased by R303 10k from VSYS (≥0.13 mA at VSYS 2.6 V). R304/R305 100k/100k give VREF = 0.625 V.
  - **Comparator:** U30 LM2903DR2G (onsemi, C57474, −40…105 °C; LM393/D p.1-3: input common mode 0…VCC−2.0 V over temperature, Icc 0.4 mA typ).
    - A: SNS vs VREF → CTRL (R306 100k pull-up to VSYS) → Q10 2N7002 → R307 10k → Q9 AO3401A gate.
    - B: same inputs, OUTB pulls R309 887k from SNS to GND while the node is held off. The hysteresis therefore doesn't depend on VSYS.
  - **Thresholds:** off = 0.625 × (1 + 432/100) = 3.32 V; on = 0.625 × (1 + 432/(100‖887)) = 3.63 V. About ±2 % (Vref ±0.5 %, resistors 1 %).
  - **Q9 AO3401A** (C15127): <60 mΩ at −4.5 V, <85 mΩ at −2.5 V, 4 A (`AOS_AO3401A.pdf`). About 0.2 V drop at a ~3 A peak. Gate RC R308 100k / C302 10 nF for a slow turn-on, as in the VDD_FEM switch.
  - **VSYS_SW** carries a PWR_FLAG and TP31. The Power sheet's boost input symbol changed from VSYS to VSYS_SW (text edit) and `blocks.boost` is updated.
- **Tools:**
  - New `unit=` and `mirror_axis=` support in `blocks.py` / `wires.py`.
  - `sexpblk.find_symbol` takes `REF@unit`.
  - `setfield.py` has a `hide` option.
  - `movesyms.py` keys by ref@unit. Its first run hit a KeyError that a `| tail` pipe hid from `set -e`, and applywires then doubled the wires. The sheet was restored from `backup/holdoff_v1` and re-run without pipes.
  - Footgun: never pipe a step in a `set -e` chain.
- **Verification:**
  - Netlist: SNS = R301/2, R302/1, C301, R309/1, U30/3, U30/5. VREF = R304/2, R305/1, U30/2, U30/6. OUTA → Q10 G + R306. OUTB → R309. VSYS_SW = Q9 D + boost input (C24, C25, L2, R18, U4 VIN).
  - ERC: only cross-sheet items.
  - Layout lint: 0 wires crossing symbols; overlaps are only power symbols on pins.
  - KiCad render checked.
- **Cost:** $0.26.
- **Not verified:**
  - Behaviour on a board (T17d).
  - Q9 SOT-23 thermal at sustained high input current.
  - USB-plugged cold start waits for 3.6 V (Q-14).
- Design report v7 published: hold-off in the power tree, new Hold-off section with the threshold diagram and sheet, six sheets cost $10.46, Q-14 listed.

## Owner: the panel is the user's choice; the DC input takes any DC source up to the charger's maximum
- The owner's point: the panel is external, so it depends on the user, and the node shouldn't be sized around it.
  - P-11 is rewritten (panel external, user's choice).
  - Q-13 is retired into F-6: firmware adapts the duty cycle to the energy available, with GPS-timed wake windows.
- New P-12 (owner): any DC source, 3.6–24 V operating (VBUS operating range, `TI_BQ25798.pdf` p.10), up to 3.3 A (IINDPM 100 mA–3.3 A, POR 3 A, p.63). It must survive up to 30 V (VAC1/VAC2/VBUS absolute maximum, p.8), reverse polarity and hot plug.
- New F-7: firmware sets VAC_OVP to 26 V at boot.
- **Consequences, tracked as T22:**
  - The DC-005 is only 12 V 1 A, so it must be replaced.
  - The SS34 is 3 A, with about 1.6 W loss at 3.3 A.
  - A TVS with 24 V standoff clamps above the 30 V absolute maximum at full surge.
  - The AO3400A input FETs are 30 V parts against a 24 V input.
  - The snubber stays.
- The VAC_OVP POR question (T17a) now decides whether P-12 works at all with a flat battery.

## T22: DC input reworked for 3.6–24 V (P-12)
- **Jack:** DC-005G-2.5A-2.0 (C692446, 24 V 2.5 A; `XKB_DC-005G-2.5A-2.0.pdf`).
  - LCSC search: no board-edge 5.5 × 2.1 mm jack rated above 2.5 A, so P-12's current is capped at 2.4 A by firmware IINDPM (F-7).
  - A hardware ILIM_HIZ divider (100k/133k from REGN → 2.03–2.46 A over REGN 4.6–5.2 V; `TI_BQ25798.pdf` §9.3.4.3, p.16) was considered but left out, because there's no clean space on the control-pin side. At power-up with a flat battery only the 1 A default charge current flows (the hold-off keeps the system off).
  - New footprint `klepon:DC-005G_Horizontal`: pads at 0 / −6.2 / (−2.9, 4.6) mm, two Ø1.5 NPTH pegs at (−6.2, ±3.5), front face −13.7.
- **Reverse polarity:** Q11 WST2319 (C2906299; −40 V, ±20 V gate, 58 mΩ max at −4.5 V; `Winsok_WST2319.pdf`) replaces SS34 D1 (3 A, about 1.8 W at 3.3 A). Gate: R22 100k to GND, D3 BZT52C12 clamp from source.
- **TVS:** D1 is now SMAJ24A (C19077541; standoff 24 V, breakdown 26.7 V min, clamp 38.9 V at 10.3 A; `SMAJ_series.pdf`), placed after Q11 so a reversed supply doesn't forward-bias it.
  - Residual risk: at full surge the clamp is above the BQ25798's 30 V absolute maximum on VAC2 (p.8).
- **Input FETs:** Q3/Q4 are now SI2318A (C2681218; 40 V, ±20 V gate, 46 mΩ at 4.5 V; `UMW_SI2318A.pdf`). Same SOT-23 GSD pinout, so the AO3400A symbol is kept.
- **TI Fig 10-1 (p.130) elements that were missing:**
  - 294 Ω in series with ACDRV1/ACDRV2 (R20, R21; C477682).
  - A gate–common-source zener on each pair, cathode at the gates (D4, D5 BZT52C10, 9.5–10.5 V). ACDRV drives the gates 5 V above the common source (p.6), and the FETs allow ±12/±20 V.
- **Net rename:** VSOLAR → VDCIN.
- **Layout:** the DC row moved down 5.08 mm. Labels pinned: D3, C2, and #PWR018 (VCC_3V3) beside its arrow.
- **Verification:**
  - Netlist diff vs pre-T22: only the intended nets.
  - ERC unchanged (cross-sheet items only).
  - Layout lint: 0 wires crossing symbols; overlaps are only power symbols on pins plus Q11/R22 pin-to-pin at the gate.
  - KiCad render checked.
- **Cost:** +$0.14.
- Reports updated: design report v8 (24 V DC input, BOM and costs, six sheets $10.59) and solar report v4 (24 V jack section).
- Q-12 answered by the owner: keep the ESP32-C5-WROOM-1U.

## Q-12 / Q-14 answered; T23 USB bypass
- Q-12: keep the ESP32-C5-WROOM-1U (owner).
- Q-14: yes, USB bypasses the hold-off (owner); new requirement P-13.
- T23 (TODO row written after the edit; the design was agreed with the owner first):
  - Q12 2N7002 (C8545), drain on the Q10 drain node (Net-(Q10-D)), so either FET pulls the Q9 gate network low.
  - Gate from USB `VBUS` through R310 10k, with R311 100k to GND (≈ 4.5 V gate at 5 V; 2N7002 VGS max ±20 V; USB-C here is a 5 V sink only).
  - The DC jack (VDCIN) does not bypass. VBUS net = J1, Q1 and VAC1 only, so charger OTG cannot drive it.
- Verified: netlist diff (only Q12, R310, R311 added); ERC unchanged; layout lint (0 crossings; overlaps are power symbols on pins and the Q12/R311 pin join); render checked; VBUS label moved left of its arrow.
- Cost +$0.022. Report v9 (hold-off $0.28, total $10.61).
- Bench item: on a 500 mA SDP port the boot surge comes from VBUS through the charger; check VSYS doesn't sag below the TLV62569/TPS61089 UVLO.

## T11 SoC sheet started
- Part: RV1106G3, LCSC C5328706 ($23.87 qty 1, 632 in stock; lcsc.com search 2026-11-20). The G2 (C5272606, $13.68, 1 Gb DDR3L) exists, but the owner chose the G3.
- Package (`Rockchip RV1106 Datasheet V1.3` §2.3, Fig 2-5, p.17):
  - QFN-128, 12.3 × 12.3 mm BSC, 0.35 mm pitch, 32 pins per side.
  - b = 0.08 / 0.13 / 0.18 mm; L = 0.3 / 0.4 / 0.5 mm; EP = 6.9 / 7.0 / 7.1 mm square; K = 2.25 REF.
  - Pin 1 is at the top of the left side, counter-clockwise from the top (Fig 2-3 and 2-4, p.16).
- Pin list: 128 pins + EP (VSS, 129) from xlsx sheet "06.PinOut List" (extracted to the scratch `soc/pins.json`).
- **T11a symbol:** `klepon:RV1106G3`, generated by script (the scripting server `create_symbol` can't make a 6-unit, 129-pin symbol with alternates). Generator: `hardware/tools/libgen/gen_rv1106_sym.py` from `rv1106_pins.json`, which is xlsx sheet 06.
  - Units: 1 Power (31 pins), 2 System (18), 3 SD and SPI1 (17), 4 SDIO VCCIO5 (10), 5 GPIO1 VCCIO1/6 (21), 6 unused camera/Ethernet/audio (32).
  - Script check: 129 pins, each exactly once.
  - Pin name = the function in use + GPIO. All mux functions are pin alternates.
  - Name changes: "DVDDD_3" in the xlsx is a typo, named DVDD_3; three multi-name 1.8 V pins are shortened.
  - Rendered with `kicad-cli sym export svg` and checked: no text overlap after widening the bodies.
- **T11b footprint:** `klepon:Rockchip_QFN-128-1EP_12.3x12.3mm_P0.35mm_EP7x7mm`. Generator: `hardware/tools/libgen/gen_qfn128_fp.py`.
  - Pads 0.18 × 0.80 mm at 6.00 mm. Corner pads are trimmed to 0.75 mm; without the trim the corner gap was 0.12 mm.
  - Minimum pad-to-pad clearance is 0.170 mm (script check).
  - Exposed pad 7 × 7 mm, 3 × 3 paste windows of 1.8 mm, 16 thermal vias (0.3 / 0.5 mm).
  - Pin 1 at the top-left, counter-clockwise; the render was checked against Fig 2-3/2-4.
  - No 3D model yet.
- **Root sheet:** the SoC sheet has no pins yet. Planned split, per the "one function per A4" rule: SoC (units 2–5, crystals, reset, debug), SoC Power (unit 1 decoupling + unit 6 unused), microSD.
- A separate pass is extracting the reference circuits from the RV1106G-AI-IPC-V13 and Luckfox schematics and the design guide into the scratch `soc/reference.md`.

## T11 paused, T24 started (owner, 2026-11-20)
- The owner asked whether to use the RK3566 instead, because more routing references exist for it. Comparison first, including memory cost for 512 MB or 1 GB.
- **SoC sheet state when paused (not yet verified):**
  - U10 units 2–5 placed and wired, with 39 hierarchical labels and 17 no-connect flags.
  - Crystals: 24 MHz KYX K3A240001210 (C368741, 12 pF, ±10 ppm over −40..85 °C, 40 Ω) and 32.768 kHz Epson FC-135 (C32346).
  - nPOR 1k/10nF; VBUSDET 10k/15k; USB 2.2 R (C2906903); SARADC_IN0 10k to 1.8 V + 1 nF + RECOVERY pad; 22 R on SD/SDIO/SPI1 clocks; I2C 10k pull-ups.
  - C5 handshake/data-ready moved to GPIO1_C5/C6 (off the FSPI pads).
  - Remaining for T11: last field fix not rendered, netlist/ERC not run, SoC Power and microSD sheets not drawn, root sheet not wired.
- Reference-circuit extraction is in the scratch `soc/reference.md`. The RV1106 is rated 0–80 °C ambient (DS V1.3 Table 3-2 p.21); LCSC lists −20..85 °C.
- **T24 live prices (lcsc.com product pages, 2026-11-20; qty 1 / qty 30):**
  - RK3566 C2943786: $14.23 / $10.44 (691 in stock; BGA-565 15.5 × 14.4 mm).
  - RV1106G3 C5328706: $23.87 / $21.14.
  - RK809-5 PMIC C2939628: $2.42 / $1.86.
  - DRAM 512 MB:
    - DDR3L 4 Gb ×16 Samsung K4B4G1646E-BYMA C500275 (−40..95 °C): $12.53 / $10.42.
    - DDR4 4 Gb ×16 K4A4G165WF-BCTD C2803249: $17.82 / $15.36.
    - DDR4 4 Gb ×16 SK hynix H5AN4G6NBJR-VKC C2849414: $18.17 / $17.16.
  - DRAM 1 GB:
    - LPDDR4 8 Gb ×32 K4F8E3S4HD-MGCL C2920231: $30.71 / $29.12.
    - DDR4 8 Gb ×16 Rayson RS512M16Z2DD C41356073: $36.07 / $34.21.
    - Samsung K4A8G165WC C2803251: $49.76.
- **JLCPCB quote** (jlcpcb.com/quote, 80 × 60 mm, 5 pcs): 4-layer $8.00, 6-layer $32.00 (7–8 days), before shipping. The qty 50 quote couldn't be scripted (quantity dropdown).
- RV1106-only regulators that an RK809 would replace: TLV62569 C141836 $0.071 and EA3036CQBR C570857 $0.292 (local LCSC DB).
- **T24 report** (owner): docs/reports/soc-compare/ (`index.html`, `research.md` with all RK3566 sources, `rv1106-reference-circuits.md`).
- **Per-board cost** (SoC + memory + SoC-specific power, qty 30, before PCB): RV1106G2 $12.37; RV1106G3 $21.62; RK3566 + 512 MB with one DDR3L ×16 $24.83 (the 16-bit bus needs an RK template, unproven on RK3566); 2× 2 Gb $29.49; 1 GB with 2× DDR3L $35.25; 1 GB with LPDDR4 $43.53 (the configuration every RK3566 board uses).
- **PCB:** Rockchip recommends 6 layers; 4 is possible only with its template rules.
- **Recommendation:** stay with the RV1106 (G3, or G2 to save $9.25 if 128 MB is enough). Waiting for the owner's choice.
- The research pass saved `hardware/datasheets/Rockchip_RV1106_Datasheet_V2.2-20260602.pdf` (temperature −20 to 85 °C, p.27). Index it in T2.
- **Owner decision 2026-11-20: stay with the RV1106G3 (T24 closed). T11 resumed.**
- **T11 SoC sheet:**
  - SoC reference changed U10 → **U100**: Radio Power already used U10/U11, and the duplicate showed in the netlist (`U10/4` on VCC5V0_SYS).
  - Unit fields placed on separate lines.
  - Netlist checked: crystals, nPOR, VBUSDET divider, SARADC pull-up, I2C pull-ups and the rails as designed.
  - ERC: only hier_label_mismatch (root not wired yet).
  - Scripting server `find_wires_crossing_symbols` and `find_overlapping_elements` report false positives on the multi-unit U100: they use a bounding box spanning all units (28–33 mm "overlaps"). Checked in the render instead.
- **T11 SoC Power sheet (`soc_power.kicad_sch`, new root sheet "SoC Power"):**
  - Unit 1 regenerated: supply pins grouped by rail, with gaps for the per-pin filters.
  - Unit 6: 30 no-connect flags, FEPHY_EXTR 6.04k 1% (C97819), CODEC_VCM 4.7 µF (C23733).
  - Decoupling banks:
    - VDD_ARM: 10u/1u/100n.
    - VDD_0V9: 2×10u, 2×1u, 9×100n (one per pin, HDG text).
    - VCC_DDR: 2×10u/1u/100n.
    - VCC_1V8: 100n OSC, 100n CODEC, 1u + 100n DDR_PLL.
    - VCC_3V3: 8×100n.
  - Filtered pins: pin 96 BLM15PD121 (C76891) + 100n; pins 24 and 1 through 1R (C2906901) + 100n; pin 19 through 100R + 1u.
  - DRAM_ZQ: 240R 1% (C114755).
  - PWR_FLAGs on the 4 filtered nets (ERC power_pin_not_driven).
  - Verified: netlist (every supply pin on the right rail), ERC clean on this sheet, render checked, overlaps are only power symbols on pins.
- **T11 microSD sheet (`microsd.kicad_sch`, root sheet "microSD"):**
  - Socket: SHOU HAN TF PUSH C393941 ($0.066; `hardware/datasheets/ShouHan_TF-PUSH.pdf`).
    - New symbol `klepon:microSD_TF_PUSH`: VDD on top, VSS/SH at the bottom, signals and DET on the left, so it can be drawn with wires only.
    - New footprint `klepon:microSD_ShouHan_TF-PUSH`, from the p.1 land drawing scaled on the 8.00 mm hole pitch (generator `hardware/tools/libgen/gen_tfpush_fp.py`). Signal-pad X positions are ±0.1 mm, so check them at T15.
    - The EasyEDA footprint API returned 403, so it wasn't used.
  - Card power, per REF p.19: AO3401A Q401, 100k + 100 nF gate-source, 10k from SD_PWREN; 100 nF + 10k bleeder; 4.7 µF + 100 nF at the socket; PWR_FLAG on VCC3V3_SD.
  - DET: Cd → 100R → SD_DET. The Cd contact is assumed to close to the shell (UNVERIFIED; the datasheet has no description), so R403 10k DET→GND is fitted as DNP (KiCad `dnp yes`) as a fallback.
  - No CMD/DAT pull-ups (internal) and no ESD (as LPM).
- **References renumbered:** SoC 1xx → 5xx (clashed with Radio Power R101/R102/R110–R112/C101–C103); SoC Power 2xx → 6xx (clashed with GPS C201–C204). Done with `hardware/tools/schgen/renum.py` (text edit of Reference/instance fields plus builders and field files). Duplicate check across all 13 sheets: none.
- **Root sheet re-laid out** with `hardware/tools/schgen/rootlayout.py` (text edit: the scripting server has no move/resize-sheet tool):
  - Left column: USB and Charger, Battery, microSD, GPS. Centre: SoC (50.8 × 101.6). Right column: HaLow, Radio Power, ESP32-C5, Antenna. Bottom row: Power, Hold-off, SoC Power.
  - 47 sheet pins added through the scripting server. Its pins come out with their text outside the box, so the script fixes justification on every pin.
  - 21 straight wires drawn (applywires), including TS USB↔Battery redrawn vertically.
- **Verification:**
  - Netlist vs pre-T11: every existing net keeps its old members; only the intended SoC connections were added (GPS 73/87/89/91, Radio Power 72/75/104, I2C 64/65 with pull-ups, CHG_INT 60, USB via R508/R509, rails).
  - ERC: 19 pin_not_connected + 19 isolated_pin_label, all SoC pins for HaLow (9) and ESP32-C5 (10), waiting for T12/T13.
  - Renders checked on all three sheets and the root.
- **Cost of the three new sheets** (qty 1): $24.71 (RV1106G3 $23.87). Drawn sheets now total $35.32.
- Q-15 (operating temperature) added to the requirements.
- Next: T12 HaLow sheet, then T13 ESP32-C5 and T14 Antenna.

## T12 HaLow sheet started (2026-11-20)
- **Module:** Heltec HT-HC01 V2. Not stocked by LCSC (live search 2026-11-20); heltec.org lists 902–928 MHz at $11.90 (list $13.90). The U701 `Supplier` field holds the source and reason.
- **Footprint `klepon:HT-HC01_V2`:** converted from Heltec's own Altium library, `HT-HC01_V2.PcbLib`, which the datasheet links on p.19 (resource.heltec.cn).
  - Conversion: pcbnew's Altium reader (`hardware/tools/libgen/altium_fp_convert.py`) and `import_htc01_fp.py`, which drops the User.2 items and adds a courtyard and an 18.5 × 14 body.
  - Pads: 38 at 1.5 mm pitch, numbered clockwise from the top-left (1–12 top, 13–20 right, 21–31 bottom, 32–38 left), plus two bottom "0" pads, which are GND in Heltec's SchLib.
  - Pin names were checked against both the datasheet p.7–9 table and the SchLib (converted with `kicad-cli sym upgrade`).
- **Symbol `klepon:HT-HC01_V2`** (`gen_htc01_sym.py`): SDIO pins 4 rows apart for the pull-ups; JTAG/GPIO grouped in fours; GND pins stacked (pin 0 visible, the others passive and hidden at the same point).
- **Circuit** per Heltec's SDIO reference (`hardware/datasheets/Heltec_HT-HC01_V2_SDIO_reference.pdf`) and datasheet p.9/p.17–18:
  - 10k pull-ups to VCC3V3_HALOW on CLK, CMD and D0–D3.
  - 10k to GND on JTAG TCK/TDI/TMS/TRST_N/TDO and GPIO_1–9, as four 4×10k 0402 arrays (C25725) in line into a GND bus; 10k pull-down on BUSY.
  - 10 µF + 100 nF on each of VBAT, VDD_IO and VDD_FEM. VDD_IO and VBAT both on VCC3V3_HALOW (VDDIO ≤ VBAT, p.18).
  - Pull-ups go to the module rail, so they don't back-power it when it's off.
  - ANT goes to the HALOW_ANT label; the DC block, match and LPF are on the Antenna sheet (T14).
- **Root:** 10 HaLow sheet pins, 9 straight wires to the SoC.
- **Verified:**
  - Netlist: every HaLow net and rail as designed; all 9 GND pads + pad 0 on GND.
  - ERC: only HALOW_ANT (T14) and the 10 C5 pins (T13).
  - Layout lint: 0 crossings; overlap flags are power symbols on pins and U701's bounding box.
  - Render checked; no duplicate references.
- **Cost:** HaLow sheet $12.05 ($11.90 module + $0.15 passives). Drawn sheets now total $47.37.

## T13 ESP32-C5 sheet started (2026-11-20)
- **Module:** ESP32-C5-WROOM-1U-N16R8-V1.2, C54951857 ($5.91 qty 1, $4.59 at 30, 506 in stock). Cheapest in-stock C5-WROOM-1U; the N8R8 is $6.01. Pin 19 is SPICS1 for the PSRAM, so it's left unconnected.
- **Footprint:** Espressif's official KiCad library (github.com/espressif/kicad-libraries, `ESP32-C5-WROOM-1U.kicad_mod`, fetched 2026-11-20). 40 pads: 1–28, a 3×3 thermal grid (29), and 30–32 at the antenna. Checked against datasheet v1.3 p.55: 1.27 mm pitch, 1.5 × 0.9 mm pads. The 3D model reference to Espressif's library variable was removed. The repo's license shows as NOASSERTION on GitHub; check its README before redistributing.
- **Symbol `klepon:ESP32-C5-WROOM-1U`:** `hardware/tools/libgen/gen_c5_sym.py`, from Table 3-2.
- **Circuit** per datasheet Fig 9-2 p.50 and boot straps p.16–18:
  - 22 µF (C59461) + 100 nF on 3V3.
  - EN: 10k + 1 µF.
  - IO28: 10k pull-up (SPI boot by default; the RV1106 holds it low and pulses EN to reflash).
  - SPI slave on the IO_MUX pins.
  - ANT2 (pin 31) left unconnected; ANT1 is the module's U.FL.
- **Root:** 10 sheet pins and 10 straight wires.
- **Verified:**
  - Netlist: every C5 net to the planned U100 pin, as tabled in `docs/rv1106-pinmap.md`.
  - ERC: whole design down to the one expected item, HALOW_ANT (T14).
  - Lint: 0 crossings; overlaps are only power symbols on pins.
  - Render checked; no duplicate references.
- **Cost:** ESP32-C5 sheet ≈ $5.94. Drawn sheets now total ≈ $53.31.

## T14 Antenna sheet started (2026-11-20)
- **HaLow RF path:** HALOW_ANT → C901 100 pF C0G DC block (Heltec SDIO reference) → 5-pole LC low-pass → J901 U.FL (C88374, same part as the GPS).
  - Filter: C902 2.7 pF, L901 8.2 nH, C903 5.6 pF, L902 8.2 nH, C904 2.7 pF. C0G caps C1561/C1574; Murata LQW15AN8N2G00D wire-wound inductors C84404 (`hardware/datasheets/Murata_LQW15AN8N2G00D.pdf`: Q ≥ 25 @ 250 MHz, SRF ≥ 5.5 GHz, 0.14 Ω).
  - Simulated (ABCD model, inductor Q and SRF at the datasheet limits): 0.60 dB loss at 915 MHz worst case (0.32 dB at Q 50), RL 31 dB, −20 dB at 2fo, −44 dB at 3fo (2.745 GHz).
  - Alternatives considered:
    - Integrated LTCC LPF RFLPF16080G9D9T (C474017, $0.18): 0.9 dB loss max.
    - Multilayer 10 nH (SRF 3.2 GHz): 1.1 dB loss.
    - Discrete chosen for lower loss and cost ($0.12).
  - Values are a starting point: tune on the first board with a VNA and a spectrum analyser. The shunt pads double as the antenna match.
- **Root:** HALOW_ANT wire from the HaLow box to the Antenna box down the right margin.
- **All 12 sub-sheets drawn.**
  - Full-design ERC: 0 items. No duplicate references.
  - HaLow RF chain verified in the netlist.
- **Cost:** Antenna sheet ≈ $0.24; drawn sheets total ≈ $53.55.
- Next:
  - T15: footprint checks (QFN-128, microSD TF PUSH, HT-HC01 V2 import, C5 import, DC-005G, FHD4020S/KF301).
  - T17a/c/d, T19 power budget refresh (ESP32 removed, GPS added).
  - T2 datasheet README.
  - Then board layout.

## T15 footprint checks started (2026-11-20)
- **Pin ↔ pad check** (`hardware/tools/schgen/check_pinpad.py`, kicadxml netlist vs every .kicad_mod): 296 parts, 0 mismatches. Sanity-checked counts: U100 129/129, U701 39/39, U801 32/32, J401 10/10.
- **microSD footprint corrected** from the drawing's vector data (C393941 p.1; page rotated 270°; hole pitch 66.0 pt = 8.00 mm → 8.25 pt/mm):
  - Cd pad 0.70 wide (was 0.60).
  - Signal pads 0.05 mm further left: Cd −5.60, pins 8..1 −4.50..+3.20 at 1.10 pitch (matches "8 × 1.10 = 8.80").
  - Top-right shell pad 1.60 × 1.50 at +7.80 (was 1.50 at 7.75).
  - Other shell pads within 0.01 mm. Pad order Cd, 8..1 left to right (component side) ✓.
- **Footprints checked against datasheets:**
  - ESP32-C5 (Espressif official) vs land pattern p.55: 1.27 pitch, 1.5 × 0.9 pads, 16.51 span, 17.5 row spacing, 4.7 mm 3 × 3 thermal (1.3 + 0.4), pins 30–32 at 1.27 ✓.
  - HT-HC01 V2 (Heltec PcbLib) vs datasheet p.19: 1.5 pitch, 13.50 between pads 2 and 11 ✓. The 2 × 2 corner GND pads cover both corner castellations.
  - FHD4020S (L2) on L_Changjiang_FNR4020S: the FNR/FHD land tables (C167869 p.2, C602029 p.2) give gap 1.9 / pad 1.1 / length 3.7; the KiCad pads are 1.1 × 3.7 at ±1.5 ✓. FNR4030S (L1): same land ✓.
  - XRIM252012S 1008 (L5–L8, L10, L11) on L_1008_2520Metric: KiCad pads 1.25 × 2.2, larger than the maker's minimum land (A 2.60, B 0.70, C 2.10), and they cover the 0.85 mm electrodes. OK.
  - KF301-5.0 (J3) on MKDS 1×02 P5.00: drawing says 5.00 pitch, Ø1.20 holes, Ø1.0 pins; footprint has 5.00 pitch, 1.3 drill ✓.
  - FC-135 32 kHz (Y502) on Crystal_SMD_3215: Epson recommends 1.0 × 1.8 pads at 2.5 centres = KiCad exactly ✓.
  - KYX 3225 (Y501): pads 1–3 crystal, 2–4 case, diagonal ✓.
  - 4D02 array on R_Array_Convex_4x0402: 0.50 pitch, terminals 0.40/0.30 = pads 0.4/0.3 ✓ (UniOhm p.5).
  - QFN-128 and DC-005G were generated from their datasheets (T11b, T22) and the QFN pad clearance was checked by script.
  - U.FL (Hirose U.FL-R-SMT-1), USB-C (HRO TYPE-C-31-M-12), SW (XKB TS-1187A), BQ25798 RQM, TPS61089 RNR: KiCad footprints named for the exact part.
- **Small-part pinouts** (second check, `docs/reports/t15-pinouts.md`): 16 groups (SOT-23 FETs, TL432, XC6206, TLV62569, ME6211, DW01A, FS8205A, USBLC6, SMAJ24A, BZT52, LED), 0 mismatches.
  - AO3400A/AO3401A/WST2319 datasheets print no pin numbers: the mapping (1 G, 2 S, 3 D) is inferred from the pin-1 dot and confirmed by the CJ 2N7002 and UMW SI2318A datasheets, which print it.
  - TL432 here is UMW's 1.25 V part (the design already uses 1.25 V).
  - D2 LED: the vendor numbers the anode 1 (KiCad pad 1 = cathode). Wiring is correct; check polarity in the JLCPCB placement preview.
  - FET orientations and body-diode directions all as intended.
  - New datasheets filed: CJ_2N7002, SMAJ24A_C19077541, YONGYUTAI_BZT52C12, KENTO_KT-0603R.
- **T15 done.**

## T19 power budget refresh started (2026-11-20)
- **T19 power budget** rewritten (`docs/power-budget.md`, computed by `docs/calc/power_budget.py`):
  - Sources:
    - Rockchip power report V1.2 (heavy case only).
    - C5 Table 6-4/6-9; HT-HC01 p.12–14; ATGM336H p.8.
    - BQ25798 IQ_BAT 17 µA; LM2903 0.4 mA; TLV62569 35 µA; TPS61089 100 µA.
  - Results:
    - Everything listening 1.19 W (28.6 Wh/day). SoC idle 0.47 W (EST).
    - 5 V bus peak 1.07 A, battery peak 2.0 A, both within the boost/BATFET/DW01A limits.
    - Off-state 0.64 mA.
    - A 2–3.5 W panel sustains 19–33 % listening; 24 h listening needs ~10.6 W.
    - Two 18650s for 3 sunless days at 25 %.
  - Key finding: duty-cycle with GPS-timed wake windows (F-6). The SoC idle and suspend figures are the biggest unknown (MEASURE).
  - project rules power-tree text was out of date (it still listed the EA3036C and TPS22917, which the owner replaced with per-rail TLV62569s); corrected.
