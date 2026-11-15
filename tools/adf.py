import sys,struct,os
def L(b,o):return struct.unpack('>i',b[o:o+4])[0]
d=open(sys.argv[1],'rb').read(); out=sys.argv[2] if len(sys.argv)>2 else None
ffs=d[3]&1
blk=lambda n:d[n*512:(n+1)*512]
def walk(n,path):
    b=blk(n)
    for i in range(72):
        h=L(b,24+i*4)
        while h:
            e=blk(h); nl=e[432]; name=e[433:433+nl].decode('latin1'); st=L(e,508)
            p=path+'/'+name
            if st==2:
                print('D',p); 
                if out: os.makedirs(out+p,exist_ok=True)
                walk(h,p)
            else:
                size=L(e,324); print('F %8d %s'%(size,p))
                if out:
                    data=b'';x=h
                    while x:
                        xb=blk(x); cnt=L(xb,8)
                        for k in range(cnt):
                            db=L(xb,308-k*4); data+= blk(db) if ffs else blk(db)[24:24+L(blk(db),12)]
                        x=L(xb,504)
                    open(out+p,'wb').write(data[:size])
            h=L(e,496)
r=blk(880); print('volume',r[433:433+r[432]].decode('latin1'))
if out: os.makedirs(out,exist_ok=True)
walk(880,'')
