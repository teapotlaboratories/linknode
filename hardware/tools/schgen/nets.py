import sys,re,subprocess,os
sys.path.insert(0,os.path.dirname(__file__)); import symlib
out=sys.argv[2]
subprocess.run(['kicad-cli','sch','export','netlist','-o',out,sys.argv[1]],check=True,capture_output=True)
t=symlib.parse(open(out).read())
nets=[c for c in t if isinstance(c,list) and c[0]=='nets'][0]
for n in nets[1:]:
    name=[x for x in n if isinstance(x,list) and x[0]=='name'][0][1]
    nodes=sorted(f"{[y for y in x if isinstance(y,list) and y[0]=='ref'][0][1]}/{[y for y in x if isinstance(y,list) and y[0]=='pin'][0][1]}" for x in n if isinstance(x,list) and x[0]=='node')
    print(name+': '+' '.join(nodes))
