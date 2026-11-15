#!/usr/bin/env python3
"""Scan unpacked level files for enemy-script VM instructions that touch the
RNG state glob.3e0..3e5: ops 14/18/1c (SET/ADD/SUB) with target 0x83e0..0x83e5
and ops 28/2c/30/34 (IF) with field 0x83e0..0x83e5. Linear scan of every even
offset, so it is a candidate list, not a proof of reachability.

    python scan_vm_rng.py <levelf> [<levelf> ...]
"""
import os, sys, collections

NAMES = {0x14: 'SET', 0x18: 'ADD', 0x1c: 'SUB', 0x28: 'IFEQ', 0x2c: 'IFNE', 0x30: 'IFLT', 0x34: 'IFGT'}


def scan(path):
    d = open(path, 'rb').read()
    r16 = lambda a: int.from_bytes(d[a:a + 2], 'big')
    out = []
    for a in range(0, len(d) - 8, 2):
        op = r16(a)
        if op not in NAMES: continue
        v = r16(a + 2); k = a + 4
        lit = None
        if v == 0: lit = r16(k); k += 2
        f = r16(k)
        if 0x83e0 <= f <= 0x83e5:
            vs = ('#%d' % (lit - 65536 if lit & 0x8000 else lit)) if lit is not None else ('field 0x%04x' % v)
            out.append((a, '%s %s glob.%x' % (NAMES[op], vs, f - 0x8000)))
    print('%s (level number word = %d): %d hits' % (os.path.basename(path), r16(0), len(out)))
    for s, c in collections.Counter(t for _, t in out).most_common():
        print('   %3d x %-28s at %s' % (c, s, ','.join('%05x' % a for a, t in out if t == s)[:80]))


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('levels', nargs='+')
    for p in ap.parse_args().levels:
        scan(p)
