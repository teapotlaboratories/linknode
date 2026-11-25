"""Build hardware/datasheets/README.md from the schematic netlist (T2).
Usage: python3 gen_datasheet_index.py <netlist.xml> <jlcpcb_parts.db> <datasheets dir>
Every BOM line with an LCSC code must map to a file in DS below; the script exits non-zero if one doesn't."""
import sys, os, sqlite3, collections, xml.etree.ElementTree as ET
net, db, dsdir = sys.argv[1:4]
# LCSC code -> datasheet file (a series sheet is used for generic passives)
DS = {
 'C5328706': 'Rockchip_RV1106_Datasheet_V2.2-20260602.pdf', 'C2876593': 'TI_BQ25798_RevC_2026.pdf',
 'C165129': 'TI_TPS61089.pdf', 'C141836': 'TI_TLV62569.pdf', 'C54951857': 'esp32-c5-wroom-1_wroom-1u_datasheet_en.pdf',
 'C49233943': 'ZHONGKEWEI_ATGM336H-5NR32-G.pdf', 'C82942': 'Microne_ME6211.pdf', 'C5446': 'Torex_XC6206.pdf',
 'C57474': 'onsemi_LM393_LM2903.pdf', 'C545558': 'UMW_TL432.pdf', 'C351410': 'PUOLOP_DW01A.pdf', 'C908265': 'FUXINSEMI_FS8205A.pdf',
 'C2827654': 'TECHPUBLIC_USBLC6-2SC6.pdf', 'C20917': 'AOS_AO3400A.pdf', 'C15127': 'AOS_AO3401A.pdf', 'C8545': 'CJ_2N7002.pdf',
 'C2681218': 'UMW_SI2318A.pdf', 'C2906299': 'Winsok_WST2319.pdf', 'C19077541': 'SMAJ24A_C19077541.pdf',
 'C173431': 'MDD_BZT52.pdf', 'C2891780': 'YONGYUTAI_BZT52C12.pdf', 'C2286': 'KENTO_KT-0603R.pdf',
 'C165948': 'HRO_TYPE-C-31-M-12.pdf', 'C692446': 'XKB_DC-005G-2.5A-2.0.pdf', 'C393941': 'ShouHan_TF-PUSH.pdf', 'C22390021': 'DOWO_TPD4E05U06DQAR.pdf',
 'C441182': 'Kefa_KF2EDGR-3.81.pdf', 'C157931': 'JST_XH.pdf', 'C173752': 'JST_PH.pdf',
 'C474881': 'Kefa_KF301-5.0.pdf', 'C88374': 'Hirose_U.FL-R-SMT-1.pdf', 'C318884': 'XKB_TS-1187A.pdf',
 'C368741': 'KYX_K3A240001210_24MHz.pdf', 'C32346': 'Epson_FC-135_Q13FC13500004.pdf',
 'C602029': 'Changjiang_FHD4020S.pdf', 'C167869': 'Changjiang_FNR4030S.pdf', 'C22471111': 'Xiangru_XRIM252012S.pdf',
 'C84404': 'Murata_LQW15AN8N2G00D.pdf', 'C395068': 'Fenghua_VHF100505HQ_47nH.pdf', 'C76891': 'Murata_BLM15PD121SN1.pdf',
 'C2889048': 'Shiheng_CMFA103F3435_NTC.pdf', 'C25725': 'UniOhm_4D02_resistor_array.pdf',
 'C114755': 'Yageo_RC0402_resistor.pdf', 'C276278': 'Yageo_RC0402_resistor.pdf', 'C477682': 'Yageo_RC0402_resistor.pdf', 'C97819': 'Yageo_RC0402_resistor.pdf',
 'C2076806': 'Panasonic_ERJ2RK_resistor.pdf', 'C11631': 'RALEC_RTT02_resistor.pdf', 'C2906901': 'FOJAN_FRC0402_resistor.pdf', 'C2906903': 'FOJAN_FRC0402_resistor.pdf',
 'C22977': 'UniRoyal_0603WAF_resistor.pdf', 'C880605': 'CCTC_TCC0402_X7R.pdf',
 'C1523': 'Fenghua_0402B_X7R.pdf', 'C1542': 'Fenghua_0402B_X7R.pdf',
 'C1546': 'Fenghua_0402CG_C0G.pdf', 'C1549': 'Fenghua_0402CG_C0G.pdf', 'C1555': 'Fenghua_0402CG_C0G.pdf', 'C1561': 'Fenghua_0402CG_C0G.pdf', 'C1574': 'Fenghua_0402CG_C0G.pdf', 'C1576': 'Fenghua_0402CG_C0G.pdf',
}
for code in ('C1525', 'C15195', 'C23733', 'C52923', 'C307331'): DS[code] = 'Samsung_CL_MLCC.pdf'
for code in ('C19702', 'C19666', 'C23630', 'C59461'): DS[code] = 'Samsung_CL_MLCC.pdf'
for code in ('C15850', 'C377773', 'C45783'): DS[code] = 'Samsung_CL_MLCC.pdf'
GAP = {c: 'catalogue covers the CL part-number scheme but does not list this MPN; get the Samsung per-part spec (DC bias) before relying on effective capacitance'
       for c in ('C307331', 'C19702', 'C15850', 'C377773', 'C45783')}
