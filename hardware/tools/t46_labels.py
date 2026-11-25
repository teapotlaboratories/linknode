"""T46 (owner, 2026-11-23): silkscreen labels for the user-facing parts and the Teapotlabs branding, in the BWLC1A style
(~/Developments/bwlc1a/tracker-c0/hardware/kicad/tracker-c0.kicad_pcb, read 2026-11-23):
- user labels: F.SilkS knockout, bold, size 1.0 / thickness 0.2 ("LTE ANT", "GNSS"); small ones 0.8 / 0.15 ("CHRG");
  polarity marks "+" / "-" plain, size 1.0 / thickness 0.15.
  No CHG label at LED D2: no 0.8 mm spot exists around it (min_text_height 0.8) and it is not a wiring label.
- branding on B.SilkS: TeapotLogo footprint (copied to linknode.pretty) + "Teapotlabs" and the product name in the
  "Really Free" face, size 3 / thickness 0.15, justify left bottom mirror, with the tracker's offsets to the logo;
  "REVISION 1" separately, knockout bold 2.0 / 0.35, justify mirror.
- the Really Free font is embedded in the board (embedded_fonts yes + the tracker's embedded_files block).
Usage: python3 t46_labels.py <board.kicad_pcb> <font_block.txt> [--check-only]
Pass 1 (pcbnew): logo footprint + KiCad-font texts. Pass 2 (text edit): the two Really Free texts and the font block.
The checker reports every label box against same-side pads (THT pads on both), other courtyards, footprint silk,
the board edge and the other new items."""
import sys, re, uuid, pcbnew
BRD, FONT = sys.argv[1], sys.argv[2]; CHECK = '--check-only' in sys.argv
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
# (text, x, y, size, thickness, bold, knockout)
TOP = [('BAT', 104.0, 107.1, 1.0, 0.2, True, True), ('+', 112.45, 111.47, 1.0, 0.15, False, False), ('-', 112.45, 113.97, 1.0, 0.15, False, False),
       ('NTC', 102.6, 125.1, 1.0, 0.2, True, True),
       ('DC IN', 105.4, 150.4, 1.0, 0.2, True, True), ('+', 109.35, 149.75, 1.0, 0.15, False, False), ('-', 115.0, 149.05, 1.0, 0.15, False, False),
       ('PWR', 121.3, 152.9, 0.8, 0.15, True, True), ('USB', 131.6, 149.9, 1.0, 0.2, True, True), ('SD', 153.7, 143.3, 1.0, 0.2, True, True),
       ('WiFi HaLow', 162.0, 105.2, 1.0, 0.2, True, True), ('GPS', 170.6, 112.4, 1.0, 0.2, True, True), ('WiFi 2.4GHz 5GHz', 163.5, 152.5, 1.0, 0.2, True, True)]
REV = ('REVISION 1', 167.0, 129.8)
# tracker block translated by (dx, dy): logo (150.459433, 106.131975) rot 180; Teapotlabs anchor (146.345, 105.82); name (145.450523, 109.22)
DX, DY = 21.74, 3.87
LOGO = (150.459433 + DX, 106.131975 + DY)
RF = [('Teapotlabs', 146.345 + DX, 105.82 + DY), ('LinkNode', 145.450523 + DX, 109.22 + DY + 0.3)]  # +0.3: 'LinkNode' k/L ascenders met the 'p' descender (T48)

b = pcbnew.LoadBoard(BRD)
new = []
if not any(f.GetFPIDAsString().endswith('TeapotLogo') for f in b.GetFootprints()):
    lib = BRD.rsplit('/', 1)[0] + '/library/linknode.pretty' if '/' in BRD else 'library/linknode.pretty'
    fp = pcbnew.FootprintLoad(lib, 'TeapotLogo'); fp.SetFPID(pcbnew.LIB_ID('linknode', 'TeapotLogo'))
    fp.SetReference('LOGO1'); b.Add(fp); fp.SetPosition(V(*LOGO)); fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT); fp.SetOrientationDegrees(180)
    new.append(fp)
    def add(text, x, y, size, th, bold, ko, layer, mirror=False):
        t = pcbnew.PCB_TEXT(b); t.SetText(text); t.SetLayer(layer); t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(th))
        t.SetBold(bold); t.SetIsKnockout(ko); t.SetMirrored(mirror); t.SetPosition(V(x, y)); b.Add(t); new.append(t); return t
    for it in TOP: add(*it, pcbnew.F_SilkS)
    add(REV[0], REV[1], REV[2], 2.0, 0.35, True, True, pcbnew.B_SilkS, True)

# ---- checker ----
def box(it):
    if it.GetClass() == 'PCB_TEXT' and not it.IsKnockout():
        bb = it.GetEffectiveTextShape().BBox(); h = it.GetTextThickness()/2e6
        return (bb.GetLeft()/1e6 - h, bb.GetTop()/1e6 - h, bb.GetRight()/1e6 + h, bb.GetBottom()/1e6 + h)
    bb = it.GetBoundingBox(); return (bb.GetLeft()/1e6, bb.GetTop()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6)
def gap(a, c):
    dx = max(c[0] - a[2], a[0] - c[2], 0); dy = max(c[1] - a[3], a[1] - c[3], 0); return (dx*dx + dy*dy) ** 0.5 if dx and dy else max(dx, dy) if (dx or dy) else -1
items = [x for x in new] if new else []
if not items:  # re-check an already-labelled board
    for d in b.GetDrawings():
        if d.GetClass() == 'PCB_TEXT' and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS): items.append(d)
    items += [f for f in b.GetFootprints() if f.GetFPIDAsString().endswith('TeapotLogo')]
