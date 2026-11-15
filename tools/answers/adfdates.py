#!/usr/bin/env python3
"""List every entry of an OFS/FFS ADF with its AmigaDOS date stamp, size,
header block, protection bits, comment and SHA-1 of the content.

Usage: python adfdates.py <disk.adf> [...]   (one table per image)
"""
import sys, struct, hashlib, datetime

EPOCH = datetime.datetime(1978, 1, 1)


def L(b, o):
    return struct.unpack('>I', b[o:o + 4])[0]


def stamp(b, o):
    d, m, t = L(b, o), L(b, o + 4), L(b, o + 8)
    return EPOCH + datetime.timedelta(days=d, minutes=m, seconds=t / 50.0), (d, m, t)


class Adf:
    def __init__(self, path):
        self.d = open(path, 'rb').read()
        self.ffs = self.d[3] & 1
        self.boot = self.d[:4]

    def blk(self, n):
        return self.d[n * 512:(n + 1) * 512]

    def data(self, h):
        e = self.blk(h)
        size = L(e, 324)
        out = b''
        x = h
        while x:
            xb = self.blk(x)
            for k in range(L(xb, 8)):
                db = L(xb, 308 - k * 4)
                b = self.blk(db)
                out += b if self.ffs else b[24:24 + L(b, 12)]
            x = L(xb, 504)
        return out[:size]

    def walk(self, n=880, path=''):
        b = self.blk(n)
        for i in range(72):
            h = L(b, 24 + i * 4)
            while h:
                e = self.blk(h)
                name = e[433:433 + e[432]].decode('latin1')
                st = struct.unpack('>i', e[508:512])[0]
                dt, raw = stamp(e, 420)
                cl = e[328]
                com = e[329:329 + cl].decode('latin1')
                p = path + '/' + name
                if st == 2:
                    yield ('D', p, 0, dt, raw, h, L(e, 320), com, '')
                    yield from self.walk(h, p)
                else:
                    dat = self.data(h)
                    yield ('F', p, L(e, 324), dt, raw, h, L(e, 320), com,
                           hashlib.sha1(dat).hexdigest())
                h = L(e, 496)


def main():
    for path in sys.argv[1:]:
        a = Adf(path)
        r = a.blk(880)
        print('#', path)
        print('# dostype %r ffs=%d volume %r' % (a.boot[:3], a.ffs, r[433:433 + r[432]].decode('latin1')))
        for lab, o in (('root altered', 420), ('volume altered', 472), ('created', 484)):
            print('#   %-15s %s %s' % (lab, *stamp(r, o)))
        ents = sorted(a.walk(), key=lambda e: e[3])
        for t, p, size, dt, raw, h, prot, com, sha in ents:
            print('%s %-19s %8d blk%4d prot%08x %s %s%s' % (
                t, dt.strftime('%Y-%m-%d %H:%M:%S'), size, h, prot, sha[:12] or ' ' * 12, p,
                ('  ;' + com) if com else ''))
        print()


if __name__ == '__main__':
    main()
