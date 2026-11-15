#!/usr/bin/env python3
"""Find references to runtime addresses in relocated bans.exe code hunks (0 and 3):
absolute longwords (jsr/jmp/lea/move etc.) and PC-relative branches
(bsr/bra/bcc, .w and .b). Heuristic: scans every even offset.

    python code_xref.py <bans.exe> 0x222b26 [...]
"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bansexe import BansExe


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('exe')
    ap.add_argument('addr', nargs='+')
    a = ap.parse_args()
    x = BansExe(a.exe)
    segs = [(x.bases[i], x.hunk_image(i), i) for i, h in enumerate(x.hunks) if h[1] == 'CODE']
    for t in [int(v, 0) for v in a.addr]:
        print('xrefs to %06x:' % t)
        for base, d, hn in segs:
            for o in range(0, len(d) - 4, 2):
                if struct.unpack('>I', d[o:o + 4])[0] == t:
                    print('  abs   %06x hunk%d+%05X  (opcode word before: %s)' % (base + o, hn, o, d[o - 2:o].hex()))
                op = struct.unpack('>H', d[o:o + 2])[0]
                if op >> 12 == 6:
                    disp = op & 0xff; p = base + o
                    if disp == 0: tg = p + 2 + struct.unpack('>h', d[o + 2:o + 4])[0]
                    elif disp == 0xff: continue
                    else: tg = p + 2 + (disp - 256 if disp > 127 else disp)
                    if tg == t: print('  rel   %06x hunk%d+%05X  %s' % (p, hn, o, d[o:o + 4].hex(' ')))


if __name__ == '__main__':
    main()
