# spawns.py levelc levelf ground.png out.png [xoff]
import sys,struct
from PIL import Image,ImageDraw
c=open(sys.argv[1],'rb').read(); d=open(sys.argv[2],'rb').read()
g=Image.open(sys.argv[3]).convert('RGB'); out=sys.argv[4]; XO=int(sys.argv[5]) if len(sys.argv)>5 else 0
L=lambda b,o:struct.unpack('>I',b[o:o+4])[0]; S=lambda b,o:struct.unpack('>h',b[o:o+2])[0]
pal=[tuple(d[L(d,0x16)+i*6+1:L(d,0x16)+i*6+6:2]) for i in range(128)]
B=L(c,8); gb=B+L(c,B); nb=(L(c,B)-4)//20
def bob(i):
    de=B+4+20*i; go=gb+L(c,de); w=S(c,de+4); h=S(c,de+6); hx=S(c,de+8); hy=S(c,de+10)
    if not(0<w<=20 and 0<h<=256): return None
    im=Image.new('RGBA',(w*16,h)); px=im.load()
    for y in range(h):
        row=go+y*w*14
        for x in range(w*16):
            bit=lambda r:(c[row+r*w*2+x//8]>>(7-x%8))&1
            if bit(0): px[x,y]=pal[sum(bit(1+p)<<p for p in range(6))]+(255,)
    return im,hx,hy
TT=L(d,0xe); SC=L(d,0x12); o=L(d,0x1c); recs=[]
while S(d,o)>=0: recs.append([S(d,o+i*2) for i in range(6)]); o+=12
def first_frame(t):
    td=L(d,TT+t); a=SC+S(d,td)
    for k in range(0,240,2):
        p=a+k
        if S(d,p)!=0: continue
        q=p+2; v=S(d,q)
        if v==0: q+=4
        elif v>0 and v<0x200: q+=2
        else: continue
        n=S(d,q); b=S(d,q+2)
        if 0<=n<=8 and 0<b<nb: return b
    return None
H=g.height; dr=ImageDraw.Draw(g); cache={}; hit=0
for trig,x,y,t,fl,p in recs:
    b=first_frame(t)
    if b is not None:
        if b not in cache: cache[b]=bob(b)
        r=cache[b]
        if r:
            im,hx,hy=r; X=x-hx+XO; Y=H-1-(y+hy)
            if 0<=Y<H: g.paste(im,(X,Y),im); hit+=1; continue
    X=x+XO; Y=H-1-y
    dr.rectangle((X-3,Y-3,X+3,Y+3),outline=(255,0,255))
print(len(recs),'spawnów,',hit,'z grafiką')
g.save(out)
