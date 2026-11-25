"""T32 floorplan variants for t32_place.py (select with env T32_LAYOUT; default 'v1').
All numbers are floorplan mm from the board's top-left corner. The RV1106 cluster keeps its T29 arrangement and rotation
0, whose bus exits are: SDIO + HaLow control north, microSD + USB west, ESP32 link + GPS + debug east, charger I2C south.
Each layout gives: W, H; cluster placement ('v1' = old rule, or the cluster bbox's left/top); anchors (ref -> place_bb
keywords, given X0, Y0, X1, Y1, EDGE_DY); groups (sheet, [rects], anchor)."""

def _v1_anchors(X0, Y0, X1, Y1, EDGE_DY):
    return [('MH1', dict(left=X0+0.5, top=Y0+0.5)), ('MH2', dict(right=X1-0.5, top=Y0+0.5)),
            ('MH3', dict(left=X0+0.5, bottom=Y1-0.5)), ('MH4', dict(right=X1-0.5, bottom=Y1-0.5)),
            ('J3', dict(rot=270, left=X0-0.47, top=Y0+25.0)), ('J4', dict(rot=270, left=X0-0.48, top=Y0+33.75)),
            ('J2', dict(rot=0, left=X0+8.2, bottom=Y1+0.10)), ('J1', dict(right=X0+44.2, dy=EDGE_DY)),
            ('SW1', dict(left=X0+21.2, dy=EDGE_DY)), ('J401', dict(left=X0+44.6, dy=EDGE_DY)),
            ('U701', dict(rot=0, left=X0+8.5, top=Y0+0.5)), ('U801', dict(rot=0, left=X0+30.0, top=Y0+0.5)),
            ('U20', dict(rot=0, left=X0+52.0, top=Y0+8.0))]

def _square_anchors(X0, Y0, X1, Y1, EDGE_DY):
    # radios along the top (as v1), RV1106 right under the HaLow, microSD + USB-C under the RV1106, power in the right half
    return [('MH1', dict(left=X0+0.5, top=Y0+0.5)), ('MH2', dict(right=X1-0.5, top=Y0+0.5)),
            ('MH3', dict(left=X0+0.5, bottom=Y1-0.5)), ('MH4', dict(right=X1-0.5, bottom=Y1-0.5)),
            ('J3', dict(rot=90, right=X1+0.47, top=Y0+25.0)), ('J4', dict(rot=90, right=X1+0.48, top=Y0+33.75)),
            ('J401', dict(left=X0+8.0, dy=EDGE_DY)), ('J1', dict(left=X0+26.6, dy=EDGE_DY)),
            ('SW1', dict(left=X0+38.6, dy=EDGE_DY)), ('J2', dict(rot=0, left=X0+48.0, bottom=Y1+0.10)),
            ('U701', dict(rot=0, left=X0+8.5, top=Y0+0.5)), ('U801', dict(rot=0, left=X0+30.0, top=Y0+0.5)),
            ('U20', dict(rot=0, left=X0+52.0, top=Y0+8.0))]

def _long_anchors(X0, Y0, X1, Y1, EDGE_DY):
    # power | RV1106 | radios. HaLow turned 180 so its SDIO pins face the RV1106 and its RF pin faces the right end;
    # ESP32-C5 under it with SPI facing the RV1106; GPS + both U.FL in the right-hand column.
    return [('MH1', dict(left=X0+0.5, top=Y0+0.5)), ('MH2', dict(right=X1-0.5, top=Y0+0.5)),
            ('MH3', dict(left=X0+0.5, bottom=Y1-0.5)), ('MH4', dict(right=X1-0.5, bottom=Y1-0.5)),
            ('J3', dict(rot=270, left=X0-0.47, top=Y0+8.5)), ('J4', dict(rot=270, left=X0-0.48, top=Y0+17.25)),
            ('J2', dict(rot=0, left=X0+8.0, bottom=Y1+0.10)), ('SW1', dict(left=X0+17.5, dy=EDGE_DY)),
            ('J1', dict(left=X0+25.6, dy=EDGE_DY)), ('J401', dict(left=X0+36.9, dy=EDGE_DY)),
            ('U701', dict(rot=180, left=X1-39.0, top=Y0+1.5)), ('U801', dict(rot=0, left=X1-39.0, bottom=Y1-1.0)),
            ('U20', dict(rot=0, left=X1-17.0, bottom=Y1-8.5))]

