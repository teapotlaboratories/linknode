import re,sys
p=sys.argv[1]; s=open(p).read()
head=s[:s.index('\t(lib_symbols')]
open(p,'w').write(head+'\t(lib_symbols)\n\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n)\n')
