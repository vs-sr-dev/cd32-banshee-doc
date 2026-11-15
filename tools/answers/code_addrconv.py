#!/usr/bin/env python3
"""Runtime address <-> bans.exe hunk offset / file offset.

Prints the hunk table with the Ghidra-style load bases (hunks packed back to
back from 0x21f000) and converts addresses given as runtime (0x2222ba),
hunkN+off (hunk0+0x32ba) or file offset (file:0x32ee).

    python code_addrconv.py <bans.exe>                  table
    python code_addrconv.py <bans.exe> 0x2222ba ...     convert
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bansexe import BansExe, parse_addr


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('exe')
    ap.add_argument('addr', nargs='*')
    a = ap.parse_args()
    x = BansExe(a.exe)
    print('hunk kind mem    length    file_body  runtime_base  runtime_end')
    for (i, k, fs, ln, mf), b in zip(x.hunks, x.bases):
        print('%4d %-4s %-5s %8d  %-9s  0x%06x      0x%06x' % (i, k, mf, ln, '0x%06x' % fs if fs is not None else '--', b, b + ln))
    for s in a.addr:
        try:
            print(x.describe(parse_addr(x, s)))
        except ValueError as e:
            print('%s  %s (heap/stub/custom chips)' % (s, e))


if __name__ == '__main__':
    main()
