# RV1106 pin map (draft)

Status: draft, 2026-11-20. Checked against `Rockchip RV1106G_PinOut_V1.1_20220507.xlsx` (sheet 06), RV1103G/RV1106G Hardware Design Guide V1.1, `Heltec_HT-HC01_V2.pdf` p.7–9, `esp32_datasheet_en.pdf` p.15 and the ESP32 / ESP32-C5 module strapping tables. It is final once the SoC sheet is drawn and ERC is clean.

## Constraints that set this map

- **One SDIO controller** with two pin options that can't both be used: `_M0` on GPIO2_A (VCCIO5) and `_M1` on GPIO1_C (VCCIO6) (guide §2.3.2).
- **SPI0 has only `_M0`**, on GPIO1_C0–C3, the same pins as SDIO `_M1`. So HaLow uses SDIO `_M0`.
- **SPI1 `_M0`** is on the EMMC_D4–D7 pins (GPIO4_A). Those pins are free because LinkNode has no on-board flash (requirement H-10).
- **Boot order** is SFC/SPI flash, then eMMC, then the SD card (guide §2.1.3). With no flash fitted, the board boots from the SD card. The C5 enable and boot pins are kept off the FSPI/eMMC pins that the boot ROM probes.
- **SDMMC_DET low** (card present) switches the SDMMC pins from JTAG/UART to SD (guide §2.1.4).
- **IO voltages:** VCCIO1, 3, 4, 5 and 6 run at 3.3 V. VCCIO4 is fixed at 3.3 V, so the SD card runs in SD 2.0 mode with no 1.8 V UHS switching. VCCIO7 (camera) stays at 1.8 V and is unused.

## Pin assignments

