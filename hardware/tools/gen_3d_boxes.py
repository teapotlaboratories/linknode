"""Simple VRML 3D model for the HaLow module HT-HC01 V2, the one part with no vendor model (not sold on LCSC).
The other seven parts now use EasyEDA/LCSC STEP models fetched with easyeda2kicad and aligned by tools/align_easyeda_3d.py.
The box definitions for those parts are kept below for reference but no longer generated (T26, 2026-11-21).
Each model is a few coloured boxes at datasheet size, placed on the footprint origin, sitting on the board (z = 0).
KiCad reads VRML in 0.1-inch units, so every mm value is divided by 2.54. Good enough for renders and a first height
check; replace with vendor STEP models before any MCAD enclosure work.
Sources (hardware/datasheets/):
  RV1106G3 QFN-128: 12.3 x 12.3 x 0.85 mm (Rockchip_RV1106_Datasheet_V2.2 Fig 2-7 p.19)
  HT-HC01 V2: 18.5 x 14 x 2.6 mm (Heltec_HT-HC01_V2.pdf p.10)
  ESP32-C5-WROOM-1U: 18 x 19.6 x 3.3 mm, shield about 15.8 x 15.9 (esp32-c5-wroom-1_wroom-1u_datasheet_en.pdf Fig 10-2 p.51)
  ATGM336H-5NR32-G: 9.7 x 10.1 x 2.1 mm (ZHONGKEWEI_ATGM336H-5NR32-G.pdf p.9)
  EST (drawings without a text layer; typical catalogue sizes):
    BQ25798 RQM VQFN-29: 4 x 4 x 0.9 mm
    HRO TYPE-C-31-M-12: shell 8.94 x 7.3 x 3.26 mm
    XKB TS-1187A: 5.1 x 5.1 x 1.5 mm with a 2.6 mm round actuator to 1.7 mm
    ShouHan TF-PUSH: 14.9 x 13.9 x 1.85 mm shell, card slot toward +y
"""
import sys, os
OUT = sys.argv[1] if len(sys.argv) > 1 else 'library/3dmodels'
U = 1 / 2.54
COL = {'black': (0.08, 0.08, 0.09, 0.4), 'shield': (0.55, 0.56, 0.59, 0.25), 'pcb': (0.06, 0.28, 0.17, 0.2),
       'gold': (0.85, 0.65, 0.2, 0.9), 'grey': (0.35, 0.36, 0.38, 0.3), 'white': (0.9, 0.9, 0.88, 0.2)}

def box(cx, cy, z0, sx, sy, sz, col):
    r, g, b, shin = COL[col]
    return ('Transform { translation %.4f %.4f %.4f children Shape { appearance Appearance { material Material { '
            'diffuseColor %.3f %.3f %.3f specularColor 0.25 0.25 0.25 shininess %.2f } } geometry Box { size %.4f %.4f %.4f } } }\n'
            % (cx*U, -cy*U, (z0 + sz/2)*U, r, g, b, shin, sx*U, sy*U, sz*U))

def cyl(cx, cy, z0, d, h, col):
    r, g, b, shin = COL[col]
    return ('Transform { translation %.4f %.4f %.4f rotation 1 0 0 1.5708 children Shape { appearance Appearance { material Material { '
            'diffuseColor %.3f %.3f %.3f shininess %.2f } } geometry Cylinder { radius %.4f height %.4f } } }\n'
            % (cx*U, -cy*U, (z0 + h/2)*U, r, g, b, shin, d/2*U, h*U))

M = {
 'RV1106G3_QFN128': [box(0, 0, 0.02, 12.3, 12.3, 0.83, 'black'), cyl(-5.2, -5.2, 0.85, 0.8, 0.01, 'grey')],
 'HT-HC01_V2':      [box(0, 0, 0, 18.5, 14.0, 0.8, 'pcb'), box(0, 0, 0.8, 17.3, 12.8, 1.8, 'shield')],
 'ESP32-C5-WROOM-1U': [box(0.25, 0, 0, 18.0, 19.6, 0.8, 'pcb'), box(0.25, 1.4, 0.8, 15.8, 15.9, 2.5, 'shield'),
                       cyl(-6.2, -8.2, 0.8, 2.0, 1.25, 'gold')],
 'ATGM336H_5N':     [box(0, 0, 0, 9.7, 10.1, 0.8, 'pcb'), box(0, 0, 0.8, 9.1, 9.5, 1.3, 'shield')],
 'BQ25798_VQFN29':  [box(0, 0, 0, 4.0, 4.0, 0.9, 'black'), cyl(-1.5, -1.5, 0.9, 0.4, 0.01, 'grey')],
 'USB_C_HRO_TYPE-C-31-M-12': [box(0, -0.15, 0, 8.94, 7.3, 3.26, 'shield')],
 'SW_TS-1187A':     [box(0, 0, 0, 5.1, 5.1, 1.0, 'grey'), box(0, 0, 1.0, 5.1, 5.1, 0.2, 'shield'), cyl(0, 0, 1.2, 2.6, 0.5, 'black')],
 'microSD_TF-PUSH': [box(0.45, -3.65, 0, 14.9, 13.9, 1.85, 'shield')],
}
os.makedirs(OUT, exist_ok=True)
for name, parts in M.items():
    if name != 'HT-HC01_V2': continue
    open(os.path.join(OUT, name + '.wrl'), 'w').write('#VRML V2.0 utf8\n# LinkNode placeholder model, see hardware/tools/gen_3d_boxes.py\n' + ''.join(parts))
    print('wrote', name + '.wrl')
