# samples.py file base outdir [rate]  -> WAV per unique sample (8-bit signed PCM, Paula)
import sys,struct,wave,os
d=open(sys.argv[1],'rb').read(); B=int(sys.argv[2],0); out=sys.argv[3]; rate=int(sys.argv[4]) if len(sys.argv)>4 else 5911
L=lambda o:struct.unpack('>I',d[o:o+4])[0]; W=lambda o:struct.unpack('>H',d[o:o+2])[0]
os.makedirs(out,exist_ok=True); seen={}; lim=L(B); i=-1
while True:
    i+=1; o=B+i*16
    if o-B>=lim: break
    off=L(o); ln=W(o+4)*2; loop=W(o+6); lim=min(lim,off)
    if off==0 or B+off+ln>len(d): continue
    key=(off,ln)
    if key in seen: continue
    seen[key]=i
    pcm=bytes((b+128)&255 for b in d[B+off:B+off+ln])
    w=wave.open('%s/%02d_%05x%s.wav'%(out,i,off,'_loop' if loop==0xffff else ''),'wb'); w.setnchannels(1); w.setsampwidth(1); w.setframerate(rate); w.writeframes(pcm); w.close()
print(sys.argv[1],i,'rekordów,',len(seen),'unikalnych sampli')