eb = b.GetBoardEdgesBoundingBox(); E = (eb.GetLeft()/1e6, eb.GetTop()/1e6, eb.GetRight()/1e6, eb.GetBottom()/1e6)
OPEN = ('J', 'TP', 'MH')
OBS = {False: [], True: []}   # side -> [(box, min gap, label)]; gap < thr is a conflict (thr 0 means overlap only)
for f in b.GetFootprints():
    if f.GetFPIDAsString().endswith('TeapotLogo'): continue
    r = f.GetReference()
    for p in f.Pads():
        tht = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
        for side in (False, True):
            if tht or f.IsFlipped() == side: OBS[side].append((box(p), 0.2, f'pad {r}.{p.GetNumber()}'))
    side = f.IsFlipped()
    cy = f.GetCourtyard(pcbnew.B_CrtYd if side else pcbnew.F_CrtYd)
    if cy.OutlineCount() and not r.startswith(OPEN):
        bb = cy.BBox(); OBS[side].append(((bb.GetLeft()/1e6, bb.GetTop()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6), 1e-9, f'courtyard {r}'))
    for g_ in f.GraphicalItems():
        if g_.GetLayer() == (pcbnew.B_SilkS if side else pcbnew.F_SilkS) and g_.GetClass() == 'PCB_SHAPE':
            OBS[side].append((box(g_), 0.15, f'silk {r}'))
    if r.startswith('MH'):
        c = f.GetPosition(); rr = 2.75
        for sd in (False, True): OBS[sd].append(((c.x/1e6 - rr, c.y/1e6 - rr, c.x/1e6 + rr, c.y/1e6 + rr), 0.2, f'M3 head {r}'))
def isbottom(it): return it.IsFlipped() if it.GetClass() == 'FOOTPRINT' else it.GetLayer() == pcbnew.B_SilkS
def conflicts(it):
    bottom = isbottom(it); name = it.GetReference() if it.GetClass() == 'FOOTPRINT' else it.GetText()
    a = box(it); worst = []
    for c, thr, lab in OBS[bottom]:
        g = gap(a, c)
        if (g < thr) if thr > 1e-6 else (g < 0): worst.append(f'{lab} {g:.2f}')
    for o in items:
        if o is not it and isbottom(o) == bottom and gap(a, box(o)) < 0.2:
            worst.append('new item ' + (o.GetText() if o.GetClass() != 'FOOTPRINT' else o.GetReference()))
    e = min(a[0] - E[0], a[1] - E[1], E[2] - a[2], E[3] - a[3])
    if e < 0.5: worst.append(f'edge {e:.2f}')
    return worst, a, bottom, name

FALLBACK = {t: [(0.8, 0.15, True), (0.8, 0.15, False), (0.6, 0.12, False)] for t in ('CHG', 'PWR')}
def search(it, R=4.0, step=0.1):
    p0 = it.GetPosition(); cand = []
    n = int(R/step)
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            d = (i*i + j*j) ** 0.5 * step
            if d <= R: cand.append((d, i*step, j*step))
    cand.sort()
    for d, dx, dy in cand:
        it.SetPosition(pcbnew.VECTOR2I(p0.x + mm(dx), p0.y + mm(dy)))
        if not conflicts(it)[0]: return d
    it.SetPosition(p0); return None
bad = 0
for it in items:
    moved = 0.0
    if new and conflicts(it)[0] and it.GetClass() != 'FOOTPRINT':
        moved = search(it)
        if moved is None and it.GetText() in FALLBACK:   # small labels: try the tracker's smaller styles, then 90 deg
            for size, th, ko in FALLBACK[it.GetText()]:
                for ang in (0, 90):
                    it.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); it.SetTextThickness(mm(th)); it.SetIsKnockout(ko); it.SetTextAngleDegrees(ang)
                    moved = search(it, R=3.0)
                    if moved is not None: break
                if moved is not None: break
    worst, a, bottom, name = conflicts(it); bad += bool(worst)
    pos = it.GetPosition()
    print(('FAIL ' if worst else 'ok   ') + ('B ' if bottom else 'T ') + f'{name:11s} {it.GetTextHeight()/1e6 if it.GetClass()=="PCB_TEXT" else 0:.1f}{"KO" if it.GetClass()=="PCB_TEXT" and it.IsKnockout() else "  "} r{it.GetTextAngleDegrees() if it.GetClass()=="PCB_TEXT" else 0:.0f} at {pos.x/1e6:.2f},{pos.y/1e6:.2f} moved {moved if moved is not None else "none found"} box {a[0]:.2f},{a[1]:.2f} - {a[2]:.2f},{a[3]:.2f}', '; '.join(worst))
print('conflicts:', bad, 'of', len(items))
if CHECK or bad: sys.exit(0 if CHECK else 1)
b.Save(BRD)

# ---- pass 2: Really Free texts + embedded font (text edit) ----
s = open(BRD).read()
blk = ''
for t, x, y in RF:
    blk += f'''
	(gr_text "{t}"
		(at {x:.6f} {y:.6f} 0)
		(layer "B.SilkS")
		(uuid "{uuid.uuid4()}")
		(effects
			(font
				(face "Really Free")
				(size 3 3)
				(thickness 0.15)
			)
			(justify left bottom mirror)
		)
	)'''
k = s.rindex('\n\t(embedded_fonts no)'); assert s.count('\n\t(embedded_fonts no)') == 1
s = s[:k] + blk + '\n' + open(FONT).read().rstrip('\n') + s[k + len('\n\t(embedded_fonts no)'):]
open(BRD, 'w').write(s)
print('pass 2: Really Free texts + embedded font written')