NOLCSC = {'HT-HC01_V2': 'Heltec_HT-HC01_V2.pdf'}   # Heltec module: not stocked by LCSC (bought from Heltec)
c = sqlite3.connect(db)
G = collections.defaultdict(list)
for comp in ET.parse(net).getroot().iter('comp'):
    r = comp.get('ref')
    if r.startswith('#'): continue
    lc = ''
    for x in comp.iter('field'):
        if x.get('name') == 'LCSC': lc = (x.text or '').strip()
    G[(lc, comp.findtext('value'), comp.findtext('footprint') or '')].append(r)
rows, missing = [], []
for (lc, v, fp), refs in G.items():
    if lc:
        f = DS.get(lc)
        if not f or not os.path.exists(os.path.join(dsdir, f)):
            # 0402WGF/0402 UniRoyal resistors share one series sheet
            row = c.execute('select manufacturer from components where lcsc=?', (lc,)).fetchone()
            if row and 'UNI ROYAL' in (row[0] or '') and '0402' in fp: f = 'UniRoyal_0402WGF_resistor.pdf'
        if not f or not os.path.exists(os.path.join(dsdir, f)): missing.append((lc, v, refs)); continue
        m = c.execute('select mfr_part, manufacturer from components where lcsc=?', (lc,)).fetchone() or ('', '')
        rows.append((f, lc, v, m[0], m[1] or '', refs))
    elif v in NOLCSC:
        rows.append((NOLCSC[v], '(none)', v, 'HT-HC01 V2', 'Heltec', refs))
    # parts without LCSC code are test points, pin headers and debug pads
def nat(r):
    import re
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', r)]
if missing:
    print('MISSING datasheet:', missing); sys.exit(1)
rows.sort(key=lambda r: (r[0], r[1]))
used = sorted({r[0] for r in rows})
out = ['# Datasheets', '',
 'Index for `hardware/datasheets/` (T2). The table is generated from the schematic netlist by',
 '`hardware/tools/gen_datasheet_index.py`, which fails if a BOM line has no datasheet here. Regenerate it after every BOM change.',
 'Generic passives cite one series datasheet from the same manufacturer as the LCSC part.', '',
 '## BOM parts', '', '| Datasheet | LCSC | Value | MPN / manufacturer | References |', '|---|---|---|---|---|']
for f, lc, v, mpn, mfr, refs in rows:
    rs = ' '.join(sorted(refs, key=nat))
    out.append(f'| [`{f}`]({f}) | {lc} | {v} | {mpn} / {mfr} | {rs} |' + (' ¹' if lc in GAP else ''))
out += ['', '¹ The Samsung ' + next(iter(GAP.values())) + '.', '', f'{len(rows)} BOM lines, {len(used)} datasheet files. Test points, the debug UART header (J501) and the',
        'RECOVERY pad (TP501) have no LCSC part or datasheet.', '']
