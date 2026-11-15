# map.py levelf out.png [pal.rgb idxbase]
import sys,struct
from PIL import Image
d=open(sys.argv[1],'rb').read(); out=sys.argv[2]
L=lambda o:struct.unpack('>I',d[o:o+4])[0]; W=lambda o:struct.unpack('>H',d[o:o+2])[0]
M=L(0x24); T=L(0x28)
hdr=[W(M+i*2) for i in range(4)]; rows=(L(0x28)-M-8)//48 if T>M else hdr[1]
print('map@%x tiles@%x hdr %s rows %d'%(M,T,hdr,rows))
pal=[(0,0,0),(85,85,85),(170,170,170),(255,255,255)]
if len(sys.argv)>4:
    p=open(sys.argv[3],'rb').read(); b=int(sys.argv[4]); pal=[tuple(p[(b+i)*3:(b+i)*3+3]) for i in range(4)]
img=Image.new('RGB',(24*16,rows*16)); px=img.load(); mx=0
for r in range(rows):
    for c in range(24):
        t=W(M+8+r*48+c*2); mx=max(mx,t)
        for y in range(16):
            w0=W(T+t*64+y*4); w1=W(T+t*64+y*4+2)
            for x in range(16):
                v=((w0>>(15-x))&1)|(((w1>>(15-x))&1)<<1)
                px[c*16+x,r*16+y]=pal[v]
print('max tile',mx,'tiles avail',(len(d)-T)//64)
img.save(out)
