import sys,json; sys.path.insert(0,sys.argv[1])
from wires import write
d=json.load(open(sys.argv[2]))
n,J=write(sys.argv[3],[[tuple(p) for p in w] for w in d['wires']],[tuple(p) for p in d['pins']])
print(n,'segments',len(J),'junctions')
