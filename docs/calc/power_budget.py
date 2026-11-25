"""LinkNode Rev 1 power budget (T19). Every figure is cited in docs/power-budget.md; EST values are marked there.
Run: python3 docs/calc/power_budget.py"""
VBAT = 3.7          # nominal 1S Li-ion
ETA_BOOST = 0.90    # TPS61089 VSYS -> 5.04 V at 0.1-1 A (EST, datasheet efficiency curves)
ETA_BUCK = {'0V9': 0.78, '1V35': 0.85, '1V8': 0.85, '3V3': 0.90}   # TLV62569 from 5 V (EST)
ETA_LDO_GPS = 3.3 / VBAT                                            # ME6211 from VSYS: linear
def from_batt(p_w, rail):
    if rail == '5V': return p_w / ETA_BOOST
    if rail == 'GPS': return p_w / ETA_LDO_GPS
    return p_w / (ETA_BOOST * ETA_BUCK[rail])

# --- loads (W at the rail) ---
SOC_IDLE = {'0V9': 0.88 * 0.190, '1V35': 1.36 * 0.060, '1V8': 1.8 * 0.020, '3V3': 3.3 * 0.020}   # EST, no camera/NPU/VPU
SOC_HEAVY = {'0V9': 0.88 * 0.4785 + 0.836 * 0.0401, '1V35': 1.376 * 0.0925, '1V8': 1.788 * 0.020, '3V3': 3.297 * 0.0346}  # Rockchip report, 25 C
HALOW_LISTEN = {'3V3': 3.3 * 0.032, '5V': 5.0 * 0.017}     # 4 MHz listen, LNA on (p.13)
HALOW_TX = {'3V3': 3.3 * 0.051, '5V': 5.0 * 0.400}         # MCS0 27 dBm 1 MHz, max (p.12)
C5_RX = {'3V3': 3.3 * 0.087}                               # 2.4 GHz RX (Table 6-4)
C5_TX = {'3V3': 3.3 * 0.313}                               # 802.11b 19 dBm peak (Table 6-4)
GPS = {'GPS': 3.3 * 0.026 + 3.3 * 0.010}                   # module 26 mA (p.8) + active antenna 10 mA (EST)
def total(*loads):
    return sum(from_batt(p, r) for L in loads for r, p in L.items())
OFF_mA = 0.017 + 0.4 + (3.3 - 1.25) / 10e3 * 1e3 + VBAT / 532e3 * 1e3 + 0.003 + 0.011 + 0.0001 * 6   # BQ, LM2903, TL432 bias, divider, DW01A, GPS backup, bucks off
ON_Q_W = OFF_mA / 1e3 * VBAT + 5.04 * 100e-6 / ETA_BOOST + 6 * 35e-6 * 5.04 / ETA_BOOST

soc_idle = total(SOC_IDLE); soc_heavy = total(SOC_HEAVY)
listen = total(SOC_IDLE, HALOW_LISTEN, C5_RX, GPS) + ON_Q_W
listen_nogps = total(SOC_IDLE, HALOW_LISTEN, C5_RX) + ON_Q_W
print('SoC idle from battery %.2f W (heavy %.2f W)' % (soc_idle, soc_heavy))
for n, L in (('HaLow listen', HALOW_LISTEN), ('C5 RX', C5_RX), ('GPS', GPS)): print('%-13s %.3f W from battery' % (n, total(L)))
print('All listening, GPS on   %.2f W = %.1f Wh/day' % (listen, listen * 24))
print('All listening, GPS off  %.2f W = %.1f Wh/day' % (listen_nogps, listen_nogps * 24))
print('Node off (hold-off) %.2f mA = %.3f Wh/day' % (OFF_mA, OFF_mA / 1e3 * VBAT * 24))
# --- peaks on the 5 V bus (A) ---
peak5 = (0.400 + 3.3 * 0.313 / (5.04 * ETA_BUCK['3V3']) + 3.3 * 0.051 / (5.04 * ETA_BUCK['3V3'])
         + 0.882 * 1.085 / (5.04 * ETA_BUCK['0V9']) + 1.363 * 0.2425 / (5.04 * ETA_BUCK['1V35'])
         + 1.816 * 0.0389 / (5.04 * ETA_BUCK['1V8']) + 3.286 * 0.0944 / (5.04 * ETA_BUCK['3V3']))
print('5 V bus worst case %.2f A; battery at 3.0 V: %.2f A (+GPS 0.10 A peak)' % (peak5, peak5 * 5.04 / ETA_BOOST / 3.0))
# --- solar ---
PSH, DERATE, ETA_CHG = 4.0, 0.75, 0.90
for P in (2.0, 3.5):
    E = P * PSH * DERATE * ETA_CHG
    off_e = OFF_mA / 1e3 * VBAT * 24
    D = (E - off_e) / (listen * 24 - off_e)
    print('Panel %.1f W: %.1f Wh/day harvested -> listening duty <= %.0f %% (%.1f h/day)' % (P, E, D * 100, D * 24))
print('Panel for 24 h listening: %.1f W' % (listen * 24 / (PSH * DERATE * ETA_CHG)))
for d in (0.25,):
    e = listen * 24 * d + OFF_mA / 1e3 * VBAT * 24 * (1 - d)
    print('At %d %% duty: %.1f Wh/day; 3 days without sun %.1f Wh -> %.1f x 3.5 Ah 18650 (12.6 Wh, 80 %% usable)' % (d * 100, e, 3 * e, 3 * e / (12.6 * 0.8)))
