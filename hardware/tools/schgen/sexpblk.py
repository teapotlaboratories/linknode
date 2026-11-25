"""Whitespace-agnostic helpers for .kicad_sch text: find placed symbol blocks and their properties by paren matching."""
import re
def close(s,i):
    """index just past the ')' matching the '(' at s[i] (ignores parens inside strings)."""
    d=0; q=False; j=i
    while j<len(s):
        c=s[j]
        if q:
            if c=='\\': j+=1
            elif c=='"': q=False
        elif c=='"': q=True
        elif c=='(': d+=1
        elif c==')':
            d-=1
            if d==0: return j+1
        j+=1
    raise ValueError('unbalanced')
def lib_end(s):
    i=s.find('(lib_symbols'); return close(s,i) if i>=0 else 0
def symbols(s):
    """yield (start,end,ref) for placed symbols (outside lib_symbols)."""
    j=lib_end(s)
    for m in re.finditer(r'\(symbol\s*\(lib_id',s[j:]):
        a=j+m.start(); b=close(s,a); blk=s[a:b]
        r=re.search(r'\(property\s+"Reference"\s+"([^"]*)"',blk)
        yield a,b,(r.group(1) if r else None)
def unit_of(blk):
    m=re.search(r'\(unit (\d+)\)',blk); return int(m.group(1)) if m else 1
def find_symbol(s,ref,unit=None):
    """ref may be 'U30@2' to pick unit 2 of a multi-unit part."""
    if unit is None and '@' in ref: ref,unit=ref.split('@'); unit=int(unit)
    for a,b,r in symbols(s):
        if r==ref and (unit is None or unit_of(s[a:b])==unit): return a,b
    raise KeyError((ref,unit))
def prop_span(blk,name):
    m=re.search(r'\(property\s+"%s"\s+"'%re.escape(name),blk)
    if not m: raise KeyError(name)
    return m.start(),close(blk,m.start())
def strip_top(s,tag):
    """remove every top-level (tag ...) block (e.g. wire, junction) outside lib_symbols."""
    out=[];pos=0; j=lib_end(s)
    for m in re.finditer(r'\n?[ \t]*\(%s\s'%tag,s):
        if m.start()<j or m.start()<pos: continue
        a=m.start(); k=s.index('(',a); b=close(s,k)
        out.append(s[pos:a]); pos=b
    out.append(s[pos:]); return ''.join(out)
