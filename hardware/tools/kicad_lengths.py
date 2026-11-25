"""Net lengths exactly as KiCad's DRC measures them (tracks plus via barrels through the stack-up), read by running
kicad-cli DRC on a temporary copy with a 1 mm length limit on each net: every violation reports the actual length.
Usage: python3 kicad_lengths.py <board.kicad_pcb> NET[,NET...]  -> JSON {net: mm}. T30, 2026-11-22."""
import sys, os, re, json, shutil, subprocess, tempfile
board, nets = sys.argv[1], sys.argv[2].split(',')
d = tempfile.mkdtemp(); base = os.path.splitext(os.path.basename(board))[0]
src = os.path.dirname(os.path.abspath(board))
shutil.copy(board, os.path.join(d, base + '.kicad_pcb'))
for ext in ('.kicad_pro',):
    p = os.path.join(src, base + ext)
    if os.path.exists(p): shutil.copy(p, os.path.join(d, base + ext))
rules = ['(version 1)'] + ['(rule "len%d" (condition "A.NetName == \'%s\'") (constraint length (max 1mm)))' % (i, n) for i, n in enumerate(nets)]
open(os.path.join(d, base + '.kicad_dru'), 'w').write('\n'.join(rules) + '\n')
out = os.path.join(d, 'drc.json')
subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '-o', out, os.path.join(d, base + '.kicad_pcb')], capture_output=True)
res = {}
for x in json.load(open(out))['violations']:
    if x['type'] != 'length_out_of_range': continue
    m = re.search(r"rule 'len(\d+)'.*?actual ([\d.]+) mm", x['description'])
    if m: res[nets[int(m.group(1))]] = float(m.group(2))
shutil.rmtree(d)
print(json.dumps(res))
