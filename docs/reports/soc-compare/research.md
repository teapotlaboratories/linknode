# RK3566 chip-down vs RV1106G3: research notes for Klepon

Compiled 2026-11-20. Every fact carries a source. **UNVERIFIED** marks anything not confirmed in a primary
document, and **INFERENCE** marks my own reasoning. Downloaded copies are in this folder
(`scratch/rk3566/`).

## Sources used (short names)

| Short name | What | Where |
|---|---|---|
| **DS66** | Rockchip RK3566 Datasheet Rev 1.0 (2020-12-10). PDF page = printed page. | https://files.pine64.org/doc/quartz64/Rockchip%20RK3566%20Datasheet%20V1.0-20201210.pdf (local `rk3566_ds_v10_pine64.pdf`) |
| **HDG66** | Rockchip RK3566 Hardware Design Guide V1.1 (2022-02-06), Chinese. Printed page = PDF page − 3. | https://gitlab.com/firefly-linux/docs-soc_internal-cn/-/raw/rk356x/firefly-5.10/Hardware/Rockchip_RK3566_Hardware_Design_Guide_V1.1_20220206_CN.pdf (local `RK3566_HDG_V1.1_CN.pdf`) |
| **HDG68** | Rockchip RK3568 Hardware Design Guide Rev V1.2 (2022-01-26), English. Printed page = PDF page − 19. | https://dl.xkwy2018.com/downloads/RK3568/RK356X/Hardware/Rockchip_RK3568_Hardware_Design_Guide_V1.2_EN.pdf (local `RK3568_HDG_V1.2_EN.pdf`) |
| **EVB2** | Rockchip RK3566 EVB2 User Guide V1.1, Chinese | https://gitlab.com/firefly-linux/docs-soc_internal-cn/-/raw/rk356x/firefly-5.10/Hardware/Rockchip_RK3566_EVB2_User_Guide_V1.1_CN.pdf |
| **PWR356X** | Rockchip "RK356X Power Consumption Test Report V1.0" (2021-04-30), xlsx, marked "Rockchip Confidential" | https://github.com/hqnicolas/RK3568-hardware-design (`01_Common Document/`; repo has **no license**) |
| **TPL4L** | Rockchip RK3568 DDR4 template `RK3568_Template_DDR4P216SD4_48x31_1600MHz_V10_20210128YWQ` (PADS .asc/.pcb, Allegro .brd, OrCAD .DSN) | same repo, `02_DDR Template/` |
| **DS68J** | Rockchip RK3568J Datasheet V1.0 (2022-03-04) | https://dl.radxa.com/cm3p/docs/datasheets/ |
| **RV-DS13 / RV-DS22** | Rockchip RV1106 Datasheet V1.3 / V2.2 (local) | `hardware/datasheets/Rockchip_RV1106_Datasheet_V1.3.pdf`, `..._V2.2-20260602.pdf` |
| **RV-HDG** | Rockchip RV1103G/RV1106G Hardware Design Guide V1.1 (local) | `resources/resource/Rockchip-RV1103G-RV1106G-Hardware-Design-Guide-en-V1-1-20221221.pdf` |
| **RV-PWR** | Rockchip RV1106G Power Consumption Test Report V1.2 (local xlsx) | `resources/resource/rv1103_rv1106/Rockchip_RV1106G_Power_Consumption_Test_Report_V1.2_20220622.xlsx` |

The HDG68, PWR356X and TPL4L copies are third-party re-uploads of Rockchip documents, not Rockchip-hosted. Several
are marked "Rockchip Confidential". Treat their redistribution status as unclear.

---

## 1. RK3566 memory interface

### What the chip supports

- **DRAM types:** DDR3, DDR3L, DDR4, LPDDR3, LPDDR4 and LPDDR4X (DS66 p.7 §1.1; p.8 §1.2.5). Only one type is used at a time (DS66 p.17, notes).
- **Bus width and capacity:**
  - DDR3/DDR3L/DDR4: "32bits data width, 2 ranks (chip selects), total addressing space is 8GB(max)".
  - LPDDR3/LPDDR4/LPDDR4X: the same, but with 4 ranks.
  - Sources: DS66 p.8 §1.2.5; HDG66 PDF p.19 (printed p.16) §2.1.9.1.
- **DDR PHY supply (VDDQ) per type** (DS66 p.51, Table 3-2):
  - DDR3 1.5 V; DDR3L 1.35 V; LPDDR3 and DDR4 1.2 V; LPDDR4 1.1 V; LPDDR4X 0.6 V.
  - LPDDR4X also needs a separate VDDQL supply (HDG66 PDF p.21).

