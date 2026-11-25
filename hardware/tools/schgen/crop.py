import sys,pymupdf
# crop.py in.svg out.png x1 y1 x2 y2 (mm)  -- assumes A4 landscape SVG in mm units
f,o=sys.argv[1],sys.argv[2]; x1,y1,x2,y2=map(float,sys.argv[3:7])
d=pymupdf.open(f); p=d[0]; W=p.rect.width; k=W/297.0
p.get_pixmap(dpi=int(sys.argv[7]) if len(sys.argv)>7 else 200,clip=pymupdf.Rect(x1*k,y1*k,x2*k,y2*k)).save(o)
