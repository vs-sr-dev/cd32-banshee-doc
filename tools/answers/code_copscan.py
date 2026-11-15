#!/usr/bin/env python3
"""Find the copper lists in bans.exe hunk 4 (chip DATA) that set BPLCON0 to a
display mode, print their display registers, and the code sites whose
relocated longwords point into each list.

    python code_copscan.py <bans.exe>
"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from relocs import parse

NAMES = {0x08e: 'DIWSTRT', 0x090: 'DIWSTOP', 0x092: 'DDFSTRT', 0x094: 'DDFSTOP', 0x100: 'BPLCON0', 0x102: 'BPLCON1',
         0x104: 'BPLCON2', 0x108: 'BPL1MOD', 0x10a: 'BPL2MOD', 0x10c: 'BPLCON4', 0x1fc: 'FMODE', 0x080: 'COP1LCH', 0x084: 'COP2LCH'}


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('exe')
    ap.add_argument('--hunk', type=int, default=4, help='hunk holding the copper lists (default 4)')
    a = ap.parse_args()
    d = open(a.exe, 'rb').read()
    hunks, relocs = parse(d)
    start = {h[0]: h[2] for h in hunks}
    _, _, fs, ln, _ = hunks[a.hunk]
    body = d[fs:fs + ln]
    r16 = lambda o: struct.unpack('>H', body[o:o + 2])[0]

    def ok(o):
        w1, w2 = r16(o), r16(o + 2)
        if w1 & 1: return w2 & 1 == 0 or (w1, w2) == (0xffff, 0xfffe)
        return 0x20 <= w1 <= 0x1fe

    refs = {}
    for src, tgt, off in relocs:
        if tgt == a.hunk:
            v = struct.unpack('>I', d[start[src] + off:start[src] + off + 4])[0]
            refs.setdefault(v, []).append((src, off))
    seen = set()
    for o in range(0, len(body) - 4, 2):
        if r16(o) == 0x0100 and r16(o + 2) & 0x7000 | r16(o + 2) & 0x10 and r16(o + 2) & 0x0200 and o not in seen:
            s = o
            while s >= 4 and ok(s - 4) and r16(s - 4) != 0xffff: s -= 4
            e, regs, nbpl = s, {}, 0
            while e < len(body) - 4 and ok(e):
                w1, w2 = r16(e), r16(e + 2)
                if (w1, w2) == (0xffff, 0xfffe): break
                if w1 & 1 == 0:
                    if w1 == 0x100: seen.add(e)
                    if w1 in NAMES: regs.setdefault(w1, w2)
                    if 0xe0 <= w1 <= 0xfe: nbpl += 1
                e += 4
            print('list hunk%d+0x%X..+0x%X (file 0x%06X), %d bpl-pointer moves' % (a.hunk, s, e, fs + s, nbpl))
            print('   ' + ' '.join('%s=$%04x' % (NAMES[k], v) for k, v in sorted(regs.items())))
            for r in sorted(v for v in refs if s <= v <= e):
                print('   hunk%d+0x%X referenced from %s' % (a.hunk, r, ', '.join('hunk%d+0x%X' % v for v in refs[r][:6])))


if __name__ == '__main__':
    main()