def _dside_anchors(X0, Y0, X1, Y1, EDGE_DY):
    # trial C: power sheets on the underside. Top: radios on top, RV1106 under the ESP32-C5, connectors along the bottom.
    return [('MH1', dict(left=X0+0.5, top=Y0+0.5)), ('MH2', dict(right=X1-0.5, top=Y0+0.5)),
            ('MH3', dict(left=X0+0.5, bottom=Y1-0.5)), ('MH4', dict(right=X1-0.5, bottom=Y1-0.5)),
            ('J3', dict(rot=270, left=X0-0.47, top=Y0+19.0)), ('J4', dict(rot=270, left=X0-0.48, top=Y0+27.75)),
            ('J401', dict(left=X0+8.0, dy=EDGE_DY)), ('J1', dict(left=X0+30.5, dy=EDGE_DY)),
            ('SW1', dict(left=X0+42.0, dy=EDGE_DY)), ('J2', dict(rot=0, left=X0+50.2, bottom=Y1+0.10)),
            ('U701', dict(rot=0, left=X0+8.5, top=Y0+0.5)), ('U801', dict(rot=0, left=X0+30.0, top=Y0+0.5)),
            ('U20', dict(rot=90, left=X0+52.5, top=Y0+10.0))]

def _long2_anchors(X0, Y0, X1, Y1, EDGE_DY):
    # T40 B2 (owner, 2026-11-23): B with the GPS moved above the RV1106 and the RV1106 moved down, radio column = HaLow + ESP32-C5
    W = X1 - X0; CL = W - 53.5       # RV1106 cluster left edge (floorplan mm)
    return [('MH1', dict(left=X0+0.5, top=Y0+0.5)), ('MH2', dict(right=X1-0.5, top=Y0+0.5)),
            ('MH3', dict(left=X0+0.5, bottom=Y1-0.5)), ('MH4', dict(right=X1-0.5, bottom=Y1-0.5)),
            ('J3', dict(rot=270, left=X0-0.47, top=Y0+8.5)), ('J4', dict(rot=270, left=X0-0.48, top=Y0+17.25)),
            ('J2', dict(rot=0, left=X0+8.0, bottom=Y1+0.10)), ('SW1', dict(left=X0+17.5, dy=EDGE_DY)),
            ('J1', dict(left=X0+CL-4.4, dy=EDGE_DY)), ('J401', dict(left=X0+CL+6.7, dy=EDGE_DY)),
            ('U20', dict(rot=0, left=X0+CL+3.0, top=Y0+0.8)),
            ('U701', dict(rot=180, left=X1-28.0, top=Y0+1.5)), ('U801', dict(rot=0, left=X1-28.0, bottom=Y1-1.0))]

def _long3_anchors(X0, Y0, X1, Y1, EDGE_DY):
    # T40 B3 (owner, 2026-11-23): HaLow directly above the RV1106 (SDIO pins face each other), GPS top of the right column
    # above the ESP32-C5, every switching part at the power end.
    W = X1 - X0; CL = W - 53.5
    return [('MH1', dict(left=X0+0.5, top=Y0+0.5)), ('MH2', dict(right=X1-0.5, top=Y0+0.5)),
            ('MH3', dict(left=X0+0.5, bottom=Y1-0.5)), ('MH4', dict(right=X1-0.5, bottom=Y1-0.5)),
            ('J3', dict(rot=270, left=X0-0.47, top=Y0+8.5)), ('J4', dict(rot=270, left=X0-0.48, top=Y0+17.25)),
            ('J2', dict(rot=0, left=X0+8.0, bottom=Y1+0.10)), ('SW1', dict(left=X0+17.5, dy=EDGE_DY)),
            ('J1', dict(left=X0+CL-4.4, dy=EDGE_DY)), ('J401', dict(left=X0+CL+6.7, dy=EDGE_DY)),
            ('U701', dict(rot=0, left=X0+CL+1.0, top=Y0+0.5)),
            ('U20', dict(rot=0, left=X1-27.5, top=Y0+1.0)), ('U801', dict(rot=0, left=X1-28.0, bottom=Y1-1.0))]

