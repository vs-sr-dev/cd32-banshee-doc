#!/usr/bin/env python3
"""Compare the floppy picture.exe (uncrunched) with the CD one (decrunched).

    python picture_diff.py <floppy picture.exe> <CD picture.exe>
    python picture_diff.py <floppy picture.exe> <dir with hunk1.bin hunk2.bin hunk3.bin>

The CD file is decrunched in memory with rnc2.py; a directory written by
`python rnc2.py exe <CD picture.exe> <dir>` is accepted as well.
Offsets printed are from the start of each hunk body; for the floppy file the
body's file offset is printed too.
"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rnc2


def hunks(path):
    d = open(path, 'rb').read()
    w = lambda o: struct.unpack('>I', d[o:o + 4])[0]
    assert w(0) == 0x3F3
    n = w(8); o = 20 + 4 * n
    out = []
    while o < len(d):
        t = w(o) & 0x3FFFFFFF
        if t in (0x3E9, 0x3EA):
            size = w(o + 4) * 4
            out.append((o + 8, d[o + 8:o + 8 + size])); o += 8 + size
        elif t == 0x3EB:
            out.append((None, b'')); o += 8
        elif t == 0x3F2:
            o += 4
        elif t == 0x3EC:
            o += 4
            while w(o):
                o += 8 + 4 * w(o)
            o += 4
        else:
            raise SystemExit('hunk type %x at %x' % (t, o))
    return out


def cd_hunks(path):
    """Decrunched bodies of hunks 1..3 of the CD picture.exe (or read from a hunk dir)."""
    if os.path.isdir(path):
        return [open(os.path.join(path, 'hunk%d.bin' % i), 'rb').read() for i in (1, 2, 3)]
    out = []
    for foff, body in hunks(path)[1:4]:
        assert body[8:12] == b'RNC', 'CD hunk is not an RNC method 2 stream'
        out.append(rnc2.unpack(body, 8))
    return out


if len(sys.argv) != 3:
    raise SystemExit(__doc__)
fl = hunks(sys.argv[1])
cd = cd_hunks(sys.argv[2])
for i, ((foff, a), b) in enumerate(zip(fl, cd)):
    b = b[:len(a)]
    diff = [k for k in range(len(a)) if a[k] != b[k]]
    print('floppy hunk %d (body @ file 0x%x, %d B)  vs CD hunk %d: %d bytes differ'
          % (i, foff, len(a), i + 1, len(diff)))
    if i == 0:
        for k in range(0x1bc, len(a), 2):
            print('   +0x%03x  floppy %s  CD %s' % (k, a[k:k + 2].hex(), b[k:k + 2].hex()))
    if i == 1:
        for k in range(0, 0x2c8, 4):
            r, va, vb = struct.unpack('>H', a[k:k + 2])[0], a[k + 2:k + 4].hex(), b[k + 2:k + 4].hex()
            if va != vb and (0xe0 <= r < 0x140):
                print('   +0x%03x  move $%03x  floppy %s  CD %s' % (k, r, va, vb))
        pal = b[0x2c8:0x2c8 + 192]
        hi = [((pal[j*3] >> 4) << 8) | ((pal[j*3+1] >> 4) << 4) | (pal[j*3+2] >> 4) for j in range(64)]
        cols = [struct.unpack('>H', b[k + 2:k + 4])[0] for k in range(0, 0x2c8, 4)
                if 0x180 <= struct.unpack('>H', b[k:k + 2])[0] < 0x1c0]
        print('   CD copper colour words == high nibbles of the 64-entry table, bank 0: %s'
              % (cols[:32] == hi[:32]))
        print('   floppy copper colour words all zero: %s' % all(
            a[k + 2:k + 4] == b'\0\0' for k in range(0, 0x2c8, 4)
            if 0x180 <= struct.unpack('>H', a[k:k + 2])[0] < 0x1c0))