| Group | RV1106 pin | GPIO | Function | Net | Connects to | Peer pin | Note |
|---|---|---|---|---|---|---|---|
| SD card | 15 | GPIO3_A4 | SDMMC_CLK | SD_CLK | microSD | CLK | 22 Ω series (Rockchip guide Table 2-7) |
| SD card | 16 | GPIO3_A5 | SDMMC_CMD | SD_CMD | microSD | CMD |  |
| SD card | 14 | GPIO3_A3 | SDMMC_D0 | SD_D0 | microSD | DAT0 |  |
| SD card | 12 | GPIO3_A2 | SDMMC_D1 | SD_D1 | microSD | DAT1 |  |
| SD card | 18 | GPIO3_A7 | SDMMC_D2 | SD_D2 | microSD | DAT2 |  |
| SD card | 17 | GPIO3_A6 | SDMMC_D3 | SD_D3 | microSD | CD/DAT3 |  |
| SD card | 11 | GPIO3_A1 | SDMMC_DET | SD_DET | microSD | card-detect switch | Low = card inserted, selects SDMMC over JTAG/UART (guide §2.1.4) |
| HaLow | 111 | GPIO2_A2 | SDIO_CLK_M0 | HALOW_SDIO_CLK | HT-HC01 V2 | PAD_18 MM_SDIO_CLK | 22 Ω series (guide Table 2-8) |
| HaLow | 112 | GPIO2_A3 | SDIO_CMD_M0 | HALOW_SDIO_CMD | HT-HC01 V2 | PAD_21 MM_SDIO_CMD | 10k–100k pull-up (Heltec pin notes) |
| HaLow | 110 | GPIO2_A1 | SDIO_D0_M0 | HALOW_SDIO_D0 | HT-HC01 V2 | PAD_17 MM_SDIO_D0 | pull-up |
| HaLow | 109 | GPIO2_A0 | SDIO_D1_M0 | HALOW_SDIO_D1 | HT-HC01 V2 | PAD_16 MM_SDIO_D1 | pull-up |
| HaLow | 114 | GPIO2_A5 | SDIO_D2_M0 | HALOW_SDIO_D2 | HT-HC01 V2 | PAD_23 MM_SDIO_D2 | pull-up |
| HaLow | 113 | GPIO2_A4 | SDIO_D3_M0 | HALOW_SDIO_D3 | HT-HC01 V2 | PAD_22 MM_SDIO_D3 | pull-up |
| HaLow | 107 | GPIO2_A6 | GPIO out | HALOW_RESET_N | HT-HC01 V2 | PAD_35 RESET_N | active low |
| HaLow | 106 | GPIO2_A7 | GPIO out | HALOW_WAKE | HT-HC01 V2 | PAD_36 WAKE |  |
| HaLow | 105 | GPIO2_B0 | GPIO in | HALOW_BUSY | HT-HC01 V2 | PAD_34 MM_GPIO_0 (BUSY) | needed for power save |
| HaLow | 104 | GPIO2_B1 | GPIO out | HALOW_PWR_EN | Radio Power | TLV62569 EN (VBAT + VDD_IO) | default pull-down keeps HaLow off at boot |
| HaLow | 72 | GPIO1_A0 | GPIO out | HALOW_FEM_EN | Radio Power | VDD_FEM P-FET switch | 5 V front-end |
| ESP32 | 94 | GPIO1_C1 | SPI0_CLK_M0 | ESP32_SPI_CLK | ESP32-WROOM-32UE | GPIO18 (VSPICLK) | IO_MUX pins, ESP32 datasheet p.15 |
| ESP32 | 93 | GPIO1_C2 | SPI0_MOSI_M0 | ESP32_SPI_MOSI | ESP32-WROOM-32UE | GPIO23 (VSPID) |  |
| ESP32 | 92 | GPIO1_C3 | SPI0_MISO_M0 | ESP32_SPI_MISO | ESP32-WROOM-32UE | GPIO19 (VSPIQ) |  |
| ESP32 | 95 | GPIO1_C0 | SPI0_CS0_M0 | ESP32_SPI_CS | ESP32-WROOM-32UE | GPIO5 (VSPICS0) | GPIO5 is a strap pin; CS idles high |
| ESP32 | 91 | GPIO1_C4 | GPIO in | ESP32_HANDSHAKE | ESP32-WROOM-32UE | GPIO26 | ESP ready for next transfer |
| ESP32 | 90 | GPIO1_C5 | GPIO in | ESP32_DATA_READY | ESP32-WROOM-32UE | GPIO27 | ESP has a frame for Linux |
| ESP32 | 89 | GPIO1_D0 | UART3_TX_M1 | ESP32_UART_RX | ESP32-WROOM-32UE | U0RXD (GPIO3) | console + esptool |
| ESP32 | 87 | GPIO1_D1 | UART3_RX_M1 | ESP32_UART_TX | ESP32-WROOM-32UE | U0TXD (GPIO1) |  |
| ESP32 | 83 | GPIO1_C6 | GPIO out (open drain) | ESP32_EN | ESP32-WROOM-32UE | EN | 10k pull-up + 1 µF on EN |
| ESP32 | 84 | GPIO1_C7 | GPIO out (open drain) | ESP32_BOOT | ESP32-WROOM-32UE | GPIO0 | 10k pull-up; low at reset = download mode (Table 6) |
| ESP32 | 73 | GPIO1_A1 | GPIO out | ESP32_PWR_EN | Radio Power | TLV62569 EN |  |
| ESP32-C5 | 38 | GPIO4_A7 | SPI1_CLK_M0 | C5_SPI_CLK | ESP32-C5-WROOM-1U | SPI slave CLK (GPIO matrix) | C5 pins chosen on its sheet |
| ESP32-C5 | 45 | GPIO4_A1 | SPI1_MOSI_M0 | C5_SPI_MOSI | ESP32-C5-WROOM-1U | SPI slave MOSI |  |
| ESP32-C5 | 46 | GPIO4_A0 | SPI1_MISO_M0 | C5_SPI_MISO | ESP32-C5-WROOM-1U | SPI slave MISO |  |
| ESP32-C5 | 40 | GPIO4_A5 | SPI1_CS0_M0 | C5_SPI_CS | ESP32-C5-WROOM-1U | SPI slave CS |  |
| ESP32-C5 | 44 | GPIO4_A2 | GPIO in | C5_HANDSHAKE | ESP32-C5-WROOM-1U | GPIO (TBD) |  |
| ESP32-C5 | 42 | GPIO4_A3 | GPIO in | C5_DATA_READY | ESP32-C5-WROOM-1U | GPIO (TBD) |  |
| ESP32-C5 | 85 | GPIO1_D3 | UART5_TX_M1 | C5_UART_RX | ESP32-C5-WROOM-1U | U0RXD | console + esptool |
| ESP32-C5 | 86 | GPIO1_D2 | UART5_RX_M1 | C5_UART_TX | ESP32-C5-WROOM-1U | U0TXD |  |
| ESP32-C5 | 74 | GPIO1_A2 | GPIO out (open drain) | C5_EN | ESP32-C5-WROOM-1U | EN (CHIP_PU) | 10k pull-up + 1 µF |
| ESP32-C5 | 77 | GPIO1_B0 | GPIO out (open drain) | C5_BOOT | ESP32-C5-WROOM-1U | GPIO28 | 10k pull-up; low at reset = download mode (Table 4-3) |
| ESP32-C5 | 75 | GPIO1_A3 | GPIO out | C5_PWR_EN | Radio Power | TLV62569 EN |  |

