# bobs.py file bankoff outdir [palette.rgb] -> sheet of all bobs
import sys,struct,os
from PIL import Image,ImageDraw
d=open(sys.argv[1],'rb').read(); B=int(sys.argv[2],0); out=sys.argv[3]
pal=None
if len(sys.argv)>4:
    p=open(sys.argv[4],'rb').read(); pal=[tuple(p[i*3:i*3+3]) for i in range(len(p)//3)]
L=lambda o:struct.unpack('>I',d[o:o+4])[0]; W=lambda o:struct.unpack('>h',d[o:o+2])[0]
gbase=B+L(B); n=(L(B)-4)//20
os.makedirs(out,exist_ok=True); ims=[]
for i in range(n):
    de=B+4+20*i; go=gbase+L(de); w=W(de+4); h=W(de+6)
    if not(0<w<=20 and 0<h<=256): ims.append(None); continue
    im=Image.new('RGBA',(w*16,h),(0,0,0,0)); px=im.load()
    for y in range(h):
        row=go+y*w*2*7
        for x in range(w*16):
            bit=lambda r:(d[row+r*w*2+x//8]>>(7-x%8))&1 if row+r*w*2+x//8<len(d) else 0
            if not bit(0): continue
            v=sum(bit(1+p)<<p for p in range(6))
            px[x,y]=(pal[v]+(255,)) if pal else (v*4,v*4,v*4,255)
    ims.append(im)
print(n,'obiektów, gfx@',hex(gbase))
# sheet
cols=12; cw=max((i.width for i in ims if i),default=16)+4
rows=[ims[k:k+cols] for k in range(0,n,cols)]
H=sum(max([i.height for i in r if i]+[8])+14 for r in rows)
sh=Image.new('RGB',(cols*min(cw,100)+0,H),(30,30,60)); dr=ImageDraw.Draw(sh); y=0
cw=min(cw,100)
for ri,r in enumerate(rows):
    for ci,im in enumerate(r):
        dr.text((ci*cw,y),str(ri*cols+ci),fill=(255,255,0))
        if im: sh.paste(im.crop((0,0,min(im.width,cw-2),im.height)),(ci*cw,y+12),im.crop((0,0,min(im.width,cw-2),im.height)))
    y+=max([i.height for i in r if i]+[8])+14
sh.save(out+'/_sheet.png')
for i,im in enumerate(ims):
    if im: im.save(out+'/%03d.png'%i)
