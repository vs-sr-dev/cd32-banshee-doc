#!/usr/bin/env python3
"""Load the CD32 executable (bans.exe, AmigaDOS hunk file) and build relocated
memory images with the same bases the Ghidra project uses: hunks packed back to
back from 0x21f000.

    python bansexe.py <bans.exe>                     hunk / base table
    python bansexe.py <bans.exe> 0x22ecd0 hunk0+0x1234 file:0x2586
                                                     convert addresses
    python bansexe.py <bans.exe> --dump 1 out.bin    write relocated hunk N

Library use:
    from bansexe import BansExe
    x = BansExe('bans.exe')
    x.read(0x236cdc, 16); x.to_hunk(0x22ecd0); x.to_runtime(1, 0x10)
"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from relocs import parse

BASE = 0x21f000
EXPECTED = [0x21f000, 0x236cdc, 0x23d610, 0x290f64, 0x291084, 0x2951f4]


class BansExe:
    def __init__(self, path, base=BASE, check=True):
        self.raw = open(path, 'rb').read()
        hunks, relocs = parse(self.raw)
        self.hunks = hunks                      # (idx, kind, filestart, length, memflag)
        self.bases = []
        a = base
        for h in hunks:
            self.bases.append(a)
            a += h[3]
        self.end = a
        if check and len(self.bases) == len(EXPECTED):
            assert self.bases == EXPECTED, 'hunk bases differ from the Ghidra layout'
        self.img = []
        for (i, k, fs, ln, mf) in hunks:
            self.img.append(bytearray(ln) if fs is None else bytearray(self.raw[fs:fs + ln]))
        for (src, tgt, off) in relocs:
            v = struct.unpack_from('>I', self.img[src], off)[0]
            struct.pack_into('>I', self.img[src], off, (v + self.bases[tgt]) & 0xffffffff)
        self.mem = b''.join(bytes(x) for x in self.img)

    def to_hunk(self, addr):
        for i, b in enumerate(self.bases):
            if b <= addr < b + self.hunks[i][3]:
                return i, addr - b
        raise ValueError('0x%x is outside the executable' % addr)

    def to_runtime(self, hunk, off):
        return self.bases[hunk] + off

    def to_file(self, addr):
        h, off = self.to_hunk(addr)
        fs = self.hunks[h][2]
        return None if fs is None else fs + off

    def from_file(self, fo):
        for i, (_, k, fs, ln, _) in enumerate(self.hunks):
            if fs is not None and fs <= fo < fs + ln:
                return self.bases[i] + fo - fs
        raise ValueError('file offset 0x%x is not inside a hunk body' % fo)

    def read(self, addr, n):
        assert BASE <= addr and addr + n <= self.end, 'read outside image'
        o = addr - self.bases[0]
        return self.mem[o:o + n]

    def hunk_image(self, i):
        return bytes(self.img[i])

    def w(self, a): return struct.unpack('>H', self.read(a, 2))[0]
    def s(self, a): return struct.unpack('>h', self.read(a, 2))[0]
    def l(self, a): return struct.unpack('>I', self.read(a, 4))[0]

    def describe(self, addr):
        h, off = self.to_hunk(addr)
        fo = self.to_file(addr)
        return '0x%06x = hunk%d+0x%x = %s' % (addr, h, off, 'file 0x%06x' % fo if fo is not None else 'BSS (no file image)')


def parse_addr(x, s):
    if s.startswith('hunk'):
        h, off = s[4:].split('+')
        return x.to_runtime(int(h), int(off, 0))
    if s.startswith('file:'):
        return x.from_file(int(s[5:], 0))
    return int(s, 0)


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('exe')
    ap.add_argument('addr', nargs='*', help='runtime address, hunkN+off or file:off')
    ap.add_argument('--dump', nargs=2, metavar=('HUNK', 'OUT'))
    a = ap.parse_args()
    x = BansExe(a.exe)
    if a.dump:
        open(a.dump[1], 'wb').write(x.hunk_image(int(a.dump[0])))
        return
    if not a.addr:
        print('hunk  kind  memory   length    runtime base  file offset')
        for (i, k, fs, ln, mf), b in zip(x.hunks, x.bases):
            print('  %-3d %-5s %-6s 0x%06x  0x%06x      %s' % (i, k, mf, ln, b, '0x%06x' % fs if fs is not None else '-- (bss)'))
    for s in a.addr:
        print(x.describe(parse_addr(x, s)))


if __name__ == '__main__':
    main()