def _long4_anchors(X0, Y0, X1, Y1, EDGE_DY):
    # T40 B4 (owner, 2026-11-23): B3 with the ESP32-C5 turned 180, the GPS section turned 90 CCW and lowered to line up
    # with the RV1106, and the HaLow turned 180 (RF pin to the right, a 1.5 mm channel kept above it for its north SDIO pads).
    W = X1 - X0; H = Y1 - Y0; CL = W - 53.5; ucy = 18.0 + 11.7          # RV1106 centre y (cluster top 18.0)
    return [('MH1', dict(left=X0+0.5, top=Y0+0.5)), ('MH2', dict(right=X1-0.5, top=Y0+0.5)),
            ('MH3', dict(left=X0+0.5, bottom=Y1-0.5)), ('MH4', dict(right=X1-0.5, bottom=Y1-0.5)),
            ('J3', dict(rot=270, left=X0-0.47, top=Y0+8.5)), ('J4', dict(rot=270, left=X0-0.48, top=Y0+17.25)),
            ('J2', dict(rot=0, left=X0+8.0, bottom=Y1+0.10)), ('SW1', dict(left=X0+17.5, dy=EDGE_DY)),
            ('J1', dict(left=X0+CL-4.4, dy=EDGE_DY)), ('J401', dict(left=X0+CL+6.7, dy=EDGE_DY)),
            ('U701', dict(rot=180, left=X0+CL+1.0, top=Y0+2.0)),
            ('U20', dict(rot=90, left=X1-27.0, top=Y0+ucy-5.95)), ('U801', dict(rot=180, left=X1-28.0, bottom=Y1-1.0))]

def _long5_anchors(X0, Y0, X1, Y1, EDGE_DY):
    # T40 B5 (owner, 2026-11-23): B4 with the GPS, the HaLow RF filter + U.FL and the ESP32-C5 moved up so the right-hand
    # mounting holes sit above/below the radio modules instead of beside them -> shorter board. CL = cluster left edge.
    W = X1 - X0; CL = W - 46.5
    return [('MH1', dict(left=X0+0.5, top=Y0+0.5)), ('MH2', dict(right=X1-0.5, top=Y0+0.5)),
            ('MH3', dict(left=X0+0.5, bottom=Y1-0.5)), ('MH4', dict(right=X1-0.5, bottom=Y1-0.5)),
            ('J3', dict(rot=270, left=X0-0.47, top=Y0+8.5)), ('J4', dict(rot=270, left=X0-0.48, top=Y0+17.25)),
            ('J2', dict(rot=0, left=X0+8.0, bottom=Y1+0.10)), ('SW1', dict(left=X0+17.5, dy=EDGE_DY)),
            ('J1', dict(left=X0+CL-4.4, dy=EDGE_DY)), ('J401', dict(left=X0+CL+8.4, dy=EDGE_DY)),   # T41 Block 1: +1.7 mm for a 2.7 mm wall to the USB-C plug
            ('U701', dict(rot=180, left=X0+CL+1.0, top=Y0+2.0)),
            ('U20', dict(rot=90, left=X0+CL+27.5, top=Y0+6.0)), ('U801', dict(rot=180, right=X1-0.5, top=Y0+19.0))]

def _long6_anchors(X0, Y0, X1, Y1, EDGE_DY):
    # T40 B6 (owner, 2026-11-23): B5 with the GPS + ESP32-C5 stack centred vertically in the right column
    a = dict((r, dict(kw)) for r, kw in _long5_anchors(X0, Y0, X1, Y1, EDGE_DY))
    H = Y1 - Y0; stack = 5.5 + 11.9 + 1.0 + 23.0          # J20 above the GPS, GPS (rot 90), gap, ESP32-C5 (rot 180)
    top = (H - stack)/2
    a['U20']['top'] = Y0 + top + 5.5; a['U801']['top'] = Y0 + top + 5.5 + 11.9 + 1.0
    return list(a.items())

