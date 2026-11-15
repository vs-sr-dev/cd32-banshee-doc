# ground.py levelf out.png [maxrows]
import sys,struct
from PIL import Image
d=open(sys.argv[1],'rb').read(); out=sys.argv[2]
L=lambda o:struct.unpack('>I',d[o:o+4])[0]; W=lambda o:struct.unpack('>H',d[o:o+2])[0]
DIR=L(6); STR=L(0xa); PO=L(0x16)
pal=[tuple(d[PO+i*6+1:PO+i*6+6:2]) for i in range(128)]
def stream():
    p=STR; v=0
    while True:
        b=d[p]; p+=1
        if b&0x80:
            n=b&15; hi=(b<<4)&0x700
            for _ in range(n+1): v=hi|d[p]; p+=1; yield v
            continue
        n=b&15; c=b>>4
        if c==0:
            for _ in range(n+1): yield v
        elif c==1:
            for _ in range(n+1): v=(v-1)&0xffff; yield v
        elif c==2:
            for _ in range(n+1): v=(v-1)&0xffff; yield v
            v=(v+7)&0xffff; yield v
        elif c==3:
            for _ in range(n+1): v=(v+1)&0xffff; yield v
        elif c==4:
            return
        else:
            q=p-1; w=(b<<8)|d[p]; p+=1; a=q+0x5000-w
            hb=d[a]; a+=1; n2=hb&15; hi=(hb<<4)&0x700
            for _ in range(n2+1): v=hi|d[a]; a+=1; yield v
tiles=list(stream())
rows=len(tiles)//24
if len(sys.argv)>3: rows=min(rows,int(sys.argv[3]))
print('stream@%x dir@%x tiles %d rows %d (%d px) maxidx %d'%(STR,DIR,len(tiles),len(tiles)//24,len(tiles)//24*16,max(tiles)))
cache={}
def tile(t):
    if t in cache: return cache[t]
    e=L(DIR+t*4); a=DIR+(e&0x3ffff)*2; planes=[]
    for k in range(7):
        code=(e>>(30-2*k))&3
        if code==0: pl=[W(a+i*2) for i in range(16)]; a+=32
        elif code==1: pl=[0xffff]*16
        elif code==2: pl=[0]*16
        else: pl=[W(a)]*16; a+=2
        planes.append(pl)
    pix=[[sum(((planes[k][y]>>(15-x))&1)<<k for k in range(7)) for x in range(16)] for y in range(16)]
    cache[t]=pix; return pix
H=rows*16; img=Image.new('RGB',(384,H)); px=img.load()
for i in range(rows*24):
    r,c=divmod(i,24); col=23-c; row=rows-1-r
    T=tile(tiles[i])
    for y in range(16):
        for x in range(16): px[col*16+x,row*16+y]=pal[T[y][x]]
img.save(out)
