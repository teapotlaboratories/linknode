"""Renumber references inside one sheet (and its builder/field files): prefix+digits, hundreds digit old->new.
Usage: renum.py OLD NEW file.kicad_sch [builder.py fields.txt ...]   (e.g. 1 5 soc.kicad_sch)"""
import re, sys
old, new = sys.argv[1], sys.argv[2]
pat = re.compile(r'\b(R|C|Y|J|TP|FB)%s(\d\d)\b' % old)
sch = sys.argv[3]; s = open(sch).read(); n = 0
def sub_ref(m):
    global n; n += 1; return m.group(1) + pat.sub(lambda k: k.group(1) + new + k.group(2), m.group(2)) + m.group(3)
s = re.sub(r'(\(property "Reference" ")([^"]+)(")', sub_ref, s)
s = re.sub(r'(\(reference ")([^"]+)(")', sub_ref, s)
open(sch, 'w').write(s); print(sch, 'refs touched', n)
for f in sys.argv[4:]:
    t = open(f).read(); t2 = re.sub(r"(?<=['\"\n])(R|C|Y|J|TP|FB)%s(\d\d)(?=['\":])" % old, lambda k: k.group(1) + new + k.group(2), t)
    t2 = re.sub(r"^(R|C|Y|J|TP|FB)%s(\d\d):" % old, lambda k: k.group(1) + new + k.group(2) + ':', t2, flags=re.M)
    open(f, 'w').write(t2); print(f, 'changed', t != t2)