LAYOUTS = {
    'v1': dict(W=70, H=64, cluster='v1', anchors=_v1_anchors, groups=[
        ('Power',           [(21.0, 23.8, 44.0, 35.6)], (32, 29.5)),
        ('Radio Power',     [(0.6, 16.6, 29.6, 23.6)], (19, 20)),
        ('USB and Charger', [(12.8, 34.6, 44.0, 54.0), (22.0, 54.0, 33.2, 63.4)], (25, 46)),
        ('Battery',         [(0.6, 24.0, 21.0, 40.0)], (12, 30)),
        ('Hold-off',        [(0.6, 38.0, 24.0, 47.6), (0.6, 47.6, 8.0, 55.8)], (12, 43)),
        ('GPS',             [(51.0, 7.6, 69.4, 23.4)], (60, 20)),
        ('Antenna',         [(0.6, 7.8, 8.2, 17.2)], (4, 11)),
        ('microSD',         [(33.6, 46.0, 45.0, 54.4)], (42, 50)),
        ('SoC',             [(30.0, 36.0, 69.4, 63.4)], (44, 46))]),
    'square': dict(W=70, H=64, cluster=dict(left=4.5, top=17.5), anchors=_square_anchors, groups=[
        ('Radio Power',     [(30.0, 24.0, 52.0, 31.0)], (42, 27)),
        ('Power',           [(30.0, 30.0, 56.0, 45.0)], (42, 37)),
        ('Battery',         [(52.0, 24.0, 69.4, 42.0)], (58, 32)),
        ('Hold-off',        [(48.0, 38.0, 69.4, 52.0)], (58, 45)),
        ('USB and Charger', [(29.0, 40.0, 62.0, 63.4)], (44, 52)),
        ('GPS',             [(51.0, 7.6, 69.4, 23.4)], (60, 20)),
        ('Antenna',         [(0.6, 7.8, 8.2, 17.2)], (4, 11)),
        ('microSD',         [(0.6, 42.0, 29.0, 48.0)], (16, 45)),
        ('SoC',             [(0.6, 17.0, 32.0, 47.0)], (18, 30))]),
    'long': dict(W=94, H=50, cluster=dict(left=29.0, top=0.5), anchors=_long_anchors, groups=lambda W, H: [
        ('Radio Power',     [(8.0, 0.6, 30.0, 10.0)], (19, 5)),
        ('Power',           [(8.0, 8.0, 30.0, 26.0)], (19, 16)),
        ('Battery',         [(0.6, 7.5, 15.0, H - 16)], (8, 20)),
        ('Hold-off',        [(0.6, H - 24, 18.0, H - 8)], (8, H - 16)),
        ('USB and Charger', [(8.0, 20.0, 38.0, H - 0.6)], (22, H - 18)),
        ('GPS',             [(W - 17, 16.0, W - 0.6, H - 0.6)], (W - 10, H - 18)),
        ('Antenna',         [(W - 17, 0.6, W - 0.6, 17.0)], (W - 12, 10)),
        ('microSD',         [(36.0, 24.5, 57.0, H - 16.2)], (47, 27)),
        ('SoC',             [(30.0, 0.6, 57.0, H - 16)], (42, 20))]),
    'dside': dict(W=67, H=60, cluster=dict(left=30.0, top=24.5), anchors=_dside_anchors,
        bottom_sheets=('Power', 'Radio Power', 'USB and Charger', 'Battery', 'Hold-off'),
        keep_top=('J1', 'J2', 'SW1', 'J3', 'J4', 'U1', 'D2'),
        bottom_groups=lambda W, H: [     # underside regions, in top-view floorplan mm; kept off the radio modules where possible
            ('USB and Charger', [(20.0, 36.0, W - 0.6, H - 0.6)], (45, H - 10)),
            ('Power',           [(0.6, 17.0, 30.0, 44.0), (54.0, 24.0, W - 0.6, 44.0)], (16, 32)),
            ('Radio Power',     [(0.6, 17.0, 30.0, 44.0), (30.0, 0.6, 52.0, 24.0)], (20, 22)),
            ('Battery',         [(0.6, 15.0, 22.0, 44.0)], (8, 26)),
            ('Hold-off',        [(0.6, 30.0, 30.0, H - 0.6)], (12, 40))],
        groups=lambda W, H: [
            ('GPS',             [(50.0, 0.6, W - 0.6, 30.0)], (58, 20)),
            ('Antenna',         [(0.6, 7.8, 8.2, 17.2)], (4, 11)),
            ('microSD',         [(8.0, 36.0, 30.0, H - 16.2)], (20, 40)),
            ('USB and Charger', [(20.0, 36.0, W - 0.6, H - 0.6)], (38, H - 12)),
            ('SoC',             [(0.6, 17.0, W - 0.6, H - 10.0)], (30, 36))]),
    'long2': dict(W=84, H=54, cluster=dict(left=30.5, top=12.6), cluster_left_from_right=53.5, anchors=_long2_anchors, groups=lambda W, H: [
        ('Radio Power',     [(W - 28.0, 17.6, W - 0.6, H - 24.2)], (W - 14, 24)),
        ('Antenna',         [(W - 8.0, 7.8, W - 0.6, 18.0), (W - 28.0, 17.6, W - 0.6, H - 24.2)], (W - 4, 15)),
        ('GPS',             [(W - 54.5, 0.6, W - 28.5, 12.4)], (W - 38, 6)),
        ('Power',           [(8.0, 0.6, W - 53.5, 26.0)], ((8 + W - 53.5)/2, 12)),
        ('Battery',         [(0.6, 7.5, 15.0, H - 16)], (8, 20)),
        ('Hold-off',        [(0.6, H - 26, 18.0, H - 8)], (8, H - 16)),
        ('USB and Charger', [(8.0, 20.0, W - 47.5, H - 0.6)], (20, H - 18)),
        ('microSD',         [(W - 60.0, 28.0, W - 28.5, H - 16.2)], (W - 52, H - 18)),
        ('SoC',             [(W - 60.0, 0.6, W - 28.5, H - 16.0)], (W - 42, 25))]),
    'long3': dict(W=84, H=58, cluster=dict(left=30.5, top=17.0), cluster_left_from_right=53.5, anchors=_long3_anchors, groups=lambda W, H: [
        ('Antenna',         [(W - 62.5, 0.6, W - 53.0, 16.5)], (W - 58, 6)),
        ('GPS',             [(W - 28.5, 0.6, W - 0.6, 33.0)], (W - 18, 16)),
        ('Radio Power',     [(8.0, 0.6, W - 62.5, 12.0)], (14, 6)),
        ('Power',           [(8.0, 10.0, W - 62.5, 17.0), (8.0, 17.0, W - 53.5, 28.0)], ((8 + W - 53.5)/2, 18)),
        ('Battery',         [(0.6, 7.5, 15.0, H - 16)], (8, 22)),
        ('Hold-off',        [(0.6, H - 26, 18.0, H - 8)], (8, H - 16)),
        ('USB and Charger', [(8.0, 24.0, W - 47.5, H - 0.6)], (20, H - 18)),
        ('microSD',         [(W - 60.0, 36.0, W - 28.5, H - 16.2)], (W - 52, H - 18)),
        ('SoC',             [(W - 60.0, 0.6, W - 28.5, H - 16.0)], (W - 42, 30))]),
    'long4': dict(W=84, H=60, cluster=dict(left=30.5, top=18.0), cluster_left_from_right=53.5, anchors=_long4_anchors,
        rf_chain=dict(src=('U701', '38'), dir=(1, 0), side=1, series=['C901', 'L901', 'L902'], shunts=['C902', 'C903', 'C904'],
                      conn='J901', start=2.6, pitch=2.6, shunt_off=1.55, conn_gap=1.6), groups=lambda W, H: [
        ('Antenna',         [(W - 31.5, 0.6, W - 0.6, 17.5)], (W - 26, 14)),
        ('GPS',             [(W - 28.5, 17.0, W - 0.6, H - 24.5)], (W - 20, 28)),
        ('Radio Power',     [(8.0, 0.6, W - 60.0, 12.0)], (14, 6)),
        ('Power',           [(8.0, 10.0, W - 57.0, 20.0), (8.0, 20.0, W - 54.0, 28.0)], ((8 + W - 57.0)/2, 18)),
        ('Battery',         [(0.6, 7.5, 15.0, H - 16)], (8, 22)),
        ('Hold-off',        [(0.6, H - 26, 18.0, H - 8)], (8, H - 16)),
        ('USB and Charger', [(8.0, 24.0, W - 47.5, H - 0.6)], (20, H - 18)),
        ('microSD',         [(W - 60.0, 36.0, W - 28.5, H - 16.2)], (W - 52, H - 18)),
        ('SoC',             [(W - 60.0, 0.6, W - 28.5, H - 16.0)], (W - 42, 30))]),
    'long5': dict(W=77, H=60, cluster=dict(left=30.5, top=18.0), cluster_left_from_right=46.5, anchors=_long5_anchors,
        rf_chain=dict(src=('U701', '38'), origin=(3.8, 0.0), dir=(0, -1), side=1, series=['C901', 'L901', 'L902'], shunts=['C902', 'C903', 'C904'],
                      conn='J901', start=1.3, pitch=2.6, shunt_off=1.75, conn_gap=1.6),
        groups=lambda W, H: [
        ('GPS',             [(W - 21.0, 0.6, W - 0.6, 18.6)], (W - 12, 12)),
        ('Radio Power',     [(8.0, 0.6, W - 55.5, 12.0)], (14, 6)),
        ('Power',           [(8.0, 10.0, W - 52.5, 20.0), (8.0, 20.0, W - 47.0, 28.0)], ((8 + W - 52.5)/2, 18)),
        ('Battery',         [(0.6, 7.5, 15.0, H - 16)], (8, 22)),
        ('Hold-off',        [(0.6, H - 26, 18.0, H - 8)], (8, H - 16)),
        ('USB and Charger', [(8.0, 24.0, W - 40.5, H - 0.6)], (20, H - 18)),
        ('microSD',         [(W - 53.0, 36.0, W - 21.5, H - 16.2)], (W - 45, H - 18)),
        ('SoC',             [(W - 53.0, 0.6, W - 21.5, H - 0.6)], (W - 35, 30))]),
    'long6': dict(W=77, H=60, cluster=dict(left=30.5, top=18.0), cluster_left_from_right=46.5, anchors=_long6_anchors,
        rf_chain=dict(src=('U701', '38'), origin=(3.8, 0.0), dir=(0, -1), side=-1, series=['C901', 'L901', 'L902'], shunts=['C902', 'C903', 'C904'],
                      conn='J901', start=1.2, pitch=2.0, shunt_off=1.6, conn_gap=3.05, conn_body=(1, 0)),   # U.FL body beside the line: keeps it off the top edge (owner)
        groups=lambda W, H: [
        ('GPS',             [(W - 21.0, 0.6, W - 0.6, (H - 41.4)/2 + 18.0)], (W - 12, (H - 41.4)/2 + 10)),
        ('Radio Power',     [(8.0, 0.6, W - 55.5, 12.0)], (14, 6)),
        ('Power',           [(8.0, 10.0, W - 52.5, 20.0), (8.0, 20.0, W - 47.0, 28.0)], ((8 + W - 52.5)/2, 18)),
        ('Battery',         [(0.6, 7.5, 15.0, H - 16)], (8, 22)),
        ('Hold-off',        [(0.6, H - 26, 18.0, H - 8)], (8, H - 16)),
        ('USB and Charger', [(8.0, 24.0, W - 40.5, H - 0.6)], (20, H - 18)),
        ('microSD',         [(W - 53.0, 36.0, W - 21.5, H - 16.2)], (W - 45, H - 18)),
        ('SoC',             [(W - 53.0, 0.6, W - 21.5, H - 0.6)], (W - 35, 30))]),
}
