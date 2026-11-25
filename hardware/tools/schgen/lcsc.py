import sqlite3,json,sys
c=sqlite3.connect(__import__('os').environ.get('JLCPCB_DB', 'jlcpcb_parts.db'))
def find(sub, terms, package, n=2):
    sql="select lcsc,mfr_part,package,library_type,stock,price_json,description from components where subcategory like ? and package like ?"
    args=[f'%{sub}%',f'{package}%']
    for t in terms: sql+=" and description like ?"; args.append(f'%{t}%')
    sql+=" order by case library_type when 'Basic' then 0 when 'Preferred' then 1 else 2 end, stock desc limit ?"; args.append(n)
    out=[]
    for r in c.execute(sql,args):
        p=json.loads(r[5]) if r[5] else []
        out.append((r[0],r[1],r[2],r[3],r[4],p[0]['price'] if p else None,r[6][:70]))
    return out
if __name__=='__main__':
    for line in sys.stdin:
        line=line.strip()
        if not line: continue
        sub,pkg,*terms=line.split('|')
        print('##',line)
        for o in find(sub,terms,pkg): print('  ',o)