OTHER = {   # files that are not a BOM line, with the reason they are kept
 'Reference for a BOM part': {
  'Shiheng_MF52A103F3435_NTC.pdf': 'Pack NTC MF52A103F3435 (C84036, leaded epoxy bead, 10k 1 %, B25/85 3435 K): taped to the cells and wired to J4 (T27). Part of the pack wiring, not fitted on the board. R-T table within 0.3 % of the CMFA part from -20 to 60 C, so the TS divider R7/R8 is unchanged.',
  'Heltec_HT-HC01_V2_SDIO_reference.pdf': 'Heltec SDIO reference schematic for U701 (pull-ups, decoupling, DC block).',
  'Rockchip_RV1106_Datasheet_V1.3.pdf': 'Older RV1106 datasheet; V2.2 is current. Kept because early worklog citations use it.',
  'Rockchip_RV1106_User_Manual_GPIO.pdf': 'RV1106 GPIO chapter of the TRM (bank voltages, pin functions).',
  'TI_BQ25798.pdf': 'BQ25798 Rev B. Superseded by Rev C (`TI_BQ25798_RevC_2026.pdf`); kept for the T17 comparison.',
  'ZHONGKEWEI_ATGM336H-5N.pdf': 'ATGM336H-5N family manual (peak current, antenna supply limit) for U20.',
  'esp32-c5_datasheet_en.pdf': 'ESP32-C5 chip datasheet behind the U801 module.',
  'SMAJ_series.pdf': 'Byte-identical copy of `SMAJ24A_C19077541.pdf`, cited under this name in the 2026-11-20 worklog and the T15 report.',
  'ST_USBLC6-2.pdf': 'ST original of the USBLC6-2 (U1 is the TECH PUBLIC second source).',
  'Kefa_KF2EDGK-3.81.pdf': 'Screw plug for J2 (KF2EDGK-3.81-2P, LCSC C440858), shipped loose, not assembled (T38).',
  'Kefa_KF301-5.0.pdf': 'Earlier 5 mm screw terminal for J3/J4, replaced by JST XH/PH (T33). Kept for the record.',
  'XKB_DC-005G-2.5A-2.0.pdf': 'Earlier DC barrel jack for J2, replaced by the Kefa terminal block (T38). Kept for the record.',
  'TI_TPD4E05U06.pdf': 'TI original of the TPD4E05U06 (U401/U402 are the DOWO pin-compatible part, T42).',
  'XKB_DC-005.pdf': 'XKB DC-005 family drawing; J2 used the DC-005G-2.5A-2.0 sheet until T38 (now a KF2EDGR terminal block).',
 },
 'Reference designs': {
  'Core1106.pdf': 'Luckfox Core1106 SoM schematic (power tree and boot reference; the SoM itself was replaced by the chip-down design).',
  'Luckfox-Pico-Pro-Max.pdf': 'Luckfox Pico Pro Max schematic (RV1106G3 chip-down reference).',
  'Voltaic_P105_dwg.pdf': 'Voltaic P105 panel drawing, an example handheld 6 V panel for P-11.',
 },
 'For users (not on the LinkNode BOM)': {
  'BatWireless_BWCD-L5.0W2.0H2.5.pdf': 'Suggested pogo pin for a user\'s mating board on the expansion pads (T49, H-17): LCSC C2826549, plunger Ø0.90, flange Ø2.00, 2.5 mm stroke, 75 g, 10,000 cycles (p.4-5).',
 },
 'Dropped parts (kept for the decision record)': {
  'Shiheng_CMFA103F3435_NTC.pdf': 'Former on-board NTC TH1 (C2889048, 0603 SMD). Removed in T27: the cells are off-board, so the NTC moved to the pack as a leaded MF52A part.',
  'Everanalog_EA3036C.pdf': 'Core1106 PMIC; rejected: 1 A per channel against 1.6 A VDD_0V9 peaks (project rules, power tree).',
  'Everanalog_EA3036_Datasheet_V1.1.pdf': 'EA3036 (non-C) datasheet, same decision.',
  'Silergy_SY7088.pdf': 'Earlier 5 V boost candidate, replaced by the TPS61089.',
  'TI_TPS22917.pdf': 'Load switch from the Core1106 tree, dropped with the per-rail TLV62569s.',
  'TI_TPS22918.pdf': 'Load switch candidate, dropped with the per-rail TLV62569s.',
  'esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf': 'Original ESP32 module, replaced by the GPS (G-1, N-2, N-8).',
  'esp32_datasheet_en.pdf': 'Original ESP32 chip, same decision.',
 },
}
extra = sorted(set(os.listdir(dsdir)) - set(used) - {'README.md'})
described = {f for g in OTHER.values() for f in g}
if set(extra) - described or described - set(extra):
    print('undescribed:', sorted(set(extra) - described), 'stale:', sorted(described - set(extra))); sys.exit(1)
out += ['## Other documents', '']
for title, files in OTHER.items():
    out += [f'### {title}', '', '| File | Why it is here |', '|---|---|']
    out += [f'| [`{f}`]({f}) | {why} |' for f, why in sorted(files.items())] + ['']
out += ['## Elsewhere', '',
 '- `resources/resource/`: owner-supplied material: the Rockchip RV1103G/RV1106G hardware design guide, the RV1106 power-sequence',
 '  figure and power-consumption report, the Luckfox and Rockchip reference schematics (`board_reference/`), and the Quectel',
 '  FGH100M HaLow guide. Prefer it over web copies (project rules).',
 '- `docs/reports/soc-compare/`: RK3566 comparison sources (T24), linked by URL rather than filed here.', '']
open(os.path.join(dsdir, 'README.md'), 'w').write('\n'.join(out))
print(len(rows), 'BOM lines,', len(used), 'BOM datasheets,', len(extra), 'other files')
