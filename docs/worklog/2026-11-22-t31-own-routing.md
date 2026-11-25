# 2026-11-22: T31, RV1106 routed without Freerouting

- **Owner:** clear absolutely every track and via (fan-out, USB pair and GND stitching included) and route only the RV1106 again, without Freerouting.
- **Start state:** main board after T30 (backup `pcb_pre_t30_usb` and the T30 result itself kept as `pcb_t30_final`).
- **Cleared** every track and via on a copy (`scratch/t31`): 2193 removed, 157 RV1106 connections open.
- **New `hardware/tools/fanout.py`:** re-creates the U100 fan-out with parts unmoved.
  - GND stubs 37/57; 29 ring vias (pin 52 none).
  - 32 straight bottom links (C619, C628, R503 left for the router).
  - Y501 GND vias at 1.38 mm. DRC clean, 114 open.
- **USB pair:** usbpair (no Freerouting), attempt 0. R508/R509 at (138.2, 145.3), SoC skew 0.27.
  - Signal path matched with `tune.py add` (+1.80 mm on D+): 31.80 / 31.80 mm.
- **New `hardware/tools/t31_route.py`:** escape stubs, then signal nets (0.5 mm from the USB pair), then local rails (0.2 mm, both ends within 15 mm of U100).
  - netroute gained `pair_filter` and per-net `widths`.
- **Owner:** walk through section by section, with an HTML report (images, route, reference) per section, and wait for approval before each next one.
  - Stopped the full `t31_route.py` run (killed by PID). It had saved partial routes, so the copy was restored to the post-USB state (`usb_tuned`).
- **Sections:**
  1. fan-out
  2. USB
  3. SDIO
  4. microSD
  5. crystals and system corner
  6. ESP32-C5 link
  7. GPS, I2C and enables
  8. local rails and ground
  9. final checks
- **Walkthrough page:** `docs/reports/t31-walkthrough/` (source `docs/reports/t31-walkthrough/`). Sections 1–2 shown, awaiting approval.
  - State: DRC clean, 108 RV1106 connections open, USB path skew 0.00 mm.
