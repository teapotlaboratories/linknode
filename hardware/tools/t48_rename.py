"""T48 (owner, 2026-11-23): rename the project Klepon -> LinkNode.
Usage: python3 t48_rename.py <repo root> [--dry-run]
- KiCad: hardware/kicad/klepon.kicad_{pro,pcb,sch,prl,dru} -> linknode.*, library/klepon.kicad_sym -> linknode.kicad_sym,
  library/klepon.pretty -> linknode.pretty; contents: lib tables, every `klepon:` lib_id, schematic instance
  (project "klepon"), the .kicad_pro sheet/file names, the bottom silkscreen name (its render_cache is dropped so KiCad
  redraws it in the embedded Really Free font).
- Tools (hardware/tools/**) and the living docs listed in DOCS.
- Not touched (history): worklogs, archived pages, past reports, docs/exports, backups, output/.
- The repo folder ~/Developments/klepon keeps its name: 'Developments/klepon' and 'Developments-klepon' (paths) are protected.
Case map: KLEPON -> LINKNODE, Klepon -> LinkNode, klepon -> linknode."""
import sys, os, re, glob
ROOT = sys.argv[1]; DRY = '--dry-run' in sys.argv
K = os.path.join(ROOT, 'hardware/kicad')
PROTECT = [('Developments/klepon', '\x00A'), ('Developments-klepon', '\x00B')]
def ren(s, skip_line=None):
    out = []
    for line in s.split('\n'):
        if skip_line and skip_line in line: out.append(line); continue
        for a, b in PROTECT: line = line.replace(a, b)
        line = line.replace('KLEPON', 'LINKNODE').replace('Klepon', 'LinkNode').replace('klepon', 'linknode')
        for a, b in PROTECT: line = line.replace(b, a)
        out.append(line)
    return '\n'.join(out)
def drop_render_cache(s, text):
    """Remove (render_cache "<text>" ...) blocks so KiCad regenerates the glyphs."""
    key = f'(render_cache "{text}"'; n = 0
    while key in s:
        i = s.index(key); d = 0
        for j, ch in enumerate(s[i:]):
            if ch == '(': d += 1
            elif ch == ')':
                d -= 1
                if d == 0: break
        k = s.rindex('\n', 0, i); s = s[:k] + s[i + j + 1:]; n += 1
    return s, n
report = []
def edit(path, skip_line=None, pcb=False):
    s = open(path, encoding='utf-8').read(); t = ren(s, skip_line)
    if pcb: t, n = drop_render_cache(t, 'LinkNode'); report.append(f'  render_cache dropped: {n}')
    if t != s:
        report.append(f'edit {os.path.relpath(path, ROOT)}: {len(re.findall("(?i)klepon", s)) - len(re.findall("(?i)klepon", t))} names')
        if not DRY: open(path, 'w', encoding='utf-8').write(t)
def move(a, b):
    report.append(f'rename {os.path.relpath(a, ROOT)} -> {os.path.relpath(b, ROOT)}')
    assert os.path.exists(a) and not os.path.exists(b), (a, b)
    if not DRY: os.rename(a, b)
# 1. KiCad files (content first, then names)
for p in sorted(glob.glob(os.path.join(K, '*.kicad_sch'))): edit(p)
for ext in ('kicad_pro', 'kicad_prl', 'kicad_dru'): edit(os.path.join(K, 'klepon.' + ext))
edit(os.path.join(K, 'klepon.kicad_pcb'), pcb=True)
for t in ('sym-lib-table', 'fp-lib-table'): edit(os.path.join(K, t))
edit(os.path.join(K, 'library/klepon.kicad_sym'))
for p in sorted(glob.glob(os.path.join(K, 'library/klepon.pretty/*.kicad_mod'))): edit(p)
edit(os.path.join(K, 'library/3dmodels/HT-HC01_V2.wrl'))
edit(os.path.join(K, 'library/3dmodels/easyeda_alignment.json'))
for ext in ('kicad_pro', 'kicad_pcb', 'kicad_sch', 'kicad_prl', 'kicad_dru'):
    move(os.path.join(K, 'klepon.' + ext), os.path.join(K, 'linknode.' + ext))
move(os.path.join(K, 'library/klepon.kicad_sym'), os.path.join(K, 'library/linknode.kicad_sym'))
move(os.path.join(K, 'library/klepon.pretty'), os.path.join(K, 'library/linknode.pretty'))
# 2. tools
for p in sorted(glob.glob(os.path.join(ROOT, 'hardware/tools/**/*'), recursive=True)):
    if os.path.isfile(p) and p.endswith(('.py', '.sh', '.md', '.json', '.txt')) and not p.endswith('t48_rename.py'): edit(p)
# 3. living docs
DOCS = ['docs/requirements.md', 'docs/power-budget.md', 'docs/rv1106-pinmap.md', 'docs/calc/power_budget.py', 'hardware/datasheets/README.md']
for d in DOCS:
    if os.path.exists(os.path.join(ROOT, d)): edit(os.path.join(ROOT, d))
edit(os.path.join(ROOT, 'docs/todo.md'), skip_line='| T48 |')
print('\n'.join(report)); print('dry run' if DRY else 'done')
