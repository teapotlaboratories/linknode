#!/bin/bash
# usage: pcbcrop.sh out.png x1 y1 x2 y2 [layers]
S=scratch
L=${6:-F.Cu,F.SilkS,F.Fab,F.CrtYd,Edge.Cuts}
kicad-cli pcb export svg --mode-single --page-size-mode 1 --exclude-drawing-sheet -l "$L" -o $S/render/pcb.svg /home/argonite/Developments/klepon/hardware/kicad/linknode.kicad_pcb >/dev/null 2>&1
$S/venv/bin/python -I -W ignore $S/crop.py $S/render/pcb.svg "$1" $2 $3 $4 $5 ${7:-120}