## Other SoC pins

| Use | Pin | GPIO / function |
|---|---|---|
| Debug console header | 79 / 80 | GPIO1_B2 UART2_TX_M1 / GPIO1_B3 UART2_RX_M1 |
| Charger I²C | 5 / 7 | GPIO3_C7 I2C4_SCL_M2 / GPIO3_D0 I2C4_SDA_M2 (VCCIO7, **1.8 V only**), 10k pull-ups R504/R505 to VCC_1V8. Moved from pins 64/65 (I2C1_M0) on 2026-11-26 (T69): those pins are boxed in at the chip's south-east corner once VCC_DDR takes the corridor under the chip. BQ25798 VIH 1.3 V with a 1.8 V pull-up rail (`hardware/datasheets/TI_BQ25798.pdf` p.16–17). Linux device tree: `&i2c4 { pinctrl-0 = <&i2c4m2_xfer>; }` instead of i2c1m0. Pins 64/65 unused |
| Charger interrupt | 60 | GPIO0_A2 (CHG_INT) |
| USB to laptop | 27 / 26 / 25 | USB_DP / USB_DM / USB_VBUSDET |
| Still free | 41, 39, 47, 48, 76, 78, 58, 59, 62, 63 | GPIO4_A4, A6, B0, B1 (probed by the boot ROM), GPIO1_A4, GPIO1_B1, GPIO0_A0, A3, A4 |

## Firmware notes

- When a radio is powered off, drive its RV1106 pins low or switch them to inputs. Otherwise the internal pull-ups back-power the module through its IO diodes.
- The ESP EN and BOOT lines are open drain with external pull-ups. To enter download mode, hold BOOT low, pulse EN low, then run esptool over that ESP's UART.


## Update 2026-11-20: the original ESP32 is replaced by a GPS (T18)

The ESP32 rows above (SPI0_M0 on GPIO1_C, UART3_M1, EN/BOOT and PWR_EN) no longer apply. **Proposed** GPS pins,
which reuse pins the ESP32 freed. They are to be confirmed on the SoC sheet (T11), including that the bank
(VCCIO6) runs at 3.3 V to match the module's 3.3 V I/O:

| GPS net | RV1106 pin | GPIO | Function | ATGM336H pin |
|---|---|---|---|---|
| GPS_TXD | 87 | GPIO1_D1 | UART3_RX_M1 | TXD0 (2) |
| GPS_RXD | 89 | GPIO1_D0 | UART3_TX_M1 | RXD0 (3) |
| GPS_PPS | 91 | GPIO1_C4 | GPIO in | 1PPS (4) |
| GPS_PWR_EN | 73 | GPIO1_A1 | GPIO out | ME6211 CE (100k pull-down) |

