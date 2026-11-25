#!/bin/bash
# usage: [SCH=<dir with *.kicad_sch>] [PRO=<file.kicad_pro>] drccheck.sh <board.kicad_pcb> <outdir> [dru]
# Copies the project around the board into <outdir>, refills zones (pcbnew), runs DRC with schematic parity on the saved file
# and again with --refill-zones, prints violation counts, parity and unconnected for both.
set -e
K=$(cd "$(dirname "$0")/../kicad" && pwd)
B=$1; O=$2; DRU=${3:-$K/linknode.kicad_dru}
mkdir -p $O; cp $K/*.kicad_sch $K/sym-lib-table $K/fp-lib-table $K/linknode.kicad_pro $K/linknode.kicad_prl $O/; ln -sfn $K/library $O/library
if [ -n "$SCH" ]; then cp $SCH/*.kicad_sch $O/; fi
if [ -n "$PRO" ]; then cp $PRO $O/linknode.kicad_pro; fi
cp $DRU $O/linknode.kicad_dru; cp $B $O/linknode.kicad_pcb
cd $K && python3 - $O/linknode.kicad_pcb <<'P' 2>&1 | grep -v "Debug\|leak"
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); f = pcbnew.ZONE_FILLER(b); f.Fill(b.Zones()); b.Save(sys.argv[1]); print('refilled')
P
cd $O && kicad-cli pcb drc --format json --schematic-parity -o drc_saved.json linknode.kicad_pcb >/dev/null 2>&1 || true
kicad-cli pcb drc --format json --schematic-parity --refill-zones -o drc_refill.json linknode.kicad_pcb >/dev/null 2>&1 || true
python3 - <<'P'
import json, collections
for f in ('drc_saved.json', 'drc_refill.json'):
    d = json.load(open(f)); c = collections.Counter(v['type'] for v in d['violations'])
    print(f, dict(c), 'parity', len(d.get('schematic_parity', [])), 'unconnected', len(d['unconnected_items']))
P
rmdir ~/.local/share/kicad/10.0/scripting 2>/dev/null || true
