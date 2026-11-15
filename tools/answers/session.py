#!/usr/bin/env python3
"""Line the CD's 41 wrong-clock file dates up against the retail floppy set.

For every CD file that also exists on a floppy: CD date, floppy date,
floppy-minus-CD offset, the gap since the previous file in each session, the
implied write rate, and whether the contents are byte-identical.

Usage: python session.py <track1.iso> <disk1.adf> <disk2.adf> <disk3.adf> <disk4.adf>
"""
import sys, os, datetime, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from adfdates import Adf

SEC = 2048


def iso_files(path):
    f = open(path, 'rb')
    rd = lambda lba, n: (f.seek(lba * SEC), f.read(n))[1]
    pvd = rd(16, SEC)
    out = {}

    def walk(lba, size, prefix):
        d = rd(lba, size)
        o = 0
        while o < len(d):
            n = d[o]
            if n == 0:
                o = (o // SEC + 1) * SEC
                continue
            ext = int.from_bytes(d[o + 2:o + 6], 'little')
            ln = int.from_bytes(d[o + 10:o + 14], 'little')
            y, mo, dd, h, mi, s = d[o + 18:o + 24]
            fl = d[o + 25]
            nm = d[o + 33:o + 33 + d[o + 32]].decode('latin1').split(';')[0]
            if nm not in ('\x00', '\x01'):
                p = prefix + '/' + nm
                if fl & 2:
                    walk(ext, ln, p)
                else:
                    dt = datetime.datetime(1900 + y, mo, dd, h, mi, s) if mo else None
                    data = rd(ext, ln) if ln else b''
                    out[p] = (dt, ln, ext, hashlib.sha1(data).hexdigest(), (y, mo, dd, h, mi, s))
            o += n
    walk(int.from_bytes(pvd[158:162], 'little'), int.from_bytes(pvd[166:170], 'little'), '')
    return out


def main():
    cd = iso_files(sys.argv[1])
    fl = {}
    for disk, path in enumerate(sys.argv[2:6], 1):
        for t, p, size, dt, raw, h, prot, com, sha in Adf(path).walk():
            if t == 'F' and p.count('/') == 1 and dt.year == 1992:
                fl[p] = (disk, dt, size, sha)
    rows = sorted((v[0], p) for p, v in cd.items() if v[0] and v[0].year == 1992)
    print('%-13s %4s %8s  %-8s %-11s %7s %5s %6s %5s %7s  %s' % (
        'file', 'disk', 'bytes', 'CD', 'floppy', 'fl-CD', 'gCD', 'KB/sCD', 'gFl', 'KB/sFl', 'content'))
    pc = pf = None
    for dt, p in rows:
        _, size, _, sha, _ = cd[p]
        disk, fdt, fsize, fsha = fl.get(p, (0, None, 0, ''))
        off = (fdt.replace(microsecond=0) - dt).total_seconds() if fdt else None
        g1 = (dt - pc).total_seconds() if pc else None
        g2 = (fdt - pf).total_seconds() if (fdt and pf) else None
        r = lambda g: '%6.1f' % (size / 1024 / g) if g else '     -'
        print('%-13s %4s %8d  %s %-11s %7s %5s %6s %5s %7s  %s' % (
            p[1:], disk or '-', size, dt.strftime('%H:%M:%S'),
            fdt.strftime('%H:%M:%S.%f')[:11] if fdt else '-',
            '%+d:%02d' % divmod(int(off), 60) if off is not None else '-',
            '%d' % g1 if g1 is not None else '-', r(g1),
            '%.0f' % g2 if g2 is not None else '-', r(g2),
            'same' if sha == fsha else ('DIFFERENT' if fsha else 'not on floppy')))
        pc, pf = dt, fdt or pf
    print()
    for p, v in sorted(cd.items()):
        if not v[0] or v[0].year < 1979:
            print('zero/epoch record: %-14s extent %d length %d raw date bytes %s' % (p, v[2], v[1], v[4]))


if __name__ == '__main__':
    main()