SPI0 is now unused, which removes the SPI0_M0 / SDIO_M1 overlap on GPIO1_C.

## As drawn on the SoC sheets (T11, 2026-11-20)

Final for Rev 1, matching `hardware/kicad/soc.kicad_sch` (U100 units 2–5) and the netlist. Changes from the tables above:

- **C5_HANDSHAKE → pin 90 GPIO1_C5 and C5_DATA_READY → pin 83 GPIO1_C6** (were pins 44 and 42). Pins 44/42 are FSPI_D2/D1, which the boot ROM may drive while it probes for SPI flash. The VCCIO3 FSPI/eMMC pins 39, 41, 42, 44, 47 and 48 are left unconnected.
- **GPS confirmed** on pins 87 (GPS_TXD → UART3_RX_M1), 89 (GPS_RXD ← UART3_TX_M1), 91 (GPS_PPS) and 73 (GPS_PWR_EN). VCCIO1 and VCCIO6 are 3.3 V, matching the module.
- **SD card power:** the card VDD is on VCC_3V3 directly (T71, owner 2026-11-26). The REF p.19 switch (AO3401A Q401 on SD_PWREN, pin 59) was removed: the card is the only boot device and must be powered from reset anyway, and the Luckfox Pico and Pico Plus power TF1 straight from VCC_3V3. A hung card is recovered by power-cycling the node (BQ25798 System Power Reset, `TI_BQ25798.pdf` p.73). Pin 59 (GPIO0_A1) is free.
- **SARADC_IN0** (pin 23): 10k to VCC_1V8 + 1 nF, with test pad TP501 "RECOVERY" (short it to GND at boot for Rockusb). SARADC_IN1 is unconnected.
- **Debug console:** UART2_M1 pins 79/80 to J501, a 3-pin header (not fitted).
- **Unused, no-connect:** pins 58, 62, 63 (GPIO0_A0/A3/A4), 76, 78, 92–95, 84, and all VCCIO7 camera, FEPHY and codec signal pins.
- **IO supplies:** VCCIO1/3/4/5/6 and PMU at 3.3 V. VCCIO7 (MIPI_AVDD1V8) at 1.8 V through 1 Ω.

## ESP32-C5 side (T13, 2026-11-20)

| Net | RV1106 pin | C5 module pin | C5 GPIO / function |
|---|---|---|---|
| C5_SPI_CLK (22 Ω R512 at the SoC) | 38 SPI1_CLK_M0 | 8 | IO6 FSPICLK (IO_MUX) |
| C5_SPI_MOSI | 45 SPI1_MOSI_M0 | 9 | IO7 FSPID |
| C5_SPI_MISO | 46 SPI1_MISO_M0 | 4 | IO2 FSPIQ |
| C5_SPI_CS | 40 SPI1_CS0_M0 | 12 | IO10 FSPICS0 |
| C5_HANDSHAKE | 90 GPIO1_C5 | 21 | IO23 |
| C5_DATA_READY | 83 GPIO1_C6 | 23 | IO24 |
| C5_UART_TX (C5 → RV1106) | 86 UART5_RX_M1 | 25 | TXD0 |
| C5_UART_RX (RV1106 → C5) | 85 UART5_TX_M1 | 24 | RXD0 |
| C5_EN (10k pull-up + 1 µF) | 74 GPIO1_A2 | 3 | EN (CHIP_PU) |
| C5_BOOT (10k pull-up) | 77 GPIO1_B0 | 15 | IO28 strap: 1 = SPI boot, 0 = joint download (datasheet p.18) |

Straps GPIO26/27/25, GPIO7 and MTMS/MTDI keep their defaults. GPIO7 and MTMS (IO2) are SPI pins, but they only set the JTAG source and the SDIO clock edge, which are unused with the default eFuses. Unused C5 pins are left unconnected. Pin 19 (IO15) is the PSRAM chip select on the N16R8 and must stay unconnected.
