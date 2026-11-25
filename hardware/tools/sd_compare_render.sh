set -e; C=$(dirname $(readlink -f $0))
R="-w 1300 -h 1400 --zoom 2.6 --background opaque"
cd $C/cal; for s in top bottom; do p=$([ $s = top ] && echo -0.8 || echo 0.8); kicad-cli pcb render --side $s $R --pan $p,3.0,0 -o q_$s.png linknode.kicad_pcb >/dev/null 2>&1; done
cd $C/before; for s in top bottom; do p=$([ $s = top ] && echo -0.8 || echo 0.8); kicad-cli pcb render --side $s $R --pan $p,3.0,0 -o q_$s.png linknode.kicad_pcb >/dev/null 2>&1; done
for d in before after; do cd $C/$d; for s in top bottom; do p=$([ $s = top ] && echo -0.8 || echo 0.8); kicad-cli pcb render --side $s $R --quality high --pan $p,3.0,0 -o hq_$s.png linknode.kicad_pcb > hq_$s.log 2>&1; echo $d $s done; done; done
