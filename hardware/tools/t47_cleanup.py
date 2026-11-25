"""T47 (2026-11-23): remove routing debris that kicad-cli DRC reports as via_dangling / track_dangling, repeatedly, on the
given nets only, and refuse to save if the board's unconnected count rises (so nothing needed is removed).
Usage: python3 t47_cleanup.py <board.kicad_pcb> NET[,NET...]   (one round per run: repeat until it removes nothing)"""
import sys, os, json, subprocess, tempfile, math, pcbnew
B = sys.argv[1]; NETS = set(sys.argv[2].split(','))
def drc(path):
    out = os.path.join(tempfile.mkdtemp(), 'd.json')
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-all', '-o', out, path], capture_output=True)
    return json.load(open(out))['violations']
removed = []
for rnd in range(1):                     # one round per process (one board per process); call again until nothing is removed
    b = pcbnew.LoadBoard(B); u0 = b.GetConnectivity().GetUnconnectedCount(False)   # one board per process: later counts run in a subprocess
    items = [(x['type'], i) for x in drc(B) if x['type'] in ('via_dangling', 'track_dangling') for i in x['items']]
    hit = []
    for typ, it in items:
        p = (it['pos']['x'], it['pos']['y'])
        for t in b.GetTracks():
            if t.GetNetname() not in NETS: continue
            if t.GetClass() == 'PCB_VIA' and typ == 'via_dangling' and math.dist(p, (t.GetPosition().x/1e6, t.GetPosition().y/1e6)) < 0.005: hit.append(t)
            if t.GetClass() != 'PCB_VIA' and typ == 'track_dangling' and math.dist(p, (t.GetStart().x/1e6, t.GetStart().y/1e6)) < 0.005: hit.append(t)
    if not hit: break
    keep = []; desc = [(t.GetClass()[4:], t.GetNetname()[-18:]) for t in hit]
    for t in hit: b.Remove(t); keep.append(t)
    tmp = B + '.cleanup_try.kicad_pcb'; b.Save(tmp)                      # count on a reloaded copy (SWIG handles go stale)
    u1 = int(subprocess.run([sys.executable, '-c', 'import pcbnew,sys; print(pcbnew.LoadBoard(sys.argv[1]).GetConnectivity().GetUnconnectedCount(False))', tmp], capture_output=True, text=True).stdout.strip().splitlines()[-1])
    if u1 > u0:
        os.remove(tmp); print('stop: removing %s would raise unconnected %d -> %d' % (desc, u0, u1)); break
    os.replace(tmp, B); removed += desc
print(json.dumps(dict(removed=removed)))