### Does it support a 16-bit bus (one x16 DDR4 or DDR3L chip)?

**The documents point to yes, but only on a Rockchip template, and I found no shipping RK3566 board that does it.**

- The datasheets and design guides list only 32-bit as the headline width (above).
- The DDR rules in both design guides mention 16-bit, for DDR3/DDR3L and for DDR4. HDG66 PDF p.20 (printed p.17) §2.1.9.2 says, translated: "If you need a template with a total bit width of 16 bit, or one compatible with 16 bit/32 bit, you must use the template provided by RK; no difference is allowed."
  - HDG68 PDF p.33 (printed p.14) has the same rule in English: "If need to support the template with a total bit width of 16bit and a template with a total bit width compatible of 16bit/32bit, it's must use the template provided by RK, and no difference is allowed."
  - HDG68 PDF p.37 (printed p.18) also refers to a "16bit DDR4 template" (the single-die/dual-die options of a DDR4 chip).
  - **INFERENCE:** the controller can run a half-width (16-bit) DDR3/DDR3L/DDR4 bus. Rockchip ties this to its own layout template, which this research has not found for the RK3566.
- No LPDDR3/LPDDR4/LPDDR4X 16-bit mode is mentioned. The LPDDR4 rules say "DQ, CA sequences cannot be swapped" (HDG66 PDF p.20).
- I did not confirm 16-bit support in the DDR init binary (`rk3568_ddr_*.bin` in rkbin). `tools/ddrbin_tool_user_guide.txt` (https://github.com/rockchip-linux/rkbin) has no bus-width option for RK3566/RK3568. Boot logs print `BW=` (bus width), but every RK356x log I found shows `BW=32`. **UNVERIFIED.**
- **The x16 configurations that Rockchip documents are 2× x16 (32-bit):**
  - "DDR4 two 16bit 1CS, DQ point-to-point, CA T topology" (HDG68 PDF p.38, printed p.19).
  - The RK3568 DDR4 template TPL4L places two `DDR4_16BIT_FBGA96` parts (U3300, U3301) in its PADS ASCII part list.

### Real boards (all 32-bit; no single-x16 RK3566 board found)

| Board | DRAM as drawn | PMIC | Source |
|---|---|---|---|
| Radxa ZERO 3W v1.11 | LPDDR4/4X, one x32 package ("LPDDR4X_1X32bit") | RK817 | https://dl.radxa.com/zero3/docs/hw/3w/radxa_zero_3w_v1110_schematic.pdf (index page "14.LPDDR4_1X32bit") |
| Radxa ZERO 3E v1.2 | LPDDR4 1×32 bit | RK817 | https://dl.radxa.com/zero3/docs/hw/3e/radxa_zero_3e_v1200_schematic.pdf |
| Pine64 Quartz64 Model A v2.0 | "DRAM-LPDDR4_1X32bit_200P" | RK817 | https://files.pine64.org/doc/quartz64/Quartz64_model-A_schematic_v2.0_20210427.pdf |
| Pine64 Quartz64 Model B v1.3 | "DRAM-LPDDR4X_1X32bit_200P" | RK809 | https://files.pine64.org/doc/quartz64/Quartz64_model-B_Schematic-V1.3_20220124.pdf |
| Pine64 Quartz64 Zero v0.1 (RK3566T) | "DRAM-LPDDR4X_1X32bit_200P"; 1 GB LPDDR4 listed | RK817 | https://files.pine64.org/doc/quartz64/Quartz64-ZERO_Schematic_v01_20240428.pdf ; https://www.cnx-software.com/2024/10/03/quartz64-zero-a-customizable-cost-optimized-rockchip-rk3566t-sbc-with-raspberry-pi-pcie-connector/ |
| Pine64 SOQuartz | LPDDR4 (2/4/8 GB) | RK809 | https://wiki.pine64.org/wiki/Quartz64 |
| Orange Pi 3B | 2/4/8 GB LPDDR4/4X | not checked | https://www.cnx-software.com/2023/08/05/orange-pi-3b-a-rockchip-rk3566-sbc-with-an-m-2-nvme-sata-ssd-socket-up-to-8gb-ram/ |
| Luckfox Core3566 | 2 or 4 GB (type not confirmed) | not checked | https://www.cnx-software.com/2023/07/04/luckfox-core3566-raspberry-pi-compute-module-4-alternative/ (**UNVERIFIED** type) |
| Rockchip RK3566 EVB2 | "LPDDR4 (512x16bit+512x16bit, 2GB)"; board file `RK_EVB2_RK3566_LPDDR4D200P132SD6_V11` | RK809-5 | EVB2 PDF p.3, p.12–13 |
| Rockchip RK3568 EVB1 (reference only) | DDR4, 2× x16 (`RK_EVB1_RK3568_DDR4P216SD6_V10`) | RK809-5 | PWR356X sheet "RK3568 EVB1 Scenario" |
| oshwhub "RK3566最小系统（四层板）" | Samsung K4F6E3S4HM-MGCJ LPDDR4 2 GB (x32 package) | RK809-5 + TCS4525 | https://oshwhub.com/mizewei/rk3566-zui-xiao-xi-tong |

Firefly's "Core-3566JD4" and some third-party SoMs use DDR4. For example, a Zhihu article describes an X3566 core
board with DDR4 on an 8-layer PCB (https://www.zhihu.com/tardis/jm/art/1996906933802791713). I did not open their
schematics to see the chip count and width. **UNVERIFIED.**

---

## 2. Package and PCB

### Package

- **RK3566 package:** FCCSP565L (DS66 p.17, p.20–21).
  - 565 balls on a 15.5 × 14.4 mm body.
  - Ball size 0.3 mm; nominal ball diameter "b" is 0.25 mm (min 0.20, max 0.30).
  - Pitch: "0.65&0.4mm". The bottom-view drawing (DS66 p.21, Fig. 2-3) shows a 0.65 mm inner grid with staggered outer rows at 0.4 mm.
  - Height A is 0.833 mm nominal.
- **RK3568/RK3568J package:** FCCSP636L, 19 × 19 mm, 0.65 mm pitch, 0.35 mm balls (DS68J p.17). The RK3568 is **not** pin- or footprint-compatible with the RK3566.
- **RV1106G2/G3 package:** QFN128, 12.3 × 12.3 mm, 0.35 mm pitch (RV-DS22 p.15).

### Does Rockchip allow 4 layers?

**Yes, with caveats.** The RK3568 guide has a 4-layer section and 4-layer DDR4 routing rules. The RK3566 Chinese guide has
no stack-up chapter: it points to a separate "Rockchip_RK3566_High_Speed_PCB_Design_Guide", which I did not find
(HDG66 PDF p.4).

- **HDG68 §3.1 (PDF p.170–171, printed p.151–152):**
  - "6-layer PCB design is recommended for RK3568."
  - It also gives a 4-layer 1.6 mm reference stack-up (Fig. 3-2):
    - TOP / 80 µm PP 1080 / GND / 1265 µm core / POWER / 82 µm PP 1080 / BOTTOM.
    - 1 oz copper; L1 references L2, and L4 references L3.
- **HDG68 DDR rules (PDF p.196, printed p.177):**
  - On 6 layers, use TOP-GND-POWER-Signal-GND-Bottom.
  - DDR impedance is 50 Ω single-ended and 100 Ω differential (±10 %).
  - A stitching via must be within 30 mil of each signal via.
  - Keep DDR traces at least 40 mil from the edge of the reference plane.
- **HDG68, 4-layer DDR4 (PDF p.207, printed p.188):**
  - "If it is a 4-layer board, DDR4 needs to rout through the Power layer"
  - Those signals must use G-S-S-G (ground guard traces), and Rockchip recommends "copy the reference PCB directly … apply the template provided by RK."
  - The DDR3/DDR3L, DDR4 and DDR4+ECC tables each repeat a "Routing requirements for 4-layer board" row: G-S-S-G on the bottom layer (PDF p.199, 200, 208, 212).
  - The LPDDR4/4X section (PDF p.212–) has **no** 4-layer row. **INFERENCE:** Rockchip's 4-layer guidance targets DDR3/DDR4, not LPDDR4.
- **HDG68, VCC_DDR on 4 layers (PDF p.194, printed p.175):** "If it is a 4-layer board, the signal of the bottom layer has to take this plane as reference."
- **HDG68, thermal (PDF p.242, printed p.223):** "It is recommended to use a 6-layer board or more."
- **HDG66, EMC (PDF p.86, printed p.83), translated:** "If the PCB has more than 4 layers, route all clocks on inner layers." The guide's RK3566 thermal simulation also uses a 4-layer JEDEC board (PDF p.81; DS66 p.58). That is a thermal test board, not a working design.
- **RV1106 for comparison:** "In RV1103G/RV1106G design, it's recommended to use 4-layer PCB stackup" (RV-HDG p.39).

### Rockchip's own 4-layer DDR4 template (strongest evidence)

TPL4L is named `..._DDR4P216SD4_48x31_1600MHz`. Its PADS ASCII header reads `MAXIMUMLAYER 4`, `VIAMODE T`
(through vias), and `PAIRED_LAYERS 1 4`. It places two DDR4 x16 chips and runs DDR4 at 1600 MHz.

- **Vias (decoded from PADS basic units, 38 100 per mil):**
  - `PROVIA_16_8`: 0.2 mm drill / 0.4 mm pad, used about 2,418 times.
  - `PROVIA_20_12`: 0.3 / 0.5 mm.
- **Trace widths in the routing:** 3.5 mil (133 348 BU), 3.8 mil, 4 mil and 10 mil.
- **No blind or buried vias.**
- **This template is for the RK3568** (19 × 19 mm, 0.65 mm pitch), **not the RK3566**. The RK3566 outer rows are at 0.4 mm pitch, so its escape differs.
- **INFERENCE from naming:** the suffix `SD4`/`SD6` appears to encode layer count, since the 4-layer template is `SD4`. On that reading, both Rockchip EVBs are 6-layer: RK3568 EVB1 `DDR4P216SD6` and RK3566 EVB2 `LPDDR4D200P132SD6`. No document states this. **UNVERIFIED.**

### Minimum via/trace rules in the guide (HDG68 §3.1.3, PDF p.171–174)

- Outer two ball rows fan out on TOP with **4 mil** traces. The second row exits between balls.
- From the third row in, change layer with vias "placed in the middle of balls" on a grid, every 2–4 rows. Leave one row empty to keep plane channels open.
- **3.5 mil** traces route between vias on inner and bottom layers.
- GND balls: at least one via per 1.5 balls, ideally one per ball, with 10 mil "井" (grid-pattern) cross-ties on TOP (PDF p.194). HDG66 PDF p.84 says the same for the RK3566.
- SDIO: 50 Ω, under 4 inch, CLK-to-data skew under 120 mil, ground guard with vias at most 300 mil apart (HDG66 PDF p.49).
- The guide gives no explicit drill size. The template uses 0.2/0.4 mm (above).
- **Fab check:** JLCPCB multilayer allows a 0.15 mm hole / 0.25 mm via and 0.09/0.09 mm (3.5/3.5 mil) trace/space, with 3 mil "acceptable in BGA fan-outs". It offers epoxy-filled, capped via-in-pad, which is the default on 6 layers and up. Source: https://jlcpcb.com/capabilities/pcb-capabilities (fetched 2026-11-20).

### Layer counts of reference boards

| Board | Layers | Source |
|---|---|---|
| Rockchip RK3568 DDR4 template | **4** (through vias only) | TPL4L `.asc` header |
| Rockchip RK3566 EVB2 / RK3568 EVB1 | probably 6 (from file name) | **INFERENCE/UNVERIFIED** |
| Radxa ZERO 3W/3E | not published | https://docs.radxa.com/en/zero/zero3/download (no layer data) |
| Pine64 Quartz64 A/B, SOQuartz, Zero | not published | https://wiki.pine64.org/wiki/Quartz64 |
| Orange Pi 3B | not found | — |
| oshwhub RK3566 minimum system (LPDDR4, RK809-5) | **4** (JLC impedance stack "3313"), hand-built, boots the Taishanpi Ubuntu image | https://oshwhub.com/mizewei/rk3566-zui-xiao-xi-tong |
| hw-myry/rk3566-devkit (LPDDR4) | 6 | https://github.com/hw-myry/rk3566-devkit (README) |
| X3566 DDR4 core board | 8 | Zhihu article above |
| Boardcon EM3566 SBC | 8 | https://www.cnx-software.com/2021/07/28/boardcon-em3566-linux-sbc-is-powered-by-a-rockchip-rk3566-system-on-module/ (from search snippet, **UNVERIFIED**) |
| CopperPilot tablet (RK3566 + LPDDR4X) | 8, 0.8 mm | https://github.com/CopperPilot/tablet |

Notes on the 4-layer RK3566 board on oshwhub:
- The author removed some filter capacitors under the SoC and DDR, because a 4-layer board without via-in-pad left no
  room. The author calls this "不推荐" (not recommended).
- The RK809-5 I2C lines were swapped and needed a bodge wire.
- The board reboots under full load without a heatsink.
- It has had no EMI/ESD testing or volume validation.
- **A 4-layer RK3566 with x32 LPDDR4 can boot. That proves it runs, not that it is reliable.**

---

## 3. Power

### PMIC options

- **Rockchip's reference:** RK817-5 or RK809-5 (HDG66 PDF p.13–14, Fig. 1-2/1-3; §2.2.4–2.2.5).
  - In the RK817-5 design, GPU and NPU share one supply "for cost reasons" (HDG66 PDF p.33).
  - RK817-5 (HDG66 PDF p.39, printed p.36):
    - USB input 3.8–5.5 V; BAT 2.7–5.5 V.
    - Built-in 3.5 A switching charger, power path, fuel gauge and RTC.
    - "16 µA" standby at 32 kHz.
- **Discrete regulators are documented:**
  - HDG66 PDF p.16 (printed p.13): when no matching PMIC is used, use a separate reset IC.
  - HDG68 §2.2.4 (PDF p.78–80, printed p.59–61) gives "RK3568 + Discrete Power (Based NVR_DEMO)", described as "Mainly for products with low requirements of standby power". It covers:
    - RESETn released at least 10 ms after the last rail; on power-down, RESETn falls first.
    - A reset IC with a 2.93 V threshold if SPI flash is used.
    - **VDD_CPU buck ≥ 4 A**, I2C or PWM DVS, 0.8–1.2 V, default ≈ 0.938 V, ±1.5 % accuracy, more than 135 µF output capacitance, ripple within 80 mV.
    - **VDD_GPU/NPU buck ≥ 3 A**, 0.81–1.1 V.
  - PWR356X "SOC Limit Power Reference" peak currents and buck sizes:
    - VDD_CPU 3 A at 1.2 V (buck ≥ 4 A).
    - VDD_GPU 1.2 A, VDD_NPU 1 A, VDD_LOG 1.2 A (each buck ≥ 2 A).
  - The RK3568 NVR demo power data is labelled "Discrete power supply scheme" (PWR356X).
  - **INFERENCE:** a discrete RK3566 design is possible and resembles the current Klepon RV1106 tree. Rockchip, however, steers products that need low standby power toward the PMIC.
- **Prices (LCSC, fetched 2026-11-20):** RK809-5A C20417421 costs $1.46 at 100 pcs, 404 in stock. RK817-5 was not found in stock.

### Rails and sequencing (RK3566)

- **Rails** (HDG66 PDF p.30, Table 2-9; DS66 p.51 Table 3-2):
  - Core rails, 0.9 V typical (0.81 V min), with DVS: VDD_CPU, VDD_GPU, VDD_NPU, VDD_LOGIC.
  - PMU_VDD_LOGIC_0V9.
  - PLL supplies at 0.9 V and 1.8 V (PMU and SYS).
  - VCC_DDR (per DRAM type).
  - IO domains PMUIO0/1/2 and VCCIO1–7 (3.3 V or 1.8 V).
  - Analog 0.9/1.8/3.3 V for USB2, MIPI, HDMI, eDP and the multi-PHY. Unused PHYs still need their supplies, or the matching DT nodes must be disabled (HDG66 PDF p.38).
- **Power-up order** (HDG66 PDF p.30–31, printed p.27–28):
  1. VDDA0V9_PMU / VDDA_0V9 / VDD_LOGIC
  2. VCCA1V8_PMU / VCC_1V8 / VCC3V3_PMU / VDD_GPU
  3. VDD_CPU
  4. VCC_DDR
  5. VCC_3V3
  6. RESETn, released at least 10 ms after the last rail.

  The general rule is lower voltage first within a module. RESETn must go low before PMUIO1 drops below 2.93 V.
- **Rails that must stay on in standby** (HDG66 PDF p.31): VCC_DDR (self-refresh), VDDA0V9_PMU, VCCA1V8_PMU and VCC3V3_PMU. Wake-up then works only from PMUIO0/1/2 pins.

### Power figures

**From Rockchip (PWR356X):**

- **RK3566 tablet** (RK3566 + RK817, 4 GB LPDDR4; measured at VBAT 3.8 V, so PMIC losses are included):

  | State | Power | Current at 3.8 V | Notes |
  |---|---|---|---|
  | Static desktop, screen removed | 534.5 mW | 140.7 mA | VDD_LOGIC 231 mA at 0.905 V and VCC_DDR 52.5 mA are the largest loads |
  | "Primary standby" (screen off, system running) | 271.7 mW | 71.5 mA | |
  | **"Secondary standby" (suspend)** | **14.2 mW** | **3.74 mA** | |
  | 1080p video | 843 mW | | |
  | 3D games | 1.7–2.36 W | | |

- **RK3568 EVB CPU rail only:**

  | CPU load | Clock | VDD_CPU current | Voltage |
  |---|---|---|---|
  | One core | 408 MHz | 106 mA | 0.836 V |
  | Four cores | 1200 MHz | 878 mA | 0.833 V |
  | Four cores | 1992 MHz | 2233 mA | 1.16 V (≈ 2.6 W) |

**From board vendors and reviews:**

- **Pine64 Quartz64 Model B:** "under 2 W" idle (powertop tunables not set) and "under 5 W" with `stress-ng -c4` (https://wiki.pine64.org/wiki/Quartz64).
- **Geniatech XPI-3566-Zero:** about 1.0 W idle and 1.54 W peak, measured with a USB tester on an older kernel (https://taoofmac.com/space/blog/2024/09/16/1600).
- **Radxa ZERO 3W:** Radxa publishes no figure; the product brief asks for a 5 V/2 A supply. Third-party reviews quote about 1.8–2.3 W idle with Wi-Fi up and about 3 W, up to 4 W under load. **UNVERIFIED** (search snippets from https://site-easygoingnerd-com.pages.dev/review/radxa-zero-3w-review/ and https://magazinmehatronika.com/radxa-zero-3w-recenzija).
- **Mainline Linux suspend on RK3566:** I found no measured figure. Pine64 forum threads ask whether s2ram works (https://forum.pine64.org/showthread.php?tid=14976). **UNVERIFIED.**

**RV1106 for comparison:**

- RV-PWR (RV1106G EVB with 2K camera, NPU and audio, SoC side): **731.7 mW at 25 °C** and 876 mW at 60 °C ambient.
  - VDD_0V9 478.5 mA at 0.88 V; VCC_DDR 92.5 mA at 1.376 V.
  - The report has no idle or suspend number.
- A Luckfox forum user reports the Pico Pi (RV1106G3) at about 0.3 W in sleep. **UNVERIFIED:** the page returned 403, and this is a search-snippet figure (https://forums.luckfox.com/viewtopic.php?p=8201).
- An element14 thread reports ≥ 70 mA deep sleep on a Luckfox RV1103 board. **UNVERIFIED** (https://community.element14.com/technologies/internet-of-things/f/forum/56442/).

**INFERENCE:** the RK3566 can probably idle near the RV1106 if it is clocked down. In Rockchip's own tablet data, the
awake floor (about 270 mW at VBAT, screen off) sits below the RV1106 heavy-camera figure. The cost is a PMIC-based
standby design, external DRAM and DVS rails. The big RK3566 advantage is a documented 14 mW suspend with the RK817.
That needs Rockchip's PMIC_SLEEP scheme and vendor firmware. Its status on mainline is **UNVERIFIED**.

---

## 4. Boot and interfaces (RK3566)

- **Boot order** (HDG66 PDF p.17, printed p.14): FSPI NOR → FSPI NAND → NAND → eMMC → **SDMMC card**; if none boots, USB OTG0 maskrom. The datasheet lists SPI flash, NAND, eMMC and SDMMC as boot devices (DS66 p.8 §1.2.4).
  - **A microSD-only boot is supported.**
  - The Quartz64 Zero lists "bootable SDHC/SDXC MicroSD card" with eMMC and SPI flash optional (cnx-software link in §1).
- **Footgun, `SDMMC0_DET`:** this pin selects SDMMC or JTAG/UART on the SD pins at reset. It must read **low**, as a card-detect switch pulls it, or SDMMC0 boot fails (HDG66 PDF p.18).
- **Second footgun, `FLASH_VOL_SEL`:** this pin sets the VCCIO2 level at reset (HDG66 PDF p.17).
- **SD/SDIO controllers:**
  - SDMMC0, SDMMC1 and SDMMC2: three 4-bit SD3.0/SDIO3.0 controllers, plus a separate eMMC 5.1 controller (DS66 p.8, p.15).
  - The guide recommends SDMMC0 for the boot card. SDMMC1 and SDMMC2 can also take SD cards, but are "more often used as SDIO for Wi-Fi" (HDG66 PDF p.47–48).
  - SDIO 3.0 needs VCCIO_WL at 1.8 V; SDIO 2.0 uses 3.3 V.
  - **HaLow on SDMMC1 plus a boot SD on SDMMC0 fits, leaving SDMMC2 spare.** The RV1106 has one SDIO controller plus SDMMC0 (RV-DS22 p.14).
- **SPI:** four SPI controllers, master or slave (DS66 p.16). There is also one FSPI for boot flash (HDG66 PDF p.27).
- **UART:** ten UARTs, up to 4 Mbps; UART0/1/3/4/5 have flow control (DS66 p.16).
- **USB:**
  - One USB 2.0 OTG (OTG0) plus USB 2.0 hosts and a USB 3.0 host (DS66 p.15; HDG66 PDF p.49).
  - OTG0_ID has an internal pull-up of about 200 kΩ, "so the OTG interface defaults to Device mode". VBUSDET goes through a divider (HDG66 PDF p.50).
  - Download mode runs over OTG0 in device mode (DS66 p.8). **USB gadget to a laptop is supported.**

---

## 5. Operating temperature

| Part | Ambient range | Source |
|---|---|---|
| RK3566 | **0 to 80 °C** (Tj max 125 °C) | DS66 p.52 Table 3-2, p.58; LCSC C2943786 also lists 0–80 °C |
| RK3568J (industrial) | **−40 to 85 °C**, CPU 1.4 GHz normal and 1.8 GHz overdrive | DS68J p.55, p.54 |
| RK3566 industrial variant | **none found** | Search results, and Radxa's "CM3J" industrial module uses the RK3568J (https://www.cnx-software.com/2025/03/27/radxa-cm3j-industrial-grade-rockchip-rk3568j-som-is-compatible-with-raspberry-pi-compute-module-4/) |
| RK3566T | lower clock (1.6 GHz vs 1.8 GHz), **not** an industrial grade | cnx-software Quartz64 Zero article |
| RV1106 | **0 to 80 °C** in Datasheet V1.3 (RV-DS13 p.21); **−20 to 85 °C** in Datasheet V2.2, 2026 (RV-DS22 p.27) | local files |

The RK3568J uses the 19 × 19 mm FCCSP636L package, so it is not a drop-in replacement for the RK3566.

---

## 6. Open reference designs

### With PCB layout source

| Design | SoC / DRAM | Format | Layers | License | Status | Link |
|---|---|---|---|---|---|---|
| Rockchip RK3568 DDR4 template (2× DDR4 x16, 1600 MHz) | RK3568 | PADS .asc/.pcb, Allegro .brd, OrCAD .DSN | 4 | none stated; Rockchip document re-uploaded | Rockchip reference | https://github.com/hqnicolas/RK3568-hardware-design/tree/main/02_DDR%20Template |
| Rockchip RK3568 DDR3 template (4× x16, `DDR3P416DD6`) | RK3568 | PADS/Allegro | 6 (from name, **UNVERIFIED**) | as above | Rockchip reference | same repo |
| Rockchip RK3568 NVR demo `DDR4P216SD4` | RK3568, DDR4, discrete power | Allegro .brd + schematic | 4 (from name, **UNVERIFIED**) | as above | Rockchip reference | same repo, `04_Product Line Branch(NVR)` |
| LCSC/LCKFB **Taishanpi (泰山派)** | RK3566, LPDDR4 | EasyEDA Pro (open project) | not stated (**UNVERIFIED**) | **GPL-3.0** | volume product; mainline DT `rk3566-lckfb-tspi.dts` | https://oshwlab.com/lckfb-team/taishanpi ; https://wiki.lckfb.com/en/tspi-rk3566/open-source-hardware/ |
| oshwhub "RK3566最小系统（四层板）" | RK3566, LPDDR4 x32, RK809-5 | EasyEDA | **4** (JLC 3313) | GPL-3.0, plus "no reposting without permission" | hand-built, boots; author lists known faults | https://oshwhub.com/mizewei/rk3566-zui-xiao-xi-tong |
| hw-myry/rk3566-devkit | RK3566, LPDDR4 | Altium (.PcbDoc) | 6 | none | photo of an assembled board in repo; bring-up state unknown | https://github.com/hw-myry/rk3566-devkit |
| CopperPilot/tablet | RK3566, LPDDR4X | **KiCad 10** | 8 (0.8 mm) | CERN-OHL-S-2.0 | AI-generated, "**not yet built**", not powered on: not a proven routing reference | https://github.com/CopperPilot/tablet |
| EEWorld/oshwhub RK3568 "four-layer JLCPCB free process" boards (IDs 91965, 91963) | RK3568, LPDDR4/4X | Altium/PADS | 4 | not confirmed | page notes BOM errors | https://en.eeworld.com.cn/Reference_Designs/detail/91965 ; .../91963 (content did not load for me; from search snippets, **UNVERIFIED**) |

### Schematics only (PDF)

- Radxa ZERO 3W and 3E, CM3 and CM3S: https://docs.radxa.com/en/zero/zero3/download and https://dl.radxa.com/ . Radxa's docs site footer says the docs are CC BY 4.0. The hardware files carry no separate license.
- Pine64 Quartz64 A, B and Zero, and SOQuartz: https://wiki.pine64.org/wiki/Quartz64
- ASUS Tinker Board 3: https://tinker-board.asus.com/download/TINKER_BOARD_3_schematic.pdf

### Open-source KiCad RK3566 projects on GitHub

The only one found (GitHub search for `rk3566 kicad`, 2026-11-20) is CopperPilot/tablet, which is unbuilt. Radxa's
`radxa-som-projects` holds carrier boards, not chip-down designs.

**Best real routing references:**

1. Rockchip's 4-layer DDR4 template (TPL4L), an RK3568 design but with Rockchip's own 4-layer DDR4 rules, vias and trace widths.
2. Taishanpi (GPL-3.0, RK3566 with LPDDR4, mainline-supported).
3. The 4-layer oshwhub minimum system.

None is KiCad, and none is an RK3566 with a 16-bit DDR4 or DDR3L bus.

---

## 7. Linux support

- **RK3566 in mainline:** Linux master (7.4-rc3 on 2026-11-20) carries about 50 `rk3566-*.dts` files in `arch/arm64/boot/dts/rockchip/`. They include `rk3566-radxa-zero-3w/3e`, `rk3566-quartz64-a/b`, `rk3566-soquartz-*`, `rk3566-orangepi-3b-*`, `rk3566-lckfb-tspi`, `rk3566-rock-3c`, `rk3566-pinenote-*` and `rk3566t.dtsi` (GitHub API listing of torvalds/linux).
  - Gaps: the NPU has no mainline driver, and the ISP is "WIP (paused)" in Collabora's FOSDEM 2026 status (https://fosdem.org/2026/events/attachments/KLFW73-no-line-like-mainline-rockchip/slides/267550/no-line-l_vrjwxmj.pdf ; https://fosdem.org/2026/events/attachments/WFZJ7U-upstream-video-capture-camera-support-rk35xy/slides/265550/fosdem26-_s0baivr.pdf).
  - Klepon needs none of the NPU, ISP or VPU.
- **RV1106 in mainline:** **not merged.** `arch/arm/boot/dts/rockchip/` has only `rv1103b*`, `rv1108`, `rv1109` and `rv1126`.
  - An RV1106/RV1103 series reached v3 on 2026-07-29 (https://lkml.iu.edu/2607.3/10715.html). Its clock driver is ported from the vendor kernel, with "no resets exposed yet", per the search snippet of https://lists.infradead.org/pipermail/linux-rockchip/2026-July/073079.html.
  - Today the RV1106 depends on Rockchip/Luckfox's vendor 5.10 kernel.
- **batman-adv:** mainline since 2.6.38, documented at https://docs.kernel.org/networking/batman-adv.html.
  - The Rockchip vendor 5.10 kernel has `net/batman-adv/Kconfig` with `BATMAN_ADV_BATMAN_V` (https://raw.githubusercontent.com/rockchip-linux/kernel/develop-5.10/net/batman-adv/Kconfig).
  - The Luckfox Pico SDK kernel tree also contains `net/batman-adv/` (https://github.com/LuckfoxTECH/luckfox-pico, `sysdrv/source/kernel/net/batman-adv/Kconfig` returns HTTP 200).
  - **It is straightforward on both.** On the RV1106 it is a kernel config change in the vendor SDK. On the RK3566 it is stock mainline.
  - Whether the default Luckfox defconfig enables it is not checked. **UNVERIFIED.**

---

## Cost snapshot (not asked, but the project ranks cost first)

LCSC live API, fetched 2026-11-20; RV1106G3 from the cached LCSC JSON of the same day (`scratch/lcsc/C5328706.json`).

| Part | LCSC | Price |
|---|---|---|
| RK3566 | C2943786 | $14.23 (1) / **$9.57 (102)**; 691 in stock |
| RV1106G3 (256 MB DDR3L in package, RV-DS22 p.7) | C5328706 | $23.87 (1) / **$21.14 (30)**; 1,933 in stock |
| RK809-5A | C20417421 | $1.46 (100) |
| DDR4 4 Gb x16 (512 MB), K4A4G165WF-BCTD | C2803249 | $14.01 (112); 111 in stock |
| DDR3 (1.5 V) 2 Gb x16 (256 MB), W632GG6NB-09 | C2641277 | $7.12 (100) |
| DDR3L 4 Gb x16 (512 MB), MT41K256M16TW-107:P | C253882 | $15.94 (100) |
| LPDDR4X 8 Gb x32 (1 GB), W66DP2RQQAGJ | C46681826 | $34.03 (30) |

**INFERENCE:**
- RK3566 + one DDR4 x16 (512 MB, which needs the unproven 16-bit mode) + RK809 comes to about $25.
- RK3566 + 1 GB x32 LPDDR4X + RK809 comes to about $45.
- Both compare with about $21 for the RV1106G3 alone.
- These figures exclude the extra PCB layers and the DRAM decoupling.
- DRAM prices are high in this snapshot.
